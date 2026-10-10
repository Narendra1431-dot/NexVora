"""Finite, controlled workflow; the LLM writes answers, never chooses privileges."""
import importlib,json,re,os
from hashlib import sha256
from fastapi import HTTPException
from ..db import col
from ..security import iso_now
from ..services import llm,rag
from ..services.mentor_context import bounded_context,bounded_history
from ..intelligence.recommendations import recommend
from .models import ChatInput,ExecuteInput,safe
from .state import snapshot
from .execution import claim,finish,fail,execute_action

def route(query):
    q=query.lower()
    if any(w in q for w in ('coding','code solution','my rank','my xp')):return 'coding',['profile','coding','competency','rag']
    if re.search(r'^(?:please\s+)?(?:recalculate|recompute|refresh|update)\s+(?:(?:my|the)\s+)?roadmap\b',q.strip()):return 'recompute',['profile','competency','gap','roadmap']
    if any(w in q for w in ('this week','weekly','week plan')):return 'weekly_plan',['profile','competency','gap','roadmap','resources','assessment','rag']
    if any(w in q for w in ('certificate','certification','credential')):return 'certificate',['profile','career','gap','certificates','rag']
    if any(w in q for w in ('resume','résumé','ats','cv ')):return 'resume',['profile','resume','evidence','competency','gap','projects','assessment','rag']
    if 'project' in q:return 'project',['profile','competency','gap','projects','evidence','rag']
    if any(w in q for w in ('assessment','quiz','exam','misconception')):return 'assessment',['profile','competency','assessment','evidence','roadmap','rag']
    if any(w in q for w in ('resource','video','course','book','notes')):return 'resources',['profile','competency','gap','roadmap','resources','rag']
    if any(w in q for w in ('blocked','prerequisite','gap','weakest','learn next','what should i learn')):return 'next_action',['profile','competency','evidence','gap','roadmap','resources','rag']
    if any(w in q for w in ('readiness','career','progress','ready','risk')):return 'readiness',['profile','competency','career','evidence','gap','roadmap','analytics','rag']
    return 'general',['profile','rag']

def skill_for(query,s):
    words=set(re.findall(r'[a-z]+',query.lower()))-{'my','what','why','how','skill','learn','next','for','the','and','is','are','in','a','to'}
    ranked=[]
    for c in s.competencies:
        names=set(re.findall(r'[a-z]+',c['name'].lower()))
        score=len({w.rstrip('s') for w in words}&{w.rstrip('s') for w in names})
        if score:ranked.append((score,c['id']))
    return max(ranked)[1] if ranked else s.recommendations.get('skillId')

def urls(value):
    if isinstance(value,dict):return set().union(*(urls(v) for v in value.values())) if value else set()
    if isinstance(value,list):return set().union(*(urls(v) for v in value)) if value else set()
    return set(re.findall(r'https?://[^\s<>"\)]+',value)) if isinstance(value,str) else set()

def validate_answer(answer,passages,context):
    used=set(re.findall(r'\[(kb-[\w-]+)\]',answer))
    allowed={p['documentId'] for p in passages}
    if used-allowed:raise HTTPException(502,'Generated citation was not retrieved; answer rejected.')
    allowed_urls=urls(context)|urls(passages)
    if {u.rstrip('.,;') for u in urls(answer)}-{u.rstrip('.,;') for u in allowed_urls}:
        raise HTTPException(502,'Generated resource link was not verified in this context; answer rejected.')
    return [p for p in passages if p['documentId'] in used]

async def chat(payload:ChatInput,student_id):
    from ..runtime.redaction import redact
    if redact(payload.message)!=payload.message:raise HTTPException(422,'Remove credentials from your message. Secrets must not be sent to the Copilot.')
    run,replay=await claim(student_id,payload.requestId,{'message':payload.message},'chat')
    if replay is not None:return replay
    try:
        s=await snapshot(student_id)
        # Compound profile/resume planning is queued; keep short foreground
        # questions and existing explicit actions backward compatible.
        if re.search(r'\b(resume|profile)\b',payload.message,re.I) and re.search(r'\b(plan|planning)\b',payload.message,re.I):
            from .graph import create,StartRun
            queued=await create(StartRun(message=payload.message,requestId='dag-'+payload.requestId[:90]),student_id)
            response={'answer':'Your specialist workflow is queued. Open its live execution to inspect agents, tools, sources and the final proposal.',
                'sources':[],'relatedSkills':[],'evidence':[],'suggestedActions':[],'actionsPerformed':[],
                'agentRun':{'id':queued['id'],'agentsUsed':[],'toolsUsed':[],'status':'QUEUED','actions':[],'stateVersion':s.stateVersion}}
            for role,content in [('user',payload.message),('assistant',response['answer'])]:
                await col('agent_messages').update_one({'studentId':student_id,'id':run['id']+'-'+role},{'$setOnInsert':{'role':role,'content':content,'createdAt':iso_now(),'runId':queued['id']}},upsert=True)
            await finish(run,response,stateVersion=s.stateVersion,toolsUsed=[],agentsUsed=[])
            return response
        # Explicit workspace commands mirror Open Dots parsing, without shell interpretation.
        proposed=None
        if payload.message.strip().lower().startswith('/workspace '):
            import shlex
            header,*body=payload.message.strip().split('\n',1)
            try:parts=shlex.split(header)
            except ValueError:raise HTTPException(422,'Invalid workspace command.')
            if len(parts)<3 or parts[1] not in ('read','write') or (parts[1]=='read' and len(parts)!=3):raise HTTPException(422,'Use /workspace read filename.txt or /workspace write filename.txt followed by quoted content.')
            content=body[0] if body else ' '.join(parts[3:])
            if parts[1]=='write' and not content:raise HTTPException(422,'Provide the note content after the filename.')
            proposed=('workspace.'+parts[1],{'fileName':parts[2],'content':content})
        elif re.match(r'^(?:please\s+)?(?:generate|create|build)\s+(?:my\s+)?resume\b',payload.message.strip(),re.I):proposed=('generate_resume',{})
        elif re.match(r'^(?:please\s+)?export\s+(?:my\s+)?resume\b',payload.message.strip(),re.I):
            draft=await col('resume_drafts').find_one({'studentId':student_id},sort=[('updatedAt',-1)])
            if not draft:raise HTTPException(422,'Generate and review a resume draft in Resume Intelligence first.')
            proposed=('workspace.exportResume',{'draftId':draft['draftId'],'version':draft['version'],'fileName':'resume-'+run['id']+'.pdf'})
        elif re.match(r'^(?:please\s+)?export\s+(?:my\s+)?roadmap\b',payload.message.strip(),re.I):proposed=('workspace.exportRoadmap',{'fileName':'roadmap-'+run['id']+'.json'})
        if proposed:
            from ..runtime.gateway import propose,ToolRequest
            approval=await propose(student_id,ToolRequest(toolName=proposed[0],arguments=proposed[1],requestId='chat-'+payload.requestId,expectedStateVersion=s.stateVersion))
            response={'answer':'Review the proposed action in Agent approvals. Nothing has been executed.','sources':[],
                'relatedSkills':[],'evidence':[],'suggestedActions':[],'nextBestAction':recommend(s),'approval':approval,'actionsPerformed':[],
                'agentRun':{'id':run['id'],'agentsUsed':['Supervisor'],'toolsUsed':[proposed[0]],'reasonCodes':['APPROVAL_REQUIRED'],'citations':[],'status':'pending_approval','actions':[],'stateVersion':s.stateVersion}}
            await finish(run,response,stateVersion=s.stateVersion,toolsUsed=[proposed[0]],agentsUsed=['Supervisor'])
            return response
        intent,names=route(payload.message);sid=skill_for(payload.message,s)
        for word,module in [('assessment','assessment'),('project','projects'),('certificate','certificates')]:
            if word in payload.message.lower() and module not in names:names.insert(-1,module)
        results={};agents=[];tools=[];errors=[];actions=[]
        for name in names:
            specialist=importlib.import_module('app.agents.'+name)
            try:
                filter_skill=sid if intent!='general' else None
                if name=='rag' and intent not in ('next_action','resources'):filter_skill=None
                outputs=await specialist.run(s,payload.message,filter_skill)
                for output in outputs:results[output.name]=output.data;tools.append(output.name)
                agents.append(specialist.NAME)
            except Exception as exc:
                errors.append({'agent':specialist.NAME,'code':type(exc).__name__})
        explicit_plan=intent=='weekly_plan' and bool(re.match(r'^(?:please\s+)?(?:create|make|save|build|schedule|plan)\b',payload.message.strip(),re.I))
        if intent=='recompute' or explicit_plan:
            action='recomputeRoadmap' if intent=='recompute' else 'planWeek'
            result=await execute_action(ExecuteInput(action=action,requestId='chat-action-'+sha256(payload.requestId.encode()).hexdigest(),expectedStateVersion=s.stateVersion),student_id)
            if result['status']=='pending_approval':
                response={'answer':'Review the proposed action in Agent approvals. Nothing has been changed.','sources':[],
                    'relatedSkills':[],'evidence':[],'suggestedActions':[],'nextBestAction':recommend(s),
                    'actionsPerformed':[],'approval':result['approval'],
                    'agentRun':{'id':run['id'],'agentsUsed':['Supervisor','Roadmap'],'toolsUsed':[action],'reasonCodes':['APPROVAL_REQUIRED'],'citations':[],'intent':intent,'status':'pending_approval','stateVersion':s.stateVersion,'actions':[]}}
                for role,content in [('user',payload.message),('assistant',response['answer'])]:
                    await col('agent_messages').update_one({'studentId':student_id,'id':run['id']+'-'+role},{'$setOnInsert':{'role':role,'content':content,'createdAt':iso_now(),'runId':run['id']}},upsert=True)
                await finish(run,response,stateVersion=s.stateVersion,toolsUsed=[action],agentsUsed=['Supervisor','Roadmap'])
                return response
            actions.append({'label':action,'status':result['status'],'result':result['result']})
            if intent=='recompute':s=await snapshot(student_id)
        rec=recommend(s)
        passages=results.get('retrieveRAG',[])[:3]
        context={'targetCareer':s.targetCareer.get('title'),'readiness':s.readiness,'stateVersion':s.stateVersion,
                 'skills':s.competencies,'evidence':s.evidence,'profile':s.profile,'roadmap':s.roadmap,
                 'resources':s.resources,'nextAction':s.recommendations}
        blocks=bounded_context(context,passages,payload.message)
        # Excerpts remain JSON values, never promoted to instruction text.
        excerpts={k:v for k,v in results.items() if k not in {'getCompetencies','getEvidence','getStudentProfile','retrieveRAG'}}
        extras={'toolResults':excerpts}
        blocks.append({'actionsPerformed':actions,'nextBestAction':rec})
        serialized=json.dumps(extras,ensure_ascii=False)
        blocks.append({'dataExcerpt':serialized[:12000],'excerptMayBeTruncated':len(serialized)>12000})
        stored=[m async for m in col('agent_messages').find({'studentId':student_id},{'_id':0}).sort('_id',-1).limit(8)]
        history=[{'role':m['role'],'content':m['content']} for m in reversed(stored)] or [h.model_dump() for h in payload.history]
        await col('agent_runs').update_one({'id':run['id'],'studentId':student_id},{'$set':{'intent':intent,'agentsUsed':['Supervisor']+agents,'toolsUsed':tools,'actions':actions,'stateVersion':s.stateVersion}})
        brain_reply=None
        try:
            if os.getenv('ENABLE_CENTRAL_BRAIN','false').lower()=='true' and not actions:
                from ..brain.orchestrator import query as brain_query
                from ..providers.base import ProviderError
                try:brain_reply=await brain_query(student_id,payload.message,require_sources=bool(re.search(r'(my course material|my textbook|uploaded document)',payload.message,re.I)))
                except ProviderError as exc:raise HTTPException(503,'Career reasoning unavailable: '+exc.code)
                answer=brain_reply['answer']['summary']
                if brain_reply['answer']['recommendations']:answer+='\n\n'+'\n'.join(brain_reply['answer']['recommendations'])
            else:answer=await llm.generate(payload.message,context_blocks=blocks,history=bounded_history(history),max_tokens=1800)
        except HTTPException as exc:
            if actions:raise HTTPException(exc.status_code,str(exc.detail)+' The requested action completed; inspect Career activity before retrying.') from exc
            raise
        cited=[] if brain_reply else validate_answer(answer,passages,blocks)
        answer_sources=[{'documentId':v['documentId'],'title':v.get('title') or v['source'],'source':v['source'],'page':v.get('page'),'chunkId':v['id']} for v in brain_reply['sources']] if brain_reply else rag.citations(cited)
        latest=await col('profiles').find_one({'studentId':student_id},{'stateVersion':1}) or {}
        stale=latest.get('stateVersion',0)!=s.stateVersion
        if stale:answer+='\n\nYour learning state changed while this answer was prepared. Refresh recommendations before acting.'
        run_public={'id':run['id'],'agentRunId':run['id'],'intent':intent,'agentsUsed':['Supervisor']+agents,
                    'toolsUsed':tools,'stateVersion':s.stateVersion,'reasonCodes':['CANONICAL_STUDENT_STATE','ALLOWLISTED_TOOLS','CITATION_VALIDATED'],
                    'citations':answer_sources,'actions':actions,'status':'completed','partialContext':bool(errors),'stale':stale,'errors':errors,'createdAt':run['createdAt']}
        response={'answer':answer,'sources':answer_sources,'relatedSkills':s.competencies,'evidence':s.evidence,
                  'suggestedActions':[s.recommendations],'nextBestAction':rec,'agentRun':run_public,'actionsPerformed':actions}
        for role,content in [('user',payload.message),('assistant',answer)]:
            await col('agent_messages').update_one({'studentId':student_id,'id':run['id']+'-'+role},{'$setOnInsert':{'role':role,'content':content,'createdAt':iso_now(),'runId':run['id']}},upsert=True)
        await col('agent_memory').update_one({'studentId':student_id},{'$set':{'lastIntent':intent,'lastStateVersion':s.stateVersion,'updatedAt':iso_now()}},upsert=True)
        await finish(run,response,**{k:v for k,v in run_public.items() if k not in {'id','agentRunId','createdAt','status'}})
        return response
    except Exception as exc:
        await fail(run,exc)
        raise
