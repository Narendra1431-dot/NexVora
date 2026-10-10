// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {AppStateContext} from '../../lib/state/app-context';
import type {AppStateContextType} from '../../lib/state/app-state';
import {CareerIntelligencePanel} from './CareerIntelligencePanel';
afterEach(()=>{cleanup();vi.unstubAllGlobals();});
const recommendation={title:'Practice Python',reason:'Missing scored evidence',currentMastery:12,targetMastery:70,currentReadiness:9,blocks:['Machine Learning'],actions:[{label:'Learn Now',tab:'resources',skillId:'python',id:'course-python'}],evidenceUsed:[],missingEvidence:true,readinessImpact:'Requires verified evidence'};
function setup(activityOnly=false){
 const value={targetCareer:{id:'ai'},competencyNodes:[],evidenceItems:[],activities:[],mentorMessages:[],setActiveTab:vi.fn(),setSelectedSkillId:vi.fn(),setCatalogSelection:vi.fn()} as unknown as AppStateContextType;
 const view=render(<AppStateContext.Provider value={value}><CareerIntelligencePanel activityOnly={activityOnly}/></AppStateContext.Provider>);return {value,...view};
}
it('opens the recommended resource with the live skill and catalog selection',async()=>{
 vi.stubGlobal('fetch',vi.fn(async(url:string)=>({ok:true,json:async()=>url.endsWith('activity')?[]:{recommendation}})));
 const {value}=setup();fireEvent.click(await screen.findByRole('button',{name:'Learn Now'}));
 expect(value.setSelectedSkillId).toHaveBeenCalledWith('python');expect(value.setCatalogSelection).toHaveBeenCalledWith({tab:'resources',id:'course-python'});expect(value.setActiveTab).toHaveBeenCalledWith('resources');
 expect(screen.getByText(/Mastery 12%/).textContent).toContain('9%');
});
it('recovers from API errors without showing invented recommendations',async()=>{
 const fetch=vi.fn().mockResolvedValueOnce({ok:false}).mockResolvedValue({ok:true,json:async()=>[]});vi.stubGlobal('fetch',fetch);
 setup();await screen.findByRole('button',{name:'Retry'});expect(screen.queryByText('Practice Python')).toBeNull();
 fetch.mockImplementation(async(url:string)=>({ok:true,json:async()=>url.endsWith('activity')?[]:{recommendation}}));fireEvent.click(screen.getByRole('button',{name:'Retry'}));await screen.findByText('Practice Python');
});
it('refreshes activity after a new copilot message',async()=>{
 const fetch=vi.fn(async()=>({ok:true,json:async()=>[]}));vi.stubGlobal('fetch',fetch);
 const {value,rerender}=setup(true);await waitFor(()=>expect(fetch).toHaveBeenCalledTimes(1));
 rerender(<AppStateContext.Provider value={{...value,mentorMessages:[{id:'new'}] as any}}><CareerIntelligencePanel activityOnly/></AppStateContext.Provider>);
 await waitFor(()=>expect(fetch).toHaveBeenCalledTimes(2));
});
