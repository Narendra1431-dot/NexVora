// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {ServerCertificatePreview} from './ServerCertificatePreview';
afterEach(()=>{cleanup();vi.unstubAllGlobals();sessionStorage.clear();});
it('loads an authenticated server-rendered preview and waits for the image before allowing generation',async()=>{
 const ready=vi.fn();sessionStorage.setItem('plcip_token','test-token');
 vi.stubGlobal('URL',class extends URL {static createObjectURL=vi.fn(()=> 'blob:preview');static revokeObjectURL=vi.fn();});
 vi.stubGlobal('fetch',vi.fn(async()=>new Response(new Blob(['png'],{type:'image/png'}))));
 const view=render(<ServerCertificatePreview courseId="course" type="premium" displayName="Alex" displaySubtitle="Learner" onReady={ready}/>);
 expect(ready).toHaveBeenLastCalledWith(false);
 const img=await screen.findByRole('img');expect(ready).not.toHaveBeenCalledWith(true);
 fireEvent.load(img);expect(ready).toHaveBeenLastCalledWith(true);
 const [url,request]=vi.mocked(fetch).mock.calls[0];expect(url).toBe('/api/v1/certificates/preview');
 expect(JSON.parse(String(request?.body))).toEqual({courseId:'course',type:'premium',displayName:'Alex',displaySubtitle:'Learner'});
 expect(request?.headers).toMatchObject({Authorization:'Bearer test-token'});
 view.unmount();await waitFor(()=>expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:preview'));
});
