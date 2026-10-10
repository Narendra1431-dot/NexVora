import { useUndoableState } from '../../lib/state/edit-history';
import {useEffect, useState, type FormEvent} from 'react';
import {useModalDialog} from '../../lib/hooks/use-modal-dialog';
import {useAppState} from '../../lib/state/app-state';
import {certButton} from './CertificateShared';

export type IndustryCertification = {id:string;name:string;provider:string;initials:string;categories:string[];level:string|null;description:string;officialUrl:string;linkCheckedAt:string};
export type AddedCredential = {id:string;certificationId:string;credentialId:string;credentialUrl:string;issueDate:string;expiryDate:string|null;status:'Added'|'Verified'|'Expired';hasProof:boolean;proofName:string|null;reviewNote?:string};
type CatalogResponse = {catalog:IndustryCertification[];credentials:AddedCredential[]};
const base='/api/v1/external-certifications';
const auth=()=>({Authorization:`Bearer ${sessionStorage.getItem('plcip_token')||''}`});
async function checked(response:Response){
 if(!response.ok){const data=await response.json().catch(()=>({}));throw new Error(typeof data.detail==='string'?data.detail:'Unable to save credential. Check your fields and try again.');}
 return response;
}
const inputClass='mt-1 block w-full rounded-lg border border-slate-300 bg-white p-2 text-sm font-normal';
export function ExternalCertifications({addedOnly,category}:{addedOnly:boolean;category:string}){
 const {refreshWorkspace}=useAppState();
 const [data,setData]=useState<CatalogResponse|null>(null);
 const [error,setError]=useState('');const [notice,setNotice]=useState('');
 const [details,setDetails]=useState<IndustryCertification|null>(null);
 const [form,setForm]=useState<{cert:IndustryCertification;credential?:AddedCredential}|null>(null);
 const [loading,setLoading]=useState(true);const [proofBusy,setProofBusy]=useState('');
 const detailsRef=useModalDialog(Boolean(details),()=>setDetails(null));
 async function load(){setLoading(true);setError('');try{setData(await (await checked(await fetch(base,{headers:auth()}))).json());}catch(e){setError((e as Error).message);}finally{setLoading(false);}}
 useEffect(()=>{let active=true;fetch(base,{headers:auth()}).then(checked).then(r=>r.json()).then(d=>{if(active)setData(d);}).catch(e=>{if(active)setError(e.message);}).finally(()=>{if(active)setLoading(false);});return()=>{active=false;};},[]);
 async function saved(credential:AddedCredential){
  setData(current=>current?{...current,credentials:[credential,...current.credentials.filter(c=>c.id!==credential.id)]}:current);
  setForm(null);setNotice('Credential saved to your profile and Evidence Vault. Verification requires independent review.');
  try{await refreshWorkspace();}catch{setNotice('Credential saved. Refresh the profile to load its updated Evidence Vault entry.');}
 }
 async function download(credential:AddedCredential){
  setProofBusy(credential.id);setError('');
  try{const response=await checked(await fetch(`${base}/credentials/${credential.id}/proof`,{headers:auth()}));const url=URL.createObjectURL(await response.blob());const a=document.createElement('a');a.href=url;a.download=credential.proofName||'certificate-proof';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  catch(e){setError((e as Error).message);}finally{setProofBusy('');}
 }
 const matches=(data?.catalog||[]).filter(c=>(category==='All'||c.categories.includes(category))&&(!addedOnly||data?.credentials.some(d=>d.certificationId===c.id)));
 return <section className="space-y-4" aria-label={addedOnly?'My Added Credentials':'External Certifications'}>
  <div><h3 className="font-bold text-lg">{addedOnly?'My Added Credentials':'External / Industry Certifications'}</h3><p className="text-sm text-slate-600 mt-1">{addedOnly?'Your external awards, stored separately from NexVora-issued certificates.':'Explore official provider certifications and add credentials you have already earned.'}</p><p className="mt-1 text-xs text-slate-500">Added = self-reported. Verified = independently reviewed by an authorized reviewer. Expired = past the recorded expiry date.</p></div>
  {error&&<div role="alert" className="rounded-xl bg-red-50 p-4 text-sm text-red-800">{error}<button className={certButton+' ml-3'} onClick={load}>Retry</button></div>}
  {notice&&<p role="status" className="rounded-xl bg-teal-50 p-3 text-sm text-teal-800">{notice}</p>}
  {loading?<p role="status">Loading certifications...</p>:data&&<><p className="text-xs text-slate-500">{matches.length} {addedOnly?'saved credentials':'certifications'}{category!=='All'?` in ${category}`:''}</p>{!matches.length&&<div className="rounded-xl border border-dashed p-8 text-center text-sm text-slate-500">{addedOnly?'No saved credentials in this category. Explore External Certifications to add an award.':'No certifications match this category.'}</div>}<div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">{matches.map(cert=>{
   const credential=data.credentials.find(c=>c.certificationId===cert.id);
   return <article key={cert.id} aria-label={cert.name} className="flex flex-col rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
    <div className="flex items-center justify-between gap-3"><span aria-label={`${cert.provider} initials`} className="flex h-11 min-w-11 items-center justify-center rounded-xl bg-slate-100 px-2 text-sm font-bold text-slate-700">{cert.initials}</span><span className={'rounded-full px-2 py-1 text-xs font-semibold '+(credential?.status==='Verified'?'bg-teal-50 text-teal-800':credential?.status==='Expired'?'bg-amber-50 text-amber-800':'bg-slate-100 text-slate-600')}>{credential?.status||'Available'}</span></div>
    <p className="mt-3 text-xs font-semibold text-slate-500">{cert.provider}</p><h4 className="mt-1 font-bold text-slate-900">{cert.name}</h4><p className="mt-2 text-sm text-slate-600">{cert.description}</p><p className="mt-3 text-xs text-teal-800">{cert.categories.join(' / ')}{cert.level?` · ${cert.level}`:''}</p>
    {addedOnly&&credential&&<dl className="my-3 space-y-1 text-xs text-slate-600"><div><dt className="inline font-semibold">Credential ID: </dt><dd className="inline break-all">{credential.credentialId||'Not provided'}</dd></div><div><dt className="inline font-semibold">Issued: </dt><dd className="inline">{credential.issueDate}</dd></div><div><dt className="inline font-semibold">Expires: </dt><dd className="inline">{credential.expiryDate||'Not specified'}</dd></div>{credential.reviewNote&&<div><dt className="font-semibold">Review note</dt><dd>{credential.reviewNote}</dd></div>}</dl>}
    <div className="mt-auto flex flex-wrap gap-2 pt-4"><button className={certButton} onClick={()=>setDetails(cert)}>View Certification</button><a className={certButton} href={cert.officialUrl} target="_blank" rel="noopener noreferrer">Official Website</a><button className={certButton} onClick={()=>{setNotice('');setForm({cert,credential});}}>{credential?'Edit Credential':'Add to My Profile'}</button>{addedOnly&&credential?.credentialUrl&&<a className={certButton} href={credential.credentialUrl} target="_blank" rel="noopener noreferrer">Open Credential</a>}{addedOnly&&credential?.hasProof&&<button className={certButton} disabled={Boolean(proofBusy)} onClick={()=>download(credential)}>{proofBusy===credential.id?'Downloading...':'Download Proof'}</button>}</div>
   </article>;
  })}</div></>}
  {details&&<div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"><div ref={detailsRef} role="dialog" aria-modal="true" aria-label="Certification details" tabIndex={-1} className="max-h-[90dvh] w-full max-w-xl overflow-auto rounded-xl bg-white p-6 space-y-4"><div className="flex justify-between gap-3"><h3 className="font-bold text-lg">{details.name}</h3><button className={certButton} onClick={()=>setDetails(null)}>Close</button></div><p className="text-sm font-semibold">{details.provider}</p><p className="text-sm text-slate-600">{details.description}</p><p className="text-sm">{details.categories.join(' / ')}{details.level?` · ${details.level}`:''}</p><p className="text-xs text-slate-500">This credential is issued by the external provider, not NexVora. Requirements and exam details are maintained on the official page. Link checked {details.linkCheckedAt}.</p><a className={certButton+' inline-block'} href={details.officialUrl} target="_blank" rel="noopener noreferrer">Open Official Certification Page</a><button className={certButton} onClick={()=>{setDetails(null);setForm({cert:details,credential:data?.credentials.find(c=>c.certificationId===details.id)});}}> {data?.credentials.some(c=>c.certificationId===details.id)?'Edit Credential':'Add to My Profile'}</button></div></div>}
  {form&&<CredentialForm key={form.cert.id} {...form} onClose={()=>setForm(null)} onSaved={saved}/>}
 </section>;
}

function CredentialForm({cert,credential,onClose,onSaved}:{cert:IndustryCertification;credential?:AddedCredential;onClose:()=>void;onSaved:(record:AddedCredential)=>Promise<void>}){
 const [id,setId]=useUndoableState(credential?.credentialId||'','Credential ID');const [url,setUrl]=useUndoableState(credential?.credentialUrl||'','Credential URL');
 const [issued,setIssued]=useUndoableState(credential?.issueDate||'','Credential issue date');const [expiry,setExpiry]=useUndoableState(credential?.expiryDate||'','Credential expiry date');
 const [file,setFile]=useState<File|null>(null);const [busy,setBusy]=useState(false);const [error,setError]=useState('');
 const dialog=useModalDialog(true,()=>{if(!busy)onClose();});
 async function submit(event:FormEvent){event.preventDefault();if(busy)return;setError('');if(file&&file.size>5*1024*1024){setError('Proof must be 5 MB or smaller.');return;}setBusy(true);
  try{const body=new FormData();body.append('payload',JSON.stringify({certificationId:cert.id,credentialId:id,credentialUrl:url,issueDate:issued,expiryDate:expiry||null}));if(file)body.append('proof',file);
   const response=await checked(await fetch(base+'/credentials'+(credential?'/'+credential.id:''),{method:credential?'PUT':'POST',headers:auth(),body}));await onSaved(await response.json());
  }catch(e){setError((e as Error).message);}finally{setBusy(false);}
 }
 return <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-4"><div ref={dialog} role="dialog" aria-modal="true" aria-label={credential?'Edit external credential':'Add external credential'} tabIndex={-1} className="max-h-[90dvh] w-full max-w-xl overflow-auto rounded-xl bg-white p-6"><form onSubmit={submit} className="space-y-4"><div className="flex justify-between gap-3"><h3 className="font-bold">{credential?'Edit':'Add'} credential</h3><button type="button" disabled={busy} className={certButton} onClick={onClose}>Cancel</button></div><p className="text-sm font-semibold">{cert.name}</p><p className="text-xs text-slate-500">Provide a credential ID, a public credential URL or proof. Details remain self-reported until independently reviewed. Editing a reviewed credential resets its verification.</p><fieldset disabled={busy} className="space-y-4"><label className="block text-sm font-semibold">Credential ID<input className={inputClass} value={id} maxLength={200} data-undo="true" onChange={e=>setId(e.target.value)}/></label><label className="block text-sm font-semibold">Credential URL<input type="url" placeholder="https://" className={inputClass} value={url} maxLength={2000} data-undo="true" onChange={e=>setUrl(e.target.value)}/></label><div className="grid grid-cols-1 sm:grid-cols-2 gap-3"><label className="block text-sm font-semibold">Issue Date<input required type="date" className={inputClass} value={issued} data-undo="true" onChange={e=>setIssued(e.target.value)}/></label><label className="block text-sm font-semibold">Expiry Date (optional)<input type="date" min={issued||undefined} className={inputClass} value={expiry} data-undo="true" onChange={e=>setExpiry(e.target.value)}/></label></div><label className="block rounded-xl border border-dashed border-slate-300 bg-slate-50 p-4 text-sm font-semibold">Upload certificate proof<input type="file" accept="application/pdf,image/png,image/jpeg" className="mt-2 block w-full text-xs file:mr-3 file:rounded-lg file:border-0 file:bg-teal-50 file:px-3 file:py-2 file:font-semibold file:text-teal-800" onChange={e=>setFile(e.target.files?.[0]||null)}/><span className="mt-2 block text-xs font-normal text-slate-500">PDF, PNG or JPEG, up to 5 MB. {file?file.name:credential?.hasProof?'Existing proof retained unless replaced.':'Proof is private to your account.'}</span></label></fieldset>{error&&<p role="alert" className="text-sm text-red-800">{error}</p>}<button className={certButton+' bg-teal-50 text-teal-800'} disabled={busy}>{busy?'Saving...':'Save Credential'}</button></form></div></div>;
}
