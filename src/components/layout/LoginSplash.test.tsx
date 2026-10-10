// @vitest-environment jsdom
import {afterEach,beforeEach,expect,it,vi} from 'vitest';
import {act,cleanup,render,screen} from '@testing-library/react';
import {LoginSplash} from './LoginSplash';
beforeEach(()=>{sessionStorage.clear();vi.useFakeTimers();vi.stubGlobal('matchMedia',()=>({matches:false,addEventListener:vi.fn(),removeEventListener:vi.fn()}));});
afterEach(()=>{cleanup();vi.useRealTimers();vi.unstubAllGlobals();});
const login=<button>Existing Login</button>;
it('uses transparent SVG layers and no boxed raster image then crossfades to mounted Login',()=>{
 const view=render(<LoginSplash>{login}</LoginSplash>);
 expect(screen.getByRole('img').tagName.toLowerCase()).toBe('svg');expect(view.container.querySelector('img, image')).toBeNull();
 expect(view.container.querySelector('video')).toBeNull();expect(view.container.querySelectorAll('.particle')).toHaveLength(5);
 
 expect(screen.queryByRole('button')).toBeNull();expect(document.body.style.overflow).toBe('hidden');
 act(()=>vi.advanceTimersByTime(5599));expect(screen.getByRole('status').className).not.toContain('splash-exit');
 act(()=>vi.advanceTimersByTime(1));expect(screen.getByRole('status').className).toContain('splash-exit');
 expect(view.container.querySelector('.nexvora-login-layer--waiting')).toBeNull();
 act(()=>vi.advanceTimersByTime(600));expect(screen.getByRole('button')).toBeTruthy();expect(document.body.style.overflow).toBe('');
 view.unmount();render(<LoginSplash>{login}</LoginSplash>);expect(screen.queryByRole('status')).toBeNull();
});
it('preserves authenticated session bypass',()=>{sessionStorage.setItem('plcip_token','existing');render(<LoginSplash>{login}</LoginSplash>);expect(screen.queryByRole('status')).toBeNull();expect(screen.getByRole('button')).toBeTruthy();});
it('shows the final image briefly without construction for reduced motion',()=>{
 vi.stubGlobal('matchMedia',()=>({matches:true,addEventListener:vi.fn(),removeEventListener:vi.fn()}));render(<LoginSplash>{login}</LoginSplash>);expect(screen.getByRole('status').className).toContain('is-reduced');act(()=>vi.advanceTimersByTime(2100));expect(screen.getByRole('button')).toBeTruthy();
});
