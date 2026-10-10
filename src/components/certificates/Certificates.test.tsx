// @vitest-environment jsdom
import {useEffect} from 'react';
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {MyCertificates} from './MyCertificates';
import {PublicCertificate} from './PublicCertificate';
import {CertificateActions} from './CertificateShared';
import type {Certificate} from './api';
import {AppStateContext} from '../../lib/state/app-context';
import type {AppStateContextType} from '../../lib/state/app-state';
import App from '../../App';
vi.mock('./ServerCertificatePreview',()=>({ServerCertificatePreview:({onReady,displayName,displaySubtitle}:{onReady:(ready:boolean)=>void;displayName:string;displaySubtitle:string})=>{useEffect(()=>onReady(true),[onReady,displayName,displaySubtitle]);return <div>Server PDF preview</div>;}}));
const course={courseId:'course',courseName:'Python Course',eligible:true,reasons:[],requiredModuleIds:['course'],completedModules:1,assessments:[{id:'exam',title:'Python test',passed:true,passingScore:80}],skills:['Python'],assessmentScore:90};
const cert={certificateId:'CIQ-'+ 'a'.repeat(32),studentName:'Test Student',courseId:'course',courseName:'Python Course',type:'premium',skills:['Python'],assessmentScore:90,issuedAt:'2026-09-30',verificationStatus:'valid',paymentStatus:'demo_confirmed',issuer:'NexVora',publicUrl:'http://localhost:5000/certificate/test',pdfUrl:'/api/v1/certificates/test/pdf',qrUrl:'/api/v1/certificates/test/qr'};
const refresh=vi.fn().mockResolvedValue({});
function setup(eligible=true){
 const calls:string[]=[];
 vi.stubGlobal('fetch',vi.fn(async(input:RequestInfo|URL)=>{const url=String(input);calls.push(url);let data:unknown={};
 if(url.endsWith('/certificates'))data={certificates:[],courses:[{...course,eligible,reasons:eligible?[]:['Complete all required modules.']}],payment:{mode:'DEMO',amount:19900,currency:'INR',notice:'DEMO payment: no money is charged.'}};
 if(url.endsWith('/create-order'))data={orderId:'order',courseId:'course',mode:'DEMO',amount:19900,currency:'INR'};
 if(url.endsWith('/confirm'))data={status:'demo_confirmed'};
 if(url.endsWith('/generate'))data=cert;
 return new Response(JSON.stringify(data));}));
 const context={student:{name:'Test Student'},setActiveTab:vi.fn(),setCatalogSelection:vi.fn(),refreshWorkspace:refresh} as unknown as AppStateContextType;
 render(<AppStateContext.Provider value={context}><MyCertificates/></AppStateContext.Provider>);return calls;
}
afterEach(()=>{cleanup();vi.unstubAllGlobals();vi.clearAllMocks();window.history.replaceState({},'','/');});
it('requires preview, explicit demo purchase and confirmation before premium generation',async()=>{
 const calls=setup();fireEvent.click(await screen.findByRole('button',{name:'Preview Premium'}));
 fireEvent.change(screen.getByLabelText('Student display name'),{target:{value:'Alex QA'}});
 fireEvent.change(screen.getByLabelText('Optional subtitle'),{target:{value:'Learning journey'}});
 expect(screen.getAllByRole('textbox')).toHaveLength(2);
 expect(screen.getByRole('dialog')).toBeTruthy();expect(calls.some(p=>p.endsWith('/generate'))).toBe(false);
 fireEvent.click(screen.getByRole('button',{name:'Purchase — create DEMO order'}));
 fireEvent.click(await screen.findByRole('button',{name:'Confirm DEMO payment (no charge)'}));
 expect(calls.some(p=>p.endsWith('/generate'))).toBe(false);
 fireEvent.click(await screen.findByRole('button',{name:'Generate Premium Certificate'}));
 await waitFor(()=>expect(refresh).toHaveBeenCalledOnce());
 expect(calls.filter(p=>p.endsWith('/generate'))).toHaveLength(1);
 const request=vi.mocked(fetch).mock.calls.find(([url])=>String(url).endsWith('/generate'));
 expect(JSON.parse(String(request?.[1]?.body))).toMatchObject({displayName:'Alex QA',displaySubtitle:'Learning journey',courseId:'course',type:'premium'});
});
it('locks both certificate actions when the server reports ineligibility',async()=>{
 setup(false);expect((await screen.findByRole('button',{name:'Generate Free'}) as HTMLButtonElement).disabled).toBe(true);
 expect((screen.getByRole('button',{name:'Preview Premium'}) as HTMLButtonElement).disabled).toBe(true);
 expect(screen.getByText('Complete all required modules.')).toBeTruthy();
});
it('public deep link survives remount without login and exposes safe viewer fields',async()=>{
 vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify(cert))));sessionStorage.clear();
 window.history.replaceState({},'','/certificate/'+cert.certificateId);
 const first=render(<App/>);expect(await screen.findByRole('heading',{name:'Python Course'})).toBeTruthy();
 expect(screen.queryByText('Sign in')).toBeNull();expect(screen.getByTitle('Issued certificate PDF preview')).toBeTruthy();
 first.unmount();render(<App/>);expect(await screen.findByRole('heading',{name:'Python Course'})).toBeTruthy();
});
it('invalid public IDs fail safely',async()=>{
 vi.stubGlobal('fetch',vi.fn(async()=>new Response(JSON.stringify({detail:'Certificate not found or invalid.'}),{status:404})));
 render(<PublicCertificate id="bad"/>);expect(await screen.findByRole('heading',{name:'Certificate not found or invalid.'})).toBeTruthy();
 expect(screen.queryByTitle('Issued certificate PDF preview')).toBeNull();
});

it('copies a public verification URL and downloads the server PDF',async()=>{
 const writeText=vi.fn().mockResolvedValue(undefined);
 Object.defineProperty(navigator,'clipboard',{configurable:true,value:{writeText}});
 const create=vi.fn().mockReturnValue('blob:certificate');const revoke=vi.fn();
 vi.stubGlobal('URL',class extends URL {static createObjectURL=create;static revokeObjectURL=revoke;});
 const click=vi.spyOn(HTMLAnchorElement.prototype,'click').mockImplementation(()=>{});
 vi.stubGlobal('fetch',vi.fn(async()=>new Response('%PDF-fixture',{headers:{'Content-Type':'application/pdf'}})));
 render(<CertificateActions certificate={cert as Certificate}/>);
 fireEvent.click(screen.getByRole('button',{name:'Copy Link'}));
 await waitFor(()=>expect(writeText).toHaveBeenCalledWith(cert.publicUrl));
 fireEvent.click(screen.getByRole('button',{name:'Download PDF'}));
 await waitFor(()=>expect(click).toHaveBeenCalledOnce());
 expect(fetch).toHaveBeenCalledWith(cert.pdfUrl);expect(create).toHaveBeenCalledOnce();click.mockRestore();
});

it('opens demo preview from My Certificates without an issuance request',async()=>{
 const calls=setup();await screen.findByRole('button',{name:'Generate Free'});
 fireEvent.click(screen.getByRole('button',{name:'Preview Demo Certificate'}));
 expect(screen.getByRole('dialog',{name:'Demo certificate preview'})).toBeTruthy();
 fireEvent.click(screen.getByRole('button',{name:'Close Preview'}));
 expect(screen.queryByRole('dialog',{name:'Demo certificate preview'})).toBeNull();
 expect(calls.every(path=>path.endsWith('/certificates'))).toBe(true);
});
