import { UndoRedoControls } from '../layout/UndoRedoControls';
import { useUndoableState } from '../../lib/state/edit-history';
import { useState } from 'react';
import { useAppState } from '../../lib/state/app-state';
export function OnboardingWizard({open,onClose}:{open:boolean;onClose:()=>void}) {
  const {student,careers,saveProfile,setTargetCareer,setActiveTab}=useAppState();
  const [name,setName]=useUndoableState(student.name,'Profile name',open);
  const [headline,setHeadline]=useUndoableState(student.headline,'Profile headline',open);
  const [degree,setDegree]=useUndoableState(student.degree,'Degree',open);
  const [institution,setInstitution]=useUndoableState(student.institution,'Institution',open);
  const [hours,setHours]=useUndoableState(student.weeklyAvailabilityHours || 10,'Weekly study hours',open);
  const [career,setCareer]=useUndoableState(student.targetCareerId,'Target career selection',open);
  const [busy,setBusy]=useState(false);
  if(!open)return null;
  return <div className="fixed inset-0 z-50 bg-slate-900/50 flex items-center justify-center p-4"><form data-undo="true" role="dialog" aria-label="Set up your learning profile" className="bg-white p-6 rounded-2xl max-w-lg w-full space-y-4 max-h-[90dvh] overflow-y-auto" onSubmit={async e=>{e.preventDefault();setBusy(true);try{if(!await saveProfile({name,headline,degree,institution,weeklyAvailabilityHours:hours}))return;if(!await setTargetCareer(career))return;onClose();setActiveTab('resume');}finally{setBusy(false);}}}><div className="flex items-center gap-3"><h2 className="text-xl font-bold">Set up your learning profile</h2><UndoRedoControls/></div><p className="text-sm text-slate-600">Save your goals, then upload your resume and take a diagnostic. Claims remain unverified until supported by evidence.</p><ol aria-label="Your setup journey" className="grid grid-cols-3 sm:grid-cols-5 gap-2 border-y border-slate-100 py-3">{['Profile','Resume','Career','Assessment','Roadmap'].map((label,index)=><li key={label} className="flex flex-col items-center text-center gap-1 text-[10px] text-slate-600"><span>{index+1}. {label}</span></li>)}</ol>{[['Name',name,setName],['Headline',headline,setHeadline],['Degree',degree,setDegree],['Institution',institution,setInstitution]].map(([label,value,setter])=><label className="block text-sm" key={label as string}>{label as string}<input aria-label={label as string} value={value as string} onChange={e=>(setter as (v:string)=>void)(e.target.value)} className="block w-full border rounded p-2" /></label>)}<label className="block text-sm">Hours per week<input type="number" min="1" max="80" value={hours} onChange={e=>setHours(Number(e.target.value))} className="block w-full border rounded p-2" /></label><label className="block text-sm">Target career<select value={career} onChange={e=>setCareer(e.target.value)} className="block w-full border rounded p-2">{careers.map(c=><option key={c.id} value={c.id}>{c.title}</option>)}</select></label><div className="flex gap-3"><button disabled={busy} className="bg-teal-700 text-white p-2 rounded">Save and upload resume</button><button type="button" onClick={onClose}>Close</button></div></form></div>;
}
