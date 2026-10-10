"""Resources-only learning content and PDF cache over the existing competency engine."""
import hashlib,json
from pathlib import Path
from urllib.parse import quote
from fastapi import APIRouter,HTTPException,Response,BackgroundTasks
from starlette.concurrency import run_in_threadpool
from ..db import col
from ..security import StudentId,iso_now
from ..engine import state
from ..services.learning_catalog import TOPICS
from ..services.learning_pdf import render_book
from ..services.learning_content import valid_chapter
from ..services import learning_videos

router=APIRouter(prefix='/learning-hub',tags=['learning-hub'])
ASSETS=Path(__file__).resolve().parents[1]/'assets'/'learning'

def closure(requirements,skills):
    result=[];done=set();active=set()
    def visit(id):
        if id in done:return
        if id in active:raise HTTPException(422,'Career prerequisite graph contains a cycle.')
        if id not in skills:raise HTTPException(422,'Career references an unavailable competency: '+id)
        active.add(id)
        for parent in skills[id].get('prerequisites',[]):visit(parent)
        active.remove(id);done.add(id);result.append(id)
    for req in requirements:visit(req['skillId'])
    return result

async def curriculum(career_id):
    career=await col('careers').find_one({'id':career_id},{'_id':0})
    if not career:raise HTTPException(404,'Target objective not found.')
    skills={s['id']:s async for s in col('skills').find({},{'_id':0})}
    ids=closure(career['requirements'],skills)
    videos_path=ASSETS/'videos.json'
    videos=json.loads(videos_path.read_text(encoding='utf-8')) if videos_path.exists() else {}
    chapters=[]
    for id in ids:
        s=skills[id];path=ASSETS/(id+'.json');notes=json.loads(path.read_text(encoding='utf-8')) if path.exists() else None
        reference=TOPICS.get(id)
        # A changed curriculum must not silently reuse an incomplete chapter.
        ready=bool(reference and valid_chapter(notes,s.get('relatedConcepts',[])))
        chapter={'id':id,'name':s['name'],'domain':s['domain'],'concepts':s.get('relatedConcepts',[]),'prerequisites':s.get('prerequisites',[]),
                 'prerequisiteNames':[skills[p]['name'] for p in s.get('prerequisites',[])],
                 'notes':notes if ready else None,'notesReady':ready,'textbooks':reference[2] if reference else [],
                 'referenceUrl':reference[3] if reference else None,'videos':videos.get(id,[])}
        chapters.append(chapter)
        signature=hashlib.sha256(json.dumps(chapter,sort_keys=True).encode()).hexdigest()
        await col('learning_topics').update_one({'id':id,'signature':signature},{'$setOnInsert':{**chapter,'signature':signature,'difficulty':['Beginner','Intermediate','Advanced'],'source':'NexVora authored curriculum and linked primary references','lastVerifiedAt':max((v['lastVerifiedAt'] for v in videos.get(id,[])),default=None),'cachedAt':iso_now()}},upsert=True)
    return career,chapters

@router.get('/{career_id}')
async def hub(career_id:str,background_tasks:BackgroundTasks,student_id:str=StudentId):
    career,chapters=await curriculum(career_id)
    result=await state.recalculate(student_id,career=career,persist=False)
    nodes={c['id']:c for c in result.competencies};milestones={m['skillId']:m for m in result.milestones}
    profile=await col('profiles').find_one({'studentId':student_id}) or {}
    assessments=[a async for a in col('assessments').find({},{'_id':0,'id':1,'title':1,'skillId':1})]
    resource_progress=profile.get('resourceProgress',{})
    resources=[r async for r in col('resources').find({'skillId':{'$in':[c['id'] for c in chapters]}},{'_id':0})]
    topics=[];stale_videos=[]
    for chapter in chapters:
        chapter['videos'],stale=await learning_videos.cached(chapter['videos']);stale_videos.extend(stale)
        id=chapter['id'];node=nodes.get(id,{});milestone=milestones.get(id,{})
        mastery=node.get('mastery',0);target=milestone.get('masteryTarget',node.get('targetLevel',85))
        completed=mastery>=target and node.get('state')=='Verified'
        locked=bool(node.get('unmetPrerequisites'))
        started=any(resource_progress.get(r['id'],{}).get('completed') for r in resources if r['skillId']==id)
        status='Completed' if completed else 'Locked/Prerequisite' if locked else 'In Progress' if mastery>0 or started else 'Ready to Start'
        topics.append({**{k:v for k,v in chapter.items() if k!='notes'},'mastery':mastery,'target':target,'status':status,
                       'difficulty':'Beginner' if mastery<40 else 'Advanced' if mastery>=75 else 'Intermediate',
                       'reason':milestone.get('reason','Start with the foundations and complete the practice questions.'),
                       'blockedBy':node.get('unmetPrerequisites',[]),'assessments':[a for a in assessments if a['skillId']==id],
                       'roadmapOrder':milestone.get('order'),'wordCount':(chapter['notes'] or {}).get('wordCount',0)})
    if stale_videos:background_tasks.add_task(learning_videos.refresh,list(dict.fromkeys(stale_videos)))
    actionable=[t for t in topics if t['status'] in ('In Progress','Ready to Start')]
    if actionable:min(actionable,key=lambda t:t['roadmapOrder'] or 999)['status']='Recommended Next'
    priority={'Recommended Next':0,'In Progress':1,'Ready to Start':2,'Locked/Prerequisite':3,'Completed':4}
    topics.sort(key=lambda t:(priority[t['status']],t['roadmapOrder'] or 999))
    signature=hashlib.sha256(json.dumps([(c['id'],c['concepts']) for c in chapters],sort_keys=True).encode()).hexdigest()
    await col('learning_careers').update_one({'careerId':career_id},{'$set':{'careerId':career_id,'title':career['title'],'topicIds':[c['id'] for c in chapters],'signature':signature,'updatedAt':iso_now()}},upsert=True)
    return {'career':{'id':career_id,'title':career['title'],'description':career['description']},'readiness':result.readiness,'topics':topics,
            'notesReady':all(c['notesReady'] for c in chapters),'missingNotes':[c['name'] for c in chapters if not c['notesReady']],
            'coverage':{'requirements':len(career['requirements']),'totalTopics':len(chapters),'readyTopics':sum(c['notesReady'] for c in chapters)},
            'resourceIds':[r['id'] for r in resources], 'videoPolicy':'Curated English videos ranked by exact-topic relevance, reputable source, then observed views. Counts are snapshots, not a claim of the most viewed videos on all of YouTube.'}

@router.get('/{career_id}/notes')
async def notes(career_id:str,topic_id:str|None=None,_:str=StudentId):
    career,chapters=await curriculum(career_id)
    if topic_id:
        chapters=[c for c in chapters if c['id']==topic_id]
        if not chapters:raise HTTPException(404,'Topic is not part of this target objective.')
    if not all(c['notesReady'] for c in chapters):raise HTTPException(503,'Notes for this curriculum are not fully available yet. No incomplete PDF will be labeled complete.')
    return {'career':career['title'],'chapters':chapters}

@router.get('/{career_id}/pdf')
async def pdf(career_id:str,topic_id:str|None=None,_:str=StudentId):
    data=await notes(career_id,topic_id,_)
    title=data['chapters'][0]['name'] if topic_id else data['career']
    # Content hash invalidates PDFs when notes, prerequisites, bibliography or title change.
    key=hashlib.sha256(('study-pdf-v2'+json.dumps(data,sort_keys=True)).encode()).hexdigest()
    cached=await col('learning_pdfs').find_one({'key':key})
    if not cached:
        blob=await run_in_threadpool(render_book,title,data['chapters'],'The selected career requirements and all transitive prerequisites in the current NexVora catalog.')
        await col('learning_pdfs').update_one({'key':key},{'$setOnInsert':{'key':key,'career':career_id,'topic':topic_id,'pdf':blob,'source':'NexVora learning notes','createdAt':iso_now()}},upsert=True)
    else:blob=bytes(cached['pdf'])
    filename=quote(title+' Complete Learning Notes.pdf',safe='')
    return Response(blob,media_type='application/pdf',headers={'Content-Disposition':"attachment; filename*=UTF-8''"+filename,'X-Content-Type-Options':'nosniff'})
