import { FormEvent, useCallback, useEffect, useState } from "react";
type User = { id: string; displayName: string; email: string; organizationName: string; role: string };
type Job = { id:string; artifact_id:string; job_type:string; status:"queued"|"running"|"completed"|"failed"; error_message:string|null };
const CONTRACT_ID = "contract-metro-harbor-2026";
const personas = [
  ["Configuration Administrator", "Alex Morgan", "config.admin@contractview.demo", "Demo-Config-2026!"],
  ["NGO Preparer", "Maya Chen", "ngo.preparer@contractview.demo", "Demo-Prepare-2026!"],
  ["NGO Approver", "Jordan Ellis", "ngo.approver@contractview.demo", "Demo-Approve-2026!"],
  ["Government Reviewer", "Samira Patel", "government.reviewer@contractview.demo", "Demo-Review-2026!"],
  ["Auditor", "Noah Williams", "auditor@contractview.demo", "Demo-Audit-2026!"],
] as const;
const roleLabel = (role: string) => role.split("_").map(word => word[0].toUpperCase() + word.slice(1)).join(" ");
export function App() {
  const [user, setUser] = useState<User | null>(null);
  const [email, setEmail] = useState(""); const [password, setPassword] = useState("");
  const [message, setMessage] = useState("Checking session…");
  const [jobs, setJobs] = useState<Job[]>([]);
  const refreshJobs = useCallback(async () => {
    const response = await fetch(`/api/ingestion/jobs?contractId=${CONTRACT_ID}`);
    if (response.ok) setJobs((await response.json()).jobs);
  }, []);
  useEffect(() => { fetch("/api/auth/me").then(async r => { if (!r.ok) throw new Error(); setUser((await r.json()).user); setMessage(""); }).catch(() => setMessage("Choose a persona to begin.")); }, []);
  useEffect(() => {
    if (user?.role !== "ngo_preparer") return;
    refreshJobs(); const timer = window.setInterval(refreshJobs, 500); return () => window.clearInterval(timer);
  }, [user, refreshJobs]);
  async function login(event: FormEvent) { event.preventDefault(); setMessage("Signing in…"); const response = await fetch("/api/auth/login", {method:"POST", headers:{"content-type":"application/json"}, body:JSON.stringify({email,password})}); if (!response.ok) { setMessage("Invalid email or password."); return; } setUser((await response.json()).user); setMessage(""); }
  async function logout() { await fetch("/api/auth/logout", {method:"POST"}); setUser(null); setEmail(""); setPassword(""); setMessage("Signed out. Choose a persona to continue."); }
  async function upload(event: FormEvent<HTMLFormElement>) { event.preventDefault(); const form = event.currentTarget; const data = new FormData(form); data.set("contractId", CONTRACT_ID); setMessage("Uploading and queueing…"); const response = await fetch("/api/ingestion/uploads", {method:"POST", body:data}); const result = await response.json(); if (!response.ok) { setMessage(result.detail || "Upload failed"); return; } setMessage("Upload queued for real background processing."); form.reset(); await refreshJobs(); }
  if (user) return <AuthenticatedWorkspace user={user} jobs={jobs} message={message} onLogout={logout} onUpload={upload}/>;
  return <main><p className="eyebrow">Synthetic role-based POC</p><h1>Sign in</h1><p className="summary">Select a seeded persona. The card fills credentials; the normal server login still runs.</p><div className="persona-grid">{personas.map(([role,name,personaEmail,personaPassword]) => <button className="persona" key={role} onClick={() => {setEmail(personaEmail);setPassword(personaPassword)}}><strong>{role}</strong><span>{name}</span></button>)}</div><form onSubmit={login}><label>Email<input value={email} onChange={e=>setEmail(e.target.value)} type="email" required/></label><label>Password<input value={password} onChange={e=>setPassword(e.target.value)} type="password" required/></label><button className="primary" type="submit">Sign in</button></form><p aria-live="polite">{message}</p></main>;
}

export function AuthenticatedWorkspace({user,jobs,message,onLogout,onUpload}:{user:User;jobs:Job[];message:string;onLogout:()=>void;onUpload:(event:FormEvent<HTMLFormElement>)=>void}) {
  return <><header className="identity"><div><strong>{user.displayName}</strong><span>{user.organizationName}</span></div><span className="role-badge">{roleLabel(user.role)}</span><button onClick={onLogout}>Log out</button></header><main><p className="eyebrow">Synthetic role-based POC</p><h1>Workspace</h1><p className="summary">Your navigation and available actions are scoped to the signed-in persona. The API enforces the same boundaries independently.</p>{user.role === "ngo_preparer" && <section className="panel"><h2>Upload ledger and evidence</h2><p>CSV, XLSX, PDF, PNG, or JPEG. Maximum 10 MB each.</p><form onSubmit={onUpload}><label>Evidence file<input name="file" type="file" accept=".csv,.xlsx,.pdf,.png,.jpg,.jpeg" required/></label><button className="primary" type="submit">Upload and process</button></form><p aria-live="polite">{message}</p><h3>Processing jobs</h3>{jobs.length === 0 ? <p>No uploads yet.</p> : <ul className="jobs">{jobs.map(job=><li key={job.id}><span>{job.job_type === "ledger_import" ? "Ledger import" : "Evidence extraction"}</span><strong className={`job-${job.status}`}>{job.status}</strong>{job.error_message && <small>{job.error_message}</small>}</li>)}</ul>}</section>}</main></>;
}
