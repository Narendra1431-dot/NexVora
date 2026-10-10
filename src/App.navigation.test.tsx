// @vitest-environment jsdom
import {afterEach,beforeEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import App from './App';
import {layoutSkills} from './components/competencies/graph-layout';
import * as seed from './lib/mock-data/seed-data';

const realFetch=globalThis.fetch;
const routes=['dashboard','profile','competencies','careers','roadmap','resources','assessments','projects','resume','certificates','mentor','coding','agent-hub'];
const fixture={profile:seed.INITIAL_STUDENT,competencies:seed.INITIAL_COMPETENCY_NODES,baselineNodes:seed.INITIAL_COMPETENCY_NODES,evidence:seed.INITIAL_EVIDENCE_ITEMS,careers:seed.INITIAL_CAREERS,milestones:seed.INITIAL_ROADMAP_MILESTONES,resources:seed.INITIAL_RESOURCES,assessments:seed.INITIAL_ASSESSMENTS,projects:seed.INITIAL_PROJECTS,resume:seed.INITIAL_RESUME_ANALYSIS,events:seed.INITIAL_ACTIVITIES,notifications:seed.INITIAL_NOTIFICATIONS,concepts:[],relationships:{nodes:[],edges:[]},mission:{title:'Assess Python',reason:'Evidence needed',description:'Assess your next skill',tab:'assessments',estimatedEffort:'20 minutes'},intelligence:{learningRisk:{level:'Low',score:0.2,modelVersion:'test'},evidenceStrength:[],limitation:'Test advisory',advisoryOnly:true,trainingData:'test'}};
beforeEach(()=>{
 sessionStorage.setItem('plcip_token','test-session');
 vi.stubGlobal('ResizeObserver',class{observe(){} unobserve(){} disconnect(){}});
});
afterEach(()=>{cleanup();sessionStorage.clear();vi.restoreAllMocks();vi.unstubAllGlobals();});

async function verifyNavigation(snapshot:unknown){
  const errors=vi.spyOn(console,'error');
  vi.stubGlobal('fetch',vi.fn(async(input:RequestInfo|URL)=>{
   const url=String(input);
   if(url.endsWith('/jobs')||url.endsWith('/documents/library'))return new Response('[]');
   if(url.endsWith('/coding/problems')||url.endsWith('/coding/games'))return new Response('[]');
   if(url.endsWith('/coding/progress'))return new Response(JSON.stringify({practice:[],games:[]}));
   if(url.endsWith('/coding/stats'))return new Response(JSON.stringify({rank:1,overallXP:0,codingXP:0,problemsSolved:0,gamesCompleted:0,currentStreak:0,successRate:0,recentActivity:[],achievements:[]}));
   if(url.endsWith('/certificates'))return new Response(JSON.stringify({certificates:[],courses:[],payment:{mode:'DEMO',amount:19900,currency:'INR',notice:'DEMO payment: no money is charged.'}}));
   if(url.includes('/learning-hub/'))return new Response(JSON.stringify({career:{id:fixture.profile.targetCareerId,title:'Target objective',description:'Current objective'},readiness:0,topics:[],notesReady:false,missingNotes:[],coverage:{requirements:0,totalTopics:0,readyTopics:0},resourceIds:[],videoPolicy:'Verified videos'}));
   if(url.endsWith('/agent/runs'))return new Response('[]');
   if(url.endsWith('/agent/history')||url.endsWith('/agent/activity')||url.endsWith('/agent/approvals')||url.endsWith('/agent/audit'))return new Response('[]');
   if(url.endsWith('/agent/recommendations'))return new Response(JSON.stringify({recommendation:null}));
   if(url.endsWith('/state'))return new Response(JSON.stringify(snapshot));
   if(url.endsWith('/mentor/status'))return new Response(JSON.stringify({provider:'test',status:'available',available:true,configuredModel:'test'}));
   if(url.endsWith('/reviews/pending'))return new Response('[]');
   throw new Error('Unexpected request: '+url);
  }));
  const first=render(<App/>);
  await waitFor(()=>expect(document.querySelector('#nav-dashboard')).toBeTruthy(),{timeout:30000});
  for(const route of routes){
   fireEvent.click(document.querySelector('#nav-'+route)!);
   await waitFor(()=>{
    expect(screen.queryByText('Loading workspace...')).toBeNull();
    expect(document.querySelector('main')!.textContent!.trim().length).toBeGreaterThan(40);
   },{timeout:30000});
   expect(document.querySelector('#nav-'+route)!.className).toContain('bg-teal-50');
  }
  fireEvent.click(document.querySelector('#nav-dashboard')!);
  await waitFor(()=>expect(screen.queryByText('Loading workspace...')).toBeNull(),{timeout:30000});
  expect(document.querySelector('main')!.textContent).toContain('Learning risk advisory');
  first.unmount();
  render(<App/>);
  await waitFor(()=>expect(document.querySelector('main')?.textContent).toContain('Learning risk advisory'),{timeout:30000});
  expect(errors.mock.calls).toEqual([]);
 }
it('opens every real sidebar page, returns to Dashboard, and restores the workspace after remount',async()=>{await verifyNavigation(fixture);},60000);
it.skipIf(process.env.LIVE_API_TEST!=='1')('renders all pages using the current MongoDB demo snapshot',async()=>{
 const auth=await realFetch('http://127.0.0.1:8000/api/v1/auth/demo',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'});
 expect(auth.ok).toBe(true);
 const {token}=await auth.json();
 const response=await realFetch('http://127.0.0.1:8000/api/v1/state',{headers:{Authorization:`Bearer ${token}`}});
 expect(response.ok).toBe(true);
 const snapshot=await response.json();
 await verifyNavigation(snapshot);
 const career=snapshot.careers.find((c:any)=>c.id===snapshot.profile.targetCareerId);
 const map=await layoutSkills(snapshot.competencies,new Set(career.requiredCompetencies.map((r:any)=>r.skillId)),career.title);
 expect(map.cards).toHaveLength(snapshot.competencies.length+1);
 for(let i=0;i<map.cards.length;i++)for(let j=i+1;j<map.cards.length;j++){
  const a=map.cards[i],b=map.cards[j];
  expect(a.x+a.width<=b.x||b.x+b.width<=a.x||a.y+a.height<=b.y||b.y+b.height<=a.y).toBe(true);
 }
},60000);
