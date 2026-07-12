import type { InvoiceDraft } from "../../domain/types";

const sumMoney = (values: string[]) => {
  const cents = values.reduce((sum, value) => {
    const [whole, fraction = "00"] = value.split(".");
    return (
      sum + BigInt(whole) * 100n + BigInt(fraction.padEnd(2, "0").slice(0, 2))
    );
  }, 0n);
  return `${cents / 100n}.${String(cents % 100n).padStart(2, "0")}`;
};
export function InvoiceDraftView({ draft }: { draft: InvoiceDraft }) {
  const budgeted = sumMoney(draft.categories.map((item) => item.limit));
  const remaining = sumMoney(draft.categories.map((item) => item.available));
  return (
    <div className="draft">
      <div className="draft-summary">
        <strong>Invoice v{draft.version}</strong>
        <span>Configuration {draft.configurationVersionId}</span>
        <b>${draft.total}</b>
      </div>
      <h3>Budget summary</h3>
      <div className="budget-total">
        <strong>Total requested ${draft.total}</strong>
        <span>Budgeted ${budgeted}</span>
        <span>Remaining ${remaining}</span>
      </div>
      <div className="category-grid">
        {draft.categories.map((item) => (
          <div key={item.name}>
            <strong>{item.name}</strong>
            <span>Requested ${item.claimed}</span>
            <span>Budgeted ${item.limit}</span>
            <span>Remaining ${item.available}</span>
          </div>
        ))}
      </div>
      <h3>Claimed expenses</h3>
      <div className="line-table">
        {draft.lines.map((line) => (
          <div key={line.expenseKey}>
            <strong>
              {line.expenseKey} · {line.vendor}
            </strong>
            <span>
              {line.category} · ${line.amount}
            </span>
            <span>Ledger: {line.ledgerSource}</span>
            <span>Extraction: {line.extractionStatus}</span>
            {line.evidenceArtifactId ? (
              <a
                href={`/api/artifacts/${line.evidenceArtifactId}`}
                target="_blank"
                rel="noreferrer"
              >
                Supporting evidence
              </a>
            ) : (
              <em>Evidence missing</em>
            )}
          </div>
        ))}
      </div>
      <h3>Unresolved findings</h3>
      {draft.findings.length === 0 ? (
        <p>No unresolved assembly findings.</p>
      ) : (
        <ul>
          {draft.findings.map((finding, index) => (
            <li key={`${finding.code}-${index}`}>
              <strong>{finding.code}</strong> {finding.expenseKey}:{" "}
              {finding.message}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
