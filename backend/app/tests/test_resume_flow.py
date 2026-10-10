"""Real demo PDF and replacement lifecycle, isolated QA MongoDB."""
from pathlib import Path
from uuid import uuid4
from fastapi.testclient import TestClient
from app.main import app
from app.seed.assessments import ASSESSMENTS


def test_demo_resume_lifecycle_and_dynamic_career():
    with TestClient(app) as client:
        auth=client.post('/api/v1/auth/register',json={'name':'Resume QA','email':f'resume-{uuid4().hex}@example.com','password':'qa-resume-pass'})
        assert auth.status_code==201
        client.headers['Authorization']='Bearer '+auth.json()['token']
        assert not client.get('/api/v1/state').json()['resume']
        assert client.post('/api/v1/career/target',json={'careerId':'career-ml-engineer'}).status_code==200
        pdf=Path(__file__).with_name('fixtures').joinpath('demo_resume.pdf').read_bytes()
        result=client.post('/api/v1/documents',files={'file':('demo_resume.pdf',pdf,'application/octet-stream')})
        assert result.status_code==200,result.text
        state=result.json()['state'];analysis=state['resume']
        assert analysis['targetCareerTitle']=='ML Engineer'
        assert analysis['extractedSkillsCount']==analysis['claimCount']==len(analysis['claims'])==len(result.json()['extractedSkills'])
        assert analysis['claimCount']>=10
        breakdown=analysis['scoreBreakdown']
        assert analysis['atsCompatibilityScore']==round(.4*breakdown['sectionStructure']+.4*breakdown['roleKeywordCoverage']+.2*breakdown['evidenceCoverage'])
        from app.db import col
        async def stored_analysis():
            return await col('resume_analysis').find_one({'documentId':analysis['documentId']})
        saved=client.portal.call(stored_analysis)
        assert saved['claimCount']==analysis['claimCount']
        assert saved['targetCareerTitle']=='ML Engineer'
        assert saved['atsCompatibilityScore']==analysis['atsCompatibilityScore']
        assert analysis['verifiedClaimsCount']==0
        assert analysis['evidenceCoveragePercent']==0
        assert {'summary','skills','education','projects'}<=set(analysis['sectionsDetected'])
        assert all(c['evidenceId'] is None for c in analysis['claims'])
        current=client.get('/api/v1/state').json()['resume']
        assert current==analysis
        # Invalid replacement leaves the previous successful analysis intact.
        assert client.post('/api/v1/documents',files={'file':('broken.pdf',b'broken','application/pdf')}).status_code==422
        assert client.post('/api/v1/resume/analyze',json={'text':'   '}).status_code==422
        assert client.get('/api/v1/state').json()['resume']['documentId']==analysis['documentId']
        bank=next(b for b in ASSESSMENTS if b['skillId']=='prog-python-advanced' and b['difficulty']=='Beginner')
        response=client.post('/api/v1/assessments/'+bank['id']+'/attempts',json={'answers':{q['id']:q['correctAnswers'] for q in bank['questions']}})
        assert response.status_code==201,response.text
        supported=client.get('/api/v1/state').json()['resume']
        claim=next(c for c in supported['claims'] if c['skillId']=='prog-python-advanced')
        assert claim['evidenceState']=='Verified'
        assert claim['evidenceId']==response.json()['evidenceId']
        assert client.post('/api/v1/career/target',json={'careerId':'career-ai-engineer'}).status_code==200
        switched=client.get('/api/v1/state').json()['resume']
        assert switched['targetCareerTitle']=='AI Engineer'
        assert switched['targetCareerId']=='career-ai-engineer'
        assert switched['documentId']==analysis['documentId']
        # Replacing with a one-skill TXT removes previous resume claims, not proof.
        replacement=client.post('/api/v1/documents',files={'file':('one-skill.txt',b'SKILLS\nSQL','text/plain')})
        assert replacement.status_code==200,replacement.text
        fresh=replacement.json()['state']['resume']
        assert fresh['claimCount']==fresh['extractedSkillsCount']==1
        assert fresh['claims'][0]['skillId']=='data-sql-querying'
        assert fresh['verifiedClaimsCount']==0
        assert all(c['skillId']!='prog-python-advanced' for c in fresh['claims'])
        assert 'Python (Advanced)' in fresh['missingSkillsForTarget']
        again=client.post('/api/v1/resume/analyze',json={'text':'SKILLS\nSQL'})
        assert again.status_code==200
        assert again.json()['state']['resume']['claimCount']==1
        assert len([e for e in again.json()['state']['evidence'] if e['type']=='Resume Claim'])==1
        empty=client.post('/api/v1/resume/analyze',json={'text':'SUMMARY\nA motivated learner.'})
        assert empty.status_code==200
        assert empty.json()['state']['resume']['claimCount']==0
        assert empty.json()['state']['resume']['evidenceCoveragePercent']==0
