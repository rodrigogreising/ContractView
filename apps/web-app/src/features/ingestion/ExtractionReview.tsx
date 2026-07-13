import { useState } from "react";
import type { Extraction } from "../../domain/types";
import { roleLabel } from "../../presentation/roleLabel";

export function ExtractionReview({
  extractions,
  onReview,
}: {
  extractions: Extraction[];
  onReview: (
    fieldId: string,
    decision: "accept" | "correct",
    value: string,
  ) => void;
}) {
  const [values, setValues] = useState<Record<string, string>>({});
  if (extractions.length === 0) return null;
  return (
    <section className="panel">
      <h2>Review proposed extraction</h2>
      <p>
        OCR output is draft-only. Compare every value with the source before
        accepting or correcting it.
      </p>
      {extractions.map((extraction) => (
        <article className="extraction" key={extraction.id}>
          <div className="extraction-head">
            <div>
              <strong>{extraction.filename}</strong>
              <small>
                {extraction.provider} · {extraction.model} ·{" "}
                {extraction.routingReason}
              </small>
              {extraction.profileVersion ? (
                <small className="runtime-reference">
                  Exact profile {extraction.profileVersion.profileKey} v{extraction.profileVersion.version} · configuration {extraction.configurationVersion?.id}@{extraction.configurationVersion?.version}
                </small>
              ) : (
                <small className="safe-route">
                  No profile assigned · {extraction.outcome || "needs_profile_review"} · no canonical expense created
                </small>
              )}
            </div>
            <a
              href={`/api/artifacts/${extraction.sourceArtifactId}`}
              target="_blank"
              rel="noreferrer"
            >
              View source evidence
            </a>
          </div>
          {extraction.fields.map((field) => {
            const current =
              values[field.id] ?? field.reviewedValue ?? field.proposedValue;
            return (
              <div className="field-review" key={field.id}>
                <label>
                  {roleLabel(field.name)}
                  <input
                    value={current}
                    disabled={field.reviewStatus !== "proposed"}
                    onChange={(event) =>
                      setValues({ ...values, [field.id]: event.target.value })
                    }
                  />
                </label>
                <span>Proposed: {field.proposedValue}</span>
                <span>
                  Confidence: {Math.round(Number(field.confidence) * 100)}%
                </span>
                <span>Source: {field.sourceLocation}</span>
                {field.reviewStatus === "proposed" ? (
                  <div>
                    <button
                      onClick={() =>
                        onReview(field.id, "accept", field.proposedValue)
                      }
                    >
                      Accept
                    </button>
                    <button
                      className="primary"
                      onClick={() => onReview(field.id, "correct", current)}
                    >
                      Correct
                    </button>
                  </div>
                ) : (
                  <strong>
                    {field.reviewStatus}: {field.reviewedValue}
                  </strong>
                )}
              </div>
            );
          })}
        </article>
      ))}
    </section>
  );
}
