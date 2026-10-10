"""Actual demo account, Redis worker, provider and Mongo execution. No doubles."""
import httpx,json,time
from uuid import uuid4
from pathlib import Path
with httpx.Client(base_url='http://127.0.0.1:8001/api/v1',timeout=90) as c:
    auth=c.post('/auth/demo',json={});auth.raise_for_status()
    h={'Authorization':'Bearer '+auth.json()['token']}
    run=c.post('/agent/runs',headers=h,json={'message':'Analyze my current profile and resume for my selected target career and create my next learning plan.','requestId':uuid4().hex})
    run.raise_for_status();id=run.json()['id'];print('Created '+id,flush=True)
    for _ in range(150):
        r=c.get('/agent/runs/'+id,headers=h);r.raise_for_status();data=r.json()
        if data['status'] in ('COMPLETED','FAILED','CANCELLED'):break
        time.sleep(1)
    proof={k:data.get(k) for k in ('id','status','proof','error','modelUsage','stateVersionBefore','stateVersionAfter')}
    proof['steps']=[{'agent':s['agentName'],'status':s['status'],'startedAt':s.get('startedAt'),'completedAt':s.get('completedAt')} for s in data.get('steps',[])]
    events=c.get('/agent/runs/'+id+'/events',headers=h)
    proof['sseVerified']='event: agent-event' in events.text
    Path('tmp/agent-graph-live-proof.json').write_text(json.dumps(proof,indent=2),encoding='utf-8')
    print(json.dumps(proof),flush=True)
