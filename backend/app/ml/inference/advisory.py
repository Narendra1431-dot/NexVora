"""Safe inference for synthetic advisory models. Never changes competency state."""
import json
import math
from pathlib import Path
from functools import lru_cache
from datetime import datetime, timezone

@lru_cache(maxsize=2)
def load(name):
    if name not in {'evidence-strength','learning-risk'}: raise ValueError('Unknown model')
    data=json.loads((Path(__file__).resolve().parents[1]/f'models/{name}.json').read_text())
    return data

def predict(name, features):
    data=load(name)
    if len(features)!=len(data['features']) or not all(isinstance(v,(float,int)) and math.isfinite(v) and 0<=v<=1 for v in features):
        raise ValueError('Expected five normalized finite features')
    if data['task']=='classification':
        logits=[b+sum(a*v for a,v in zip(row,features)) for row,b in zip(data['coefficients'],data['intercept'])]
        scores=[math.exp(x-max(logits)) for x in logits]
        probabilities=[s/sum(scores) for s in scores]
        index=max(range(len(scores)),key=scores.__getitem__)
        return {'label':['weak','moderate','strong'][data['classes'][index]],'probabilities':dict(zip(['weak','moderate','strong'],map(lambda p:round(p,4),probabilities))),'modelVersion':data['modelVersion']}
    value=max(0,min(1,data['intercept']+sum(a*v for a,v in zip(data['coefficients'],features))))
    return {'score':round(value,4),'level':'high' if value>=.65 else 'moderate' if value>=.35 else 'low','modelVersion':data['modelVersion']}

def summarize(competencies, evidence, profile, attempts):
    required={c['id'] for c in competencies if c.get('careerRequired')}
    observations=[]
    now=datetime.now(timezone.utc)
    for item in evidence:
        if item.get('superseded'): continue
        recency=0.5
        try:
            date=datetime.fromisoformat(item.get('date','').replace('Z','+00:00'))
            if date.tzinfo is None: date=date.replace(tzinfo=timezone.utc)
            recency=max(0,1-max(0,(now-date).days)/365)
        except (ValueError,TypeError): pass
        quality={'Low':.25,'Medium':.5,'High':.85}.get(item.get('quality'),.5)
        features=[max(0,min(1,float(item.get('score') or 0)/100)),quality,float(bool(item.get('provenance'))),float(item.get('skillId') in required),recency]
        observations.append({'evidenceId':item.get('id'),**predict('evidence-strength',features)})
    nodes=[c for c in competencies if c.get('careerRequired')]
    mastery=sum(c.get('mastery',0)/100 for c in nodes)/max(1,len(nodes))
    gap=sum(max(0,c.get('targetLevel',85)-c.get('mastery',0))/100 for c in nodes)/max(1,len(nodes))
    completed=sum(bool(r.get('completed')) for r in profile.get('resourceProgress',{}).values())
    engagement=min(1,(len(attempts)+completed)/10)
    strength=sum({'weak':.2,'moderate':.5,'strong':.8}[r['label']] for r in observations)/max(1,len(observations))
    time_fit=min(1,(profile.get('weeklyAvailabilityHours') or 0)/10)
    features=[mastery,gap,engagement,strength,time_fit]
    return {'trainingData':'synthetic_demo','advisoryOnly':True,'limitation':'Demonstration predictions, not measured learner outcomes. Evidence labels never grant verification. Engagement uses recorded attempts and completed resources, not time tracking.','learningRisk':{**predict('learning-risk',features),'features':dict(zip(load('learning-risk')['features'],features))},'evidenceStrength':observations}
