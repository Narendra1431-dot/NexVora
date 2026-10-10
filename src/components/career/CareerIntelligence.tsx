import { useState } from 'react';
import { useAppState } from '../../lib/state/app-state';
import {
  Compass,
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Sparkles,
  TrendingUp,
  Search,
  Layers,
  BookOpen,
  Award,
  HelpCircle,
  Clock,
  ShieldCheck
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Legend
} from 'recharts';

export function CareerIntelligence() {
  const {
    careers,
    student,
    competencyNodes,
    setTargetCareer,
    selectedCareerId,
    setSelectedCareerId,
    setActiveTab
  } = useAppState();

  const [searchQuery, setSearchQuery] = useState('');

  const activeCareer = careers.find((c) => c.id === selectedCareerId) || careers[0];
  const isCurrentTarget = activeCareer.id === student.targetCareerId;

  const filteredCareers = careers.filter(
    (c) =>
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.category.toLowerCase().includes(searchQuery.toLowerCase())
  );

  // Compute Current vs Required mastery chart data
  const comparisonData = activeCareer.requiredCompetencies.map((req) => {
    const node = competencyNodes.find((n) => n.id === req.skillId);
    return {
      skillName: req.skillName.length > 18 ? `${req.skillName.slice(0, 16)}...` : req.skillName,
      Current: node ? node.mastery : 0,
      Required: req.requiredMastery
    };
  });

  // Categorize gaps for this career
  const directGaps = activeCareer.requiredCompetencies.filter((req) => {
    const node = competencyNodes.find((n) => n.id === req.skillId);
    return node && node.mastery < req.requiredMastery && node.state === 'Skill Gap';
  });

  const prereqGaps = activeCareer.requiredCompetencies.filter((req) => {
    const node = competencyNodes.find((n) => n.id === req.skillId);
    return node && node.state === 'Prerequisite Gap';
  });

  const evidenceGaps = activeCareer.requiredCompetencies.filter((req) => {
    const node = competencyNodes.find((n) => n.id === req.skillId);
    return node && (node.state === 'Estimated' || node.state === 'Unverified Claim' || node.evidenceCount < 2);
  });

  return (
    <div className="space-y-6 pb-12">
      {/* Top Banner: Career Search & Explorer */}
      <div className="bg-white p-5 rounded-2xl border border-slate-200/80 shadow-2xs flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-slate-900 tracking-tight flex items-center gap-2">
            
            <span>Market Benchmark & Career Intelligence</span>
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Compare evidenced competencies against curated role benchmarks. These profiles are planning guides, not live labor-market forecasts.
          </p>
        </div>

        <div className="relative w-full md:w-72">
          <Search className="w-3.5 h-3.5 text-slate-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search roles (e.g. AI Engineer, Data Scientist)..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1.5 bg-slate-50 border border-slate-200 rounded-xl text-xs outline-hidden focus:border-teal-500 text-slate-800"
          />
        </div>
      </div>

      {!filteredCareers.length && <div className="flex items-center gap-3 p-4 bg-white rounded-xl border border-slate-200"><p className="text-sm text-slate-600">No matching roles. Try a different title or category.</p></div>}
      {/* Role Picker Cards */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        {filteredCareers.map((c) => {
          const isSelected = c.id === activeCareer.id;
          const isTarget = c.id === student.targetCareerId;
          return (
            <div
              key={c.id}
              onClick={() => setSelectedCareerId(c.id)}
              className={`p-3.5 rounded-xl border interactive-card cursor-pointer flex flex-col justify-between ${
                isSelected
                  ? 'bg-teal-50/70 border-teal-500 shadow-xs ring-1 ring-teal-500'
                  : 'bg-white border-slate-200 hover:bg-slate-50'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-1">
                  <span className="text-[10px] font-semibold text-slate-400 truncate">{c.category}</span>
                  {isTarget && (
                    <span className="text-[9px] bg-teal-600 text-white font-bold px-1.5 py-0.2 rounded">
                      Target
                    </span>
                  )}
                </div>
                <div className="text-xs font-bold text-slate-900 line-clamp-1">{c.title}</div>
              </div>

              <div className="mt-3 pt-2 border-t border-slate-100 flex items-center justify-between text-xs">
                <span className="text-[10px] text-slate-500 font-medium">Readiness:</span>
                <span className="font-bold text-teal-800">{c.currentReadiness}%</span>
              </div>
            </div>
          );
        })}
      </div>

      {/* Selected Career Detailed View */}
      <div className="bg-white rounded-2xl border border-slate-200/80 shadow-2xs overflow-hidden">
        {/* Detail Header */}
        <div className="p-6 border-b border-slate-100 bg-slate-50 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2">
              <span className="text-xs font-semibold text-teal-700 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                {activeCareer.category}
              </span>
              <span className="text-xs text-slate-500">Market Demand: <strong className="text-slate-800">{activeCareer.marketDemand}</strong></span>
              <span className="text-xs text-slate-500">• Average Salary: <strong className="text-slate-800">{activeCareer.avgSalary}</strong></span>
            </div>
            <h3 className="text-xl font-bold text-slate-900 mt-1">{activeCareer.title}</h3>
            <p className="text-xs text-slate-600 max-w-2xl mt-1 leading-relaxed">{activeCareer.description}</p>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-3 shrink-0">
            <div className="text-right sm:mr-2">
              <div className="text-xs text-slate-500 font-medium">Your Role Readiness</div>
              <div className="text-2xl font-bold text-teal-700">{activeCareer.currentReadiness}%</div>
            </div>

            {isCurrentTarget ? (
              <span className="px-4 py-2 bg-emerald-50 text-emerald-800 border border-emerald-200 rounded-xl text-xs font-bold flex items-center gap-1.5">
                <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                <span>Current Active Target</span>
              </span>
            ) : (
              <button
                onClick={() => setTargetCareer(activeCareer.id)}
                className="px-4 py-2 bg-teal-700 hover:bg-teal-800 text-white rounded-xl text-xs font-bold transition shadow-xs flex items-center gap-1.5 cursor-pointer"
              >
                <Sparkles className="w-4 h-4" />
                <span>Set As Target Career & Recalculate</span>
              </button>
            )}
          </div>
        </div>

        {/* Current vs Required Mastery Chart */}
        <div className="p-6 border-b border-slate-100">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                Current Mastery vs Target Role Benchmark
              </h4>
              <p className="text-[11px] text-slate-500">
                Direct side-by-side gap visualization for key required competencies
              </p>
            </div>
            <div className="flex items-center gap-4 text-xs">
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 bg-teal-600 rounded-xs" />
                <span className="text-slate-700 font-medium">Your Current Mastery</span>
              </div>
              <div className="flex items-center gap-1.5">
                <div className="w-3 h-3 bg-slate-300 rounded-xs" />
                <span className="text-slate-500 font-medium">Required Benchmark</span>
              </div>
            </div>
          </div>

          <div className="h-64 w-full">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={comparisonData}>
                <XAxis dataKey="skillName" tick={{ fill: '#475569', fontSize: 10 }} axisLine={false} tickLine={false} />
                <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} />
                <Tooltip
                  formatter={(val: any, name: any) => [`${val}%`, name]}
                  contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', color: '#fff', fontSize: '11px' }}
                />
                <Bar dataKey="Current" fill="#0d9488" radius={[4, 4, 0, 0]} />
                <Bar dataKey="Required" fill="#cbd5e1" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Four-Pillar Career Gap Analysis */}
        <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 bg-slate-50/50">
          {/* 1. Direct Gaps */}
          <div className="p-4 bg-white rounded-xl border border-slate-200/80 shadow-2xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-xs text-amber-900 uppercase">Direct Skill Gaps</span>
              <span className="text-[11px] bg-amber-100 text-amber-800 font-bold px-1.5 py-0.2 rounded">
                {directGaps.length} Found
              </span>
            </div>
            <p className="text-[11px] text-slate-500">
              Competencies directly below role requirements without prerequisite impediments.
            </p>
            <div className="space-y-1.5 pt-1 text-xs">
              {directGaps.length === 0 ? (
                <div className="text-slate-400 text-[11px]">No direct unblocked gaps</div>
              ) : (
                directGaps.map((g) => (
                  <div key={g.skillId} className="p-2 bg-amber-50/60 border border-amber-200 rounded-lg">
                    <div className="font-semibold text-slate-900">{g.skillName}</div>
                    <div className="text-[10px] text-amber-800 font-medium">Why: Current mastery 46% vs required {g.requiredMastery}%.</div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* 2. Prerequisite Gaps */}
          <div className="p-4 bg-white rounded-xl border border-slate-200/80 shadow-2xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-xs text-rose-900 uppercase">Prerequisite Gaps</span>
              <span className="text-[11px] bg-rose-100 text-rose-800 font-bold px-1.5 py-0.2 rounded">
                {prereqGaps.length} Blocked
              </span>
            </div>
            <p className="text-[11px] text-slate-500">
              Advanced role requirements blocked by incomplete foundational skills.
            </p>
            <div className="space-y-1.5 pt-1 text-xs">
              {prereqGaps.length === 0 ? (
                <div className="text-slate-400 text-[11px]">Prerequisites satisfied</div>
              ) : (
                prereqGaps.map((g) => (
                  <div key={g.skillId} className="p-2 bg-rose-50/60 border border-rose-200 rounded-lg">
                    <div className="font-semibold text-slate-900">{g.skillName}</div>
                    <div className="text-[10px] text-rose-800 font-medium">Why: Requires PyTorch (≥80%) and Transformers (≥75%) first.</div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* 3. Evidence Gaps */}
          <div className="p-4 bg-white rounded-xl border border-slate-200/80 shadow-2xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-xs text-sky-900 uppercase">Evidence Gaps</span>
              <span className="text-[11px] bg-sky-100 text-sky-800 font-bold px-1.5 py-0.2 rounded">
                {evidenceGaps.length} Unverified
              </span>
            </div>
            <p className="text-[11px] text-slate-500">
              Skills where self-reported claims exist but lack verified commit/rubric proof.
            </p>
            <div className="space-y-1.5 pt-1 text-xs">
              {evidenceGaps.slice(0, 2).map((g) => (
                <div key={g.skillId} className="p-2 bg-sky-50/60 border border-sky-200 rounded-lg">
                  <div className="font-semibold text-slate-900">{g.skillName}</div>
                  <div className="text-[10px] text-sky-800 font-medium">Why: Self-reported on resume; needs project proof.</div>
                </div>
              ))}
            </div>
          </div>

          {/* 4. Knowledge Debt */}
          <div className="p-4 bg-white rounded-xl border border-slate-200/80 shadow-2xs space-y-2">
            <div className="flex items-center justify-between">
              <span className="font-bold text-xs text-purple-900 uppercase">Knowledge Debt</span>
              <span className="text-[11px] bg-purple-100 text-purple-800 font-bold px-1.5 py-0.2 rounded">
                Low Risk
              </span>
            </div>
            <p className="text-[11px] text-slate-500">
              Outdated or unassessed skills that risk decaying confidence if not periodically refreshed.
            </p>
            <div className="p-2 bg-purple-50/60 border border-purple-200 rounded-lg text-xs">
              <div className="font-semibold text-slate-900">Docker Microservices</div>
              <div className="text-[10px] text-purple-800 font-medium">Assessed 60 days ago; periodic re-verification advised.</div>
            </div>
          </div>
        </div>

        {/* Recommended Certifications & Projects for this Role */}
        <div className="p-6 grid grid-cols-1 md:grid-cols-2 gap-6 border-t border-slate-100">
          <div>
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wide mb-2 flex items-center gap-1.5">
              <Award className="w-4 h-4 text-teal-600" />
              <span>Recommended Industry Certifications</span>
            </h4>
            <div className="space-y-2 text-xs">
              {activeCareer.recommendedCertifications.map((cert, idx) => (
                <div key={idx} className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between">
                  <span className="font-semibold text-slate-800">{cert}</span>
                  <span className="text-[10px] bg-teal-50 text-teal-800 border border-teal-200 font-bold px-2 py-0.5 rounded">
                    High Alignment
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div>
            <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wide mb-2 flex items-center gap-1.5">
              <BookOpen className="w-4 h-4 text-blue-600" />
              <span>Recommended Verification Proof Projects</span>
            </h4>
            <div className="space-y-2 text-xs">
              {activeCareer.recommendedProjects.map((pId) => (
                <div key={pId} className="p-3 bg-slate-50 border border-slate-200 rounded-xl flex items-center justify-between">
                  <div>
                    <div className="font-semibold text-slate-800">
                      {pId === 'proj-rag-hybrid'
                        ? 'Enterprise Hybrid RAG System with Re-ranking'
                        : pId === 'proj-transformer-from-scratch'
                        ? 'Autoregressive Transformer Decoder from Scratch'
                        : 'Production vLLM Inference Serving Benchmark'}
                    </div>
                    <div className="text-[10px] text-slate-500">Provides verified rubric proof</div>
                  </div>
                  <button
                    onClick={() => setActiveTab('projects')}
                    className="px-2.5 py-1 bg-white border border-slate-200 text-slate-700 hover:bg-teal-50 hover:text-teal-800 rounded-lg text-xs font-semibold transition cursor-pointer"
                  >
                    View
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
