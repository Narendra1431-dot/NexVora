import { useState } from 'react';
import { useAppState } from '../../lib/state/app-state';
import {
  Compass,
  CheckCircle2,
  Lock,
  Play,
  ArrowRight,
  Clock,
  Sparkles,
  ShieldAlert,
  ChevronRight,
  RefreshCw,
  FolderGit2,
  FileCheck2
} from 'lucide-react';
import { RoadmapMilestone, MilestoneState } from '../../types';

export function AdaptiveRoadmap() {
  const {
    roadmap,
    targetCareer,
    advanceMilestone,
    setActiveTab,
    setSelectedSkillId,
    showToast
  } = useAppState();

  const [filterState, setFilterState] = useState<string>('all');
  const [selectedMilestoneId, setSelectedMilestoneId] = useState<string>(
    roadmap[0]?.id || 'ms-01'
  );

  const selectedMilestone =
    roadmap.find((m) => m.id === selectedMilestoneId) || roadmap[0];

  const filteredMilestones = roadmap.filter((m) => {
    if (filterState === 'all') return true;
    if (filterState === 'active') return m.state === 'Active';
    if (filterState === 'completed') return m.state === 'Completed';
    if (filterState === 'locked') return m.state === 'Locked' || m.state === 'Blocked';
    return true;
  });

  const handleInspectSkill = (skillId: string) => {
    setSelectedSkillId(skillId);
    setActiveTab('competencies');
  };

  const handleActionClick = (milestone: RoadmapMilestone) => {
    if (milestone.state === 'Locked' || milestone.state === 'Blocked') {
      showToast('Prerequisite Locked', `Complete previous prerequisites to unlock this milestone.`, 'warning');
      return;
    }
    setSelectedSkillId(milestone.skillId);
    if (milestone.assessmentId) {
      setActiveTab('assessments');
    } else if (milestone.projectId) {
      setActiveTab('projects');
    } else {
      setActiveTab("resources");
    }
  };

  const getStatusBadge = (state: MilestoneState) => {
    switch (state) {
      case 'Completed':
        return (
          <span className="flex items-center gap-1 text-[11px] font-bold text-emerald-800 bg-emerald-50 border border-emerald-200 px-2 py-0.5 rounded">
            <CheckCircle2 className="w-3 h-3" />
            <span>Completed</span>
          </span>
        );
      case 'Active':
        return (
          <span className="flex items-center gap-1 text-[11px] font-bold text-teal-800 bg-teal-50 border border-teal-200 px-2 py-0.5 rounded animate-pulse">
            <Play className="w-3 h-3 fill-current" />
            <span>Active Focus</span>
          </span>
        );
      case 'Blocked':
      case 'Locked':
        return (
          <span className="flex items-center gap-1 text-[11px] font-semibold text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
            <Lock className="w-3 h-3" />
            <span>Locked (Prereqs)</span>
          </span>
        );
      case 'Needs Assessment':
        return (
          <span className="flex items-center gap-1 text-[11px] font-bold text-amber-800 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded">
            <ShieldAlert className="w-3 h-3" />
            <span>Needs Diagnostic</span>
          </span>
        );
      default:
        return null;
    }
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            
            <span>Adaptive Career Roadmap ({targetCareer.title})</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Dynamically sequenced milestones. Automatically re-orders and unlocks dependencies when competencies update.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <div className="flex bg-slate-100 p-0.5 rounded-xl text-xs font-semibold">
            {['all', 'active', 'completed', 'locked'].map((tab) => (
              <button
                key={tab}
                onClick={() => setFilterState(tab)}
                className={`px-3 py-1 rounded-lg capitalize transition cursor-pointer ${
                  filterState === tab
                    ? 'bg-white text-slate-900 shadow-2xs'
                    : 'text-slate-500 hover:text-slate-700'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Main Grid: Milestones Pipeline & Inspector */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Milestone Sequence List */}
        <div className="lg:col-span-2 space-y-3">
          {!filteredMilestones.length && <div className="flex items-center gap-3 p-5 rounded-xl border border-dashed border-slate-200 bg-white"><p className="text-xs text-slate-600">No milestones match this filter. Choose another filter to explore your learning path.</p></div>}
          {filteredMilestones.map((milestone, idx) => {
            const isSelected = milestone.id === selectedMilestone?.id;
            const isCompleted = milestone.state === 'Completed';
            const isActive = milestone.state === 'Active';
            const isLocked = milestone.state === 'Locked' || milestone.state === 'Blocked';

            return (
              <div
                key={milestone.id}
                onClick={() => setSelectedMilestoneId(milestone.id)}
                className={`p-4 rounded-2xl border interactive-card cursor-pointer flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                  isSelected
                    ? 'bg-teal-50/40 border-teal-500 shadow-xs ring-1 ring-teal-500/20'
                    : 'bg-white border-slate-200/80 hover:bg-slate-50 shadow-2xs'
                } ${isLocked ? 'opacity-70' : ''}`}
              >
                <div className="flex items-start gap-3.5">
                  <div
                    className={`w-9 h-9 rounded-xl flex items-center justify-center font-bold text-xs shrink-0 ${
                      isCompleted
                        ? 'bg-emerald-100 text-emerald-800'
                        : isActive
                        ? 'bg-teal-700 text-white shadow-xs'
                        : 'bg-slate-100 text-slate-500'
                    }`}
                  >
                    {isCompleted ? <CheckCircle2 className="w-5 h-5" /> : `0${milestone.order}`}
                  </div>

                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-[10px] font-bold uppercase text-slate-400 font-mono">
                        {milestone.domain}
                      </span>
                      {getStatusBadge(milestone.state)}
                    </div>

                    <h4 className="text-xs font-bold text-slate-900">{milestone.title}</h4>
                    <p className="text-[11px] text-slate-500 mt-0.5 line-clamp-1">{milestone.reason}</p>

                    <div className="flex items-center gap-3 text-[10px] text-slate-400 mt-2">
                      <span className="flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {milestone.estimatedDuration}
                      </span>
                      <span>Target: {milestone.masteryTarget}% mastery</span>
                      <span>Current: {milestone.currentMastery}%</span>
                    </div>
                  </div>
                </div>

                <div className="flex sm:flex-col items-center sm:items-end justify-between gap-2 shrink-0 pt-2 sm:pt-0 border-t sm:border-t-0 border-slate-100">
                  
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      handleActionClick(milestone);
                    }}
                    disabled={isLocked}
                    className={`px-3 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1 cursor-pointer ${
                      isCompleted
                        ? 'bg-slate-100 text-slate-700 hover:bg-slate-200'
                        : isActive
                        ? 'bg-teal-700 hover:bg-teal-800 text-white shadow-xs'
                        : 'bg-slate-100 text-slate-400 cursor-not-allowed'
                    }`}
                  >
                    {isCompleted ? (
                      <span>Review Artifact</span>
                    ) : isActive ? (
                      <>
                        <span>Continue</span>
                        <ArrowRight className="w-3 h-3" />
                      </>
                    ) : (
                      <>
                        <Lock className="w-3 h-3" />
                        <span>Locked</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            );
          })}
        </div>

        {/* Right Col: Selected Milestone Detail Inspector */}
        <div className="space-y-4">
          {selectedMilestone && (
            <div className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs space-y-4 text-xs">
              <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                <span className="text-[10px] font-bold uppercase text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                  Milestone Inspector
                </span>
                {getStatusBadge(selectedMilestone.state)}
              </div>

              <div>
                <h3 className="text-sm font-bold text-slate-900">{selectedMilestone.title}</h3>
                <p className="text-slate-600 text-xs mt-1 leading-relaxed">{selectedMilestone.reason}</p>
              </div>

              {/* Sequencing Rationale */}
              <div className="p-3 bg-teal-50/50 border border-teal-100 rounded-xl space-y-1">
                <span className="font-bold text-teal-900 text-[10px] uppercase tracking-wide flex items-center gap-1">
                  <Sparkles className="w-3 h-3 text-teal-600" />
                  <span>Sequencing Logic</span>
                </span>
                <p className="text-slate-700 text-[11px] leading-relaxed">
                  Prerequisites: {selectedMilestone.prerequisites.join(', ') || 'Foundational'}
                </p>
                <div className="text-[11px] text-teal-800 font-semibold pt-1">
                  Completion Condition: {selectedMilestone.completionCondition}
                </div>
              </div>

              {/* Tasks to practice */}
              <div className="space-y-2">
                <span className="font-bold text-slate-900 uppercase text-[10px] tracking-wide">
                  Practice Tasks & Deliverables
                </span>
                <div className="space-y-1.5">
                  {selectedMilestone.practiceTasks.map((task: string, i: number) => (
                    <div
                      key={i}
                      className="p-2 bg-slate-50 border border-slate-200/80 rounded-lg text-slate-700 text-[11px] flex items-start gap-2"
                    >
                      <span className="text-teal-700 font-bold">•</span>
                      <span>{task}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Evidence Generated */}
              <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
                <span className="text-slate-500 font-medium text-[10px] uppercase">
                  Proof Generated Upon Completion
                </span>
                <div className="font-semibold text-slate-900 text-[11px]">
                  {selectedMilestone.evidenceGenerated}
                </div>
              </div>

              <div className="pt-2 border-t border-slate-100 flex flex-col gap-2">
                <button
                  onClick={() => handleInspectSkill(selectedMilestone.skillId)}
                  className="w-full py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 font-semibold rounded-xl text-xs transition cursor-pointer"
                >
                  View Competency Node
                </button>
                <button
                  onClick={() => handleActionClick(selectedMilestone)}
                  disabled={selectedMilestone.state === 'Locked' || selectedMilestone.state === 'Blocked'}
                  className="w-full py-2 bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white font-bold rounded-xl text-xs transition flex items-center justify-center gap-1.5 shadow-xs cursor-pointer"
                >
                  <span>
                    {selectedMilestone.state === 'Completed'
                      ? 'Re-evaluate Milestone'
                      : 'Launch Active Milestone'}
                  </span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
