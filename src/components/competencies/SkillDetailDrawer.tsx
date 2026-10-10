import type { CompetencyNode } from '../../types';
import { prerequisitePath } from './graph-layout';
import { ConceptObservations } from './ConceptObservations';
import { useModalDialog } from '../../lib/hooks/use-modal-dialog';
import { useAppState } from '../../lib/state/app-state';
import {
  X,
  ShieldCheck,
  CheckCircle2,
  Clock,
  AlertTriangle,
  FileText,
  Sparkles,
  ArrowRight,
  TrendingUp,
  Link2,
  BookOpen,
  Calendar,
  Layers
} from 'lucide-react';
import { getNodeStateBadgeColor, formatDate } from '../../lib/utils/formatters';

interface SkillDetailDrawerProps {
  skillId: string | null;
  nodeOverride?: CompetencyNode;
  onClose: () => void;
}

export function SkillDetailDrawer({ skillId, onClose, nodeOverride }: SkillDetailDrawerProps) {
  const { targetCareer, mission, conceptObservations, relationships, assessments, showToast, competencyNodes, evidenceItems, setActiveTab, setSelectedSkillId } = useAppState();
  const node = nodeOverride || competencyNodes.find((n) => n.id === skillId);
  const dialogRef = useModalDialog(Boolean(node), onClose);
  if (!node) return null;

  const requirement = targetCareer.requiredCompetencies.find(r=>r.skillId===node.id);
  const onPath = prerequisitePath(competencyNodes,targetCareer.requiredCompetencies.map(r=>r.skillId)).has(node.id);
  const badge = getNodeStateBadgeColor(node.state);
  const relationshipEdges = relationships.edges.filter(edge=>edge.source === `skill:${skillId}` || edge.target === `skill:${skillId}`);
  const relationshipLabels = new Map(relationships.nodes.map(item=>[item.id,item.label]));

  // Find supporting evidence
  const supportingEvidence = evidenceItems.filter(
    (e) => e.skillId === node.id || e.skillName.toLowerCase() === node.name.toLowerCase()
  );

  // Find prerequisite nodes
  const prereqNodes = competencyNodes.filter((n) => node.prerequisites.includes(n.id));

  return (
    <div ref={dialogRef} role="dialog" aria-modal="true" aria-label={`${node.name} skill details`} tabIndex={-1} className="fixed inset-y-0 right-0 z-50 max-w-md w-full bg-white shadow-2xl border-l border-slate-200 flex flex-col">
      {/* Drawer Header */}
      <div className="p-4 border-b border-slate-100 flex items-start justify-between bg-slate-50/70">
        <div>
          <div className="flex items-center gap-2">
            <span
              className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${badge.bg} ${badge.text} ${badge.border}`}
            >
              {node.state}
            </span>
            <span className="text-xs text-slate-500 font-medium">({node.domain})</span>
          </div>
          <h3 className="text-base font-bold text-slate-900 mt-1 flex items-center gap-2">{node.name}</h3>
        </div>
        <button
          aria-label="Close skill details"
          onClick={onClose}
          className="p-1.5 text-slate-400 hover:text-slate-600 rounded-lg hover:bg-slate-200 transition cursor-pointer"
        >
          <X className="w-4 h-4" />
        </button>
      </div>

      {/* Drawer Body */}
      <div className="flex-1 overflow-y-auto p-4 space-y-5 text-xs text-slate-700">
        {nodeOverride && <p className="p-3 bg-amber-50 text-amber-800 rounded-lg">Mastery and confidence below are from the saved baseline. Evidence and career requirements are current.</p>}
        <div className="p-3 bg-teal-50 border border-teal-100 rounded-xl"><p className="font-semibold">Target: {requirement?requirement.requiredMastery+'%':'No direct role threshold'}</p><details className="mt-2"><summary className="cursor-pointer font-semibold">Why is this required?</summary><p className="mt-2">{requirement?`${node.name} is listed in the ${targetCareer.title} requirements (${requirement.importance}).`:onPath?`This skill is a prerequisite for a skill required by ${targetCareer.title}.`:'This supporting skill is not required by the selected career catalog.'}</p></details></div>
        {/* Mastery & Confidence Meters */}
        <div className="grid grid-cols-2 gap-3">
          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
            <div className="flex items-center justify-between text-slate-500 mb-1">
              <span className="font-semibold">Mastery</span>
              <span className="font-bold text-slate-900 text-sm">{node.mastery}%</span>
            </div>
            <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
              <div className="bg-teal-600 h-full rounded-full" style={{ width: `${node.mastery}%` }} />
            </div>
            <div className="text-[10px] text-slate-400 mt-1">Direct skill capability</div>
          </div>

          <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
            <div className="flex items-center justify-between text-slate-500 mb-1">
              <span className="font-semibold">Confidence</span>
              <span className="font-bold text-teal-800 text-sm">{node.confidence}%</span>
            </div>
            <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
              <div className="bg-teal-500 h-full rounded-full" style={{ width: `${node.confidence}%` }} />
            </div>
            <div className="text-[10px] text-slate-400 mt-1">Evidence certainty</div>
          </div>
        </div>

        {/* Metadata Details */}
        <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-slate-500">Career Importance:</span>
            <span className="font-bold text-slate-900">{node.careerImportance}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-500">Node Type:</span>
            <span className="font-semibold text-slate-800">{node.type}</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-500">Evidence Count:</span>
            <span className="font-bold text-slate-900">{node.evidenceCount} evidence records</span>
          </div>
          <div className="flex items-center justify-between">
            <span className="text-slate-500">Last Assessed:</span>
            <span className="font-medium text-slate-800">{node.lastAssessed || 'Never'}</span>
          </div>
        </div>

        {/* Remaining Gap & Recommended Action */}
        <div className="p-3.5 bg-amber-50/70 border border-amber-200 rounded-xl space-y-1.5">
          <div className="font-bold text-amber-900 flex items-center gap-1.5">
            <AlertTriangle className="w-3.5 h-3.5 text-amber-600" />
            <span>Remaining Competency Gap</span>
          </div>
          <p className="text-amber-800 leading-relaxed text-[11px]">{node.remainingGap}</p>
          <div className="pt-2 border-t border-amber-200/60 flex items-center justify-between">
            <span className="font-semibold text-slate-700 text-[11px]">Recommended Action:</span>
          </div>
          <p className="text-slate-800 font-medium text-[11px]">{node.recommendedAction}</p>
        </div>

        {/* Prerequisites */}
        {prereqNodes.length > 0 && (
          <div>
            <h4 className="font-bold text-slate-900 uppercase tracking-wide text-[11px] mb-2 flex items-center gap-1.5">
              <Link2 className="w-3.5 h-3.5 text-slate-500" />
              <span>Prerequisites</span>
            </h4>
            <div className="space-y-1.5">
              {prereqNodes.map((prereq) => (
                <div
                  key={prereq.id}
                  role="button" tabIndex={0}
                  onKeyDown={e=>{if(e.key === "Enter" || e.key === " "){e.preventDefault();setSelectedSkillId(prereq.id);}}}
                  onClick={() => setSelectedSkillId(prereq.id)}
                  className="flex items-center justify-between p-2.5 bg-slate-50 border border-slate-200 rounded-lg hover:bg-slate-100 transition cursor-pointer"
                >
                  <span className="font-medium text-slate-800">{prereq.name}</span>
                  <span className="font-semibold text-teal-700">{prereq.mastery}%</span>
                </div>
              ))}
            </div>
          </div>
        )}

        <ConceptObservations observations={conceptObservations} skillId={node.id} />
        <details className="border border-slate-200 rounded-xl p-3">
          <summary className="font-semibold cursor-pointer">Evidence and learning relationships ({relationshipEdges.length})</summary>
          <ul className="mt-3 space-y-3">{relationshipEdges.map(edge=><li key={edge.id}>
            <p><strong>{relationshipLabels.get(edge.source)}</strong> {edge.type.toLowerCase().replaceAll('_',' ')} <strong>{relationshipLabels.get(edge.target)}</strong></p>
            <p className="text-slate-500">{edge.reason}</p>
          </li>)}</ul>
        </details>
        {/* Related Concepts */}
        {node.relatedConcepts && node.relatedConcepts.length > 0 && (
          <div>
            <h4 className="font-bold text-slate-900 uppercase tracking-wide text-[11px] mb-2">
              Related Concepts & Topics
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {node.relatedConcepts.map((c, i) => (
                <span
                  key={i}
                  className="px-2.5 py-1 bg-slate-100 text-slate-700 border border-slate-200 rounded-md text-[11px]"
                >
                  {c}
                </span>
              ))}
            </div>
          </div>
        )}

        {/* Supporting Evidence in Vault */}
        <div>
          <div className="flex items-center justify-between mb-2">
            <h4 className="font-bold text-slate-900 uppercase tracking-wide text-[11px] flex items-center gap-1.5">
              <FileText className="w-3.5 h-3.5 text-purple-600" />
              <span>Supporting Evidence Vault ({supportingEvidence.length})</span>
            </h4>
          </div>

          {supportingEvidence.length === 0 ? (
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-center text-slate-400 text-[11px]">
              No evidence artifacts linked yet. Submit an assessment or code project to verify this node.
            </div>
          ) : (
            <div className="space-y-2">
              {supportingEvidence.map((ev) => (
                <div key={ev.id} className="p-2.5 bg-slate-50 border border-slate-200 rounded-xl space-y-1">
                  <div className="flex items-center justify-between">
                    <span className="font-bold text-slate-900 truncate pr-1">{ev.title}</span>
                    <span className="text-[10px] bg-emerald-100 text-emerald-800 font-bold px-1.5 rounded">
                      {ev.verificationState}
                    </span>
                  </div>
                  <p className="text-slate-500 text-[10px]">{ev.source}</p><p className="text-slate-500 text-[10px]">{ev.provenance}</p><p className="text-slate-500 text-[10px]">Score/confidence: {ev.confidenceScore}%; quality: {ev.quality}; recorded: {ev.date}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Drawer Footer Actions */}
      <div className="p-4 border-t border-slate-100 bg-slate-50/50 flex gap-2">
        <button
          onClick={() => {
            if(!assessments.some(a=>a.skillId===node.id)){showToast('Assessment unavailable','No scored assessment is available for this skill yet. Use the roadmap or project review.','warning');return;}
            setSelectedSkillId(node.id);
            setActiveTab('assessments');
            onClose();
          }}
          className="flex-1 py-2 bg-teal-700 hover:bg-teal-800 text-white rounded-xl font-bold transition flex items-center justify-center gap-1.5 cursor-pointer text-xs"
        >
          <span>Assess This Skill</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </button>
        <button
          onClick={() => {
            setSelectedSkillId(node.id);
            setActiveTab('resources');
            onClose();
          }}
          className="px-3 py-2 bg-white border border-slate-200 hover:bg-slate-100 text-slate-700 rounded-xl font-semibold transition cursor-pointer text-xs"
        >
          Resources
        </button>
        <button onClick={()=>{setSelectedSkillId(node.id);setActiveTab('roadmap');onClose();}} className="px-3 py-2 border border-teal-200 text-teal-800 bg-teal-50 rounded-xl font-semibold text-xs">Learn Next</button>
      </div>
    </div>
  );
}
