import {createContext,useContext,useEffect,useMemo,useRef,useState,useSyncExternalStore,type ReactNode,type SetStateAction} from 'react';

export type HistoryCommand={label:string;scope?:string;mergeKey?:string;undo:()=>void|Promise<void>;redo:()=>void|Promise<void>};
type Entry=HistoryCommand & {at:number};
export function createEditHistory(){
 let past:Entry[]=[],future:Entry[]=[],busy=false,error='',generation=0;
 const listeners=new Set<()=>void>();
 let state={canUndo:false,canRedo:false,undoLabel:'',redoLabel:'',busy:false,error:''};
 const emit=()=>{state={canUndo:past.length>0,canRedo:future.length>0,undoLabel:past.at(-1)?.label||'',redoLabel:future.at(-1)?.label||'',busy,error};listeners.forEach(fn=>fn());};
 const store={
  subscribe:(fn:()=>void)=>{listeners.add(fn);return()=>{listeners.delete(fn);};},getSnapshot:()=>state,
  add:(command:HistoryCommand)=>{if(busy)return;const last=past.at(-1),now=Date.now();
   if(command.mergeKey&&last?.mergeKey===command.mergeKey&&now-last.at<700&&!future.length)past[past.length-1]={...command,undo:last.undo,at:now};
   else past=[...past.slice(-79),{...command,at:now}];future=[];error='';emit();},
  removeScope:(scope:string)=>{past=past.filter(c=>c.scope!==scope);future=future.filter(c=>c.scope!==scope);emit();},
  clear:()=>{generation++;past=[];future=[];error='';emit();},
  run:async(direction:'undo'|'redo')=>{if(busy)return;const entry=(direction==='undo'?past:future).at(-1);if(!entry)return;
   const version=generation;busy=true;error='';emit();
   try{await entry[direction]();if(version!==generation)return;
    // A closed form can remove its commands while an asynchronous action runs.
    if(direction==='undo'&&past.at(-1)===entry){past.pop();future.push(entry);}
    else if(direction==='redo'&&future.at(-1)===entry){future.pop();past.push(entry);}
   }catch(e){error=e instanceof Error?e.message:'Unable to restore this change. Try again.';}
   finally{busy=false;emit();}
  }
 };return store;
}
type HistoryStore=ReturnType<typeof createEditHistory>;
const HistoryContext=createContext<HistoryStore|null>(null);
const empty={canUndo:false,canRedo:false,undoLabel:'',redoLabel:'',busy:false,error:''};
const noopSubscribe=()=>()=>{};
export function useEditHistory(){return useContext(HistoryContext);}
export function useHistoryStatus(){const store=useEditHistory();return useSyncExternalStore(store?.subscribe||noopSubscribe,store?.getSnapshot||(()=>empty));}
export function EditHistoryProvider({children}:{children:ReactNode}){
 const store=useMemo(createEditHistory,[]);
 useEffect(()=>{const key=(e:KeyboardEvent)=>{
  if(e.defaultPrevented||e.isComposing||e.altKey||!(e.ctrlKey||e.metaKey))return;
  const letter=e.key.toLowerCase();if(letter!=='z'&&letter!=='y')return;
  const target=e.target instanceof HTMLElement?e.target:null;
  if(target?.closest('input,textarea,select,[contenteditable="true"]')&&!target.closest('[data-undo="true"]'))return;
  const direction=letter==='y'||e.shiftKey?'redo':'undo';
  const status=store.getSnapshot();
  if(status.busy||status[direction==='undo'?'canUndo':'canRedo']){e.preventDefault();void store.run(direction);}
 };document.addEventListener('keydown',key);return()=>document.removeEventListener('keydown',key);},[store]);
 return <HistoryContext.Provider value={store}>{children}</HistoryContext.Provider>;
}

/** Draft history is disposed when its editor closes. Programmatic resets never become edits. */
export function useUndoableState<T>(initial:T|(()=>T),label:string,active=true){
 const history=useEditHistory();const [value,setValue]=useState(initial);const current=useRef(value);
 const scope=useRef<string>(crypto.randomUUID()).current;
 const apply=(next:T)=>{current.current=next;setValue(next);};
 useEffect(()=>{if(!active)history?.removeScope(scope);return()=>history?.removeScope(scope);},[history,scope,active]);
 const set=(action:SetStateAction<T>)=>{
  if(history?.getSnapshot().busy)return;
  const before=current.current;const next=typeof action==='function'?(action as (old:T)=>T)(before):action;
  if(Object.is(before,next))return;apply(next);
  if(active)history?.add({label,scope,mergeKey:scope,undo:()=>apply(before),redo:()=>apply(next)});
 };
 const reset=(next:T)=>{history?.removeScope(scope);apply(next);};
 return [value,set,reset] as const;
}
