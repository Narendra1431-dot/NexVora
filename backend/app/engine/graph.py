"""Read-only graph projections from canonical catalogs and student evidence."""
from collections import defaultdict
from hashlib import sha256
from .competency import EVIDENCE_PROFILE


def concept_observations(attempts):
    """Latest observation per skill/topic; absence means unassessed, never zero."""
    latest={}
    for attempt in sorted(attempts,key=lambda a:(a.get('createdAt',''),a['id']),reverse=True):
        groups=defaultdict(list)
        for item in attempt.get('breakdown',[]):
            if item.get('concept'): groups[item['concept']].append(item)
        for concept,items in groups.items():
            key=f"{attempt.get('skillId')}:{concept}"
            if key in latest: continue
            latest[key]={'id':key,'skillId':attempt.get('skillId'),'name':concept,'score':round(100*sum(bool(q.get('correct')) for q in items)/len(items)),'attemptId':attempt['id'],'assessedAt':attempt.get('createdAt'),'verification':'assessment_observation','sampleSize':len(items),'errorTags':sorted({tag for q in items for tag in q.get('errorTags',[])})}
    return list(latest.values())


def project_graph(skills, career, evidence, assessments, resources, projects, submissions):
    nodes={}; edges={}
    def node(kind,ident,label):
        key=f'{kind}:{ident}'
        nodes[key]={'id':key,'kind':kind,'sourceId':ident,'label':label}
        return key
    def edge(kind,source,target,reason):
        key=sha256(f'{kind}:{source}:{target}'.encode()).hexdigest()[:24]
        edges[key]={'id':key,'type':kind,'source':source,'target':target,'reason':reason}
    known={s['id'] for s in skills}
    shared=defaultdict(list)
    for skill in skills: node('skill',skill['id'],skill['name'])
    for skill in skills:
        sid='skill:'+skill['id']
        for prereq in skill.get('prerequisites',[]):
            if prereq in known: edge('PREREQUISITE_OF','skill:'+prereq,sid,'Declared catalog prerequisite')
        for concept in skill.get('relatedConcepts',[]):
            normalized=' '.join(concept.casefold().split())
            cid=node('concept',sha256(normalized.encode()).hexdigest()[:16],concept)
            edge('PART_OF',cid,sid,'Declared concept coverage')
            shared[cid].append(sid)
    for cid,members in shared.items():
        for i,source in enumerate(sorted(set(members))):
            for target in sorted(set(members))[i+1:]:
                edge('RELATED_TO',source,target,'Shared concept: '+nodes[cid]['label'])
    if career:
        cid=node('career',career['id'],career['title'])
        for requirement in career.get('requirements',[]):
            if requirement['skillId'] in known: edge('REQUIRED_FOR','skill:'+requirement['skillId'],cid,f"Target mastery {requirement.get('requiredMastery',requirement.get('targetLevel',0))}%")
    for assessment in assessments:
        if assessment.get('skillId') in known:
            aid=node('assessment',assessment['id'],assessment['title'])
            edge('ASSESSES',aid,'skill:'+assessment['skillId'],'Server-scored assessment bank')
    for resource in resources:
        if resource.get('skillId') in known:
            rid=node('resource',resource['id'],resource['title'])
            edge('BUILDS',rid,'skill:'+resource['skillId'],'Learning resource; completion alone is not verification')
    for project in projects:
        pid=node('project',project['id'],project['title'])
        for skill_id in project.get('skillsValidated',[]):
            if skill_id in known: edge('ASSESSES',pid,'skill:'+skill_id,'Project rubric targets this skill')
    for item in evidence:
        if item.get('superseded') or item.get('skillId') not in known: continue
        eid=node('evidence',item['id'],item.get('title','Evidence'))
        sid='skill:'+item['skillId']
        edge('SUPPORTED_BY',sid,eid,'Recorded evidence: '+item.get('verificationState','Unverified'))
        if item.get('verificationState')=='Verified' and EVIDENCE_PROFILE.get(item.get('type'),{}).get('verifies'):
            edge('VERIFIES',eid,sid,'Verified observation; overall skill still depends on aggregate mastery and prerequisites')
    by_project={p['id']:p for p in projects}
    for submission in submissions:
        if submission.get('verificationState')!='Verified': continue
        pid=node('submission',submission['id'],'Reviewed '+by_project.get(submission['projectId'],{}).get('title','project'))
        for skill_id in by_project.get(submission['projectId'],{}).get('skillsValidated',[]):
            if skill_id in known: edge('DEMONSTRATES',pid,'skill:'+skill_id,'Authorized rubric review passed')
    return {'nodes':sorted(nodes.values(),key=lambda n:n['id']),'edges':sorted(edges.values(),key=lambda e:e['id'])}
