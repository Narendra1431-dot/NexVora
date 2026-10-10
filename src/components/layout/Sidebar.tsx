import { Brand } from './Brand';
import { ProfileAvatar } from '../profile/ProfileAvatar';
import { useAppState } from '../../lib/state/app-state';
import { ChevronLeft, ChevronRight, Flame } from 'lucide-react';
import { NavigationIcon, type NavigationIconName } from './NavigationIcons';
import DesignButton from '../common/DesignButton';
import { motion } from 'motion/react';

interface SidebarProps {
  collapsed: boolean;
  setCollapsed: (val: boolean) => void;
  mobileOpen: boolean;
  setMobileOpen: (val: boolean) => void;
}

const NAV_ITEMS: {id: NavigationIconName; label: string; badge?: string}[] = [
  { id: 'dashboard', label: 'Dashboard', badge: 'Live' },
  { id: 'profile', label: 'Profile & Vault' },
  { id: 'competencies', label: 'Competencies', badge: 'Graph' },
  { id: 'careers', label: 'Career Intelligence' },
  { id: 'roadmap', label: 'Learning Roadmap', badge: 'Adaptive' },
  { id: 'resources', label: 'Resources' },
  { id: 'coding', label: 'Coding Space' },
  { id: 'assessments', label: 'Assessments', badge: 'Interactive' },
  { id: 'projects', label: 'Projects & Verify' },
  { id: 'resume', label: 'Resume Intelligence', badge: 'ATS' },
  { id: 'certificates', label: 'My Certificates' },
  { id: 'agent-hub', label: 'Agent Hub' },
  { id: 'mentor', label: 'AI Mentor', badge: 'Grounded' }
];

export function Sidebar({ collapsed, setCollapsed, mobileOpen, setMobileOpen }: SidebarProps) {
  const { activeTab, setActiveTab, student, targetCareer } = useAppState();

  const handleNav = (id: string) => {
    setActiveTab(id);
    setMobileOpen(false);
  };

  return (
    <>
      {/* Mobile backdrop */}
      {mobileOpen && (
        <motion.div
          className="fixed inset-0 bg-slate-900/50 backdrop-blur-xs z-40 lg:hidden"
          onClick={() => setMobileOpen(false)}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
        />
      )}

      <aside
        className={`fixed lg:sticky top-0 left-0 z-40 h-screen bg-white border-r border-slate-200 transition-all duration-300 ease-in-out flex flex-col justify-between ${
          collapsed ? 'w-20' : 'w-64'
        } ${mobileOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'}`}
      >
        {/* Brand & collapse trigger */}
        <div>
          <div className={`h-16 flex items-center justify-between border-b border-slate-100 ${collapsed?'px-1':'px-3'}`}>
            <Brand symbolOnly={collapsed}/>

            <DesignButton
              onClick={() => setCollapsed(!collapsed)}
              className="hidden lg:flex p-1.5 rounded-lg text-slate-400 hover:text-slate-700 hover:bg-slate-100 transition"
              aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
              variant="secondary"
              size="sm"
            >
              {collapsed ? <ChevronRight className="w-4 h-4" /> : <ChevronLeft className="w-4 h-4" />}
            </DesignButton>
          </div>

          {/* Target Career Quick Badge (when expanded) */}
          {!collapsed && (
            <div className="mx-3 mt-3 p-3 bg-slate-50 border border-slate-200/80 rounded-xl">
              <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
                <span>Target Objective</span>
                <span className="font-semibold text-teal-700 bg-teal-50 px-1.5 py-0.5 rounded text-[11px] border border-teal-200">
                  {targetCareer.currentReadiness}% Ready
                </span>
              </div>
              <div className="text-xs font-bold text-slate-900 truncate">{targetCareer.title}</div>
              <div className="w-full bg-slate-200 h-1.5 rounded-full mt-2 overflow-hidden">
                <motion.div
                  className="bg-teal-600 h-full rounded-full transition-all duration-500"
                  style={{ width: `${targetCareer.currentReadiness}%` }}
                  initial={{ width: 0 }}
                  animate={{ width: `${targetCareer.currentReadiness}%` }}
                  transition={{ duration: 0.5, ease: 'easeOut' }}
                />
              </div>
            </div>
          )}

          {/* Navigation Links */}
          <nav className="p-2.5 space-y-1 mt-2 overflow-y-auto max-h-[calc(100vh-280px)] no-scrollbar">
            {NAV_ITEMS.map((item) => {
              const isActive = activeTab === item.id;
              return (
                <DesignButton
                  key={item.id}
                  id={`nav-${item.id}`}
                  onClick={() => handleNav(item.id)}
                  className={`w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-xs font-medium transition group cursor-pointer focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-teal-600 focus-visible:ring-offset-2 ${
                    isActive
                      ? 'bg-teal-50 text-teal-900 font-semibold border border-teal-200/80 shadow-xs'
                      : 'text-slate-600 hover:bg-slate-50 hover:text-slate-900'
                  }`}
                  title={collapsed ? item.label : undefined}
                  aria-label={item.label}
                  aria-current={isActive ? 'page' : undefined}
                  motionVariant="buttonPress"
                  size="sm"
                >
                  <span className="relative flex h-4 w-4 shrink-0 items-center justify-center">
                    <span aria-hidden="true" className={`absolute -inset-1.5 rounded-lg ${isActive ? 'bg-teal-100/80 ring-1 ring-inset ring-teal-300/40' : 'group-hover:bg-slate-100'}`} />
                    <NavigationIcon name={item.id} className={`relative h-4 w-4 ${isActive ? 'text-teal-800' : 'text-slate-500 group-hover:text-slate-800'}`} />
                  </span>
                  {!collapsed && (
                    <div className="flex-1 flex items-center justify-between min-w-0">
                      <span className="truncate">{item.label}</span>
                      {item.badge && (
                        <span
                          className={`text-[10px] px-1.5 py-0.5 rounded-md font-medium tracking-wide ${
                            isActive
                              ? 'bg-teal-100 text-teal-800'
                              : 'bg-slate-100 text-slate-500 group-hover:bg-slate-200'
                          }`}
                        >
                          {item.badge}
                        </span>
                      )}
                    </div>
                  )}
                </DesignButton>
              );
            })}
          </nav>
        </div>

        {/* Bottom Student Profile Card */}
        <div className="p-3 border-t border-slate-100">
          <motion.div
            onClick={() => handleNav('profile')}
            className={`flex items-center gap-2.5 p-2 rounded-xl hover:bg-slate-50 transition cursor-pointer ${
              collapsed ? 'justify-center' : ''
            }`}
            whileHover={{ scale: 1.02, x: 2 }}
            whileTap={{ scale: 0.98 }}
            transition={{ duration: 0.2 }}
          >
            <ProfileAvatar name={student.name} avatar={student.avatar} className="h-8 w-8"/>
            {!collapsed && (
              <div className="min-w-0 flex-1">
                <div className="text-xs font-semibold text-slate-900 truncate">{student.name}</div>
                <div className="text-[11px] text-slate-500 flex items-center gap-1">
                  <Flame className="w-3 h-3 text-amber-500 fill-amber-500" />
                  <span>{student.streakDays} day streak</span>
                </div>
              </div>
            )}
          </motion.div>
        </div>
      </aside>
    </>
  );
}
