// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest';
import { cleanup, fireEvent, render, screen } from '@testing-library/react';
import { AppStateContext } from '../../lib/state/app-context';
import type { AppStateContextType } from '../../lib/state/app-state';
import { CommandPalette } from './CommandPalette';

afterEach(cleanup);
function setup() {
  const setCatalogSelection=vi.fn(), setActiveTab=vi.fn(), setCommandPaletteOpen=vi.fn();
  const value={commandPaletteOpen:true,setCommandPaletteOpen,competencyNodes:[],careers:[],resources:[],projects:[],assessments:[{id:'sql-bank',title:'SQL baseline',skillName:'SQL',category:'Diagnostic',estimatedTime:'5 mins'}],setCatalogSelection,setActiveTab,setSelectedSkillId:vi.fn(),setTargetCareer:vi.fn()} as unknown as AppStateContextType;
  render(<AppStateContext.Provider value={value}><CommandPalette/></AppStateContext.Provider>);
  return {setCatalogSelection,setActiveTab,setCommandPaletteOpen};
}
describe('Global search interactions',()=>{
  it('keyboard selection navigates to the exact matching bank',()=>{
    const actions=setup();
    fireEvent.change(screen.getByRole('textbox',{name:'Search workspace items'}),{target:{value:'SQL'}});
    fireEvent.keyDown(screen.getByRole('button',{name:/SQL baseline/}),{key:'Enter'});
    expect(actions.setCatalogSelection).toHaveBeenCalledWith({tab:'assessments',id:'sql-bank'});
    expect(actions.setActiveTab).toHaveBeenCalledWith('assessments');
    expect(actions.setCommandPaletteOpen).toHaveBeenCalledWith(false);
  });
  it('Escape closes the dialog without changing student or navigation state',()=>{
    const actions=setup();
    fireEvent.keyDown(screen.getByRole('textbox',{name:'Search workspace items'}),{key:'Escape'});
    expect(actions.setCommandPaletteOpen).toHaveBeenCalledWith(false);
    expect(actions.setActiveTab).not.toHaveBeenCalled();
    expect(actions.setCatalogSelection).not.toHaveBeenCalled();
  });
});
