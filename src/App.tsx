import { AssistantWidget } from './components/assistant/AssistantWidget';
import { CopilotIntegration } from './copilot/CopilotIntegration';
import { LoginSplash } from './components/layout/LoginSplash';
import { EditHistoryProvider } from './lib/state/edit-history';
import { useState, lazy, Suspense } from 'react';
import { AppStateProvider, useAppState } from './lib/state/app-state';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import {BackgroundActivity} from './components/intelligence/BackgroundActivity';
import { CommandPalette } from './components/layout/CommandPalette';
import { ToastContainer } from './components/common/ToastContainer';
import { HackathonDemoBar } from './components/layout/HackathonDemoBar';
import { OnboardingWizard } from './components/onboarding/OnboardingWizard';

const MyCertificates = lazy(()=>import('./components/certificates/MyCertificates').then(m=>({default:m.MyCertificates})));
const PublicCertificate = lazy(()=>import('./components/certificates/PublicCertificate').then(m=>({default:m.PublicCertificate})));

const CodingSpace = lazy(()=>import('./components/coding/CodingSpace').then(m=>({default:m.CodingSpace})));
// View Components
const CommandCenter = lazy(()=>import('./components/dashboard/CommandCenter').then(m=>({default:m.CommandCenter})));
const ProfileEvidenceVault = lazy(()=>import('./components/profile/ProfileEvidenceVault').then(m=>({default:m.ProfileEvidenceVault})));
const CompetencyGraph = lazy(()=>import('./components/competencies/CompetencyGraph').then(m=>({default:m.CompetencyGraph})));
const CareerIntelligence = lazy(()=>import('./components/career/CareerIntelligence').then(m=>({default:m.CareerIntelligence})));
const AdaptiveRoadmap = lazy(()=>import('./components/roadmap/AdaptiveRoadmap').then(m=>({default:m.AdaptiveRoadmap})));
const ResourceCenter = lazy(()=>import('./components/resources/ResourceCenter').then(m=>({default:m.ResourceCenter})));
const AssessmentEngine = lazy(()=>import('./components/assessments/AssessmentEngine').then(m=>({default:m.AssessmentEngine})));
const ProjectVerification = lazy(()=>import('./components/projects/ProjectVerification').then(m=>({default:m.ProjectVerification})));
const ResumeIntelligence = lazy(()=>import('./components/resume/ResumeIntelligence').then(m=>({default:m.ResumeIntelligence})));
const AiMentor = lazy(()=>import('./components/mentor/AiMentor').then(m=>({default:m.AiMentor})));
const AgentHub = lazy(()=>import('./components/intelligence/AgentHub').then(m=>({default:m.AgentHub})));

function MainAppContent() {
  const { activeTab, catalogSelection, onboardingOpen, setOnboardingOpen } = useAppState();
  const [collapsed, setCollapsed] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-900 font-sans selection:bg-teal-100 selection:text-teal-900">
      {/* Interactive Hackathon Demo Stepper Bar */}
      <HackathonDemoBar />

      <div className="flex flex-1 relative">
        {/* Responsive Collapsible Sidebar */}
        <Sidebar
          collapsed={collapsed}
          setCollapsed={setCollapsed}
          mobileOpen={mobileOpen}
          setMobileOpen={setMobileOpen}
        />

        {/* Main Content Area */}
        <div className="flex-1 flex flex-col min-w-0">
          {/* Header */}
          <Header onToggleMobileMenu={() => setMobileOpen(!mobileOpen)} />
          <BackgroundActivity />

          {/* Page Container */}
          <main role="main" className="flex-1 p-4 md:p-6 w-full">
            <Suspense fallback={<p role="status">Loading workspace...</p>}>
            {activeTab === 'coding' && <CodingSpace />}
            {activeTab === 'certificates' && <MyCertificates />}
            {activeTab === 'dashboard' && <CommandCenter />}
            {activeTab === 'profile' && <ProfileEvidenceVault />}
            {activeTab === 'competencies' && <CompetencyGraph />}
            {activeTab === 'careers' && <CareerIntelligence />}
            {activeTab === 'roadmap' && <AdaptiveRoadmap />}
            {activeTab === 'resources' && <ResourceCenter key={catalogSelection?.id} />}
            {activeTab === 'assessments' && <AssessmentEngine key={catalogSelection?.id} />}
            {activeTab === 'projects' && <ProjectVerification key={catalogSelection?.id} />}
            {activeTab === 'resume' && <ResumeIntelligence />}
            {activeTab === 'mentor' && <AiMentor />}
            {activeTab === 'agent-hub' && <AgentHub />}
            </Suspense>
          </main>
        </div>
      </div>

      {/* Global Modals & Notifications */}
      <CommandPalette />
      <OnboardingWizard open={onboardingOpen} onClose={() => setOnboardingOpen(false)} />
      <ToastContainer />
      <AssistantWidget />
    </div>
  );
}

export default function App() {
  const path = typeof window !== 'undefined' ? window.location.pathname : '/';
  if(path.startsWith('/certificate/')) {
    const id=path.slice('/certificate/'.length).replace(/\/$/,'');
    return <Suspense fallback={<p role="status">Loading certificate...</p>}><PublicCertificate id={id}/></Suspense>;
  }
  return (
    <LoginSplash><EditHistoryProvider><AppStateProvider>
      <CopilotIntegration>
        <MainAppContent />
      </CopilotIntegration>
    </AppStateProvider></EditHistoryProvider></LoginSplash>
  );
}
