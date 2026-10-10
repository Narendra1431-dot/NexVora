import { ProfileAvatar } from './ProfileAvatar';
import { ProfileEditor } from './ProfileEditor';
import { AvatarPicker } from './AvatarPicker';
import { useUndoableState } from '../../lib/state/edit-history';
import { useState } from 'react';
import { useAppState } from '../../lib/state/app-state';
import {
  User,
  ShieldCheck,
  FileCheck2,
  UploadCloud,
  PlusCircle,
  ExternalLink,
  Calendar,
  CheckCircle2,
  Clock,
  AlertTriangle,
  GraduationCap,
  Briefcase,
  Github,
  Award,
  BookOpen,
  Filter,
  X
} from 'lucide-react';
import { EvidenceType, VerificationState } from '../../types';

export function ProfileEvidenceVault() {
  const {
    competencyNodes,
    student,
    careers,
    targetCareer,
    evidenceItems,
    addEvidence,
    showToast
  } = useAppState();

  const [editing,setEditing]=useState(false);
  const [avatarOpen,setAvatarOpen]=useState(false);
  const readinessCareer=careers.find(c=>c.id===student.readinessDisplayCareerId)||targetCareer;
  const [typeFilter, setTypeFilter] = useState('All');
  const [modalOpen, setModalOpen] = useState(false);

  // New evidence form
  const [newTitle, setNewTitle, resetNewTitle] = useUndoableState('', 'Evidence title', modalOpen);
  const [newType, setNewType] = useUndoableState<EvidenceType>('Project', 'Evidence type', modalOpen);
  const [newSkill, setNewSkill, resetNewSkill] = useUndoableState('', 'Evidence skill', modalOpen);
  const [newSource, setNewSource, resetNewSource] = useUndoableState('', 'Evidence source', modalOpen);
  const [newSummary, setNewSummary, resetNewSummary] = useUndoableState('', 'Evidence notes', modalOpen);

  const filteredEvidence = evidenceItems.filter(
    (e) => typeFilter === 'All' || e.type === typeFilter
  );

  const handleAddEvidence = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newTitle || !newSkill) {
      showToast('Missing Fields', 'Please provide a title and associated skill.', 'warning');
      return;
    }

    const skill = competencyNodes.find(n=>n.name.toLowerCase()===newSkill.toLowerCase() || n.id===newSkill);
    if (!skill) {showToast("Unknown skill", "Select an existing competency name.", "warning"); return;}
    const result = await addEvidence({
      title: newTitle,
      type: newType,
      source: newSource || 'Manual Submission',
      verificationState: 'Unverified',
      skillId: skill.id,
      skillName: newSkill,
      confidenceScore: 35,
      quality: 'Low',
      provenance: 'Unverified student-submitted claim.',
      summary: newSummary || 'Direct student verification artifact.'
    });

    if (!result) return;
    setModalOpen(false);
    resetNewTitle('');
    resetNewSkill('');
    resetNewSource('');
    resetNewSummary('');
  };

  return (
    <div className="space-y-6 pb-12">
      {editing&&<ProfileEditor onClose={()=>setEditing(false)}/>}
      {avatarOpen&&<AvatarPicker onClose={()=>setAvatarOpen(false)}/>} 
      {/* Student Profile Card */}
      <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-2xs space-y-6">
        <div className="flex flex-col md:flex-row md:flex-wrap md:items-center justify-between gap-6 pb-6 border-b border-slate-100">
          <div className="flex items-center gap-4">
            <button type="button" aria-label="Change profile photo" onClick={()=>setAvatarOpen(true)} className="shrink-0 rounded-full focus-visible:ring-2 focus-visible:ring-teal-600"><ProfileAvatar name={student.name} avatar={student.avatar}/></button>
            <div className="min-w-0 break-words">
              <div className="flex flex-wrap items-center gap-2">
                <h2 className="text-lg font-bold text-slate-900">{student.name}</h2>
                <span className="text-xs bg-emerald-50 text-emerald-700 font-bold px-2 py-0.5 rounded border border-emerald-200">
                  Signed-in Profile
                </span>
              </div>
              <p className="text-xs text-slate-500 mt-0.5">{student.headline}</p>
              {student.overallXP!==undefined&&<p className="text-xs text-teal-700 mt-1">NexVora XP: {student.overallXP} · Overall rank #{student.overallRank} · Coding XP: {student.codingXP||0}</p>}
              <div className="flex flex-wrap items-center gap-3 text-xs text-slate-500 mt-2">
                <span className="flex items-center gap-1">
                  <GraduationCap className="w-3.5 h-3.5 text-teal-600" />
                  {student.degree}, {student.institution}
                </span>
                <span className="flex items-center gap-1">
                  <Clock className="w-3.5 h-3.5 text-slate-400" />
                  {student.weeklyAvailabilityHours} hrs/wk dedicated
                </span>
              </div>
            </div>
          </div>

          <div className="flex items-center gap-3 self-stretch md:self-auto shrink-0">
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-center flex-1 md:flex-initial min-w-0 md:min-w-[120px]">
              <div className="text-xs text-slate-500 font-medium">Target Readiness</div>
              <div className="text-xl font-bold text-teal-700">{readinessCareer.currentReadiness}%</div><p className="mt-1 max-w-40 text-xs text-slate-500">{readinessCareer.title} / verified evidence</p>
            </div>
            <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl text-center flex-1 md:flex-initial min-w-0 md:min-w-[120px]">
              <div className="text-xs text-slate-500 font-medium">Evidence Vault</div>
              <div className="text-xl font-bold text-slate-900">{evidenceItems.length} items</div>
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          <button onClick={()=>setEditing(true)} className="rounded-lg border border-slate-200 px-3.5 py-2 text-sm font-medium hover:bg-slate-50 interactive-btn cursor-pointer">Edit Profile</button>
          <button onClick={()=>setAvatarOpen(true)} className="rounded-lg border border-slate-200 px-3.5 py-2 text-sm font-medium hover:bg-slate-50 interactive-btn cursor-pointer">Change Photo / Avatar</button>
        </div>
        {/* Education, Experience & Learning Archetype */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-xs">
          <div className="p-4 bg-slate-50 border border-slate-200/80 rounded-xl space-y-2">
            <span className="font-bold text-slate-900 uppercase text-[10px] tracking-wide flex items-center gap-1.5">
              <GraduationCap className="w-4 h-4 text-teal-600" />
              <span>Academic Credentials</span>
            </span>
            <div className="font-semibold text-slate-800">{student.degree}</div>
            <div className="text-slate-500">{student.institution}{student.gpa?` (GPA ${student.gpa})`:""}</div>
            <p className="text-slate-500 whitespace-pre-wrap break-words">{student.gradYear&&`Graduation: ${student.gradYear}`}{student.academicDetails&&`\n${student.academicDetails}`}</p><div className="text-[11px] text-teal-800 pt-1">Self-reported education; supporting evidence is listed below.</div>
          </div>

          <div className="p-4 bg-slate-50 border border-slate-200/80 rounded-xl space-y-2">
            <span className="font-bold text-slate-900 uppercase text-[10px] tracking-wide flex items-center gap-1.5">
              <Briefcase className="w-4 h-4 text-blue-600" />
              <span>Prior Experience</span>
            </span>
            <div className="font-semibold text-slate-800">Profile Summary</div>
            <div className="text-slate-500">{student.headline}</div>
            <div className="text-[11px] text-slate-600 pt-1">
              {student.bio}
            </div><p className="whitespace-pre-wrap break-words text-slate-600">{student.priorExperience||"No prior experience added."}</p>
          </div>

          <div className="p-4 bg-slate-50 border border-slate-200/80 rounded-xl space-y-2">
            <span className="font-bold text-slate-900 uppercase text-[10px] tracking-wide flex items-center gap-1.5">
              <BookOpen className="w-4 h-4 text-purple-600" />
              <span>Learning Preferences</span>
            </span>
            <div className="font-semibold text-slate-800">{(student.learningPreferences||[]).join(', ')||'No preferences added.'}</div>
            <div className="text-slate-500">Pace: {student.weeklyAvailabilityHours} hrs/week committed</div>
            <div className="text-[11px] text-emerald-700 font-semibold pt-1">Learning preferences are self-reported.</div>
          </div>
        </div>
      </div>

      {/* Evidence Vault Header & Action */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h3 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            
            <span>Central Evidence Vault ({evidenceItems.length} Artifacts)</span>
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Every competency state and career readiness score is strictly derived from this auditable proof chain.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <select
            value={typeFilter}
            onChange={(e) => setTypeFilter(e.target.value)}
            className="px-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs font-medium text-slate-700 outline-hidden"
          >
            <option value="All">All Types ({evidenceItems.length})</option>
            <option value="Assessment">Assessment Proofs</option>
            <option value="Project">Project Proofs</option>
            <option value="GitHub Artifact">GitHub Repos</option>
            <option value="Course Record">Course Records</option>
            <option value="Certificate">Certificates</option>
            <option value="Resume Claim">Resume Claims</option>
          </select>

          <button
            onClick={() => setModalOpen(true)}
            className="px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-xs cursor-pointer"
          >
            <PlusCircle className="w-3.5 h-3.5" />
            <span>Add New Evidence</span>
          </button>
        </div>
      </div>

      {!filteredEvidence.length && <div className="flex items-center gap-3 p-5 rounded-xl border border-dashed border-slate-200 bg-white"><p className="text-sm text-slate-600">No evidence matches this view. Add an artifact or choose another evidence type.</p></div>}
      {/* Evidence Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredEvidence.map((ev) => {
          const isVerified = ev.verificationState === 'Verified';
          return (
            <div
              key={ev.id}
              className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs hover:shadow-md transition flex flex-col justify-between"
            >
              <div>
                
                {/* Type & Verification Status */}
                <div className="flex items-center justify-between gap-2 mb-2">
                  <span className="text-[10px] bg-slate-100 text-slate-700 font-bold px-2 py-0.5 rounded">
                    {ev.type}
                  </span>
                  <span
                    className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                      isVerified
                        ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                        : 'bg-amber-50 text-amber-800 border border-amber-200'
                    }`}
                  >
                    {ev.verificationState}
                  </span>
                </div>

                <h4 className="text-xs font-bold text-slate-900 leading-snug">{ev.title}</h4>
                <p className="text-[11px] text-slate-500 mt-1">{ev.source}</p>

                {/* Associated Skill & Confidence */}
                <div className="mt-3 pt-2.5 border-t border-slate-100 flex items-center justify-between text-xs">
                  <span className="text-[11px] font-semibold text-teal-800 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                    {ev.skillName}
                  </span>
                  <span className="text-[11px] text-slate-500 font-mono">
                    {ev.confidenceScore}% certainty
                  </span>
                </div>
              </div>

              <div className="mt-3 pt-2 border-t border-slate-100 text-[10px] text-slate-400 flex items-center justify-between">
                <span>{ev.date}</span>
                <span className="font-mono text-slate-400">ID: {ev.id}</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Add Evidence Modal */}
      {modalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-bold text-slate-900">Add Evidence Artifact to Vault</h3>
              <button onClick={() => setModalOpen(false)} className="text-slate-400 hover:text-slate-600">
                <X className="w-4 h-4" />
              </button>
            </div>

            <form onSubmit={handleAddEvidence} className="space-y-3 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">Evidence Title</label>
                <input
                  type="text"
                  required
                  value={newTitle}
                  data-undo="true" onChange={(e) => setNewTitle(e.target.value)}
                  placeholder="e.g. Distributed Model Training Lab Submission"
                  className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-teal-500"
                />
              </div>

              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Evidence Type</label>
                  <select
                    value={newType}
                    data-undo="true" onChange={(e) => setNewType(e.target.value as EvidenceType)}
                    className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl outline-hidden"
                  >
                    <option value="Project">Project Proof</option>
                    <option value="Assessment">Assessment Score</option>
                    <option value="Certificate">Certificate</option>
                    <option value="GitHub Artifact">GitHub Artifact</option>
                    <option value="Course Record">Course Record</option>
                  </select>
                </div>
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Associated Skill</label>
                  <select aria-label="Associated skill" required value={newSkill} data-undo="true" onChange={e=>setNewSkill(e.target.value)} className="w-full p-2.5 bg-slate-50 border rounded-xl"><option value="">Choose a competency</option>{competencyNodes.map(n=><option key={n.id} value={n.id}>{n.name}</option>)}</select>
                </div>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Source / Verification Link</label>
                <input
                  type="text"
                  value={newSource}
                  data-undo="true" onChange={(e) => setNewSource(e.target.value)}
                  placeholder="e.g. github.com/username/project"
                  className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-teal-500"
                />
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">Summary / Proof Details</label>
                <textarea
                  rows={3}
                  value={newSummary}
                  data-undo="true" onChange={(e) => setNewSummary(e.target.value)}
                  placeholder="Evaluation criteria, rubric passed, or score..."
                  className="w-full p-2.5 bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-teal-500"
                />
              </div>

              <div className="pt-2 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setModalOpen(false)}
                  className="px-4 py-2 border border-slate-200 rounded-xl text-slate-600 hover:bg-slate-50 font-semibold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white rounded-xl font-bold cursor-pointer shadow-xs"
                >
                  Save & Update Competencies
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
