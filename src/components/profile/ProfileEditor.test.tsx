// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {AppStateContext} from '../../lib/state/app-context';
import {EditHistoryProvider} from '../../lib/state/edit-history';
import {ProfileEditor} from './ProfileEditor';
import {ProfileAvatar} from './ProfileAvatar';
import {AvatarPicker} from './AvatarPicker';
afterEach(()=>{cleanup();vi.restoreAllMocks();vi.unstubAllGlobals();});
const student={name:'Test Student',headline:'Learner',degree:'B.Tech',institution:'College',gpa:'',gradYear:'2027',weeklyAvailabilityHours:5,bio:'',learningPreferences:['Labs']};
function setup(ui:React.ReactNode){const saveProfile=vi.fn().mockResolvedValue(true),refreshWorkspace=vi.fn().mockResolvedValue(undefined);render(<EditHistoryProvider><AppStateContext.Provider value={{student,careers:[{id:'ai',title:'AI Engineer'}],saveProfile,refreshWorkspace} as any}>{ui}</AppStateContext.Provider></EditHistoryProvider>);return {saveProfile,refreshWorkspace};}
it('edits all profile fields, saves current values and cancels without a write',async()=>{
 const close=vi.fn();const {saveProfile}=setup(<ProfileEditor onClose={close}/>);
 for(const [label,value] of [['Name','New Name'],['Headline / Role','Developer'],['Degree','MSc'],['College','New College'],['GPA','9/10'],['Graduation year','2028'],['Profile summary','My summary'],['Prior experience','Internship'],['Academic details','AI major'],['Learning preferences','Books, Projects']])fireEvent.change(screen.getByLabelText(label),{target:{value}});
 fireEvent.change(screen.getByLabelText('Weekly learning hours'),{target:{value:'12'}});fireEvent.change(screen.getByLabelText('Target readiness display source'),{target:{value:'ai'}});
 fireEvent.click(screen.getByRole('button',{name:'Save'}));await waitFor(()=>expect(close).toHaveBeenCalled());
 expect(saveProfile).toHaveBeenCalledWith({name:'New Name',headline:'Developer',degree:'MSc',institution:'New College',gpa:'9/10',gradYear:'2028',weeklyAvailabilityHours:12,bio:'My summary',priorExperience:'Internship',academicDetails:'AI major',learningPreferences:['Books','Projects'],readinessDisplayCareerId:'ai'});
 cleanup();const second=setup(<ProfileEditor onClose={close}/>);fireEvent.change(screen.getByLabelText('Name'),{target:{value:'Not saved'}});fireEvent.click(screen.getByRole('button',{name:'Cancel'}));expect(second.saveProfile).not.toHaveBeenCalled();
});
it('selects an avatar, saves it and resets to initials',async()=>{
 const fetch=vi.fn().mockResolvedValue({ok:true});vi.stubGlobal('fetch',fetch);const close=vi.fn();const {refreshWorkspace}=setup(<AvatarPicker onClose={close}/>);
 expect(screen.getAllByRole('button',{pressed:false})).toHaveLength(16);
 fireEvent.click(screen.getByRole('button',{name:'Hero · teal guardian'}));expect(screen.getByRole('button',{name:'Hero · teal guardian'}).getAttribute('aria-pressed')).toBe('true');
 fireEvent.click(screen.getByRole('button',{name:'Save Avatar'}));await waitFor(()=>expect(refreshWorkspace).toHaveBeenCalled());expect(fetch).toHaveBeenCalledWith('/api/v1/profile/avatar',expect.objectContaining({method:'PUT',body:JSON.stringify({presetId:'hero-1'})}));
 fireEvent.click(screen.getByRole('button',{name:'Remove / Reset Photo'}));fireEvent.click(screen.getByRole('button',{name:'Save Avatar'}));await waitFor(()=>expect(fetch).toHaveBeenCalledWith('/api/v1/profile/avatar',expect.objectContaining({method:'DELETE'})));
});
it('validates file size and type, previews a crop and uploads the cropped file',async()=>{
 vi.stubGlobal('URL',class extends URL{static createObjectURL=vi.fn(()=> 'blob:profile');static revokeObjectURL=vi.fn();});
 class FakeImage {naturalWidth=600;naturalHeight=400;onload?:()=>void;set src(_value:string){queueMicrotask(()=>this.onload?.());}}
 vi.stubGlobal('Image',FakeImage);
 const draw=vi.fn();vi.spyOn(HTMLCanvasElement.prototype,'getContext').mockReturnValue({fillRect:vi.fn(),drawImage:draw} as any);
 vi.spyOn(HTMLCanvasElement.prototype,'toBlob').mockImplementation(callback=>callback(new Blob(['cropped'],{type:'image/webp'})));
 const fetch=vi.fn().mockResolvedValue({ok:true});vi.stubGlobal('fetch',fetch);setup(<AvatarPicker onClose={vi.fn()}/>);
 const input=screen.getByLabelText('Upload Photo');fireEvent.change(input,{target:{files:[new File(['bad'],'bad.svg',{type:'image/svg+xml'})]}});expect(screen.getByRole('alert').textContent).toContain('JPG');
 fireEvent.change(input,{target:{files:[new File([new Uint8Array(5*1024*1024+1)],'big.png',{type:'image/png'})]}});expect(screen.getByRole('alert').textContent).toContain('5 MB');
 fireEvent.change(input,{target:{files:[new File(['photo'],'photo.png',{type:'image/png'})]}});await waitFor(()=>expect(draw).toHaveBeenCalled());
 fireEvent.change(screen.getByLabelText('Zoom'),{target:{value:'2'}});await waitFor(()=>expect(draw.mock.calls.at(-1)?.slice(1)).toEqual([200,100,200,200,0,0,384,384]));
 fireEvent.click(screen.getByRole('button',{name:'Save Avatar'}));await waitFor(()=>expect(fetch).toHaveBeenCalledWith('/api/v1/profile/photo',expect.objectContaining({method:'POST',body:expect.any(FormData)})));
});
it('falls back to initials when an uploaded photo fails',()=>{
 render(<ProfileAvatar name="Test Student" avatar={{kind:'photo',dataUrl:'data:image/webp;base64,broken'}}/>);fireEvent.error(screen.getByRole('img'));expect(screen.getByRole('img',{name:"Test Student's initials"})).toBeTruthy();expect(screen.getByText('TS')).toBeTruthy();
});
