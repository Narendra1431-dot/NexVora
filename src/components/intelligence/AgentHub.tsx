import {useCallback,useEffect,useState} from 'react';
import {Activity,ArrowRight,CheckCircle2,Clock,GitBranch,Loader2,ShieldCheck} from 'lucide-react';
import {intelligenceApi} from './api';
import {AgentGovernance} from './AgentGovernance';

type Step={stepId:string;id:string;agentName:string;task:string;status:string;dependencyIds:string[];durationMs?:number;retryCount:number;toolsUsed?:string[];inputSummary?:unknown;outputSummary?:unknown;errorSummary?:string};
type Run={id:string;userRequest:string;status:string;createdAt:string;durationMs?:number;stateVersionBefore:number;stateVersionAfter:number;finalResultSummary?:string;error?:{code:string;message:string};steps?:Step[];toolCalls?:{toolCallId:string;toolName:string;status:string;sourceRefs:string[]}[];proof?:{agentsExecuted:number;toolCalls:number;sourcesRetrieved:number;approvals:number};sources?:unknown[];artifacts?:{artifactId:string;name:string}[];result?:{recommendations:string[]};changes?:string[]};
type Event={eventId:string;eventType:string;safeMessage:string;timestamp:string};
const terminal=(status:string)=>['COMPLETED','FAILED','CANCELLED'].includes(status);
const panel='rounded-xl border border-slate-200 bg-white p-5';
const button='max-w-full break-words rounded-lg border border-slate-300 px-3 py-2 text-sm font-semibold disabled:opacity-50';
const seconds=(ms?:number)=>ms===undefined?'\u2014':(ms/1000).toFixed(2)+'s';

export function AgentHub(){
 const initial=window.location.pathname.endsWith('/approvals')?'Approvals':window.location.pathname.endsWith('/activity')?'Audit History':'Overview';
 const [view,setView]=useState(initial),[runs,setRuns]=useState<Run[]>([]),[selected,setSelected]=useState(()=>new URLSearchParams(window.location.search).get('run')||''),[detail,setDetail]=useState<Run|null>(null);
 const [message,setMessage]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState(''),[stream,setStream]=useState(''),[events,setEvents]=useState<Event[]>([]),[step,setStep]=useState<Step|null>(null);
 const refresh=useCallback(async()=>{setRuns(await intelligenceApi('/agent/runs/run'));},[]);
 useEffect(()=>{void refresh().catch(()=>setError('Run history could not be loaded.'));const timer=setInterval(()=>void refresh().catch(()=>{}),5000);return()=>clearInterval(timer);},[refresh]);
 useEffect(()=>{
  if(!selected)return;
  const controller=new AbortController();let cursor='',active=true,lastLoaded=0;
  setEvents([]);setDetail(null);setStep(null);
  const load=async()=>{const value=await intelligenceApi('/agent/runs/run/'+selected);if(active){setDetail(value);lastLoaded=Date.now();}};
  const listen=async()=>{
   while(active){
    try{
     await load();
     const response=await fetch('/api/v1/agent/runs/run/'+selected+'/events'+(cursor?'?after='+cursor:''),{headers:{Authorization:'Bearer '+sessionStorage.getItem('plcip_token')},signal:controller.signal});
     if(!response.ok||!response.body)throw new Error('Stream unavailable');
     setStream('Connected to backend events');const reader=response.body.getReader(),decoder=new TextDecoder();let buffer='',ended=false;
     while(active){const chunk=await reader.read();if(chunk.done)break;buffer+=decoder.decode(chunk.value,{stream:true});let end;
      while((end=buffer.indexOf('\n\n'))>=0){const frame=buffer.slice(0,end);buffer=buffer.slice(end+2);const lines=frame.split('\n');const id=lines.find(l=>l.startsWith('id: '));if(id)cursor=id.slice(4);
       if(frame.includes('event: stream-end'))ended=true;
       const data=lines.find(l=>l.startsWith('data: '));if(data&&!ended){const record=JSON.parse(data.slice(6)) as Event;setEvents(rows=>rows.some(r=>r.eventId===record.eventId)?rows:[...rows,record].slice(-100));}
      }
      if(!ended&&Date.now()-lastLoaded>1500)await load();
     }
     if(ended){await load();setStream('Execution history synchronized');return;}
    }catch{if(!active)return;setStream('Event stream interrupted; reconnecting…');}
     await new Promise(resolve=>setTimeout(resolve,2000));
    }
   };
   void listen();return()=>{active=false;controller.abort();};
  },[selected]);
  useEffect(()=>{
   if(!selected||['Approvals','Audit History'].includes(view))return;
   let active=true;
   void intelligenceApi('/agent/runs/run/'+selected).then(value=>{if(active)setDetail(value);}).catch(()=>{if(active)setError('Workflow details could not be refreshed.');});
   return()=>{active=false;};
  },[view,selected]);
  useEffect(()=>{
   if(!step)return;
   const close=(event:KeyboardEvent)=>{if(event.key==='Escape')setStep(null);};
   window.addEventListener('keydown',close);
   return()=>window.removeEventListener('keydown',close);
  },[step]);
  const start=async()=>{if(!message.trim()||busy)return;setBusy(true);setError('');try{const run=await intelligenceApi('/agent/runs/run',{message,requestId:crypto.randomUUID()});setSelected(run.id);setView('Active Runs');await refresh();}catch(e){setError(e instanceof Error?e.message:'Could not start workflow.');}finally{setBusy(false);}};
  const download=async(id:string,name:string)=>{if(!detail)return;try{const response=await fetch('/api/v1/agent/runs/'+detail.id+'/artifacts/'+id+'/download',{headers:{Authorization:'Bearer '+sessionStorage.getItem('plcip_token')}});if(!response.ok)throw new Error('Artifact download failed.');const url=URL.createObjectURL(await response.blob());const link=document.createElement('a');link.href=url;link.download=name;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}catch(e){setError(String(e));}};
  const retry=async()=>{if(!detail)return;try{const value=await intelligenceApi('/agent/runs/run/'+detail.id+'/retry',{message:detail.userRequest,requestId:crypto.randomUUID()});setSelected(value.id);await refresh();}catch(e){setError(String(e));}};
  const cancel=async()=>{if(!detail)return;try{setDetail(await intelligenceApi('/agent/runs/run/'+detail.id+'/cancel',{}));}catch(e){setError(String(e));}};
  const changeView=(name:string)=>{setView(name);window.history.replaceState({},'',name==='Approvals'?'/agent-hub/approvals':name==='Audit History'?'/agent-hub/activity':name.includes('Runs')?'/agent-hub/runs':'/agent-hub');};
  useEffect(()=>{
   if(!selected)return;
   const url=new URL(window.location.href);url.searchParams.set('run',selected);window.history.replaceState({},'',url.pathname+url.search);
  },[selected,view]);
  const filtered=runs.filter(r=>view==='Active Runs'?!terminal(r.status):view==='Completed Runs'?r.status==='COMPLETED':view==='Failed Runs'?['FAILED','CANCELLED'].includes(r.status):true);
  const completed=runs.filter(r=>r.status==='COMPLETED');
  return <div className="space-y-5">
   <header><p className="text-xs font-semibold uppercase tracking-widest text-teal-700">Agent Hub</p><h1 className="text-2xl font-bold text-slate-900 mt-1">NexVora Agentic Intelligence</h1><p className="text-sm text-slate-500 mt-2">Real specialist actions, recorded tools and source references. Student scores remain governed by deterministic services.</p></header>
   <nav aria-label="Agent Hub views" className="flex flex-wrap gap-2">{['Overview','Active Runs','Completed Runs','Failed Runs','Approvals','Audit History'].map(name=><button key={name} onClick={()=>changeView(name)} aria-pressed={view===name} className={button+(view===name?' bg-teal-50 border-teal-300 text-teal-900':' bg-white')}>{name}</button>)}</nav>
   {error&&<p role="alert" className="text-sm text-red-700">{error}</p>}
   {['Approvals','Audit History'].includes(view)?<AgentGovernance/>:<>
   <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
    {[['Active workflows',runs.filter(r=>!terminal(r.status)).length],['Completed today',completed.filter(r=>r.createdAt.slice(0,10)===new Date().toISOString().slice(0,10)).length],['Average completed time',completed.length?seconds(completed.reduce((n,r)=>n+(r.durationMs||0),0)/completed.length):'—']].map(([label,value])=><div key={label} className={panel}><p className="text-xs text-slate-500">{label}</p><p className="text-2xl font-bold mt-1">{value}</p></div>)}
   </div><p className="text-xs text-slate-500">Summary covers your latest 50 recorded workflows. Times use backend measurements.</p>
   <section className={panel}><h2 className="font-semibold flex gap-2 items-center"><GitBranch size={18}/> Start a governed workflow</h2><textarea aria-label="Agent workflow request" maxLength={3000} value={message} onChange={e=>setMessage(e.target.value)} placeholder="Analyze my current profile and resume for my selected career and create my next learning plan." className="mt-3 border rounded-lg p-3 w-full min-h-24 text-sm"/><div className="flex flex-wrap items-center gap-3 mt-2"><button disabled={busy||!message.trim()} onClick={()=>void start()} className={button+' bg-teal-700 text-white'}>{busy?'Submitting…':'Run specialists'}</button><button className="text-sm text-teal-700 underline" onClick={()=>setMessage('Analyze my current profile and resume for my selected target career and create my next learning plan.')}>Use career planning example</button></div><p className="text-xs text-slate-500 mt-3">Analysis produces recommendations. Applying a roadmap change requires a separate approval.</p></section>
   <div className="grid lg:grid-cols-[280px_1fr] gap-5">
    <section className={panel}><h2 className="font-semibold mb-3">Recorded workflows</h2>{!filtered.length&&<p className="text-sm text-slate-500">No workflows in this view.</p>}<ul className="space-y-2">{filtered.map(run=><li key={run.id}><button onClick={()=>setSelected(run.id)} className={'text-left w-full rounded-lg border p-3 text-sm '+(run.id===selected?'border-teal-400 bg-teal-50':'border-slate-200')}><span className="block font-medium line-clamp-2">{run.userRequest}</span><span className="block text-xs mt-2">{run.status} · {seconds(run.durationMs)}</span><time className="text-xs text-slate-500">{new Date(run.createdAt).toLocaleString()}</time></button></li>)}</ul></section>
    <div className="space-y-4 min-w-0">{detail?<>
     <section className={panel}><div className="flex flex-wrap justify-between gap-3"><h2 className="font-semibold">Execution graph</h2><span className="text-xs text-slate-500">{stream}</span></div><p className="text-xs break-all mt-2">{detail.id} · {detail.status}</p>{!terminal(detail.status)&&<button onClick={()=>void cancel()} className={button+' mt-3'}>Request cancellation</button>}
      {!detail.steps?.length&&<p className="mt-4 text-sm text-slate-500">Waiting for the worker and supervisor to confirm the execution graph.</p>}
      <ol className="mt-4 grid md:grid-cols-2 gap-3">{detail.steps?.map(s=><li key={s.stepId}><button onClick={()=>setStep(s)} className={'rounded-lg border p-3 text-left w-full h-full '+(s.status==='RUNNING'?'border-teal-400 bg-teal-50':'border-slate-200')}><span className="flex items-center gap-2 font-semibold capitalize text-sm">{s.status==='RUNNING'?<Loader2 size={16} className="animate-spin motion-reduce:animate-none"/>:s.status==='COMPLETED'?<CheckCircle2 size={16} className="text-teal-700"/>:<Clock size={16}/>} {s.agentName}</span><span className="block text-xs mt-2">{s.status} · {seconds(s.durationMs)}</span><span className="block text-xs text-slate-500 mt-1">{s.dependencyIds.length?'After '+s.dependencyIds.join(', '):'Starts independently'}</span></button></li>)}</ol>
     </section>
     {detail.proof&&<section className={panel}><h2 className="font-semibold flex items-center gap-2"><ShieldCheck size={18}/>Proof of Execution</h2><dl className="grid grid-cols-2 md:grid-cols-4 gap-3 mt-4 text-sm">{Object.entries(detail.proof).filter(([k])=>['agentsExecuted','toolCalls','sourcesRetrieved','approvals'].includes(k)).map(([k,v])=><div key={k}><dt className="text-xs text-slate-500">{k.replace(/([A-Z])/g,' $1')}</dt><dd className="font-bold text-xl">{String(v)}</dd></div>)}</dl><p className="text-xs mt-3">State version: {detail.stateVersionBefore} → {detail.stateVersionAfter}. {detail.changes?.length?detail.changes.join(', '):'No state changes recorded by this workflow.'}</p></section>}
     {['FAILED','CANCELLED'].includes(detail.status)&&<button onClick={()=>void retry()} className={button}>Retry analysis as a new run</button>}
     {detail.error&&<p role="alert" className={panel+' text-red-700 text-sm'}>{detail.error.code}: {detail.error.message}</p>}
     {detail.finalResultSummary&&<section className={panel}><h2 className="font-semibold">Result and next actions</h2><button className={button+' mt-3'} onClick={async()=>{try{await intelligenceApi('/agent/runs/run/'+detail.id+'/roadmap-proposal',{});changeView('Approvals');}catch(e){setError(String(e));}}}>Review weekly-plan approval</button><button className={button+' mt-3 ml-2'} onClick={async()=>{try{await intelligenceApi('/agent/runs/run/'+detail.id+'/report-proposal',{});changeView('Approvals');}catch(e){setError(String(e));}}}>Review report export</button>{detail.artifacts?.map(a=><button key={a.artifactId} onClick={()=>void download(a.artifactId,a.name)} className={button+' mt-3 ml-2'}>Download {a.name}</button>)}<p className="text-sm whitespace-pre-wrap mt-3">{detail.finalResultSummary}</p><ul className="mt-3 space-y-2">{detail.result?.recommendations.map((r,i)=><li key={i} className="flex gap-2 text-sm"><ArrowRight className="shrink-0 text-teal-700" size={16}/>{r}</li>)}</ul><details className="mt-4"><summary className="text-sm cursor-pointer">Retrieved sources</summary><pre className="text-xs whitespace-pre-wrap break-words mt-2 max-h-64 overflow-auto">{JSON.stringify(detail.sources||[],null,2)}</pre></details></section>}
     <details className={panel}><summary className="font-semibold cursor-pointer">Backend event history</summary><ul className="mt-3 space-y-2 text-xs">{events.map(e=><li key={e.eventId}><time className="text-slate-500">{new Date(e.timestamp).toLocaleTimeString()}</time> · {e.eventType}<p>{e.safeMessage}</p></li>)}</ul></details>
    </>:<section className={panel+' text-sm text-slate-500'}><Activity size={20} className="mb-3"/>Select a workflow to inspect its recorded execution.</section>}</div>
   </div></>}
   {step&&<div className="fixed inset-0 z-50 bg-slate-900/30 flex justify-end" onClick={()=>setStep(null)}><section role="dialog" aria-modal="true" aria-label="Agent step details" className="w-full max-w-lg bg-white p-6 overflow-auto" onClick={e=>e.stopPropagation()}><button onClick={()=>setStep(null)} className={button}>Close details</button><h2 className="text-xl font-bold capitalize mt-4">{step.agentName}</h2><p className="mt-2 text-sm">{step.task}</p><p className="text-xs mt-2">{step.status} · {seconds(step.durationMs)} · Retries: {step.retryCount}</p><h3 className="font-semibold mt-5">Tools used</h3><p className="text-sm">{step.toolsUsed?.join(', ')||'No completed tools'}</p><h3 className="font-semibold mt-5">Input summary</h3><pre className="text-xs whitespace-pre-wrap break-words mt-2">{JSON.stringify(step.inputSummary,null,2)}</pre><h3 className="font-semibold mt-5">Recorded result</h3><pre className="text-xs whitespace-pre-wrap break-words mt-2">{JSON.stringify(step.outputSummary||step.errorSummary,null,2)}</pre></section></div>}
  </div>;
}
