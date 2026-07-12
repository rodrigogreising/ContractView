import { useState } from "react";
import type { InvoiceDraft, RevisionFeedback } from "../../domain/types";

export function RevisionFeedbackPanel({
  feedback,
  draft,
  onCorrect,
}: {
  feedback: RevisionFeedback;
  draft: InvoiceDraft;
  onCorrect: (expenseKey: string, description: string, reason: string) => void;
}) {
  const expenseKey = feedback.lineKeys[0] || draft.lines[0]?.expenseKey || "";
  const source = draft.lines.find((line) => line.expenseKey === expenseKey);
  const [description, setDescription] = useState(
    source?.description || "Corrected per government feedback",
  );
  return (
    <section className="panel feedback-panel">
      <h2>Government feedback on version 1</h2>
      <strong>{feedback.reasonCode}</strong>
      <p>{feedback.note}</p>
      <p>
        Immutable predecessor: {feedback.predecessorInvoiceVersionId} · Editable
        invoice v{draft.version}
      </p>
      <label>
        Corrected description for {expenseKey}
        <input
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />
      </label>
      <button
        className="primary"
        onClick={() =>
          onCorrect(expenseKey, description, "Resolved government feedback")
        }
      >
        Apply correction to version {draft.version}
      </button>
    </section>
  );
}
