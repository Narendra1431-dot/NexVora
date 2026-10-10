import {Undo2,Redo2} from 'lucide-react';
import {useEditHistory,useHistoryStatus} from '../../lib/state/edit-history';
export function UndoRedoControls(){
 const history=useEditHistory(),state=useHistoryStatus();
 return <div className="relative flex shrink-0 items-center rounded-lg border border-slate-200 bg-white p-0.5" role="group" aria-label="Edit history">
  {(['undo','redo'] as const).map(direction=>{const undo=direction==='undo',Icon=undo?Undo2:Redo2,label=undo?'Undo':'Redo',detail=undo?state.undoLabel:state.redoLabel,available=undo?state.canUndo:state.canRedo;
   return <button key={direction} type="button" aria-label={label} aria-keyshortcuts={undo?'Control+Z Meta+Z':'Control+Shift+Z Meta+Shift+Z Control+Y Meta+Y'} title={`${label}${detail?': '+detail:''} (${undo?'Ctrl/Cmd + Z':'Ctrl/Cmd + Shift + Z'})`} disabled={!available||state.busy} onClick={()=>void history?.run(direction)} className="rounded-md p-1.5 text-slate-600 hover:bg-teal-50 hover:text-teal-800 disabled:opacity-35 disabled:cursor-not-allowed focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-600"><Icon aria-hidden="true" className="h-4 w-4"/></button>;
  })}
  {state.error&&<p role="alert" className="absolute right-0 top-full z-50 mt-2 w-64 rounded-xl border border-amber-200 bg-white p-3 text-xs text-amber-900 shadow-lg">{state.error}</p>}
  <span className="sr-only" role="status">{state.busy?'Restoring change...':''}</span>
 </div>;
}
