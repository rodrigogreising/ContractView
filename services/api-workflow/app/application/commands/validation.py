from datetime import date
from decimal import Decimal
from hashlib import sha256
import json
import uuid

from .access_scope import invoice_scope
from ...authorization import Action,Actor,execute_authorized,require_permission
from .provenance import append_event_tx, append_relation_tx
from .budget import calculate_budget
from .invoice_snapshots import create_invoice_snapshot_tx
from ...shared_contracts import RuleResult, ValidationRunDto

from ..ports.statements import Statement
from ..transaction import transaction as database
ENGINE_VERSION="deterministic-validation-v1"
RULE_VERSIONS={
    "SERVICE_PERIOD":"service-period-v1","REQUIRED_EVIDENCE":"required-evidence-v1",
    "BUDGET_AVAILABLE":"budget-available-v1","TOTAL_RECONCILIATION":"total-reconciliation-v1",
    "POSSIBLE_DUPLICATE":"possible-duplicate-v1",
}

def _canonical(value)->str:return json.dumps(value,sort_keys=True,separators=(",",":"))
def _hash(value)->str:return sha256(_canonical(value).encode()).hexdigest()
def _result(rule,severity,reason,outcome,message,normalized,expense=None):
    return RuleResult(rule_code=rule,rule_version=RULE_VERSIONS[rule],severity=severity,reason_code=reason,outcome=outcome,expense_key=expense,normalized_input=normalized,message=message).model_dump(by_alias=True)

def execute_validation(actor:Actor,invoice_id:str)->dict:
    def command():
        with database() as connection:
            invoice=connection.invoices.execute(Statement.VALIDATION_READ_INVOICE_VERSIONS_001,(invoice_id,)).fetchone()
            if not invoice:raise FileNotFoundError(invoice_id)
            config=connection.configuration.execute(Statement.VALIDATION_READ_CONFIGURATION_VERSIONS_002,(invoice[1],)).fetchone()[0]
            lines=connection.invoices.execute(Statement.VALIDATION_READ_INVOICE_LINES_003,(invoice_id,)).fetchall()
            normalized={"invoiceVersionId":invoice_id,"configurationVersionId":invoice[1],"total":f"{invoice[3]:.2f}","lines":[{"expenseKey":r[0],"date":r[1].isoformat(),"vendor":r[2],"category":r[3],"amount":f"{r[4]:.2f}","evidenceArtifactId":r[5],"ledgerSource":r[6]} for r in lines]}
            rules={item["code"]:item for item in config["rules"] if item.get("enabled",True)}
            results=[]
            start=date.fromisoformat(config["servicePeriod"]["start"]);end=date.fromisoformat(config["servicePeriod"]["end"])
            if "SERVICE_PERIOD" in rules:
                for row in lines:
                    passed=start<=row[1]<=end
                    results.append(_result("SERVICE_PERIOD",rules["SERVICE_PERIOD"]["severity"],"IN_SERVICE_PERIOD" if passed else f"SERVICE_PERIOD:{row[0]}","pass" if passed else "fail",f"{row[1]} is within {start}..{end}" if passed else f"{row[1]} is outside {start}..{end}",{"date":row[1].isoformat(),"start":start.isoformat(),"end":end.isoformat()},row[0]))
            if "REQUIRED_EVIDENCE" in rules:
                for row in lines:
                    passed=row[5] is not None
                    results.append(_result("REQUIRED_EVIDENCE",rules["REQUIRED_EVIDENCE"]["severity"],"EVIDENCE_PRESENT" if passed else f"REQUIRED_EVIDENCE:{row[0]}","pass" if passed else "fail","Supporting evidence is linked" if passed else "Supporting evidence is missing",{"evidenceArtifactId":row[5]},row[0]))
            category_totals={}
            for row in lines:category_totals[row[3]]=category_totals.get(row[3],Decimal("0.00"))+row[4]
            budget=calculate_budget(category_totals,config["categories"])
            if "BUDGET_AVAILABLE" in rules:
                for category in budget["categories"]:
                    passed=not category["overBudget"]
                    results.append(_result("BUDGET_AVAILABLE",rules["BUDGET_AVAILABLE"]["severity"],"BUDGET_AVAILABLE" if passed else f"BUDGET_AVAILABLE:{category['code']}","pass" if passed else "fail",f"Requested {category['requested']:.2f}; limit {category['budgeted']:.2f}",{"category":category["name"],"requested":f"{category['requested']:.2f}","limit":f"{category['budgeted']:.2f}","remaining":f"{category['remaining']:.2f}"}))
            if "TOTAL_RECONCILIATION" in rules:
                calculated=sum((row[4] for row in lines),Decimal("0.00"));control=Decimal(str(config["ledgerControlTotal"]));passed=calculated==invoice[3]==control
                results.append(_result("TOTAL_RECONCILIATION",rules["TOTAL_RECONCILIATION"]["severity"],"TOTAL_RECONCILED" if passed else "TOTAL_RECONCILIATION","pass" if passed else "fail",f"Invoice {invoice[3]:.2f}; lines {calculated:.2f}; control {control:.2f}",{"invoiceTotal":f"{invoice[3]:.2f}","lineTotal":f"{calculated:.2f}","controlTotal":f"{control:.2f}"}))
            if "POSSIBLE_DUPLICATE" in rules:
                window=int(rules["POSSIBLE_DUPLICATE"].get("dayWindow",1));tolerance=Decimal(str(rules["POSSIBLE_DUPLICATE"].get("amountTolerance","0.00")));duplicates=[]
                for index,left in enumerate(lines):
                    for right in lines[index+1:]:
                        if left[2]==right[2] and abs(left[4]-right[4])<=tolerance and abs((left[1]-right[1]).days)<=window:
                            duplicates.append((left,right))
                if duplicates:
                    for left,right in duplicates:
                        results.append(_result("POSSIBLE_DUPLICATE",rules["POSSIBLE_DUPLICATE"]["severity"],f"POSSIBLE_DUPLICATE:{right[0]}:{left[0]}","fail",f"{right[0]} may duplicate {left[0]}",{"left":left[0],"right":right[0],"vendor":left[2],"amountDifference":f"{abs(left[4]-right[4]):.2f}","dayDifference":abs((left[1]-right[1]).days),"tolerance":f"{tolerance:.2f}","window":window},right[0]))
                else:results.append(_result("POSSIBLE_DUPLICATE",rules["POSSIBLE_DUPLICATE"]["severity"],"NO_POSSIBLE_DUPLICATE","pass","No configured duplicate candidate",{"tolerance":f"{tolerance:.2f}","window":window}))
            stable_results=sorted(results,key=lambda item:(item["ruleCode"],item["expenseKey"] or "",item["reasonCode"]))
            run_id=f"validation-{uuid.uuid4().hex}";input_hash=_hash(normalized);output_hash=_hash(stable_results)
            snapshot=create_invoice_snapshot_tx(connection,actor,invoice_id,"validation")
            connection.validation.execute(Statement.VALIDATION_WRITE_VALIDATION_RUNS_004,(run_id,invoice_id,invoice[1],ENGINE_VERSION,json.dumps(normalized),input_hash,output_hash,actor.user_id,invoice[4],snapshot["id"]))
            append_relation_tx(connection,invoice[0],invoice[2],"validated_by",
                {"kind":"invoice_snapshot","id":snapshot["id"],"version":invoice[4],"sha256":snapshot["sha256"]},
                {"kind":"validation_run","id":run_id,"version":ENGINE_VERSION},actor=actor)
            for item in stable_results:
                result_id=f"result-{uuid.uuid4().hex}"
                connection.validation.execute(Statement.VALIDATION_WRITE_VALIDATION_RESULTS_005,(result_id,run_id,item["ruleCode"],item["ruleVersion"],item["severity"],item["reasonCode"],item["outcome"],item["expenseKey"],json.dumps(item["normalizedInput"]),item["message"]))
                if item["outcome"]=="fail":connection.validation.execute(Statement.VALIDATION_WRITE_VALIDATION_FINDINGS_006,(f"validation-finding-{uuid.uuid4().hex}",result_id,invoice_id,run_id,item["expenseKey"],item["reasonCode"],item["severity"],item["message"]))
            append_event_tx(connection,"validation_completed","validation_run",run_id,actor_id=actor.user_id,organization_id=invoice[2],contract_id=invoice[0],payload={"invoiceVersionId":invoice_id,"configurationVersionId":invoice[1],"engineVersion":ENGINE_VERSION,"inputHash":input_hash,"outputHash":output_hash,"invoiceSnapshotId":snapshot["id"]},version_references=[
                {"kind":"validation_run","id":run_id,"version":ENGINE_VERSION},
                {"kind":"invoice_snapshot","id":snapshot["id"],"version":invoice[4],"sha256":snapshot["sha256"]},
                {"kind":"invoice","id":invoice_id,"version":snapshot["payload"]["invoiceVersion"]},
                {"kind":"configuration","id":invoice[1],"version":invoice[1]},
            ])
            connection.commit()
        return get_validation(actor,run_id)
    return execute_authorized(actor,Action.CREATE,invoice_scope(actor,invoice_id),command)

def get_validation(actor:Actor,run_id:str)->dict:
    with database() as connection:
        run=connection.validation.execute(Statement.VALIDATION_READ_VALIDATION_RUNS_007,(run_id,)).fetchone()
        if not run:raise FileNotFoundError(run_id)
        require_permission(actor,Action.READ,invoice_scope(actor,run[1]))
        rows=connection.validation.execute(Statement.VALIDATION_READ_VALIDATION_RESULTS_008,(run_id,)).fetchall()
    return ValidationRunDto(id=run[0],invoice_version_id=run[1],configuration_version_id=run[2],engine_version=run[3],normalized_inputs=run[4],input_hash=run[5],output_hash=run[6],status=run[7],results=[{"ruleCode":r[0],"ruleVersion":r[1],"severity":r[2],"reasonCode":r[3],"outcome":r[4],"expenseKey":r[5],"normalizedInput":r[6],"message":r[7]} for r in rows]).model_dump(by_alias=True)

def latest_validation(actor:Actor,invoice_id:str)->dict|None:
    with database() as connection:row=connection.validation.execute(Statement.VALIDATION_READ_VALIDATION_RUNS_009,(invoice_id,)).fetchone()
    return get_validation(actor,row[0]) if row else None
