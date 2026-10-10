import { NavigationIcon } from './NavigationIcons';
import { useModalDialog } from '../../lib/hooks/use-modal-dialog';
import { useState, useEffect, useRef } from 'react';
import { useAppState } from '../../lib/state/app-state';
import { Search, X, ArrowRight } from 'lucide-react';
import { motion, AnimatePresence } from 'motion/react';

export function CommandPalette() {
  const {
    commandPaletteOpen,
    setCommandPaletteOpen,
    competencyNodes,
    careers,
    resources,
    assessments,
    projects,
    setActiveTab,
    setCatalogSelection,
    setSelectedSkillId,
    setTargetCareer
  } = useAppState();

  const [query, setQuery] = useState('');
  const inputRef = useRef<HTMLInputElement>(null);
  const dialogRef = useModalDialog(commandPaletteOpen,()=>setCommandPaletteOpen(false));

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
        e.preventDefault();
        setCommandPaletteOpen(!commandPaletteOpen);
      }
      if (e.key === 'Escape' && commandPaletteOpen) {
        setCommandPaletteOpen(false);
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [commandPaletteOpen, setCommandPaletteOpen]);

  useEffect(() => {
    if (!commandPaletteOpen) setQuery('');
  }, [commandPaletteOpen]);

  if (!commandPaletteOpen) return null;

  const q = query.toLowerCase().trim();

  const matchedSkills = competencyNodes
    .filter((s) => s.name.toLowerCase().includes(q) || s.domain.toLowerCase().includes(q))
    .slice(0, 4);

  const matchedCareers = careers
    .filter((c) => c.title.toLowerCase().includes(q) || c.category.toLowerCase().includes(q))
    .slice(0, 3);

  const matchedResources = resources
    .filter((r) => r.title.toLowerCase().includes(q) || r.skillName.toLowerCase().includes(q))
    .slice(0, 3);

  const matchedAssessments = assessments
    .filter((a) => a.title.toLowerCase().includes(q) || a.skillName.toLowerCase().includes(q))
    .slice(0, 3);

  const matchedProjects = projects
    .filter((p) => p.title.toLowerCase().includes(q))
    .slice(0, 3);

  const handleSelectSkill = (skillId: string) => {
    setSelectedSkillId(skillId);
    setActiveTab('competencies');
    setCommandPaletteOpen(false);
  };

  const handleSelectCareer = (careerId: string) => {
    setTargetCareer(careerId);
    setActiveTab('careers');
    setCommandPaletteOpen(false);
  };

  const handleSelectResource = (id: string) => {
    setCatalogSelection({tab: 'resources', id});
    setActiveTab('resources');
    setCommandPaletteOpen(false);
  };

  const handleSelectAssessment = (id: string) => {
    setCatalogSelection({tab: 'assessments', id});
    setActiveTab('assessments');
    setCommandPaletteOpen(false);
  };

  const handleSelectProject = (id: string) => {
    setCatalogSelection({tab: 'projects', id});
    setActiveTab('projects');
    setCommandPaletteOpen(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-20 px-4">
      <AnimatePresence>
        {commandPaletteOpen && (
          <motion.div
            className="fixed inset-0 bg-slate-900/40 backdrop-blur-xs transition-opacity"
            onClick={() => setCommandPaletteOpen(false)}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
          />
        )}
      </AnimatePresence>

      <AnimatePresence>
        {commandPaletteOpen && (
          <motion.div 
            ref={dialogRef} 
            role="dialog" 
            aria-modal="true" 
            aria-label="Search workspace" 
            tabIndex={-1} 
            className="relative w-full max-w-2xl bg-white rounded-2xl shadow-2xl border border-slate-200 overflow-hidden z-10 flex flex-col max-h-[75vh]"
            initial={{ opacity: 0, y: -20, scale: 0.95 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, y: -20, scale: 0.95 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
          >
            {/* Search Header */}
            <div className="p-4 border-b border-slate-100 flex items-center gap-3">
              <Search className="w-5 h-5 text-slate-400 shrink-0" />
              <input
                aria-label="Search workspace items"
                ref={inputRef}
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search competencies, target careers, resources, assessments, projects..."
                className="flex-1 text-sm bg-transparent outline-hidden text-slate-900 placeholder:text-slate-400 font-medium"
              />
              <motion.button
                aria-label="Close search"
                onClick={() => setCommandPaletteOpen(false)}
                className="p-1 text-slate-400 hover:text-slate-600 rounded-md transition"
                whileHover={{ scale: 1.1, rotate: 90 }}
                whileTap={{ scale: 0.9 }}
                transition={{ duration: 0.2 }}
              >
                <X className="w-4 h-4" />
              </motion.button>
            </div>

            {/* Results Stream */}
            <div className="flex-1 overflow-y-auto p-3 space-y-4 text-xs">
              {/* Skills / Competencies */}
              {matchedSkills.length > 0 && (
                <div>
                  <div className="px-3 py-1 text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <NavigationIcon name="competencies" className="w-3.5 h-3.5 text-teal-600" />
                    <span>Competencies & Skills</span>
                  </div>
                  <div className="mt-1 space-y-0.5">
                    {matchedSkills.map((skill) => (
                      <motion.div
                        key={skill.id}
                        role="button"
                        tabIndex={0}
                        onKeyDown={e => { if(e.key === "Enter" || e.key === " ") {e.preventDefault(); e.currentTarget.click();} } }
                        onClick={() => handleSelectSkill(skill.id)}
                        className="flex items-center justify-between p-2.5 rounded-xl hover:bg-teal-50/60 transition cursor-pointer text-slate-700 hover:text-slate-900"
                        whileHover={{ scale: 1.02, x: 2 }}
                        whileTap={{ scale: 0.98 }}
                        transition={{ duration: 0.2 }}
                      >
                        <div className="flex items-center gap-2">
                          <span className="font-semibold text-slate-900">{skill.name}</span>
                          <span className="text-[10px] bg-slate-100 text-slate-600 px-1.5 py-0.5 rounded">
                            {skill.domain}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-[11px]">
                          <span className="font-semibold text-teal-700">{skill.mastery}% mastery</span>
                          <ArrowRight className="w-3 h-3 text-slate-400" />
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              )}

              {/* Careers */}
              {matchedCareers.length > 0 && (
                <div>
                  <div className="px-3 py-1 text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <NavigationIcon name="careers" className="w-3.5 h-3.5 text-blue-600" />
                    <span>Career Roles</span>
                  </div>
                  <div className="mt-1 space-y-0.5">
                    {matchedCareers.map((c) => (
                      <motion.div
                        key={c.id}
                        role="button"
                        tabIndex={0}
                        onKeyDown={e => { if(e.key === "Enter" || e.key === " ") {e.preventDefault(); e.currentTarget.click();} } }
                        onClick={() => handleSelectCareer(c.id)}
                        className="flex items-center justify-between p-2.5 rounded-xl hover:bg-blue-50/60 transition cursor-pointer"
                        whileHover={{ scale: 1.02, x: 2 }}
                        whileTap={{ scale: 0.98 }}
                        transition={{ duration: 0.2 }}
                      >
                        <div>
                          <div className="font-semibold text-slate-900">{c.title}</div>
                          <div className="text-[10px] text-slate-600">{c.category}</div>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-semibold text-blue-700 bg-blue-50 px-2 py-0.5 rounded-full border border-blue-200">
                            {c.currentReadiness}% Ready
                          </span>
                          <ArrowRight className="w-3 h-3 text-slate-400" />
                        </div>
                      </motion.div>
                    ))}
                  </div>
                </div>
              )}

              {/* Resources */}
              {matchedResources.length > 0 && (
                <div>
                  <div className="px-3 py-1 text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <NavigationIcon name="resources" className="w-3.5 h-3.5 text-amber-600" />
                    <span>Curated Resources</span>
                  </div>
                  <div className="mt-1 space-y-0.5">
                    {matchedResources.map((r) => (
                      <motion.div
                        key={r.id}
                        role="button"
                        tabIndex={0}
                        onKeyDown={e => { if(e.key === "Enter" || e.key === " ") {e.preventDefault(); e.currentTarget.click();} } }
                        onClick={() => handleSelectResource(r.id)}
                        className="flex items-center justify-between p-2.5 rounded-xl hover:bg-slate-50 transition cursor-pointer"
                        whileHover={{ scale: 1.02, x: 2 }}
                        whileTap={{ scale: 0.98 }}
                        transition={{ duration: 0.2 }}
                      >
                        <div className="truncate max-w-md">
                          <div className="font-semibold text-slate-900 truncate">{r.title}</div>
                          <div className="text-[10px] text-slate-600">{r.provider} • {r.duration}</div>
                        </div>
                        <span className="text-[10px] bg-slate-100 text-slate-600 px-2 py-0.5 rounded">
                          {r.type}
                        </span>
                      </motion.div>
                    ))}
                  </div>
                </div>
              )}

              {/* Assessments & Projects */}
              {matchedAssessments.length > 0 && (
                <div>
                  <div className="px-3 py-1 text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <NavigationIcon name="assessments" className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Assessments</span>
                  </div>
                  <div className="mt-1 space-y-0.5">
                    {matchedAssessments.map((a) => (
                      <motion.div
                        key={a.id}
                        role="button"
                        tabIndex={0}
                        onKeyDown={e => { if(e.key === "Enter" || e.key === " ") {e.preventDefault(); e.currentTarget.click();} } }
                        onClick={() => handleSelectAssessment(a.id)}
                        className="flex items-center justify-between p-2.5 rounded-xl hover:bg-emerald-50/50 transition cursor-pointer"
                        whileHover={{ scale: 1.02, x: 2 }}
                        whileTap={{ scale: 0.98 }}
                        transition={{ duration: 0.2 }}
                      >
                        <div>
                          <div className="font-semibold text-slate-900">{a.title}</div>
                          <div className="text-[10px] text-slate-600">{a.category} • {a.estimatedTime}</div>
                        </div>
                        <span className="text-[11px] font-semibold text-emerald-700">Take Assessment</span>
                      </motion.div>
                    ))}
                  </div>
                </div>
              )}

              {matchedProjects.length > 0 && (
                <div>
                  <div className="px-3 py-1 text-[11px] font-bold text-slate-400 uppercase tracking-wider flex items-center gap-1.5">
                    <NavigationIcon name="projects" className="w-3.5 h-3.5 text-purple-600" />
                    <span>Verification Projects</span>
                  </div>
                  <div className="mt-1 space-y-0.5">
                    {matchedProjects.map((p) => (
                      <motion.div
                        key={p.id}
                        role="button"
                        tabIndex={0}
                        onKeyDown={e => { if(e.key === "Enter" || e.key === " ") {e.preventDefault(); e.currentTarget.click();} } }
                        onClick={() => handleSelectProject(p.id)}
                        className="flex items-center justify-between p-2.5 rounded-xl hover:bg-purple-50/50 transition cursor-pointer"
                        whileHover={{ scale: 1.02, x: 2 }}
                        whileTap={{ scale: 0.98 }}
                        transition={{ duration: 0.2 }}
                      >
                        <div>
                          <div className="font-semibold text-slate-900">{p.title}</div>
                          <div className="text-[10px] text-slate-600">{p.estimatedEffort} • {p.difficulty}</div>
                        </div>
                        <span className="text-[11px] font-semibold text-purple-700">Verify Code</span>
                      </motion.div>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* Footer shortcuts */}
            <div className="p-3 bg-slate-50 border-t border-slate-100 flex items-center justify-between text-[11px] text-slate-500">
              <div className="flex items-center gap-3">
                <span>Press <kbd className="px-1.5 py-0.5 bg-white border border-slate-200 rounded text-slate-700">ESC</kbd> to exit</span>
                <span>Type to filter across platform entities</span>
              </div>
              <span className="font-medium text-slate-700">Career Intelligence Search</span>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}
