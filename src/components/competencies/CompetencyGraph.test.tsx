// @vitest-environment jsdom
import {afterEach,it,expect,vi} from 'vitest';
import {render,screen,fireEvent,cleanup,waitFor} from '@testing-library/react';
import {useState} from 'react';
import {AppStateContext} from '../../lib/state/app-context';
import type {AppStateContextType} from '../../lib/state/app-state';
import {CompetencyGraph} from './CompetencyGraph';
import {layoutSkills} from './graph-layout';
vi.mock('./SkillDetailDrawer',()=>({SkillDetailDrawer:({skillId,onClose}:any)=><div role="dialog">Inspector {skillId}<button onClick={onClose}>Close inspector</button></div>}));
vi.mock('./graph-layout',async(importOriginal)=>{const actual=await importOriginal<typeof import('./graph-layout')>();return {...actual,layoutSkills:vi.fn(async()=>({cards:[],edges:[],width:400,height:300}))};});
afterEach(cleanup);
const go=vi.fn();
function Harness({initialMode='current'}:{initialMode?:'before'|'current'}={}){
 const [selectedSkillId,setSelectedSkillId]=useState<string|null>(null);const [graphComparisonMode,setGraphComparisonMode]=useState<'before'|'current'>(initialMode);
 const nodes=[{id:'foundation',name:'Linear Algebra',domain:'Math & Foundations',state:'Verified',mastery:90,confidence:90,evidenceCount:2,prerequisites:[],remainingGap:'',recommendedAction:'Continue',careerImportance:'High'},{id:'python',name:'Python',domain:'Core Programming',state:'Prerequisite Gap',mastery:20,confidence:30,evidenceCount:1,prerequisites:['foundation'],remainingGap:'Needs proof',recommendedAction:'Assess Python',careerImportance:'Critical'}];
 const value={competencyNodes:nodes,initialBaselineNodes:nodes.map(n=>({...n,mastery:0})),selectedSkillId,setSelectedSkillId,graphComparisonMode,setGraphComparisonMode,targetCareer:{title:'AI Engineer',currentReadiness:25,requiredCompetencies:[{skillId:'python',requiredMastery:85}]},mission:{skillId:'python',reason:'Python needs evidence',tab:'assessments'},roadmap:[],setActiveTab:go} as unknown as AppStateContextType;
 return <AppStateContext.Provider value={value}><CompetencyGraph/></AppStateContext.Provider>;
}
it('defaults to collapsed domains, expands relevant prerequisites and collapses again',async()=>{
 render(<Harness/>);expect(screen.getByText('Choose a domain to explore')).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:'Expand Relevant Path'}));
 await waitFor(()=>expect(screen.getByLabelText('Responsive competency list')).toBeTruthy());expect(screen.getByText('Requires: Linear Algebra')).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:'Collapse All'}));expect(screen.getByText('Choose a domain to explore')).toBeTruthy();
});
it('search selects a skill, inspector opens, filters and reset operate on live nodes',async()=>{
 render(<Harness/>);fireEvent.change(screen.getByRole('textbox',{name:'Search competencies'}),{target:{value:'Python'}});fireEvent.keyDown(screen.getByRole('textbox',{name:'Search competencies'}),{key:'Enter'});
 const card=await screen.findByRole('button',{name:/Python 20%/});fireEvent.click(card);expect(screen.getByRole('dialog').textContent).toContain('python');
 fireEvent.click(screen.getByRole('button',{name:'Close inspector'}));fireEvent.change(screen.getByRole('combobox',{name:'State filter'}),{target:{value:'Estimated'}});expect(screen.getByText('No skills match these filters')).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:'Reset View'}));expect(screen.getByText('Choose a domain to explore')).toBeTruthy();
});
it('preserves baseline comparison and Learn Next navigation',()=>{
 render(<Harness/>);fireEvent.click(screen.getByRole('tab',{name:'Before vs Current'}));fireEvent.click(screen.getByRole('button',{name:'Before Assessment'}));
 expect(screen.getByText('0% to 90%')).toBeTruthy();expect(screen.getByText('0% to 20%')).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:'Learn Next'}));expect(go).toHaveBeenCalledWith('assessments');
});
it('captures Ctrl-wheel zoom and clears the requirement explanation on reset',async()=>{
 render(<Harness/>);
 fireEvent.click(screen.getByRole('button',{name:'Expand Relevant Path'}));
 await waitFor(()=>expect(screen.queryByRole('status')).toBeNull());
 const map=screen.getByLabelText('Interactive prerequisite map');
 const wheel=new WheelEvent('wheel',{ctrlKey:true,deltaY:-100,bubbles:true,cancelable:true});
 fireEvent(map,wheel);expect(wheel.defaultPrevented).toBe(true);
 expect(screen.getByText('108%')).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:'Why is this required?'}));
 expect(screen.getByLabelText('Career requirement explanation')).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:'Reset View'}));
 expect(screen.queryByLabelText('Career requirement explanation')).toBeNull();
});
it('collapses a searched skill and collapses one domain from All Skills',async()=>{
 render(<Harness/>);
 fireEvent.change(screen.getByRole('textbox',{name:'Search competencies'}),{target:{value:'Python'}});
 fireEvent.keyDown(screen.getByRole('textbox',{name:'Search competencies'}),{key:'Enter'});
 expect(await screen.findByRole('button',{name:/Python 20%/})).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:'Collapse Programming'}));
 expect(screen.queryByRole('button',{name:/Python 20%/})).toBeNull();
 fireEvent.click(screen.getByRole('tab',{name:'All Skills'}));
 fireEvent.click(screen.getByRole('button',{name:'Collapse Programming'}));
 expect(screen.queryByRole('button',{name:/Python 20%/})).toBeNull();
 expect(screen.getByRole('button',{name:/Linear Algebra 90%/})).toBeTruthy();
});
it('returns to current values when expanding a career path from the baseline',async()=>{
 render(<Harness/>);
 fireEvent.click(screen.getByRole('tab',{name:'Before vs Current'}));
 fireEvent.click(screen.getByRole('button',{name:'Before Assessment'}));
 fireEvent.click(screen.getByRole('button',{name:'Expand Relevant Path'}));
 expect(await screen.findByRole('button',{name:/Python 20%/})).toBeTruthy();
 expect(screen.queryByRole('button',{name:/Python 0%/})).toBeNull();
});
it('starts Career Path with current values even when shared comparison mode was left on before',async()=>{
 render(<Harness initialMode="before"/>);
 fireEvent.click(screen.getByRole('button',{name:'Expand Programming'}));
 expect(await screen.findByRole('button',{name:/Python 20%/})).toBeTruthy();
 expect(screen.queryByRole('button',{name:/Python 0%/})).toBeNull();
});
it('keeps skills accessible in the list when auto-layout fails',async()=>{
 vi.mocked(layoutSkills).mockRejectedValueOnce(new Error('Layout failed'));
 render(<Harness/>);
 fireEvent.click(screen.getByRole('button',{name:'Expand Relevant Path'}));
 expect((await screen.findByRole('alert')).textContent).toContain('Use the skill list');
 expect(screen.getByLabelText('Responsive competency list').className).not.toContain('lg:hidden');
 fireEvent.click(screen.getByRole('button',{name:/Python 20%/}));
 expect(screen.getByRole('dialog').textContent).toContain('python');
});
