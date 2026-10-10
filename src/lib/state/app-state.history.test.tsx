// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {AppStateProvider,useAppState} from './app-state';
import {EditHistoryProvider} from './edit-history';
import {UndoRedoControls} from '../../components/layout/UndoRedoControls';
import * as seed from '../mock-data/seed-data';
afterEach(()=>{cleanup();sessionStorage.clear();vi.unstubAllGlobals();});
function Editor(){const {student,saveProfile,setTargetCareer}=useAppState();return <><p>{student.name}</p><p>{student.targetCareerId}</p><UndoRedoControls/><button onClick={()=>saveProfile({name:'Edited Student'})}>Save profile</button><button onClick={()=>setTargetCareer('career-backend-engineer')}>Switch career</button></>;}
function setup(){
 sessionStorage.setItem('plcip_token','history-test');
 const snapshot={profile:{...seed.INITIAL_STUDENT},competencies:seed.INITIAL_COMPETENCY_NODES,baselineNodes:[],evidence:[],careers:seed.INITIAL_CAREERS,milestones:[],resources:[],assessments:[],projects:[],resume:{},events:[],notifications:[]};
 const fetch=vi.fn(async(input:RequestInfo|URL,init?:RequestInit)=>{
  const url=String(input);
  if(url.endsWith('/agent/history'))return new Response('[]');
  if(url.endsWith('/profile'))Object.assign(snapshot.profile,JSON.parse(String(init?.body)));
  if(url.endsWith('/career/target'))snapshot.profile.targetCareerId=JSON.parse(String(init?.body)).careerId;
  return new Response(JSON.stringify(url.endsWith('/state')?snapshot:{}));
 });vi.stubGlobal('fetch',fetch);
 render(<EditHistoryProvider><AppStateProvider><Editor/></AppStateProvider></EditHistoryProvider>);return {snapshot,fetch};
}
it('undoes and redoes persisted profile fields through the API',async()=>{
 const {snapshot,fetch}=setup();const before=snapshot.profile.name;
 fireEvent.click(await screen.findByRole('button',{name:'Save profile'}));await screen.findByText('Edited Student');
 await waitFor(()=>expect((screen.getByRole('button',{name:'Undo'}) as HTMLButtonElement).disabled).toBe(false));
 fireEvent.click(screen.getByRole('button',{name:'Undo'}));await screen.findByText(before);
 fireEvent.click(screen.getByRole('button',{name:'Redo'}));await screen.findByText('Edited Student');
 expect(fetch.mock.calls.filter(([url])=>String(url).endsWith('/profile'))).toHaveLength(3);
});
it('reverts career selection through the domain endpoint and refuses to overwrite newer profile data',async()=>{
 const {snapshot}=setup();const original=snapshot.profile.targetCareerId;
 fireEvent.click(await screen.findByRole('button',{name:'Switch career'}));await screen.findByText('career-backend-engineer');
 await waitFor(()=>expect((screen.getByRole('button',{name:'Undo'}) as HTMLButtonElement).disabled).toBe(false));fireEvent.click(screen.getByRole('button',{name:'Undo'}));await screen.findByText(original);
 fireEvent.click(screen.getByRole('button',{name:'Save profile'}));await screen.findByText('Edited Student');snapshot.profile.name='Changed on another device';
 fireEvent.click(screen.getByRole('button',{name:'Undo'}));await screen.findByRole('alert');expect(snapshot.profile.name).toBe('Changed on another device');
});
