// @vitest-environment jsdom
import {useState} from 'react';
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {AppStateContext} from '../../lib/state/app-context';
import type {AppStateContextType} from '../../lib/state/app-state';
import {TargetLearningHub,type Hub} from './TargetLearningHub';
const video={id:'rfscVS0vtbw',title:'Python Course',channel:'freeCodeCamp.org',url:'https://www.youtube.com/watch?v=rfscVS0vtbw',thumbnail:'https://i.ytimg.com/vi/rfscVS0vtbw/hqdefault.jpg',views:123,durationSeconds:600,language:'en',level:'Beginner',lastVerifiedAt:'2026-09-30',source:'YouTube',relevance:1};
const topic={id:'python',name:'Python',domain:'Programming',concepts:['Functions'],prerequisiteNames:[],status:'Recommended Next',mastery:0,target:85,difficulty:'Beginner',reason:'Close this gap.',notesReady:true,wordCount:2000,videos:[video],textbooks:[{title:'Fluent Python',author:'Luciano Ramalho'}],referenceUrl:'https://docs.python.org/3/',assessments:[{id:'python-test',title:'Python Assessment'}]};
const fixture=(id:string):Hub=>({career:{id,title:id==='ai'?'AI Engineer':'Backend Developer',description:'Target description'},readiness:20,topics:[{...topic,id:id+'-python'},...(id==='ai'?[{...topic,id:'linear',name:'Linear Algebra'}]:[])],notesReady:true,missingNotes:[],coverage:{requirements:1,totalTopics:id==='ai'?2:1,readyTopics:id==='ai'?2:1},resourceIds:[id+'-course'],videoPolicy:'Curated English videos'});
const coverage=vi.fn(),navigate=vi.fn(),select=vi.fn();
function setup(fetcher:(url:RequestInfo|URL,init?:RequestInit)=>Promise<Response>){
 vi.stubGlobal('fetch',vi.fn(fetcher));
 function Wrapper(){const [id,setId]=useState('ai');const context={targetCareer:{id,title:fixture(id).career.title},careers:[{id:'ai',title:'AI Engineer'},{id:'backend',title:'Backend Developer'}],competencyNodes:[],resources:[],setTargetCareer:async(value:string)=>{setId(value);return true;},setActiveTab:navigate,setCatalogSelection:select} as unknown as AppStateContextType;return <AppStateContext.Provider value={context}><TargetLearningHub onCoverage={coverage}/></AppStateContext.Provider>;}
 return render(<Wrapper/>);
}
afterEach(()=>{cleanup();vi.unstubAllGlobals();vi.clearAllMocks();});
it('changes all materials with the objective, de-duplicates videos, filters topics and navigates to assessments',async()=>{
 setup(async url=>new Response(JSON.stringify(fixture(String(url).endsWith('backend')?'backend':'ai'))));
 await screen.findByText('AI Engineer Overview');expect(screen.getAllByRole('link',{name:'Watch on YouTube'})).toHaveLength(1);
 expect(coverage).toHaveBeenLastCalledWith(['ai-course']);
 fireEvent.change(screen.getByLabelText('Focus topic'),{target:{value:'linear'}});expect(screen.getAllByRole('article',{name:'Linear Algebra'})).toHaveLength(1);expect(screen.queryByRole('article',{name:'Python'})).toBeNull();
 fireEvent.click(screen.getByRole('button',{name:'Python Assessment'}));expect(select).toHaveBeenCalledWith({tab:'assessments',id:'python-test'});expect(navigate).toHaveBeenCalledWith('assessments');
 fireEvent.change(screen.getByLabelText('Target Objective'),{target:{value:'backend'}});
 await screen.findByText('Backend Developer Overview');expect(screen.queryByText('AI Engineer Overview')).toBeNull();expect(screen.queryByRole('article',{name:'Linear Algebra'})).toBeNull();expect(coverage).toHaveBeenLastCalledWith(['backend-course']);
 expect(screen.getByRole('link',{name:'Watch on YouTube'}).getAttribute('href')).toBe(video.url);
});
it('downloads full and topic PDFs and opens the same notes in an accessible reader',async()=>{
 const note={introduction:'Introduction',foundations:'Foundations content',concepts:[],examples:[],flow:['Process step'],interview:[],practice:[{question:'Try this',answer:'Solution'}],summary:'Summary',source:'NexVora original notes'};
 setup(async url=>String(url).includes('/pdf')?new Response('%PDF-fixture'):String(url).includes('/notes')?new Response(JSON.stringify({chapters:[{id:'python',name:'Python',notes:note,prerequisiteNames:[],referenceUrl:'https://docs.python.org/3/'}]})):new Response(JSON.stringify(fixture('ai'))));
 vi.stubGlobal('URL',class extends URL{static createObjectURL=vi.fn(()=> 'blob:notes');static revokeObjectURL=vi.fn();});const click=vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(()=>{});
 await screen.findByText('AI Engineer Overview');fireEvent.click(screen.getByRole('button',{name:'Download Full PDF'}));await waitFor(()=>expect(click).toHaveBeenCalledTimes(1));
 fireEvent.click(screen.getAllByRole('button',{name:'Topic PDF'})[0]);await waitFor(()=>expect(click).toHaveBeenCalledTimes(2));
 expect(vi.mocked(fetch).mock.calls.some(([u])=>String(u).includes('topic_id=ai-python'))).toBe(true);
 fireEvent.click(screen.getByRole('button',{name:'View Notes'}));expect(await screen.findByText('Foundations content')).toBeTruthy();fireEvent.click(screen.getByRole('button',{name:'Close Notes'}));expect(screen.queryByRole('dialog')).toBeNull();click.mockRestore();
});
it('rejects stale responses after changing career and handles failed loads',async()=>{
 let resolveOld:(r:Response)=>void=()=>{};
 setup(async url=>String(url).endsWith('/ai')?new Promise<Response>(resolve=>{resolveOld=resolve;}):new Response(JSON.stringify(fixture('backend'))));
 fireEvent.change(screen.getByLabelText('Target Objective'),{target:{value:'backend'}});await screen.findByText('Backend Developer Overview');
 resolveOld(new Response(JSON.stringify(fixture('ai'))));await waitFor(()=>expect(coverage).toHaveBeenLastCalledWith(['backend-course']));expect(screen.queryByText('AI Engineer Overview')).toBeNull();
});
it('does not offer an incomplete PDF as complete',async()=>{
 setup(async()=>new Response(JSON.stringify({...fixture('ai'),notesReady:false,missingNotes:['Python']})));
 await screen.findByText(/Complete PDF unavailable/);expect((screen.getByRole('button',{name:'Download Full PDF'}) as HTMLButtonElement).disabled).toBe(true);
});
