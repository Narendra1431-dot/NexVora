"""Explainable recommendations; no model-generated scores or verification."""
from ..security import iso_now

def recommend(s):
    mission=s.recommendations
    skill=next((c for c in s.competencies if c['id']==mission.get('skillId')),None)
    sid=(skill or {}).get('id')
    evidence=[e for e in s.evidence if e.get('skillId')==sid]
    assessments=[a for a in s.assessments if a.get('skillId')==sid]
    assessments.sort(key=lambda a:abs({'Beginner':20,'Intermediate':55,'Advanced':80}.get(a.get('difficulty'),50)-(skill or {}).get('mastery',0)))
    resources=[r for r in s.resources if r.get('skillId')==sid]
    preferences=s.profile.get('learningPreferences') or []
    resources.sort(key=lambda r:(not any(str(p).lower() in (r.get('type','')+' '+r.get('provider','')).lower() for p in preferences),-r.get('rankingScore',0)))
    projects=[p for p in s.projects if sid in p.get('skillsValidated',[])]
    blocks=[c['name'] for c in s.competencies if sid in c.get('prerequisiteChain',[]) and c.get('careerRequired')]
    actions=[]
    if sid:
        actions.append({'label':'Learn Now','tab':'resources','skillId':sid,'id':resources[0]['id'] if resources else None})
        if assessments:actions.append({'label':'Take Assessment','tab':'assessments','id':assessments[0]['id'],'skillId':sid})
        if projects:actions.append({'label':'Build Proof','tab':'projects','id':projects[0]['id'],'skillId':sid})
        actions.append({'label':'Why This?','tab':'competencies','skillId':sid})
    unsupported=[c for c in s.resume.get('claims',[]) if c.get('evidenceState')!='Verified']
    return {'stateVersion':s.stateVersion,'careerId':s.targetCareer.get('id'),'title':mission.get('title','Review your career objective'),
        'reason':mission.get('reason','Choose a target objective to create a learning plan.'),'skillId':sid,
        'currentMastery':(skill or {}).get('mastery'),'targetMastery':(skill or {}).get('targetLevel'),
        'confidence':(skill or {}).get('confidence'),'blocks':blocks,'currentReadiness':s.readiness,
        'readinessImpact':'Readiness changes only after scored or reviewed evidence; no improvement is guaranteed.',
        'evidenceUsed':[{'id':e.get('id'),'title':e.get('title'),'verificationState':e.get('verificationState')} for e in evidence],
        'missingEvidence':not any(e.get('verificationState')=='Verified' for e in evidence),
        'resources':resources[:3],'assessment':assessments[0] if assessments else None,'project':projects[0] if projects else None,
        'resumeAction':{'unsupportedClaims':len(unsupported),'tab':'resume','reason':'Build assessment or project proof for unsupported claims.'} if s.resume else None,
        'actions':actions,'reasonCodes':['DETERMINISTIC_MISSION','PREREQUISITE_ORDER','VERIFIED_EVIDENCE_ONLY'],
        'generatedAt':iso_now()}

def weekly_plan(s):
    available=max(0,s.profile.get('weeklyAvailabilityHours') or 0)
    remaining=available;items=[]
    for m in s.roadmap:
        if m.get('state',m.get('status')) in ('Completed','Blocked','Locked'):continue
        hours=min(2,remaining)
        if hours<=0:break
        items.append({'skillId':m['skillId'],'title':m.get('title',m.get('skillName','Learning milestone')),
                      'hours':hours,'reason':m.get('reason'),'assessmentId':m.get('assessmentId'),
                      'resourceIds':m.get('resourceIds',[]),'status':'Suggested, not booked'})
        remaining-=hours
    return {'stateVersion':s.stateVersion,'availableHours':available,'allocatedHours':available-remaining,'items':items,
            'note':'Suggested study blocks, not calendar appointments or promised completion. Set weekly availability in Profile to allocate time.'}
