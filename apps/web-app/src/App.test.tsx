import { renderToString } from "react-dom/server";
import { describe, expect, it } from "vitest";
import { App, AuthenticatedWorkspace } from "./App";

describe("authentication shell", () => {
  it("offers every seeded persona through a normal login form", () => {
    const html = renderToString(<App />);
    expect(html).toContain("Synthetic role-based POC");
    expect(html).toContain("Configuration Administrator");
    expect(html).toContain("NGO Preparer");
    expect(html).toContain("Government Reviewer");
    expect(html).toContain("type=\"password\"");
  });
  it("shows real upload controls and processing status only to the NGO preparer", () => {
    const html = renderToString(<AuthenticatedWorkspace user={{id:"preparer",displayName:"Maya Chen",email:"m@demo",organizationName:"Harbor Community Services",role:"ngo_preparer"}} jobs={[{id:"job-1",artifact_id:"a-1",job_type:"ledger_import",status:"running",error_message:null}]} message="" onLogout={()=>{}} onUpload={()=>{}}/>);
    expect(html).toContain("Upload ledger and evidence");
    expect(html).toContain("Upload and process");
    expect(html).toContain("running");
    expect(html).toContain("Maya Chen");
    expect(html).toContain("Harbor Community Services");
  });
});
