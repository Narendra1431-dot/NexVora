import {useEffect,useState} from 'react';
export function ServerCertificatePreview({courseId,type,displayName,displaySubtitle,onReady}:{courseId:string;type:'free'|'premium';displayName:string;displaySubtitle:string;onReady:(ready:boolean)=>void}){
 const [image,setImage]=useState('');const [error,setError]=useState('');
 useEffect(()=>{
  const controller=new AbortController();let url='';let active=true;
  onReady(false);setImage('');setError('');
  const timer=setTimeout(async()=>{try{
   const response=await fetch('/api/v1/certificates/preview',{method:'POST',headers:{'Content-Type':'application/json',Authorization:`Bearer ${sessionStorage.getItem('plcip_token')||''}`},body:JSON.stringify({courseId,type,displayName,displaySubtitle}),signal:controller.signal});
   if(!response.ok){const problem=await response.json().catch(()=>({}));throw new Error(typeof problem.detail==='string'?problem.detail:'Unable to preview. Check your display name and try again.');}
   const blob=await response.blob();if(!active)return;
   url=URL.createObjectURL(blob);setImage(url);
  }catch(e){if(active&&!controller.signal.aborted)setError((e as Error).message);}},250);
  return()=>{active=false;controller.abort();clearTimeout(timer);if(url)URL.revokeObjectURL(url);};
 },[courseId,type,displayName,displaySubtitle,onReady]);
 return <div className="space-y-2">{error?<p role="alert" className="text-sm text-red-800">{error}</p>:!image?<p role="status" className="p-8 text-center text-slate-600 bg-slate-50 rounded-lg">Preparing your certificate preview...</p>:<img src={image} alt="Your certificate rendered from the final PDF template" className="w-full h-auto border rounded-sm" onLoad={()=>onReady(true)} onError={()=>{onReady(false);setError('Certificate preview image could not load.');}}/>}<p className="text-xs text-slate-500">Preview only. The server assigns the final certificate ID, issue date and verification QR on issuance.</p></div>;
}
