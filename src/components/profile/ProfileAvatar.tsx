import {useState} from 'react';
import type {ProfileAvatar as AvatarValue} from '../../types';
export const DEFAULT_AVATARS=[
 ['student-1','Student · short hair'],['student-2','Student · long hair'],['coder-1','Coder · glasses'],['coder-2','Coder · hoodie'],
 ['ai-1','AI · orbit'],['ai-2','AI · horizon'],['hero-1','Hero · teal guardian'],['hero-2','Hero · midnight scout'],
 ['minimal-1','Minimal · warm'],['minimal-2','Minimal · cool'],['initials-1','Initials · teal'],['initials-2','Initials · navy'],
 ['scholar-1','Scholar · cap'],['scholar-2','Scholar · curls'],['explorer-1','Explorer · sunrise'],['explorer-2','Explorer · dusk'],
] as const;
const initials=(name:string)=>name.trim().split(/\s+/).map(p=>p[0]).slice(0,2).join('').toUpperCase()||'?';
export function ProfileAvatar({name,avatar,className='h-16 w-16'}:{name:string;avatar?:AvatarValue|null;className?:string}){
 const [failed,setFailed]=useState('');
 const photo=avatar?.kind==='photo'&&/^data:image\/(webp|png|jpeg);base64,/.test(avatar.dataUrl)?avatar.dataUrl:'';
 const id=avatar?.kind==='preset'?avatar.presetId:'';
 const known=DEFAULT_AVATARS.some(([key])=>key===id);
 const second=id.endsWith('-2'),ai=id.startsWith('ai-'),hero=id.startsWith('hero-'),coder=id.startsWith('coder-');
 const skin=second?'#c99172':'#edc5a6',ink=second?'#334155':'#115e59',background=second?'#e2e8f0':'#ccfbf1';
 return <span className={`inline-flex shrink-0 overflow-hidden rounded-full bg-slate-100 ring-1 ring-inset ring-slate-200 ${className}`}>
 {photo&&failed!==photo?<img src={photo} onError={()=>setFailed(photo)} alt={`${name}'s profile photo`} className="h-full w-full object-cover"/>:
 <svg role="img" aria-label={`${name}'s ${known?'selected avatar':'initials'}`} viewBox="0 0 80 80" className="h-full w-full">
  <rect width="80" height="80" fill={background}/>
  {!known||id.startsWith('initials-')?<><path d="M0 60 80 15v65H0" fill={ink} opacity=".09"/><text x="40" y="43" dominantBaseline="middle" textAnchor="middle" fill={ink} fontFamily="Inter,system-ui,sans-serif" fontWeight="600" fontSize="27">{initials(name)}</text></>:
  ai?<><path d="M20 76V59q20-15 40 0v17" fill={ink}/><rect x="17" y="18" width="46" height="39" rx={second?18:12} fill={ink}/><rect x="23" y="27" width="34" height="19" rx="8" fill="#f0fdfa"/><path d="M40 18v-8" stroke={ink} strokeWidth="3"/><circle cx="40" cy="9" r="4" fill="#14b8a6"/><circle cx="32" cy="36" r="3" fill={ink}/><circle cx="48" cy="36" r="3" fill={ink}/><path d="M35 43h10" stroke="#14b8a6" strokeWidth="2"/></>:
  <>
   {hero&&<path d="M20 47 7 80h66L60 47Z" fill={second?'#64748b':'#0d9488'}/>}
   {second&&!hero&&<path d="M21 29q0-20 19-20 21 0 21 23v32H20z" fill="#334155"/>}
   <path d="M10 80V68q1-19 30-20 30 1 30 20v12" fill={ink}/>
   <path d="M33 44h14v11q-7 8-14 0" fill={skin}/><ellipse cx="40" cy="31" rx="17" ry="21" fill={skin}/>
   {!id.startsWith('minimal-')&&<path d={second?'M23 31q-5-23 17-23 22 1 18 25L44 17q-5 12-21 14':'M23 31q-6-23 16-23 24 0 20 25l-9-17q-7 12-27 8z'} fill="#243746"/>}
   {hero&&<path d="m23 26 17 4 17-4-3 15-14-3-14 3z" fill={ink}/>}
   <circle cx="33" cy="33" r="1.8" fill={hero?'#f0fdfa':'#334155'}/><circle cx="47" cy="33" r="1.8" fill={hero?'#f0fdfa':'#334155'}/>
   <path d="M35 43q5 4 10 0" stroke="#804e42" strokeWidth="1.8" fill="none" strokeLinecap="round"/>
   {coder&&<g fill="none" stroke="#0f172a" strokeWidth="2"><rect x="26" y="28" width="12" height="10" rx="3"/><rect x="42" y="28" width="12" height="10" rx="3"/><path d="M38 32h4m-9 30-5 5 5 5m14-10 5 5-5 5" stroke={ink==='#115e59'?'#5eead4':'#cbd5e1'}/></g>}
   {id.startsWith('scholar-')&&<><path d="m13 15 27-10 27 10-27 10z" fill={ink}/><path d="M62 17v18" stroke="#d97706" strokeWidth="2"/></>}
   {id.startsWith('explorer-')&&<path d="m23 59 17 12 17-12" fill="none" stroke="#fbbf24" strokeWidth="5"/>}
   {hero&&<circle cx="40" cy="66" r="5" fill="#99f6e4"/>}
  </>}
 </svg>}
 </span>;
}
