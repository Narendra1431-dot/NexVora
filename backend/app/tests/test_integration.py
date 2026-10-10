"""Real MongoDB integration in an isolated test database."""
import os
os.environ['MONGODB_DB']='career_intelligence_qa'
os.environ['RATE_LIMIT_PER_MINUTE']='2000'
from fastapi.testclient import TestClient
from app.main import app
from app.seed.assessments import ASSESSMENTS
from app.seed.projects import PROJECTS, RESOURCES
from uuid import uuid4

def test_connected_journey(monkeypatch):
    # Supervisor path only; never hit the live Central Brain providers.
    monkeypatch.setenv('ENABLE_CENTRAL_BRAIN','false')
    with TestClient(app) as c:
        assert c.get('/health').status_code==200
        assert c.get('/api/v1/state').status_code==401
        auth=c.post('/api/v1/auth/register',json={'name':'QA Learner','email':f'qa-{uuid4().hex}@example.com','password':'qa-secure-pass'}); assert auth.status_code==201, auth.text
        c.headers['Authorization']='Bearer '+auth.json()['token']
        before=c.get('/api/v1/state'); assert before.status_code==200,before.text
        assert before.json()['readiness']==0
        assert before.headers['X-Request-ID']
        assert before.json()['intelligence']['advisoryOnly']
        intelligence=c.get('/api/v1/analytics/intelligence')
        assert intelligence.status_code==200,intelligence.text
        assert intelligence.json()['trainingData']=='synthetic_demo'
        assert len(before.json()['competencies'])>=27
        profile=c.patch('/api/v1/profile',json={'headline':'QA saved profile'}); assert profile.json()['headline']=='QA saved profile'
        resume=c.post('/api/v1/resume/analyze',json={'text':'Skills: Python, SQL. Education: Computer Science.'}); assert resume.status_code==200,resume.text
        ev=c.get('/api/v1/evidence').json(); assert ev and all(e['verificationState']=='Unverified' for e in ev)
        spoof=c.post('/api/v1/evidence',json={'title':'fake proof','type':'Assessment','skillId':ev[0]['skillId'],'verificationState':'Verified','confidenceScore':100}); assert spoof.status_code==201,spoof.text
        assert spoof.json()['evidence']['verificationState']=='Unverified'
        a=ASSESSMENTS[0]
        failed=c.post(f"/api/v1/assessments/{a['id']}/attempts",json={'answers':{}}); assert failed.status_code==201,failed.text
        assert failed.json()['attempt']['score']==0
        partial=c.post(f"/api/v1/assessments/{a['id']}/attempts",json={'answers':{q['id']:q['correctAnswers'] for q in a['questions'][:3]}})
        assert partial.status_code==201,partial.text
        assert partial.json()['attempt']['score']==75
        assert partial.json()['attempt']['passed'] is False
        partial_evidence=next(e for e in c.get('/api/v1/evidence').json() if e['id']==partial.json()['evidenceId'])
        assert partial_evidence['verificationState']=='Needs Review'
        passed=c.post(f"/api/v1/assessments/{a['id']}/attempts",json={'answers':{q['id']:q['correctAnswers'] for q in a['questions']}}); assert passed.status_code==201,passed.text
        assert passed.json()['attempt']['score']==100
        after=c.get('/api/v1/state').json(); assert after['stateVersion']>before.json()['stateVersion']
        assert any(n['mastery']>0 for n in after['competencies'])
        assessed_node=next(n for n in after['competencies'] if n['id']==a['skillId'])
        assert assessed_node['lastAssessedAt'] and assessed_node['lastAssessed']!='Never'
        assert after['concepts']
        assert after['relationships']['edges']
        assert all(e['type']!='VERIFIES' or e['source'].startswith('evidence:') for e in after['relationships']['edges'])
        assert after['events']
        assert after['milestones']!=before.json()['milestones']
        r=c.post(f"/api/v1/projects/{PROJECTS[0]['id']}/submissions",json={'githubUrl':'https://github.com/example/example','description':'A long description does not prove any working implementation. '*4}); assert r.status_code==201,r.text
        assert r.json()['submission']['verificationState']=='Needs Review'
        sub_id=r.json()['submission']['id']
        review={'criteria':[{'criterion':r['criterion'],'score':90,'evidence':'QA fixture: reviewer inspected a known test artifact.'} for r in PROJECTS[0]['rubric']], 'feedback':'QA fixture review; not a real student evaluation.'}
        assert c.post('/api/v1/submissions/'+sub_id+'/review',json=review).status_code==403
        original_token=c.headers['Authorization']
        reviewer=c.post('/api/v1/auth/register',json={'name':'QA Reviewer','email':'reviewer-qa@example.com','password':'qa-reviewer-pass'})
        if reviewer.status_code==409: reviewer=c.post('/api/v1/auth/login',json={'email':'reviewer-qa@example.com','password':'qa-reviewer-pass'})
        c.headers['Authorization']='Bearer '+reviewer.json()['token']
        reviewed=c.post('/api/v1/submissions/'+sub_id+'/review',json=review); assert reviewed.status_code==200,reviewed.text
        assert reviewed.json()['verificationState']=='Verified'
        c.headers['Authorization']=original_token
        assert any(e['type']=='Project' and e['verificationState']=='Verified' for e in c.get('/api/v1/evidence').json())

        r=c.post('/api/v1/rag/query',json={'message':'scaled dot product attention sqrt softmax'}); assert r.status_code==200,r.text
        assert r.json()['passages'] and r.json()['sources']
        r=c.post('/api/v1/career/target',json={'careerId':'career-data-analyst'}); assert r.status_code==200,r.text
        r=c.post(f"/api/v1/resources/{RESOURCES[0]['id']}/action",json={'bookmarked':True}); assert r.status_code==200,r.text
        r=c.post('/api/v1/documents',files={'file':('resume.txt',b'Skills: Python and SQL','text/plain')}); assert r.status_code==200,r.text
        assert c.post('/api/v1/documents',files={'file':('resume.pdf',b'not a pdf','application/pdf')}).status_code==422
        import io
        from pypdf import PdfWriter
        from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
        writer=PdfWriter(); page=writer.add_blank_page(width=612,height=792)
        font=DictionaryObject({NameObject('/Type'):NameObject('/Font'),NameObject('/Subtype'):NameObject('/Type1'),NameObject('/BaseFont'):NameObject('/Helvetica')})
        page[NameObject('/Resources')]=DictionaryObject({NameObject('/Font'):DictionaryObject({NameObject('/F1'):font})})
        stream=DecodedStreamObject(); stream.set_data(b'BT /F1 12 Tf 72 720 Td (Skills: Python and SQL. Education: Computer Science.) Tj ET')
        page[NameObject('/Contents')]=writer._add_object(stream)
        buf=io.BytesIO(); writer.write(buf)
        pdf=c.post('/api/v1/documents',files={'file':('qa-resume.pdf',buf.getvalue(),'application/pdf')}); assert pdf.status_code==200,pdf.text
        assert 'Python (Advanced)' in pdf.json()['extractedSkills']
        active_claims=[e for e in c.get('/api/v1/evidence').json() if e['type']=='Resume Claim']
        assert len(active_claims)==2
        assert all(e['documentId']==pdf.json()['documentId'] for e in active_claims)
        parsed=c.get('/api/v1/state').json()['resume']
        assert parsed['parsedSections'] and parsed['documentId']==pdf.json()['documentId']
        assert 'T' in parsed['uploadedAtRaw']
        diag=c.post('/api/v1/diagnostic/start',json={'skillId':'prog-python-advanced'}); assert diag.status_code==200,diag.text
        diagnostic=diag.json()
        invalid=c.post('/api/v1/attempts/'+diagnostic['id']+'/submit',json={'answers':{'oversized':'x'*60000}})
        assert invalid.status_code==413
        assert 'correctAnswers' not in diagnostic['assessment']['questions'][0]
        attempt=c.post('/api/v1/attempts/'+diagnostic['id']+'/submit',json={'answers':{}}); assert attempt.status_code==200,attempt.text
        assert c.post('/api/v1/attempts/'+diagnostic['id']+'/submit',json={'answers':{}}).status_code==409
        for endpoint in ['/me','/resources/recommendations','/projects/recommendations']:
            assert c.get('/api/v1'+endpoint).status_code==200

        for path in ['/catalog/skills','/catalog/careers','/catalog/resources','/catalog/projects','/catalog/assessments','/profile','/competencies','/roadmap','/notifications','/notifications/activity','/analytics/overview','/mentor/status','/competencies/concepts','/competencies/relationships']:
            response=c.get('/api/v1'+path); assert response.status_code==200,(path,response.text)
        import app.agents.supervisor as supervisor_module
        from app.services import llm
        captured=[]
        async def fixture_generate(prompt, **kwargs):
            captured.append((prompt, kwargs))
            return 'Transport fixture answer; not a live AI response.'
        monkeypatch.setattr(llm,'generate',fixture_generate)
        monkeypatch.setattr(supervisor_module.llm,'generate',fixture_generate)
        version_before=c.get('/api/v1/state').json()['stateVersion']
        mentor=c.post('/api/v1/mentor/chat',json={'message':'Which project and assessment should I try?','history':[]})
        assert mentor.status_code==200,mentor.text
        assert {'recommendProject','getAssessments','retrieveRAG'} <= set(mentor.json()['agentRun']['toolsUsed'])
        assert not mentor.json()['agentRun']['errors']
        assert captured[0][0]=='Which project and assessment should I try?'
        assert c.get('/api/v1/state').json()['stateVersion']==version_before
        async def invalid_citation(prompt, **kwargs): return 'Unsupported [kb-invented-document].'
        monkeypatch.setattr(llm,'generate',invalid_citation)
        monkeypatch.setattr(supervisor_module.llm,'generate',invalid_citation)
        assert c.post('/api/v1/mentor/chat',json={'message':'attention softmax'}).status_code==502
        no_results=c.post('/api/v1/rag/query',json={'message':'zzzzqxjvvv 998877665544'})
        assert no_results.json()['status']=='insufficient_grounded_information'
        bank=c.get('/api/v1/catalog/assessments').json(); assert all('correctAnswers' not in q for a in bank for q in a['questions'])
        other=c.post('/api/v1/auth/register',json={'name':'Other','email':f'qa-{uuid4().hex}@example.com','password':'qa-secure-pass'}).json()
        c.headers['Authorization']='Bearer '+other['token']
        assert c.delete('/api/v1/evidence/'+ev[0]['id']).status_code==404
        assert not c.get('/api/v1/evidence').json()
        assert not c.get('/api/v1/competencies/concepts').json()
        assert not any(n['kind']=='evidence' for n in c.get('/api/v1/competencies/relationships').json()['nodes'])
        assert not next(r for r in c.get('/api/v1/state').json()['resources'] if r['id']==RESOURCES[0]['id']).get('bookmarked',False)
