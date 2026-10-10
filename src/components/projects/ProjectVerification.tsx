import { useUndoableState } from '../../lib/state/edit-history';
import { useState, useEffect } from 'react';
import { useAppState } from '../../lib/state/app-state';
import {
  FolderGit2,
  Github,
  CheckCircle2,
  Clock,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  Code2,
  Layers,
  FileCheck2,
  AlertCircle,
  ExternalLink,
  ChevronRight,
  RefreshCw
} from 'lucide-react';
import { RubricReview } from './RubricReview';
import { ProjectItem } from '../../types';

export function ProjectVerification() {
  const {
    student,
    catalogSelection,
    projects,
    verifyProject,
    targetCareer,
    setActiveTab
  } = useAppState();

  const [selectedProjectId, setSelectedProjectId] = useState<string>(
    (catalogSelection?.tab === 'projects' ? catalogSelection.id : null) || projects[0]?.id || ''
  );

  const selectedProject =
    projects.find((p) => p.id === selectedProjectId) || projects[0];

  const [repoUrl, setRepoUrl, resetRepoUrl] = useUndoableState(
    selectedProject?.submissionDetails?.githubUrl || '', 'Project repository'
  );
  const [isVerifying, setIsVerifying] = useState(false);
  

  const [description, setDescription, resetDescription] = useUndoableState('', 'Project notes');
  useEffect(() => {
    resetRepoUrl(selectedProject?.submissionDetails?.githubUrl || '');
    resetDescription(selectedProject?.submissionDetails?.description || '');
  }, [selectedProjectId]);
  const handleStartVerification = async () => {
    setIsVerifying(true);
    await verifyProject(selectedProject.id, {githubUrl:repoUrl, description});
    setIsVerifying(false);
  };

  const isVerified = selectedProject?.verified || false;

  return (
    <div className="space-y-6 pb-12">{student.canReview && <RubricReview />}<label className="block bg-white border rounded-xl p-4">Submission description<textarea aria-label="Project description" value={description} data-undo="true" onChange={e=>setDescription(e.target.value)} className="block w-full border p-3 mt-2" /></label><p className="text-sm text-slate-600">Repository submissions are saved for rubric review. A URL or description alone does not verify skills.</p>
      {/* Top Banner */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            
            <span>Project Recommendations & Rubric Verification Engine</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Submit repository artifacts against engineering rubrics to produce verifiable evidence proofs.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-500 font-medium">Active Evaluation Rubric:</span>
          <span className="font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
            Enterprise Production Standard
          </span>
        </div>
      </div>

      {/* Main Grid: Project List & Detail/Verification Panel */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        {/* Left Column: Project Catalog */}
        <div className="space-y-3">
          <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
            Portfolio Verification Projects ({projects.length})
          </h3>
          <div className="space-y-2">
            {!projects.length && <div className="flex items-center gap-3 p-4 border rounded-xl bg-white"><p className="text-xs text-slate-600">No projects are available in the current catalog.</p></div>}
            {projects.map((p) => {
              const isSelected = p.id === selectedProject?.id;
              const isProjVerified = p.verified;

              return (
                <div
                  key={p.id}
                  onClick={() => setSelectedProjectId(p.id)}
                  className={`p-3.5 rounded-xl border transition cursor-pointer ${
                    isSelected
                      ? 'bg-teal-50/70 border-teal-500 shadow-xs'
                      : 'bg-white border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-[10px] bg-slate-100 text-slate-600 font-bold px-1.5 py-0.2 rounded">
                      {p.difficulty}
                    </span>
                    <span
                      className={`text-[10px] font-bold px-1.5 py-0.2 rounded ${
                        isProjVerified
                          ? 'bg-emerald-100 text-emerald-800'
                          : 'bg-amber-50 text-amber-800'
                      }`}
                    >
                      {isProjVerified ? 'Verified' : 'Pending Verification'}
                    </span>
                  </div>
                  <div className="text-xs font-bold text-slate-900">{p.title}</div>
                  <div className="text-[11px] text-slate-500 mt-1">
                    Skills: {p.skillsValidated.slice(0, 2).join(', ')}
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Right 2 Columns: Project Workspace & Verification Console */}
        <div className="md:col-span-2 space-y-6">
          {selectedProject && (
            <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-2xs space-y-6">
              {/* Project Header */}
              <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 pb-4 border-b border-slate-100">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-bold uppercase text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                      Capstone Verification
                    </span>
                    <span className="text-xs text-slate-500">Effort: {selectedProject.estimatedEffort}</span>
                  </div>
                  <h3 className="text-lg font-bold text-slate-900 mt-1">{selectedProject.title}</h3>
                  <p className="text-xs text-slate-600 mt-1 leading-relaxed">{selectedProject.objective}</p>
                </div>

                {isVerified && (
                  <div className="shrink-0 p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-center">
                    <div className="text-lg font-bold text-emerald-800">
                      {selectedProject.submissionDetails?.evaluationScore || 94} / 100
                    </div>
                    <div className="text-[10px] font-bold text-emerald-700 uppercase">Verified Proof</div>
                  </div>
                )}
              </div>

              {/* Concepts & Skills Validated */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
                <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
                  <span className="font-bold text-slate-900 uppercase text-[10px] tracking-wide">
                    Concepts Covered
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedProject.concepts.map((tech: string, i: number) => (
                      <span
                        key={i}
                        className="px-2 py-1 bg-white border border-slate-200 rounded-md text-slate-700 font-mono text-[11px]"
                      >
                        {tech}
                      </span>
                    ))}
                  </div>
                </div>

                <div className="p-3.5 bg-slate-50 border border-slate-200 rounded-xl space-y-1.5">
                  <span className="font-bold text-slate-900 uppercase text-[10px] tracking-wide">
                    Target Competencies Addressed
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {selectedProject.skillsValidated.map((s: string, i: number) => (
                      <span
                        key={i}
                        className="px-2 py-1 bg-teal-50 text-teal-800 border border-teal-200 rounded-md font-semibold text-[11px]"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              {/* Deliverables Checklist */}
              <div className="space-y-2 text-xs">
                <h4 className="font-bold text-slate-900 uppercase tracking-wide text-[11px]">
                  Required Deliverables
                </h4>
                <div className="space-y-1.5">
                  {selectedProject.deliverables.map((deliv: string, idx: number) => (
                    <div
                      key={idx}
                      className="p-2.5 bg-slate-50 border border-slate-200 rounded-lg flex items-center gap-2.5 text-slate-700"
                    >
                      <CheckCircle2
                        className={`w-4 h-4 ${
                          isVerified ? 'text-emerald-600' : 'text-slate-400'
                        }`}
                      />
                      <span>{deliv}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Interactive Verification Console */}
              <div className="p-5 bg-slate-900 text-white rounded-2xl border border-slate-800 space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Github className="w-5 h-5 text-teal-400" />
                    <span className="font-bold text-xs">Repository Rubric Verification</span>
                  </div>
                  <span className="text-[10px] text-slate-400 font-mono">Automated AST & Test Runner</span>
                </div>

                <div className="flex flex-col sm:flex-row gap-2">
                  <input
                    type="text"
                    value={repoUrl}
                    data-undo="true" onChange={(e) => setRepoUrl(e.target.value)}
                    disabled={isVerifying}
                    placeholder="https://github.com/username/repo"
                    className="flex-1 px-3 py-2 bg-slate-800/80 border border-slate-700 rounded-xl text-xs text-white font-mono outline-hidden focus:border-teal-400"
                  />
                  <button
                    onClick={handleStartVerification}
                    disabled={isVerifying}
                    className="px-4 py-2 bg-teal-500 hover:bg-teal-400 disabled:opacity-50 text-slate-950 font-bold rounded-xl text-xs transition flex items-center justify-center gap-1.5 cursor-pointer shadow-xs"
                  >
                    {isVerifying ? (
                      <>
                        <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                        <span>Evaluating Code...</span>
                      </>
                    ) : isVerified ? (
                      <>
                        <CheckCircle2 className="w-3.5 h-3.5" />
                        <span>Re-verify Repository</span>
                      </>
                    ) : (
                      <>
                        <ShieldCheck className="w-3.5 h-3.5" />
                        <span>Run Verification Engine</span>
                      </>
                    )}
                  </button>
                </div>

                {/* Progress Stepper during verification */}
                {isVerifying && <p className="text-sm p-3">Saving submission for review...</p>}

                {selectedProject.submittedAt && !isVerifying && <div className="p-4 border border-slate-500 rounded-xl text-sm space-y-2">
                  <p>{isVerified ? `Authorized rubric review passed: ${selectedProject.submissionDetails?.evaluationScore}/100` : 'Submission saved; authorized rubric review pending.'}</p>
                  <p>{selectedProject.submissionDetails?.feedback}</p>
                  <p>Current career readiness: {targetCareer.currentReadiness}%.</p>
                  <button onClick={()=>setActiveTab('competencies')} className="underline">View current competency impact</button>
                </div>}

              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
