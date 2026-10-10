import copy
from app.engine.graph import concept_observations, project_graph

def test_latest_concept_observation_preserves_zero_and_sample_size():
    attempts=[{'id':'old','skillId':'s','createdAt':'2026-01-01','breakdown':[{'concept':'joins','correct':True}]},{'id':'new','skillId':'s','createdAt':'2026-02-01','breakdown':[{'concept':'joins','correct':False,'errorTags':['incorrect_or_missing_answer']},{'concept':'joins','correct':False}]}]
    original=copy.deepcopy(attempts)
    assert concept_observations([])==[]
    observed=concept_observations(attempts)
    assert len(observed)==1 and observed[0]['score']==0 and observed[0]['sampleSize']==2
    assert observed[0]['attemptId']=='new'
    assert observed[0]['errorTags']==['incorrect_or_missing_answer']
    assert attempts==original

def test_graph_trace_requires_valid_verifier_and_review():
    skills=[{'id':'a','name':'A','relatedConcepts':['shared']},{'id':'b','name':'B','prerequisites':['a'],'relatedConcepts':['shared']}]
    career={'id':'role','title':'Role','requirements':[{'skillId':'b','requiredMastery':80}]}
    evidence=[{'id':'claim','skillId':'b','type':'Manual Claim','verificationState':'Verified'},{'id':'proof','skillId':'b','type':'Assessment','verificationState':'Verified'},{'id':'stale','skillId':'b','type':'Assessment','verificationState':'Verified','superseded':True}]
    projects=[{'id':'p','title':'Project','skillsValidated':['b']}]
    graph=project_graph(skills,career,evidence,[{'id':'q','title':'Test','skillId':'b'}],[{'id':'r','title':'Lesson','skillId':'b'}],projects,[{'id':'pending','projectId':'p','verificationState':'Needs Review'},{'id':'reviewed','projectId':'p','verificationState':'Verified'}])
    assert {e['type'] for e in graph['edges']}=={'PREREQUISITE_OF','PART_OF','RELATED_TO','REQUIRED_FOR','ASSESSES','BUILDS','SUPPORTED_BY','VERIFIES','DEMONSTRATES'}
    assert [e['source'] for e in graph['edges'] if e['type']=='VERIFIES']==['evidence:proof']
    assert [e['source'] for e in graph['edges'] if e['type']=='DEMONSTRATES']==['submission:reviewed']
    assert all(e['source'] in {n['id'] for n in graph['nodes']} and e['target'] in {n['id'] for n in graph['nodes']} for e in graph['edges'])


def test_diagnostic_difficulty_tracks_mastery_and_ignores_missing_skills():
    from app.engine.diagnostic import select_bank
    from app.engine.competency import CompetencyNode
    from app.seed.assessments import ASSESSMENTS
    skill_id='prog-python-advanced'
    banks=[a for a in ASSESSMENTS if a['skillId']==skill_id]
    low=select_bank(banks,{skill_id:CompetencyNode(id=skill_id,name='Python',domain='Programming',mastery=15)})
    high=select_bank(banks,{skill_id:CompetencyNode(id=skill_id,name='Python',domain='Programming',mastery=90)})
    assert low['difficulty']=='Beginner'
    assert high['difficulty']=='Advanced'
    assert low['id']!=high['id']
    assert select_bank(banks,{}) is None
