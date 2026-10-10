export type VerificationState = 'Verified' | 'Estimated' | 'Unverified' | 'Needs Review';

export type NodeStateType = 
  | 'Verified' 
  | 'Estimated' 
  | 'In Progress' 
  | 'Skill Gap' 
  | 'Prerequisite Gap' 
  | 'Unverified Claim';

export type CompetencyDomain = 
  | 'Math & Foundations' 
  | 'Core Programming' 
  | 'Data Systems' 
  | 'Machine Learning' 
  | 'Deep Learning & NLP' 
  | 'MLOps & Deployment';

export interface CompetencyNode {
  id: string;
  name: string;
  domain: CompetencyDomain;
  type: 'Skill' | 'Concept' | 'Prerequisite' | 'Career Requirement';
  state: NodeStateType;
  mastery: number; // 0 - 100
  confidence: number; // 0 - 100
  careerImportance: 'Critical' | 'High' | 'Medium' | 'Foundational';
  evidenceCount: number;
  lastAssessed?: string;
  prerequisites: string[]; // Node IDs
  dependents: string[]; // Node IDs
  relatedConcepts: string[];
  remainingGap: string;
  recommendedAction: string;
  history?: { date: string; mastery: number; event: string }[];
  // Graph coordinate positions for visual layout
  x: number;
  y: number;
}

export type EvidenceType = 
  | 'Resume Claim' 
  | 'Course Record' 
  | 'Certificate' 
  | 'GitHub Artifact' 
  | 'Assessment' 
  | 'Coding Challenge' 
  | 'Project' 
  | 'Manual Claim' 
  | 'Mentor Review';

export interface EvidenceItem {
  id: string;
  title: string;
  type: EvidenceType;
  skillId: string;
  skillName: string;
  verificationState: VerificationState;
  quality: 'High' | 'Medium' | 'Low';
  confidenceScore: number; // 0 - 100
  date: string;
  source: string;
  provenance: string;
  url?: string;
  artifacts?: string[];
  summary: string;
}

export interface CareerRequirement {
  skillId: string;
  skillName: string;
  requiredMastery: number;
  importance: 'Required' | 'Preferred' | 'Bonus';
  category: string;
}

export type GapType = 'Direct Gap' | 'Prerequisite Gap' | 'Evidence Gap' | 'Knowledge Debt';

export interface CareerGap {
  skillId: string;
  skillName: string;
  gapType: GapType;
  currentMastery: number;
  requiredMastery: number;
  whyExplanation: string;
  recommendedAction: string;
  priority: 'High' | 'Medium' | 'Low';
}

export interface CareerRole {
  id: string;
  title: string;
  category: string;
  description: string;
  marketDemand: 'Very High' | 'High' | 'Growing' | 'Stable';
  avgSalary: string;
  currentReadiness: number; // calculated 0 - 100
  requiredCompetencies: CareerRequirement[];
  recommendedProjects: string[];
  recommendedCertifications: string[];
}

export type MilestoneState = 'Completed' | 'Active' | 'Locked' | 'Blocked' | 'Needs Assessment';

export interface RoadmapMilestone {
  id: string;
  order: number;
  title: string;
  skillId: string;
  domain: CompetencyDomain;
  state: MilestoneState;
  reason: string;
  prerequisites: string[];
  estimatedDuration: string; // e.g. "8 hours"
  masteryTarget: number;
  currentMastery: number;
  completionCondition: string;
  evidenceGenerated: string;
  practiceTasks: string[];
  resourceIds: string[];
  assessmentId?: string;
  projectId?: string;
}

export type ResourceType = 'Article' | 'Documentation' | 'Course' | 'Video' | 'Practice' | 'Book' | 'Lab';

export interface LearningResource {
  id: string;
  title: string;
  provider: string;
  skillId: string;
  skillName: string;
  type: ResourceType;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  duration: string;
  qualityRating: number; // e.g. 4.8
  prerequisites: string[];
  reasonRecommended: string;
  url: string;
  bookmarked?: boolean;
  completed?: boolean;
}

export type QuestionType = 'MCQ' | 'Multiple Select' | 'Short Answer' | 'Reasoning' | 'Coding';

export interface AssessmentQuestion {
  id: string;
  type: QuestionType;
  topic: string;
  question: string;
  codeSnippet?: string;
  options?: string[];
  correctAnswers: number[] | string;
  explanation: string;
}

export interface AssessmentItem {
  id: string;
  title: string;
  category: 'Baseline Diagnostic' | 'Skill Assessment' | 'Concept Assessment' | 'Coding Challenge';
  skillId: string;
  skillName: string;
  difficulty: 'Beginner' | 'Intermediate' | 'Advanced';
  estimatedTime: string;
  questionsCount: number;
  questions: AssessmentQuestion[];
  targetSkillsImpacted: { skillId: string; skillName: string; baselineMastery: number; targetMastery: number }[];
  historyRecord?: {
    date: string;
    score: number;
    accuracy: number;
    skillsUpdated: string[];
  };
}

export interface ProjectItem {
  id: string;
  title: string;
  difficulty: 'Intermediate' | 'Advanced' | 'Capstone';
  skillsValidated: string[];
  concepts: string[];
  careerRelevance: string;
  estimatedEffort: string;
  evidenceValue: 'Critical' | 'High' | 'Medium';
  reasonRecommended: string;
  objective: string;
  requirements: string[];
  prerequisites: string[];
  deliverables: string[];
  rubric: { criterion: string; weight: number; targetLevel: string }[];
  testCriteria: string[];
  verified: boolean;
  submittedAt?: string;
  submissionDetails?: {
    githubUrl: string;
    description: string;
    evaluationScore: number;
    feedback: string;
    skillsVerified: string[];
  };
}

export interface ResumeClaim {
  id: string;
  claim: string;
  skillName: string;
  skillId: string;
  section: string;
  evidenceState: 'Verified' | 'Unsupported' | 'In Progress';
  evidenceId?: string;
  relatedCareerRequirement: string;
  recommendedAction: string;
}

export interface ResumeAnalysis {
  documentId?: string;
  targetCareerId?: string;
  targetCareerTitle?: string;
  claimCount?: number;
  scoreBreakdown?: {sectionStructure:number;roleKeywordCoverage:number;evidenceCoverage:number};
  parsedSections?: {name:string;text:string}[];
  fileName: string;
  uploadedAt: string;
  resumeScore: number; // 0 - 100
  atsCompatibilityScore: number; // 0 - 100
  sectionsDetected: string[];
  extractedSkillsCount: number;
  verifiedClaimsCount: number;
  unsupportedClaimsCount: number;
  careerAlignmentScore: number;
  evidenceCoveragePercent: number;
  claims: ResumeClaim[];
  missingSkillsForTarget: string[];
  weakClaims: string[];
  suggestedImprovements: string[];
  recommendedProofProject: string;
}

export interface ActivityItem {
  id: string;
  type: 'Assessment Completed' | 'Skill Mastery Updated' | 'Evidence Verified' | 'Roadmap Recalculated' | 'Project Recommended' | 'Career Target Changed';
  title: string;
  description: string;
  timestamp: string;
  delta?: string;
  linkTab?: string;
}

export type ProfileAvatar = {kind: "preset"; presetId: string} | {kind: "photo"; dataUrl: string};

export interface StudentProfile {
  overallXP?: number;
  codingXP?: number;
  overallRank?: number;
  avatar?: ProfileAvatar | null;
  priorExperience?: string;
  academicDetails?: string;
  readinessDisplayCareerId?: string;
  isDemo?: boolean;
  canReview?: boolean;
  id: string;
  name: string;
  email: string;
  headline: string;
  bio: string;
  location: string;
  degree: string;
  institution: string;
  gradYear: string;
  gpa: string;
  githubHandle: string;
  githubConnected: boolean;
  learningPreferences: string[];
  weeklyAvailabilityHours: number;
  streakDays: number;
  targetCareerId: string;
  lastCompetencyUpdate: string;
}

export interface NotificationItem {
  id: string;
  title: string;
  message: string;
  type: 'assessment' | 'verification' | 'roadmap' | 'career' | 'system';
  timestamp: string;
  read: boolean;
  linkTab?: string;
}

export interface MentorMessage {
  agentRun?: {id?:string;agentsUsed:string[];toolsUsed:string[];stateVersion:number;status:string;actions:{label:string;status:string}[]};
  id: string;
  sender: 'user' | 'assistant';
  failed?: boolean;
  timestamp: string;
  text: string;
  reasoningSummary?: string;
  relatedCompetencies?: { id?:string; name: string; mastery: number; state: NodeStateType }[];
  evidenceReferences?: { id: string; title: string; type: EvidenceType }[];
  citations?: { documentId?:string; chunkId?:string; title: string; source: string; year: string }[];
  suggestedAction?: { label: string; tab: string; actionData?: any };
}
