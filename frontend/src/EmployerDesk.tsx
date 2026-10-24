import React, { useEffect, useState } from 'react';
import { Building2, CheckCircle2, Clock3, ShieldCheck } from 'lucide-react';

const API = 'http://localhost:5000/api';
async function call(path: string, options: RequestInit = {}) {
  const response = await fetch(API + path, { headers: { 'Content-Type': 'application/json' }, ...options });
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || 'Could not save this submission.');
  return data;
}

export default function EmployerDesk({ offline = false }: { offline?: boolean }) {
  const [items, setItems] = useState<any[]>([]);
  const [form, setForm] = useState({ organization: '', organization_type: 'Small or local business', contact_email: '', website: '', evidence_route: 'Shop or establishment license', role_title: '', location: '', description: '', pay_info: '', social_protection: '', growth_path: '', no_candidate_fee: false });
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  async function load() { try { setItems(await call('/employer/submissions')); } catch (e: any) { setError(e.message==='Failed to fetch'?'Local review queue is unavailable until the backend is running. Intake steps are still visible.':e.message); } }
  useEffect(() => { load(); }, []);
  function update(key: string, value: string | boolean) { setForm((old) => ({ ...old, [key]: value })); }
  async function submit(event: React.FormEvent) {
    event.preventDefault(); setSaving(true); setError(''); setResult(null);
    try { const response = await call('/employer/submissions', { method: 'POST', body: JSON.stringify(form) }); setResult(response); setForm({ organization: '', organization_type: 'Small or local business', contact_email: '', website: '', evidence_route: 'Shop or establishment license', role_title: '', location: '', description: '', pay_info: '', social_protection: '', growth_path: '', no_candidate_fee: false }); await load(); }
    catch (e: any) { setError(e.message); } finally { setSaving(false); }
  }
  return <>
    <div className="section-heading"><div className="eyebrow"><span className="eyebrow-dash"/>EMPLOYER INTAKE</div><h1>Share a role for careful review.</h1><p>Every employer submission stays private while its organization and vacancy details are checked. This local prototype cannot approve or publish a vacancy.</p></div>
    <div className="employer-layout"><form className="card-surface employer-form" onSubmit={submit}>
      <div className="employer-step"><span>01</span><div><b>Who is hiring?</b><small>We do not ask for Aadhaar, PAN, bank, GSTIN, or EPFO numbers.</small></div></div>
      <div className="employer-fields"><label>Organization name<input required maxLength={160} value={form.organization} onChange={e => update('organization',e.target.value)} placeholder="Registered or local business name"/></label><label>Organization type<select value={form.organization_type} onChange={e=>update('organization_type',e.target.value)}><option>Small or local business</option><option>Company</option><option>Nonprofit</option><option>Public organization</option><option>Authorized staffing partner</option></select></label><label>Work email<input required type="email" value={form.contact_email} onChange={e=>update('contact_email',e.target.value)} placeholder="you@organization.example"/></label><label>Website (optional)<input value={form.website} onChange={e=>update('website',e.target.value)} placeholder="organization.example"/></label></div>
      <label>Business evidence route<select value={form.evidence_route} onChange={e=>update('evidence_route',e.target.value)}><option>Udyam registration</option><option>Shop or establishment license</option><option>Local trade permit</option><option>Employer reference check</option><option>Authorization from the hiring organization</option><option>Other business evidence</option></select></label>
      <div className="employer-step employer-step-next"><span>02</span><div><b>Tell us about the vacancy</b><small>Clear responsibilities and real terms help candidates make informed choices.</small></div></div>
      <div className="employer-fields"><label>Role title<input required maxLength={160} value={form.role_title} onChange={e=>update('role_title',e.target.value)} placeholder="e.g. Junior Accounts Assistant"/></label><label>Location or work arrangement<input value={form.location} onChange={e=>update('location',e.target.value)} placeholder="Town, hybrid, remote…"/></label><label>Pay range or wage basis (optional)<input maxLength={180} value={form.pay_info} onChange={e=>update('pay_info',e.target.value)} placeholder="e.g. ₹18,000–22,000 per month"/></label><label>Social protection (optional)<input maxLength={180} value={form.social_protection} onChange={e=>update('social_protection',e.target.value)} placeholder="State PF, ESI, or not applicable"/></label><label className="employer-description">Growth or progression (optional)<input maxLength={240} value={form.growth_path} onChange={e=>update('growth_path',e.target.value)} placeholder="What could this role lead to?"/></label><label className="employer-description">Role description<textarea required minLength={30} maxLength={6000} rows={5} value={form.description} onChange={e=>update('description',e.target.value)} placeholder="Responsibilities, required skills, pay range if available, and application steps"/></label></div>
      <label className="fee-attestation"><input type="checkbox" checked={form.no_candidate_fee} onChange={e=>update('no_candidate_fee',e.target.checked)}/><span><b>No candidate fees</b><small>I confirm candidates will not be charged to apply, interview, complete mandatory training, buy a toolkit, or secure this role.</small></span></label>
      {error&&<p className="employer-error" role="alert">{error}</p>}{result&&<div className="employer-result" role="status"><Clock3 size={17}/><span><b>Submission #{result.id} · Pending review</b><small>{result.message}</small>{result.signals?.length>0&&<small>Safety signals to review: {result.signals.map((x:any)=>x.label).join(', ')}</small>}</span></div>}
      {offline&&<p className="employer-error" role="status">Offline mode is read-only for employers. Keep this form as a draft and submit when the service is reachable.</p>}
      <button className="btn-primary" disabled={saving||offline}>{offline?'Connect to submit for review':saving?'Sending for review…':'Submit for security review'} <ShieldCheck size={16}/></button>
    </form><aside className="employer-aside"><div className="employer-aside-icon"><Building2 size={21}/></div><h2>Fair checks for every employer.</h2><p>Small businesses can choose a local evidence route. GSTIN and EPFO records are not required here.</p><div className="employer-promise"><CheckCircle2/><span><b>No instant publishing</b><small>Submissions cannot enter candidate search directly.</small></span></div><div className="employer-promise"><CheckCircle2/><span><b>No candidate payment</b><small>Training, toolkit, placement, and onboarding fees are not allowed.</small></span></div><div className="employer-promise"><CheckCircle2/><span><b>Human review required</b><small>This prototype queues submissions but has no live reviewer integration.</small></span></div><div className="employer-queue"><b>Recent submissions on this device</b>{items.length?items.slice(0,5).map(x=><div key={x.id}><span>{x.role_title}<small>{x.organization}</small></span><i>{x.status}</i></div>):<small>No employer submissions yet.</small>}</div></aside></div>
  </>;
}
