from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

JobType=Literal['agent_workflow','resume_analysis','document_ingestion','embedding_generation','rag_index_update',
    'career_gap_explanation','roadmap_generation','resource_enrichment','assessment_generation',
    'project_recommendation','resume_generation','certificate_description','student_intelligence_refresh']

class Strict(BaseModel):
    model_config=ConfigDict(extra='forbid')

class Citation(Strict):
    chunkId:str=Field(max_length=120)
    quote:str=Field(min_length=5,max_length=700)

class Advisory(Strict):
    intent:str=Field(max_length=80)
    summary:str=Field(min_length=1,max_length=5000)
    recommendations:list[str]=Field(default_factory=list,max_length=12)
    evidenceRefs:list[str]=Field(default_factory=list,max_length=30)
    citations:list[Citation]=Field(default_factory=list,max_length=12)
    confidence:float=Field(ge=0,le=1)

class Query(Strict):
    question:str=Field(min_length=3,max_length=4000)
    documentIds:list[str]=Field(default_factory=list,max_length=10)

class JobRequest(Strict):
    type:JobType
    inputRefs:list[str]=Field(default_factory=list,max_length=10)
    requestId:str=Field(min_length=8,max_length=100)

class ExtractedClaim(Strict):
    text:str=Field(min_length=1,max_length=600)
    quote:str=Field(min_length=5,max_length=600)
    skillId:str=Field(max_length=100)

class ResumeExtraction(Strict):
    summary:str=Field(max_length=1800)
    claims:list[ExtractedClaim]=Field(default_factory=list,max_length=60)
    projects:list[str]=Field(default_factory=list,max_length=30)
