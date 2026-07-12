import { useEffect, useState } from "react";
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
  const expenseKey = feedback.lineKeys[0] || "";
  const source = draft.lines.find((line) => line.expenseKey === expenseKey);
  const [description, setDescription] = useState(source?.description || "");
  useEffect(() => {
    setDescription(source?.description || "");
  }, [expenseKey, source?.description]);
  return (
    <section className="panel feedback-panel">
      <h2>Government feedback on version 1</h2>
      <strong>{feedback.reasonCode}</strong>
      <p>{feedback.note}</p>
      <p>Exact returned lines: {feedback.lineKeys.join(", ") || "none"}</p>
      <p>
        Immutable predecessor: {feedback.predecessorInvoiceVersionId} · Editable
        invoice v{draft.version}
      </p>
      {!source && (
        <p role="alert">
          No correctable returned line is present on this editable revision.
        </p>
      )}
      <label>
        Corrected description for {expenseKey}
        <input
          value={description}
          onChange={(event) => setDescription(event.target.value)}
        />
      </label>
      <button
        className="primary"
        disabled={!source || !description.trim()}
        onClick={() =>
          onCorrect(expenseKey, description, "Resolved government feedback")
        }
      >
        Apply correction to version {draft.version}
      </button>
    </section>
  );
}
