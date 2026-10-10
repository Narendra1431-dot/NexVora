import { useAppState } from '../../lib/state/app-state';
import { Play, RotateCcw, ChevronRight, Sparkles, X, ChevronLeft } from 'lucide-react';

const DEMO_STEPS = [
  { step: 1, label: '1. Resume Evidence', tab: 'resume', desc: 'Observe self-reported claims & ATS gap analysis' },
  { step: 2, label: '2. Baseline Diagnostic', tab: 'assessments', desc: 'Diagnose foundational knowledge' },
  { step: 3, label: '3. Target: AI Engineer', tab: 'careers', desc: 'Set career target & calculate initial readiness' },
  { step: 4, label: '4. Competency Graph', tab: 'competencies', desc: 'Explore interactive living skill network & drawer' },
  { step: 5, label: '5. Career Gap Analysis', tab: 'careers', desc: 'Diagnose direct, prereq, and evidence gaps' },
  { step: 6, label: '6. Adaptive Roadmap', tab: 'roadmap', desc: 'Plan state-driven milestones with prerequisite locks' },
  { step: 7, label: '7. Grounded Resources', tab: 'resources', desc: 'Curated learning with "Why this?" rationale' },
  { step: 8, label: '8. Adaptive Assessment', tab: 'assessments', desc: 'Take PyTorch test & trigger instant competency jump' },
  { step: 9, label: '9. Project Verification', tab: 'projects', desc: 'Verify RAG Capstone & produce high-weight proof' },
  { step: 10, label: '10. Readiness & Resume Jump', tab: 'dashboard', desc: 'Verify how readiness & verified claims increased' }
];

export function HackathonDemoBar() {
  const {
    demoStep,
    setDemoStep,
    triggerHackathonStep,
    isDemoBarVisible,
    setIsDemoBarVisible,
    resetDemo,
    student,
    targetCareer
  } = useAppState();

  if (!student.isDemo) return null;

  if (!isDemoBarVisible) {
    return (
      <div className="bg-slate-900 text-white px-4 py-1.5 flex items-center justify-between text-xs border-b border-slate-800">
        <div className="flex items-center gap-2">
          <span className="inline-flex items-center gap-1 font-medium text-teal-400">
            <Sparkles className="w-3.5 h-3.5" />
            Hackathon Demo Flow:
          </span>
          <span className="text-slate-300">
            Current Persona: <strong className="text-white">{student.name}</strong> → Target:{' '}
            <strong className="text-white">{targetCareer.title}</strong> ({targetCareer.currentReadiness}% Ready)
          </span>
        </div>
        <button
          onClick={() => setIsDemoBarVisible(true)}
          className="text-xs text-slate-400 hover:text-white underline cursor-pointer"
        >
          Show Guided Demo Bar
        </button>
      </div>
    );
  }

  const currentStepObj = DEMO_STEPS[demoStep - 1] || DEMO_STEPS[0];

  const handleNext = () => {
    if (demoStep < DEMO_STEPS.length) {
      triggerHackathonStep(demoStep + 1);
    }
  };

  const handlePrev = () => {
    if (demoStep > 1) {
      triggerHackathonStep(demoStep - 1);
    }
  };

  return (
    <div className="bg-slate-900 text-slate-100 border-b border-slate-800 px-4 py-2.5 shadow-md">
      <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-3">
        {/* Left Badge & Current Step Indicator */}
        <div className="flex items-center gap-2.5 shrink-0">
          <div className="flex items-center gap-1.5 bg-teal-950 border border-teal-800/80 px-2.5 py-1 rounded-md text-teal-300 font-semibold text-xs tracking-wide">
            <Sparkles className="w-3.5 h-3.5 text-teal-400 animate-pulse" />
            <span>HACKATHON DEMO TOUR</span>
          </div>
          <div className="text-xs text-slate-300 hidden sm:block">
            Step <strong className="text-white font-semibold">{demoStep} of {DEMO_STEPS.length}</strong>:
            <span className="ml-1 text-teal-300 font-medium">{currentStepObj.desc}</span>
          </div>
        </div>

        {/* Step Selector Pills */}
        <div className="flex items-center gap-1 overflow-x-auto w-full md:w-auto py-1 no-scrollbar text-xs">
          {DEMO_STEPS.map((s) => {
            const isCurrent = s.step === demoStep;
            return (
              <button
                key={s.step}
                onClick={() => triggerHackathonStep(s.step)}
                className={`px-2 py-1 rounded text-xs font-medium whitespace-nowrap transition cursor-pointer ${
                  isCurrent
                    ? 'bg-teal-600 text-white font-semibold shadow-sm ring-1 ring-teal-400'
                    : 'bg-slate-800/70 text-slate-300 hover:bg-slate-700 hover:text-white'
                }`}
                title={s.desc}
              >
                {s.step}
              </button>
            );
          })}
        </div>

        {/* Controls */}
        <div className="flex items-center gap-2 shrink-0 self-end md:self-center">
          <button
            onClick={handlePrev}
            disabled={demoStep === 1}
            className="px-2 py-1 bg-slate-800 text-slate-300 hover:text-white disabled:opacity-40 rounded text-xs flex items-center gap-1 transition cursor-pointer"
            aria-label="Previous demo step"
          >
            <ChevronLeft className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">Prev</span>
          </button>

          <button
            onClick={handleNext}
            disabled={demoStep === DEMO_STEPS.length}
            className="px-2.5 py-1 bg-teal-500 hover:bg-teal-400 text-slate-950 font-semibold disabled:opacity-40 rounded text-xs flex items-center gap-1 transition shadow-sm cursor-pointer"
          >
            <span>Next Step</span>
            <ChevronRight className="w-3.5 h-3.5" />
          </button>

          <button
            onClick={resetDemo}
            className="px-2 py-1 bg-slate-800/80 hover:bg-slate-700 text-slate-300 hover:text-rose-300 rounded text-xs flex items-center gap-1 transition cursor-pointer border border-slate-700"
            title="Reset to initial baseline persona"
          >
            <RotateCcw className="w-3 h-3" />
            <span className="hidden sm:inline">Reset</span>
          </button>

          <button
            onClick={() => setIsDemoBarVisible(false)}
            className="text-slate-400 hover:text-white p-1 rounded transition ml-1"
            title="Hide Guided Demo Bar"
            aria-label="Hide Guided Demo Bar"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </div>
  );
}
