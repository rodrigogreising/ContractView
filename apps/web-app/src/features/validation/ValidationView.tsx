import type { ValidationRunDto as ValidationRun } from "../../generated/contracts";

export function ValidationView({ validation }: { validation: ValidationRun }) {
  const findings = validation.results.filter((item) => item.outcome === "fail");
  return (
    <div className="validation">
      <div className="validation-meta">
        <strong>{validation.engineVersion}</strong>
        <span>Input {validation.inputHash.slice(0, 12)}</span>
        <span>Output {validation.outputHash.slice(0, 12)}</span>
      </div>
      <h3>Validation findings</h3>
      {findings.length === 0 ? (
        <p>All deterministic checks passed.</p>
      ) : (
        <ul>
          {findings.map((item) => (
            <li className={`finding-${item.severity}`} key={item.reasonCode}>
              <strong>
                {item.severity}: {item.reasonCode}
              </strong>
              <span>
                {item.ruleCode} · {item.ruleVersion}
              </span>
              <p>{item.message}</p>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
