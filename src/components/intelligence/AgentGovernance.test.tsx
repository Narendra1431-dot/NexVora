// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {AgentGovernance} from './AgentGovernance';
import {intelligenceApi} from './api';
const {refresh}=vi.hoisted(()=>({refresh:vi.fn()}));
vi.mock('./api',()=>({intelligenceApi:vi.fn()}));
vi.mock('../../lib/state/app-state',()=>({useAppState:()=>({refreshWorkspace:refresh})}));
afterEach(()=>{cleanup();vi.clearAllMocks();});
for(const decision of ['approve','reject'] as const)it(decision+' pauses until an explicit decision and refreshes only completed actions',async()=>{
 const row={id:'action-qa',toolName:'workspace.write',status:'pending_approval',reason:'Save reviewed notes',preview:{fileName:'notes.txt',content:'Study SQL'},createdAt:'2026-10-05T12:00:00Z'};
 vi.mocked(intelligenceApi).mockImplementation(async(path,body)=>{
   if(path==='/agent/approvals')return [row];
   if(path==='/agent/audit')return [];
   return {...row,status:decision==='approve'?'completed':'rejected'};
 });
 render(<AgentGovernance/>);
 await screen.findByRole('button',{name:'Approve'});
 expect(vi.mocked(intelligenceApi).mock.calls.every(c=>c[1]===undefined)).toBe(true);
 fireEvent.click(screen.getByRole('button',{name:decision==='approve'?'Approve':'Reject'}));
 await waitFor(()=>expect(screen.queryByRole('button',{name:'Approve'})).toBeNull());
 expect(intelligenceApi).toHaveBeenCalledWith('/agent/approvals/action-qa',{decision});
 expect(refresh).toHaveBeenCalledTimes(decision==='approve'?1:0);
});
