import type { ApprovalPreview, Attestation, GeneratedPackage, Submission } from "../domain/types";
import { ApprovalPanel } from "../features/approval/ApprovalPanel";

export function NgoApproverWorkspace(props: { preview: ApprovalPreview; attestation: Attestation | null; generatedPackage: GeneratedPackage | null; submission: Submission | null; message: string; onAttest: (text: string) => void; onGeneratePackage: () => void; onSubmit: () => void }) {
  return <ApprovalPanel {...props} />;
}
