import {useState} from 'react';
import {useAppState} from '../../lib/state/app-state';
import {useUndoableState} from '../../lib/state/edit-history';
import {useModalDialog} from '../../lib/hooks/use-modal-dialog';
import {UndoRedoControls} from '../layout/UndoRedoControls';
const field='mt-1 block w-full rounded-lg border border-slate-300 bg-white p-2.5 text-sm font-normal';
export function ProfileEditor({onClose}:{onClose:()=>void}){
 const {student,careers,saveProfile}=useAppState();
 const [form,setForm]=useUndoableState({name:student.name||'',headline:student.headline||'',degree:student.degree||'',institution:student.institution||'',gpa:student.gpa||'',gradYear:student.gradYear||'',weeklyAvailabilityHours:student.weeklyAvailabilityHours??0,bio:student.bio||'',priorExperience:student.priorExperience||'',academicDetails:student.academicDetails||'',learningPreferences:(student.learningPreferences||[]).join(', '),readinessDisplayCareerId:student.readinessDisplayCareerId||''},'Profile draft');
 const [busy,setBusy]=useState(false),[error,setError]=useState('');
 const close=()=>{if(!busy)onClose();};const dialog=useModalDialog(true,close);
 const update=(key:keyof typeof form,value:string|number)=>setForm(p=>({...p,[key]:value}));
 return <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-3 sm:p-6"><div ref={dialog} role="dialog" aria-modal="true" aria-label="Edit Profile" tabIndex={-1} className="max-h-[90dvh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-5 sm:p-6">
 <form data-undo="true" className="space-y-5" onSubmit={async e=>{e.preventDefault();setBusy(true);setError('');try{const saved=await saveProfile({...form,name:form.name.trim(),learningPreferences:form.learningPreferences.split(',').map(v=>v.trim()).filter(Boolean)});if(saved)onClose();else setError('Profile was not saved. Check the fields and try again.');}catch(e){setError((e as Error).message);}finally{setBusy(false);}}}>
 <div className="flex flex-wrap items-center justify-between gap-3"><h2>Edit Profile</h2><UndoRedoControls/></div><p className="text-sm text-slate-500">Education and experience are self-reported. Readiness is calculated from verified competency evidence.</p>
 <fieldset disabled={busy} className="grid grid-cols-1 gap-4 sm:grid-cols-2">
 {([['name','Name',120],['headline','Headline / Role',200],['degree','Degree',120],['institution','College',160],['gpa','GPA',8],['gradYear','Graduation year',10]] as const).map(([key,label,max])=><label key={key} className="text-sm font-medium">{label}<input className={field} required={key==='name'} value={form[key]} maxLength={max} onChange={e=>update(key,e.target.value)}/></label>)}
 <label className="text-sm font-medium">Weekly learning hours<input className={field} required type="number" min="0" max="80" step="1" value={form.weeklyAvailabilityHours} onChange={e=>update('weeklyAvailabilityHours',Number(e.target.value))}/></label>
 <label className="text-sm font-medium">Target readiness display source<select className={field} value={form.readinessDisplayCareerId} onChange={e=>update('readinessDisplayCareerId',e.target.value)}><option value="">Follow selected target career</option>{careers.map(c=><option key={c.id} value={c.id}>{c.title}</option>)}</select></label>
 {([['bio','Profile summary',2000],['priorExperience','Prior experience',3000],['academicDetails','Academic details',3000]] as const).map(([key,label,max])=><label key={key} className="text-sm font-medium sm:col-span-2">{label}<textarea className={field} rows={3} maxLength={max} value={form[key]} onChange={e=>update(key,e.target.value)}/></label>)}
 <label className="text-sm font-medium sm:col-span-2">Learning preferences<input className={field} maxLength={960} value={form.learningPreferences} aria-label="Learning preferences" onChange={e=>update('learningPreferences',e.target.value)} aria-describedby="preference-help"/><span id="preference-help" className="mt-1 block text-xs text-slate-500">Separate up to 12 preferences with commas, such as videos, books, labs or projects.</span></label>
 </fieldset>{error&&<p role="alert" className="text-sm text-red-700">{error}</p>}
 <div className="flex justify-end gap-2"><button type="button" disabled={busy} onClick={close} className="rounded-lg border px-4 py-2 text-sm">Cancel</button><button disabled={busy||!form.name.trim()} className="rounded-lg bg-teal-700 px-4 py-2 text-sm text-white disabled:opacity-50">{busy?'Saving...':'Save'}</button></div>
 </form></div></div>;
}
