// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {AgentHub} from './AgentHub';
import {intelligenceApi} from './api';
vi.mock('./api',()=>({intelligenceApi:vi.fn()}));
vi.mock('./AgentGovernance',()=>({AgentGovernance:()=> <div>Governed approvals</div>}));
afterEach(()=>{cleanup();vi.restoreAllMocks();vi.unstubAllGlobals();window.history.replaceState({},'','/');});
it('renders recorded execution, uses authenticated SSE and opens actual step output',async()=>{
 const step={id:'profile',stepId:'agt-qa-profile',agentName:'profile',task:'Inspect profile',status:'COMPLETED',dependencyIds:[],durationMs:12,retryCount:0,toolsUsed:['getStudentProfile'],outputSummary:{name:'QA Student'}};
 const run={id:'agt-qa',userRequest:'Analyze my career',status:'COMPLETED',createdAt:'2026-10-08T00:00:00Z',stateVersionBefore:4,stateVersionAfter:4,durationMs:150,steps:[step],proof:{agentsExecuted:1,toolCalls:1,sourcesRetrieved:0,approvals:0},finalResultSummary:'Review your next skill.'};
 vi.mocked(intelligenceApi).mockImplementation(async(path)=>path==='/agent/runs/run'?[run]:run);
 const replay=Array.from({length:80},(_,i)=>'id: '+i+'\nevent: agent-event\ndata: '+JSON.stringify({eventId:String(i),eventType:'tool.completed',safeMessage:'Tool finished',timestamp:'2026-10-08T00:00:00Z'})+'\n\n').join('');
 const fetchMock=vi.fn(async(_input:RequestInfo|URL,_init?:RequestInit)=>new Response(replay+'event: stream-end\ndata: {}\n\n',{headers:{'Content-Type':'text/event-stream'}}));
 vi.stubGlobal('fetch',fetchMock);sessionStorage.setItem('plcip_token','test-session');
 render(<AgentHub/>);
 fireEvent.click(await screen.findByRole('button',{name:/Analyze my career/}));
 expect(await screen.findByText('Proof of Execution')).toBeTruthy();
 expect(await screen.findByText('Execution history synchronized')).toBeTruthy();
 expect(vi.mocked(intelligenceApi).mock.calls.filter(([path])=>path==='/agent/runs/run/agt-qa').length).toBeLessThanOrEqual(4);
 expect(new URLSearchParams(window.location.search).get('run')).toBe('agt-qa');
 expect(fetchMock.mock.calls[0][0]).toContain('/agent/runs/run/agt-qa/events');
 expect(new Headers(fetchMock.mock.calls[0][1]?.headers).get('Authorization')).toBe('Bearer test-session');
 fireEvent.click(screen.getByRole('button',{name:/profile COMPLETED/}));
 expect(await screen.findByRole('dialog',{name:'Agent step details'})).toBeTruthy();
 expect(screen.getByText(/QA Student/)).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:'Close details'}));
 expect(screen.queryByRole('dialog')).toBeNull();
});
