import unittest
import os
from datetime import datetime, timedelta
os.environ['CAREERTRUST_DATABASE_URI']='sqlite://'
from app import app, db, Candidate, Job, Application, Task, EmployerSubmission, seed
class CareerTrustTests(unittest.TestCase):
 def setUp(self):
  app.config['TESTING']=True
  self.ctx=app.app_context(); self.ctx.push(); db.drop_all(); seed(); self.client=app.test_client()
 def tearDown(self): db.session.remove(); db.drop_all(); self.ctx.pop()
 def test_seeded_demo_and_match(self):
  self.assertEqual(self.client.get('/api/jobs').status_code,200)
  self.assertEqual(Job.query.count(),40)
  self.assertEqual(sum(1 for j in Job.query.all() if j.scam_label),6)
  self.assertIn('requirements',self.client.get('/api/jobs').json[0]['match'])
 def test_profile_update_changes_match(self):
  job=Job.query.first(); before=self.client.get(f'/api/jobs/{job.id}').json['match']['score']
  p=self.client.get('/api/profile').json; p['skills']['power bi']=3
  self.assertEqual(self.client.put('/api/profile',json=p).status_code,200)
  after=self.client.get(f'/api/jobs/{job.id}').json['match']['score']
  self.assertGreaterEqual(after,before)
 def test_trust_detects_fees_but_cautious_listing(self):
  scam=self.client.post('/api/trust',json={'text':'Pay a refundable registration fee for guaranteed placement. Send bank details immediately.','email':'fast@gmail.com','domain':'unknown.example'}).json
  self.assertEqual(scam['tier'],'High-risk indicators detected'); self.assertTrue(scam['signals'])
  normal=self.client.post('/api/trust',json={'text':'Analyst role supporting data reports.','domain':'newstartup.example'}).json
  self.assertNotEqual(normal['tier'],'High-risk indicators detected')
 def test_application_and_roadmap_persist(self):
  job=Job.query.first(); response=self.client.post('/api/applications',json={'job_id':job.id}); self.assertEqual(response.status_code,201)
  self.assertEqual(self.client.post('/api/applications',json={'job_id':job.id}).status_code,409)
  task=Task.query.first(); self.assertEqual(self.client.patch(f'/api/roadmap/{task.id}',json={'status':'Completed','evidence':'Dashboard project'}).status_code,200)
 def test_evidence_creation_is_persisted_and_explained(self):
  response=self.client.post('/api/evidence',json={'skill':'Power BI','source':'Candidate dashboard project','status':'Demonstrated'})
  self.assertEqual(response.status_code,201)
  self.assertEqual(self.client.get('/api/profile').json['evidence'][-1]['source'],'Candidate dashboard project')
 def test_computed_audit_reports_all_seeded_listings(self):
  self.assertEqual(self.client.get('/api/evaluation').json['evaluated'],40)
  result=self.client.post('/api/fairness').json
  self.assertTrue(all(x['max_gap']==0 for x in result['tests']))
 def test_interview_and_resume_privacy_flows(self):
  job=Job.query.filter_by(scam_label=False).first()
  questions=self.client.post('/api/interview/questions',json={'job_id':job.id})
  self.assertEqual(questions.status_code,201)
  self.assertTrue(any('Exploratory Data Analysis project' in x['evidence'] for x in questions.json))
  q=questions.json[0]
  self.assertEqual(self.client.patch(f"/api/interview/{q['id']}",json={'answer':'A practice answer','completed':True}).json['completed'],True)
  resume=self.client.post('/api/resumes',json={'job_id':job.id})
  self.assertEqual(resume.status_code,201)
  self.assertTrue(resume.json['redacted'])
  self.assertEqual(resume.json['content']['contact_details'],'Not included in this local preview')
  self.assertEqual(self.client.post('/api/disclosures',json={'resume_id':resume.json['id'],'recipient':'Demo employer','fields':['Evidence-backed skills'],'consent':False}).status_code,400)
  disclosure=self.client.post('/api/disclosures',json={'resume_id':resume.json['id'],'recipient':'Demo employer','fields':['Evidence-backed skills'],'consent':True})
  self.assertEqual(disclosure.status_code,201)
  self.assertIn('no file was sent',disclosure.json['mode'])
 def test_employer_posts_are_held_and_fee_traps_are_flagged(self):
  before=Job.query.count()
  payload={'organization':'Local Demo Works','organization_type':'Small or local business','contact_email':'team@localworks.example','website':'localworks.example','evidence_route':'Local trade permit','role_title':'Office assistant','location':'Pune','description':'Support office work and customer records. Applicants pay a toolkit fee before onboarding.','no_candidate_fee':True}
  response=self.client.post('/api/employer/submissions',json=payload)
  self.assertEqual(response.status_code,201)
  self.assertEqual(response.json['status'],'Pending review')
  self.assertFalse(response.json['publishable'])
  self.assertTrue(response.json['signals'])
  self.assertEqual(Job.query.count(),before)
  self.assertEqual(self.client.get('/api/employer/submissions').json[0]['status'],'Pending review')
 def test_employer_preflight_is_transparent_and_never_publishable(self):
  payload={'organization':'Corner Market','organization_type':'Small or local business','contact_email':'owner@cornermarket.example','website':'','evidence_route':'Local trade permit','role_title':'Store assistant','location':'Local','description':'Help customers, arrange shelves, and check daily inventory with the shop owner.','no_candidate_fee':True}
  result=self.client.post('/api/employer/preflight',json=payload)
  self.assertEqual(result.status_code,200)
  self.assertIn('not a fraud probability',result.json['score_type'])
  self.assertFalse(result.json['publishable'])
  self.assertFalse(result.json['requires_changes'])
  self.assertTrue(any(x['status']=='Not checked' for x in result.json['authority_checks']))
  self.assertTrue(any(y['label']=='Udyam verification' for x in result.json['authority_checks'] for y in x.get('sources',[])))
 def test_high_risk_employer_submission_returns_for_changes_without_saving(self):
  before=EmployerSubmission.query.count()
  payload={'organization':'Corner Market','organization_type':'Small or local business','contact_email':'owner@cornermarket.example','website':'cornermarket.example','evidence_route':'Local trade permit','role_title':'Store assistant','location':'Local','description':'Pay a registration fee and send your bank details immediately to secure this guaranteed placement.','no_candidate_fee':True}
  response=self.client.post('/api/employer/submissions',json=payload)
  self.assertEqual(response.status_code,422)
  self.assertTrue(response.json['requires_changes'])
  self.assertGreaterEqual(response.json['risk_score'],50)
  self.assertFalse(response.json['publishable'])
  self.assertEqual(EmployerSubmission.query.count(),before)
 def test_candidate_profile_includes_college_and_language_without_matching_on_them(self):
  p=self.client.get('/api/profile').json; p.update({'college':'Demo College','education':'Diploma','language':'తెలుగు'})
  self.assertEqual(self.client.put('/api/profile',json=p).status_code,200)
  saved=self.client.get('/api/profile').json
  self.assertEqual(saved['college'],'Demo College'); self.assertEqual(saved['language'],'తెలుగు')
  self.assertTrue(all(x['max_gap']==0 for x in self.client.post('/api/fairness').json['tests']))
 def test_ghost_vacancy_is_paused_and_cannot_receive_applications(self):
  job=Job.query.first(); job.updated=datetime.utcnow()-timedelta(days=15); job_id=job.id; db.session.commit()
  visible=self.client.get('/api/jobs').json
  self.assertNotIn(job_id,[x['id'] for x in visible])
  self.assertEqual(Job.query.get(job_id).status,'Needs confirmation')
  self.assertEqual(self.client.post('/api/applications',json={'job_id':job_id}).status_code,409)
 def test_fee_detector_respects_plain_negative_wording(self):
  safe=self.client.post('/api/trust',json={'text':'Candidates are not charged training fees or placement costs.','domain':'example.org'}).json
  self.assertFalse(any('payment' in x['label'].lower() for x in safe['signals']))
 def test_private_trust_report_and_correction_workflow(self):
  self.assertEqual(self.client.post('/api/trust/reports',json={'kind':'Concern','details':'fee request'}).status_code,201)
  self.assertEqual(self.client.post('/api/trust/reports',json={'kind':'Correction request','details':'Please review changed email details'}).status_code,201)
  self.assertEqual(len(self.client.get('/api/trust/reports').json),2)
if __name__=='__main__': unittest.main()
