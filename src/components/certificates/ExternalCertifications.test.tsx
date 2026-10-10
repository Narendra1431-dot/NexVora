// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor,within} from '@testing-library/react';
import {MyCertificates} from './MyCertificates';
import {AppStateContext} from '../../lib/state/app-context';
import type {AppStateContextType} from '../../lib/state/app-state';
import catalog from './external-catalog.fixture.json';

const refresh=vi.fn().mockResolvedValue({});
function setup(fail=false){
  let credentials:unknown[]=[];
  const fetcher=vi.fn(async(input:RequestInfo|URL,init?:RequestInit)=>{
   const url=String(input);
   if(url.endsWith('/certificates'))return new Response(JSON.stringify({certificates:[],courses:[],payment:{mode:'DEMO',notice:'DEMO payment',amount:19900,currency:'INR'}}));
   if(url.endsWith('/proof'))return new Response('%PDF-proof');
   if(init?.method==='POST'||init?.method==='PUT'){
    if(fail)return new Response(JSON.stringify({detail:'Credential URL is invalid.'}),{status:422});
    const body=init.body as FormData;const fields=JSON.parse(String(body.get('payload')));
    const record={...fields,id:'saved-credential',status:'Added',hasProof:body.has('proof'),proofName:'certificate-proof.pdf'};
    credentials=[record];return new Response(JSON.stringify(record),{status:201});
   }
   return new Response(JSON.stringify({catalog,credentials}));
  });
  vi.stubGlobal('fetch',fetcher);
  vi.stubGlobal('sessionStorage', {
    getItem: vi.fn(() => 'test-token'),
    setItem: vi.fn(),
    removeItem: vi.fn(),
    clear: vi.fn(),
  });
  const ctx={student:{name:'QA'},refreshWorkspace:refresh} as unknown as AppStateContextType;
  const view=render(<AppStateContext.Provider value={ctx}><MyCertificates/></AppStateContext.Provider>);
  return {fetcher,view};
}
afterEach(()=>{cleanup();vi.unstubAllGlobals();vi.clearAllMocks();});
it('separates tabs, all categories and official details for every provider',async()=>{
 setup();fireEvent.click(screen.getByRole('tab',{name:'External Certifications'}));
 await screen.findByRole('article',{name:catalog[0].name});expect(screen.getAllByRole('article')).toHaveLength(13);
 for(const cert of catalog){
  const card=within(screen.getByRole('article',{name:cert.name}));
  expect(card.getByRole('link',{name:'Official Website'}).getAttribute('href')).toBe(cert.officialUrl);
  expect(card.getByRole('link',{name:'Official Website'}).getAttribute('target')).toBe('_blank');
  fireEvent.click(card.getByRole('button',{name:'View Certification'}));
  const dialog=within(screen.getByRole('dialog'));
  expect(dialog.getByRole('link',{name:'Open Official Certification Page'}).getAttribute('href')).toBe(cert.officialUrl);
  fireEvent.click(dialog.getByRole('button',{name:'Close'}));
 }
 for(const category of ['Cloud','DevOps','AI/ML','Development','Database','Linux','Networking']){
  fireEvent.click(screen.getByRole('button',{name:category}));
  expect(screen.getAllByRole('article')).toHaveLength(catalog.filter(c=>c.categories.includes(category)).length);
 }
 fireEvent.click(screen.getByRole('button',{name:'NexVora'}));
 expect(screen.getByRole('tab',{name:'NexVora Certificates'}).getAttribute('aria-selected')).toBe('true');
 expect(screen.queryByRole('article')).toBeNull();
 fireEvent.click(screen.getByRole('tab',{name:'My Added Credentials'}));
 expect(await screen.findByText(/No saved credentials/)).toBeTruthy();
},30000);
it('saves fields and proof, shows Added, edits and downloads proof',async()=>{
 const {fetcher}=setup();
 vi.stubGlobal('URL',class extends URL{static createObjectURL=vi.fn(()=> 'blob:proof');static revokeObjectURL=vi.fn();});
 const click=vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(()=>{});
 fireEvent.click(screen.getByRole('tab',{name:'External Certifications'}));
 const card=within(await screen.findByRole('article',{name:catalog[0].name}));
 fireEvent.click(card.getByRole('button',{name:'Add to My Profile'}));
 fireEvent.change(screen.getByLabelText('Credential ID'),{target:{value:'AWS-123'}});
 fireEvent.change(screen.getByLabelText('Credential URL'),{target:{value:'https://www.credly.com/badges/example'}});
 fireEvent.change(screen.getByLabelText('Issue Date'),{target:{value:'2025-01-01'}});
 fireEvent.change(screen.getByLabelText('Expiry Date (optional)'),{target:{value:'2028-01-01'}});
 fireEvent.change(screen.getByLabelText(/Upload certificate proof/),{target:{files:[new File(['%PDF-test'],'proof.pdf',{type:'application/pdf'})]}});
 fireEvent.click(screen.getByRole('button',{name:'Save Credential'}));
 await waitFor(()=>expect(refresh).toHaveBeenCalled());
 const request=fetcher.mock.calls.find(([,init])=>init?.method==='POST')![1]!;
 expect(request.body).toBeInstanceOf(FormData);
 expect(JSON.parse(String((request.body as FormData).get('payload')))).toEqual({certificationId:catalog[0].id,credentialId:'AWS-123',credentialUrl:'https://www.credly.com/badges/example',issueDate:'2025-01-01',expiryDate:'2028-01-01'});
 fireEvent.click(screen.getByRole('tab',{name:'My Added Credentials'}));
 expect(screen.getAllByRole('article')).toHaveLength(1);expect(screen.getByText('Added',{exact:true})).toBeTruthy();
 expect(screen.getByRole('link',{name:'Open Credential'}).getAttribute('href')).toContain('credly.com');
 fireEvent.click(screen.getByRole('button',{name:'Download Proof'}));await waitFor(()=>expect(click).toHaveBeenCalledOnce());click.mockRestore();
 fireEvent.click(screen.getByRole('button',{name:'Edit Credential'}));
 expect((screen.getByLabelText('Credential ID') as HTMLInputElement).value).toBe('AWS-123');
 fireEvent.click(screen.getByRole('button',{name:'Cancel'}));expect(screen.queryByRole('dialog')).toBeNull();
});
it('keeps failed submissions editable and shows the server error',async()=>{
 setup(true);fireEvent.click(screen.getByRole('tab',{name:'External Certifications'}));
 fireEvent.click(within(await screen.findByRole('article',{name:catalog[0].name})).getByRole('button',{name:'Add to My Profile'}));
 fireEvent.change(screen.getByLabelText('Issue Date'),{target:{value:'2025-01-01'}});
 fireEvent.click(screen.getByRole('button',{name:'Save Credential'}));
 expect(await screen.findByRole('alert')).toHaveProperty('textContent','Credential URL is invalid.');
 expect(screen.getByRole('dialog')).toBeTruthy();expect(refresh).not.toHaveBeenCalled();
});
