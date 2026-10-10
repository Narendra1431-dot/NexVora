// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {AppStateContext} from '../../lib/state/app-context';
import {BackgroundActivity} from './BackgroundActivity';
import {LearningMaterial} from './LearningMaterial';
afterEach(()=>{cleanup();vi.restoreAllMocks();vi.unstubAllGlobals();});

it('restores jobs, reports a queue outage, and refreshes state on completion',async()=>{
 let status='Queued';const refresh=vi.fn(),toast=vi.fn();
 vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify([{jobId:'job-1',type:'resume_analysis',status,progress:status==='Completed'?100:0,stage:status==='Completed'?'Ready':'Waiting for queue service. Your request is saved.',retryCount:0}]))));
 render(<AppStateContext.Provider value={{refreshWorkspace:refresh,showToast:toast} as any}><BackgroundActivity/></AppStateContext.Provider>);
 await screen.findByText('Waiting for queue service. Your request is saved.');
 fireEvent.click(screen.getByRole('button',{name:/Background activity/}));
 expect(screen.getByRole('button',{name:'Cancel'})).toBeTruthy();
 status='Completed';window.dispatchEvent(new Event('intelligence-job'));
 await waitFor(()=>expect(refresh).toHaveBeenCalledTimes(1));
 expect(toast).toHaveBeenCalled();
 await screen.findByRole('button',{name:'View result'});
 expect(screen.queryByRole('button',{name:'Cancel'})).toBeNull();
});

it('shows honest abstention and retains document source controls',async()=>{
 vi.stubGlobal('fetch',vi.fn(async(input:RequestInfo|URL)=>new Response(JSON.stringify(String(input).endsWith('/documents/library')?[]:{answer:{summary:'Insufficient grounded evidence.',recommendations:[],citations:[]},sources:[],abstained:true}))));
 render(<LearningMaterial/>);
 fireEvent.click(screen.getByText('My course material · grounded questions'));
 fireEvent.change(screen.getByRole('textbox',{name:'Question about learning material'}),{target:{value:'Explain attention'}});
 fireEvent.click(screen.getByRole('button',{name:'Ask with sources'}));
 await screen.findByText('Insufficient grounded evidence.');
 expect(screen.getByRole('combobox',{name:'Learning material source'})).toBeTruthy();
});
