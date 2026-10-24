from datetime import datetime, timedelta
import re, json, os
from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('CAREERTRUST_DATABASE_URI', 'sqlite:///careertrust.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
allowed_origins=[origin.strip() for origin in os.environ.get('CAREERTRUST_ALLOWED_ORIGINS','http://localhost:5173').split(',') if origin.strip()]
CORS(app, origins=allowed_origins)
db = SQLAlchemy(app)

class Candidate(db.Model):
    id=db.Column(db.Integer, primary_key=True); name=db.Column(db.String(100), default='Aarav Mehta'); goal=db.Column(db.String(120), default='Junior Data Analyst'); location=db.Column(db.String(100), default='Pune'); skills=db.Column(db.Text, default='{}'); evidence=db.Column(db.Text, default='[]'); profile_extra=db.Column(db.Text, default='{}')
class Job(db.Model):
    id=db.Column(db.Integer, primary_key=True); title=db.Column(db.String(160)); employer=db.Column(db.String(140)); location=db.Column(db.String(100)); work=db.Column(db.String(40)); required=db.Column(db.Text); preferred=db.Column(db.Text); description=db.Column(db.Text); email=db.Column(db.String(160)); domain=db.Column(db.String(160)); source=db.Column(db.String(100)); scam_label=db.Column(db.Boolean, default=False); status=db.Column(db.String(40), default='Active'); updated=db.Column(db.DateTime, default=datetime.utcnow); saved=db.Column(db.Boolean, default=False); pay_info=db.Column(db.String(180), default=''); social_protection=db.Column(db.String(180), default=''); growth_path=db.Column(db.String(240), default='')
class Application(db.Model):
    id=db.Column(db.Integer, primary_key=True); job_id=db.Column(db.Integer, db.ForeignKey('job.id')); status=db.Column(db.String(40), default='Saved'); notes=db.Column(db.Text, default=''); created=db.Column(db.DateTime, default=datetime.utcnow); follow_up=db.Column(db.String(30), default=''); feedback=db.Column(db.String(240), default='')
class EmployerSubmission(db.Model):
    id=db.Column(db.Integer, primary_key=True); organization=db.Column(db.String(160)); organization_type=db.Column(db.String(50)); contact_email=db.Column(db.String(200)); website=db.Column(db.String(200)); evidence_route=db.Column(db.String(80)); role_title=db.Column(db.String(160)); location=db.Column(db.String(120)); description=db.Column(db.Text); status=db.Column(db.String(40), default='Pending review'); signals=db.Column(db.Text, default='[]'); created=db.Column(db.DateTime, default=datetime.utcnow); pay_info=db.Column(db.String(180), default=''); social_protection=db.Column(db.String(180), default=''); growth_path=db.Column(db.String(240), default='')
class Task(db.Model):
    id=db.Column(db.Integer, primary_key=True); skill=db.Column(db.String(80)); title=db.Column(db.String(180)); day=db.Column(db.Integer); duration=db.Column(db.Integer); status=db.Column(db.String(30), default='Planned'); evidence=db.Column(db.Text, default='')
class InterviewPrompt(db.Model):
 id=db.Column(db.Integer, primary_key=True); job_id=db.Column(db.Integer, db.ForeignKey('job.id')); question=db.Column(db.Text); basis=db.Column(db.String(180)); evidence=db.Column(db.String(240)); answer=db.Column(db.Text, default=''); completed=db.Column(db.Boolean, default=False); created=db.Column(db.DateTime, default=datetime.utcnow)
class ResumeVersion(db.Model):
 id=db.Column(db.Integer, primary_key=True); job_id=db.Column(db.Integer, db.ForeignKey('job.id')); title=db.Column(db.String(160)); content=db.Column(db.Text); redacted=db.Column(db.Boolean, default=True); created=db.Column(db.DateTime, default=datetime.utcnow)
class Disclosure(db.Model):
 id=db.Column(db.Integer, primary_key=True); resume_id=db.Column(db.Integer, db.ForeignKey('resume_version.id')); recipient=db.Column(db.String(160)); fields=db.Column(db.Text); consent=db.Column(db.Boolean, default=False); created=db.Column(db.DateTime, default=datetime.utcnow)
class TrustReport(db.Model):
 id=db.Column(db.Integer, primary_key=True); kind=db.Column(db.String(40)); details=db.Column(db.Text); status=db.Column(db.String(40), default='Received'); created=db.Column(db.DateTime, default=datetime.utcnow)

ALIASES={'python':'python','sql':'sql','power bi':'power bi','powerbi':'power bi','data visualization':'visualization','excel':'excel','communication':'communication','statistics':'statistics','pandas':'pandas','problem solving':'problem solving'}
def norm(s): return ALIASES.get(s.lower().strip(), s.lower().strip())
def jskills(j): return json.loads(j.required)
def get_candidate():
    c=Candidate.query.first()
    if not c:
        c=Candidate(); db.session.add(c); db.session.commit()
    return c
def match(j, c=None):
    c=c or get_candidate(); skills=json.loads(c.skills); ev=json.loads(c.evidence); req=jskills(j); pref=json.loads(j.preferred)
    # Each requirement carries equal weight within its mandatory/preferred bucket; evidence status discounts self-report.
    rows=[]; points=0; total=len(req)*2+len(pref)
    for s in req+pref:
        key=norm(s); level=float(skills.get(key,0)); record=next((x for x in ev if norm(x.get('skill',''))==key),None)
        credit=min(1,level/3) if level else 0
        if record and record.get('status')=='Demonstrated': credit=min(1,credit+0.25)
        wt=2 if s in req else 1; points+=credit*wt
        rows.append({'skill':s,'type':'Required' if s in req else 'Preferred','status':record.get('status','Not demonstrated') if record else 'Not demonstrated','evidence':record.get('source') if record else None,'score':round(credit*100)})
    return {'score':round(points/total*100) if total else 0,'requirements':rows,'supported':[r['skill'] for r in rows if r['score']>0], 'gaps':[r['skill'] for r in rows if r['score']==0]}
def serialize_job(j):
    m=match(j)
    age=max(0,(datetime.utcnow()-j.updated).days)
    freshness='Recent demo listing date' if age<=7 else ('Confirmation due soon' if age<=14 else 'Employer reconfirmation needed')
    if j.status=='Needs confirmation': freshness='Paused · employer reconfirmation needed'
    return {'id':j.id,'title':j.title,'employer':j.employer,'location':j.location,'work':j.work,'required':jskills(j),'age_days':age,'freshness':freshness,'pay_info':j.pay_info or '','social_protection':j.social_protection or '','growth_path':j.growth_path or '', 'preferred':json.loads(j.preferred),'description':j.description,'email':j.email,'domain':j.domain,'source':j.source,'status':j.status,'updated':j.updated.isoformat()+'Z','saved':j.saved,'match':m}
def seed():
    db.create_all()
    # Keep existing local demo databases usable when profile and feedback fields are added.
    with db.engine.begin() as connection:
        for table, column, definition in [('candidate','profile_extra',"TEXT DEFAULT '{}'"),('application','feedback',"VARCHAR(240) DEFAULT ''"),('job','pay_info',"VARCHAR(180) DEFAULT ''"),('job','social_protection',"VARCHAR(180) DEFAULT ''"),('job','growth_path',"VARCHAR(240) DEFAULT ''"),('employer_submission','pay_info',"VARCHAR(180) DEFAULT ''"),('employer_submission','social_protection',"VARCHAR(180) DEFAULT ''"),('employer_submission','growth_path',"VARCHAR(240) DEFAULT ''")]:
            existing={row[1] for row in connection.exec_driver_sql(f'PRAGMA table_info({table})')}
            if column not in existing: connection.exec_driver_sql(f'ALTER TABLE {table} ADD COLUMN {column} {definition}')
    if not Candidate.query.first():
        db.session.add(Candidate(skills=json.dumps({'python':2,'sql':2,'pandas':2,'excel':1,'problem solving':2,'communication':1}), evidence=json.dumps([{'skill':'Python','status':'Demonstrated','source':'Exploratory Data Analysis project'},{'skill':'SQL','status':'Self-reported','source':'Coursework: SQL fundamentals'},{'skill':'Pandas','status':'Demonstrated','source':'Exploratory Data Analysis project'},{'skill':'Problem solving','status':'Self-reported','source':'Candidate profile'}])))
    if not Job.query.first():
        base=[('Junior Data Analyst','Northstar Analytics','Python,SQL,Excel','Power BI,Communication','Careers','careers.northstar.example','jobs@northstar.example'),('Reporting Analyst','Cedar Labs','SQL,Excel,Power BI','Python,Communication','Company site','cedarlabs.example','talent@cedarlabs.example'),('Graduate Data Associate','Riverstone Insights','Python,Statistics,SQL','Pandas,Visualization','NCS demo feed','ncs.example','recruit@riverstone.example'),('Data Operations Associate','BrightPath Systems','SQL,Excel','Python,Communication','Company site','brightpath.example','people@brightpath.example'),('Junior BI Analyst','Orbit Retail','Power BI,SQL,Visualization','Excel,Python','Partner feed','orbit-retail.example','careers@orbit-retail.example'),('Data Trainee','Acorn Metrics','Python,Statistics','Pandas,SQL','Company site','acornmetrics.example','jobs@acornmetrics.example')]
        for i in range(40):
            b=base[i%len(base)]; scam=i in [6,13,19,25,31,37]; title,emp,req,pref,source,domain,email=b
            if scam:
                emp='Northstar Analytics'; title='Junior Data Analyst'; req='Python,SQL,Excel'; pref='Power BI,Communication'; source='Unverified repost'; domain='northstar-careers-pay.example' if i%2 else 'quickhire.example'; email='apply.fastjobs@gmail.com'; desc='Pay a refundable registration fee before your interview. Guaranteed placement this week. Send bank and identity details immediately.'
            else: desc='Support reporting and analysis using '+req+'. Collaborate with a small team and communicate findings. Candidates do not pay hiring charges.'
            db.session.add(Job(title=title,employer=emp,location=['Pune','Bengaluru','Remote'][i%3],work=['Hybrid','On-site','Remote'][i%3],required=json.dumps([x.strip() for x in req.split(',')]),preferred=json.dumps([x.strip() for x in pref.split(',')]),description=desc,email=email,domain=domain,source=source,scam_label=scam,updated=datetime.utcnow()-timedelta(days=i%18)))
        db.session.commit()
    if not Task.query.first():
        for i,(sk,title,day,dur) in enumerate([('Power BI','Build a small KPI dashboard',1,6),('Excel','Practice pivot tables and lookups',7,4),('Statistics','Review descriptive statistics',12,5),('SQL','Write joins and window queries',18,6),('Communication','Present a one page insight brief',25,4)]): db.session.add(Task(skill=sk,title=title,day=day,duration=dur))
        db.session.commit()

@app.get('/api/health')
def health(): return jsonify({'status':'ok','product':'CareerTrust'})
@app.get('/api/profile')
def profile():
 c=get_candidate(); return jsonify({'name':c.name,'goal':c.goal,'location':c.location,'skills':json.loads(c.skills),'evidence':json.loads(c.evidence),**json.loads(c.profile_extra or '{}')})
@app.put('/api/profile')
def update_profile():
 c=get_candidate(); data=request.get_json() or {}; c.name=str(data.get('name',c.name))[:100]; c.goal=str(data.get('goal',c.goal))[:120]; c.location=str(data.get('location',c.location))[:100]
 if isinstance(data.get('skills'),dict): c.skills=json.dumps({norm(str(k)):max(0,min(3,float(v))) for k,v in data['skills'].items()})
 if isinstance(data.get('evidence'),list): c.evidence=json.dumps(data['evidence'])
 extra=json.loads(c.profile_extra or '{}')
 for key,limit in [('college',160),('education',100),('language',40)]:
  if key in data: extra[key]=str(data[key])[:limit]
 c.profile_extra=json.dumps(extra)
 db.session.commit(); return profile()
def pause_stale_vacancies():
 now=datetime.utcnow(); changed=False
 for j in Job.query.filter_by(status='Active').all():
  if (now-j.updated).days>14: j.status='Needs confirmation'; changed=True
 if changed: db.session.commit()

@app.get('/api/jobs')
def jobs():
 pause_stale_vacancies()
 q=request.args.get('q','').lower(); rows=[serialize_job(j) for j in Job.query.all() if j.status=='Active']; rows=[x for x in rows if q in (x['title']+' '+x['employer']+' '+x['location']).lower()]; rows.sort(key=lambda x:x['match']['score'],reverse=True); return jsonify(rows)
@app.get('/api/jobs/<int:jid>')
def job_detail(jid):
 pause_stale_vacancies(); j=Job.query.get_or_404(jid); return jsonify(serialize_job(j))
@app.post('/api/jobs/<int:jid>/save')
def save_job(jid):
 j=Job.query.get_or_404(jid); pause_stale_vacancies()
 if j.status!='Active': return jsonify({'error':'This vacancy is paused until its employer confirms it is still open.'}),409
 j.saved=not j.saved; db.session.commit(); return jsonify({'saved':j.saved})
@app.post('/api/applications')
def apply():
 d=request.get_json() or {}; j=Job.query.get_or_404(d.get('job_id')); pause_stale_vacancies()
 if j.status!='Active': return jsonify({'error':'This vacancy is paused until its employer confirms it is still open.'}),409
 old=Application.query.filter_by(job_id=j.id).first()
 if old: return jsonify({'error':'An application for this demo listing already exists','application_id':old.id}),409
 a=Application(job_id=j.id,status='Applied',notes=str(d.get('notes',''))[:1000]); db.session.add(a); db.session.commit(); return jsonify({'id':a.id,'status':a.status}),201
@app.get('/api/applications')
def applications():
 return jsonify([{'id':a.id,'job_id':a.job_id,'job':Job.query.get(a.job_id).title,'employer':Job.query.get(a.job_id).employer,'status':a.status,'notes':a.notes,'created':a.created.isoformat(),'follow_up':a.follow_up,'feedback':a.feedback or 'Employer feedback not provided'} for a in Application.query.order_by(Application.created.desc()).all()])
@app.patch('/api/applications/<int:aid>')
def update_application(aid):
 a=Application.query.get_or_404(aid); d=request.get_json() or {}; allowed={'Saved','Planned','Applied','Assessment','Interview','Rejected','Offer','Withdrawn','Closed'}
 if d.get('status') not in allowed: return jsonify({'error':'Unsupported status'}),400
 a.status=d['status']; a.notes=str(d.get('notes',a.notes))[:1000]; a.follow_up=str(d.get('follow_up',a.follow_up))[:30]; a.feedback=str(d.get('feedback',a.feedback))[:240]; db.session.commit(); return jsonify({'id':a.id,'status':a.status})
@app.get('/api/roadmap')
def roadmap(): return jsonify([{'id':t.id,'skill':t.skill,'title':t.title,'day':t.day,'duration':t.duration,'status':t.status,'evidence':t.evidence} for t in Task.query.order_by(Task.day).all()])
@app.patch('/api/roadmap/<int:tid>')
def update_task(tid):
 t=Task.query.get_or_404(tid); d=request.get_json() or {}; state=d.get('status')
 if state not in ['Planned','Started','Completed']: return jsonify({'error':'Unsupported task status'}),400
 t.status=state; t.evidence=str(d.get('evidence',''))[:1000]; db.session.commit(); return jsonify({'id':t.id,'status':t.status,'note':'Completion does not establish skill mastery; add evidence to update your profile.'})
def assess(text,employer='',email='',domain='',url=''):
 signals=[]; low=text.lower()
 for words,label,pts in [(['registration fee','recruitment fee','pay a fee','fee to apply','fees to apply','processing fee','refundable fee','placement fee','job placement fee','training fee','training-kit fee','training kit fee','toolkit fee','buy a toolkit','purchase a toolkit','training kit required','paid training','onboarding fee','onboarding charge','onboarding deposit','security deposit','deposit to apply','deposit to secure','upfront payment','pay before interview','pay for interview','pay to secure','equipment fee','work kit fee','mandatory paid training','mandatory course payment','pay for training'],'Upfront payment or paid-training condition',35),(['guaranteed placement','guaranteed job','guaranteed offer'],'Unusually certain job guarantee',20),(['immediately','within 24 hours','act now','urgent'],'Pressure language',10),(['bank details','bank account','account number','identity details','government id','send your aadhaar','aadhaar number','aadhar number','pan number','send your pan','passport scan','upload id','upi pin','one time password','password',' otp '],'Sensitive information requested early',20)]:
  found=None
  for w in words:
   pos=low.find(w)
   if pos<0: continue
   prefix=low[max(0,pos-48):pos]
   if re.search(r"(?:\bno|\bnot|\bnever|\bwithout|\bdoes not|\bdo not|\bwill not|\bdon't|\bdoesn't)\s+(?:[\w'-]+\s+){0,2}$",prefix): continue
   found=w; break
  if found: signals.append({'label':label,'evidence':found,'points':pts})
 j=None
 if domain:
  j=Job.query.filter_by(domain=domain).first()
  if not j: signals.append({'label':'Domain not in demo reference records','evidence':domain,'points':10})
 if email and '@' in email and domain and email.rsplit('@',1)[-1].lower()!=domain.lower(): signals.append({'label':'Email domain differs from supplied domain','evidence':email+' vs '+domain,'points':15})
 dup=Job.query.filter(Job.description.contains('Pay a refundable registration fee')).first() if ('registration fee' in low or 'guaranteed placement' in low) else None
 if dup: signals.append({'label':'Text resembles a labelled synthetic demo clone','evidence':'Similar wording appears in synthetic listing #'+str(dup.id),'points':20})
 score=min(100,sum(x['points'] for x in signals)); tier='High-risk indicators detected' if score>=50 else ('Verification recommended' if score>=20 else ('Unable to verify' if not domain and not email else 'Lower observed risk'))
 return {'tier':tier,'score':score,'signals':signals,'verification':'Domain checked only against fictional local demo references; no live verification performed.','precautions':['Never pay to apply or secure an interview.','Verify the vacancy through an independently located official channel.','Share sensitive identity or bank information only through a verified hiring process.'],'comparison':({'id':dup.id,'title':dup.title,'employer':dup.employer,'source':dup.source} if dup else None),'disclaimer':'A warning is not proof of fraud. Demo scores are transparent rule totals, not calibrated probabilities.'}
@app.post('/api/trust')
def trust():
 d=request.get_json() or {}; j=Job.query.get(d.get('job_id')) if d.get('job_id') else None
 text=str(d.get('text',j.description if j else ''))[:12000]; employer=str(d.get('employer',j.employer if j else ''))[:160]; email=str(d.get('email',j.email if j else ''))[:200]; domain=str(d.get('domain',j.domain if j else ''))[:200]
 return jsonify(assess(text,employer,email,domain,str(d.get('url',''))))
@app.post('/api/fairness')
def fairness():
 c=get_candidate(); results=[]
 attrs=[('Name','name','Maya Rao'),('Gender-related name signal','name','Aditi Sharma'),('College tier','college_tier','Tier 1'),('Location proxy','location','Delhi'),('Career gap metadata','career_gap','0 months')]
 base={j.id:match(j,c)['score'] for j in Job.query.limit(8).all()}
 for label,key,val in attrs:
  # Same scoring engine; irrelevant metadata isn't consumed by the scoring function.
  variant=Candidate(name=val,goal=c.goal,location=(val if key=='location' else c.location),skills=c.skills,evidence=c.evidence)
  scores={j.id:match(j,variant)['score'] for j in Job.query.limit(8).all()}; gaps=[abs(scores[k]-v) for k,v in base.items()]
  results.append({'attribute':label,'baseline':round(sum(base.values())/max(1,len(base)),1),'modified':round(sum(scores.values())/max(1,len(scores)),1),'max_gap':max(gaps,default=0),'should_influence':False,'flagged':max(gaps,default=0)>0})
 return jsonify({'tests':results,'scope':'Controlled counterfactual check on seeded profile and first 8 jobs; not a population fairness evaluation.'})
@app.get('/api/evaluation')
def evaluation():
 rows=Job.query.all(); tp=fp=tn=fn=0
 for j in rows:
  result=assess(j.description,j.employer,j.email,j.domain); pred=result['score']>=int(request.args.get('threshold',30)); truth=j.scam_label
  if pred and truth: tp+=1
  elif pred: fp+=1
  elif truth: fn+=1
  else: tn+=1
 total=len(rows); precision=tp/(tp+fp) if tp+fp else 0; recall=tp/(tp+fn) if tp+fn else 0
 ev=json.loads(get_candidate().evidence); coverage=sum(1 for j in rows[:10] for x in match(j)['requirements'] if x['evidence'])/max(1,sum(len(match(j)['requirements']) for j in rows[:10]))
 return jsonify({'threshold':int(request.args.get('threshold',30)),'evaluated':total,'ground_truth_scams':sum(1 for j in rows if j.scam_label),'tp':tp,'fp':fp,'tn':tn,'fn':fn,'precision':round(precision,3),'recall':round(recall,3),'false_positive_rate':round(fp/(fp+tn) if fp+tn else 0,3),'evidence_coverage':round(coverage,3),'limitation':'Synthetic labelled dataset only; small and intentionally constructed. Metrics do not estimate real-world performance.'})
@app.post('/api/refresh/<int:jid>')
def refresh(jid):
 pause_stale_vacancies(); j=Job.query.get_or_404(jid); age=max(0,(datetime.utcnow()-j.updated).days)
 # This is a local demo date check only; it never resets freshness or contacts an employer.
 return jsonify({'id':j.id,'status':j.status,'age_days':age,'freshness':'Employer reconfirmation needed' if age>14 else ('Confirmation due soon' if age>7 else 'Recent demo listing date'),'live_check':False,'message':'No employer was contacted. A reviewer must reconfirm a vacancy before it can be trusted as current.'})
@app.post('/api/demo/reset')
def reset():
 TrustReport.query.delete(); EmployerSubmission.query.delete(); Disclosure.query.delete(); ResumeVersion.query.delete(); InterviewPrompt.query.delete(); Application.query.delete(); Task.query.delete(); Job.query.delete(); Candidate.query.delete(); db.session.commit(); seed(); return jsonify({'status':'demo reset','jobs':Job.query.count()})
@app.get('/api/employer/submissions')
def employer_submissions():
 return jsonify([{'id':x.id,'organization':x.organization,'role_title':x.role_title,'status':x.status,'created':x.created.isoformat(),'pay_info':x.pay_info or '','social_protection':x.social_protection or '','growth_path':x.growth_path or '', 'signals':json.loads(x.signals or '[]')} for x in EmployerSubmission.query.order_by(EmployerSubmission.created.desc()).all()])
@app.post('/api/employer/submissions')
def create_employer_submission():
 d=request.get_json() or {}; organization=str(d.get('organization','')).strip()[:160]; email=str(d.get('contact_email','')).strip()[:200]; website=str(d.get('website','')).strip().lower().removeprefix('https://').removeprefix('http://').split('/')[0][:200]; role=str(d.get('role_title','')).strip()[:160]; description=str(d.get('description','')).strip()[:6000]; evidence=str(d.get('evidence_route','')).strip()[:80]; org_type=str(d.get('organization_type','')).strip()[:50]; pay_info=str(d.get('pay_info','')).strip()[:180]; social_protection=str(d.get('social_protection','')).strip()[:180]; growth_path=str(d.get('growth_path','')).strip()[:240]
 if not organization or '@' not in email or not role or len(description)<30: return jsonify({'error':'Add an organization, contact email, role title, and at least 30 characters describing the role.'}),400
 if evidence not in ['Udyam registration','Shop or establishment license','Local trade permit','Employer reference check','Authorization from the hiring organization','Other business evidence']: return jsonify({'error':'Choose one business evidence route. Do not enter Aadhaar, PAN, bank, GSTIN, or EPFO identifiers.'}),400
 if d.get('no_candidate_fee') is not True: return jsonify({'error':'Confirm that candidates will not be charged to apply, interview, train, or secure this role.'}),400
 risk=assess(description,organization,email,website); signals=[x for x in risk['signals'] if x['label']!='Domain not in demo reference records']
 email_domain=email.rsplit('@',1)[-1].lower(); free_domains={'gmail.com','yahoo.com','yahoo.in','outlook.com','hotmail.com','rediffmail.com'}
 if email_domain in free_domains: signals.append({'label':'Personal mailbox needs additional organization check','evidence':email_domain,'points':10})
 if not website: signals.append({'label':'No public website supplied; alternate business evidence needs review','evidence':evidence,'points':5})
 if org_type=='Authorized staffing partner' and evidence!='Authorization from the hiring organization': signals.append({'label':'Staffing-partner authorization not supplied','evidence':evidence,'points':20})
 reference=Job.query.filter(db.func.lower(Job.employer)==organization.lower()).first()
 if reference and website and website!=reference.domain.lower(): signals.append({'label':'Organization name matches a demo employer but website differs','evidence':website+' vs '+reference.domain,'points':25})
 row=EmployerSubmission(organization=organization,organization_type=org_type,contact_email=email,website=website,evidence_route=evidence,role_title=role,location=str(d.get('location',''))[:120],description=description,status='Pending review',signals=json.dumps(signals),pay_info=pay_info,social_protection=social_protection,growth_path=growth_path); db.session.add(row); db.session.commit()
 return jsonify({'id':row.id,'status':row.status,'publishable':False,'signals':signals,'message':'This submission is held for manual review. It is not a published vacancy; this demo has no reviewer or live verification connection.'}),201

@app.get('/api/dashboard')
def dashboard():
 pause_stale_vacancies()
 return jsonify({'jobs':Job.query.filter_by(status='Active').count(),'applications':Application.query.count(),'verification':sum(1 for j in Job.query.all() if assess(j.description,j.employer,j.email,j.domain)['score']>=20),'roadmap_total':Task.query.count(),'roadmap_done':Task.query.filter_by(status='Completed').count()})
@app.post('/api/evidence')
def add_evidence():
 c=get_candidate(); d=request.get_json() or {}; skill=str(d.get('skill','')).strip()[:80]; source=str(d.get('source','')).strip()[:240]; status=d.get('status','Self-reported')
 if not skill or not source: return jsonify({'error':'Skill and evidence source are required'}),400
 if status not in ['Demonstrated','Self-reported','Partially supported','Needs review']: return jsonify({'error':'Unsupported evidence status'}),400
 ev=json.loads(c.evidence); ev.append({'skill':skill,'status':status,'source':source}); c.evidence=json.dumps(ev); skills=json.loads(c.skills); skills.setdefault(norm(skill),1); c.skills=json.dumps(skills); db.session.commit(); return jsonify({'evidence':ev,'skills':skills}),201

@app.post('/api/interview/questions')
def create_interview_questions():
 d=request.get_json() or {}; j=Job.query.get_or_404(d.get('job_id')); c=get_candidate(); ev=json.loads(c.evidence); prompts=[]
 for skill in jskills(j):
  record=next((x for x in ev if norm(x.get('skill',''))==norm(skill)),None)
  if record and record.get('status')=='Demonstrated':
   q=f"Walk me through how you used {skill} in {record.get('source')}. What did you do, and what would you improve next time?"
   basis=f"Required skill: {skill}"; source=record.get('source','Candidate evidence')
  elif record:
   q=f"You listed {skill} in your profile. How would you describe your current experience, and what would you like to practice next?"
   basis=f"Required skill: {skill}"; source=record.get('source','Candidate profile')
  else:
   q=f"{j.title} asks for {skill}. How would you approach learning or testing it before taking on a work task?"
   basis=f"Learning-oriented question for a role gap: {skill}"; source='No supporting profile record yet'
  prompt=InterviewPrompt(job_id=j.id,question=q,basis=basis,evidence=source); db.session.add(prompt); prompts.append(prompt)
 db.session.commit(); return jsonify([{'id':p.id,'job_id':p.job_id,'question':p.question,'basis':p.basis,'evidence':p.evidence,'answer':p.answer,'completed':p.completed} for p in prompts]),201
@app.get('/api/interview')
def interview_questions():
 query=InterviewPrompt.query.order_by(InterviewPrompt.created.desc())
 if request.args.get('job_id'): query=query.filter_by(job_id=int(request.args['job_id']))
 return jsonify([{'id':p.id,'job_id':p.job_id,'question':p.question,'basis':p.basis,'evidence':p.evidence,'answer':p.answer,'completed':p.completed} for p in query.limit(80).all()])
@app.patch('/api/interview/<int:pid>')
def update_interview_prompt(pid):
 p=InterviewPrompt.query.get_or_404(pid); d=request.get_json() or {}; p.answer=str(d.get('answer',p.answer))[:3000]; p.completed=bool(d.get('completed',p.completed)); db.session.commit(); return jsonify({'id':p.id,'answer':p.answer,'completed':p.completed})
def serialize_resume(r):
 return {'id':r.id,'job_id':r.job_id,'title':r.title,'content':json.loads(r.content),'redacted':r.redacted,'created':r.created.isoformat()}
@app.get('/api/resumes')
def resumes(): return jsonify([serialize_resume(r) for r in ResumeVersion.query.order_by(ResumeVersion.created.desc()).all()])
@app.post('/api/resumes')
def create_resume():
 d=request.get_json() or {}; j=Job.query.get_or_404(d.get('job_id')); c=get_candidate(); evidence=json.loads(c.evidence); skills=[{'skill':x.get('skill',''),'status':x.get('status','Self-reported'),'source':x.get('source','')} for x in evidence if x.get('skill')]
 content={'candidate':c.name,'career_goal':c.goal,'role_focus':j.title,'organization':j.employer,'evidence_skills':skills,'contact_details':'Not included in this local preview'}
 r=ResumeVersion(job_id=j.id,title=str(d.get('title') or f"{j.title} · tailored draft")[:160],content=json.dumps(content),redacted=True); db.session.add(r); db.session.commit(); return jsonify(serialize_resume(r)),201
@app.get('/api/disclosures')
def disclosures(): return jsonify([{'id':x.id,'resume_id':x.resume_id,'recipient':x.recipient,'fields':json.loads(x.fields),'consent':x.consent,'created':x.created.isoformat(),'mode':'Local demo record; no file was sent'} for x in Disclosure.query.order_by(Disclosure.created.desc()).all()])
@app.post('/api/disclosures')
def create_disclosure():
 d=request.get_json() or {}; r=ResumeVersion.query.get_or_404(d.get('resume_id')); recipient=str(d.get('recipient','')).strip()[:160]; fields=d.get('fields',[])
 allowed={'Candidate name','Career goal','Role focus','Evidence-backed skills'}
 if not recipient or d.get('consent') is not True or not isinstance(fields,list) or any(x not in allowed for x in fields): return jsonify({'error':'Choose a recipient, selected fields, and explicit consent to save this demo disclosure record.'}),400
 row=Disclosure(resume_id=r.id,recipient=recipient,fields=json.dumps(fields),consent=True); db.session.add(row); db.session.commit(); return jsonify({'id':row.id,'resume_id':row.resume_id,'recipient':row.recipient,'fields':fields,'consent':True,'mode':'Local demo record; no file was sent'}),201
@app.get('/api/trust/reports')
def trust_reports(): return jsonify([{'id':x.id,'kind':x.kind,'details':x.details,'status':x.status,'created':x.created.isoformat()} for x in TrustReport.query.order_by(TrustReport.created.desc()).all()])
@app.post('/api/trust/reports')
def create_trust_report():
 d=request.get_json() or {}; kind=d.get('kind'); details=str(d.get('details','')).strip()[:1600]
 if kind not in ['Concern','Correction request','Appeal'] or len(details)<8: return jsonify({'error':'Choose a report type and enter at least 8 characters of context.'}),400
 row=TrustReport(kind=kind,details=details,status='Received'); db.session.add(row); db.session.commit(); return jsonify({'id':row.id,'kind':row.kind,'details':row.details,'status':row.status,'created':row.created.isoformat(),'visibility':'Private local demo record'}),201

if __name__=='__main__':
 with app.app_context(): seed()
 app.run(port=5000,debug=False)



