"""Idempotent adaptation after deterministic state commits; no LLM execution."""
from pymongo.errors import DuplicateKeyError
from ..db import col
from ..security import iso_now
from ..intelligence.recommendations import recommend

async def publish(s, trigger='State Updated'):
    recommendation=recommend(s)
    from ..agents.models import ToolInput
    from ..tools.registry import execute
    for name in ('getEvidence','getCompetencies','calculateReadiness','getRoadmap'):
        await execute(ToolInput(name=name),s)
    certificate_result=await execute(ToolInput(name='checkCertificateEligibility'),s)
    recommendation['certifications']={
        'courses':[{k:c.get(k) for k in ('courseId','courseName','eligible','reasons')} for c in certificate_result.data['courses']],
        'external':certificate_result.data['external']}
    await col('agent_recommendations').update_one({'studentId':s.studentId,'stateVersion':s.stateVersion},
        {'$setOnInsert':{'studentId':s.studentId,**recommendation}},upsert=True)
    timeline=[{'label':trigger,'status':'completed'},
              {'label':'Evidence cross-checked against owned records','status':'completed'},
              {'label':'Competency and readiness recalculated','status':'completed'},
              {'label':'Roadmap and learning priorities adapted','status':'completed'},
              {'label':'Next action recommended','status':'completed'}]
    doc={'id':f'workflow-{s.stateVersion}','agentRunId':f'workflow-{s.stateVersion}','studentId':s.studentId,
         'kind':'workflow','intent':trigger,'agentsUsed':['Evidence','Competency','Career','Roadmap','Certificate'],
         'toolsUsed':['getEvidence','getCompetencies','calculateReadiness','getRoadmap','checkCertificateEligibility'],
         'stateVersion':s.stateVersion,'reasonCodes':['DOMAIN_STATE_COMMITTED','NO_LLM_SCORE_MUTATION'],
         'citations':[],'actions':timeline,'status':'completed','createdAt':iso_now()}
    try:await col('agent_runs').insert_one(doc)
    except DuplicateKeyError:
        await col('agent_runs').update_one({'studentId':s.studentId,'id':doc['id'],'status':'failed'},{'$set':{k:v for k,v in doc.items() if k!='_id'}})
    return recommendation

async def after_commit(student_id,result,profile,career,events):
    from ..agents.state import snapshot
    profile={**profile,'stateVersion':(await col('profiles').find_one({'studentId':student_id},{'stateVersion':1}) or {}).get('stateVersion',0)}
    s=await snapshot(student_id,derived=result,profile=profile,career=career)
    await publish(s,(events or [{}])[0].get('title','Student state updated'))

    # Persist a deduplicated outbox job; never invoke an LLM in a domain commit.
    from ..workers.tasks import IN_WORKER
    if events and not IN_WORKER.get():
        from ..workers.queue import enqueue
        await enqueue(student_id,'student_intelligence_refresh',[],f'state-refresh-{s.stateVersion}',state_version=s.stateVersion)
