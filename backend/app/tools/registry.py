"""Allowlisted, student-bound domain adapters. No database or shell tool exists."""
from fastapi import HTTPException
from ..agents.models import ToolInput,ToolOutput,safe

async def execute(call:ToolInput, s):
    from ..runtime.gateway import read_tool
    return await read_tool(call,s,_execute)

async def _execute(call:ToolInput, s):
    name=call.name
    if call.skillId and call.skillId not in s.mastery:raise HTTPException(404,'Unknown competency.')
    if name=='getCodingProgress':data={'progress':s.codingProgress,'xp':s.xp,'rule':'Code execution and grading remain in the dedicated Coding Space sandbox.'}
    elif name=='getRank':data={'rank':s.rank,'xp':s.xp}
    elif name=='getStudentProfile':data=s.profile
    elif name=='getCompetencies':data=[c for c in s.competencies if not call.skillId or c['id']==call.skillId]
    elif name=='getEvidence':data=[e for e in s.evidence if not call.skillId or e.get('skillId')==call.skillId]
    elif name=='calculateCareerGap':data=s.careerGaps
    elif name=='calculateReadiness':data={'career':s.targetCareer.get('title'),'readiness':s.readiness,'requirements':s.targetCareer.get('requirements',[])}
    elif name=='getRoadmap':
        from ..intelligence.recommendations import weekly_plan
        data={'milestones':s.roadmap,'nextAction':s.recommendations,'weeklyPlan':weekly_plan(s)}
    elif name=='searchResources':
        from fastapi import BackgroundTasks
        from ..routers.learning_hub import hub
        career_id=s.targetCareer.get('id')
        learning=await hub(career_id,BackgroundTasks(),s.studentId) if career_id else {'topics':[]}
        topics=[t for t in learning['topics'] if not call.skillId or t['id']==call.skillId]
        courses=[r for r in s.resources if not call.skillId or r.get('skillId')==call.skillId]
        data={'coursesAndPractice':courses[:6],'topics':topics[:3],
              'fullNotesPdf':'/api/v1/learning-hub/'+career_id+'/pdf' if career_id and learning.get('notesReady') else None,
              'why':'Current career requirements, prerequisite gaps, mastery, difficulty, quality and available time inform recommendations.',
              'preferences':s.profile.get('learningPreferences'),'rankingLimitation':'ML ranking is an advisory model trained on synthetic demo data.'}
    elif name=='getAssessments':data={'available':[a for a in s.assessments if not call.skillId or a.get('skillId')==call.skillId],'history':s.assessmentHistory}
    elif name=='recommendProject':data=[p for p in s.projects if not call.skillId or call.skillId in p.get('skillsValidated',[])][:3]
    elif name=='analyzeResume':data={'analysis':s.resume,'proofBuilding':{'assessments':s.assessments[:3],'projects':s.projects[:3]},'rule':'Unsupported claims remain unverified. Upload or paste in Resume Intelligence to replace the resume.'}
    elif name=='checkCertificateEligibility':
        from ..routers.certificates import eligibility,public
        from ..seed.external_certifications import CATALOG
        courses=[r for r in s.resources if r.get('type')=='Course' and (not call.courseId or r['id']==call.courseId)]
        if call.courseId and not courses:raise HTTPException(404,'Course not found.')
        required={c['id'] for c in s.careerGaps}
        category_skills={'AI/ML':('dl-','ml-'),'Cloud':('cloud-','mlops-'),'DevOps':('ops-iac','prog-docker','prog-testing'),'Development':('prog-','web-'),'Database':('data-',),'Linux':('ops-linux',),'Networking':('cloud-networking',)}
        external=[]
        for c in CATALOG:
            matching=[sid for sid in required if any(sid.startswith(prefix) for cat in c['categories'] for prefix in category_skills.get(cat,()))]
            if matching:external.append({**c,'gapSkillIds':matching,'why':'Covers areas in your current career gaps; provider prerequisites and exam requirements still apply.'})
        data={'issued':[public(c) for c in s.certificates], 'courses':[await eligibility(s.studentId,r['id']) for r in courses[:6]],'external':external[:5],
              'nextAction':{'tab':'certificates','label':'Preview certificate options'},'rule':'Premium purchase and backend eligibility remain mandatory. Recommendations never issue certificates.'}
    elif name=='getAnalytics':data={'readiness':s.readiness,'advisory':s.analytics,'history':s.events[:10],
        'progressPrediction':{'available':False,'reason':'No calibrated outcome forecasting model is installed. Synthetic learning-risk scores are advisory signals, not readiness forecasts.'}}
    elif name=='retrieveRAG':
        from ..services import rag
        passages=await rag.retrieve(call.query,tags=[call.skillId] if call.skillId else None,top_k=8)
        # Stable second-stage lexical/topic reranking of hybrid candidates.
        words=set(call.query.lower().split())
        passages.sort(key=lambda p:(-sum(w in p['title'].lower() for w in words if len(w)>3),-p['score']))
        data=[p for p in passages if p['score']>=.24][:3]
        from ..agents.proof import execution_context
        if execution_context.get():
            from ..rag.retrieval import retrieve
            owned=await retrieve(s.studentId,call.query,[])
            data=owned[:3]+data
    else:raise HTTPException(422,'Tool not allowed.')
    return ToolOutput(name=name,stateVersion=s.stateVersion,data=safe(data))
