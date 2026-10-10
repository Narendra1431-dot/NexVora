import {AgentGovernance} from '../intelligence/AgentGovernance';
import {LearningMaterial} from '../intelligence/LearningMaterial';
import { useUndoableState } from '../../lib/state/edit-history';
import {CareerIntelligencePanel} from '../common/CareerIntelligencePanel';
import { useEffect, useRef, useState } from 'react';
import { useAppState } from '../../lib/state/app-state';
import { motion, AnimatePresence } from 'motion/react';
import {
  Bot,
  Send,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  TrendingUp,
  HelpCircle,
  FileCheck2,
  CheckCircle2
} from 'lucide-react';

export function AiMentor() {
  const {
    mission, mentorError, mentorBusy, mentorStatus, checkMentorStatus,
    student,
    targetCareer,
    evidenceItems,
    mentorMessages,
    sendMentorMessage,
    setActiveTab,
    setSelectedSkillId
  } = useAppState();

  const [inputMessage, setInputMessage, resetInputMessage] = useUndoableState('', 'Mentor question');
  const [checking,setChecking] = useState(false);
  const endRef=useRef<HTMLDivElement>(null);
  useEffect(()=>{void checkMentorStatus();},[]);
  useEffect(()=>{endRef.current?.scrollIntoView?.({block:'nearest'});},[mentorMessages,mentorBusy]);
  const checkConnection=async()=>{setChecking(true);try{await checkMentorStatus(true);}finally{setChecking(false);}};


  const quickPrompts = [
    `Why am I not ready for ${targetCareer.title} yet?`,
    'Explain the exact prerequisite chain for Transformers',
    'What should I do this week to maximize readiness?',
    'How would verifying my RAG project affect my readiness?'
  ];

  const messageVariants = {
    hidden: { opacity: 0, y: 20, scale: 0.95 },
    visible: { 
      opacity: 1, 
      y: 0, 
      scale: 1,
      transition: { 
        duration: 0.3, 
        staggerChildren: 0.05
      }
    }
  };

  const messageItemVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.2 }
    }
  };

  const loadingVariants = {
    hidden: { opacity: 0, scale: 0.8 },
    visible: {
      opacity: 1,
      scale: 1,
      transition: { duration: 0.2 }
    }
  };

  const inputAreaVariants = {
    hidden: { opacity: 0, y: 10 },
    visible: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.3, delay: 0.1 }
    }
  };

  const handleSend = async (textToSend?: string) => {
    const text = textToSend || inputMessage;
    if (!text.trim() || mentorBusy) return;

    resetInputMessage('');
    const sent=await sendMentorMessage(text);
    if(!sent) resetInputMessage(text);
  };

  return (
    <div className="space-y-6 pb-12">{mentorError && <p role="alert" className="border border-red-200 bg-red-50 text-red-800 p-4 rounded-xl">{mentorError}</p>}
      {/* Top Banner */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            
            <span>NexVora Agentic Copilot</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Ask questions, plan your learning, and explore your evidence and curated {targetCareer.title} requirements.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-500 font-medium">Model Grounding:</span>
          <span className="font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200 flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5" />
            <span>{evidenceItems.length} Evidence Records Available</span>
          </span>
        </div>
      </div>

      <section aria-label="AI service status" className="rounded-xl border border-slate-200 bg-white p-4 text-xs flex flex-wrap items-center justify-between gap-3">
        <div><strong>{mentorStatus?.provider || 'AI service'}</strong><p className="text-slate-600 mt-1">{mentorStatus?.configuredModel || 'Checking configuration'} | {mentorStatus?.status.replaceAll('_',' ') || 'Checking status'}</p>
        {mentorStatus && !mentorStatus.available && <p className="mt-1 text-amber-800">AI replies are unavailable until the connection check succeeds. Your learning data is still available.</p>}</div>
        <button disabled={checking || mentorBusy} onClick={checkConnection} className="border rounded-lg px-3 py-2 disabled:opacity-50">{checking?'Checking connection...':'Check connection'}</button>
      </section>
      <CareerIntelligencePanel activityOnly/>
      <AgentGovernance/>
      <LearningMaterial/>
      {/* Main Advisor Workspace */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Chat Stream (Left 2 Cols) */}
        <div className="lg:col-span-2 bg-white rounded-2xl border border-slate-200/80 shadow-2xs flex flex-col h-[650px] overflow-hidden">
          {/* Message History */}
          <div role="log" aria-label="Mentor conversation" aria-live="polite" aria-busy={mentorBusy} className="flex-1 overflow-y-auto p-4 space-y-4 text-xs">
            {!mentorMessages.length && <div className="p-6 text-center text-slate-600"><h3 className="font-semibold text-slate-900">What would you like to learn?</h3><p className="mt-2">Ask a general question or choose a prompt below. Personal recommendations use your recorded evidence; claims are not treated as verified skills.</p></div>}
            {mentorMessages.length > 0 && (
              <motion.div
                variants={messageVariants}
                initial="hidden"
                animate="visible"
                className="space-y-4"
              >
                {mentorMessages.map((m) => {
                  const isUser = m.sender === 'user';
                  return (
                    <motion.div
                      key={m.id}
                      variants={messageItemVariants}
                      className={`flex items-start gap-3 ${isUser ? 'flex-row-reverse' : ''}`}
                    >
                      <div
                        className={`w-8 h-8 rounded-xl flex items-center justify-center shrink-0 text-xs font-bold ${
                          isUser
                            ? 'bg-slate-900 text-white'
                            : 'bg-teal-50 text-teal-800 border border-teal-200'
                        }`}
                      >
                        {isUser ? student.name.split(' ').filter(Boolean).map(n=>n[0]).slice(0,2).join('') : <Bot className="w-4 h-4 text-teal-700" />}
                      </div>

                      <div
                        className={`max-w-xl p-4 rounded-2xl space-y-2 ${
                          isUser
                            ? 'bg-slate-900 text-white rounded-tr-xs'
                            : 'bg-slate-50 text-slate-800 border border-slate-200/80 rounded-tl-xs'
                        }`}
                      >
                        <div className="flex items-center justify-between text-[10px] opacity-70">
                          <span>{isUser ? student.name : 'NexVora Copilot'}</span>
                          <span>{m.timestamp}</span>
                        </div>

                        <div className="whitespace-pre-line leading-relaxed text-xs">
                          {m.text}
                        </div>

                        {!isUser && m.agentRun && <details className="border-t pt-2 text-[11px]"><summary className="cursor-pointer font-semibold">Analysis sources and actions</summary><p className="mt-2">{(m.agentRun.agentsUsed ?? []).filter(n=>n!=='Supervisor').join(' · ')}</p><p>State {m.agentRun.stateVersion} · {m.agentRun.status}</p>{(m.agentRun.actions ?? []).map((a,i)=><p key={i}>{a.label} — {a.status}</p>)}</details>}
                        {!isUser && m.agentRun?.id?.startsWith('agt-') && <button className="text-xs font-semibold text-teal-700 underline" onClick={()=>{setActiveTab('agent-hub');window.history.replaceState({},'', '/agent-hub/runs?run='+encodeURIComponent(m.agentRun?.id || ""));}}>View live execution</button>}
                        {m.failed && <p className="text-amber-200">Reply failed. Your question is preserved in the composer for retry.</p>}
                        {!isUser && Boolean(m.citations?.length) && <div className="border-t pt-2"><p className="font-semibold">Sources</p>{m.citations?.map((citation,index)=><p key={citation.chunkId || index} className="mt-1 break-words">[{citation.documentId}] {citation.title} - {citation.source}</p>)}</div>}
                        {/* Cited Competencies & Evidence Badges */}
                        {!isUser && (m.relatedCompetencies || m.evidenceReferences) && (
                          <div className="pt-2 border-t border-slate-200/60 mt-2 space-y-1.5 text-[10px]">
                            {m.relatedCompetencies && m.relatedCompetencies.length > 0 && (
                              <div className="flex flex-wrap items-center gap-1">
                                <span className="font-semibold text-slate-500">Context skills:</span>
                                {m.relatedCompetencies.map((c, i) => (
                                  <button
                                    key={i}
                                    type="button"
                                    onClick={() => {setSelectedSkillId(c.id || null);setActiveTab('competencies');}}
                                    className="px-1.5 py-0.5 bg-white border border-slate-200 rounded font-mono text-teal-800 hover:underline"
                                  >
                                    {c.name} ({c.mastery}%)
                                  </button>
                                ))}
                              </div>
                            )}
                            {m.evidenceReferences && m.evidenceReferences.length > 0 && (
                              <div className="flex flex-wrap items-center gap-1">
                                <span className="font-semibold text-slate-500">Context evidence:</span>
                                {m.evidenceReferences.map((e, i) => (
                                  <span
                                    key={i}
                                    className="px-1.5 py-0.5 bg-teal-50 text-teal-800 border border-teal-200 rounded font-mono"
                                  >
                                    {e.title}
                                  </span>
                                ))}
                              </div>
                            )}
                            {m.suggestedAction && (
                              <div className="pt-1.5">
                                <button
                                  onClick={() => setActiveTab(m.suggestedAction!.tab)}
                                  className="px-2.5 py-1 bg-teal-700 hover:bg-teal-800 text-white font-bold rounded-lg text-xs transition flex items-center gap-1 cursor-pointer"
                                >
                                  <span>{m.suggestedAction.label}</span>
                                  <ArrowRight className="w-3 h-3" />
                                </button>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
</motion.div>
                   );
                })}
              </motion.div>
            )}
            {mentorBusy && (
              <motion.p 
                variants={loadingVariants}
                initial="hidden"
                animate="visible"
                role="status" 
                className="text-teal-700"
              >Preparing your answer...</motion.p>
            )}
            <div ref={endRef}/>
          </div>

          <motion.div
            variants={inputAreaVariants}
            initial="hidden"
            animate="visible"
            className="p-3 bg-white border-t border-slate-100 flex items-center gap-2"
          >
            <input
              aria-label="Message to AI mentor"
              maxLength={8000}
              type="text"
              value={inputMessage}
              data-undo="true" onChange={(e) => setInputMessage(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && !e.nativeEvent.isComposing && handleSend()}
              placeholder="Ask about competencies, prerequisites, career benchmark gaps..."
              className="flex-1 text-xs px-3.5 py-2.5 bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-teal-500 text-slate-900"
            />
            <button
              aria-label="Send message"
              onClick={() => handleSend()}
              disabled={mentorBusy || !inputMessage.trim()}
              className="p-2.5 bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white rounded-xl transition cursor-pointer shadow-xs"
            >
              <Send className="w-4 h-4" />
            </button>
</motion.div>
        </div>

        {/* Right Column: Grounding Context Telemetry */}
        <div className="space-y-4">
          <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs space-y-4 text-xs">
            <h3 className="font-bold text-slate-900 uppercase tracking-wide text-xs flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-teal-600" />
              <span>Grounded Knowledge Base</span>
            </h3>

            <div className="space-y-2.5">
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <span className="text-slate-400 font-medium">Target Role:</span>
                <div className="font-bold text-slate-900 text-sm mt-0.5">{targetCareer.title}</div>
                <div className="text-[11px] text-teal-700 font-semibold mt-0.5">
                  Current Readiness: {targetCareer.currentReadiness}%
                </div>
              </div>

              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <span className="text-slate-400 font-medium">Evidence Record Count:</span>
                <div className="font-bold text-slate-900 text-sm mt-0.5">
                  {evidenceItems.length} Evidence Records
                </div>
                <div className="text-[11px] text-slate-500 mt-0.5">
                  Includes claims and verified observations
                </div>
              </div>

              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                <span className="text-slate-400 font-medium">Active Bottlenecks:</span>
                <div className="font-bold text-amber-800 mt-0.5">{mission.title}</div>
                <div className="text-[11px] text-slate-500 mt-0.5">
                  {mission.reason}
                </div>
              </div>
            </div>

            <div className="pt-2 border-t border-slate-100 space-y-2">
              <button
                onClick={() => setActiveTab('assessments')}
                className="w-full py-2 bg-teal-50 hover:bg-teal-100 text-teal-800 border border-teal-200 rounded-xl font-bold transition flex items-center justify-center gap-1 cursor-pointer"
              >
                <span>Explore available assessments</span>
                <ArrowRight className="w-3 h-3" />
              </button>
              <button
                onClick={() => setActiveTab('projects')}
                className="w-full py-2 bg-slate-50 hover:bg-slate-100 text-slate-700 border border-slate-200 rounded-xl font-semibold transition flex items-center justify-center gap-1 cursor-pointer"
              >
                <span>Review recommended projects</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
