import { Brand } from './Brand';
import { ProfileAvatar } from '../profile/ProfileAvatar';
import { UndoRedoControls } from './UndoRedoControls';
import DesignButton from '../common/DesignButton';
import { useState } from 'react';
import { useAppState } from '../../lib/state/app-state';
import {
  Menu,
  Search,
  Bell,
  Sparkles,
  ChevronDown,
  RotateCcw,
  User,
  PlusCircle,
  ShieldCheck,
  FileUp,
  Layers,
  CheckCircle2
} from 'lucide-react';
import { NotificationDrawer } from './NotificationDrawer';
import { motion } from 'motion/react';
import './Header.css';

interface HeaderProps {
  onToggleMobileMenu: () => void;
}

const TAB_TITLES: Record<string, { title: string; subtitle: string }> = {
  coding: {title:'Coding Space',subtitle:'Practice, missions and evidence-backed progress'},
  dashboard: { title: 'Intelligence Command Center', subtitle: 'Living competency telemetry & priority actions' },
  profile: { title: 'Profile & Evidence Vault', subtitle: 'Verified proof artifacts, transcripts, and repository signals' },
  competencies: { title: 'Competency Intelligence', subtitle: 'Interactive skill mastery graph & dependency network' },
  careers: { title: 'Career Intelligence Explorer', subtitle: 'Market benchmark gap analysis & role readiness' },
  roadmap: { title: 'Adaptive Learning Roadmap', subtitle: 'State-driven milestone sequencing with prerequisite locks' },
  resources: { title: 'Resource Recommendations', subtitle: 'Curated learning pathways with grounded rationale' },
  assessments: { title: 'Adaptive Assessments', subtitle: 'Diagnostic testing & instantaneous competency delta evaluation' },
  projects: { title: 'Project Verification Engine', subtitle: 'Rubric-evaluated code submissions generating verifiable proof' },
  resume: { title: 'Resume Intelligence', subtitle: 'ATS claim extraction & evidence coverage gap analysis' },
  certificates: {title: 'My Certificates', subtitle: 'Course achievements, eligibility and public verification'},
  mentor: { title: 'AI Competency Mentor', subtitle: 'Grounded career advisor with evidence citations' }
};

export function Header({ onToggleMobileMenu }: HeaderProps) {
  const {
    logout,
    activeTab,
    student,
    targetCareer,
    careers,
    setTargetCareer,
    setCommandPaletteOpen,
    unreadNotificationCount,
    resetDemo,
    setOnboardingOpen,
    setActiveTab
  } = useAppState();

  const [notificationsOpen, setNotificationsOpen] = useState(false);
  const [careerDropdownOpen, setCareerDropdownOpen] = useState(false);
  const [profileMenuOpen, setProfileMenuOpen] = useState(false);

  const currentView = TAB_TITLES[activeTab] || { title: 'Career Intelligence', subtitle: 'Platform' };

  return (
    <>
      <header 
        className="sticky top-0 z-30 bg-white/90 backdrop-blur-md border-b border-slate-200 h-16 px-2 sm:px-4 lg:px-6 flex items-center justify-between transition-all header-premium"
        style={
          {
            '--header-bg': 'var(--color-bg-elevated)',
            '--header-border': 'var(--color-border-primary)',
            '--header-text-primary': 'var(--color-text-primary)',
            '--header-text-secondary': 'var(--color-text-secondary)',
            '--header-shadow': 'var(--shadow-sm)',
          } as React.CSSProperties
        }
      >
          {/* Left: Mobile Toggle & Page Title */}
        <div className="flex items-center gap-1 sm:gap-3">
          <DesignButton
            onClick={onToggleMobileMenu}
            className="p-2 -ml-1 text-slate-500 hover:text-slate-800 rounded-lg lg:hidden"
            aria-label="Open mobile menu"
            variant="secondary"
            size="sm"
          >
            <Menu className="w-5 h-5" />
          </DesignButton>

          <span className="lg:hidden"><Brand compact/></span>
          <div className="hidden lg:block">
            <h1 className="text-sm font-bold text-slate-900 tracking-tight leading-tight flex items-center gap-2">
              <span>{currentView.title}</span>
              <span className="text-[10px] font-semibold text-slate-400 font-mono hidden xl:inline">/</span>
              <span className="text-xs font-normal text-slate-600 hidden xl:inline">{currentView.subtitle}</span>
            </h1>
          </div>
        </div>

          {/* Center: Global Search Bar Trigger */}
        <div className="flex-1 max-w-md mx-3 hidden xl:block">
          <DesignButton
            onClick={() => setCommandPaletteOpen(true)}
            className="w-full flex items-center justify-between px-3 py-1.5 bg-slate-100/80 hover:bg-slate-100 border border-slate-200/80 rounded-xl text-xs text-slate-500 transition cursor-pointer group"
            motionVariant="hover"
            size="sm"
          >
            <div className="flex items-center gap-2">
              <Search className="w-3.5 h-3.5 text-slate-400 group-hover:text-slate-600" />
              <span>Search competencies, careers, projects...</span>
            </div>
            <kbd className="px-1.5 py-0.5 text-[10px] bg-white border border-slate-200 text-slate-400 rounded font-mono shadow-2xs">
              ⌘K
            </kbd>
          </DesignButton>
        </div>

        {/* Right: Actions, Career Switcher, Notifications, Avatar */}
        <div className="flex items-center gap-1 sm:gap-2">
          <UndoRedoControls />
          {/* Mobile search trigger */}
          <DesignButton
            onClick={() => setNotificationsOpen(!notificationsOpen)}
            className="p-2 text-slate-500 hover:text-slate-800 rounded-lg relative cursor-pointer"
            aria-label="Notifications"
            variant="secondary"
            size="sm"
          >
            <Bell className="w-4 h-4" />
            {unreadNotificationCount > 0 && (
              <span className="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
            )}
          </DesignButton>

          {/* Target Career Quick Switcher */}
          <div className="relative">
            <DesignButton
              onClick={() => setCareerDropdownOpen(!careerDropdownOpen)}
              className="flex items-center gap-2 px-2.5 py-1.5 bg-slate-50 hover:bg-slate-100 border border-slate-200 rounded-xl text-xs text-slate-800 font-medium transition cursor-pointer career-btn"
              variant="secondary"
              size="sm"
            >
              <div className="w-2 h-2 rounded-full bg-teal-500" />
              <span className="hidden sm:inline font-semibold">{targetCareer.title}</span>
              <span className="hidden min-[400px]:inline text-teal-700 font-bold bg-teal-50 px-1.5 py-0.5 rounded text-[11px]">
                {targetCareer.currentReadiness}%
              </span>
              <ChevronDown className="w-3.5 h-3.5 text-slate-400" />
            </DesignButton>

                {careerDropdownOpen && (
                  <>
                    <motion.div
                      className="fixed inset-0 z-40"
                      onClick={() => setCareerDropdownOpen(false)}
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      transition={{ duration: 0.2 }}
                    />
                    <motion.div
                      className="absolute right-0 mt-2 w-64 bg-white rounded-xl shadow-xl border border-slate-200 p-2 z-50 text-xs"
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                      transition={{ duration: 0.2, ease: 'easeOut' }}
                    >
                      <div className="px-2 py-1 font-bold text-slate-400 uppercase tracking-wider text-[10px]">
                        Switch Target Career
                      </div>
                      <div className="mt-1 space-y-1">
                        {careers.map((c) => {
                          const isSelected = c.id === targetCareer.id;
                          return (
                            <DesignButton
                              key={c.id}
                              onClick={() => {
                                setTargetCareer(c.id);
                                setCareerDropdownOpen(false);
                              }}
                              className={`w-full flex items-center justify-between p-2 rounded-lg text-left transition cursor-pointer ${
                                isSelected
                                  ? 'bg-teal-50 text-teal-900 font-semibold'
                                  : 'text-slate-700 hover:bg-slate-50'
                              }`}
                              variant="secondary"
                              size="sm"
                            >
                              <div className="truncate pr-2">
                                <div className="font-semibold text-slate-900 truncate">{c.title}</div>
                                <div className="text-[10px] text-slate-600">{c.category}</div>
                              </div>
                              <span className="text-[11px] font-bold text-teal-700 shrink-0">
                                {c.currentReadiness}%
                              </span>
                            </DesignButton>
                          );
                        })}
                      </div>
                    </motion.div>
                  </>
                )}
              </div>

              {/* Profile Avatar / Menu */}
              <div className="relative">
                <button
                  type="button"
                  onClick={() => setActiveTab('profile')}
                  className="rounded-full focus-visible:ring-2 focus-visible:ring-teal-600 cursor-pointer"
                  aria-label="View profile"
                >
                  <ProfileAvatar name={student.name} avatar={student.avatar} className="w-8 h-8" />
                </button>
              </div>
            </div>
          </header>

      {/* Notification Drawer Component */}

      <NotificationDrawer open={notificationsOpen} onClose={() => setNotificationsOpen(false)} />
    </>
  );
}
