from typing import Literal
from pydantic import Field
from ..agents.models import StrictModel

class AssistantInput(StrictModel):
    message: str = Field(min_length=1,max_length=3000)
    requestId: str = Field(min_length=8,max_length=90)
    research: bool = False

class Plan(StrictModel):
    mode: Literal['project','general','external','mixed']
    topics: list[Literal['artificial intelligence','machine learning','data science','software development','Python','JavaScript','React','FastAPI','Docker','Kubernetes','cloud computing','AWS','Azure','Google Cloud','RAG','large language models','transformers','SQL','cybersecurity','MLOps','GitHub','Rasa','OpenAI','Llama','Anthropic']] = Field(default_factory=list,max_length=3)
    deep: bool = False

class Citation(StrictModel):
    sourceId: str
    quote: str = Field(max_length=500)

class Reply(StrictModel):
    answer: str = Field(min_length=1,max_length=12000)
    citations: list[Citation] = Field(default_factory=list,max_length=12)
    limitations: list[str] = Field(default_factory=list,max_length=8)
