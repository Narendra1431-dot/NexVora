import {CareerIntelligencePanel} from '../common/CareerIntelligencePanel';
import { useState } from 'react';
import { useAppState } from '../../lib/state/app-state';
import {
  TrendingUp,
  ShieldCheck,
  Clock,
  AlertCircle,
  Award,
  Flame,
  ArrowRight,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Calendar,
  Layers,
  FileCheck2,
  BookOpen,
  FolderGit2,
  CheckCircle2,
  HelpCircle,
  CheckSquare,
  Activity
} from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  RadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  AreaChart,
  Area
} from 'recharts';
import DesignButton from '../common/DesignButton';
import { motion } from 'motion/react';

export function CommandCenter() {
  const {
    mission,
    intelligence,
    student,
    targetCareer,
    competencyNodes,
    evidenceItems,
    roadmap,
    activities,
    resources,
    projects,
    assessments,
    setActiveTab,
    setSelectedSkillId,
    setDemoStep
  } = useAppState();

  const [expandedReason, setExpandedReason] = useState(false);
  const [chartView, setChartView] = useState<'radar' | 'trend'>('trend');

  // Compute summary stats dynamically from living model
  const verifiedSkillsCount = competencyNodes.filter((n) => n.state === 'Verified').length;
  const inProgressSkillsCount = competencyNodes.filter((n) => n.state === 'In Progress').length;
  const criticalGapsCount = competencyNodes.filter(
    (n) => (n.state === 'Skill Gap' || n.state === 'Prerequisite Gap') && targetCareer.requiredCompetencies.some(r=>r.skillId===n.id && r.importance==='Required')
  ).length;

  const avgConfidence = Math.round(
    evidenceItems.reduce((acc, e) => acc + e.confidenceScore, 0) / (evidenceItems.length || 1)
  );

  const completedMilestones = roadmap.filter((m) => m.state === 'Completed').length;
  const roadmapPercent = Math.round((completedMilestones / Math.max(1, roadmap.length)) * 100);

  // Domain mastery distribution for charts
  const domainMasteryData = [...new Set(competencyNodes.map(n => n.domain))].map(domain => {
    const nodes = competencyNodes.filter(n => n.domain === domain);
    return {domain, mastery:Math.round(nodes.reduce((sum,n)=>sum+n.mastery,0)/Math.max(1,nodes.length)),target:85};
  });
  const readinessTrendData = [{checkpoint:'Current evidenced state',readiness:targetCareer.currentReadiness,benchmark:85}];
  const weeklyActivityData: {day:string;hours:number;assessments:number}[] = [];

  // Priority Gaps list
  const priorityGaps = competencyNodes
    .filter((n) => n.state === 'Skill Gap' || n.state === 'Prerequisite Gap')
    .slice(0, 3);

  const topRecommendedProject = projects[0];
  const topRecommendedResource = resources[0];
  const upcomingAssessment = assessments[0];

  return (
    <div className="space-y-6 pb-12">
      {intelligence && <section className="bg-white border border-slate-200 rounded-xl p-4 text-sm space-y-2" aria-label="Synthetic model advisory">
        <h3 className="font-semibold">Learning risk advisory: {intelligence.learningRisk.level}</h3>
        <p>Synthetic demo model score: {Math.round(intelligence.learningRisk.score * 100)} / 100. This is not a measured probability of failure.</p>
        <p>{intelligence.evidenceStrength.length} evidence records classified for advisory strength. These labels do not verify skills.</p>
        <p className="text-xs text-slate-500">{intelligence.limitation}</p>
      </section>}

      {/* Top Welcome Section */}
      <motion.div 
        className="bg-slate-900 text-white rounded-2xl p-6 shadow-sm border border-slate-800 flex flex-col md:flex-row md:items-center justify-between gap-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: 'easeOut' }}
      >
        <div className="space-y-2">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-teal-300 bg-teal-950/80 px-2.5 py-0.5 rounded-full border border-teal-700/60">
              Living Competency Model
            </span>
            <span className="text-xs text-slate-400">
              Synchronized {student.lastCompetencyUpdate}
            </span>
          </div>
          <h2 className="text-xl md:text-2xl font-bold tracking-tight text-white flex items-center gap-3">
            
            Welcome back, {student.name}
          </h2>
          <p className="text-xs text-slate-300 max-w-2xl leading-relaxed">
            Targeting <strong className="text-teal-300 font-semibold">{targetCareer.title}</strong>. 
            Your current validated career readiness is{' '}
            <span className="font-bold text-teal-300 text-sm">{targetCareer.currentReadiness}%</span>.
            {targetCareer.currentReadiness < 80 ? (
              <span> Complete assessments and submit reviewed projects to close your evidence gaps.</span>
            ) : (
              <span> You have satisfied priority career benchmarks and verified core deep learning requirements!</span>
            )}
          </p>
        </div>

        <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 shrink-0">
          <DesignButton
            onClick={() => setActiveTab('roadmap')}
            className="w-full sm:w-auto px-4 py-2.5 bg-teal-500 hover:bg-teal-400 text-slate-950 font-bold text-xs rounded-xl transition flex items-center justify-center gap-2 shadow-xs cursor-pointer"
            variant="primary"
            size="sm"
          >
            <span>Continue Roadmap</span>
            <ArrowRight className="w-4 h-4" />
          </DesignButton>
          <DesignButton
            onClick={() => setActiveTab('competencies')}
            className="w-full sm:w-auto px-3.5 py-2.5 bg-slate-800/80 hover:bg-slate-700 text-slate-200 text-xs font-semibold rounded-xl border border-slate-700 transition flex items-center justify-center gap-1.5 cursor-pointer"
            variant="primary"
            size="sm"
          >
            <Layers className="w-3.5 h-3.5 text-teal-400" />
            <span>Graph View</span>
          </DesignButton>
        </div>
      </motion.div>

      {/* Primary Metrics Summary Row */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3.5">
        <motion.div 
          className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: 'easeOut' }}
          whileHover={{ scale: 1.02, boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)' }}
        >
          <div className="flex items-center justify-between text-slate-500 mb-1.5">
            <span className="text-xs font-semibold">Career Readiness</span>
            
          </div>
          <div className="text-2xl font-bold text-slate-900">{targetCareer.currentReadiness}%</div>
          <div className="text-[11px] text-teal-700 font-medium mt-0.5">Target: 85%+</div>
        </motion.div>

        <motion.div 
          className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: 'easeOut', delay: 0.05 }}
          whileHover={{ scale: 1.02, boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)' }}
        >
          <div className="flex items-center justify-between text-slate-500 mb-1.5">
            <span className="text-xs font-semibold">Verified Skills</span>
            
          </div>
          <div className="text-2xl font-bold text-slate-900">{verifiedSkillsCount}</div>
          <div className="text-[11px] text-slate-500 mt-0.5">Out of {competencyNodes.length} mapped</div>
        </motion.div>

        <motion.div 
          className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: 'easeOut', delay: 0.1 }}
          whileHover={{ scale: 1.02, boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)' }}
        >
          <div className="flex items-center justify-between text-slate-500 mb-1.5">
            <span className="text-xs font-semibold">In Progress</span>
            
          </div>
          <div className="text-2xl font-bold text-slate-900">{inProgressSkillsCount}</div>
          <div className="text-[11px] text-blue-700 mt-0.5">Active validation</div>
        </motion.div>

        <motion.div 
          className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: 'easeOut', delay: 0.15 }}
          whileHover={{ scale: 1.02, boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)' }}
        >
          <div className="flex items-center justify-between text-slate-500 mb-1.5">
            <span className="text-xs font-semibold">Critical Gaps</span>
            
          </div>
          <div className="text-2xl font-bold text-slate-900">{criticalGapsCount}</div>
          <div className="text-[11px] text-amber-700 mt-0.5">Blocks target role</div>
        </motion.div>

        <motion.div 
          className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: 'easeOut', delay: 0.2 }}
          whileHover={{ scale: 1.02, boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)' }}
        >
          <div className="flex items-center justify-between text-slate-500 mb-1.5">
            <span className="text-xs font-semibold">Evidence Items</span>
            <FileCheck2 className="w-4 h-4 text-purple-600" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{evidenceItems.length}</div>
          <div className="text-[11px] text-purple-700 font-medium mt-0.5">{avgConfidence}% avg confidence</div>
        </motion.div>

        <motion.div 
          className="bg-white p-4 rounded-xl border border-slate-200/80 shadow-2xs"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3, ease: 'easeOut', delay: 0.25 }}
          whileHover={{ scale: 1.02, boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)' }}
        >
          <div className="flex items-center justify-between text-slate-500 mb-1.5">
            <span className="text-xs font-semibold">Learning Streak</span>
            <Flame className="w-4 h-4 text-amber-500 fill-amber-500" />
          </div>
          <div className="text-2xl font-bold text-slate-900">{student.streakDays} days</div>
          <div className="text-[11px] text-emerald-700 font-medium mt-0.5">Recorded profile streak</div>
        </motion.div>
      </div>

      <CareerIntelligencePanel/>

      {/* Main Grid: Charts & Tables */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left 2 Cols: Charts & Priority Gaps */}
        <div className="lg:col-span-2 space-y-6">
          {/* Domain Mastery Radar & Weekly Activity */}
          {/* Domain Mastery Radar & Readiness Progression & Weekly Activity */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Visual Intelligence: Radar or Trend */}
            <motion.div 
              className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: 'easeOut', delay: 0.1 }}
              whileHover={{ scale: 1.01 }}
            >
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                  <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                    {chartView === 'trend' ? 'Career Readiness Progression' : 'Skill Mastery Distribution'}
                  </h4>
                </div>
                <div className="flex items-center gap-1 bg-slate-100 p-0.5 rounded-lg text-[10px]">
                  <DesignButton
                    onClick={() => setChartView('trend')}
                    className={`px-2 py-0.5 rounded-md font-semibold transition cursor-pointer ${
                      chartView === 'trend' ? 'bg-white text-teal-700 shadow-xs' : 'text-slate-500 hover:text-slate-800'
                    }`}
                    variant="secondary"
                    size="sm"
                  >
                    Trend
                  </DesignButton>
                  <DesignButton
                    onClick={() => setChartView('radar')}
                    className={`px-2 py-0.5 rounded-md font-semibold transition cursor-pointer ${
                      chartView === 'radar' ? 'bg-white text-teal-700 shadow-xs' : 'text-slate-500 hover:text-slate-800'
                    }`}
                    variant="secondary"
                    size="sm"
                  >
                    Radar
                  </DesignButton>
                </div>
              </div>

              <div className="h-56 w-full">
                {chartView === 'trend' ? (
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={readinessTrendData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                      <defs>
                        <linearGradient id="colorReadiness" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#0f766e" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="#0f766e" stopOpacity={0.0} />
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="checkpoint" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
                      <YAxis domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} />
                      <Tooltip
                        formatter={(val: any, name: any) => [`${val}%`, name === 'readiness' ? 'Readiness Score' : 'Role Target']}
                        contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', color: '#fff', fontSize: '11px' }}
                      />
                      <Area type="monotone" dataKey="readiness" stroke="#0f766e" strokeWidth={2.5} fillOpacity={1} fill="url(#colorReadiness)" />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <ResponsiveContainer width="100%" height="100%">
                    <RadarChart data={domainMasteryData}>
                      <PolarGrid stroke="#e2e8f0" />
                      <PolarAngleAxis dataKey="domain" tick={{ fill: '#475569', fontSize: 10 }} />
                      <PolarRadiusAxis angle={30} domain={[0, 100]} tick={{ fill: '#94a3b8', fontSize: 9 }} />
                      <Radar name="Target" dataKey="target" stroke="#94a3b8" fill="#cbd5e1" fillOpacity={0.25} />
                      <Radar name="Current Mastery" dataKey="mastery" stroke="#0d9488" fill="#0d9488" fillOpacity={0.45} />
                    </RadarChart>
                  </ResponsiveContainer>
                )}
              </div>
              <div className="flex items-center justify-center gap-4 text-[11px] text-slate-500 pt-1">
                {chartView === 'trend' ? (
                  <div className="flex items-center gap-2">
                    <span className="w-2.5 h-0.5 bg-teal-700" />
                    <span>Living Score Trajectory (Target: 85%)</span>
                  </div>
                ) : (
                  <>
                    <div className="flex items-center gap-1.5">
                      <div className="w-2.5 h-2.5 rounded-xs bg-teal-600" />
                      <span>Current Mastery</span>
                    </div>
                    <div className="flex items-center gap-1.5">
                      <div className="w-2.5 h-2.5 rounded-xs bg-slate-300" />
                      <span>Target Requirement</span>
                    </div>
                  </>
                )}
              </div>
            </motion.div>

            {/* Weekly Learning Activity */}
            <motion.div 
              className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4, ease: 'easeOut', delay: 0.2 }}
              whileHover={{ scale: 1.01 }}
            >
              <div className="flex items-center justify-between mb-2">
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                  Weekly Learning Activity
                </h4>
                <span className="text-[11px] text-slate-400">Time tracking not recorded</span>
              </div>
              <div className="h-56 w-full">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={weeklyActivityData}>
                    <XAxis dataKey="day" tick={{ fill: '#64748b', fontSize: 10 }} axisLine={false} tickLine={false} />
                    <YAxis tick={{ fill: '#94a3b8', fontSize: 10 }} axisLine={false} tickLine={false} />
                    <Tooltip
                      formatter={(val: any) => [`${val} hrs`, 'Study Time']}
                      contentStyle={{ backgroundColor: '#0f172a', borderRadius: '8px', color: '#fff', fontSize: '11px' }}
                    />
                    <Bar dataKey="hours" fill="#0f766e" radius={[4, 4, 0, 0]} />
                  </BarChart>
                </ResponsiveContainer>
              </div>
              <div className="text-center text-[11px] text-slate-500 pt-1">
                Complete learning resources to record evidence-backed activity.
              </div>
            </motion.div>
          </div>

          {/* Targeted Action Trio: Upcoming Assessment, Recommended Project, Remediation Resource */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3.5">
            {/* Upcoming Assessment */}
            {upcomingAssessment && (
              <motion.div 
                className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs flex flex-col justify-between hover:border-teal-300 transition"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, ease: 'easeOut', delay: 0.3 }}
                whileHover={{ scale: 1.02, borderColor: '#14b8a6' }}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded">
                      Assessment
                    </span>
                    <span className="text-[11px] text-slate-400">{upcomingAssessment.estimatedTime}</span>
                  </div>
                  <h5 className="text-xs font-bold text-slate-900 line-clamp-1">{upcomingAssessment.title}</h5>
                  <p className="text-[11px] text-slate-500 line-clamp-2">
                    Validates {upcomingAssessment.skillName} to turn estimated mastery into verified signals.
                  </p>
                </div>
                <DesignButton
                  onClick={() => setActiveTab('assessments')}
                  className="mt-3 w-full py-1.5 bg-slate-100 hover:bg-teal-50 hover:text-teal-800 text-slate-700 text-xs font-semibold rounded-lg transition flex items-center justify-center gap-1 cursor-pointer"
                  variant="secondary"
                  size="sm"
                >
                  <CheckSquare className="w-3.5 h-3.5" />
                  <span>Start Test</span>
                </DesignButton>
              </motion.div>
            )}

            {/* Recommended Project */}
            {topRecommendedProject && (
              <motion.div 
                className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs flex flex-col justify-between hover:border-teal-300 transition"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, ease: 'easeOut', delay: 0.4 }}
                whileHover={{ scale: 1.02, borderColor: '#14b8a6' }}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase font-bold text-purple-700 bg-purple-50 px-2 py-0.5 rounded">
                      Project
                    </span>
                    <span className="text-[11px] text-purple-700 font-bold">Review required</span>
                  </div>
                  <h5 className="text-xs font-bold text-slate-900 line-clamp-1">{topRecommendedProject.title}</h5>
                  <p className="text-[11px] text-slate-500 line-clamp-2">
                    Rubric verification with code rubric, testing, and vector embeddings benchmark.
                  </p>
                </div>
                <DesignButton
                  onClick={() => setActiveTab('projects')}
                  className="mt-3 w-full py-1.5 bg-teal-700 hover:bg-teal-800 text-white text-xs font-semibold rounded-lg transition flex items-center justify-center gap-1 shadow-xs cursor-pointer"
                  variant="primary"
                  size="sm"
                >
                  <FolderGit2 className="w-3.5 h-3.5" />
                  <span>Verify Project</span>
                </DesignButton>
              </motion.div>
            )}

            {/* Recommended Resource */}
            {topRecommendedResource && (
              <motion.div 
                className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs flex flex-col justify-between hover:border-teal-300 transition"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.3, ease: 'easeOut', delay: 0.5 }}
                whileHover={{ scale: 1.02, borderColor: '#14b8a6' }}
              >
                <div className="space-y-1.5">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] uppercase font-bold text-blue-700 bg-blue-50 px-2 py-0.5 rounded">
                      Study Resource
                    </span>
                    <span className="text-[11px] text-slate-400">{topRecommendedResource.duration}</span>
                  </div>
                  <h5 className="text-xs font-bold text-slate-900 line-clamp-1">{topRecommendedResource.title}</h5>
                  <p className="text-[11px] text-slate-500 line-clamp-2">
                    {topRecommendedResource.reasonRecommended}
                  </p>
                </div>
                <DesignButton
                  onClick={() => setActiveTab('resources')}
                  className="mt-3 w-full py-1.5 bg-slate-100 hover:bg-slate-200 text-slate-700 text-xs font-semibold rounded-lg transition flex items-center justify-center gap-1 cursor-pointer"
                  variant="secondary"
                  size="sm"
                >
                  <BookOpen className="w-3.5 h-3.5" />
                  <span>View Resource</span>
                </DesignButton>
              </motion.div>
            )}
          </div>

          {/* Priority Skill Gaps Table */}
          <motion.div 
            className="bg-white rounded-2xl border border-slate-200/80 shadow-2xs overflow-hidden"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: 'easeOut', delay: 0.6 }}
          >
            <div className="p-4 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                  Priority Competency Gaps ({targetCareer.title})
                </h4>
                <p className="text-[11px] text-slate-500">Skills requiring verification or direct study to satisfy role requirements</p>
              </div>
              <DesignButton
                onClick={() => setActiveTab('competencies')}
                className="text-xs font-semibold text-teal-700 hover:text-teal-800 flex items-center gap-1 cursor-pointer"
                variant="secondary"
                size="sm"
              >
                <span>View All In Graph</span>
                <ArrowRight className="w-3.5 h-3.5" />
              </DesignButton>
            </div>

            <div className="divide-y divide-slate-100 text-xs">
              {priorityGaps.map((gap, index) => (
                <motion.div 
                  key={gap.id} 
                  className="p-4 hover:bg-slate-50/70 transition flex flex-col sm:flex-row sm:items-center justify-between gap-3"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, ease: 'easeOut', delay: 0.7 + (index * 0.05) }}
                  whileHover={{ scale: 1.01, backgroundColor: '#f8fafc' }}
                >
                  <div className="space-y-1">
                    <div className="flex items-center gap-2">
                      <span className="font-bold text-slate-900">{gap.name}</span>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded font-semibold ${
                          gap.state === 'Skill Gap'
                            ? 'bg-amber-50 text-amber-800 border border-amber-200'
                            : 'bg-rose-50 text-rose-800 border border-rose-200'
                        }`}
                      >
                        {gap.state}
                      </span>
                      <span className="text-[10px] text-slate-400 font-medium">({gap.domain})</span>
                    </div>
                    <p className="text-slate-600 text-[11px] leading-relaxed max-w-xl">
                      {gap.remainingGap}
                    </p>
                  </div>

                  <div className="flex items-center gap-3 shrink-0">
                    <div className="text-right">
                      <div className="font-bold text-slate-900">{gap.mastery}%</div>
                      <div className="text-[10px] text-slate-400">Req: 85%</div>
                    </div>
                    <DesignButton
                      onClick={() => {
                        setSelectedSkillId(gap.id);
                        setActiveTab('competencies');
                      }}
                      className="px-3 py-1.5 bg-slate-100 hover:bg-teal-50 hover:text-teal-800 text-slate-700 rounded-lg font-semibold transition cursor-pointer"
                      variant="secondary"
                      size="sm"
                    >
                      Inspect
                    </DesignButton>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>

        {/* Right Col: Roadmap Progress & Real-time Activity Feed */}
        <div className="space-y-6">
          {/* Current Roadmap Progress Card */}
          <motion.div 
            className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs space-y-3"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: 'easeOut', delay: 0.8 }}
          >
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                Adaptive Roadmap
              </h4>
              <span className="text-xs font-bold text-teal-700 bg-teal-50 px-2 py-0.5 rounded">
                {roadmapPercent}% Complete
              </span>
            </div>

            <div className="w-full bg-slate-100 h-2 rounded-full overflow-hidden">
              <motion.div
                className="bg-teal-600 h-full rounded-full transition-all duration-500"
                style={{ width: `${roadmapPercent}%` }}
                initial={{ width: 0 }}
                animate={{ width: `${roadmapPercent}%` }}
                transition={{ duration: 0.6, ease: 'easeOut' }}
              />
            </div>

            <div className="space-y-2 pt-1 text-xs">
              {roadmap.slice(0, 3).map((m, index) => (
                <motion.div
                  key={m.id}
                  onClick={() => setActiveTab('roadmap')}
                  className="p-2.5 rounded-xl border border-slate-100 hover:border-slate-200 hover:bg-slate-50 transition cursor-pointer"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, ease: 'easeOut', delay: 0.9 + (index * 0.05) }}
                  whileHover={{ scale: 1.02, backgroundColor: '#f8fafc', borderColor: '#e2e8f0' }}
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-semibold text-slate-900 truncate pr-2">{m.title}</span>
                    <span
                      className={`text-[10px] font-bold px-1.5 py-0.2 rounded shrink-0 ${
                        m.state === 'Completed'
                          ? 'bg-emerald-100 text-emerald-800'
                          : m.state === 'Active'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-slate-100 text-slate-500'
                      }`}
                    >
                      {m.state}
                    </span>
                  </div>
                  <div className="text-[10px] text-slate-500 flex items-center justify-between">
                    <span>Target: {m.masteryTarget}%</span>
                    <span>{m.estimatedDuration}</span>
                  </div>
                </motion.div>
              ))}
            </div>

            <DesignButton
              onClick={() => setActiveTab('roadmap')}
              className="w-full py-2 bg-slate-50 hover:bg-slate-100 text-slate-700 font-semibold rounded-xl text-xs transition text-center cursor-pointer block border border-slate-200"
              variant="secondary"
              size="sm"
            >
              Open Full Adaptive Roadmap
            </DesignButton>
          </motion.div>

          {/* Real-Time Activity Feed */}
          <motion.div 
            className="bg-white p-4 rounded-2xl border border-slate-200/80 shadow-2xs space-y-3"
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: 'easeOut', delay: 1 }}
          >
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-bold text-slate-900 uppercase tracking-wide">
                Recent Intelligence Activity
              </h4>
              <span className="text-[10px] text-slate-400">Evidence log</span>
            </div>

            <div className="space-y-3 text-xs">
              {activities.slice(0, 5).map((act, index) => (
                <motion.div 
                  key={act.id} 
                  className="flex items-start gap-2.5"
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, ease: 'easeOut', delay: 1.1 + (index * 0.05) }}
                >
                  <div className="w-2 h-2 rounded-full bg-teal-500 mt-1.5 shrink-0" />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-1">
                      <span className="font-semibold text-slate-900 truncate">{act.title}</span>
                      {act.delta && (
                        <span className="text-[10px] font-bold text-teal-700 bg-teal-50 px-1 rounded shrink-0">
                          {act.delta}
                        </span>
                      )}
                    </div>
                    <p className="text-[11px] text-slate-500 leading-snug">{act.description}</p>
                    <span className="text-[10px] text-slate-400">{act.timestamp}</span>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  );
}
