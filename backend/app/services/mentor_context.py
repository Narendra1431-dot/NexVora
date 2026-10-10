"""Bounded, read-only projection for provider context; canonical state is unchanged."""
import json

def bounded_context(context, passages, query):
    def rows(key, fields, limit):
        value=context.get(key,[])
        if not isinstance(value,list): return []
        ordered=sorted(value,key=lambda row: str(row.get('name',row.get('title',''))).lower() not in query.lower())
        return [{k:(v[:180] if isinstance(v,str) else v) for k in fields if isinstance((v:=row.get(k)),(str,int,float,bool))} for row in ordered[:limit]]
    projected={k:context.get(k) for k in ('targetCareer','readiness','stateVersion')}
    projected['skills']=rows('skills',('id','name','mastery','confidence','state'),34)
    projected['evidence']=rows('evidence',('title','skillName','status','type'),5)
    projected['roadmap']=rows('roadmap',('title','status'),3)
    projected['resources']=rows('resources',('title','url'),3)
    projected['nextAction']={k:str(context.get('nextAction',{}).get(k,''))[:200] for k in ('title','reason')}
    projected['scope']='Selected context only. Missing information is unknown; never infer missing evidence.'
    for key in ('assessment','project','resume'):
        if key in context:
            projected[key+'Excerpt']=json.dumps(context[key],ensure_ascii=False)[:700]
    # Hard text budget includes optional tool excerpts, while preserving valid JSON.
    while len(json.dumps(projected,ensure_ascii=False))>7000 and projected['skills']:
        projected['skills'].pop()
    return [projected]+[f"[{p['documentId']}] {p['text'][:800]}" for p in passages[:3]]

def bounded_history(history):
    output=[]; remaining=4000
    for entry in reversed(history):
        content=entry['content'][:min(1200,remaining)]
        if not content: break
        output.append({'role':entry['role'],'content':content}); remaining-=len(content)
    return list(reversed(output))
