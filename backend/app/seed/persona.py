"""The seeded demo persona: Alex Rivera, targeting AI Engineer.

Baseline is intentionally *interesting* rather than flattering:

* verified maths, Python, SQL and supervised ML from transcripts and repos,
* PyTorch only **estimated** from a resume claim,
* a RAG claim that is **unverified**,
* Transformer, fine-tuning and serving skills as genuine gaps,
* locked downstream milestones until prerequisites clear.

Every mastery number the UI shows is computed from the evidence below by the
competency engine — nothing is hard-coded into the state.
"""

from __future__ import annotations

from typing import Any

PROFILE: dict[str, Any] = {
    "name": "Alex Rivera",
    "email": "alex.rivera@cs.university.edu",
    "headline": "Aspiring AI & Machine Learning Systems Engineer",
    "bio": "CS junior with strong mathematical fundamentals and backend skills, transitioning into production deep learning and LLM engineering.",
    "location": "San Francisco, CA",
    "degree": "B.S. in Computer Science",
    "institution": "University of California, Berkeley",
    "gradYear": "2026",
    "gpa": "3.82",
    "githubHandle": "alexrivera-dev",
    "githubConnected": True,
    "learningPreferences": ["Code-First Hands On", "Deep Theory Explanations", "Project Based"],
    "weeklyAvailabilityHours": 15,
    "streakDays": 14,
    "targetCareerId": "career-ai-engineer",
    "onboardingCompleted": False,
}

DEMO_EMAIL = "alex.rivera@cs.university.edu"

RESUME_TEXT = """ALEX RIVERA
Aspiring AI & Machine Learning Systems Engineer
alex.rivera@cs.university.edu | github.com/alexrivera-dev | San Francisco, CA

EDUCATION
B.S. in Computer Science, University of California, Berkeley (2026), GPA 3.82
Relevant coursework: Demo ML Course Machine Learning, CS 188 Artificial Intelligence, CS 61B Data Structures

EXPERIENCE
Machine Learning Intern, ScaleAI Lab (Summer 2025)
- Built multimodal data ingestion pipelines processing 2.4M daily samples
- Benchmarked PyTorch training throughput and maintained feature store transformations

PROJECTS
- Trained and deployed PyTorch vision models for internal document classification
- Implemented a RAG pipeline for documentation search using ChromaDB and LangChain

SKILLS
Python, PyTorch, Pandas, NumPy, SQL, Docker, scikit-learn, Linear Algebra, Statistics
Experience with Transformer self-attention architectures and deployed LLMs with low latency
"""

# --------------------------------------------------------------------------
# Evidence: the ONLY source of baseline mastery.
# --------------------------------------------------------------------------
EVIDENCE: list[dict[str, Any]] = [
    {
        "id": "ev-001",
        "title": "Demo ML Course: Introduction to Machine Learning - Final Grade A",
        "type": "Course Record",
        "skillId": "ml-supervised",
        "skillName": "Supervised Learning Algorithms",
        "verificationState": "Verified",
        "quality": "High",
        "confidenceScore": 95,
        "date": "2025-12-18",
        "source": "UC Berkeley Registrar Transcript",
        "provenance": "Official academic transcript via Parchment with verified digital signature.",
        "url": "https://credentials.berkeley.edu/verify/cs189-alexrivera",
        "summary": "Mastered empirical risk minimisation, SVMs, tree ensembles and regularisation with a 94.2% course score.",
    },
    {
        "id": "ev-002",
        "title": "Advanced Python Decorators & AsyncIO Microbenchmark",
        "type": "GitHub Artifact",
        "skillId": "prog-python-advanced",
        "skillName": "Python (Advanced)",
        "verificationState": "Verified",
        "quality": "High",
        "confidenceScore": 92,
        "date": "2026-02-14",
        "source": "github.com/alexrivera-dev/py-async-bench",
        "provenance": "Public repository, 42 stars, CI lint and test suite passing on every commit.",
        "url": "https://github.com/alexrivera-dev/py-async-bench",
        "summary": "Concurrent network request handlers, custom memory pool and typed protocol interfaces.",
    },
    {
        "id": "ev-003",
        "title": "Linear Algebra & SVD Diagnostic Assessment",
        "type": "Assessment",
        "skillId": "math-linear-algebra",
        "skillName": "Linear Algebra",
        "verificationState": "Verified",
        "quality": "High",
        "confidenceScore": 96,
        "date": "2026-03-12",
        "source": "Platform Diagnostic Engine",
        "provenance": "Adaptive multi-question evaluation, 92% accuracy, no anomaly flags.",
        "summary": "Strong intuition for projection matrices, singular value decomposition and orthogonal bases.",
    },
    {
        "id": "ev-004",
        "title": 'Resume claim: "Trained and deployed PyTorch vision models"',
        "type": "Resume Claim",
        "skillId": "dl-pytorch",
        "skillName": "PyTorch Framework & Tensors",
        "verificationState": "Estimated",
        "quality": "Medium",
        "confidenceScore": 68,
        "date": "2026-03-01",
        "source": "Uploaded resume: Alex_Rivera_Resume_2026.pdf",
        "provenance": "Extracted from the Projects section. No verifiable commit history attached.",
        "summary": "Suggests torchvision familiarity, but no proof of custom training loops or distributed training.",
    },
    {
        "id": "ev-005",
        "title": 'Resume claim: "Implemented a RAG pipeline using ChromaDB"',
        "type": "Resume Claim",
        "skillId": "dl-rag-systems",
        "skillName": "Retrieval Augmented Generation (RAG)",
        "verificationState": "Needs Review",
        "quality": "Medium",
        "confidenceScore": 62,
        "date": "2026-03-01",
        "source": "Uploaded resume: Alex_Rivera_Resume_2026.pdf",
        "provenance": "Self-reported text. Requires repository verification or a passing rubric evaluation.",
        "summary": "Claims a retrieval project with ChromaDB. No evaluation metrics or re-ranking evidence supplied.",
    },
    {
        "id": "ev-006",
        "title": "LeetCode 250+ Solved Algorithmic Problems",
        "type": "Coding Challenge",
        "skillId": "prog-data-structures",
        "skillName": "Data Structures & Algorithms",
        "verificationState": "Verified",
        "quality": "High",
        "confidenceScore": 90,
        "date": "2026-02-28",
        "source": "LeetCode profile API",
        "provenance": "Authenticated OAuth verification of submitted solutions.",
        "summary": "Top 8% globally across dynamic programming, graph search and tree traversal categories.",
    },
    {
        "id": "ev-007",
        "title": "Dockerizing FastAPI Microservices Certificate",
        "type": "Certificate",
        "skillId": "prog-docker-containers",
        "skillName": "Docker & Containerization",
        "verificationState": "Verified",
        "quality": "Medium",
        "confidenceScore": 78,
        "date": "2026-01-20",
        "source": "Coursera / DeepLearning.AI",
        "provenance": "Digital certificate DLAI-99412-DOCKER, verification page reachable.",
        "url": "https://coursera.org/verify/DLAI-99412",
        "summary": "Multi-stage image builds, secret injection and compose networking for CPU workloads only.",
    },
    {
        "id": "ev-008",
        "title": "CS 61B Data Structures Transcript Record",
        "type": "Course Record",
        "skillId": "data-sql-querying",
        "skillName": "Advanced SQL & Data Modeling",
        "verificationState": "Verified",
        "quality": "Medium",
        "confidenceScore": 80,
        "date": "2025-05-22",
        "source": "UC Berkeley Registrar Transcript",
        "provenance": "Official transcript entry covering relational modelling and query planning coursework.",
        "summary": "Covered relational algebra, indexing strategies and query optimisation as part of the database module.",
    },
    {
        "id": "ev-009",
        "title": "Probability & Statistics Coursework Record",
        "type": "Course Record",
        "skillId": "math-prob-stats",
        "skillName": "Probability & Statistics",
        "verificationState": "Verified",
        "quality": "High",
        "confidenceScore": 88,
        "date": "2025-12-20",
        "source": "UC Berkeley Registrar Transcript",
        "provenance": "Official transcript entry for the probability and inference sequence.",
        "summary": "Covered maximum likelihood estimation, hypothesis testing and Bayesian inference fundamentals.",
    },
    {
        "id": "ev-010",
        "title": "Multivariate Calculus & Optimisation Record",
        "type": "Course Record",
        "skillId": "math-multivariate-calculus",
        "skillName": "Multivariate Calculus",
        "verificationState": "Verified",
        "quality": "Medium",
        "confidenceScore": 84,
        "date": "2025-05-18",
        "source": "UC Berkeley Registrar Transcript",
        "provenance": "Official transcript entry covering gradients, Jacobians and optimisation.",
        "summary": "Strong command of partial derivatives and the chain rule as applied to backpropagation.",
    },
    {
        "id": "ev-011",
        "title": "Data Wrangling Notebook Portfolio",
        "type": "GitHub Artifact",
        "skillId": "data-numpy-pandas",
        "skillName": "NumPy & Pandas Processing",
        "verificationState": "Verified",
        "quality": "High",
        "confidenceScore": 90,
        "date": "2026-01-30",
        "source": "github.com/alexrivera-dev/data-wrangling",
        "provenance": "Repository with vectorised transformation benchmarks and CI-checked notebooks.",
        "url": "https://github.com/alexrivera-dev/data-wrangling",
        "summary": "High-throughput vectorised pipelines, memory-mapped reads and time-series alignment.",
    },
    {
        "id": "ev-012",
        "title": "Deep Learning Specialisation Module Certificate",
        "type": "Certificate",
        "skillId": "dl-neural-networks",
        "skillName": "Neural Network Architecture",
        "verificationState": "Verified",
        "quality": "Medium",
        "confidenceScore": 80,
        "date": "2026-01-08",
        "source": "DeepLearning.AI",
        "provenance": "Certificate with graded programming assignments on backpropagation and regularisation.",
        "summary": "Covered network architecture choices, normalisation and activation design.",
    },
    {
        "id": "ev-013",
        "title": "Model Validation Capstone Record",
        "type": "Course Record",
        "skillId": "ml-model-evaluation",
        "skillName": "Model Evaluation & Validation",
        "verificationState": "Verified",
        "quality": "Medium",
        "confidenceScore": 82,
        "date": "2025-12-19",
        "source": "Demo ML Course Capstone",
        "provenance": "Graded capstone submission with cross-validated evaluation protocol.",
        "summary": "Precision-recall analysis, leakage detection and calibration on imbalanced datasets.",
    },
    {
        "id": "ev-014",
        "title": "Vector Indexing Reading Notes",
        "type": "Manual Claim",
        "skillId": "data-vector-databases",
        "skillName": "Vector DBs & Embeddings Index",
        "verificationState": "Unverified",
        "quality": "Low",
        "confidenceScore": 40,
        "date": "2026-02-10",
        "source": "Self-reported study log",
        "provenance": "Student-declared reading with no artefact attached.",
        "summary": "Read up on HNSW and IVF indexing, but no implementation or benchmark exists yet.",
    },
]

# Areas the student has explicitly started but not yet proven.
IN_PROGRESS_SKILLS: list[str] = ["dl-pytorch", "dl-transformers", "ml-unsupervised"]

ACTIVITIES: list[dict[str, Any]] = [
    {
        "id": "act-seed-1",
        "type": "Evidence Verified",
        "title": "Transcript verified for Demo ML Course",
        "description": "Academic record processed; supervised learning moved to verified mastery.",
        "timestamp": "",
        "delta": "Verified",
        "linkTab": "profile",
    },
    {
        "id": "act-seed-2",
        "type": "Assessment Completed",
        "title": "Linear algebra baseline diagnostic",
        "description": "Diagnostic completed at 92% accuracy; linear algebra confirmed as verified.",
        "timestamp": "",
        "delta": "91% accuracy",
        "linkTab": "assessments",
    },
    {
        "id": "act-seed-3",
        "type": "Career Target Changed",
        "title": "Target career set to AI Engineer",
        "description": "Gap analysis and roadmap generation aligned to the AI Engineer requirement set.",
        "timestamp": "",
        "linkTab": "careers",
    },
    {
        "id": "act-seed-4",
        "type": "Project Recommended",
        "title": "Hybrid RAG capstone recommended",
        "description": "Recommended to resolve the unsupported RAG resume claim with rubric-verified proof.",
        "timestamp": "",
        "linkTab": "projects",
    },
]

NOTIFICATIONS: list[dict[str, Any]] = [
    {
        "id": "notif-seed-1",
        "title": "Assessment recommendation",
        "message": "The adaptive PyTorch assessment is available and unblocks your Transformer milestone.",
        "type": "assessment",
        "timestamp": "",
        "read": False,
        "linkTab": "assessments",
    },
    {
        "id": "notif-seed-2",
        "title": "Critical gap identified",
        "message": "Transformer architecture is a required AI Engineer competency and currently sits below its target.",
        "type": "roadmap",
        "timestamp": "",
        "read": False,
        "linkTab": "competencies",
    },
    {
        "id": "notif-seed-3",
        "title": "Evidence pending verification",
        "message": "The RAG resume claim is awaiting a repository or rubric-verified project.",
        "type": "verification",
        "timestamp": "",
        "read": True,
        "linkTab": "resume",
    },
    {
        "id": "notif-seed-4",
        "title": "Competency model synchronised",
        "message": "Skill states were refreshed from the evidence vault by the deterministic engine.",
        "type": "system",
        "timestamp": "",
        "read": True,
        "linkTab": "dashboard",
    },
]
