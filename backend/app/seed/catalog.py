"""Skill graph, career targets and assessment banks.

Skill nodes carry layout coordinates (``x``/``y``) because the existing
competency graph renders an SVG canvas and expects stable positions.

Every skill's baseline mastery comes from linked evidence rather than from a
stored number: the competency engine recomputes it on every read.
"""

from __future__ import annotations

from typing import Any

# --------------------------------------------------------------------------
# Domains
# --------------------------------------------------------------------------
DOMAINS = (
    "Math & Foundations",
    "Core Programming",
    "Data Systems",
    "Machine Learning",
    "Deep Learning & NLP",
    "MLOps & Deployment",
)


def skill(
    skill_id: str,
    name: str,
    domain: str,
    node_type: str,
    importance: str,
    prerequisites: list[str],
    concepts: list[str],
    x: int,
    y: int,
    target_level: int = 85,
) -> dict[str, Any]:
    return {
        "id": skill_id,
        "slug": skill_id,
        "name": name,
        "domain": domain,
        "type": node_type,
        "careerImportance": importance,
        "prerequisites": prerequisites,
        "relatedConcepts": concepts,
        "targetLevel": target_level,
        "x": x,
        "y": y,
    }


SKILLS: list[dict[str, Any]] = [
    # --- Math & Foundations -------------------------------------------------
    skill("math-linear-algebra", "Linear Algebra", DOMAINS[0], "Prerequisite", "Critical", [],
          ["Eigenvalues & Eigenvectors", "Matrix Decomposition (SVD)", "Tensor Operations"], 80, 100),
    skill("math-multivariate-calculus", "Multivariate Calculus", DOMAINS[0], "Prerequisite", "Foundational",
          [], ["Gradients & Jacobians", "Hessian Matrices", "Chain Rule in Backprop"], 80, 220),
    skill("math-prob-stats", "Probability & Statistics", DOMAINS[0], "Concept", "Critical",
          ["math-linear-algebra"],
          ["Bayes Theorem", "Maximum Likelihood Estimation (MLE)", "Markov Chains"], 240, 100),
    skill("math-optimization", "Convex & Stochastic Optimization", DOMAINS[0], "Concept", "High",
          ["math-multivariate-calculus"],
          ["Gradient Descent Variants", "Adam & Momentum", "Learning Rate Schedules"], 240, 220),

    # --- Core Programming --------------------------------------------------
    skill("prog-python-advanced", "Python (Advanced)", DOMAINS[1], "Skill", "Critical", [],
          ["AsyncIO", "Metaclasses & Decorators", "Memory Profiling & C-Extensions"], 80, 350),
    skill("prog-data-structures", "Data Structures & Algorithms", DOMAINS[1], "Prerequisite", "Critical",
          ["prog-python-advanced"],
          ["Graphs & Trees", "Dynamic Programming", "Trie & Hash Indexes"], 240, 350),
    skill("prog-docker-containers", "Docker & Containerization", DOMAINS[1], "Skill", "High",
          ["prog-python-advanced"],
          ["Multi-Stage GPU Builds", "CUDA Base Containers", "Docker Compose"], 240, 470),
    skill("prog-testing-cicd", "Automated Testing & CI/CD", DOMAINS[1], "Skill", "High",
          ["prog-python-advanced"],
          ["Pytest Fixtures & Mocks", "GitHub Actions Matrix", "Coverage Gates"], 400, 470),
    skill("prog-rest-apis", "REST API & Service Design", DOMAINS[1], "Skill", "High",
          ["prog-python-advanced"],
          ["Idempotency & Versioning", "Pydantic Validation", "Auth Middleware"], 400, 590),

    # --- Data Systems ------------------------------------------------------
    skill("data-numpy-pandas", "NumPy & Pandas Processing", DOMAINS[2], "Skill", "Critical",
          ["prog-python-advanced"],
          ["Vectorization & Broadcasting", "Memory Mapping", "Time Series Alignment"], 400, 250),
    skill("data-sql-querying", "Advanced SQL & Data Modeling", DOMAINS[2], "Skill", "High",
          ["prog-python-advanced"],
          ["Window Functions", "Recursive CTEs", "Query Execution Plans"], 400, 370),
    skill("data-vector-databases", "Vector DBs & Embeddings Index", DOMAINS[2], "Career Requirement", "Critical",
          ["prog-data-structures", "data-sql-querying"],
          ["HNSW vs IVF Indexing", "Cosine vs Dot Product Metrics", "Chroma & Milvus"], 560, 370),
    skill("data-feature-store", "Feature Stores & Data Versioning", DOMAINS[2], "Skill", "Medium",
          ["data-sql-querying", "data-numpy-pandas"],
          ["Point-in-Time Joins", "DVC & Dataset Lineage", "Online/Offline Skew"], 560, 490),

    # --- Machine Learning --------------------------------------------------
    skill("ml-supervised", "Supervised Learning Algorithms", DOMAINS[3], "Skill", "Critical",
          ["math-linear-algebra", "math-prob-stats", "data-numpy-pandas"],
          ["Gradient Boosted Trees (XGBoost)", "Regularization (L1/L2)", "Support Vector Machines"], 560, 120),
    skill("ml-unsupervised", "Unsupervised & Dimensionality", DOMAINS[3], "Concept", "High",
          ["data-numpy-pandas"],
          ["t-SNE & UMAP", "K-Means & DBSCAN", "PCA Decomposition"], 560, 240),
    skill("ml-model-evaluation", "Model Evaluation & Validation", DOMAINS[3], "Career Requirement", "Critical",
          ["ml-supervised", "math-prob-stats"],
          ["ROC-AUC & Precision-Recall", "Cross-Validation & Leakage", "LLM Benchmark Metrics"], 720, 120),
    skill("ml-experiment-tracking", "Experiment Tracking & Reproducibility", DOMAINS[3], "Skill", "Medium",
          ["ml-model-evaluation"],
          ["Weights & Biases Runs", "Config Sweeps", "Artifact Lineage"], 720, 20),

    # --- Deep Learning & NLP ----------------------------------------------
    skill("dl-neural-networks", "Neural Network Architecture", DOMAINS[4], "Skill", "Critical",
          ["math-multivariate-calculus", "ml-supervised"],
          ["Backpropagation through Time", "Activation Functions", "Layer & Batch Normalization"], 720, 240),
    skill("dl-pytorch", "PyTorch Framework & Tensors", DOMAINS[4], "Career Requirement", "Critical",
          ["dl-neural-networks", "prog-python-advanced"],
          ["Autograd Engine", "Custom Dataset & DataLoader", "DistributedDataParallel (DDP)"], 880, 200),
    skill("dl-transformers", "Transformer Architecture & Attention", DOMAINS[4], "Career Requirement", "Critical",
          ["dl-pytorch"],
          ["Scaled Dot-Product Attention", "Multi-Head Attention", "Rotary Positional Embeddings", "KV Cache"],
          1040, 180),
    skill("dl-rag-systems", "Retrieval Augmented Generation (RAG)", DOMAINS[4], "Career Requirement", "Critical",
          ["data-vector-databases", "dl-transformers"],
          ["Contextual Chunking", "Cross-Encoder Re-ranking", "Self-RAG & Agentic Loops"], 1040, 320),
    skill("dl-llm-finetuning", "LLM Fine-Tuning & Quantization", DOMAINS[4], "Career Requirement", "Critical",
          ["dl-transformers", "dl-pytorch"],
          ["QLoRA & PEFT", "DPO vs PPO Alignment", "AWQ & GGUF Quantization"], 1200, 200),
    skill("dl-prompt-engineering", "Prompt & Context Engineering", DOMAINS[4], "Skill", "High",
          ["dl-transformers"],
          ["Few-Shot Templates", "Structured Output Constraints", "Context Budgeting"], 1200, 80),
    skill("dl-computer-vision", "Computer Vision Fundamentals", DOMAINS[4], "Concept", "Medium",
          ["dl-pytorch"],
          ["CNN Architectures", "Data Augmentation", "Detection & Segmentation"], 1200, 320),

    # --- MLOps & Deployment ------------------------------------------------
    skill("mlops-model-serving", "Model Serving & Inference Optimization", DOMAINS[5], "Career Requirement", "High",
          ["prog-docker-containers", "dl-pytorch"],
          ["vLLM & TensorRT-LLM", "Continuous Batching & PagedAttention", "Triton Inference Server"], 1040, 450),
    skill("mlops-production-pipeline", "CI/CD & Production LLM Pipelines", DOMAINS[5], "Career Requirement", "High",
          ["mlops-model-serving", "dl-rag-systems"],
          ["Langfuse Observability", "Prompt Versioning & Registry", "Cost & Token Guardrails"], 1200, 450),
    skill("mlops-monitoring", "Model Monitoring & Drift Detection", DOMAINS[5], "Skill", "Medium",
          ["ml-model-evaluation", "mlops-model-serving"],
          ["Data vs Concept Drift", "Latency SLO Alerting", "Shadow Deployments"], 1200, 560),
]


# --------------------------------------------------------------------------
# Careers: required skills, target mastery and importance
# --------------------------------------------------------------------------
CAREERS: list[dict[str, Any]] = [
    {
        "id": "career-ai-engineer",
        "slug": "career-ai-engineer",
        "title": "AI Engineer",
        "category": "Applied AI & Systems",
        "description": "Bridges deep learning models and scalable production software. Specialises in LLM architectures, RAG pipelines, model quantization, inference serving and evaluation.",
        "marketDemand": "Very High",
        "avgSalary": "$165,000 - $225,000",
        "recommendedProjects": ["proj-rag-hybrid", "proj-transformer-from-scratch", "proj-vllm-serving-bench"],
        "recommendedCertifications": [
            "NVIDIA Certified Associate: Generative AI LLMs",
            "AWS Certified Machine Learning - Specialty",
        ],
        "requirements": [
            ("prog-python-advanced", 90, "Required", "Core"),
            ("dl-pytorch", 85, "Required", "Deep Learning"),
            ("dl-transformers", 85, "Required", "Deep Learning"),
            ("dl-rag-systems", 80, "Required", "Applications"),
            ("data-vector-databases", 75, "Required", "Data Systems"),
            ("ml-model-evaluation", 80, "Required", "Validation"),
            ("dl-llm-finetuning", 75, "Preferred", "Deep Learning"),
            ("mlops-model-serving", 70, "Preferred", "MLOps"),
        ],
    },
    {
        "id": "career-data-scientist",
        "slug": "career-data-scientist",
        "title": "Data Scientist",
        "category": "Analytics & Predictive Modeling",
        "description": "Extracts strategic business intelligence, designs rigorous experiments and builds statistical and machine learning predictive models.",
        "marketDemand": "High",
        "avgSalary": "$140,000 - $190,000",
        "recommendedProjects": ["proj-enterprise-sql-warehouse", "proj-churn-predictive-pipeline"],
        "recommendedCertifications": ["Google Professional Data Engineer"],
        "requirements": [
            ("math-prob-stats", 90, "Required", "Math"),
            ("data-numpy-pandas", 90, "Required", "Data"),
            ("data-sql-querying", 85, "Required", "Data"),
            ("ml-supervised", 85, "Required", "ML"),
            ("ml-model-evaluation", 85, "Required", "Validation"),
            ("ml-unsupervised", 70, "Preferred", "ML"),
        ],
    },
    {
        "id": "career-ml-engineer",
        "slug": "career-ml-engineer",
        "title": "ML Engineer",
        "category": "Machine Learning Infrastructure",
        "description": "Develops automated training pipelines, distributed computing workflows and scalable real-time inference infrastructure for enterprise models.",
        "marketDemand": "Very High",
        "avgSalary": "$160,000 - $215,000",
        "recommendedProjects": ["proj-transformer-from-scratch", "proj-vllm-serving-bench"],
        "recommendedCertifications": ["Databricks Certified Machine Learning Professional"],
        "requirements": [
            ("prog-python-advanced", 90, "Required", "Core"),
            ("dl-pytorch", 85, "Required", "Deep Learning"),
            ("prog-docker-containers", 80, "Required", "Infrastructure"),
            ("mlops-model-serving", 80, "Required", "MLOps"),
            ("ml-experiment-tracking", 70, "Preferred", "ML"),
        ],
    },
    {
        "id": "career-data-analyst",
        "slug": "career-data-analyst",
        "title": "Data Analyst",
        "category": "Analytics & Reporting",
        "description": "Transforms raw corporate data into interactive dashboards, cohort analytics and executive business recommendations.",
        "marketDemand": "High",
        "avgSalary": "$90,000 - $130,000",
        "recommendedProjects": ["proj-enterprise-sql-warehouse"],
        "recommendedCertifications": ["Microsoft Certified: Power BI Data Analyst"],
        "requirements": [
            ("data-sql-querying", 90, "Required", "Data"),
            ("data-numpy-pandas", 85, "Required", "Data"),
            ("math-prob-stats", 75, "Required", "Math"),
            ("ml-supervised", 60, "Preferred", "ML"),
        ],
    },
    {
        "id": "career-backend-engineer",
        "slug": "career-backend-engineer",
        "title": "Backend Developer (Python/Distributed)",
        "category": "Software Engineering",
        "description": "Architects robust REST/gRPC APIs, asynchronous background queue architectures, relational schemas and microservice container clusters.",
        "marketDemand": "Very High",
        "avgSalary": "$140,000 - $185,000",
        "recommendedProjects": ["proj-enterprise-sql-warehouse"],
        "recommendedCertifications": ["AWS Certified Developer Associate"],
        "requirements": [
            ("prog-python-advanced", 95, "Required", "Core"),
            ("prog-data-structures", 90, "Required", "Core"),
            ("prog-docker-containers", 80, "Required", "Infrastructure"),
            ("data-sql-querying", 85, "Required", "Data"),
            ("prog-rest-apis", 80, "Required", "Core"),
            ("prog-testing-cicd", 75, "Preferred", "Quality"),
        ],
    },
    {
        "id": "career-cloud-engineer",
        "slug": "career-cloud-engineer",
        "title": "Cloud & MLOps Engineer",
        "category": "Cloud & Infrastructure",
        "description": "Manages Kubernetes clusters, GPU node provisioners, terraform infrastructure-as-code and resilient multi-region architectures.",
        "marketDemand": "High",
        "avgSalary": "$150,000 - $205,000",
        "recommendedProjects": ["proj-vllm-serving-bench"],
        "recommendedCertifications": ["Google Cloud Professional Cloud Architect"],
        "requirements": [
            ("prog-docker-containers", 90, "Required", "Infrastructure"),
            ("mlops-model-serving", 85, "Required", "MLOps"),
            ("prog-testing-cicd", 80, "Required", "Quality"),
            ("mlops-monitoring", 75, "Preferred", "MLOps"),
            ("mlops-production-pipeline", 80, "Required", "MLOps"),
        ],
    },
]
# Additional role coverage and prerequisite concepts.
SKILLS.extend([
    skill('web-html-css','HTML & CSS',DOMAINS[1],'Skill','High',[],['Semantic HTML','Responsive layout'],80,650),
    skill('web-typescript','JavaScript & TypeScript',DOMAINS[1],'Skill','High',[],['Type narrowing','Promises'],240,650),
    skill('web-react','React',DOMAINS[1],'Skill','High',['web-typescript','web-html-css'],['Component state','Accessibility'],400,650),
    skill('cloud-networking','Networking Fundamentals',DOMAINS[5],'Prerequisite','High',[],['DNS','TLS','TCP/IP'],560,650),
    skill('security-threats','Threat Modeling & Application Security',DOMAINS[5],'Skill','High',['cloud-networking','prog-rest-apis'],['OWASP','Least privilege'],720,650),
    skill('ops-linux','Linux Administration',DOMAINS[5],'Skill','High',[],['Processes','Permissions'],880,650),
    skill('ops-iac','Infrastructure as Code',DOMAINS[5],'Skill','High',['ops-linux','cloud-networking'],['Declarative state','Change review'],1040,650),
])
for role_id,title,required in [
    ('career-software-engineer','Software Engineer',['prog-python-advanced','prog-data-structures','prog-testing-cicd','prog-rest-apis','data-sql-querying']),
    ('career-frontend-developer','Frontend Developer',['web-html-css','web-typescript','web-react','prog-testing-cicd']),
    ('career-cybersecurity-analyst','Cybersecurity Analyst',['cloud-networking','ops-linux','security-threats','prog-python-advanced']),
    ('career-devops-engineer','DevOps Engineer',['ops-linux','cloud-networking','ops-iac','prog-docker-containers','prog-testing-cicd'])]:
    CAREERS.append({'id':role_id,'slug':role_id,'title':title,'category':'Engineering','description':f'Curated demo competency profile for {title}; targets are platform benchmarks, not hiring guarantees.','marketDemand':'Growing','avgSalary':'Not estimated','requirements':[(sid,80,'Required',next(s['domain'] for s in SKILLS if s['id']==sid)) for sid in required],'recommendedProjects':['proj-rag-hybrid'],'recommendedCertifications':[]})
for career in CAREERS:
    if career['id']=='career-backend-engineer': career['title']='Backend Developer'
