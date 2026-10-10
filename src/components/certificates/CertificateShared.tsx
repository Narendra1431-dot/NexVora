import {useState} from 'react';
import type {Certificate} from './api';
export const certButton='rounded-lg border border-slate-200 bg-white px-3 py-2 text-sm font-semibold text-slate-700 hover:bg-slate-50 disabled:opacity-50';
export function CertificateActions({certificate}:{certificate:Certificate}){
 const [notice,setNotice]=useState('');
 const action=async(kind:'copy'|'share'|'download')=>{setNotice('');try{
  if(kind==='download'){
   const response=await fetch(certificate.pdfUrl);if(!response.ok)throw new Error('PDF download failed.');
   const url=URL.createObjectURL(await response.blob());const a=document.createElement('a');a.href=url;a.download=certificate.certificateId+'.pdf';document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(url),1000);setNotice('PDF download started.');
  }else if(kind==='share'&&navigator.share){await navigator.share({title:certificate.courseName+' certificate',url:certificate.publicUrl});}
  else{await navigator.clipboard.writeText(certificate.publicUrl);setNotice('Verification link copied.');}
 }catch(error){if((error as Error).name!=='AbortError')setNotice((error as Error).message||'Unable to complete this action.');}};
 return <div className="space-y-2"><div className="flex flex-wrap gap-2"><a className={certButton} href={'/certificate/'+certificate.certificateId} target="_blank" rel="noreferrer">Open</a><a className={certButton} href={certificate.publicUrl} target="_blank" rel="noopener noreferrer">Verify</a><button className={certButton} onClick={()=>action('download')}>Download PDF</button><button className={certButton} onClick={()=>action('copy')}>Copy Link</button><button className={certButton} onClick={()=>action('share')}>Share</button></div>{notice&&<p role="status" className="text-xs text-slate-600">{notice}</p>}</div>;
}
