import { useEffect, useRef, useState } from 'react';
import { MessageCircle, Mic, Send, Square, Volume2, X } from 'lucide-react';
import { intelligenceApi } from '../intelligence/api';
import { useModalDialog } from '../../lib/hooks/use-modal-dialog';
import { useAppState } from '../../lib/state/app-state';
import DesignButton from '../../components/common/DesignButton';
import { useVoice } from './useVoice';
import { motion, AnimatePresence } from 'motion/react';

type Answer={answer:string;mode:string;sources?:{id?:string;title?:string;source?:string;url?:string;basis?:string}[];limitations?:string[];approval?:boolean;agentRun?:{id?:string};research?:{queries:string[];sourcesRetrieved:number;domainsCompared:number;pagesRead:number}};
type Message={id:string;role:string;content:string;response?:Answer};
const control='rounded-lg border border-slate-200 px-3 py-2 text-sm font-semibold disabled:opacity-40';
const safeLink=(url?:string)=>{try{return url&&new URL(url).protocol==='https:'?url:undefined;}catch{return undefined;}};

export function AssistantWidget(){
 const {setActiveTab}=useAppState();
 const [open,setOpen]=useState(false),[input,setInput]=useState(''),[messages,setMessages]=useState<Message[]>([]),[busy,setBusy]=useState(false),[error,setError]=useState(''),[deep,setDeep]=useState(false),[search,setSearch]=useState('');
 const alive=useRef(true);useEffect(()=>{alive.current=true;return()=>{alive.current=false;};},[]);
 const conversation=useRef<HTMLDivElement>(null);
 useEffect(()=>{if(open&&conversation.current)conversation.current.scrollTop=conversation.current.scrollHeight;},[open,messages,busy]);
 const voice=useVoice(setInput);
 const close=()=>{voice.stop();setOpen(false);};
 const modal=useModalDialog(open,close);
 useEffect(()=>{if(!open)return;let active=true;setError('');
  void Promise.all([intelligenceApi('/assistant/history'),intelligenceApi('/assistant/capabilities')]).then(([rows,cap])=>{if(active){setMessages(rows);setSearch(cap.search);}}).catch(()=>{if(active)setError('Conversation history could not load. Check your connection.');});return()=>{active=false;};
 },[open]);
 const submit=async()=>{if(busy||!input.trim())return;const question=input.trim();setBusy(true);setError('');voice.stop();
  try{const response:Answer=await intelligenceApi('/assistant/chat',{message:question,requestId:crypto.randomUUID(),research:deep});if(alive.current){setMessages(rows=>[...rows,{id:crypto.randomUUID(),role:'user',content:question},{id:crypto.randomUUID(),role:'assistant',content:response.answer,response}]);setInput('');}}
  catch(e){if(alive.current)setError(e instanceof Error?e.message:'Assistant unavailable. Please retry.');}finally{if(alive.current)setBusy(false);}
 };
 const inspect=(response:Answer)=>{close();setActiveTab('agent-hub');const id=response.agentRun?.id;window.history.replaceState({},'',response.approval?'/agent-hub/approvals':id?.startsWith('agt-')?'/agent-hub/runs?run='+encodeURIComponent(id):'/agent-hub');};
 return (
    <>
      <AnimatePresence>
        {!open && (
          <motion.button
            type="button"
            aria-label="Open NexVora assistant"
            onClick={() => setOpen(true)}
            className="fixed bottom-5 right-5 z-40 rounded-full bg-teal-800 text-white p-3 shadow-lg hover:bg-teal-900 focus-visible:outline-2 focus-visible:outline-offset-4"
            initial={{ opacity: 0, scale: 0.8, y: 20 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 20 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            whileHover={{ scale: 1.1 }}
            whileTap={{ scale: 0.95 }}
          >
            <MessageCircle size={22} />
          </motion.button>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {open && (
          <div className="fixed inset-0 z-50 bg-slate-900/20 flex justify-end items-end p-2 sm:p-5" onClick={close}>
            <motion.div
              ref={modal}
              role="dialog"
              aria-modal="true"
              aria-label="NexVora assistant"
              onClick={e => e.stopPropagation()}
              className="w-full max-w-md h-[min(760px,calc(100dvh-16px))] flex flex-col rounded-2xl border border-slate-200 bg-white shadow-xl overflow-hidden"
              initial={{ opacity: 0, x: 300, scale: 0.95 }}
              animate={{ opacity: 1, x: 0, scale: 1 }}
              exit={{ opacity: 0, x: 300, scale: 0.95 }}
              transition={{ duration: 0.3, ease: 'easeOut' }}
            >
    <header className="p-4 border-b flex items-center justify-between"><div><h2 className="font-bold text-slate-900">NexVora assistant</h2><p className="text-xs text-slate-500">Your skills, learning and career questions</p></div><button aria-label="Close assistant" className={control} onClick={close}><X size={18}/></button></header>
<div ref={conversation} className="flex-1 overflow-y-auto p-4 space-y-4 min-h-0" aria-live="polite">
      <AnimatePresence>
        {!messages.length && (
          <motion.p
            className="text-sm text-slate-600"
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            Ask about your skill gaps, resume or next learning step. Current questions use external research when available.
          </motion.p>
        )}
        {messages.map((m, index) => (
          <motion.article
            key={m.id}
            className={'rounded-xl p-3 ' + (m.role === 'user' ? 'bg-teal-50' : 'bg-slate-50')}
            initial={{ opacity: 0, y: 20, x: m.role === 'user' ? 30 : -30 }}
            animate={{ opacity: 1, y: 0, x: 0 }}
            exit={{ opacity: 0, y: -10, x: m.role === 'user' ? 30 : -30 }}
            transition={{ duration: 0.3, delay: index * 0.05, ease: 'easeOut' }}
          >
            <p className="text-xs font-semibold text-slate-500 mb-2">{m.role === 'user' ? 'You' : 'NexVora'}</p>
            <p className="text-sm leading-relaxed whitespace-pre-wrap break-words">{m.content}</p>
            {m.response?.limitations?.map((s, i) => (
              <motion.p key={i} className="mt-2 text-xs text-amber-800" initial={{ opacity: 0, y: 5 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                {s}
              </motion.p>
            ))}
            {!!m.response?.sources?.length && (
              <motion.ul className="mt-3 space-y-2 text-xs" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                {m.response.sources.map((s, i) => (
                  <li key={s.id || i}>
                    {safeLink(s.url) ? (
                      <a href={safeLink(s.url)} target="_blank" rel="noopener noreferrer" className="text-teal-800 underline">
                        {s.title || s.url}
                      </a>
                    ) : (
                      <span>{s.title || s.source || 'Internal source'}</span>
                    )}
                    {s.basis && <span className="block text-slate-500">{s.basis}</span>}
                  </li>
                ))}
              </motion.ul>
            )}
            {m.response?.research && (
              <motion.details className="text-xs mt-3" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                <summary>Research performed</summary>
                <p>{m.response.research.sourcesRetrieved} sources; {m.response.research.domainsCompared} domains; {m.response.research.pagesRead} official pages read.</p>
                <ul>
                  {m.response.research.queries.map(q => <li key={q}>{q}</li>)}
                </ul>
              </motion.details>
            )}
            {m.role === 'assistant' && (
              <motion.div className="flex flex-wrap gap-2 mt-3" initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ delay: 0.1 }}>
                <DesignButton
                  className={control}
                  disabled={!voice.canSpeak}
                  aria-label="Read answer aloud"
                  onClick={() => voice.speak(m.content)}
                  variant="secondary"
                  size="sm"
                >
                  <Volume2 size={16} />
                </DesignButton>
                {m.response && (m.response.approval || m.response.agentRun?.id?.startsWith('agt-')) && (
                  <DesignButton
                    className={control}
                    onClick={() => inspect(m.response!)}
                    variant="secondary"
                    size="sm"
                  >
                    {m.response.approval ? 'Review approval' : 'View workflow'}
                  </DesignButton>
                )}
              </motion.div>
            )}
          </motion.article>
        ))}
      </AnimatePresence>
      {busy && <motion.p role="status" className="text-sm text-teal-800" initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.2 }}>Preparing your answer…</motion.p>}
    </div>
<form className="p-4 border-t space-y-2" onSubmit={e => { e.preventDefault(); void submit(); }}>
      <AnimatePresence>
        {(error || voice.error) && (
          <motion.p role="alert" className="text-xs text-red-700" initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }} exit={{ opacity: 0, y: -10 }} transition={{ duration: 0.2 }}>
            {error || voice.error}
          </motion.p>
        )}
      </AnimatePresence>
      {search === 'not_configured' && <p className="text-xs text-amber-800">External search is not configured. Current facts cannot be verified.</p>}
      <motion.label className="flex items-center gap-2 text-xs" whileHover={{ scale: 1.01 }} transition={{ duration: 0.2 }}>
        <input type="checkbox" checked={deep} onChange={e => setDeep(e.target.checked)} /> Research multiple sources
      </motion.label>
      <textarea aria-label="Assistant question" maxLength={3000} rows={3} value={input} disabled={busy} onChange={e => setInput(e.target.value)} className="w-full border border-slate-300 rounded-lg p-2 text-sm resize-none" placeholder="What should I learn next?" />
      <div className="flex gap-2">
        <button
          type="button"
          className={control}
          disabled={!voice.canListen || busy}
          onClick={voice.listening ? voice.stop : voice.listen}
          aria-label={voice.listening ? 'Stop listening' : 'Use microphone'}
        >
          {voice.listening ? <Square size={17} /> : <Mic size={17} />}
        </button>
        {voice.speaking && (
          <button
            type="button"
            className={control}
            onClick={voice.stop}
          >
            Stop audio
          </button>
        )}
        <button
          type="submit"
          disabled={busy || !input.trim()}
          className={control + ' ml-auto bg-teal-800 text-white flex items-center gap-2'}
        >
          <Send size={16} /> Send
        </button>
      </div>
      <p className="text-[11px] text-slate-500">{voice.listening ? 'Listening… Review the transcript before sending.' : voice.canListen ? 'Microphone starts only on click. Your browser may use a remote speech service.' : 'Speech input is unavailable in this browser; typing remains available.'}</p>
</form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </>
  );
}
