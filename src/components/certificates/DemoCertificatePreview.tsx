import {useState} from 'react';
import {useModalDialog} from '../../lib/hooks/use-modal-dialog';
import {certButton} from './CertificateShared';

export function DemoCertificatePreview({onClose}:{onClose:()=>void}) {
 const [tier,setTier]=useState<'free'|'premium'>('premium');
 const [zoom,setZoom]=useState(100);
 const [fullScreen,setFullScreen]=useState(false);
 const [loaded,setLoaded]=useState(false);
 const [error,setError]=useState(false);
 const dialog=useModalDialog(true,onClose);
 const path='/api/v1/certificates/demo/'+tier;
 const changeTier=(value:'free'|'premium')=>{setTier(value);setLoaded(false);setError(false);setZoom(100);};
 return <div className="fixed inset-0 z-50 bg-slate-900/60 flex items-center justify-center p-0 sm:p-4"><section ref={dialog} role="dialog" aria-modal="true" aria-label="Demo certificate preview" tabIndex={-1} className={'bg-white flex flex-col min-h-0 shadow-xl '+(fullScreen?'fixed inset-0':'w-full max-w-6xl h-[94dvh] rounded-xl')}>
  <header className="p-4 border-b border-slate-200 space-y-3 shrink-0"><div className="flex flex-wrap items-center justify-between gap-2"><div><h2 className="font-semibold text-slate-900">Preview Demo Certificate</h2><p className="text-xs text-amber-800 mt-1">DEMO / SAMPLE — not issued, not verified, and never added to your Evidence Vault.</p></div><button className={certButton} onClick={onClose}>Close Preview</button></div>
   <div className="flex flex-wrap gap-2" role="group" aria-label="Certificate template"><button className={certButton} aria-pressed={tier==='free'} onClick={()=>changeTier('free')}>Standard Certificate Preview</button><button className={certButton} aria-pressed={tier==='premium'} onClick={()=>changeTier('premium')}>Premium Certificate Preview</button></div>
   <div className="flex flex-wrap items-center gap-2"><button className={certButton} aria-label="Zoom out" disabled={zoom<=50} onClick={()=>setZoom(z=>Math.max(50,z-25))}>−</button><output aria-label="Preview zoom" className="text-sm w-12 text-center">{zoom}%</output><button className={certButton} aria-label="Zoom in" disabled={zoom>=200} onClick={()=>setZoom(z=>Math.min(200,z+25))}>+</button><button className={certButton} onClick={()=>setZoom(100)}>Fit Width</button><button className={certButton} aria-pressed={fullScreen} onClick={()=>setFullScreen(v=>!v)}>{fullScreen?'Exit Full-screen':'Full-screen Viewer'}</button><a className={certButton+' !bg-teal-700 !text-white'} href={path+'/pdf'} download={`NexVora-${tier}-DEMO-SAMPLE.pdf`}>Download Sample PDF</a></div>
  </header>
  <div className="flex-1 min-h-0 overflow-auto bg-slate-100 p-3 sm:p-5" aria-label="Certificate preview canvas">
   {!loaded&&!error&&<p role="status" className="text-sm text-slate-600 mb-3">Rendering sample certificate...</p>}
   {error?<p role="alert" className="p-4 bg-white border rounded-lg text-red-800">The sample preview could not load. Try switching templates or reopening the preview.</p>:<img key={tier} src={path+'/preview.png'} alt={`${tier==='premium'?'Premium Verified':'Standard'} Certificate — DEMO / SAMPLE. Alex Rivera, Machine Learning Foundations, sample date, DEMO-CERT-001.${tier==='premium'?' Score 88%. Verified skills (sample): Python, ML, Model Evaluation.':''} NexVora signature and demo verification QR.`} onLoad={()=>setLoaded(true)} onError={()=>setError(true)} className="block mx-auto shadow-sm" style={{width:zoom+'%',maxWidth:'none',height:'auto'}}/>}
  </div>
  <p className="p-3 text-xs text-slate-500 border-t">A4 landscape · Rendered directly from the final certificate PDF template · QR opens a sample-only notice.</p>
 </section></div>;
}
