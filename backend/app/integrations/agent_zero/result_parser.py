import json
from fastapi import HTTPException
from .schemas import ResearchResult
from ...runtime.redaction import redact

def parse_result(raw,expected_url):
    try:result=ResearchResult.model_validate(json.loads(raw))
    except (ValueError,TypeError):raise HTTPException(502,'Agent Zero returned an invalid structured result.')
    if result.sourceUrl!=expected_url or redact(result.model_dump())!=result.model_dump():
        raise HTTPException(502,'Agent Zero result failed source or privacy validation.')
    return result
