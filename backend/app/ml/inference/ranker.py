"""Safe JSON-only model loading: no pickle or executable artifact loading."""
import json
import math
import re
from functools import lru_cache
from pathlib import Path
@lru_cache(maxsize=1)
def model():
    data = json.loads((Path(__file__).resolve().parents[1]/'models/ranker.json').read_text())
    if len(data['coefficients']) != 5 or not all(math.isfinite(v) for v in data['coefficients']):
        raise ValueError('Invalid ranking artifact')
    return data

def predict(features):
    if len(features)!=5 or not all(math.isfinite(v) and 0<=v<=1 for v in features): raise ValueError('Features must be five normalized finite numbers')
    data=model()
    return max(0,min(1,data['intercept']+sum(a*b for a,b in zip(features,data['coefficients']))))

def rank(resources, competencies, hours=10):
    by_id={c['id']:c for c in competencies}
    ranked=[]
    for r in resources:
        c=by_id.get(r.get('skillId'),{})
        mastery=c.get('mastery',0)/100
        target=c.get('targetLevel',85)/100
        difficulty={'Beginner':.2,'Intermediate':.5,'Advanced':.8}.get(r.get('difficulty'),.5)
        duration = r.get('duration', '').lower()
        numeric = re.findall(r'[0-9.]+',duration)
        duration_hours = float(numeric[0]) if numeric else 1
        if 'min' in duration and 'hour' not in duration: duration_hours /= 60
        elif 'week' in duration: duration_hours *= 5
        prereq_fit = .25 if c.get('unmetPrerequisites') else 1
        features=[max(0,target-mastery), 1 if c.get('careerRequired') else .25, (1-abs(difficulty-mastery))*prereq_fit, min(1,r.get('qualityRating',4)/5),min(1,hours/max(.1,duration_hours))]
        ranked.append({**r,'rankingScore':round(predict(features),4),'rankingModel':'demo-ranker-1 (synthetic training data)','reasonRecommended':f"Recommended for {r.get('skillName', 'this skill')}: mastery {int(mastery*100)}%, target {int(target*100)}%; difficulty and available time included. " + ('Close prerequisites first.' if c.get('unmetPrerequisites') else 'Prerequisites fit current state.')})
    return sorted(ranked,key=lambda r:-r['rankingScore'])

def rank_projects(projects, competencies, hours=10):
    """Apply the same demo utility ranker to aggregate project skill requirements."""
    by_id={c['id']:c for c in competencies}
    output=[]
    for project in projects:
        relevant=[by_id[s] for s in project.get('skillsValidated',[]) if s in by_id]
        mastery=sum(c.get('mastery',0)/100 for c in relevant)/max(1,len(relevant))
        gap=sum(max(0,c.get('targetLevel',85)-c.get('mastery',0))/100 for c in relevant)/max(1,len(relevant))
        importance=sum(bool(c.get('careerRequired')) for c in relevant)/max(1,len(relevant))
        difficulty={'Beginner':.2,'Intermediate':.5,'Advanced':.8}.get(project.get('difficulty'),.5)
        prerequisite_fit=.25 if any(c.get('unmetPrerequisites') for c in relevant) else 1
        # Rubric coverage measures documented criteria, not project implementation quality.
        quality=min(1,len(project.get('rubric',[]))/5)
        effort=re.findall(r'[0-9.]+',project.get('estimatedEffort',''))
        effort_hours=float(effort[0]) if effort else 10
        if 'week' in project.get('estimatedEffort','').lower(): effort_hours*=5
        features=[gap,importance,(1-abs(difficulty-mastery))*prerequisite_fit,quality,min(1,hours/max(.1,effort_hours))]
        output.append({**project,'rankingScore':round(predict(features),4),'rankingModel':'demo-ranker-1 (synthetic training data)','rankingReason':'Ranks evidenced skill gaps, career overlap, prerequisite fit, rubric coverage and estimated effort; not an artifact quality judgment.'})
    return sorted(output,key=lambda p:-p['rankingScore'])
