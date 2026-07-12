import type { ContractContextDto } from "../generated/contracts";

export function ContractSelector({ contexts, value, onChange }: { contexts: ContractContextDto[]; value: string; onChange: (contractId: string) => void }) {
  return <label className="contract-selector">Contract<select aria-label="Authorized contract" value={value} onChange={(event) => onChange(event.target.value)}>{contexts.map((context) => <option key={context.contractId} value={context.contractId}>{context.contractName}</option>)}</select></label>;
}
