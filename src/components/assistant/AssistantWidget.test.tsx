// @vitest-environment jsdom
import {afterEach,expect,it,vi} from 'vitest';
import {cleanup,fireEvent,render,screen,waitFor} from '@testing-library/react';
import {AssistantWidget} from './AssistantWidget';
import {intelligenceApi} from '../intelligence/api';
vi.mock('../intelligence/api',()=>({intelligenceApi:vi.fn()}));
vi.mock('../../lib/state/app-state',()=>({useAppState:()=>({setActiveTab:vi.fn()})}));
afterEach(()=>{cleanup();vi.restoreAllMocks();});
it('opens accessible chat, submits text, shows failure and leaves other UI available',async()=>{
  vi.mocked(intelligenceApi).mockImplementation(async(path)=>path==='/assistant/history'?[]:path==='/assistant/capabilities'?{search:'not_configured'}:{answer:'Use a base case.',mode:'general',sources:[],limitations:[]});
  render(<AssistantWidget/>);
  fireEvent.click(screen.getByRole('button',{name:'Open NexVora assistant'}));
  expect(await screen.findByRole('dialog',{name:'NexVora assistant'})).toBeTruthy();
  expect(await screen.findByText(/External search is not configured/)).toBeTruthy();
  fireEvent.change(screen.getByRole('textbox',{name:'Assistant question'}),{target:{value:'Explain recursion'}});
  fireEvent.click(screen.getByRole('button',{name:'Send'}));
  expect(await screen.findByText('Use a base case.')).toBeTruthy();
  expect(vi.mocked(intelligenceApi).mock.calls.find(([path])=>path==='/assistant/chat')?.[1]).toMatchObject({message:'Explain recursion',research:false});
  fireEvent.keyDown(document,{key:'Escape'});
  await waitFor(() => expect(screen.queryByRole('dialog')).toBeNull());
  expect(screen.getByRole('button',{name:'Open NexVora assistant'})).toBeTruthy();
});
