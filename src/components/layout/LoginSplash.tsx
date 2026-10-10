import './LoginSplash.css';
import {useEffect,useState,type ReactNode} from 'react';
const SEEN='nexvora_splash_shown';
function shouldShow(){
 if(typeof window==='undefined')return false;
 try{return !sessionStorage.getItem('plcip_token')&&!sessionStorage.getItem(SEEN);}catch{return true;}
}
/** Transparent SVG layers use the supplied mark as reference, with no raster background. */
function SplashMark(){
 return <svg className="nexvora-splash-art" viewBox="0 0 1000 650" role="img" aria-label="NexVora – SKILLS TODAY • OPPORTUNITIES TOMORROW">
  <defs>
   <linearGradient id="nv-arc" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#91ffff"/><stop offset=".38" stopColor="#00e4ee"/><stop offset="1" stopColor="#008def"/></linearGradient>
   <linearGradient id="nv-star" x1="0" y1="0" x2="1" y2="1"><stop stopColor="#e8ffff"/><stop offset=".45" stopColor="#16ebf3"/><stop offset="1" stopColor="#0095ec"/></linearGradient>
   <linearGradient id="nv-word" x1="0" y1="0" x2="0" y2="1"><stop stopColor="#73ffff"/><stop offset=".5" stopColor="#00d9e3"/><stop offset="1" stopColor="#008de4"/></linearGradient>
   <linearGradient id="nv-arrow" x1="0" y1="1" x2="1" y2="0"><stop stopColor="#e6f7ff"/><stop offset=".55" stopColor="#ffffff"/><stop offset="1" stopColor="#42eff7"/></linearGradient>
   <linearGradient id="nv-sweep"><stop stopColor="#fff" stopOpacity="0"/><stop offset=".5" stopColor="#fff" stopOpacity=".4"/><stop offset="1" stopColor="#fff" stopOpacity="0"/></linearGradient>
   <clipPath id="nv-letter-area"><rect x="140" y="443" width="720" height="125"/></clipPath>
  </defs>
  <g className="nv-energy" aria-hidden="true"><circle className="energy-dot" cx="500" cy="245" r="2"/><circle className="orbit-ring" cx="500" cy="245" r="140"/><circle className="orbit-ring ring-2" cx="500" cy="245" r="190"/></g>
  <g className="particles-container" aria-hidden="true">{[[340,150],[670,155],[300,320],[690,335],[500,65]].map(([x,y],i)=><circle key={i} className={`particle particle-${i}`} cx={x} cy={y} r="2"/>)}</g>
  <g className="logo-overlay">
   <path className="outer-arc" pathLength="100" d="M 353,353 A 178,178 0 1 1 676,189" fill="none" stroke="url(#nv-arc)" strokeWidth="25"/>
   <path className="inner-arc" d="M 360 167 C 327 258 355 341 432 362 L 390 361 C 325 318 317 237 360 167" fill="#0077a7"/>
   <g className="inner-star"><path d="M500 126 L518 218 L594 239 L518 258 L500 337 L482 258 L407 239 L482 218Z" fill="url(#nv-star)"/><path d="M500 126 L500 239 L482 218Z M500 239 L594 239 L518 258Z M500 239 L500 337 L482 258Z" fill="#009ce7" opacity=".7"/><path d="M500 126 L518 218 L500 239Z M407 239 L482 218 L500 239Z" fill="#a8ffff" opacity=".7"/></g>
   <path className="small-star" d="M589 109 L598 132 L621 140 L598 148 L589 173 L582 148 L558 140 L582 132Z" fill="url(#nv-star)"/>
   <g className="arrow">
    <path d="M311 291 C314 421 529 430 710 150 C584 411 372 480 311 291Z" fill="url(#nv-arrow)"/>
    <path d="M311 291 C330 386 517 388 672 240 C536 410 350 416 311 291Z" fill="url(#nv-arc)"/>
    <path d="M678 156 L741 118 L729 184 L714 151Z" fill="url(#nv-star)"/>
    <path d="M423 426 C559 444 644 371 686 289 C664 415 556 481 423 426Z" fill="url(#nv-word)"/>
   </g>
  </g>
  <g className="wordmark-container" clipPath="url(#nv-letter-area)"><text className="wordmark nex" x="500" y="551" textAnchor="end">Nex</text><text className="wordmark vora" x="500" y="551" fill="url(#nv-word)">Vora</text></g>
  <text className="tagline-container" x="500" y="606" textAnchor="middle">SKILLS TODAY • OPPORTUNITIES TOMORROW</text>
  <path className="glow-sweep" d="M200 60 L255 60 L650 620 L595 620Z" fill="url(#nv-sweep)" aria-hidden="true"/>
 </svg>;
}
export function LoginSplash({children}:{children:ReactNode}){
 const [visible,setVisible]=useState(shouldShow),[fading,setFading]=useState(false);
 const [reduced,setReduced]=useState(()=>typeof window!=='undefined'&&Boolean(window.matchMedia?.('(prefers-reduced-motion: reduce)').matches));
 useEffect(()=>{
  if(!visible)return;
  try{sessionStorage.setItem(SEEN,'1');}catch{}
  const bodyOverflow=document.body.style.overflow,rootOverflow=document.documentElement.style.overflow;
  document.body.style.overflow='hidden';document.documentElement.style.overflow='hidden';
  const media=window.matchMedia?.('(prefers-reduced-motion: reduce)');
  const change=()=>setReduced(Boolean(media?.matches));media?.addEventListener?.('change',change);
  return()=>{document.body.style.overflow=bodyOverflow;document.documentElement.style.overflow=rootOverflow;media?.removeEventListener?.('change',change);};
 },[visible]);
 useEffect(()=>{
  if(!visible)return;
  const fade=setTimeout(()=>setFading(true),reduced?1500:5600);
  const done=setTimeout(()=>setVisible(false),reduced?2100:6200);
  return()=>{clearTimeout(fade);clearTimeout(done);};
 },[visible,reduced]);
 return <>
  <div className={`nexvora-login-layer${visible&&!fading?' nexvora-login-layer--waiting':''}`} inert={visible?true:undefined} aria-hidden={visible?true:undefined}>{children}</div>
  {visible&&<div id="splash-screen" role="status" aria-label="NexVora introduction" className={`nexvora-splash${reduced?' is-reduced':''}${fading?' splash-exit':''}`}><div className="logo-container"><SplashMark/></div></div>}
 </>;
}
