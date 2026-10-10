import {useEffect,useRef,useState} from 'react';
import {useAppState} from '../../lib/state/app-state';
import {intelligenceApi} from './api';

const labels:Record<string,string>={resume_analysis:'Resume analysis',document_ingestion:'Learning material',embedding_generation:'Learning material',rag_index_update:'Learning material',career_gap_explanation:'Career guidance',roadmap_generation:'Learning strategy',resource_enrichment:'Resource guidance',assessment_generation:'Practice preparation',project_recommendation:'Project guidance',resume_generation:'Resume guidance',certificate_description:'Achievement description',student_intelligence_refresh:'Career intelligence'};
export function BackgroundActivity(){
 const {refreshWorkspace,showToast}=useAppState();
 const [jobs,setJobs]=useState<any[]>([]),[open,setOpen]=useState(false),[error,setError]=useState(''),[result,setResult]=useState<any>(null);
 const seen=useRef(new Map<string,string>()),refresh=useRef(refreshWorkspace),toast=useRef(showToast);refresh.current=refreshWorkspace;toast.current=showToast;
 useEffect(()=>{let active=true,running=false;
  async function poll(){if(running)return;running=true;try{const rows=await intelligenceApi('/jobs');if(!active)return;
   for(const job of rows){const prior=seen.current.get(job.jobId);if(prior&&prior!==job.status&&job.status==='Completed'){await refresh.current();toast.current('Analysis ready','Your background results are ready.','success');}seen.current.set(job.jobId,job.status);}
   setJobs(rows);
  }catch{/* Existing pages remain usable if the additive service is unavailable. */}finally{running=false;}}
  void poll();const timer=setInterval(()=>void poll(),4000);window.addEventListener('intelligence-job',poll);
  return()=>{active=false;clearInterval(timer);window.removeEventListener('intelligence-job',poll);};
 },[]);
 async function action(id:string,name:string){setError('');try{const value=await intelligenceApi('/jobs/'+id+'/'+name,name==='result'?undefined:{});if(name==='result')setResult(value.data);else setJobs(rows=>rows.map(j=>j.jobId===id?value:j));}catch(e){setError((e as Error).message);}}
 if(!jobs.length)return null;
 const pending=jobs.filter(j=>['Queued','Processing'].includes(j.status));
 return <section aria-label="Background activity" className="mx-4 mt-3 rounded-xl border border-slate-200 bg-white px-4 py-3 text-sm md:mx-6">
  <button className="font-semibold text-teal-800" aria-expanded={open} onClick={()=>setOpen(!open)}>Background activity{pending.length?' · '+pending.length+' pending':''}</button>
  {pending[0]&&<span className="ml-3 text-slate-600">{pending[0].stage}</span>}
  {open&&<div className="mt-3 space-y-3">{jobs.slice(0,10).map(j=><article key={j.jobId} className="rounded-lg border border-slate-100 p-3"><div className="flex flex-wrap justify-between gap-2"><strong>{labels[j.type]||'Analysis'}</strong><span>{j.status} · {j.progress}%</span></div><progress className="mt-2 h-1 w-full accent-teal-600" value={j.progress} max={100}/><p className="mt-1 text-slate-600">{j.stage}</p>{j.error&&<p role="alert">Analysis failed ({j.error}). Your verified scores were not changed by AI.</p>}<div className="mt-2 flex gap-4 text-teal-800">{j.status==='Completed'&&<button onClick={()=>void action(j.jobId,'result')}>View result</button>}{j.status==='Queued'&&<button onClick={()=>void action(j.jobId,'cancel')}>Cancel</button>}{j.status==='Failed'&&j.retryCount<3&&<button onClick={()=>void action(j.jobId,'retry')}>Retry</button>}</div></article>)}
   {error&&<p role="alert" className="text-red-700">{error}</p>}
   {result&&<article className="rounded-lg bg-slate-50 p-4"><button className="float-right text-teal-800" onClick={()=>setResult(null)}>Close result</button><h3 className="font-semibold">Analysis result</h3><p className="mt-2 whitespace-pre-wrap">{result.answer?.summary||result.summary||'Learning material indexed and ready for grounded questions.'}</p>{result.answer?.recommendations?.map((r:string,i:number)=><p className="mt-2" key={i}>{r}</p>)}{result.claims?.map((c:any,i:number)=><p className="mt-2" key={i}>{c.text} — {c.classification}</p>)}<p className="mt-3 text-xs text-slate-500">AI explanations are advisory. Scores and verification come from backend evidence rules.</p></article>}
  </div>}
 </section>;
}
