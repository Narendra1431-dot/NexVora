// @vitest-environment jsdom
import {act,renderHook,cleanup} from '@testing-library/react';
import {afterEach,expect,it,vi} from 'vitest';
import {useVoice} from './useVoice';
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
it('starts only on request, returns transcript for review and handles permission denial',()=>{
 let instance:any;
 class Recognition {start=vi.fn();abort=vi.fn();onresult:any;onerror:any;onend:any;constructor(){instance=this;}}
 vi.stubGlobal('SpeechRecognition',Recognition);
 const transcript=vi.fn();const {result,unmount}=renderHook(()=>useVoice(transcript));
 expect(instance).toBeUndefined();
 act(()=>result.current.listen());expect(instance.start).toHaveBeenCalledOnce();
 act(()=>instance.onresult({results:[[{transcript:'Explain Python'}]]}));
 expect(transcript).toHaveBeenCalledWith('Explain Python');
 act(()=>instance.onerror({error:'not-allowed'}));
 expect(result.current.error).toContain('denied');
 unmount();expect(instance.abort).toHaveBeenCalled();
});
it('reads the same text answer and cancels speech on close',()=>{
 const speak=vi.fn(),cancel=vi.fn();vi.stubGlobal('speechSynthesis',{speak,cancel});
 vi.stubGlobal('SpeechSynthesisUtterance',class {constructor(public text:string){}});
 const {result}=renderHook(()=>useVoice(vi.fn()));
 act(()=>result.current.speak('Your next skill is Python.'));
 expect(speak.mock.calls[0][0].text).toBe('Your next skill is Python.');
 act(()=>result.current.stop());expect(result.current.speaking).toBe(false);expect(cancel).toHaveBeenCalled();
});
