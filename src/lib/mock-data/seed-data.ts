import {
  StudentProfile,
  CompetencyNode,
  EvidenceItem,
  CareerRole,
  RoadmapMilestone,
  LearningResource,
  AssessmentItem,
  ProjectItem,
  ResumeAnalysis,
  ActivityItem,
  NotificationItem,
  MentorMessage
} from '../../types';

export const INITIAL_STUDENT: StudentProfile = {
  id: 'student-alex-rivera',
  name: 'Alex Rivera',
  email: 'alex.rivera@cs.university.edu',
  headline: 'Aspiring AI & Machine Learning Systems Engineer',
  bio: 'CS junior with strong math fundamentals and backend skills, transitioning into production deep learning and LLM engineering.',
  location: 'San Francisco, CA',
  degree: 'B.S. in Computer Science',
  institution: 'University of California, Berkeley',
  gradYear: '2026',
  gpa: '3.82',
  githubHandle: 'alexrivera-dev',
  githubConnected: true,
  learningPreferences: ['Code-First Hands On', 'Deep Theory Explanations', 'Project Based'],
  weeklyAvailabilityHours: 15,
  streakDays: 14,
  targetCareerId: 'career-ai-engineer',
  lastCompetencyUpdate: '2 hours ago'
};

export const INITIAL_COMPETENCY_NODES: CompetencyNode[] = [
  // 1. Math & Foundations
  {
    id: 'math-linear-algebra',
    name: 'Linear Algebra',
    domain: 'Math & Foundations',
    type: 'Prerequisite',
    state: 'Verified',
    mastery: 88,
    confidence: 94,
    careerImportance: 'Foundational',
    evidenceCount: 3,
    lastAssessed: '3 days ago',
    prerequisites: [],
    dependents: ['math-prob-stats', 'ml-supervised', 'dl-neural-networks'],
    relatedConcepts: ['Eigenvalues & Eigenvectors', 'Matrix Decomposition (SVD)', 'Tensor Operations'],
    remainingGap: 'Minimal gap in advanced matrix factorizations for LoRA.',
    recommendedAction: 'Review Low-Rank Adaptation mathematical derivations.',
    x: 80,
    y: 100
  },
  {
    id: 'math-multivariate-calculus',
    name: 'Multivariate Calculus',
    domain: 'Math & Foundations',
    type: 'Prerequisite',
    state: 'Verified',
    mastery: 82,
    confidence: 90,
    careerImportance: 'Foundational',
    evidenceCount: 2,
    lastAssessed: '1 week ago',
    prerequisites: [],
    dependents: ['dl-neural-networks'],
    relatedConcepts: ['Gradients & Jacobians', 'Hessian Matrices', 'Chain Rule in Backprop'],
    remainingGap: 'None detected for current AI Engineer scope.',
    recommendedAction: 'Maintain mastery through active gradient derivation practice.',
    x: 80,
    y: 220
  },
  {
    id: 'math-prob-stats',
    name: 'Probability & Statistics',
    domain: 'Math & Foundations',
    type: 'Concept',
    state: 'Verified',
    mastery: 78,
    confidence: 85,
    careerImportance: 'Critical',
    evidenceCount: 3,
    lastAssessed: '5 days ago',
    prerequisites: ['math-linear-algebra'],
    dependents: ['ml-model-evaluation', 'ml-supervised'],
    relatedConcepts: ['Bayes Theorem', 'Maximum Likelihood Estimation (MLE)', 'Markov Chains'],
    remainingGap: 'Bayesian inference and sampling methods need reinforcement.',
    recommendedAction: 'Solve 5 practical Bayesian likelihood estimation problems.',
    x: 240,
    y: 100
  },

  // 2. Core Programming
  {
    id: 'prog-python-advanced',
    name: 'Python (Advanced)',
    domain: 'Core Programming',
    type: 'Skill',
    state: 'Verified',
    mastery: 92,
    confidence: 96,
    careerImportance: 'Critical',
    evidenceCount: 5,
    lastAssessed: 'Yesterday',
    prerequisites: [],
    dependents: ['data-numpy-pandas', 'dl-pytorch', 'prog-data-structures'],
    relatedConcepts: ['AsyncIO', 'Metaclasses & Decorators', 'Memory Profiling & C-Extensions'],
    remainingGap: 'Solid command of production asynchronous Python and typing.',
    recommendedAction: 'Ready to tackle low-level PyTorch custom C++ extensions.',
    x: 80,
    y: 350
  },
  {
    id: 'prog-data-structures',
    name: 'Data Structures & Algorithms',
    domain: 'Core Programming',
    type: 'Prerequisite',
    state: 'Verified',
    mastery: 86,
    confidence: 92,
    careerImportance: 'Foundational',
    evidenceCount: 4,
    lastAssessed: '2 weeks ago',
    prerequisites: ['prog-python-advanced'],
    dependents: ['data-vector-databases'],
    relatedConcepts: ['Graphs & Trees', 'Dynamic Programming', 'Trie & Hash Indexes'],
    remainingGap: 'Minor gap in approximate nearest neighbor graph algorithms.',
    recommendedAction: 'Implement HNSW graph traversal algorithm from scratch.',
    x: 240,
    y: 350
  },
  {
    id: 'prog-docker-containers',
    name: 'Docker & Containerization',
    domain: 'Core Programming',
    type: 'Skill',
    state: 'In Progress',
    mastery: 64,
    confidence: 72,
    careerImportance: 'High',
    evidenceCount: 2,
    lastAssessed: '4 days ago',
    prerequisites: ['prog-python-advanced'],
    dependents: ['mlops-model-serving', 'mlops-production-pipeline'],
    relatedConcepts: ['Multi-Stage GPU Builds', 'CUDA Base Containers', 'Docker Compose'],
    remainingGap: 'Needs hands-on optimization for NVIDIA GPU container runtimes.',
    recommendedAction: 'Containerize a PyTorch inference server using NVIDIA CUDA runtime.',
    x: 240,
    y: 470
  },

  // 3. Data Systems
  {
    id: 'data-numpy-pandas',
    name: 'NumPy & Pandas Processing',
    domain: 'Data Systems',
    type: 'Skill',
    state: 'Verified',
    mastery: 89,
    confidence: 92,
    careerImportance: 'Critical',
    evidenceCount: 4,
    lastAssessed: '3 days ago',
    prerequisites: ['prog-python-advanced'],
    dependents: ['ml-supervised', 'ml-unsupervised'],
    relatedConcepts: ['Vectorization & Broadcasting', 'Memory Mapping', 'Time Series Alignment'],
    remainingGap: 'None detected; proficient in high-throughput tensor data preprocessing.',
    recommendedAction: 'Extend preprocessing to PyTorch DataLoader pipeline.',
    x: 400,
    y: 250
  },
  {
    id: 'data-sql-querying',
    name: 'Advanced SQL & Data Modeling',
    domain: 'Data Systems',
    type: 'Skill',
    state: 'Verified',
    mastery: 76,
    confidence: 82,
    careerImportance: 'High',
    evidenceCount: 2,
    lastAssessed: '6 days ago',
    prerequisites: ['prog-python-advanced'],
    dependents: ['data-vector-databases'],
    relatedConcepts: ['Window Functions', 'Recursive CTEs', 'Query Execution Plans'],
    remainingGap: 'Columnar database indexing patterns for massive embeddings.',
    recommendedAction: 'Practice pgvector SQL extensions with hybrid search queries.',
    x: 400,
    y: 370
  },
  {
    id: 'data-vector-databases',
    name: 'Vector DBs & Embeddings Index',
    domain: 'Data Systems',
    type: 'Career Requirement',
    state: 'In Progress',
    mastery: 58,
    confidence: 65,
    careerImportance: 'Critical',
    evidenceCount: 1,
    lastAssessed: '1 week ago',
    prerequisites: ['prog-data-structures', 'data-sql-querying'],
    dependents: ['dl-rag-systems'],
    relatedConcepts: ['HNSW vs IVF Indexing', 'Cosine vs Dot Product Metrics', 'Chroma & Pinecone'],
    remainingGap: 'Missing verified project demonstrating production hybrid lexical/vector search.',
    recommendedAction: 'Complete Project: End-to-End Hybrid RAG with Milvus or Qdrant.',
    x: 560,
    y: 370
  },

  // 4. Machine Learning
  {
    id: 'ml-supervised',
    name: 'Supervised Learning Algorithms',
    domain: 'Machine Learning',
    type: 'Skill',
    state: 'Verified',
    mastery: 84,
    confidence: 90,
    careerImportance: 'Critical',
    evidenceCount: 4,
    lastAssessed: '4 days ago',
    prerequisites: ['math-linear-algebra', 'math-prob-stats', 'data-numpy-pandas'],
    dependents: ['ml-model-evaluation', 'dl-neural-networks'],
    relatedConcepts: ['Gradient Boosted Trees (XGBoost)', 'Regularization (L1/L2)', 'Support Vector Machines'],
    remainingGap: 'Proficient in tabular modeling; baseline solid for deep learning transitions.',
    recommendedAction: 'Maintain with periodic algorithmic review.',
    x: 560,
    y: 120
  },
  {
    id: 'ml-unsupervised',
    name: 'Unsupervised & Dimensionality',
    domain: 'Machine Learning',
    type: 'Concept',
    state: 'Verified',
    mastery: 75,
    confidence: 80,
    careerImportance: 'High',
    evidenceCount: 2,
    lastAssessed: '1 week ago',
    prerequisites: ['data-numpy-pandas'],
    dependents: ['dl-rag-systems'],
    relatedConcepts: ['t-SNE & UMAP', 'K-Means & DBSCAN', 'PCA Decomposition'],
    remainingGap: 'Dimensionality reduction for visualizing high-dimensional text embeddings.',
    recommendedAction: 'Build an interactive UMAP visualizer for 1536-dim OpenAI embeddings.',
    x: 560,
    y: 240
  },
  {
    id: 'ml-model-evaluation',
    name: 'Model Evaluation & Validation',
    domain: 'Machine Learning',
    type: 'Career Requirement',
    state: 'Verified',
    mastery: 80,
    confidence: 88,
    careerImportance: 'Critical',
    evidenceCount: 3,
    lastAssessed: '5 days ago',
    prerequisites: ['ml-supervised', 'math-prob-stats'],
    dependents: ['dl-llm-finetuning', 'mlops-model-serving'],
    relatedConcepts: ['ROC-AUC & Precision-Recall Curves', 'Cross-Validation & Data Leakage', 'LLM Benchmark Metrics (MMLU, BLEU, ROUGE)'],
    remainingGap: 'Evaluation frameworks for non-deterministic generative models (G-Eval).',
    recommendedAction: 'Take assessment on LLM-as-a-Judge validation methodologies.',
    x: 720,
    y: 120
  },

  // 5. Deep Learning & NLP
  {
    id: 'dl-neural-networks',
    name: 'Neural Network Architecture',
    domain: 'Deep Learning & NLP',
    type: 'Skill',
    state: 'Verified',
    mastery: 82,
    confidence: 86,
    careerImportance: 'Critical',
    evidenceCount: 3,
    lastAssessed: '4 days ago',
    prerequisites: ['math-multivariate-calculus', 'ml-supervised'],
    dependents: ['dl-pytorch', 'dl-transformers'],
    relatedConcepts: ['Backpropagation through Time', 'Activation Functions', 'Layer & Batch Normalization'],
    remainingGap: 'Grounded understanding of vanishing/exploding gradients and residual connections.',
    recommendedAction: 'Implement a multi-layer perceptron from scratch in pure NumPy.',
    x: 720,
    y: 240
  },
  {
    id: 'dl-pytorch',
    name: 'PyTorch Framework & Tensors',
    domain: 'Deep Learning & NLP',
    type: 'Career Requirement',
    state: 'In Progress',
    mastery: 68,
    confidence: 74,
    careerImportance: 'Critical',
    evidenceCount: 2,
    lastAssessed: '3 days ago',
    prerequisites: ['dl-neural-networks', 'prog-python-advanced'],
    dependents: ['dl-transformers', 'dl-llm-finetuning'],
    relatedConcepts: ['Autograd Engine', 'Custom Dataset & DataLoader', 'Distributed Data Parallel (DDP)'],
    remainingGap: 'Target mastery is 85%. Need verified evidence in custom training loops and multi-GPU DDP.',
    recommendedAction: 'Take Adaptive PyTorch Assessment to raise mastery and unlock DDP milestone.',
    x: 880,
    y: 200
  },
  {
    id: 'dl-transformers',
    name: 'Transformer Architecture & Attention',
    domain: 'Deep Learning & NLP',
    type: 'Career Requirement',
    state: 'Skill Gap',
    mastery: 46,
    confidence: 52,
    careerImportance: 'Critical',
    evidenceCount: 1,
    lastAssessed: '1 week ago',
    prerequisites: ['dl-pytorch'],
    dependents: ['dl-llm-finetuning', 'dl-rag-systems'],
    relatedConcepts: ['Scaled Dot-Product Attention', 'Multi-Head Attention', 'Rotary Positional Embeddings (RoPE)', 'KV Cache'],
    remainingGap: 'Critical direct gap! Required 85% for AI Engineer role. Current mastery is 46%.',
    recommendedAction: 'Complete Milestone: Transformer Deep Dive and flash attention calculations.',
    x: 1040,
    y: 180
  },
  {
    id: 'dl-rag-systems',
    name: 'Retrieval Augmented Generation (RAG)',
    domain: 'Deep Learning & NLP',
    type: 'Career Requirement',
    state: 'In Progress',
    mastery: 62,
    confidence: 70,
    careerImportance: 'Critical',
    evidenceCount: 2,
    lastAssessed: '2 days ago',
    prerequisites: ['data-vector-databases', 'dl-transformers'],
    dependents: ['mlops-production-pipeline'],
    relatedConcepts: ['Contextual Chunking', 'Re-ranking with Cross-Encoders', 'Self-RAG & Agentic Loops'],
    remainingGap: 'Lacks verified project evidence on low-latency contextual re-ranking.',
    recommendedAction: 'Verify Capstone RAG Project with automated rubric evaluator.',
    x: 1040,
    y: 320
  },
  {
    id: 'dl-llm-finetuning',
    name: 'LLM Fine-Tuning & Quantization',
    domain: 'Deep Learning & NLP',
    type: 'Career Requirement',
    state: 'Prerequisite Gap',
    mastery: 35,
    confidence: 40,
    careerImportance: 'Critical',
    evidenceCount: 0,
    lastAssessed: 'Never',
    prerequisites: ['dl-transformers', 'dl-pytorch'],
    dependents: ['mlops-model-serving'],
    relatedConcepts: ['QLoRA & Parameter-Efficient Fine-Tuning', 'DPO vs PPO Alignment', 'AWQ & GGUF Quantization'],
    remainingGap: 'Prerequisite blocked: Requires PyTorch 80%+ and Transformer 75%+ before unlocking.',
    recommendedAction: 'Complete PyTorch & Transformer prerequisites first.',
    x: 1200,
    y: 200
  },

  // 6. MLOps & Deployment
  {
    id: 'mlops-model-serving',
    name: 'Model Serving & Inference Optimization',
    domain: 'MLOps & Deployment',
    type: 'Career Requirement',
    state: 'Skill Gap',
    mastery: 42,
    confidence: 48,
    careerImportance: 'High',
    evidenceCount: 1,
    lastAssessed: '2 weeks ago',
    prerequisites: ['prog-docker-containers', 'dl-pytorch'],
    dependents: ['mlops-production-pipeline'],
    relatedConcepts: ['vLLM & TensorRT-LLM', 'Continuous Batching & PagedAttention', 'Triton Inference Server'],
    remainingGap: 'Required for production AI deployments. Latency optimization and throughput benchmarks needed.',
    recommendedAction: 'Benchmark vLLM throughput vs naive HuggingFace pipelines in docker.',
    x: 1040,
    y: 450
  },
  {
    id: 'mlops-production-pipeline',
    name: 'CI/CD & Production LLM Pipelines',
    domain: 'MLOps & Deployment',
    type: 'Career Requirement',
    state: 'Unverified Claim',
    mastery: 50,
    confidence: 45,
    careerImportance: 'High',
    evidenceCount: 1,
    lastAssessed: 'Never',
    prerequisites: ['mlops-model-serving', 'dl-rag-systems'],
    dependents: [],
    relatedConcepts: ['Langfuse/Arize Observability', 'Prompt Versioning & Registry', 'Cost & Token Guardrails'],
    remainingGap: 'Claim on resume needs formal code/project artifact verification.',
    recommendedAction: 'Connect GitHub repository showing automated test pipeline for AI agents.',
    x: 1220,
    y: 350
  }
];

export const INITIAL_EVIDENCE_ITEMS: EvidenceItem[] = [
  {
    id: 'ev-001',
    title: 'Demo ML Course: Introduction to Machine Learning - Final Grade A',
    type: 'Course Record',
    skillId: 'ml-supervised',
    skillName: 'Supervised Learning Algorithms',
    verificationState: 'Verified',
    quality: 'High',
    confidenceScore: 95,
    date: '2025-12-18',
    source: 'UC Berkeley Registrar Transcript',
    provenance: 'Official Academic Transcript via Parchment (Verified Digital Signature)',
    url: 'https://credentials.berkeley.edu/verify/cs189-alexrivera',
    summary: 'Mastered mathematical foundations of SVM, decision trees, boosting, and empirical risk minimization with 94.2% course score.'
  },
  {
    id: 'ev-002',
    title: 'Advanced Python Decorators & AsyncIO Microbenchmark',
    type: 'GitHub Artifact',
    skillId: 'prog-python-advanced',
    skillName: 'Python (Advanced)',
    verificationState: 'Verified',
    quality: 'High',
    confidenceScore: 92,
    date: '2026-02-14',
    source: 'github.com/alexrivera-dev/py-async-bench',
    provenance: 'GitHub Commit History, 42 Stars, Automated CI Lint & Test Suite Passing',
    url: 'https://github.com/alexrivera-dev/py-async-bench',
    summary: 'Repository demonstrating production concurrent network request handlers, custom memory allocators, and typing protocols.'
  },
  {
    id: 'ev-003',
    title: 'Linear Algebra & SVD Diagnostic Assessment',
    type: 'Assessment',
    skillId: 'math-linear-algebra',
    skillName: 'Linear Algebra',
    verificationState: 'Verified',
    quality: 'High',
    confidenceScore: 96,
    date: '2026-03-12',
    source: 'Platform Baseline Diagnostic',
    provenance: 'Adaptive Test Engine (12 Questions, 92% Accuracy, 0 Flagged Anomaly)',
    summary: 'Verified strong intuition for projection matrices, singular value decomposition, and multidimensional hyperplanes.'
  },
  {
    id: 'ev-004',
    title: 'Resume Claim: "Trained and deployed PyTorch vision models"',
    type: 'Resume Claim',
    skillId: 'dl-pytorch',
    skillName: 'PyTorch Framework & Tensors',
    verificationState: 'Estimated',
    quality: 'Medium',
    confidenceScore: 68,
    date: '2026-03-01',
    source: 'Uploaded Resume: Alex_Rivera_Resume_2026.pdf',
    provenance: 'Extracted statement under Academic Projects section. Missing verifiable commit logs.',
    summary: 'Claim suggests basic familiarity with PyTorch torchvision models, but lacks evidence of custom training loops or DDP.'
  },
  {
    id: 'ev-005',
    title: 'Resume Claim: "Implemented RAG pipeline for documentation"',
    type: 'Resume Claim',
    skillId: 'dl-rag-systems',
    skillName: 'Retrieval Augmented Generation (RAG)',
    verificationState: 'Needs Review',
    quality: 'Medium',
    confidenceScore: 62,
    date: '2026-03-01',
    source: 'Uploaded Resume: Alex_Rivera_Resume_2026.pdf',
    provenance: 'Self-reported text statement. Needs automated rubric verification or GitHub link.',
    summary: 'Self-reported RAG project using ChromaDB. Recommended to submit project repo for automated rubric evaluation.'
  },
  {
    id: 'ev-006',
    title: 'LeetCode 250+ Solved Algorithmic Problems Profile',
    type: 'Coding Challenge',
    skillId: 'prog-data-structures',
    skillName: 'Data Structures & Algorithms',
    verificationState: 'Verified',
    quality: 'High',
    confidenceScore: 90,
    date: '2026-02-28',
    source: 'LeetCode Profile API Integration',
    provenance: 'Authenticated OAuth verification from leetcode.com/alexrivera99',
    summary: 'Consistent ranking in top 8% globally for dynamic programming, graph search, and tree traversal algorithms.'
  },
  {
    id: 'ev-007',
    title: 'Dockerizing FastAPI Microservices Certification',
    type: 'Certificate',
    skillId: 'prog-docker-containers',
    skillName: 'Docker & Containerization',
    verificationState: 'Verified',
    quality: 'Medium',
    confidenceScore: 78,
    date: '2026-01-20',
    source: 'Coursera / DeepLearning.AI',
    provenance: 'Digital Certificate Verification ID: DLAI-99412-DOCKER',
    url: 'https://coursera.org/verify/DLAI-99412',
    summary: 'Demonstrated building multi-stage docker images, environment variable secret injection, and compose file networking.'
  }
];

export const INITIAL_CAREERS: CareerRole[] = [
  {
    id: 'career-ai-engineer',
    title: 'AI Engineer',
    category: 'Applied AI & Systems',
    description: 'Bridges deep learning models and scalable production software. Specializes in LLM architectures, RAG pipelines, model quantization, inference serving, and evaluation.',
    marketDemand: 'Very High',
    avgSalary: '$165,000 - $225,000',
    currentReadiness: 68, // Will update reactively
    requiredCompetencies: [
      { skillId: 'prog-python-advanced', skillName: 'Python (Advanced)', requiredMastery: 90, importance: 'Required', category: 'Core' },
      { skillId: 'dl-pytorch', skillName: 'PyTorch Framework', requiredMastery: 85, importance: 'Required', category: 'Deep Learning' },
      { skillId: 'dl-transformers', skillName: 'Transformer Architecture & Attention', requiredMastery: 85, importance: 'Required', category: 'Deep Learning' },
      { skillId: 'dl-rag-systems', skillName: 'Retrieval Augmented Generation (RAG)', requiredMastery: 80, importance: 'Required', category: 'Applications' },
      { skillId: 'data-vector-databases', skillName: 'Vector DBs & Embeddings Index', requiredMastery: 75, importance: 'Required', category: 'Data Systems' },
      { skillId: 'ml-model-evaluation', skillName: 'Model Evaluation & Validation', requiredMastery: 80, importance: 'Required', category: 'Validation' },
      { skillId: 'dl-llm-finetuning', skillName: 'LLM Fine-Tuning (LoRA/QLoRA)', requiredMastery: 75, importance: 'Preferred', category: 'Deep Learning' },
      { skillId: 'mlops-model-serving', skillName: 'Model Serving (vLLM/Triton)', requiredMastery: 70, importance: 'Preferred', category: 'MLOps' }
    ],
    recommendedProjects: [
      'proj-rag-hybrid',
      'proj-transformer-from-scratch',
      'proj-vllm-serving-bench'
    ],
    recommendedCertifications: [
      'NVIDIA Certified Associate: Generative AI LLMs',
      'AWS Certified Machine Learning - Specialty'
    ]
  },
  {
    id: 'career-data-scientist',
    title: 'Data Scientist',
    category: 'Analytics & Predictive Modeling',
    description: 'Extracts strategic business intelligence, designs rigorous A/B experiments, and builds statistical and machine learning predictive models.',
    marketDemand: 'High',
    avgSalary: '$140,000 - $190,000',
    currentReadiness: 79,
    requiredCompetencies: [
      { skillId: 'math-prob-stats', skillName: 'Probability & Statistics', requiredMastery: 90, importance: 'Required', category: 'Math' },
      { skillId: 'data-numpy-pandas', skillName: 'NumPy & Pandas Processing', requiredMastery: 90, importance: 'Required', category: 'Data' },
      { skillId: 'data-sql-querying', skillName: 'Advanced SQL & Data Modeling', requiredMastery: 85, importance: 'Required', category: 'Data' },
      { skillId: 'ml-supervised', skillName: 'Supervised Learning Algorithms', requiredMastery: 85, importance: 'Required', category: 'ML' },
      { skillId: 'ml-model-evaluation', skillName: 'Model Evaluation & Validation', requiredMastery: 85, importance: 'Required', category: 'Validation' }
    ],
    recommendedProjects: ['proj-churn-predictive-pipeline', 'proj-bayesian-ab-testing'],
    recommendedCertifications: ['Google Professional Data Engineer']
  },
  {
    id: 'career-ml-engineer',
    title: 'ML Engineer',
    category: 'Machine Learning Infrastructure',
    description: 'Develops robust automated training pipelines, distributed computing workflows, and scalable real-time inference infrastructure for enterprise models.',
    marketDemand: 'Very High',
    avgSalary: '$160,000 - $215,000',
    currentReadiness: 71,
    requiredCompetencies: [
      { skillId: 'prog-python-advanced', skillName: 'Python (Advanced)', requiredMastery: 90, importance: 'Required', category: 'Core' },
      { skillId: 'dl-pytorch', skillName: 'PyTorch Framework', requiredMastery: 85, importance: 'Required', category: 'Deep Learning' },
      { skillId: 'prog-docker-containers', skillName: 'Docker & Containerization', requiredMastery: 80, importance: 'Required', category: 'Infrastructure' },
      { skillId: 'mlops-model-serving', skillName: 'Model Serving & Optimization', requiredMastery: 80, importance: 'Required', category: 'MLOps' }
    ],
    recommendedProjects: ['proj-distributed-ddp-trainer', 'proj-vllm-serving-bench'],
    recommendedCertifications: ['Databricks Certified Machine Learning Professional']
  },
  {
    id: 'career-data-analyst',
    title: 'Data Analyst',
    category: 'Analytics & Reporting',
    description: 'Transforms raw corporate data into interactive dashboards, cohort analytics, and executive business recommendations.',
    marketDemand: 'High',
    avgSalary: '$90,000 - $130,000',
    currentReadiness: 88,
    requiredCompetencies: [
      { skillId: 'data-sql-querying', skillName: 'Advanced SQL & Data Modeling', requiredMastery: 90, importance: 'Required', category: 'Data' },
      { skillId: 'data-numpy-pandas', skillName: 'NumPy & Pandas Processing', requiredMastery: 85, importance: 'Required', category: 'Data' },
      { skillId: 'math-prob-stats', skillName: 'Probability & Statistics', requiredMastery: 75, importance: 'Required', category: 'Math' }
    ],
    recommendedProjects: ['proj-enterprise-sql-warehouse'],
    recommendedCertifications: ['Microsoft Certified: Power BI Data Analyst']
  },
  {
    id: 'career-backend-engineer',
    title: 'Backend Developer (Python/Distributed)',
    category: 'Software Engineering',
    description: 'Architects robust REST/gRPC APIs, asynchronous background queue architectures, relational schemas, and microservice container clusters.',
    marketDemand: 'Very High',
    avgSalary: '$140,000 - $185,000',
    currentReadiness: 84,
    requiredCompetencies: [
      { skillId: 'prog-python-advanced', skillName: 'Python (Advanced)', requiredMastery: 95, importance: 'Required', category: 'Core' },
      { skillId: 'prog-data-structures', skillName: 'Data Structures & Algorithms', requiredMastery: 90, importance: 'Required', category: 'Core' },
      { skillId: 'prog-docker-containers', skillName: 'Docker & Containerization', requiredMastery: 80, importance: 'Required', category: 'Infrastructure' },
      { skillId: 'data-sql-querying', skillName: 'Advanced SQL & Data Modeling', requiredMastery: 85, importance: 'Required', category: 'Data' }
    ],
    recommendedProjects: ['proj-distributed-job-queue'],
    recommendedCertifications: ['AWS Certified Developer Associate']
  },
  {
    id: 'career-cloud-engineer',
    title: 'Cloud & MLOps Engineer',
    category: 'Cloud & Infrastructure',
    description: 'Manages Kubernetes clusters, GPU node provisioners, terraform infrastructure-as-code, and resilient multi-region architectures.',
    marketDemand: 'High',
    avgSalary: '$150,000 - $205,000',
    currentReadiness: 62,
    requiredCompetencies: [
      { skillId: 'prog-docker-containers', skillName: 'Docker & Containerization', requiredMastery: 90, importance: 'Required', category: 'Infrastructure' },
      { skillId: 'mlops-model-serving', skillName: 'Model Serving & Inference', requiredMastery: 85, importance: 'Required', category: 'MLOps' }
    ],
    recommendedProjects: ['proj-k8s-gpu-autoscaling'],
    recommendedCertifications: ['Google Cloud Professional Cloud Architect']
  }
];

export const INITIAL_ROADMAP_MILESTONES: RoadmapMilestone[] = [
  {
    id: 'ms-01',
    order: 1,
    title: 'Deepen PyTorch Autograd & Multi-GPU Tensors',
    skillId: 'dl-pytorch',
    domain: 'Deep Learning & NLP',
    state: 'Active',
    reason: 'Prerequisite anchor for Transformer architectures. Current mastery (68%) must reach 85% to eliminate prerequisite bottlenecks.',
    prerequisites: ['prog-python-advanced', 'dl-neural-networks'],
    estimatedDuration: '6 hours',
    masteryTarget: 85,
    currentMastery: 68,
    completionCondition: 'Pass Adaptive PyTorch Assessment with ≥80% score or submit verified DDP script.',
    evidenceGenerated: 'Verified Assessment Artifact (dl-pytorch-mastery-eval)',
    practiceTasks: [
      'Write custom autograd Function with backward pass verification',
      'Optimize PyTorch DataLoader with pin_memory and num_workers tuning',
      'Benchmark gradient accumulation against pure batch scaling'
    ],
    resourceIds: ['res-pytorch-internals', 'res-pytorch-official-tutorials'],
    assessmentId: 'assess-pytorch-adaptive'
  },
  {
    id: 'ms-02',
    order: 2,
    title: 'Master Transformer Attention & KV Cache Mechanisms',
    skillId: 'dl-transformers',
    domain: 'Deep Learning & NLP',
    state: 'Active',
    reason: 'Highest priority direct gap for AI Engineer. Essential for understanding modern LLM decoding, FlashAttention, and context limits.',
    prerequisites: ['dl-pytorch'],
    estimatedDuration: '10 hours',
    masteryTarget: 85,
    currentMastery: 46,
    completionCondition: 'Complete transformer coding challenge and build minimal GPT decoder from scratch.',
    evidenceGenerated: 'Verified GitHub Coding Artifact & Skill Verification Badge',
    practiceTasks: [
      'Implement multi-head self-attention module in 50 lines of PyTorch',
      'Derive rotary positional embedding (RoPE) tensor transformation',
      'Calculate exact memory footprint of KV Cache for 7B parameter model'
    ],
    resourceIds: ['res-attention-paper-deepdive', 'res-karpathy-nanogpt'],
    assessmentId: 'assess-transformers-mastery',
    projectId: 'proj-transformer-from-scratch'
  },
  {
    id: 'ms-03',
    order: 3,
    title: 'Production RAG: Hybrid Search & Re-ranking Verification',
    skillId: 'dl-rag-systems',
    domain: 'Deep Learning & NLP',
    state: 'Active',
    reason: 'Resume claims RAG experience (ev-005) but current verification state is Needs Review. Verifying turns unverified claim into high-weight proof.',
    prerequisites: ['data-vector-databases', 'dl-transformers'],
    estimatedDuration: '8 hours',
    masteryTarget: 82,
    currentMastery: 62,
    completionCondition: 'Submit production RAG repo and pass automated rubric benchmark with >85% score.',
    evidenceGenerated: 'Verified Project Evidence (ev-rag-capstone-verified)',
    practiceTasks: [
      'Implement BM25 lexical + dense vector reciprocal rank fusion (RRF)',
      'Add cross-encoder re-ranking step with latency under 120ms',
      'Benchmark context precision using synthetic evaluation dataset'
    ],
    resourceIds: ['res-rag-advanced-patterns'],
    projectId: 'proj-rag-hybrid'
  },
  {
    id: 'ms-04',
    order: 4,
    title: 'Parameter-Efficient Fine-Tuning (PEFT / QLoRA)',
    skillId: 'dl-llm-finetuning',
    domain: 'Deep Learning & NLP',
    state: 'Locked',
    reason: 'Blocked by prerequisite milestone: Requires Transformer Mastery (≥75%) and PyTorch (≥80%) to unlock.',
    prerequisites: ['dl-transformers', 'dl-pytorch'],
    estimatedDuration: '12 hours',
    masteryTarget: 75,
    currentMastery: 35,
    completionCondition: 'Fine-tune a quantized Llama-3-8B checkpoint on custom domain task and log evaluation.',
    evidenceGenerated: 'Weights & Biases training run artifact and benchmark report',
    practiceTasks: [
      'Configure bitsandbytes 4-bit NormalFloat (NF4) quantization',
      'Initialize LoRA rank and alpha hyperparameter matrix on attention projections',
      'Compare memory usage: full fine-tune vs QLoRA on single 24GB GPU'
    ],
    resourceIds: ['res-qlora-paper-guide']
  },
  {
    id: 'ms-05',
    order: 5,
    title: 'High-Throughput Model Serving with vLLM & PagedAttention',
    skillId: 'mlops-model-serving',
    domain: 'MLOps & Deployment',
    state: 'Locked',
    reason: 'Final production readiness milestone for AI Engineer role.',
    prerequisites: ['prog-docker-containers', 'dl-transformers'],
    estimatedDuration: '7 hours',
    masteryTarget: 75,
    currentMastery: 42,
    completionCondition: 'Deploy vLLM container with continuous batching and report latency percentiles (P95/P99).',
    evidenceGenerated: 'Verified Docker Compose & Load Testing Benchmark Artifact',
    practiceTasks: [
      'Set up vLLM OpenAI-compatible server with continuous batching',
      'Execute load testing with Locust simulating 50 concurrent streaming users',
      'Measure throughput (tokens/sec) vs native HuggingFace pipeline'
    ],
    resourceIds: ['res-vllm-serving-guide'],
    projectId: 'proj-vllm-serving-bench'
  }
];

export const INITIAL_RESOURCES: LearningResource[] = [
  {
    id: 'res-pytorch-internals',
    title: 'PyTorch Under the Hood: Autograd Engine & Memory Management',
    provider: 'Edward Z. Yang (PyTorch Core Team)',
    skillId: 'dl-pytorch',
    skillName: 'PyTorch Framework & Tensors',
    type: 'Article',
    difficulty: 'Intermediate',
    duration: '45 mins',
    qualityRating: 4.9,
    prerequisites: ['prog-python-advanced'],
    reasonRecommended: 'Directly addresses your 68% PyTorch mastery; explains the C++ tensor dispatch table and autograd tape graph.',
    url: 'http://blog.ezyang.com/2019/05/pytorch-internals/',
    bookmarked: true,
    completed: false
  },
  {
    id: 'res-karpathy-nanogpt',
    title: 'Build nanoGPT from Scratch: Full Attention & Decoder Implementation',
    provider: 'Andrej Karpathy (YouTube / GitHub)',
    skillId: 'dl-transformers',
    skillName: 'Transformer Architecture & Attention',
    type: 'Video',
    difficulty: 'Intermediate',
    duration: '2 hours 15 mins',
    qualityRating: 5.0,
    prerequisites: ['dl-pytorch'],
    reasonRecommended: 'Covers your highest-priority Transformer gap (46% mastery) through line-by-line coding of Multi-Head Attention.',
    url: 'https://github.com/karpathy/nanoGPT',
    bookmarked: true,
    completed: false
  },
  {
    id: 'res-attention-paper-deepdive',
    title: 'Attention Is All You Need: Mathematical & Hardware Breakdown',
    provider: 'Harvard NLP & Annotated Transformer',
    skillId: 'dl-transformers',
    skillName: 'Transformer Architecture & Attention',
    type: 'Documentation',
    difficulty: 'Advanced',
    duration: '1 hour 30 mins',
    qualityRating: 4.8,
    prerequisites: ['math-linear-algebra', 'dl-neural-networks'],
    reasonRecommended: 'Strengthens theoretical confidence gap detected in baseline diagnostic regarding query-key dimension scaling.',
    url: 'http://nlp.seas.harvard.edu/annotated-transformer/',
    bookmarked: false,
    completed: false
  },
  {
    id: 'res-rag-advanced-patterns',
    title: 'Advanced RAG Architectures: Hybrid Search, Cross-Encoders & HyDE',
    provider: 'LlamaIndex Research',
    skillId: 'dl-rag-systems',
    skillName: 'Retrieval Augmented Generation (RAG)',
    type: 'Lab',
    difficulty: 'Intermediate',
    duration: '2 hours',
    qualityRating: 4.8,
    prerequisites: ['data-vector-databases'],
    reasonRecommended: 'Guides your Capstone RAG verification submission, helping you satisfy the automated rubric criteria.',
    url: 'https://docs.llamaindex.ai/en/stable/optimizing/advanced_retrieval/advanced_retrieval/',
    bookmarked: false,
    completed: false
  },
  {
    id: 'res-qlora-paper-guide',
    title: 'Efficient LLM Fine-Tuning with LoRA & 4-bit Quantization (QLoRA)',
    provider: 'HuggingFace PEFT Lab',
    skillId: 'dl-llm-finetuning',
    skillName: 'LLM Fine-Tuning & Quantization',
    type: 'Course',
    difficulty: 'Advanced',
    duration: '3 hours 30 mins',
    qualityRating: 4.9,
    prerequisites: ['dl-transformers', 'dl-pytorch'],
    reasonRecommended: 'Prepares you for the upcoming PEFT milestone once Transformer prerequisites reach 80%.',
    url: 'https://huggingface.co/blog/4bit-transformers-bitsandbytes',
    bookmarked: false,
    completed: false
  },
  {
    id: 'res-vllm-serving-guide',
    title: 'PagedAttention & vLLM: High-Throughput Serving Architecture',
    provider: 'UC Berkeley LMSYS Organization',
    skillId: 'mlops-model-serving',
    skillName: 'Model Serving & Inference Optimization',
    type: 'Article',
    difficulty: 'Advanced',
    duration: '1 hour',
    qualityRating: 4.9,
    prerequisites: ['prog-docker-containers'],
    reasonRecommended: 'Explains virtual memory paging for KV Cache, reducing GPU memory waste by up to 80%.',
    url: 'https://vllm.ai/paged-attention',
    bookmarked: false,
    completed: false
  }
];

export const INITIAL_ASSESSMENTS: AssessmentItem[] = [
  {
    id: 'assess-pytorch-adaptive',
    title: 'PyTorch Deep Learning & Tensor Operations Mastery',
    category: 'Skill Assessment',
    skillId: 'dl-pytorch',
    skillName: 'PyTorch Framework & Tensors',
    difficulty: 'Intermediate',
    estimatedTime: '8 mins',
    questionsCount: 4,
    targetSkillsImpacted: [
      { skillId: 'dl-pytorch', skillName: 'PyTorch Framework', baselineMastery: 68, targetMastery: 84 },
      { skillId: 'dl-neural-networks', skillName: 'Neural Networks', baselineMastery: 82, targetMastery: 88 }
    ],
    questions: [
      {
        id: 'q-pt-1',
        type: 'MCQ',
        topic: 'Autograd & Gradient Accumulation',
        question: 'When performing gradient accumulation across 4 micro-batches in PyTorch, which sequence of calls is correct before updating optimizer parameters?',
        options: [
          'Call optimizer.zero_grad() after every micro-batch loss.backward()',
          'Call loss.backward() on each micro-batch, then optimizer.step() and optimizer.zero_grad() once every 4 batches',
          'Call optimizer.step() after every micro-batch, and loss.backward() only on the 4th batch',
          'Call torch.no_grad() during backward passes to prevent recursion'
        ],
        correctAnswers: [1],
        explanation: 'In gradient accumulation, gradients accumulate in tensor.grad buffers across iterations. Therefore, loss.backward() is called per micro-batch, while optimizer.step() and optimizer.zero_grad() are executed once every N batches.'
      },
      {
        id: 'q-pt-2',
        type: 'Multiple Select',
        topic: 'DataLoader & Memory Throughput',
        question: 'Which techniques directly prevent the GPU from waiting on host CPU I/O during model training? (Select all that apply)',
        options: [
          'Setting pin_memory=True in the DataLoader to allocate pinned page-locked host memory',
          'Tuning num_workers to utilize multi-process asynchronous batch prefetching',
          'Calling torch.cuda.empty_cache() after every mini-batch inside the training loop',
          'Using non_blocking=True when transferring batches to GPU via tensor.to(device, non_blocking=True)'
        ],
        correctAnswers: [0, 1, 3],
        explanation: 'pin_memory, multi-worker prefetching, and non_blocking host-to-device transfers hide I/O latency. Conversely, empty_cache() forces synchronization and severely degrades training throughput.'
      },
      {
        id: 'q-pt-3',
        type: 'Coding',
        topic: 'Custom Autograd Function',
        question: 'Examine the custom ReLU implementation below. What critical issue occurs if save_for_backward is omitted in the forward pass?',
        codeSnippet: `class CustomReLU(torch.autograd.Function):
    @staticmethod
    def forward(ctx, input_tensor):
        # Missing ctx.save_for_backward(input_tensor)
        return input_tensor.clamp(min=0)

    @staticmethod
    def backward(ctx, grad_output):
        # Attempts to read input tensor to compute mask
        input_tensor, = ctx.saved_tensors
        grad_input = grad_output.clone()
        grad_input[input_tensor <= 0] = 0
        return grad_input`,
        options: [
          'The backward pass will crash with a RuntimeError because ctx.saved_tensors is empty',
          'The output tensor becomes non-differentiable silently without throwing an error',
          'The GPU memory will leak because PyTorch holds the entire computational graph',
          'The gradients will automatically default to torch.ones_like(input_tensor)'
        ],
        correctAnswers: [0],
        explanation: 'ctx.save_for_backward() tells the PyTorch autograd engine to retain tensors required for gradient computation. Attempting to unpack ctx.saved_tensors without saving results in a runtime error.'
      },
      {
        id: 'q-pt-4',
        type: 'Reasoning',
        topic: 'Distributed Data Parallel (DDP) vs DataParallel (DP)',
        question: 'Why does PyTorch strongly recommend torch.nn.parallel.DistributedDataParallel (DDP) over torch.nn.DataParallel (DP) for multi-GPU training?',
        options: [
          'DDP spawns a separate OS process per GPU, completely circumventing Python GIL bottlenecks and avoiding single-GPU scatter/gather overhead',
          'DP only works with CPU tensors and cannot access NVIDIA NVLink interconnects',
          'DDP automatically quantizes all weights into 8-bit integers during gradient synchronization',
          'DP does not support backpropagation across recurrent layers'
        ],
        correctAnswers: [0],
        explanation: 'DDP runs multi-process, eliminating the Global Interpreter Lock (GIL) constraint and utilizing efficient Ring-AllReduce collectives rather than centralized GPU 0 scatter/gather.'
      }
    ]
  },
  {
    id: 'assess-transformers-mastery',
    title: 'Transformer Architecture, Attention & Decoding Dynamics',
    category: 'Concept Assessment',
    skillId: 'dl-transformers',
    skillName: 'Transformer Architecture & Attention',
    difficulty: 'Intermediate',
    estimatedTime: '10 mins',
    questionsCount: 3,
    targetSkillsImpacted: [
      { skillId: 'dl-transformers', skillName: 'Transformer Architecture', baselineMastery: 46, targetMastery: 72 },
      { skillId: 'dl-rag-systems', skillName: 'RAG Systems', baselineMastery: 62, targetMastery: 68 }
    ],
    questions: [
      {
        id: 'q-tr-1',
        type: 'MCQ',
        topic: 'Scaled Dot-Product Attention',
        question: 'Why is the dot-product of Query (Q) and Key (K) scaled by 1/sqrt(d_k) before applying the softmax function?',
        options: [
          'To prevent the dot products from growing large in magnitude for large d_k, which would push softmax into regions with vanishingly small gradients',
          'To ensure the attention weights sum to exactly 1.0 along the sequence dimension',
          'To invert the covariance matrix of token embeddings',
          'To normalize the output vector to have zero mean and unit variance'
        ],
        correctAnswers: [0],
        explanation: 'For large values of d_k, the dot products grow large in magnitude, pushing the softmax function into regions where it has extremely small gradients. Dividing by sqrt(d_k) stabilizes the variance of the logits.'
      },
      {
        id: 'q-tr-2',
        type: 'Reasoning',
        topic: 'KV Cache in Autoregressive LLM Generation',
        question: 'During autoregressive token-by-token generation in a 7B parameter decoder model, what is the primary computational benefit of maintaining a Key-Value (KV) Cache?',
        options: [
          'It avoids re-computing the Key and Value projections of previous prompt and generated tokens, reducing attention time from O(N^2) to O(N) per step',
          'It compresses token embeddings by 50% using FP8 floating point registers',
          'It allows bidirectional attention masking during the generation phase',
          'It eliminates the need for Positional Embeddings in subsequent forward passes'
        ],
        correctAnswers: [0],
        explanation: 'Without KV caching, each newly generated token requires recomputing Q, K, and V for all prior tokens in the sequence. With KV caching, previous K and V vectors are stored in GPU memory, and only the single new token is projected.'
      },
      {
        id: 'q-tr-3',
        type: 'MCQ',
        topic: 'Rotary Position Embedding (RoPE)',
        question: 'How does Rotary Position Embedding (RoPE) represent token positions compared to absolute sinusoidal embeddings?',
        options: [
          'It rotates the Query and Key vectors in 2D complex planes such that the inner product depends strictly on the relative distance (m - n)',
          'It learns a lookup table of fixed vectors added directly to the input token embeddings',
          'It computes positional distance strictly via hyperbolic graph distances',
          'It discards positional information entirely in favor of causal attention masks'
        ],
        correctAnswers: [0],
        explanation: 'RoPE applies an orthogonal rotation matrix to Query and Key representations, ensuring their dot product inherently encodes the relative position between tokens (m - n).'
      }
    ]
  },
  {
    id: 'assess-baseline-diagnostic',
    title: 'AI Engineer Baseline Diagnostic Assessment',
    category: 'Baseline Diagnostic',
    skillId: 'ml-supervised',
    skillName: 'General AI Foundations',
    difficulty: 'Beginner',
    estimatedTime: '5 mins',
    questionsCount: 3,
    targetSkillsImpacted: [
      { skillId: 'math-prob-stats', skillName: 'Probability & Stats', baselineMastery: 70, targetMastery: 80 },
      { skillId: 'ml-supervised', skillName: 'Supervised ML', baselineMastery: 75, targetMastery: 85 }
    ],
    questions: [
      {
        id: 'q-diag-1',
        type: 'MCQ',
        topic: 'Model Overfitting & Regularization',
        question: 'If a machine learning model achieves 99.2% accuracy on the training set but only 64.1% accuracy on the validation holdout, what is the most likely diagnosis?',
        options: [
          'High Variance (Overfitting) - model memorized training noise and fails to generalize',
          'High Bias (Underfitting) - model is too simple to capture the underlying pattern',
          'Data Leakage from validation set into training set',
          'The learning rate is too small causing underconvergence'
        ],
        correctAnswers: [0],
        explanation: 'A large discrepancy between high training accuracy and low validation accuracy is the textbook hallmark of high variance / overfitting.'
      },
      {
        id: 'q-diag-2',
        type: 'MCQ',
        topic: 'Vector Similarity Metrics',
        question: 'For normalized embedding vectors of unit length (|u| = 1, |v| = 1), what is the mathematical relationship between Cosine Similarity and Dot Product?',
        options: [
          'They are exactly identical: Cosine Similarity = Dot Product',
          'Cosine similarity is always the square of the dot product',
          'Dot product is always double the cosine similarity',
          'They are inversely proportional'
        ],
        correctAnswers: [0],
        explanation: 'Cosine similarity is defined as (u · v) / (|u| * |v|). When vectors have unit length (|u| = |v| = 1), cosine similarity simplifies directly to the dot product.'
      },
      {
        id: 'q-diag-3',
        type: 'MCQ',
        topic: 'Gradient Descent Optimization',
        question: 'Why does Adam optimizer typically converge faster than basic Stochastic Gradient Descent (SGD) on sparse neural network landscapes?',
        options: [
          'Adam computes individual adaptive learning rates for each parameter using estimates of first and second moments of gradients',
          'Adam evaluates the entire dataset on every single parameter update',
          'Adam calculates the exact Hessian inverse matrix on every step',
          'Adam replaces backpropagation with genetic algorithm mutations'
        ],
        correctAnswers: [0],
        explanation: 'Adam combines the advantages of AdaGrad (handling sparse gradients) and RMSProp (handling non-stationary objectives) by tracking moving averages of both gradient and squared gradient.'
      }
    ]
  }
];

export const INITIAL_PROJECTS: ProjectItem[] = [
  {
    id: 'proj-rag-hybrid',
    title: 'Enterprise Hybrid RAG System with Re-ranking & Evaluator',
    difficulty: 'Capstone',
    skillsValidated: ['dl-rag-systems', 'data-vector-databases', 'ml-model-evaluation'],
    concepts: ['Reciprocal Rank Fusion', 'Cross-Encoder Re-ranking', 'Contextual Grounding Benchmark'],
    careerRelevance: 'Directly fulfills 2 critical requirements for AI Engineer. Resolves unverified resume claim ev-005.',
    estimatedEffort: '15 - 20 hours',
    evidenceValue: 'Critical',
    reasonRecommended: 'You claimed RAG on your resume; passing automated rubric verification validates this claim and elevates your ATS evidence coverage from 58% to 85%.',
    objective: 'Build an end-to-end question answering pipeline combining dense vector embeddings (OpenAI/BGE) and BM25 sparse search with Cohere cross-encoder re-ranking and Ragas test evaluation.',
    requirements: [
      'Implement chunking strategy with semantic sentence boundary preservation',
      'Dual indexing: Dense embedding in Chroma/Qdrant + BM25 inverted index',
      'Reciprocal Rank Fusion (RRF) algorithm to merge sparse & dense ranking',
      'Cross-encoder re-ranking stage with target latency < 150ms',
      'Automated synthetic test evaluation pipeline with minimum 0.85 faithfulness score'
    ],
    prerequisites: ['dl-transformers', 'data-vector-databases'],
    deliverables: [
      'Clean GitHub repository with README, architecture diagram, and MIT license',
      'Benchmark results file comparing Naive RAG vs Hybrid + Re-ranking',
      'Docker Compose deployment file with health check endpoint'
    ],
    rubric: [
      { criterion: 'Hybrid Retrieval Implementation (BM25 + Dense RRF)', weight: 30, targetLevel: 'Production Grade' },
      { criterion: 'Cross-Encoder Re-ranking & Latency Profiling', weight: 25, targetLevel: 'P95 < 150ms' },
      { criterion: 'Evaluation Benchmark & Faithfulness Metrics', weight: 25, targetLevel: 'Ragas Score > 0.85' },
      { criterion: 'Code Quality, Type Safety & Docker Containerization', weight: 20, targetLevel: 'Passes Ruff & MyPy' }
    ],
    testCriteria: [
      'passes 14/14 automated unit tests for chunking and search',
      're-ranking latency P95 under 150ms on 100 concurrent queries',
      'zero halluncination detected on adversarial negation prompts'
    ],
    verified: false
  },
  {
    id: 'proj-transformer-from-scratch',
    title: 'Minimal Autoregressive Transformer Decoder from Scratch',
    difficulty: 'Advanced',
    skillsValidated: ['dl-transformers', 'dl-pytorch'],
    concepts: ['Multi-Head Self Attention', 'Causal Masking', 'KV Cache', 'Rotary Embeddings'],
    careerRelevance: 'Demonstrates foundational deep learning mastery beyond simply importing HuggingFace pipelines.',
    estimatedEffort: '10 - 14 hours',
    evidenceValue: 'Critical',
    reasonRecommended: 'Closes the 46% Transformer gap by implementing the actual mathematical tensor operations in native PyTorch.',
    objective: 'Code a clean, educational, yet efficient GPT-style causal decoder in pure PyTorch without relying on torch.nn.Transformer.',
    requirements: [
      'Custom MultiHeadAttention module with scaled dot-product and causal mask',
      'RMSNorm and SwiGLU feed-forward layer implementations',
      'KV Cache generator loop supporting streaming token generation',
      'Train minimal 15M parameter model on TinyShakespeare to validation loss < 1.4'
    ],
    prerequisites: ['dl-pytorch'],
    deliverables: [
      'model.py with zero external dependencies other than torch',
      'generate.py demonstrating KV Cache speedup benchmark',
      'Training loss curve wandb / matplotlib export'
    ],
    rubric: [
      { criterion: 'Mathematical Correctness of Attention Projections', weight: 35, targetLevel: 'Exact' },
      { criterion: 'KV Cache Correctness & Memory Efficiency', weight: 35, targetLevel: 'O(N) generation verified' },
      { criterion: 'Training Convergence on Validation Set', weight: 30, targetLevel: 'Val Loss < 1.4' }
    ],
    testCriteria: [
      'custom attention output matches torch.nn.functional.scaled_dot_product_attention within 1e-5 epsilon',
      'KV cache generation delivers ≥ 3.5x tokens/sec speedup on sequence length 512'
    ],
    verified: false
  },
  {
    id: 'proj-vllm-serving-bench',
    title: 'Production LLM Inference Server with vLLM & Prometheus Telemetry',
    difficulty: 'Intermediate',
    skillsValidated: ['mlops-model-serving', 'prog-docker-containers'],
    concepts: ['Continuous Batching', 'PagedAttention', 'OpenAI API Spec', 'Prometheus Metrics'],
    careerRelevance: 'Essential MLOps proof demonstrating readiness to deploy models in enterprise cloud environments.',
    estimatedEffort: '8 - 10 hours',
    evidenceValue: 'High',
    reasonRecommended: 'Validates MLOps capability on your profile and satisfies the Cloud/Deployment requirement for AI Engineer.',
    objective: 'Deploy Mistral-7B or Llama-3-8B using vLLM in a multi-stage Docker container with Prometheus metrics tracking TTFT and tokens/sec.',
    requirements: [
      'Docker container configured with NVIDIA Container Toolkit runtime',
      'OpenAI compatible /v1/chat/completions endpoint with token streaming',
      'Load testing script using Locust or k6 simulating concurrent requests',
      'Grafana dashboard JSON monitoring Time to First Token (TTFT)'
    ],
    prerequisites: ['prog-docker-containers'],
    deliverables: [
      'Dockerfile & docker-compose.yml',
      'Benchmark report: vLLM vs naive HuggingFace pipeline throughput',
      'Grafana dashboard export'
    ],
    rubric: [
      { criterion: 'Containerization & GPU Driver Configuration', weight: 30, targetLevel: 'Flawless startup' },
      { criterion: 'Throughput Benchmark & Continuous Batching Metrics', weight: 40, targetLevel: '≥4x speedup documented' },
      { criterion: 'Observability & P99 Latency Telemetry', weight: 30, targetLevel: 'Complete Grafana metrics' }
    ],
    testCriteria: [
      'successful deployment on single GPU instance',
      'sustained 80+ tokens/second under 20 concurrent user load'
    ],
    verified: false
  }
];

export const INITIAL_RESUME_ANALYSIS: ResumeAnalysis = {
  fileName: 'Alex_Rivera_Resume_2026.pdf',
  uploadedAt: '2026-03-01',
  resumeScore: 74,
  atsCompatibilityScore: 82,
  sectionsDetected: [
    'Education',
    'Technical Skills',
    'Academic Projects',
    'Work Experience',
    'Awards & Honors'
  ],
  extractedSkillsCount: 18,
  verifiedClaimsCount: 11,
  unsupportedClaimsCount: 7,
  careerAlignmentScore: 68,
  evidenceCoveragePercent: 58,
  claims: [
    {
      id: 'rc-1',
      claim: 'Expert in Python, developing high-throughput asynchronous backend systems and data scripts',
      skillName: 'Python (Advanced)',
      skillId: 'prog-python-advanced',
      section: 'Technical Skills',
      evidenceState: 'Verified',
      evidenceId: 'ev-002',
      relatedCareerRequirement: 'AI Engineer / Core Programming',
      recommendedAction: 'Claim fully backed by GitHub artifact and verified benchmarks.'
    },
    {
      id: 'rc-2',
      claim: 'Strong mathematical background in Linear Algebra, Multivariate Calculus and Bayesian Statistics',
      skillName: 'Linear Algebra & Statistics',
      skillId: 'math-linear-algebra',
      section: 'Education',
      evidenceState: 'Verified',
      evidenceId: 'ev-003',
      relatedCareerRequirement: 'AI Engineer / Foundations',
      recommendedAction: 'Claim verified by official transcript and baseline diagnostic test.'
    },
    {
      id: 'rc-3',
      claim: 'Trained and fine-tuned custom deep neural networks using PyTorch for computer vision and NLP tasks',
      skillName: 'PyTorch Framework',
      skillId: 'dl-pytorch',
      section: 'Academic Projects',
      evidenceState: 'In Progress',
      evidenceId: 'ev-004',
      relatedCareerRequirement: 'AI Engineer / Deep Learning (Required)',
      recommendedAction: 'Complete Adaptive PyTorch Assessment to upgrade from Estimated to Verified.'
    },
    {
      id: 'rc-4',
      claim: 'Built enterprise-grade RAG pipelines utilizing vector databases and semantic search for document intelligence',
      skillName: 'Retrieval Augmented Generation (RAG)',
      skillId: 'dl-rag-systems',
      section: 'Academic Projects',
      evidenceState: 'Unsupported',
      evidenceId: 'ev-005',
      relatedCareerRequirement: 'AI Engineer / Applications (Critical)',
      recommendedAction: 'Verify Capstone RAG Project to provide verifiable proof for this resume claim.'
    },
    {
      id: 'rc-5',
      claim: 'Experience with Transformer self-attention architectures and LLM prompt engineering',
      skillName: 'Transformer Architecture & Attention',
      skillId: 'dl-transformers',
      section: 'Technical Skills',
      evidenceState: 'Unsupported',
      relatedCareerRequirement: 'AI Engineer / Core Deep Learning (Critical)',
      recommendedAction: 'Complete Transformer Coding Milestone to substantiate this claim.'
    },
    {
      id: 'rc-6',
      claim: 'Containerized microservices using Docker and automated CI/CD deployment workflows',
      skillName: 'Docker & Containerization',
      skillId: 'prog-docker-containers',
      section: 'Work Experience',
      evidenceState: 'Verified',
      evidenceId: 'ev-007',
      relatedCareerRequirement: 'AI Engineer / Infrastructure',
      recommendedAction: 'Supported by DeepLearning.AI verified credential.'
    },
    {
      id: 'rc-7',
      claim: 'Deployed large language models with low latency inference serving and monitoring pipelines',
      skillName: 'Model Serving & Inference Optimization',
      skillId: 'mlops-model-serving',
      section: 'Academic Projects',
      evidenceState: 'Unsupported',
      relatedCareerRequirement: 'AI Engineer / MLOps',
      recommendedAction: 'Complete vLLM Serving Benchmark project to verify claim.'
    }
  ],
  missingSkillsForTarget: [
    'Transformer Attention Mechanisms (Direct Gap)',
    'vLLM / Triton Model Serving (MLOps Gap)',
    'Quantization & QLoRA Fine-Tuning (Advanced Gap)',
    'HNSW Vector Index Tuning (Data Systems Gap)'
  ],
  weakClaims: [
    '"Experience with Transformer self-attention architectures" — lacks specific metrics, repository link, or verifiable benchmark.',
    '"Deployed LLMs with low latency" — zero performance metrics (P95 latency, tokens/sec, GPU specs) provided in bullet point.'
  ],
  suggestedImprovements: [
    'Substantiate the RAG bullet point with quantitative retrieval precision scores and link to verified repository.',
    'Replace generic "Experience with Transformers" with concrete architecture parameters (e.g., "Implemented Multi-Head Attention and RoPE in pure PyTorch").',
    'Include containerized deployment metrics (e.g., "Deployed vLLM inference server achieving 84 tokens/sec under 20 concurrent streams").'
  ],
  recommendedProofProject: 'proj-rag-hybrid'
};

export const INITIAL_ACTIVITIES: ActivityItem[] = [
  {
    id: 'act-1',
    type: 'Evidence Verified',
    title: 'Transcript Verified for Demo ML Course',
    description: 'UC Berkeley academic record verified: Supervised Learning mastery established at 84%.',
    timestamp: '2 hours ago',
    delta: '+12% ML Mastery',
    linkTab: 'profile'
  },
  {
    id: 'act-2',
    type: 'Assessment Completed',
    title: 'Linear Algebra Baseline Diagnostic',
    description: 'Diagnostic completed with 92% accuracy. Linear Algebra confirmed at 88% mastery.',
    timestamp: '3 days ago',
    delta: 'Verified',
    linkTab: 'assessments'
  },
  {
    id: 'act-3',
    type: 'Roadmap Recalculated',
    title: 'Adaptive Roadmap Initialized',
    description: 'Target career set to AI Engineer. 5 prioritized adaptive milestones generated based on competency gaps.',
    timestamp: '3 days ago',
    linkTab: 'roadmap'
  },
  {
    id: 'act-4',
    type: 'Project Recommended',
    title: 'Capstone Hybrid RAG Recommended',
    description: 'Recommended project to resolve unsupported resume claim ev-005 and boost career readiness.',
    timestamp: '4 days ago',
    linkTab: 'projects'
  }
];

export const INITIAL_NOTIFICATIONS: NotificationItem[] = [
  {
    id: 'notif-1',
    title: 'Assessment Recommendation',
    message: 'Adaptive PyTorch Assessment is available to unlock your Transformer milestone.',
    type: 'assessment',
    timestamp: '15 mins ago',
    read: false,
    linkTab: 'assessments'
  },
  {
    id: 'notif-2',
    title: 'Critical Gap Identified',
    message: 'Transformer Architecture detected as a priority skill gap for AI Engineer (46% vs 85% required).',
    type: 'roadmap',
    timestamp: '2 hours ago',
    read: false,
    linkTab: 'competencies'
  },
  {
    id: 'notif-3',
    title: 'Evidence Pending Review',
    message: 'Resume claim regarding enterprise RAG pipeline is awaiting project artifact verification.',
    type: 'verification',
    timestamp: '1 day ago',
    read: true,
    linkTab: 'resume'
  },
  {
    id: 'notif-4',
    title: 'Roadmap Synchronized',
    message: 'Adaptive milestones re-ranked based on latest linear algebra assessment scores.',
    type: 'system',
    timestamp: '3 days ago',
    read: true,
    linkTab: 'roadmap'
  }
];

export const INITIAL_MENTOR_CONVERSATION: MentorMessage[] = [
  {
    id: 'msg-1',
    sender: 'assistant',
    timestamp: '10:00 AM',
    text: 'Welcome Alex. I am your grounded Competency & Career Intelligence advisor. I have analyzed your living competency profile, verified academic evidence, and target role (AI Engineer). How can I guide your plan today?',
    reasoningSummary: 'Living model indicates 68% readiness for AI Engineer with strong math/Python fundamentals, but high-impact gaps in Transformer attention and verifiable RAG project evidence.',
    suggestedAction: { label: 'Explore Priority Gaps', tab: 'competencies' }
  }
];
