import {useEffect,useRef,useState} from 'react';
import Editor,{loader,type OnMount} from '@monaco-editor/react';
import * as monaco from 'monaco-editor/editor/editor.api.js';
import EditorWorker from 'monaco-editor/editor/editor.worker.js?worker';
import TsWorker from 'monaco-editor/language/typescript/ts.worker.js?worker';
import 'monaco-editor/languages/definitions/python/register.js';
import 'monaco-editor/languages/definitions/javascript/register.js';
import 'monaco-editor/languages/definitions/java/register.js';
import 'monaco-editor/languages/definitions/cpp/register.js';
import 'monaco-editor/language/typescript/monaco.contribution.js';
import 'monaco-editor/editor/contrib/format/browser/formatActions.js';
import 'monaco-editor/editor/contrib/bracketMatching/browser/bracketMatching.js';
import {codingApi} from './api';
(self as any).MonacoEnvironment={getWorker:(_:unknown,label:string)=>label==='typescript'||label==='javascript'?new TsWorker():new EditorWorker()};
loader.config({monaco});
export function CodeEditor({id,student,language,starter,onCode,onRun,onSubmit}:{id:string;student:string;language:string;starter:string;onCode:(s:string)=>void;onRun:()=>void;onSubmit:()=>void}){
 const key='nexvora-code:'+student+':'+id+':'+language;
 const [code,setCode]=useState(''),[loaded,setLoaded]=useState(false),[notice,setNotice]=useState('Loading draft…'),[font,setFont]=useState(14),[full,setFull]=useState(false);
 const pending=useRef<any>(null);
 const editor=useRef<monaco.editor.IStandaloneCodeEditor|null>(null),timer=useRef<ReturnType<typeof setTimeout>|null>(null),actions=useRef({onRun,onSubmit});actions.current={onRun,onSubmit};
 useEffect(()=>{let active=true;const abort=new AbortController();setLoaded(false);onCode('');let local:any=null;try{local=JSON.parse(localStorage.getItem(key)||'null');}catch{}codingApi('/draft?problemId='+encodeURIComponent(id)+'&language='+language,undefined,undefined,abort.signal).then(remote=>{if(!active)return;const chosen=local&&(!remote.code||local.clientUpdatedAt>(remote.clientUpdatedAt||0))?local:remote;const text=chosen.code??starter;setCode(text);onCode(text);setFont(chosen.fontSize||14);setLoaded(true);setNotice(local&&chosen===local?'Draft restored from this device':'Draft ready');}).catch(e=>{if(active){setCode(local?.code??starter);onCode(local?.code??starter);setLoaded(true);setNotice('Server draft unavailable; local recovery active. '+e.message);}});return()=>{active=false;abort.abort();if(timer.current)clearTimeout(timer.current);if(pending.current){void codingApi('/draft',pending.current,'PUT').catch(()=>{});pending.current=null;}};},[key]);
 useEffect(()=>{const close=(e:KeyboardEvent)=>{if(e.key==='Escape')setFull(false);};window.addEventListener('keydown',close);return()=>window.removeEventListener('keydown',close);},[]);
 function change(text:string,size=font){setCode(text);onCode(text);const body={problemId:id,language,code:text,fontSize:size,clientUpdatedAt:Date.now()};pending.current=body;try{localStorage.setItem(key,JSON.stringify(body));setNotice('Saved on this device; syncing…');}catch{setNotice('Local storage unavailable; syncing to server…');}if(timer.current)clearTimeout(timer.current);timer.current=setTimeout(()=>{codingApi('/draft',body,'PUT').then(()=>setNotice('Draft saved')).catch(e=>setNotice(e.message)).finally(()=>{if(pending.current===body)pending.current=null;});},600);}
 const mount:OnMount=(ed,m)=>{editor.current=ed;ed.addCommand(m.KeyMod.CtrlCmd|m.KeyCode.Enter,()=>actions.current.onRun());ed.addCommand(m.KeyMod.CtrlCmd|m.KeyMod.Shift|m.KeyCode.Enter,()=>actions.current.onSubmit());};
 async function format(){const action=editor.current?.getAction('editor.action.formatDocument');if(action?.isSupported()){await action.run();setNotice('Code formatted');}else{change(code.split('\n').map(l=>l.replace(/\t/g,'    ').trimEnd()).join('\n'));setNotice('Whitespace normalized. A full formatter is not installed for this language.');}}
 return <div className={'coding-editor '+(full?'coding-editor-full':'')}><div className="coding-toolbar"><span>{language==='mission-script'?'Mission Script (Python-like)':language} editor</span><label>Size <select aria-label="Editor font size" value={font} onChange={e=>{const size=Number(e.target.value);setFont(size);change(code,size);}}>{[12,14,16,18,20,24].map(n=><option key={n}>{n}</option>)}</select></label><button onClick={()=>void format()}>Format</button><button onClick={()=>void navigator.clipboard.writeText(code).then(()=>setNotice('Code copied')).catch(()=>setNotice('Clipboard unavailable'))}>Copy code</button><button onClick={()=>{if(confirm('Reset code to the starter?'))change(starter);}}>Reset code</button><button onClick={()=>setFull(!full)}>{full?'Exit fullscreen':'Fullscreen'}</button></div><Editor height={full?'calc(100dvh - 110px)':'400px'} language={language==='mission-script'?'python':language==='c'?'cpp':language} theme="vs-dark" value={code} onChange={v=>loaded&&change(v||'')} onMount={mount} options={{editContext:false,fontSize:font,readOnly:!loaded,minimap:{enabled:false},automaticLayout:true,scrollBeyondLastLine:false,tabSize:4,ariaLabel:'Coding editor',wordWrap:'off',accessibilitySupport:'on'}}/><p className="coding-editor-status" role="status">{notice} · Ctrl/Cmd+Enter: Run · Ctrl/Cmd+Shift+Enter: Submit</p></div>;
}
