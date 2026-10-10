// @vitest-environment jsdom
import { useState } from 'react';
import { afterEach, describe, expect, it } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { useModalDialog } from './use-modal-dialog';

afterEach(cleanup);
function Harness() {
  const [open,setOpen]=useState(false);
  const ref=useModalDialog(open,()=>setOpen(false));
  return <><button onClick={()=>setOpen(true)}>Open dialog</button>{open && <div ref={ref} role="dialog" aria-label="Test dialog" tabIndex={-1}><input aria-label="First field"/><button onClick={()=>setOpen(false)}>Close dialog</button></div>}</>;
}

describe('Modal keyboard navigation',()=>{
  it('places focus inside, wraps both ways, closes on Escape and restores focus',()=>{
    render(<Harness/>);
    const trigger=screen.getByRole('button',{name:'Open dialog'});
    trigger.focus(); fireEvent.click(trigger);
    const input=screen.getByRole('textbox',{name:'First field'});
    const close=screen.getByRole('button',{name:'Close dialog'});
    expect(document.activeElement).toBe(input);
    expect(document.body.style.overflow).toBe('hidden');
    fireEvent.keyDown(input,{key:'Tab',shiftKey:true});
    expect(document.activeElement).toBe(close);
    fireEvent.keyDown(close,{key:'Tab'});
    expect(document.activeElement).toBe(input);
    fireEvent.keyDown(input,{key:'Escape'});
    expect(screen.queryByRole('dialog')).toBeNull();
    expect(document.activeElement).toBe(trigger);
    expect(document.body.style.overflow).not.toBe('hidden');
  });
});
