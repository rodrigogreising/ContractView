export type DemoPersona = readonly [string, string, string, string];

export const demoMode =
  import.meta.env.MODE === "test" ||
  import.meta.env.VITE_CONTRACTVIEW_DEMO_MODE === "true";

export const demoPersonas: readonly DemoPersona[] = demoMode
  ? [
      ["Configuration Administrator", "Synthetic Configuration Administrator", "configuration.admin@example.test", "Demo-Config-2026!"],
      ["NGO Preparer", "Synthetic NGO Preparer", "ngo.preparer@example.test", "Demo-Prepare-2026!"],
      ["NGO Approver", "Synthetic NGO Approver", "ngo.approver@example.test", "Demo-Approve-2026!"],
      ["Government Reviewer", "Synthetic Government Reviewer", "government.reviewer@example.test", "Demo-Review-2026!"],
      ["Auditor", "Synthetic Auditor", "auditor@example.test", "Demo-Audit-2026!"],
    ]
  : [];
