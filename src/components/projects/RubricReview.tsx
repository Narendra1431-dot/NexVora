import {useEffect,useState} from 'react';
import {useAppState} from '../../lib/state/app-state';
export function RubricReview() {
  const {loadPendingReviews,submitReview,showToast}=useAppState();
  const [pending,setPending]=useState<any[]>([]);
  const [selected,setSelected]=useState('');
  const [criteria,setCriteria]=useState<Record<string,{score:number;evidence:string}>>({});
  const [feedback,setFeedback]=useState('');
  const [busy,setBusy]=useState(false);
  const refresh=()=>loadPendingReviews().then(setPending).catch(e=>showToast('Review unavailable',e.message,'warning'));
  useEffect(()=>{refresh();},[]);
  const submission=pending.find(p=>p.id===selected);
  return <section className="bg-white border rounded-xl p-5 space-y-3"><h3 className="font-bold">Authorized rubric review</h3><p className="text-sm">Inspect the student's artifact independently. Record concrete evidence for every criterion. The platform does not execute submitted code.</p><select aria-label="Pending submission" className="border p-2 w-full" value={selected} onChange={e=>{setSelected(e.target.value);setCriteria({});setFeedback('');}}><option value="">Select a pending submission ({pending.length})</option>{pending.map(p=><option key={p.id} value={p.id}>{p.projectTitle} — {p.id}</option>)}</select>{submission && <form onSubmit={async e=>{e.preventDefault();setBusy(true);try{const r=await submitReview(selected,{criteria:submission.rubric.map((r:any)=>({criterion:r.criterion,...criteria[r.criterion]})),feedback});if(r){setSelected('');refresh();}}finally{setBusy(false);}}} className="space-y-3"><a href={submission.githubUrl} target="_blank" rel="noreferrer" className="underline">Inspect submitted artifact</a><p>{submission.description}</p>{submission.rubric.map((r:any)=><fieldset className="border p-3 space-y-2" key={r.criterion}><legend>{r.criterion} ({r.weight} weight)</legend><label>Score (0–100)<input aria-label={`${r.criterion} score`} required type="number" min="0" max="100" value={criteria[r.criterion]?.score ?? ''} onChange={e=>setCriteria(p=>({...p,[r.criterion]:{...p[r.criterion],score:Number(e.target.value)}}))} className="border block p-2"/></label><label>Observed evidence<textarea aria-label={`${r.criterion} evidence`} required minLength={10} value={criteria[r.criterion]?.evidence || ''} onChange={e=>setCriteria(p=>({...p,[r.criterion]:{...p[r.criterion],evidence:e.target.value}}))} className="border block p-2 w-full"/></label></fieldset>)}<label>Feedback<textarea required minLength={10} value={feedback} onChange={e=>setFeedback(e.target.value)} className="border block w-full p-2"/></label><button disabled={busy} className="bg-teal-700 text-white p-2 rounded">Record rubric review</button></form>}</section>;
}

