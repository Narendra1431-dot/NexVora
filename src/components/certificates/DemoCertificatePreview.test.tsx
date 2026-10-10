// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen} from '@testing-library/react';
import {DemoCertificatePreview} from './DemoCertificatePreview';
afterEach(cleanup);
it('switches sample templates, zooms, fits, enters full-screen, downloads and closes without issuing',()=>{
 const close=vi.fn();render(<DemoCertificatePreview onClose={close}/>);
 expect(screen.getByRole('dialog',{name:'Demo certificate preview'})).toBeTruthy();
 expect(screen.getByRole('img').getAttribute('src')).toContain('/demo/premium/preview.png');
 expect(screen.getByRole('img').getAttribute('alt')).toContain('88%');
 fireEvent.load(screen.getByRole('img'));expect(screen.queryByText('Rendering sample certificate...')).toBeNull();
 fireEvent.click(screen.getByRole('button',{name:'Zoom in'}));expect(screen.getByRole('img').style.width).toBe('125%');
 fireEvent.click(screen.getByRole('button',{name:'Fit Width'}));expect(screen.getByRole('img').style.width).toBe('100%');
 fireEvent.click(screen.getByRole('button',{name:'Full-screen Viewer'}));expect(screen.getByRole('button',{name:'Exit Full-screen'}).getAttribute('aria-pressed')).toBe('true');
 fireEvent.click(screen.getByRole('button',{name:'Standard Certificate Preview'}));
 expect(screen.getByRole('img').getAttribute('src')).toContain('/demo/free/preview.png');
 expect(screen.getByRole('link',{name:'Download Sample PDF'}).getAttribute('href')).toBe('/api/v1/certificates/demo/free/pdf');
 fireEvent.click(screen.getByRole('button',{name:'Close Preview'}));expect(close).toHaveBeenCalledOnce();
});
it('shows a useful error and supports Escape to close',()=>{
 const close=vi.fn();render(<DemoCertificatePreview onClose={close}/>);fireEvent.error(screen.getByRole('img'));
 expect(screen.getByRole('alert').textContent).toContain('could not load');
 fireEvent.keyDown(document,{key:'Escape'});expect(close).toHaveBeenCalledOnce();
});

