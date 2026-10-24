import React, { useEffect, useState } from 'react';
import { AlertTriangle, ArrowUpRight, Building2, CheckCircle2, Clock3, ExternalLink, ShieldCheck } from 'lucide-react';

const API=(import.meta as any).env?.VITE_API_BASE||(location.hostname==='localhost'||location.hostname==='127.0.0.1'?'http://localhost:5000/api':'/api');
const STATIC_DEMO=(import.meta as any).env?.VITE_STATIC_DEMO==='true';
const emptyForm={organization:'',organization_type:'Small or local business',contact_email:'',website:'',evidence_route:'Shop or establishment license',role_title:'',location:'',description:'',pay_info:'',social_protection:'',growth_path:'',no_candidate_fee:false};
async function call(path:string,options:RequestInit={}){
 if(STATIC_DEMO)throw new Error('Employer submissions need the connected review service.');
 const response=await fetch(API+path,{headers:{'Content-Type':'application/json'},...options});
 const data=await response.json().catch(()=>({}));
 if(!response.ok){const error:any=new Error(data.error||'Could not complete this review step.');error.payload=data;throw error}
 return data;
}

export default function EmployerDesk({offline=false}:{offline?:boolean}){
 const [items,setItems]=useState<any[]>([]),[form,setForm]=useState(emptyForm),[assessment,setAssessment]=useState<any>(null),[result,setResult]=useState<any>(null),[error,setError]=useState(''),[saving,setSaving]=useState(false),[checking,setChecking]=useState(false);
 async function load(){if(STATIC_DEMO){setItems([]);return}try{setItems(await call('/employer/submissions'))}catch(e:any){setError(e.message==='Failed to fetch'?'The local review queue is unavailable until the backend is running.':e.message)}}
 useEffect(()=>{load()},[]);
 function update(key:string,value:string|boolean){setForm(old=>({...old,[key]:value}));setAssessment(null);setResult(null)}
 async function runPreflight(){setChecking(true);setError('');setResult(null);try{setAssessment(await call('/employer/preflight',{method:'POST',body:JSON.stringify(form)}))}catch(e:any){setError(e.message);if(e.payload)setAssessment(e.payload)}finally{setChecking(false)}}
 async function submit(event:React.FormEvent){event.preventDefault();setSaving(true);setError('');setResult(null);try{
   const check=await call('/employer/preflight',{method:'POST',body:JSON.stringify(form)});setAssessment(check);
   if(check.requires_changes){setError('Please revise or explain the highlighted items before submitting.');return}
   const response=await call('/employer/submissions',{method:'POST',body:JSON.stringify(form)});setResult(response);setForm({...emptyForm});setAssessment(null);await load();
  }catch(e:any){setError(e.message);if(e.payload)setAssessment(e.payload)}finally{setSaving(false)}}

 return <>
  <div className="section-heading"><div className="eyebrow"><span className="eyebrow-dash"/>EMPLOYER INTAKE</div><h1>Share a role for careful review.</h1><p>Use a staged process: check the details, correct warning signals, and wait for independent review. A submission is never published automatically.</p></div>
  <div className="employer-layout"><form className="card-surface employer-form" onSubmit={submit}>
   <div className="employer-step"><span>01</span><div><b>Who is hiring?</b><small>We do not require Aadhaar, PAN, bank, GSTIN, or EPFO numbers. Small and local businesses can use alternate evidence routes.</small></div></div>
   <div className="employer-fields"><label>Organization name<input required maxLength={160} value={form.organization} onChange={e=>update('organization',e.target.value)} placeholder="Registered or local business name"/></label><label>Organization type<select value={form.organization_type} onChange={e=>update('organization_type',e.target.value)}><option>Small or local business</option><option>Company</option><option>Nonprofit</option><option>Public organization</option><option>Authorized staffing partner</option></select></label><label>Work email<input required type="email" value={form.contact_email} onChange={e=>update('contact_email',e.target.value)} placeholder="you@organization.example"/></label><label>Website (optional)<input value={form.website} onChange={e=>update('website',e.target.value)} placeholder="organization.example"/></label></div>
   <label>Business evidence route<select value={form.evidence_route} onChange={e=>update('evidence_route',e.target.value)}><option>Udyam registration</option><option>Shop or establishment license</option><option>Local trade permit</option><option>Employer reference check</option><option>Authorization from the hiring organization</option><option>Other business evidence</option></select></label>
   <div className="employer-step employer-step-next"><span>02</span><div><b>Describe the real vacancy</b><small>Clear duties, location, pay terms, and hiring steps help candidates understand the offer.</small></div></div>
   <div className="employer-fields"><label>Role title<input required maxLength={160} value={form.role_title} onChange={e=>update('role_title',e.target.value)} placeholder="e.g. Junior Accounts Assistant"/></label><label>Location or work arrangement<input value={form.location} onChange={e=>update('location',e.target.value)} placeholder="Town, hybrid, remote…"/></label><label>Pay range or wage basis (optional)<input maxLength={180} value={form.pay_info} onChange={e=>update('pay_info',e.target.value)} placeholder="e.g. ₹18,000–22,000 per month"/></label><label>Social protection (optional)<input maxLength={180} value={form.social_protection} onChange={e=>update('social_protection',e.target.value)} placeholder="State PF, ESI, or not applicable"/></label><label className="employer-description">Growth or progression (optional)<input maxLength={240} value={form.growth_path} onChange={e=>update('growth_path',e.target.value)} placeholder="What could this role lead to?"/></label><label className="employer-description">Role description<textarea required minLength={30} maxLength={6000} rows={5} value={form.description} onChange={e=>update('description',e.target.value)} placeholder="Responsibilities, required skills, pay range if available, and application steps"/></label></div>
   <div className="employer-preflight-action"><span><b>03  Run the pre-submission check</b><small>Review signals before sending. No external authority lookup happens here.</small></span><button type="button" className="btn-outline" disabled={checking||offline||!form.organization.trim()||!form.contact_email.includes('@')||!form.role_title.trim()||form.description.trim().length<30} onClick={runPreflight}>{checking?'Checking…':'Check details'} <ShieldCheck size={15}/></button></div>
   <label className="fee-attestation"><input type="checkbox" required checked={form.no_candidate_fee} onChange={e=>update('no_candidate_fee',e.target.checked)}/><span><b>No candidate fees</b><small>I confirm candidates will not be charged to apply, interview, complete mandatory training, buy a toolkit, or secure this role.</small></span></label>
   {assessment&&<AssessmentView assessment={assessment}/>}
   {error&&<p className="employer-error" role="alert">{error}</p>}
   {result&&<div className="employer-result" role="status"><Clock3 size={17}/><span><b>Submission #{result.id} · Pending review</b><small>{result.message}</small>{typeof result.risk_score==='number'&&<small>Rule-based review score: {result.risk_score}/100 · not a fraud probability</small>}</span></div>}
   {offline&&<p className="employer-error" role="status">Offline mode is read-only for employers. This draft stays in this form; submit after the service reconnects.</p>}
   <button className="btn-primary" disabled={saving||offline}>{saving?'Running checks…':'Submit to the private review queue'} <ShieldCheck size={16}/></button>
  </form>
  <aside className="employer-aside"><div className="employer-aside-icon"><Building2 size={21}/></div><h2>A clear review path.</h2><p>Each stage shows what has and has not been checked. Only a connected authority result and an authorized reviewer could support a verified label.</p>
   <div className="review-pipeline"><div className="review-stage review-stage-current"><i>01</i><span><b>Employer submits details</b><small>Contact, business evidence route, and vacancy terms.</small></span></div><div className="review-stage"><i>02</i><span><b>Rule-based preflight</b><small>Explains matched wording and contact mismatches.</small></span></div><div className="review-stage"><i>03</i><span><b>Independent source checks</b><small>Not connected in this prototype. Official lookups below are manual.</small></span></div><div className="review-stage"><i>04</i><span><b>Human review and decision</b><small>No reviewer console is implemented; submissions remain private and pending.</small></span></div></div>
   <div className="authority-links"><b>Official lookup portals</b><small>These links are reference tools, not integrations. GST is optional and never required for local-business intake.</small><a href="https://www.udyamregistration.gov.in/Udyam_Verify.aspx" target="_blank" rel="noreferrer">Udyam registration lookup <ExternalLink size={12}/></a><a href="https://www.mca.gov.in/" target="_blank" rel="noreferrer">MCA company and LLP records <ExternalLink size={12}/></a><a href="https://tutorial.gst.gov.in/userguide/taxpayersdashboard/Search_Taxpayer.htm" target="_blank" rel="noreferrer">Optional GST taxpayer lookup <ExternalLink size={12}/></a></div>
   <div className="employer-promise"><CheckCircle2/><span><b>No instant publishing</b><small>A low rule score is not approval. Every role remains unpublished.</small></span></div><div className="employer-promise"><CheckCircle2/><span><b>No candidate payment</b><small>Fee and paid-training conditions are warning signals.</small></span></div>
   <div className="employer-queue"><b>Recent submissions in the local demo</b>{items.length?items.slice(0,5).map(x=><div key={x.id}><span>{x.role_title}<small>{x.organization}</small></span><i>{x.status}{typeof x.risk_score==='number'?` · ${x.risk_score}/100`:''}</i></div>):<small>No employer submissions yet.</small>}</div>
  </aside></div>
 </>;
}

function AssessmentView({assessment}:{assessment:any}){
 const blocked=assessment.requires_changes;
 return <section className={`employer-assessment ${blocked?'assessment-blocked':'assessment-review'}`} aria-live="polite">
  <div className="assessment-top"><span className="assessment-icon">{blocked?<AlertTriangle size={17}/>:<ShieldCheck size={17}/>}</span><div><b>{assessment.disposition}</b><small>Rule-based review score: {assessment.risk_score}/100 · not a fraud probability</small></div><span className="assessment-count">{assessment.signals?.length||0} signals</span></div>
  <p className="assessment-honesty">This checks text and supplied contact details only. It does not prove whether a company is genuine or a job is active.</p>
  {assessment.signals?.length>0&&<div className="assessment-list"><b>Signals to review</b>{assessment.signals.map((signal:any)=><p key={`${signal.label}-${signal.evidence}`}><AlertTriangle size={13}/><span>{signal.label}<small>Matched: “{signal.evidence}” · {signal.points} review points</small></span></p>)}</div>}
  <div className="assessment-list"><b>{blocked?'Changes to make':'Before this can be approved'}</b>{assessment.corrections?.map((item:string)=><p key={item}><CheckCircle2 size={13}/><span>{item}</span></p>)}</div>
  <div className="authority-status-list"><b>Independent checks</b>{assessment.authority_checks?.map((check:any)=><div key={check.name}><span><i/>{check.name}<small>{check.status} · {check.detail}</small></span>{check.sources?.map((source:any)=><a key={source.label} href={source.url} target="_blank" rel="noreferrer">{source.label}<ArrowUpRight size={11}/></a>)}</div>)}</div>
 </section>;
}
