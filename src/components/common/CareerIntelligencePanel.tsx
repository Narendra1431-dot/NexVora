import {useEffect,useState} from 'react';
import {useAppState} from '../../lib/state/app-state';

type Action={label:string;tab:string;id?:string;skillId?:string};
type Recommendation={title:string;reason:string;stateVersion:number;currentReadiness:number;currentMastery:number|null;targetMastery:number|null;readinessImpact:string;blocks:string[];evidenceUsed:{id:string;title:string;verificationState:string}[];missingEvidence:boolean;actions:Action[];certifications?:{courses:{courseId:string;courseName:string;eligible:boolean;reasons:string[]}[]}};
type Activity={id:string;intent:string;status:string;stateVersion:number;createdAt:string;actions?:{label:string;status:string}[]};

export function CareerIntelligencePanel({activityOnly=false}:{activityOnly?:boolean}){
 const {targetCareer,competencyNodes,evidenceItems,activities,mentorMessages,setActiveTab,setSelectedSkillId,setCatalogSelection}=useAppState();
 const [recommendation,setRecommendation]=useState<Recommendation|null>(null),[activity,setActivity]=useState<Activity[]>([]),[error,setError]=useState(''),[retry,setRetry]=useState(0);
 const key=JSON.stringify([targetCareer?.id,competencyNodes?.map(c=>[c.id,c.mastery,c.state]),evidenceItems?.map(e=>e.id),activities?.map(a=>a.id),activityOnly?mentorMessages?.length:0]);
 useEffect(()=>{const controller=new AbortController();let live=true;setError('');setRecommendation(null);setActivity([]);
  async function get(path:string){const r=await fetch('/api/v1/agent/'+path,{headers:{Authorization:'Bearer '+(sessionStorage.getItem('plcip_token')||'')},signal:controller.signal});if(!r.ok)throw new Error('Career intelligence is temporarily unavailable. Your existing learning pages are still available.');return r.json();}
  Promise.all([activityOnly?Promise.resolve(null):get('recommendations'),get('activity')]).then(([r,a])=>{if(live){setRecommendation(r?.recommendation||null);setActivity(Array.isArray(a)?a:[]);}}).catch(e=>{if(live&&!controller.signal.aborted)setError(e.message);});
  return()=>{live=false;controller.abort();};
 },[key,retry,activityOnly]);
 const open=(a:Action)=>{if(a.skillId)setSelectedSkillId(a.skillId);if(a.id&&['resources','assessments','projects'].includes(a.tab))setCatalogSelection({tab:a.tab as 'resources'|'assessments'|'projects',id:a.id});setActiveTab(a.tab);};
 const button='rounded-lg border border-teal-200 bg-white px-3 py-2 text-xs font-semibold text-teal-900 hover:bg-teal-50';
 return <section aria-label={activityOnly?'Career activity':'NexVora Intelligence'} className="rounded-2xl border border-teal-200 bg-teal-50/40 p-5 space-y-3">
  <h3 className="font-bold text-slate-900">{activityOnly?'Career activity':'NexVora Intelligence'}</h3>
  {error?<p className="text-xs text-amber-800">{error} <button className={button} onClick={()=>setRetry(n=>n+1)}>Retry</button></p>:!activityOnly&&!recommendation?<p className="text-sm text-slate-600">Reviewing your current evidence and learning priorities...</p>:null}
  {!activityOnly&&recommendation&&<><div className="flex items-start gap-3"><div><p className="text-xs font-semibold text-teal-700">Next Best Action</p><h4 className="mt-1 font-bold">{recommendation.title}</h4><p className="mt-1 text-sm text-slate-600">{recommendation.reason}</p></div></div>
   {recommendation.currentMastery!==null&&<p className="text-xs text-slate-600">Mastery {recommendation.currentMastery}% / required {recommendation.targetMastery}% · Career readiness {recommendation.currentReadiness}%</p>}
   {recommendation.blocks.length>0&&<p className="text-xs text-slate-600">Helps unblock: {recommendation.blocks.join(', ')}</p>}
   <div className="flex flex-wrap gap-2">{recommendation.actions.map(a=><button key={a.label} className={button} onClick={()=>open(a)}>{a.label}</button>)}</div>
   <details className="text-xs text-slate-600"><summary className="cursor-pointer font-semibold">Evidence and readiness impact</summary><p className="mt-2">{recommendation.readinessImpact}</p>{recommendation.evidenceUsed.length?<ul className="mt-2 space-y-1">{recommendation.evidenceUsed.map(e=><li key={e.id}>{e.title} — {e.verificationState}</li>)}</ul>:<p className="mt-2">No recorded evidence for this skill yet.</p>}{recommendation.missingEvidence&&<p className="mt-2">A scored assessment or reviewed project is needed to establish verified proof.</p>}</details>
   {recommendation.certifications?.courses.some(c=>c.eligible)&&<button className={button} onClick={()=>setActiveTab('certificates')}>View eligible certificate options</button>}
  </>}
  <details className="text-xs text-slate-600" open={activityOnly||undefined}><summary className="cursor-pointer font-semibold">Recent career activity</summary><ol className="mt-3 space-y-3">{activity.slice(0,5).map(a=><li key={a.id} className="border-l-2 border-teal-200 pl-3"><p className="font-semibold">{a.intent} · {a.status}</p><p className="text-[11px] text-slate-500">{new Date(a.createdAt).toLocaleString()} · state {a.stateVersion ?? 'unavailable'}</p>{a.actions?.map((step,i)=><p key={i} className="mt-1">{step.label} — {step.status}</p>)}</li>)}</ol>{!activity.length&&!error&&<p className="mt-2">Activity appears after a learning update or copilot request.</p>}</details>
 </section>;
}
