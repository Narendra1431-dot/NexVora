import httpx,json,uuid
from pathlib import Path
with httpx.Client(base_url='http://127.0.0.1:8000',timeout=120) as c:
 h=c.get('/health/agents')
 r=c.post('/api/v1/auth/register',json={'name':'Live Copilot QA','email':f'copilot-live-{uuid.uuid4().hex}@example.com','password':uuid.uuid4().hex});r.raise_for_status();headers={'Authorization':'Bearer '+r.json()['token']}
 results=[]
 for query in ['What should I learn next and why?', 'Why is Transformers blocked?', 'Create my learning plan for this week']:
  body={'message':query,'requestId':uuid.uuid4().hex};reply=c.post('/api/v1/agent/chat',headers=headers,json=body)
  data=reply.json();print(json.dumps({'query':query,'status':reply.status_code,'run':data.get('agentRun'),'answer':data.get('answer',data.get('detail',''))[:900]}),flush=True);results.append({'query':query,'status':reply.status_code,'result':data})
  if reply.is_success:
   replay=c.post('/api/v1/agent/chat',headers=headers,json=body);assert replay.json()==data
 history=c.get('/api/v1/agent/history',headers=headers).json();print('HISTORY',len(history),[m['role'] for m in history])
 Path('output/qa/copilot-live.json').write_text(json.dumps({'health':h.json(),'results':results,'historyCount':len(history)},indent=2),encoding='utf-8')
 assert all(r['status']==200 for r in results)
