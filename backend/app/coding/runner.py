"""Judge0 adapter. Never executes general user code in the NexVora process."""
import asyncio
import base64
import os
import httpx
from fastapi import HTTPException
from .catalog import LANGUAGES

def configured():return bool(os.getenv('JUDGE0_URL','').strip())
def b64(s):return base64.b64encode(s.encode()).decode()
def decode(s):
 try:return base64.b64decode(s or '').decode('utf-8',errors='replace')[:12000]
 except Exception:return 'Invalid runner output'
async def execute(code,language,tests):
 url=os.getenv('JUDGE0_URL','').rstrip('/')
 if not url:raise HTTPException(503,'Isolated runner unavailable. Configure JUDGE0_URL and JUDGE0_AUTH_TOKEN in backend/.env. No code was executed.')
 headers={}
 if os.getenv('JUDGE0_AUTH_TOKEN'):headers['X-Auth-Token']=os.environ['JUDGE0_AUTH_TOKEN']
 if os.getenv('JUDGE0_RAPIDAPI_KEY'):
  headers['X-RapidAPI-Key']=os.environ['JUDGE0_RAPIDAPI_KEY'];headers['X-RapidAPI-Host']=os.getenv('JUDGE0_RAPIDAPI_HOST','judge0-ce.p.rapidapi.com')
 results=[]
 try:
  async with httpx.AsyncClient(timeout=15,follow_redirects=False) as client:
   for case in tests:
    body=dict(source_code=b64(code),language_id=LANGUAGES[language],stdin=b64(case['input']),cpu_time_limit=2,wall_time_limit=5,memory_limit=128000,stack_limit=64000,max_file_size=64,enable_network=False,number_of_runs=1)
    r=await client.post(url+'/submissions?base64_encoded=true&wait=false',json=body,headers=headers);r.raise_for_status();token=r.json()['token']
    result={}
    for _ in range(30):
     await asyncio.sleep(.25)
     r=await client.get(url+'/submissions/'+token+'?base64_encoded=true',headers=headers);r.raise_for_status();result=r.json()
     if result.get('status',{}).get('id',0)>2:break
    status_id=result.get('status',{}).get('id',0)
    output=decode(result.get('stdout'));expected=case.get('output')
    status={3:'Accepted',4:'Wrong Answer',5:'Time Limit Exceeded',6:'Compilation Error'}.get(status_id,'Runtime Error' if status_id>6 else 'Time Limit Exceeded')
    if status_id==3 and expected is not None and output.split()!=expected.split():status='Wrong Answer'
    results.append(dict(status=status,input=case['input'],output=output,expected=expected,executionTime=float(result.get('time') or 0)*1000,memory=result.get('memory'),error=decode(result.get('compile_output') or result.get('stderr'))))
 except (httpx.HTTPError,KeyError,ValueError):raise HTTPException(503,'The isolated runner could not complete this request. Check runner configuration and availability; no XP was awarded.')
 return results
