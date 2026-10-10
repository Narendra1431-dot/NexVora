from pydantic import Field
from ...agents.models import StrictModel

class ResearchTask(StrictModel):
    url:str=Field(min_length=12,max_length=1500)

class ResearchResult(StrictModel):
    title:str=Field(min_length=1,max_length=200)
    summary:str=Field(min_length=1,max_length=3000)
    sourceUrl:str=Field(max_length=1500)
    available:bool

class MessageResult(StrictModel):
    context_id:str=Field(min_length=1,max_length=128)
    response:str=Field(max_length=20000)
