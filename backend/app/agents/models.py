"""Public contracts. A caller can never select another student or supply scores."""
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

class StrictModel(BaseModel):
    model_config = ConfigDict(extra='forbid')

class CanonicalState(StrictModel):
    concepts: list[dict[str, Any]] = Field(default_factory=list)
    codingProgress: list[dict[str, Any]] = Field(default_factory=list)
    xp: int = 0
    rank: int = 0
    studentId: str
    stateVersion: int
    profile: dict[str, Any]
    targetCareer: dict[str, Any]
    competencies: list[dict[str, Any]]
    mastery: dict[str, int | float]
    confidence: dict[str, int | float]
    evidence: list[dict[str, Any]]
    careerGaps: list[dict[str, Any]]
    readiness: int | float
    roadmap: list[dict[str, Any]]
    resources: list[dict[str, Any]]
    assessments: list[dict[str, Any]]
    assessmentHistory: list[dict[str, Any]]
    projects: list[dict[str, Any]]
    resume: dict[str, Any]
    certificates: list[dict[str, Any]]
    recommendations: dict[str, Any]
    events: list[dict[str, Any]]
    analytics: dict[str, Any]

ToolName = Literal['getStudentProfile','getCompetencies','getEvidence','calculateCareerGap','calculateReadiness','getRoadmap','searchResources','retrieveRAG','getAssessments','recommendProject','analyzeResume','checkCertificateEligibility','getAnalytics','getCodingProgress','getRank']

class ToolInput(StrictModel):
    name: ToolName
    query: str = Field(default='', max_length=8000)
    skillId: str | None = Field(default=None,max_length=100)
    courseId: str | None = Field(default=None,max_length=100)

class ToolOutput(StrictModel):
    name: ToolName
    stateVersion: int
    data: dict[str, Any] | list[dict[str, Any]]

class HistoryEntry(StrictModel):
    role: Literal['user','assistant']
    content: str = Field(max_length=8000)

class ChatInput(StrictModel):
    message: str = Field(min_length=1,max_length=8000)
    history: list[HistoryEntry] = Field(default_factory=list,max_length=20)
    requestId: str = Field(min_length=8,max_length=100)

class ExecuteInput(StrictModel):
    action: Literal['recomputeRoadmap','startAssessment','evaluateAssessment','analyzeResume','planWeek']
    requestId: str = Field(min_length=8,max_length=100)
    expectedStateVersion: int = Field(ge=0)
    skillId: str | None = Field(default=None,max_length=100)
    attemptId: str | None = Field(default=None,max_length=100)
    assessmentId: str | None = Field(default=None,max_length=100)
    answers: dict[str, Any] | None = Field(default=None,max_length=100)
    resumeText: str | None = Field(default=None,max_length=50000)

def safe(value):
    if isinstance(value,list):return [safe(v) for v in value]
    if isinstance(value,dict):return {k:safe(v) for k,v in value.items() if k not in {'_id','passwordHash','correctAnswers','correct','studentId','email','answers','pdf','proof','rawText','avatar'}}
    return value
