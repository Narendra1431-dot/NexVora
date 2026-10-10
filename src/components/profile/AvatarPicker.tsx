import {useEffect,useRef,useState} from 'react';
import {useAppState} from '../../lib/state/app-state';
import {useModalDialog} from '../../lib/hooks/use-modal-dialog';
import {DEFAULT_AVATARS,ProfileAvatar} from './ProfileAvatar';
const button='rounded-lg border border-slate-200 px-3 py-2 text-sm hover:bg-slate-50 disabled:opacity-50';
export function AvatarPicker({onClose}:{onClose:()=>void}){
 const {student,refreshWorkspace}=useAppState();
 const [mode,setMode]=useState<'current'|'preset'|'photo'|'reset'>('current'),[preset,setPreset]=useState(student.avatar?.kind==='preset'?student.avatar.presetId:'student-1');
 const [file,setFile]=useState<File|null>(null),[image,setImage]=useState<HTMLImageElement|null>(null);
 const [zoom,setZoom]=useState(1),[x,setX]=useState(50),[y,setY]=useState(50),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const canvas=useRef<HTMLCanvasElement>(null);const dialog=useModalDialog(true,()=>{if(!busy)onClose();});
 useEffect(()=>{if(!file)return;let live=true;const url=URL.createObjectURL(file),img=new Image();
 img.onload=()=>{if(!live)return;if(img.naturalWidth*img.naturalHeight>16_000_000){setError('Choose a photo up to 16 megapixels.');return;}setImage(img);};
 img.onerror=()=>{if(live)setError('This photo cannot be opened. Choose another JPG, PNG or WebP.');};img.src=url;
 return()=>{live=false;URL.revokeObjectURL(url);};},[file]);
 useEffect(()=>{if(!image||mode!=='photo'||!canvas.current)return;const ctx=canvas.current.getContext('2d');if(!ctx)return;
 const side=Math.min(image.naturalWidth,image.naturalHeight)/zoom,sx=(image.naturalWidth-side)*x/100,sy=(image.naturalHeight-side)*y/100;
 ctx.fillStyle='#f1f5f9';ctx.fillRect(0,0,384,384);ctx.drawImage(image,sx,sy,side,side,0,0,384,384);
 },[image,mode,zoom,x,y]);
 const save=async()=>{if(busy)return;setBusy(true);setError('');try{
  const headers:Record<string,string>={Authorization:'Bearer '+sessionStorage.getItem('plcip_token')};let path='/avatar',method='PUT',body:BodyInit|undefined;
  if(mode==='photo'){
   if(!image||!canvas.current)throw new Error('Wait for your photo preview.');
   const blob=await new Promise<Blob>((resolve,reject)=>canvas.current!.toBlob(v=>v?resolve(v):reject(new Error('Unable to crop this photo.')),'image/webp',.9));
   const form=new FormData();form.append('file',blob,'profile.webp');body=form;path='/photo';method='POST';
  }else if(mode==='reset')method='DELETE';else {headers['Content-Type']='application/json';body=JSON.stringify({presetId:preset});}
  const result=await fetch('/api/v1/profile'+path,{method,headers,body});if(!result.ok){const data=await result.json();throw new Error(typeof data.detail==='string'?data.detail:'Unable to save avatar.');}
  await refreshWorkspace();onClose();
 }catch(e){setError((e as Error).message);}finally{setBusy(false);}};
 const preview=mode==='preset'?{kind:'preset' as const,presetId:preset}:mode==='reset'?null:student.avatar;
 return <div className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/40 p-3 sm:p-6"><div ref={dialog} role="dialog" aria-modal="true" aria-label="Profile photo and avatar" tabIndex={-1} className="max-h-[90dvh] w-full max-w-2xl overflow-y-auto rounded-2xl bg-white p-5 sm:p-6 space-y-5">
 <h2>Profile photo and avatar</h2><div className="flex flex-wrap items-center gap-4">
 {mode==='photo'?<canvas ref={canvas} width="384" height="384" role="img" aria-label="Square photo crop preview" className="h-36 w-36 rounded-xl bg-slate-100"/>:<ProfileAvatar name={student.name} avatar={preview} className="h-24 w-24"/>}
 <div className="space-y-2"><label className={button+' inline-block cursor-pointer focus-within:ring-2 focus-within:ring-teal-600'}>Upload Photo<input aria-label="Upload Photo" type="file" accept="image/jpeg,image/png,image/webp" disabled={busy} className="sr-only" onChange={e=>{const next=e.target.files?.[0];e.target.value='';if(!next)return;setError('');if(!['image/jpeg','image/png','image/webp'].includes(next.type)){setError('Use JPG, PNG or WebP.');return;}if(next.size>5*1024*1024){setError('Photo must be 5 MB or smaller.');return;}setImage(null);setFile(next);setZoom(1);setX(50);setY(50);setMode('photo');}}/></label><p className="text-xs text-slate-500">JPG, PNG or WebP · up to 5 MB / 16 megapixels.</p><button className={button} disabled={busy} onClick={()=>{setMode('reset');setFile(null);setImage(null);setError('');}}>Remove / Reset Photo</button></div></div>
 {mode==='photo'&&<fieldset disabled={busy||!image} className="grid gap-3 sm:grid-cols-3">{([['Zoom',zoom,setZoom,1,3,.05],['Horizontal position',x,setX,0,100,1],['Vertical position',y,setY,0,100,1]] as const).map(([label,value,setter,min,max,step])=><label key={label} className="text-xs font-medium">{label}<input type="range" className="mt-2 block w-full accent-teal-700" min={min} max={max} step={step} value={value} onChange={e=>setter(Number(e.target.value))}/></label>)}</fieldset>}
 <section><h3 className="mb-3">Choose Default Avatar</h3><div className="grid grid-cols-4 gap-2 sm:grid-cols-8">{DEFAULT_AVATARS.map(([id,label])=><button key={id} type="button" title={label} aria-label={label} aria-pressed={(mode==='preset'||mode==='current'&&student.avatar?.kind==='preset')&&preset===id} disabled={busy} onClick={()=>{setPreset(id);setMode('preset');setFile(null);setImage(null);setError('');}} className={'rounded-xl border p-2 hover:bg-teal-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-600 '+((mode==='preset'||mode==='current'&&student.avatar?.kind==='preset')&&preset===id?'border-teal-600 bg-teal-50 ring-1 ring-teal-600':'border-slate-200')}><ProfileAvatar name={student.name} avatar={{kind:'preset',presetId:id}} className="h-auto w-full aspect-square"/></button>)}</div><p className="mt-2 text-xs text-slate-500">Original student, coder, AI, hero, minimal and initials styles.</p></section>
 {error&&<p role="alert" className="text-sm text-red-700">{error}</p>}
 <div className="flex justify-end gap-2"><button className={button} disabled={busy} onClick={onClose}>Cancel</button><button className={button+' bg-teal-700 text-white hover:bg-teal-800'} disabled={busy||mode==='current'||mode==='photo'&&!image} onClick={()=>void save()}>{busy?'Saving...':'Save Avatar'}</button></div>
 </div></div>;
}
