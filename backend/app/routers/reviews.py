"""Authorized human rubric reviews; no untrusted code runs on the API host."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from ..security import StudentId, iso_now, new_id
from ..config import settings
from ..db import col
from ..engine import state
router=APIRouter(tags=['project-reviews'])
class CriterionReview(BaseModel):
    criterion: str = Field(min_length=1,max_length=300)
    score: int = Field(ge=0,le=100)
    evidence: str = Field(min_length=10,max_length=2000)
class Review(BaseModel):
    criteria: list[CriterionReview] = Field(min_length=1,max_length=30)
    feedback: str = Field(min_length=10,max_length=4000)

@router.post('/submissions/{submission_id}/review')
async def review(submission_id: str, payload: Review, reviewer: str = StudentId):
    user=await col('users').find_one({'studentId':reviewer})
    if user['email'].lower() not in settings.reviewer_emails:
        raise HTTPException(403,'An authorized reviewer account is required.')
    submission=await col('submissions').find_one({'id':submission_id})
    if not submission: raise HTTPException(404,'Submission not found.')
    if submission['studentId']==reviewer: raise HTTPException(403,'Reviewers cannot verify their own submissions.')
    project=await col('projects').find_one({'id':submission['projectId']})
    rubric=project.get('rubric',[])
    by_name={r.criterion:r for r in payload.criteria}
    if len(by_name)!=len(payload.criteria) or set(by_name)!={r['criterion'] for r in rubric}:
        raise HTTPException(422,'Review must address every rubric criterion exactly once.')
    weight=sum(r['weight'] for r in rubric)
    score=round(sum(by_name[r['criterion']].score*r['weight'] for r in rubric)/max(weight,1))
    passed=score>=80 and all(r.score>=60 for r in payload.criteria)
    sid=submission['studentId']
    result={'criteria':[r.model_dump() for r in payload.criteria],'score':score,'reviewerId':reviewer,'feedback':payload.feedback,'reviewedAt':iso_now()}
    await col('submissions').update_one({'id':submission_id},{'$set':{'rubricResult':result,'verificationState':'Verified' if passed else 'Needs Review'}})
    await col('evidence').update_many({'studentId':sid,'submissionId':submission_id},{'$set':{'superseded':True}})
    for skill_id in project.get('skillsValidated',[]):
        skill=await col('skills').find_one({'id':skill_id})
        record={'id':f'review-{submission_id}-{skill_id}','studentId':sid,'title':f"Reviewed project: {project['title']}",'type':'Project','skillId':skill_id,'skillName':skill['name'],'verificationState':'Verified' if passed else 'Needs Review','quality':'High','confidenceScore':score,'score':score,'date':iso_now()[:10],'source':submission['githubUrl'],'provenance':f'Authorized human rubric review {submission_id}; reviewer {reviewer}.','summary':payload.feedback,'rubricResult':result,'createdAt':iso_now()}
        await col('evidence').update_one({'studentId':sid,'id':record['id']},{'$set':record},upsert=True)
    updated=await state.recalculate(sid,events=[state.build_event('Project Reviewed',project['title'],payload.feedback,delta=str(score),link_tab='projects')])
    return {'verificationState':'Verified' if passed else 'Needs Review','rubricResult':result,'readiness':updated.readiness}

@router.get('/reviews/pending')
async def pending(reviewer: str = StudentId):
    user=await col('users').find_one({'studentId':reviewer})
    if user['email'].lower() not in settings.reviewer_emails:
        raise HTTPException(403,'An authorized reviewer account is required.')
    output=[]
    async for submission in col('submissions').find({'studentId':{'$ne':reviewer},'verificationState':{'$ne':'Verified'}}).limit(50):
        project=await col('projects').find_one({'id':submission['projectId']})
        output.append({'id':submission['id'],'projectTitle':project['title'],'githubUrl':submission['githubUrl'],'description':submission['description'],'rubric':project['rubric']})
    return output
