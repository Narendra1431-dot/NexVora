// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {createEditHistory,EditHistoryProvider,useUndoableState} from './edit-history';
import {UndoRedoControls} from '../../components/layout/UndoRedoControls';
afterEach(()=>{cleanup();vi.restoreAllMocks();});
it('replays commands, merges typing and discards redo after a new edit',async()=>{
 const history=createEditHistory();let value='';
 for(const next of ['a','ab','abc']){const before=value;value=next;history.add({label:'Name',mergeKey:'name',undo:()=>{value=before;},redo:()=>{value=next;}});}
 await history.run('undo');expect(value).toBe('');expect(history.getSnapshot().canUndo).toBe(false);
 await history.run('redo');expect(value).toBe('abc');
 await history.run('undo');history.add({label:'Different edit',undo:()=>{},redo:()=>{}});expect(history.getSnapshot().canRedo).toBe(false);
});
it('keeps failed operations retryable and blocks double replay while saving',async()=>{
 const history=createEditHistory();const undo=vi.fn().mockRejectedValueOnce(new Error('Save failed')).mockResolvedValue(undefined);
 history.add({label:'Saved profile',undo,redo:()=>{}});await history.run('undo');expect(history.getSnapshot()).toMatchObject({canUndo:true,canRedo:false,error:'Save failed'});
 await history.run('undo');expect(history.getSnapshot()).toMatchObject({canUndo:false,canRedo:true,error:''});
 let done!:()=>void;const slow=vi.fn(()=>new Promise<void>(resolve=>{done=resolve;}));history.add({label:'Career',undo:slow,redo:()=>{}});
 const pending=history.run('undo');await history.run('undo');expect(slow).toHaveBeenCalledTimes(1);done();await pending;
});
it('clears sensitive session history and removes closed-editor commands',async()=>{
 const history=createEditHistory();const undo=vi.fn();history.add({label:'Draft',scope:'dialog',undo,redo:()=>{}});history.removeScope('dialog');expect(history.getSnapshot().canUndo).toBe(false);
 history.add({label:'Profile',undo,redo:()=>{}});history.clear();await history.run('undo');expect(undo).not.toHaveBeenCalled();
});
function Draft({open=true}:{open?:boolean}){
 const [text,setText,reset]=useUndoableState('Original','Resume text',open);
 return open?<><textarea aria-label="Resume draft" data-undo="true" value={text} onChange={e=>setText(e.target.value)}/><input aria-label="Native field"/><button onClick={()=>reset('Imported')}>Import</button></>:null;
}
it('supports top-bar buttons, paste-sized changes, keyboard undo/redo and native input isolation',async()=>{
 render(<EditHistoryProvider><UndoRedoControls/><Draft/></EditHistoryProvider>);
 const undo=screen.getByRole('button',{name:'Undo'}),redo=screen.getByRole('button',{name:'Redo'}),field=screen.getByRole('textbox',{name:'Resume draft'}) as HTMLTextAreaElement;
 expect((undo as HTMLButtonElement).disabled).toBe(true);
 fireEvent.change(field,{target:{value:'Pasted resume with project details'}});fireEvent.click(undo);
 await waitFor(()=>expect(field.value).toBe('Original'));fireEvent.click(redo);await waitFor(()=>expect(field.value).toBe('Pasted resume with project details'));
 fireEvent.keyDown(screen.getByRole('textbox',{name:'Native field'}),{key:'z',ctrlKey:true});expect(field.value).toBe('Pasted resume with project details');
 fireEvent.keyDown(field,{key:'z',metaKey:true});await waitFor(()=>expect(field.value).toBe('Original'));
 fireEvent.keyDown(field,{key:'Z',metaKey:true,shiftKey:true});await waitFor(()=>expect(field.value).toBe('Pasted resume with project details'));
 fireEvent.keyDown(field,{key:'z',ctrlKey:true});await waitFor(()=>expect(field.value).toBe('Original'));
 fireEvent.keyDown(field,{key:'y',ctrlKey:true});await waitFor(()=>expect(field.value).toBe('Pasted resume with project details'));
 fireEvent.click(screen.getByRole('button',{name:'Import'}));expect(field.value).toBe('Imported');expect((undo as HTMLButtonElement).disabled).toBe(true);
});
it('disables draft history when its dialog closes',()=>{
 const view=render(<EditHistoryProvider><UndoRedoControls/><Draft/></EditHistoryProvider>);
 fireEvent.change(screen.getByRole('textbox',{name:'Resume draft'}),{target:{value:'New'}});
 view.rerender(<EditHistoryProvider><UndoRedoControls/><Draft open={false}/></EditHistoryProvider>);
 expect((screen.getByRole('button',{name:'Undo'}) as HTMLButtonElement).disabled).toBe(true);
});
