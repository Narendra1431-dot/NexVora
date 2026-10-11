import { Brand } from '../../components/layout/Brand';
import { useEditHistory } from './edit-history';
import type { ConceptObservation } from '../../components/competencies/ConceptObservations';
import { AppStateContext } from './app-context';
import React, { useContext, useRef, useState, useEffect, useMemo, ReactNode } from 'react';
import {
  StudentProfile,
  CompetencyNode,
  EvidenceItem,
  CareerRole,
  RoadmapMilestone,
  LearningResource,
  AssessmentItem,
  ProjectItem,
  ResumeAnalysis,
  ActivityItem,
  NotificationItem,
  MentorMessage,
  NodeStateType
} from '../../types';
export interface Toast {
  id: string;
  title: string;
  message: string;
  type: 'success' | 'info' | 'warning';
}

export interface AppStateContextType {
  conceptObservations: ConceptObservation[];
  relationships: {nodes:{id:string;kind:string;sourceId:string;label:string}[];edges:{id:string;type:string;source:string;target:string;reason:string}[]};
  intelligence: {trainingData:string;advisoryOnly:boolean;limitation:string;learningRisk:{score:number;level:string;modelVersion:string};evidenceStrength:{evidenceId:string;label:string}[]};
  mission: {title:string;description:string;reason:string;tab:string;estimatedEffort:string};
  student: StudentProfile;
  competencyNodes: CompetencyNode[];
  initialBaselineNodes: CompetencyNode[];
  evidenceItems: EvidenceItem[];
  careers: CareerRole[];
  targetCareer: CareerRole;
  roadmap: RoadmapMilestone[];
  resources: LearningResource[];
  assessments: AssessmentItem[];
  projects: ProjectItem[];
  resumeAnalysis: ResumeAnalysis;
  activities: ActivityItem[];
  notifications: NotificationItem[];
  mentorMessages: MentorMessage[];
  mentorError: string;
  mentorBusy: boolean;
  mentorStatus: {provider:string;status:string;available:boolean;configuredModel:string} | null;
  checkMentorStatus: (probe?:boolean) => Promise<void>;
  unreadNotificationCount: number;

  // Navigation & UI States
  activeTab: string;
  setActiveTab: (tab: string) => any;
  catalogSelection: { tab: string; id: string } | null;
  setCatalogSelection: (selection: { tab: string; id: string } | null) => void;
  selectedSkillId: string | null;
  setSelectedSkillId: (skillId: string | null) => any;
  selectedCareerId: string;
  setSelectedCareerId: (careerId: string) => any;
  graphComparisonMode: 'current' | 'before';
  setGraphComparisonMode: (mode: 'current' | 'before') => any;
  commandPaletteOpen: boolean;
  setCommandPaletteOpen: (open: boolean) => any;
  onboardingOpen: boolean;
  setOnboardingOpen: (open: boolean) => any;

  // Hackathon Guided Demo State
  demoStep: number;
  setDemoStep: (step: number) => any;
  isDemoBarVisible: boolean;
  setIsDemoBarVisible: (visible: boolean) => any;

  refreshWorkspace: () => Promise<unknown>;
  saveProfile: (profile: Partial<StudentProfile>) => Promise<boolean>;
  logout: () => void;
  loadPendingReviews: () => Promise<any[]>;
  submitReview: (id:string, review:any) => Promise<any>;
  // Actions
  setTargetCareer: (careerId: string) => any;
  completeAssessment: (assessmentId: string, answers: Record<string, any>, score: number, accuracy: number) => any;
  verifyProject: (projectId: string, submissionDetails: { githubUrl: string; description: string }) => any;
  addEvidence: (evidence: Omit<EvidenceItem, 'id' | 'date'>) => any;
  deleteEvidence: (evidenceId: string) => any;
  updateEvidence: (item: EvidenceItem) => any;
  completeResource: (resourceId: string) => any;
  toggleBookmarkResource: (resourceId: string) => any;
  advanceMilestone: (milestoneId: string) => any;
  sendMentorMessage: (prompt: string) => any;
  uploadResume: (file: File | string) => any;
  markNotificationRead: (id: string) => any;
  markAllNotificationsRead: () => any;
  resetDemo: () => any;
  triggerHackathonStep: (step: number) => any;

  // Toasts
  toasts: Toast[];
  showToast: (title: string, message: string, type?: 'success' | 'info' | 'warning') => any;
  dismissToast: (id: string) => any;
}


// Context lives separately to preserve identity during development refresh.
export function AppStateProvider({ children }: { children: ReactNode }) {
  const [snapshot, setSnapshot] = useState<any>(null);
  const [token, setToken] = useState(() =>
    typeof window === 'undefined' ? '' : window.sessionStorage.getItem('plcip_token') || ''
  );
  const [error, setError] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [register, setRegister] = useState(false);
  const editHistory=useEditHistory();
  useEffect(()=>{editHistory?.clear();},[token,editHistory]);
  const [busy, setBusy] = useState(false);
  const [activeTab, setTab] = useState(() => {
    if (typeof window === 'undefined') return 'dashboard';
    return window.location.pathname.startsWith('/agent-hub')
      ? 'agent-hub'
      : window.location.pathname.startsWith('/coding-space')
        ? 'coding'
        : 'dashboard';
  });
  const setActiveTab=(tab:string)=>{setTab(tab);if(tab==='agent-hub'){if(!window.location.pathname.startsWith('/agent-hub'))window.history.pushState({},'', '/agent-hub');return;}if(window.location.pathname.startsWith('/agent-hub'))window.history.pushState({},'', '/');if(tab==='coding'){if(!window.location.pathname.startsWith('/coding-space'))window.history.pushState({},'', '/coding-space');}else if(window.location.pathname.startsWith('/coding-space'))window.history.pushState({},'', '/');};
  useEffect(()=>{const back=()=>setTab(window.location.pathname.startsWith('/agent-hub')?'agent-hub':window.location.pathname.startsWith('/coding-space')?'coding':'dashboard');window.addEventListener('popstate',back);return()=>window.removeEventListener('popstate',back);},[]);
  const [catalogSelection, setCatalogSelection] = useState<{tab:string;id:string}|null>(null);
  const [selectedSkillId, setSelectedSkillId] = useState<string | null>(null);
  const [selectedCareerId, setSelectedCareerId] = useState('career-ai-engineer');
  const [graphComparisonMode, setGraphComparisonMode] = useState<'current' | 'before'>('current');
  const [commandPaletteOpen, setCommandPaletteOpen] = useState(false);
  const [onboardingOpen, setOnboardingOpen] = useState(false);
  const [demoStep, setDemoStep] = useState(1);
  const [isDemoBarVisible, setIsDemoBarVisible] = useState(true);
  const [toasts, setToasts] = useState<Toast[]>([]);
  const mentorLock = useRef(false);
  const [mentorBusy,setMentorBusy] = useState(false);
  const [mentorStatus,setMentorStatus] = useState<AppStateContextType['mentorStatus']>(null);
  const [mentorError,setMentorError] = useState('');
  const [mentorMessages, setMentorMessages] = useState<MentorMessage[]>([]);
  const [baseline, setBaseline] = useState<CompetencyNode[]>([]);
  const dismissToast = (id: string) => setToasts(p => p.filter(t => t.id !== id));
  const showToast = (title: string, message: string, type: Toast['type'] = 'info') => {
    const id = crypto.randomUUID(); setToasts(p => [...p, {id, title, message, type}]);
    setTimeout(() => dismissToast(id), 6000);
  };
  const api = async (path: string, body?: any, method = 'POST') => {
    const headers: Record<string,string> = {Authorization: `Bearer ${token}`};
    if (!(body instanceof FormData)) headers['Content-Type'] = 'application/json';
    const r = await fetch('/api/v1' + path, {method, headers, body: body === undefined ? undefined : body instanceof FormData ? body : JSON.stringify(body)});
    const contentType = r.headers.get('content-type') || '';
    if (!contentType.includes('application/json')) {
      // Proxy/edge returned an HTML error page or empty body — do not treat as API data.
      throw new Error(r.ok ? 'Unexpected non-JSON response from server.' : `Request failed (${r.status}). Please try again.`);
    }
    const data = await r.json().catch(() => ({detail: 'Unexpected non-JSON response from server.'}));
    if (!r.ok) throw new Error(typeof data.detail === 'string' ? data.detail : Array.isArray(data.detail) ? data.detail.map((d: any) => d.msg).join('; ') : 'Request failed. Please try again.');
    return data;
  };
  const refresh = async () => {
    const data = await api('/state', undefined, 'GET');
    setSnapshot(data); setBaseline(p => data.baselineNodes?.length ? data.baselineNodes : p.length ? p : data.competencies); return data;
  };
  useEffect(() => { if(token) refresh().catch(e => setError(e.message)); }, [token]);
  useEffect(()=>{if(!token)return;const controller=new AbortController();
    fetch('/api/v1/agent/history',{headers:{Authorization:'Bearer '+token},signal:controller.signal}).then(r=>r.ok?r.json():[]).then(rows=>{
      if(!controller.signal.aborted&&Array.isArray(rows))setMentorMessages(current=>current.length?current:rows.map(m=>({id:m.id,sender:m.role,timestamp:new Date(m.createdAt).toLocaleTimeString(),text:m.content})));
    }).catch(()=>{});return()=>controller.abort();
  },[token]);
  const login = async (demo = false) => {
    setBusy(true); setError('');
    try {
      const data = await api(demo ? '/auth/demo' : register ? '/auth/register' : '/auth/login', demo ? {} : {email,password,name});
      sessionStorage.setItem('plcip_token', data.token); setToken(data.token); setBaseline([]);
      setOnboardingOpen(register && !demo);
    } catch(e) { setError((e as Error).message); } finally {setBusy(false);}
  };
  const logout = () => {editHistory?.clear();sessionStorage.removeItem('plcip_token'); setToken(''); setSnapshot(null); setMentorMessages([]); setBaseline([]); setError('');};
  const mutate = async (path: string, body?: any, method = 'POST') => {
    if(editHistory?.getSnapshot().busy)return null;
    try { const result = await api(path, body, method); const state = await refresh(); showToast('Saved', 'Student evidence and derived state synchronized.', 'success'); return {...result,state}; }
    catch(e) {showToast('Action failed', (e as Error).message, 'warning'); return null;}
  };
  const restoreProfile = async (expected:Record<string,unknown>, replacement:Record<string,unknown>) => {
    if(sessionStorage.getItem('plcip_token')!==token)throw new Error('This edit belongs to a previous session.');
    const current=await api('/state',undefined,'GET');
    if(Object.keys(expected).some(key=>JSON.stringify(current.profile[key])!==JSON.stringify(expected[key])))throw new Error('These profile fields changed elsewhere. Refresh before editing them again.');
    await api('/profile',replacement,'PATCH');await refresh();
  };
  const setTargetCareer = async (careerId: string) => {
    const previous=snapshot?.profile.targetCareerId;
    const r=await mutate('/career/target', {careerId});
    if(r){setSelectedCareerId(careerId);
      if(previous&&previous!==careerId){
        const restore=async(expected:string,next:string)=>{
          if(sessionStorage.getItem('plcip_token')!==token)throw new Error('This edit belongs to a previous session.');
          const current=await api('/state',undefined,'GET');
          if(current.profile.targetCareerId!==expected)throw new Error('Your target career changed elsewhere. Refresh before editing again.');
          await api('/career/target',{careerId:next});await refresh();setSelectedCareerId(next);
        };
        editHistory?.add({label:'Target career and roadmap',undo:()=>restore(careerId,previous),redo:()=>restore(previous,careerId)});
      }
    }return r;
  };
  const completeAssessment = (id: string, answers: Record<string,any>) => mutate(`/assessments/${id}/attempts`, {answers});
  const verifyProject = (id: string, details: any) => mutate(`/projects/${id}/submissions`, details);
  const addEvidence = (e: any) => mutate('/evidence', e);
  const deleteEvidence = (id: string) => mutate(`/evidence/${id}`, undefined, 'DELETE');
  const updateEvidence = (e: EvidenceItem) => mutate(`/evidence/${e.id}`, {text: e.summary || e.title}, 'PATCH');
  const completeResource = (id: string) => mutate(`/resources/${id}/action`, {completed:true});
  const toggleBookmarkResource = (id: string) => mutate(`/resources/${id}/action`, {bookmarked: !snapshot.resources.find((r:any)=>r.id===id)?.bookmarked});
  const advanceMilestone = (id: string) => mutate(`/roadmap/${id}/advance`, {});
  const markNotificationRead = (id: string) => mutate(`/notifications/${id}/read`, {});
  const markAllNotificationsRead = () => mutate('/notifications/read-all', {});
  const resetDemo = async () => {const r = await mutate('/demo/reset', {}); if(r) {editHistory?.clear();setBaseline(r.state.competencies); setMentorMessages([]); setActiveTab('dashboard');}};
  const saveProfile = async (profile: Partial<StudentProfile>) => {
    const before=Object.fromEntries(Object.keys(profile).map(key=>[key,snapshot.profile[key]]));
    const result=await mutate('/profile',profile,'PATCH');if(!result)return false;
    const after=Object.fromEntries(Object.keys(profile).map(key=>[key,result.state.profile[key]]));
    if(JSON.stringify(before)!==JSON.stringify(after))editHistory?.add({label:'Saved profile',undo:()=>restoreProfile(after,before),redo:()=>restoreProfile(before,after)});
    return true;
  };
  const uploadResume = async (file: File | string) => {
    const form = new FormData();
    if(typeof file !== 'string') form.append('file',file);
    let queued=false;
    try {const runtime=await api('/intelligence/status',undefined,'GET');queued=runtime.workers==='healthy'&&runtime.jobQueue==='healthy';} catch {}
    if(queued&&typeof file!=='string')form.append('documentType','resume');
    const result = await api(typeof file === 'string'?'/resume/analyze':queued?'/documents/upload':'/documents',typeof file === 'string'?{text:file,background:queued}:form);
    if(result.jobId){window.dispatchEvent(new Event('intelligence-job'));return result;}
    if(!result.state) throw new Error('Analysis was saved but the server returned no updated state. Reload to retrieve it.');
    setSnapshot(result.state);
    return result;
  };
  const checkMentorStatus = async (probe=false) => {
    try {const status=await api(probe?'/mentor/check':'/mentor/status', probe?{}:undefined, probe?'POST':'GET');setMentorStatus(status);if(probe && status.available)setMentorError('');}
    catch(e) {setMentorError((e as Error).message);}
  };
  const sendMentorMessage = async (prompt: string) => {
    if(mentorLock.current || !prompt.trim()) return false;
    mentorLock.current=true; setMentorBusy(true); setMentorError('');
    const timestamp = new Date().toLocaleTimeString();
    const id=crypto.randomUUID();
    setMentorMessages(p => [...p, {id, sender:'user', timestamp, text:prompt}]);
    try {
      const data = await api('/agent/chat', {message:prompt, requestId:id, history: mentorMessages.filter(m=>!m.failed).slice(-20).map(m => ({role:m.sender, content:m.text}))});
      setMentorMessages(p => [...p, {id:crypto.randomUUID(), sender:'assistant', timestamp:new Date().toLocaleTimeString(), text:data.answer, agentRun:data.agentRun, citations:data.sources, relatedCompetencies:data.relatedSkills?.slice(0,4), evidenceReferences:data.evidence?.slice(0,3), suggestedAction:data.suggestedActions?.[0] ? {label:data.suggestedActions[0].title,tab:data.suggestedActions[0].tab} : undefined}]);
      if(data.actionsPerformed?.length) {
        try {await refresh();} catch {showToast('Refresh needed','The copilot action completed. Refresh the workspace to see its latest state.','warning');}
      }
      return true;
    } catch(e) {
      setMentorMessages(p=>p.map(m=>m.id===id?{...m,failed:true}:m));
      setMentorError((e as Error).message); return false;
    } finally {mentorLock.current=false;setMentorBusy(false);void checkMentorStatus();}
  };
  const triggerHackathonStep = (step: number) => {setDemoStep(step); setActiveTab(['resume','assessments','careers','competencies','careers','roadmap','resources','assessments','projects','dashboard'][step-1] || 'dashboard');};
  if(token && !snapshot && !error) return <main className="min-h-screen flex flex-col gap-4 items-center justify-center bg-slate-50"><p role="status">Loading your workspace...</p><button onClick={logout} className="underline">Clear session and retry</button></main>;
  if(!token || !snapshot) return <main className="min-h-screen bg-slate-50 flex items-center justify-center p-6"><form className="w-full max-w-md bg-white border rounded-2xl p-8 space-y-4" onSubmit={e=>{e.preventDefault(); login();}}><Brand/><h1 className="text-2xl font-bold">Learning & Career Intelligence</h1><p>Sign in to your evidence-driven learning workspace.</p>{error && <p role="alert" className="text-red-700">{error}</p>}{register && <input aria-label="Name" placeholder="Name" required value={name} onChange={e=>setName(e.target.value)} className="border p-3 w-full rounded"/>}<input aria-label="Email" type="email" placeholder="Email" required value={email} onChange={e=>setEmail(e.target.value)} className="border p-3 w-full rounded"/><input aria-label="Password" type="password" placeholder="Password" required minLength={register?8:1} value={password} onChange={e=>setPassword(e.target.value)} className="border p-3 w-full rounded"/><button disabled={busy} className="bg-teal-700 text-white p-3 rounded w-full">{register?'Create account':'Sign in'}</button><button type="button" onClick={()=>setRegister(!register)} className="underline">{register?'Use existing account':'Create an account'}</button><button type="button" disabled={busy} onClick={()=>login(true)} className="border p-3 rounded w-full">Explore seeded demo</button>{token && <button type="button" onClick={logout}>Clear session and retry</button>}</form></main>;
  const student = snapshot.profile;
  const competencyNodes = snapshot.competencies;
  const evidenceItems = snapshot.evidence;
  const careers = snapshot.careers;
  const targetCareer = careers.find((c:CareerRole)=>c.id===student.targetCareerId) || careers[0];
  const roadmap = snapshot.milestones;
  const resources = snapshot.resources;
  const assessments = snapshot.assessments;
  const projects = snapshot.projects;
  const resumeAnalysis = {fileName:'No resume uploaded', uploadedAt:'', resumeScore:0, atsCompatibilityScore:0, sectionsDetected:[], extractedSkillsCount:0, verifiedClaimsCount:0, unsupportedClaimsCount:0, careerAlignmentScore:0, evidenceCoveragePercent:0, claims:[], missingSkillsForTarget:[], weakClaims:[], suggestedImprovements:[], recommendedProofProject:'', ...snapshot.resume};
  const activities = snapshot.events;
  const notifications = snapshot.notifications;
  const unreadNotificationCount = notifications.filter((n:NotificationItem)=>!n.read).length;
  return (
    <AppStateContext.Provider
      value={{
        loadPendingReviews:()=>api("/reviews/pending",undefined,"GET"),
        submitReview:(id,review)=>mutate(`/submissions/${id}/review`,review),
        conceptObservations:snapshot.concepts || [],
        relationships:snapshot.relationships || {nodes:[],edges:[]},
        intelligence:snapshot.intelligence,
        mission:snapshot.mission,
        refreshWorkspace: refresh, saveProfile, logout,
        student,
        competencyNodes,
        initialBaselineNodes: baseline,
        evidenceItems,
        careers,
        targetCareer,
        roadmap,
        resources,
        assessments,
        projects,
        resumeAnalysis,
        activities,
        notifications,
        mentorMessages, mentorError, mentorBusy, mentorStatus, checkMentorStatus,
        unreadNotificationCount,

        activeTab,
        setActiveTab,
        catalogSelection,
        setCatalogSelection,
        selectedSkillId,
        setSelectedSkillId: (id) => {setCatalogSelection(null); setSelectedSkillId(id);},
        selectedCareerId,
        setSelectedCareerId,
        graphComparisonMode,
        setGraphComparisonMode,
        commandPaletteOpen,
        setCommandPaletteOpen,
        onboardingOpen,
        setOnboardingOpen,

        demoStep,
        setDemoStep,
        isDemoBarVisible,
        setIsDemoBarVisible,

        setTargetCareer,
        completeAssessment,
        verifyProject,
        addEvidence,
        deleteEvidence,
        updateEvidence,
        completeResource,
        toggleBookmarkResource,
        advanceMilestone,
        sendMentorMessage,
        uploadResume,
        markNotificationRead,
        markAllNotificationsRead,
        resetDemo,
        triggerHackathonStep,

        toasts,
        showToast,
        dismissToast
      }}
    >
      {student.isDemo && <div className="bg-slate-100 text-slate-700 text-xs text-center p-2">Seeded demo persona: historical evidence and profile details are synthetic examples. New actions are processed by the live backend.</div>}
      {children}
    </AppStateContext.Provider>
  );
}

export function useAppState() {
  const context = useContext(AppStateContext);
  if (!context) {
    throw new Error('useAppState must be used within an AppStateProvider');
  }
  return context;
}
