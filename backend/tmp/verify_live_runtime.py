import httpx,time,json
from uuid import uuid4
from pathlib import Path
base='http://127.0.0.1:8001/api/v1'
with httpx.Client(timeout=100) as c:
 r=c.post(base+'/auth/register',json={'name':'Governed Runtime QA','email':'runtime-qa-'+uuid4().hex+'@example.com','password':uuid4().hex});r.raise_for_status()
 h={'Authorization':'Bearer '+r.json()['token']}
 text=b'Transformers use self-attention to relate tokens. Attention computes a weighted sum of value vectors. Softmax normalizes attention weights. Positional encodings represent token order. Scaled dot-product attention divides the dot product by the square root of the key dimension before applying softmax.'
 r=c.post(base+'/documents/upload',headers=h,data={'documentType':'textbook'},files={'file':('Original-attention-QA.txt',text,'text/plain')});r.raise_for_status();job=r.json()
 for _ in range(90):
  status=c.get(base+'/jobs/'+job['jobId'],headers=h).json()
  if status['status'] in ('Completed','Failed','Cancelled'):break
  time.sleep(1)
 summary={'jobId':job['jobId'],'status':status['status'],'progress':status['progress'],'error':status.get('error')}
 print(json.dumps(summary),flush=True)
 if status['status']!='Completed':raise RuntimeError('Actual worker did not complete ingestion')
 state=c.get(base+'/state',headers=h).json()
 retrieved=c.post(base+'/agent/execute',headers=h,json={'toolName':'query_rag','requestId':uuid4().hex,'expectedStateVersion':state['stateVersion'],'arguments':{'query':'How does attention combine value vectors?'}})
 retrieved.raise_for_status()
 assert retrieved.json()['data'] and retrieved.json()['data'][0]['documentId']==job['inputRefs'][0]
 summary['crossProcessRetrieval']=True
 r=c.post(base+'/rag/query',headers=h,json={'question':'How does attention combine value vectors? Quote the uploaded material.','documentIds':job['inputRefs']})
 summary['answerHttpStatus']=r.status_code
 if r.status_code==200:
  answer=r.json()
  assert answer['answer']['citations'] and answer['sources'] and not answer['abstained']
  summary.update(provider=answer.get('provider'),model=answer.get('model'),citations=len(answer['answer']['citations']),sourceMatched=answer['sources'][0]['documentId']==job['inputRefs'][0])
 else:summary['answerError']=r.json().get('detail')
 summary['health']=c.get(base+'/health/agentic').json()
 Path('tmp/agentic-live-verification.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
 print(json.dumps(summary),flush=True)
