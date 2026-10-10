// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {AppStateContext} from '../../lib/state/app-context';
import type {AppStateContextType} from '../../lib/state/app-state';
import {ResumeIntelligence} from './ResumeIntelligence';
afterEach(()=>{cleanup();vi.restoreAllMocks();});
function setup(hasResume=true,fail=false){
 const upload=fail?vi.fn().mockRejectedValue(new Error('Could not parse this document')):vi.fn().mockResolvedValue({state:{}});
 const navigate=vi.fn(),select=vi.fn();
 const claim={id:'claim',skillId:'python',skillName:'Python',claim:'Skills: Python',evidenceState:'Unsupported'};
 const value={student:{name:'QA Learner'},targetCareer:{title:'ML Engineer'},competencyNodes:[{id:'python',name:'Python',state:'Verified'}],resumeAnalysis:{documentId:hasResume?'doc-test':undefined,fileName:'demo.pdf',uploadedAt:'Today',claims:hasResume?[claim]:[],atsCompatibilityScore:32,careerAlignmentScore:40,evidenceCoveragePercent:0,sectionsDetected:['skills'],extractedSkillsCount:1,missingSkillsForTarget:['SQL'],suggestedImprovements:['Support Python with evidence.'],parsedSections:[{name:'skills',text:'Python'}]},setActiveTab:navigate,setSelectedSkillId:select,uploadResume:upload,showToast:vi.fn()} as unknown as AppStateContextType;
 render(<AppStateContext.Provider value={value}><ResumeIntelligence/></AppStateContext.Provider>);return {upload,navigate,select};
}
it('uses selected role, hides empty verified card and inspects exact claim',()=>{
 const {select,navigate}=setup();expect(screen.queryByText('AI Engineer benchmark')).toBeNull();expect(screen.getByText('ML Engineer keyword coverage')).toBeTruthy();
 expect(screen.queryByText('Verified Skills Found on Resume')).toBeNull();
 fireEvent.keyDown(screen.getByRole('button',{name:'Inspect Gap: Python'}),{key:'Enter'});expect(select).toHaveBeenCalledWith('python');expect(navigate).toHaveBeenCalledWith('competencies');
 fireEvent.click(screen.getByRole('tab',{name:/Bullet Point Improver/}));expect(screen.getByText(/Support Python with evidence/)).toBeTruthy();
});
it('provides styled upload, parses file and resets chooser for same-file retry',async()=>{
 const {upload}=setup();fireEvent.click(screen.getByRole('button',{name:'Upload / Paste Resume'}));
 const input=screen.getByLabelText('Upload resume file');const file=new File(['Skills: Python'],'resume.txt',{type:'text/plain'});
 fireEvent.change(input,{target:{files:[file]}});await waitFor(()=>expect(upload).toHaveBeenCalledWith(file));
 await waitFor(()=>expect(screen.queryByRole('dialog')).toBeNull());expect(screen.getByRole('status').textContent).toContain('saved');
});
it('preserves pasted text and previous analysis on parse failure',async()=>{
 const {upload}=setup(true,true);fireEvent.click(screen.getByRole('button',{name:'Upload / Paste Resume'}));
 fireEvent.change(screen.getByLabelText('Resume text'),{target:{value:'Skills: Python'}});
 fireEvent.click(screen.getByRole('button',{name:'Parse & Align Competencies'}));
 await waitFor(()=>expect(screen.getByRole('alert').textContent).toContain('Could not parse'));
 expect(upload).toHaveBeenCalledWith('Skills: Python');expect((screen.getByLabelText('Resume text') as HTMLTextAreaElement).value).toBe('Skills: Python');
 expect(screen.getByText('Parsed Document: demo.pdf')).toBeTruthy();
});
it('empty state has no fake scores and disables export',()=>{
 setup(false);expect(screen.queryByText('Overall ATS Score')).toBeNull();expect((screen.getByRole('button',{name:'Export Verified Draft'}) as HTMLButtonElement).disabled).toBe(true);
});
it('exports only resume-supported verification, not unrelated verified nodes',()=>{
 setup();fireEvent.click(screen.getByRole('button',{name:'Export Verified Draft'}));
 const dialog=screen.getByRole('dialog',{name:'Export Verified Draft'});expect(dialog.textContent).toContain('No resume claims currently meet verification requirements');expect(dialog.textContent).toContain('Target: ML Engineer');
 const link=screen.getByRole('link',{name:'Download .md'}) as HTMLAnchorElement;
 expect(link.download).toBe('QA_Learner_Verified_Resume.md');
 expect(decodeURIComponent(link.href)).toContain('No resume claims currently meet verification requirements');
});
