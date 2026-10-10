// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {AppStateContext} from '../../lib/state/app-context';
import type {AppStateContextType} from '../../lib/state/app-state';
import {AiMentor} from './AiMentor';
afterEach(cleanup);
function setup(busy=false){
 const send=vi.fn().mockResolvedValue(false), check=vi.fn().mockResolvedValue(undefined);
 const value={mission:{title:'Practice Python',reason:'Needs evidence'},mentorError:'',mentorBusy:busy,mentorStatus:{provider:'Groq',status:'missing_credentials',available:false,configuredModel:'fixture'},checkMentorStatus:check,student:{name:'Chandu'},targetCareer:{title:'Data Scientist',currentReadiness:19},evidenceItems:[],mentorMessages:[],sendMentorMessage:send,setActiveTab:vi.fn(),setSelectedSkillId:vi.fn()} as unknown as AppStateContextType;
 render(<AppStateContext.Provider value={value}><AiMentor/></AppStateContext.Provider>);return {send,check};
}
it('preserves a failed question for retry and exposes connection check',async()=>{
 const {send,check}=setup();const input=screen.getByRole('textbox',{name:'Message to AI mentor'});
 fireEvent.change(input,{target:{value:'Explain recursion'}});fireEvent.click(screen.getByRole('button',{name:'Send message'}));
 await waitFor(()=>expect((input as HTMLInputElement).value).toBe('Explain recursion'));
 expect(send).toHaveBeenCalledWith('Explain recursion');
 fireEvent.click(screen.getByRole('button',{name:'Check connection'}));await waitFor(()=>expect(check).toHaveBeenCalledWith(true));
});
it('blocks duplicate sends while generating and announces progress',()=>{
 const {send}=setup(true);fireEvent.change(screen.getByRole('textbox',{name:'Message to AI mentor'}),{target:{value:'Hello'}});
 fireEvent.keyDown(screen.getByRole('textbox',{name:'Message to AI mentor'}),{key:'Enter'});
 expect(send).not.toHaveBeenCalled();expect((screen.getByRole('button',{name:'Send message'}) as HTMLButtonElement).disabled).toBe(true);
 expect(screen.getByRole('status').textContent).toContain('Preparing');
});
