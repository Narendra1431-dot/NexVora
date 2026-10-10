"""One read-only projection of existing deterministic domain state."""
from fastapi import HTTPException
from ..db import col
from ..engine import state
from ..ml.inference.ranker import rank,rank_projects
from ..ml.inference.advisory import summarize
from .models import CanonicalState,safe

async def snapshot(student_id, *, derived=None, profile=None, career=None):
    for _ in range(3):
        profile=profile or await col('profiles').find_one({'studentId':student_id})
        if not profile:raise HTTPException(404,'Student profile not found.')
        version=profile.get('stateVersion',0)
        career=career or await state.load_career(student_id,profile) or {}
        result=derived or await state.recalculate(student_id,profile=profile,career=career,persist=False)
        resources=[r async for r in col('resources').find({},{'_id':0})]
        assessments=[a async for a in col('assessments').find({},{'_id':0,'questions':0})]
        attempts=[a async for a in col('attempts').find({'studentId':student_id},{'_id':0,'answers':0}).sort('createdAt',-1).limit(30)]
        certificates=[c async for c in col('certificates').find({'studentId':student_id},{'_id':0,'pdf':0}).limit(50)]
        events=[e async for e in col('events').find({'studentId':student_id},{'_id':0}).sort('createdAt',-1).limit(30)]
        latest=await col('profiles').find_one({'studentId':student_id},{'stateVersion':1}) or {}
        if latest.get('stateVersion',0)!=version:
            profile=career=derived=None
            continue
        nodes=result.competencies
        from ..coding.xp import leaderboard
        ranking=next(r for r in await leaderboard(student_id) if r['isCurrent'])
        coding_progress=[safe(p) async for p in col('coding_progress').find({'studentId':student_id})]
        from ..engine.graph import concept_observations
        concepts=concept_observations(attempts)
        return CanonicalState(studentId=student_id,stateVersion=version,
            concepts=concepts,codingProgress=coding_progress,xp=ranking['overallXP'],rank=ranking['rank'],
            profile={k:profile.get(k) for k in ('name','weeklyAvailabilityHours','learningPreferences','resourceProgress')},
            targetCareer=safe(career),competencies=safe(nodes),mastery={n['id']:n['mastery'] for n in nodes},
            confidence={n['id']:n['confidence'] for n in nodes},evidence=safe(result.evidence),
            careerGaps=safe([n for n in nodes if n.get('careerRequired') and (n['state']!='Verified' or n['mastery']<n['targetLevel'])]),
            readiness=result.readiness,roadmap=safe(result.milestones),
            resources=safe(rank(resources,nodes,profile.get('weeklyAvailabilityHours') or 0)),
            assessments=safe(assessments),assessmentHistory=safe(attempts),
            projects=safe(rank_projects(result.projects,nodes,profile.get('weeklyAvailabilityHours') or 0)),
            resume=safe(result.resume),certificates=safe(certificates),recommendations=safe(result.mission),events=safe(events),
            analytics=summarize(nodes,result.evidence,profile,attempts))
    raise HTTPException(409,'Student state changed during analysis. Retry with the latest state.')
