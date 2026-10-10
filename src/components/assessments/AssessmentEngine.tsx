import { useState } from 'react';
import { useAppState } from '../../lib/state/app-state';
import {
  CheckSquare,
  Clock,
  Award,
  Sparkles,
  ArrowRight,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  HelpCircle,
  RotateCcw,
  TrendingUp,
  ChevronRight,
  ListOrdered
} from 'lucide-react';
import { AssessmentItem } from '../../types';

export function AssessmentEngine() {
  const {
    selectedSkillId,
    catalogSelection,
    assessments,
    completeAssessment,
    setActiveTab,
    targetCareer
  } = useAppState();

  const [selectedAssessmentId, setSelectedAssessmentId] = useState<string>(
    (catalogSelection?.tab === 'assessments' ? catalogSelection.id : null) || assessments.find(a=>a.skillId===selectedSkillId)?.id || assessments[0]?.id || ''
  );

  const selectedAssessment =
    assessments.find((a) => a.id === selectedAssessmentId) || assessments[0];

  // In-test state
  const [inProgress, setInProgress] = useState(false);
  const [currentQIndex, setCurrentQIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<number, any>>({});
  const [confidenceRatings, setConfidenceRatings] = useState<Record<number, 'Low' | 'Medium' | 'High'>>({});
  const [showHint, setShowHint] = useState(false);
  const [testCompleted, setTestCompleted] = useState(false);
  const [computedScore, setComputedScore] = useState(0);
  const [beforeReadiness, setBeforeReadiness] = useState(0);
  const [beforeMastery, setBeforeMastery] = useState(0);

  const startTest = (id: string) => {
    setSelectedAssessmentId(id);
    setInProgress(true);
    setCurrentQIndex(0);
    setAnswers({});
    setConfidenceRatings({});
    setShowHint(false);
    setTestCompleted(false);
  };

  const currentQ = selectedAssessment?.questions[currentQIndex];

  const handleSelectOption = (optIdx: number) => {
    if(currentQ?.type === 'Multiple Select') {
      const selected: number[] = answers[currentQIndex] || [];
      setAnswers({...answers,[currentQIndex]:selected.includes(optIdx)?selected.filter(v=>v!==optIdx):[...selected,optIdx]});
    } else setAnswers({ ...answers, [currentQIndex]: optIdx });
  };

  const handleSelectConfidence = (level: 'Low' | 'Medium' | 'High') => {
    setConfidenceRatings({ ...confidenceRatings, [currentQIndex]: level });
  };

  const handleNextQ = () => {
    if (selectedAssessment && currentQIndex < selectedAssessment.questions.length - 1) {
      setCurrentQIndex(currentQIndex + 1);
      setShowHint(false);
    } else {
      finishTest();
    }
  };

  const finishTest = async () => {
    if (!selectedAssessment) return;
    const keyed = Object.fromEntries(selectedAssessment.questions.map((q, i) => [q.id, answers[i]]));
    const result = await completeAssessment(selectedAssessment.id, keyed, 0, 0);
    if (!result) return;
    setBeforeReadiness(result.attempt.beforeReadiness); setBeforeMastery(result.attempt.beforeMastery);
    setComputedScore(result.attempt.score);
    setTestCompleted(true); setInProgress(false);
  };

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <CheckSquare className="w-5 h-5 text-teal-600" />
            <span>Adaptive Diagnostic & Skill Verification Engine</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Real-time mastery evaluations that directly convert unverified claims into verified competency signals.
          </p>
        </div>

        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-500 font-medium">Standard:</span>
          <span className="font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
            Server-scored assessment
          </span>
        </div>
      </div>

      {!testCompleted && !inProgress && <div className="flex items-center gap-3 rounded-xl border border-teal-100 bg-teal-50/40 px-4 py-3"><p className="text-xs leading-relaxed text-slate-600"><strong className="block text-slate-800">One step toward a clearer learning plan.</strong>Use this assessment to discover what you know and what to practice next.</p></div>}
      {testCompleted ? (
        /* Mode A: Evaluation Results & Cascading Update Feedback */
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-2xs space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-slate-100">
            <div>
              <div className="flex items-center gap-2">
                
                <h3 className="text-base font-bold text-slate-900">
                  Assessment Complete: {selectedAssessment.title}
                </h3>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Your performance has been evaluated and committed to your living competency model.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-center min-w-[100px]">
                <div className="text-xs text-emerald-800 font-medium">Evaluation Score</div>
                <div className="text-2xl font-bold text-emerald-700">{computedScore}%</div>
              </div>
              <div className="p-3 bg-teal-50 border border-teal-200 rounded-xl text-center min-w-[100px]">
                <div className="text-xs text-teal-800 font-medium">Status</div>
                <div className="text-xs font-bold text-teal-700 uppercase mt-1">{computedScore >= 75 ? 'Passed' : 'Needs practice'}</div>
              </div>
            </div>
          </div>

          <div className="bg-slate-50 border rounded-xl p-4 text-sm space-y-2">
            <p>Score: {computedScore}%. Evidence was recorded from your submitted answers.</p>
            <p>Before: skill mastery {beforeMastery}%. Career readiness changed from {beforeReadiness}% to {targetCareer.currentReadiness}%. Mastery, confidence and milestone locks were recomputed from all evidence.</p>
            <p>Passing an assessment does not guarantee a verified skill if prerequisites or overall mastery remain below target.</p>
          </div>
          <button onClick={()=>setActiveTab('certificates')} className="text-sm font-semibold text-teal-700 hover:underline">Check course certificate eligibility</button>
          {/* Next Steps CTA */}
          <div className="pt-2 flex flex-col sm:flex-row items-center justify-between gap-3 border-t border-slate-100">
            <button
              onClick={() => startTest(selectedAssessment.id)}
              className="px-4 py-2 text-xs font-semibold text-slate-600 hover:text-slate-900 flex items-center gap-1.5 cursor-pointer"
            >
              <RotateCcw className="w-3.5 h-3.5" />
              <span>Retake Diagnostic</span>
            </button>

            <div className="flex items-center gap-2">
              <button
                onClick={() => setActiveTab('competencies')}
                className="px-4 py-2 bg-slate-100 hover:bg-slate-200 text-slate-800 rounded-xl text-xs font-semibold transition cursor-pointer"
              >
                View Competency Graph
              </button>
              <button
                onClick={() => setActiveTab('roadmap')}
                className="px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-xs cursor-pointer"
              >
                <span>View Updated Roadmap</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </button>
            </div>
          </div>
        </div>
      ) : inProgress && currentQ ? (
        /* Mode B: Active Test Runner Screen */
        <div className="bg-white rounded-2xl border border-slate-200/80 p-6 shadow-2xs space-y-6">
          {/* Header with question counter and timer */}
          <div className="flex items-center justify-between pb-4 border-b border-slate-100">
            <div>
              <span className="text-[10px] font-bold uppercase text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                Question {currentQIndex + 1} of {selectedAssessment.questions.length}
              </span>
              <h3 className="text-sm font-bold text-slate-900 mt-1">{selectedAssessment.title}</h3>
            </div>
            <div className="flex items-center gap-1.5 text-xs text-slate-600 font-mono bg-slate-100 px-3 py-1 rounded-lg">
              
              <span>Untimed practice assessment</span>
            </div>
          </div>

          {/* Question Text */}
          <div className="space-y-3">
            <h4 className="text-sm font-semibold text-slate-900 leading-relaxed">
              {currentQ.question}
            </h4>

            {currentQ.codeSnippet && (
              <pre className="p-3 bg-slate-950 text-slate-100 rounded-xl font-mono text-xs overflow-x-auto border border-slate-800">
                <code>{currentQ.codeSnippet}</code>
              </pre>
            )}
          </div>

          {/* Options */}
          <div className="space-y-2.5">
            {(currentQ.options || []).map((opt, idx) => {
              const isSelected = Array.isArray(answers[currentQIndex]) ? answers[currentQIndex].includes(idx) : answers[currentQIndex] === idx;
              return (
                <div
                  key={idx}
                  role="button" tabIndex={0} aria-pressed={isSelected}
                  onKeyDown={e=>{if(e.key==='Enter' || e.key===' ') {e.preventDefault();handleSelectOption(idx);}}}
                  onClick={() => handleSelectOption(idx)}
                  className={`p-3.5 rounded-xl border text-xs interactive-card cursor-pointer flex items-center justify-between ${
                    isSelected
                      ? 'bg-teal-50 border-teal-500 font-semibold text-teal-950 ring-1 ring-teal-500'
                      : 'bg-white border-slate-200 hover:bg-slate-50 text-slate-700'
                  }`}
                >
                  <div className="flex items-center gap-3">
                    <span
                      className={`w-6 h-6 rounded-md flex items-center justify-center text-[11px] font-bold ${
                        isSelected ? 'bg-teal-700 text-white' : 'bg-slate-100 text-slate-600'
                      }`}
                    >
                      {String.fromCharCode(65 + idx)}
                    </span>
                    <span>{opt}</span>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Confidence Self-Rating */}
          <div className="p-3 bg-slate-50 rounded-xl border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs">
            <span className="font-semibold text-slate-700">Self-Assessed Confidence:</span>
            <div className="flex items-center gap-2">
              {(['Low', 'Medium', 'High'] as const).map((level) => {
                const isSelected = confidenceRatings[currentQIndex] === level;
                return (
                  <button
                    key={level}
                    type="button"
                    onClick={() => handleSelectConfidence(level)}
                    className={`px-3 py-1 rounded-lg font-semibold transition cursor-pointer text-xs ${
                      isSelected
                        ? 'bg-teal-700 text-white shadow-xs'
                        : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-100'
                    }`}
                  >
                    {level}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Explanation / Hint Drawer */}
          <div>
            <button
              onClick={() => setShowHint(!showHint)}
              className="text-xs text-teal-700 hover:underline flex items-center gap-1 font-medium cursor-pointer"
            >
              <HelpCircle className="w-3.5 h-3.5" />
              <span>{showHint ? 'Hide Rationale' : 'View Concept Rationale'}</span>
            </button>
            {showHint && (
              <div className="mt-2 p-3 bg-teal-50/70 border border-teal-200 rounded-xl text-xs text-teal-900 leading-relaxed">
                <strong>Hint:</strong> Identify the core concept and compare each option carefully. Explanations are provided after submission.
              </div>
            )}
          </div>

          {currentQ.type === 'Short Answer' && <label className="block text-sm">Your answer<input aria-label="Your answer" value={answers[currentQIndex] || ''} onChange={e=>setAnswers({...answers,[currentQIndex]:e.target.value})} className="block border rounded p-3 w-full" /></label>}
          {/* Navigation Controls */}
          <div className="pt-4 border-t border-slate-100 flex items-center justify-between">
            <button
              disabled={currentQIndex === 0}
              onClick={() => setCurrentQIndex(currentQIndex - 1)}
              className="px-3 py-1.5 border border-slate-200 rounded-lg text-xs font-semibold text-slate-600 hover:bg-slate-50 disabled:opacity-40 cursor-pointer"
            >
              Previous
            </button>

            <button
              onClick={handleNextQ}
              disabled={answers[currentQIndex] === undefined}
              className="px-4 py-2 bg-teal-700 hover:bg-teal-800 disabled:opacity-50 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-xs cursor-pointer"
            >
              <span>{currentQIndex === selectedAssessment.questions.length - 1 ? 'Submit & Verify' : 'Next Question'}</span>
              <ChevronRight className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      ) : (
        /* Mode C: Pre-Assessment Catalog & Detail Screen */
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Assessment List */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
              Available Skill Assessments ({assessments.length})
            </h3>
            <div className="space-y-2">
              {assessments.map((a) => {
                const isSelected = a.id === selectedAssessment?.id;
                return (
                  <div
                    key={a.id}
                    onClick={() => setSelectedAssessmentId(a.id)}
                    className={`p-3.5 rounded-xl border transition cursor-pointer ${
                      isSelected
                        ? 'bg-teal-50/70 border-teal-500 shadow-xs'
                        : 'bg-white border-slate-200 hover:bg-slate-50'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-[10px] bg-slate-100 text-slate-600 font-bold px-1.5 py-0.2 rounded">
                        {a.category}
                      </span>
                      <span className="text-[11px] text-slate-500">{a.estimatedTime}</span>
                    </div>
                    <div className="text-xs font-bold text-slate-900">{a.title}</div>
                    <div className="text-[11px] text-slate-500 mt-1">Skill: {a.skillName}</div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Selected Assessment Pre-Test Overview Card */}
          {selectedAssessment && (
            <div className="md:col-span-2 bg-white rounded-2xl border border-slate-200/80 p-6 shadow-2xs space-y-5">
              <div className="flex items-start justify-between">
                <div>
                  <span className="text-[10px] font-bold uppercase text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                    {selectedAssessment.category}
                  </span>
                  <h3 className="text-lg font-bold text-slate-900 mt-1">{selectedAssessment.title}</h3>
                  <p className="text-xs text-slate-600 mt-1">
                    Validates core concepts and implementation patterns in {selectedAssessment.skillName}.
                  </p>
                </div>
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                  <span className="text-slate-400">Duration:</span>
                  <div className="font-bold text-slate-900 mt-0.5">{selectedAssessment.estimatedTime}</div>
                </div>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                  <span className="text-slate-400">Passing Score:</span>
                  <div className="font-bold text-teal-700 mt-0.5">80%</div>
                </div>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                  <span className="text-slate-400">Questions:</span>
                  <div className="font-bold text-slate-900 mt-0.5">{selectedAssessment.questions.length} Items</div>
                </div>
                <div className="p-3 bg-slate-50 border border-slate-200 rounded-xl">
                  <span className="text-slate-400">Target Skill:</span>
                  <div className="font-bold text-slate-900 mt-0.5">{selectedAssessment.skillName}</div>
                </div>
              </div>

              <div className="p-4 bg-teal-50/50 border border-teal-200 rounded-xl space-y-2 text-xs">
                <div className="font-bold text-teal-900 flex items-center gap-2">
                  <Sparkles className="w-4 h-4 text-teal-700" />
                  <span>Verification Impact Preview:</span>
                </div>
                <p className="text-teal-800 leading-relaxed text-[11px]">
                  Achieving ≥80% will provide assessment evidence for{' '}
                  <strong>{selectedAssessment.skillName}</strong>, record scored evidence. Mastery and milestone status depend on all your evidence and prerequisites.
                </p>
              </div>

              <button
                onClick={() => startTest(selectedAssessment.id)}
                className="w-full py-3 bg-teal-700 hover:bg-teal-800 text-white rounded-xl font-bold text-xs transition flex items-center justify-center gap-2 shadow-xs cursor-pointer"
              >
                <span>Begin Assessment Evaluation</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
