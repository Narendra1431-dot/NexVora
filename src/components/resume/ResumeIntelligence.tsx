import { ResumeGenerator } from './ResumeGenerator';
import { UndoRedoControls } from '../layout/UndoRedoControls';
import { useUndoableState } from '../../lib/state/edit-history';
import { useRef, useState } from 'react';
import { useAppState } from '../../lib/state/app-state';
import {
  FileText,
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  Sparkles,
  ArrowRight,
  TrendingUp,
  FileCheck2,
  ShieldCheck,
  AlertCircle,
  Copy,
  ExternalLink,
  HelpCircle,
  Download,
  X,
  FileCode,
  Check
} from 'lucide-react';
import { useModalDialog } from '../../lib/hooks/use-modal-dialog';
import { ResumeClaim } from '../../types';

export function ResumeIntelligence() {
  const {
    student,
    resumeAnalysis,
    targetCareer,
    competencyNodes,
    setActiveTab,
    setSelectedSkillId,
    uploadResume,
    showToast
  } = useAppState();

  const [activeTabSub, setActiveTabSub] = useState<'overview' | 'improvements' | 'generator'>('overview');
  const [generatorOpened,setGeneratorOpened]=useState(false);
  const [pasteModalOpen, setPasteModalOpen] = useState(false);
  const [exportModalOpen, setExportModalOpen] = useState(false);
  const [pastedResumeText, setPastedResumeText, resetPastedResumeText] = useUndoableState('', 'Resume text', pasteModalOpen);
  const [copiedDraft, setCopiedDraft] = useState(false);

  const [uploading,setUploading] = useState(false);
  const [uploadError,setUploadError] = useState('');
  const [uploadSuccess,setUploadSuccess] = useState('');
  const uploadLock = useRef(false);
  const fileInput = useRef<HTMLInputElement>(null);
  const pasteRef = useModalDialog(pasteModalOpen,()=>{if(!uploadLock.current)setPasteModalOpen(false);});
  const exportRef = useModalDialog(exportModalOpen,()=>setExportModalOpen(false));
  const hasResume = Boolean(resumeAnalysis.documentId);
  const copyText = async (text:string) => {
    try {await navigator.clipboard.writeText(text);return true;}
    catch {showToast('Copy unavailable','Use Download .md or select the text to copy manually.','warning');return false;}
  };
  const handleCopySuggestion = async (text: string) => {
    if(await copyText(text)) showToast('Copied to Clipboard','Recommendation copied.','info');
  };
  const handleInspectSkill = (skillId: string) => {
    if(competencyNodes.some(n=>n.id===skillId)) {setSelectedSkillId(skillId);setActiveTab('competencies');}
    else showToast('Skill unavailable','Refresh the page to reload the competency catalog.','warning');
  };
  const parseResume = async (value:File|string) => {
    if(uploadLock.current) return;
    uploadLock.current=true;setUploading(true);setUploadError('');setUploadSuccess('');
    try {
      if(typeof value==='string' && !value.trim()) throw new Error('Paste resume text before parsing.');
      if(typeof value!=='string' && (!/\.(pdf|txt|md)$/i.test(value.name) || value.size>8*1024*1024)) throw new Error('Choose a PDF or UTF-8 TXT file up to 8 MB.');
      const result=await uploadResume(value);
      setPasteModalOpen(false);resetPastedResumeText('');setActiveTabSub('overview');
      setUploadSuccess(result?.jobId?'Resume analysis queued. You can continue using the app; results will update automatically.':'Resume parsed, evidence cross-checked, career analysis saved.');
    } catch(error) {setUploadError((error as Error).message);}
    finally {uploadLock.current=false;setUploading(false);if(fileInput.current)fileInput.current.value='';}
  };
  const handleParseCustomResume = async (e: React.FormEvent) => {e.preventDefault();await parseResume(pastedResumeText);};

  const verifiedClaims = resumeAnalysis.claims.filter((c) => c.evidenceState === 'Verified');
  const unverifiedClaims = resumeAnalysis.claims.filter((c) => c.evidenceState !== 'Verified');

  const generatedResumeDraft = `# ${student.name}

Target: ${targetCareer.title}
Source: ${resumeAnalysis.fileName}

## Resume content (self-reported)
${(resumeAnalysis.parsedSections || []).filter(s=>['education','experience','projects','summary'].includes(s.name)).map(s=>`### ${s.name}\n${s.text}`).join('\n\n')}

## Evidence-supported resume skills
${verifiedClaims.map(c=>`- ${c.skillName} (evidence: ${c.evidenceId})`).join('\n') || 'No resume claims currently meet verification requirements.'}

## Claims requiring support (unverified)
${unverifiedClaims.map(c=>`- ${c.skillName}: ${c.claim}`).join('\n') || 'None.'}

Review this draft before use. ATS compatibility is a platform heuristic, not a hiring guarantee.
`;
  const handleCopyDraft = async () => {
    if(await copyText(generatedResumeDraft)) {setCopiedDraft(true);setTimeout(()=>setCopiedDraft(false),2000);}
  };

  return (
    <div className="space-y-6 pb-12">
      {uploading && <p role="status" className="p-4 bg-teal-50 rounded-xl text-teal-800 flex items-center gap-3">Parsing resume and checking evidence, career gaps and ATS alignment...</p>}
      {uploadError && !pasteModalOpen && <p role="alert" className="p-4 bg-red-50 text-red-800 rounded-xl flex items-center gap-3">{uploadError}</p>}
      {uploadSuccess && <p role="status" className="p-4 bg-emerald-50 text-emerald-800 rounded-xl flex items-center gap-3">{uploadSuccess}</p>}
      {/* Top Banner */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            
            <span>Resume Intelligence & Evidence Alignment</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Parses resume claims, flags unverified statements, checks ATS alignment against {targetCareer.title}, and exports modernized proof-backed resumes.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            disabled={uploading}
            onClick={() => {setUploadError('');setPasteModalOpen(true);}}
            className="px-3 py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl text-xs transition cursor-pointer flex items-center gap-1.5 border border-slate-200"
          >
            <UploadCloud className="w-3.5 h-3.5 text-teal-600" />
            <span>Upload / Paste Resume</span>
          </button>
          <button className="px-3 py-1.5 bg-teal-50 text-teal-800 border border-teal-200 rounded-xl text-xs font-semibold" onClick={()=>{setGeneratorOpened(true);setActiveTabSub('generator');}}>Generate Resume with AI</button>
          <button
            disabled={!hasResume || uploading}
            onClick={() => setExportModalOpen(true)}
            className="px-3 py-1.5 bg-teal-700 hover:bg-teal-800 text-white font-semibold rounded-xl text-xs transition cursor-pointer flex items-center gap-1.5 shadow-xs"
          >
            <Download className="w-3.5 h-3.5" />
            <span>Export Verified Draft</span>
          </button>
        </div>
      </div>

      <div role="tablist" aria-label="Resume intelligence views" className="flex flex-wrap gap-2 border-b pb-3">
       {(['overview','improvements','generator'] as const).map((id,i)=><button key={id} role="tab" aria-selected={activeTabSub===id} onClick={()=>{setActiveTabSub(id);if(id==='generator')setGeneratorOpened(true);}} className={'px-3 py-2 text-xs font-semibold rounded-lg '+(activeTabSub===id?'bg-teal-50 text-teal-800':'text-slate-500')}>{['Overview & Claims Map','Bullet Point Improver','AI Resume Generator'][i]}</button>)}
      </div>
      {generatorOpened&&<div hidden={activeTabSub!=='generator'}><ResumeGenerator/></div>}
      {!hasResume && activeTabSub!=='generator' && <div className="p-6 bg-white border border-slate-200 rounded-2xl text-sm text-slate-600 flex items-center gap-4"><p>Upload or paste your resume to analyze its sections, claims and alignment with {targetCareer.title}.</p></div>}
      {hasResume && activeTabSub!=='generator' && <>
      {/* Primary ATS & Match Score Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-3.5">
        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-xs font-semibold">Overall ATS Score</span>
            
          </div>
          <div className="text-2xl font-bold text-slate-900">{resumeAnalysis.atsCompatibilityScore} / 100</div>
          <div className="text-[11px] text-teal-700 font-medium mt-0.5">40% section structure + 40% role keywords + 20% evidence coverage</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-xs font-semibold">Target Role Match</span>
            <TrendingUp className="w-4 h-4 text-blue-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{resumeAnalysis.careerAlignmentScore}%</div>
          <div className="text-[11px] text-blue-700 font-medium mt-0.5">{targetCareer.title} keyword coverage</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-xs font-semibold">Sections Detected</span>
            <FileCheck2 className="w-4 h-4 text-purple-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{resumeAnalysis.sectionsDetected.length}</div>
          <div className="text-[11px] text-purple-700 font-medium mt-0.5">Based on uploaded text headings</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-xs font-semibold">Evidence Coverage</span>
            <ShieldCheck className="w-4 h-4 text-emerald-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{resumeAnalysis.evidenceCoveragePercent}%</div>
          <div className="text-[11px] text-emerald-700 font-medium mt-0.5">Claims backed by proof</div>
        </div>

        <div className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs">
          <div className="flex items-center justify-between text-slate-500 mb-1">
            <span className="text-xs font-semibold">Unverified Claims</span>
            <AlertCircle className="w-4 h-4 text-amber-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{unverifiedClaims.length}</div>
          <div className="text-[11px] text-amber-700 font-medium mt-0.5">Requires code/test proof</div>
        </div>
      </div>

      {activeTabSub === 'overview' ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Left: Verified vs Unverified Claims */}
          <div className="space-y-4">
            {/* Verified Skills */}
            {verifiedClaims.length > 0 && <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wide flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  <span>Verified Skills Found on Resume</span>
                </h4>
                <span className="text-xs text-emerald-700 font-bold bg-emerald-50 px-2 py-0.5 rounded">
                  {verifiedClaims.length} Verified
                </span>
              </div>
              <p className="text-xs text-slate-500">
                These claims have supporting verified skill evidence in the Evidence Vault. Repository links alone do not verify a claim.
              </p>
              <div className="space-y-2 pt-1">
                {verifiedClaims.map((item: ResumeClaim) => (
                  <div
                    key={item.id}
                    className="p-3 bg-emerald-50/40 border border-emerald-200 rounded-xl flex items-center justify-between text-xs"
                  >
                    <div>
                      <div className="font-bold text-slate-900">{item.skillName}</div>
                      <div className="text-[11px] text-slate-500 font-mono">"{item.claim}"</div>
                    </div>
                    <span className="text-[10px] bg-emerald-100 text-emerald-800 font-bold px-2 py-0.5 rounded">
                      Audited Proof
                    </span>
                  </div>
                ))}
              </div>
            </div>

            }
            {/* Unverified Claims */}
            {unverifiedClaims.length > 0 && <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wide flex items-center gap-1.5">
                  
                  <span>Unverified Resume Claims</span>
                </h4>
                <span className="text-xs text-amber-800 font-bold bg-amber-50 px-2 py-0.5 rounded">
                  {unverifiedClaims.length} Claims
                </span>
              </div>
              <p className="text-xs text-slate-500">
                Mentioned on resume, but lacking concrete assessment or verified project proof in your competency model. Click to inspect the exact gap.
              </p>
              <div className="space-y-2 pt-1">
                {unverifiedClaims.map((claim: ResumeClaim) => (
                  <div
                    key={claim.id}
                    role="button" tabIndex={0} aria-label={`Inspect Gap: ${claim.skillName}`}
                    onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();handleInspectSkill(claim.skillId);}}}
                    onClick={() => handleInspectSkill(claim.skillId)}
                    className="p-3 bg-amber-50/50 border border-amber-200 rounded-xl hover:bg-amber-50 transition cursor-pointer flex items-center justify-between"
                  >
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-bold text-xs text-slate-900">{claim.skillName}</span>
                        <span className="text-[10px] bg-amber-100 text-amber-800 font-semibold px-1.5 py-0.2 rounded">
                          {claim.evidenceState}
                        </span>
                      </div>
                      <div className="text-[11px] text-slate-500 font-mono mt-0.5">"{claim.claim}"</div>
                    </div>
                    <div className="flex items-center gap-1 text-xs font-semibold text-teal-700 shrink-0 ml-2">
                      <span>Inspect Gap</span>
                      <ArrowRight className="w-3 h-3" />
                    </div>
                  </div>
                ))}
              </div>
            </div>}
            {!resumeAnalysis.claims.length && <p className="p-4 text-sm text-slate-600">No catalog skill claims were found in this resume. No skills have been inferred or verified.</p>}
          </div>

          {/* Right: Missing Skills for Target Role & File Preview */}
          <div className="space-y-4">
            {resumeAnalysis.missingSkillsForTarget.length > 0 && <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs space-y-3">
              <div className="flex items-center justify-between">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wide flex items-center gap-1.5">
                  <AlertCircle className="w-4 h-4 text-rose-600" />
                  <span>Missing Role Keywords ({targetCareer.title})</span>
                </h4>
                <span className="text-xs text-rose-800 font-bold bg-rose-50 px-2 py-0.5 rounded">
                  {resumeAnalysis.missingSkillsForTarget.length} Missing
                </span>
              </div>
              <p className="text-xs text-slate-500">
                These selected-role catalog skills were not found in this resume. Add them only when accurate.
              </p>
              <div className="flex flex-wrap gap-1.5 pt-1">
                {resumeAnalysis.missingSkillsForTarget.map((skill: string, idx: number) => (
                  <span
                    key={idx}
                    className="px-2.5 py-1 bg-rose-50 text-rose-800 border border-rose-200 rounded-lg text-xs font-medium"
                  >
                    {skill}
                  </span>
                ))}
              </div>
            </div>

            }
            {/* Document Parsed Metadata Card */}
            <div className="p-4 bg-slate-50 border border-slate-200 rounded-2xl space-y-3 text-xs">
              <div className="flex items-center justify-between font-bold text-slate-900">
                <div className="flex items-center gap-2">
                  <FileCheck2 className="w-4 h-4 text-teal-600" />
                  <span>Parsed Document: {resumeAnalysis.fileName}</span>
                </div>
                <span className="text-slate-400 font-mono text-[11px]">{resumeAnalysis.uploadedAt}</span>
              </div>
              <p className="text-slate-600 text-[11px] leading-relaxed">
                Structured parsing detected {resumeAnalysis.sectionsDetected.length} sections, extracting {resumeAnalysis.extractedSkillsCount} unique skill claims ({verifiedClaims.length} verified, {unverifiedClaims.length} unverified). {resumeAnalysis.recommendedProofProject && <>Recommended proof project: <strong>{resumeAnalysis.recommendedProofProject}</strong>.</>}
              </p>
              {resumeAnalysis.parsedSections?.map((section,index)=><details key={`${section.name}-${index}`} className="border-t border-slate-200 pt-2">
                <summary className="capitalize font-semibold cursor-pointer">{section.name}</summary>
                <p className="whitespace-pre-wrap break-words mt-2 text-slate-600">{section.text}</p>
              </details>)}

            </div>
          </div>
        </div>
      ) : (
        /* Bullet Point Suggestions Tab */
        <div className="space-y-4">
          <div className="bg-teal-50/60 p-4 rounded-2xl border border-teal-200 text-xs text-teal-900 flex items-center justify-between">
            <div className="flex items-center gap-2">
              
              <span>
                <strong>Evidence-Backed Impact:</strong> Recommendations come from missing sections, role keywords and evidence gaps. They do not invent achievements or metrics.
              </span>
            </div>
          </div>

          {!resumeAnalysis.suggestedImprovements.length && <p className="text-sm text-slate-600">No recommendations from the current checks.</p>}
          <div className="space-y-3">
            {resumeAnalysis.suggestedImprovements.map((suggestion: string, idx: number) => (
              <div
                key={idx}
                className="bg-white rounded-2xl border border-slate-200/80 p-5 shadow-2xs space-y-3"
              >
                <div className="flex items-center justify-between text-xs">
                  <span className="font-bold text-slate-900">
                    Recommendation #{idx + 1}
                  </span>
                  <button
                    onClick={() => handleCopySuggestion(suggestion)}
                    className="px-2.5 py-1 bg-slate-100 hover:bg-teal-50 hover:text-teal-800 text-slate-700 rounded-lg text-xs font-semibold transition flex items-center gap-1 cursor-pointer"
                  >
                    <Copy className="w-3 h-3" />
                    <span>Copy Suggestion</span>
                  </button>
                </div>

                <div className="p-3 bg-emerald-50/50 border border-emerald-200 rounded-xl space-y-1">
                  <span className="text-[10px] font-bold uppercase text-emerald-800">
                    Resume Recommendation
                  </span>
                  <p className="text-emerald-950 font-medium text-xs leading-relaxed">
                    "{suggestion}"
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      </>}
      {/* Paste / Upload Resume Modal */}
      {pasteModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div ref={pasteRef} role="dialog" aria-modal="true" aria-label="Upload or Paste Resume" tabIndex={-1} className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-h-[90vh] overflow-y-auto max-w-lg w-full p-6 space-y-4">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
                <UploadCloud className="w-4 h-4 text-teal-600" />
                <span>Upload or Paste Resume</span>
              </h3>
              <UndoRedoControls/><button aria-label="Close resume upload" disabled={uploading} onClick={() => setPasteModalOpen(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                <X className="w-4 h-4" />
              </button>
            </div>

            {uploadError && <p role="alert" className="text-sm text-red-700">{uploadError}</p>}
            {uploading && <p role="status" className="text-sm text-teal-700">Parsing and saving analysis...</p>}
            <form onSubmit={handleParseCustomResume} className="space-y-4 text-xs">
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Paste Resume Content (Plain Text or Markdown)
                </label>
                <textarea
                  aria-label="Resume text" maxLength={100000} disabled={uploading}
                  rows={6}
                  value={pastedResumeText}
                  data-undo="true" onChange={(e) => setPastedResumeText(e.target.value)}
                  placeholder="Paste your education, skills section, or experience bullets here..."
                  className="w-full p-3 bg-slate-50 border border-slate-200 rounded-xl outline-hidden focus:border-teal-500 font-mono text-xs"
                />
              </div>

              <div onDragOver={e=>e.preventDefault()} onDrop={e=>{e.preventDefault();const file=e.dataTransfer.files[0];if(file)void parseResume(file);}} className="p-3 bg-slate-50 border border-dashed border-slate-300 rounded-xl text-center space-y-2">
                <FileText className="w-6 h-6 text-slate-400 mx-auto" />
                <input ref={fileInput} aria-label="Upload resume file" type="file" accept=".pdf,.txt,.md" className="sr-only" disabled={uploading} onChange={e=>{const file=e.target.files?.[0];if(file)void parseResume(file);}}/>
                <button type="button" disabled={uploading} onClick={()=>fileInput.current?.click()} className="px-4 py-2 bg-white border border-teal-300 rounded-xl font-semibold text-teal-800">Choose PDF / TXT file</button>
                <p className="text-[11px] text-slate-500">Or drop a file here. Up to 8 MB; text-based PDFs and UTF-8 text. Scanned PDFs require OCR.</p>
              </div>

              <div className="flex justify-end gap-2 pt-2 border-t border-slate-100">
                <button
                  type="button"
                  disabled={uploading}
                  onClick={() => setPasteModalOpen(false)}
                  className="px-4 py-2 border border-slate-200 rounded-xl text-slate-600 hover:bg-slate-50 font-semibold cursor-pointer"
                >
                  Cancel
                </button>
                <button
                  type="submit" disabled={uploading || !pastedResumeText.trim()}
                  className="px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white rounded-xl font-bold cursor-pointer shadow-xs"
                >
                  Parse & Align Competencies
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Export Updated Resume Draft Modal */}
      {exportModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-slate-900/60 backdrop-blur-xs">
          <div ref={exportRef} role="dialog" aria-modal="true" aria-label="Export Verified Draft" tabIndex={-1} className="bg-white rounded-2xl border border-slate-200 shadow-2xl max-w-2xl w-full p-6 space-y-4 max-h-[90vh] flex flex-col">
            <div className="flex items-center justify-between border-b border-slate-100 pb-3">
              <div className="flex items-center gap-2">
                <FileCode className="w-5 h-5 text-teal-600" />
                <div>
                  <h3 className="text-sm font-bold text-slate-900">Modernized Verified Resume Draft</h3>
                  <p className="text-[11px] text-slate-500">Uploaded content is self-reported; verified claims link to actual evidence.</p>
                </div>
              </div>
              <button aria-label="Close resume export" onClick={() => setExportModalOpen(false)} className="text-slate-400 hover:text-slate-600 cursor-pointer">
                <X className="w-4 h-4" />
              </button>
            </div>

            <div className="flex-1 overflow-y-auto bg-slate-950 text-slate-200 p-4 rounded-xl font-mono text-xs leading-relaxed border border-slate-800">
              <pre className="whitespace-pre-wrap">{generatedResumeDraft}</pre>
            </div>

            <div className="pt-3 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs text-slate-500">
                Status: <strong className="text-emerald-700 font-semibold">Review before use</strong>
              </span>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={handleCopyDraft}
                  className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-700 font-semibold rounded-xl text-xs flex items-center gap-1.5 cursor-pointer"
                >
                  {copiedDraft ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                  <span>{copiedDraft ? 'Copied!' : 'Copy Markdown'}</span>
                </button>
                <a
                  href={`data:text/markdown;charset=utf-8,${encodeURIComponent(generatedResumeDraft)}`}
                  download={`${student.name.replaceAll(' ', '_')}_Verified_Resume.md`}
                  className="px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white font-bold rounded-xl text-xs flex items-center gap-1.5 shadow-xs cursor-pointer"
                >
                  <Download className="w-3.5 h-3.5" />
                  <span>Download .md</span>
                </a>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
