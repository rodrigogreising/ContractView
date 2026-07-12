import { useState } from "react";
import type { Finding } from "../../domain/types";

export function FindingResolutionView({
  findings,
  onResolve,
}: {
  findings: Finding[];
  onResolve: (
    id: string,
    action: "correct" | "explain" | "dismiss",
    reason: string,
    correctionValue?: string,
  ) => void;
}) {
  const [reasons, setReasons] = useState<Record<string, string>>({});
  const [dates, setDates] = useState<Record<string, string>>({});
  if (findings.length === 0) return null;
  return (
    <div className="finding-resolution">
      <h3>Resolve findings</h3>
      {findings.map((item) => (
        <article
          key={item.id}
          className={`finding-card finding-${item.severity}`}
        >
          <strong>
            {item.severity}: {item.code}
          </strong>
          <span>Affected line: {item.expenseKey || "invoice"}</span>
          <p>{item.message}</p>
          <p>
            <b>Remediation:</b> {item.remediation}
          </p>
          <pre>{JSON.stringify(item.normalizedInput, null, 2)}</pre>
          {item.evidenceArtifactId && (
            <a
              href={`/api/artifacts/${item.evidenceArtifactId}`}
              target="_blank"
              rel="noreferrer"
            >
              View affected evidence
            </a>
          )}
          {item.status === "open" && (
            <>
              <label>
                Resolution reason
                <input
                  value={reasons[item.id] || ""}
                  onChange={(event) =>
                    setReasons({ ...reasons, [item.id]: event.target.value })
                  }
                />
              </label>
              {item.severity === "blocker" ? (
                <>
                  <label>
                    Corrected service date
                    <input
                      type="date"
                      value={dates[item.id] || ""}
                      onChange={(event) =>
                        setDates({ ...dates, [item.id]: event.target.value })
                      }
                    />
                  </label>
                  <button
                    className="primary"
                    onClick={() =>
                      onResolve(
                        item.id,
                        "correct",
                        reasons[item.id] || "",
                        dates[item.id],
                      )
                    }
                  >
                    Correct and revalidate
                  </button>
                </>
              ) : (
                <div>
                  <button
                    onClick={() =>
                      onResolve(item.id, "explain", reasons[item.id] || "")
                    }
                  >
                    Explain warning
                  </button>
                  <button
                    className="primary"
                    onClick={() =>
                      onResolve(item.id, "dismiss", reasons[item.id] || "")
                    }
                  >
                    Dismiss and revalidate
                  </button>
                </div>
              )}
            </>
          )}
        </article>
      ))}
    </div>
  );
}
