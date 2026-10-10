import json
import re
from ..agents.state import snapshot
from ..providers.router import structured
from ..providers.base import ProviderError
from ..rag.retrieval import retrieve
from ..db import col
from ..security import iso_now,new_id
from .schemas import Advisory
from .prompts import SYSTEM

def validate_citations(answer,passages,evidence):
    sources={p['id']:p for p in passages}
    if set(answer.evidenceRefs)-{e['id'] for e in evidence}:
        raise ProviderError('invalid_evidence_reference',answer.__class__.__name__)
    for citation in answer.citations:
        source=sources.get(citation.chunkId)
        if not source or citation.quote not in source['text']:
            raise ProviderError('invalid_citation_quote',answer.__class__.__name__)
    # Models cannot introduce external links; UI only renders server source metadata.
    if re.search(r'https?://',answer.summary+' '.join(answer.recommendations)):
        raise ProviderError('unvalidated_link',answer.__class__.__name__)

async def query(student_id,question,document_ids=(),*,background=False,require_sources=False,job_id=None):
    s=await snapshot(student_id)
    passages=await retrieve(student_id,question,document_ids)
    facts={'readiness':s.readiness,'mastery':s.mastery,'confidence':s.confidence,'careerGaps':s.careerGaps,
           'xp':s.xp,'rank':s.rank,'stateVersion':s.stateVersion}
    if require_sources and not passages:
        return {'answer':{'intent':'insufficient_evidence','summary':'Insufficient grounded evidence in your indexed material. Upload a relevant document or narrow your question.','recommendations':[],'evidenceRefs':[],'citations':[],'confidence':0},
                'sources':[],'facts':facts,'abstained':True,'stateVersion':s.stateVersion}
    # Bounded projection, not a byte slice of serialized canonical state. Source
    # excerpts and IDs always remain intact for verifiable citations.
    projection={'profile':s.profile,'targetCareer':s.targetCareer.get('title'),'readiness':s.readiness,
        'stateVersion':s.stateVersion,'xp':s.xp,'rank':s.rank,
        'skills':[{k:n.get(k) for k in ('id','name','mastery','confidence','state','targetLevel','prerequisites')} for n in s.competencies],
        'evidence':[{k:e.get(k) for k in ('id','title','skillId','verificationState','type')} for e in s.evidence[:40]],
        'roadmap':[{k:m.get(k) for k in ('id','title','status','skillId')} for m in s.roadmap[:12]],
        'nextAction':s.recommendations,
        'resources':[{k:r.get(k) for k in ('id','title','skillId','difficulty')} for r in s.resources[:8]]}
    if require_sources:
        # A source question needs its passages and learning objective, not the
        # entire profile/evidence catalog. Reduce provider token pressure and
        # unnecessary student-data disclosure without trimming source quotes.
        projection={k:projection[k] for k in ('targetCareer','readiness','stateVersion')}
        projection['nextAction']={k:s.recommendations.get(k) for k in ('title','reason','skillId')}
    context=json.dumps({'question':question,'state':projection,
        'sources':[{k:p.get(k) for k in ('id','text','documentId','source','page','section','trust')} for p in passages]},default=str)
    supplied_evidence=projection.get('evidence',[])
    instruction=SYSTEM+'\nEvidence references and document citations are separate. evidenceRefs may contain ONLY IDs from state.evidence; when state.evidence is absent or empty, evidenceRefs MUST be []. Source chunk/document IDs belong only in citations, never evidenceRefs.'
    if not passages:
        instruction+='\nThere are NO retrieved sources. citations MUST be an empty array [].'
    for repair in range(2):
        data,result,attempts=await structured(instruction,Advisory,context,background=background)
        try:
            validate_citations(data,passages,supplied_evidence)
            if require_sources and not data.citations:raise ProviderError('missing_grounded_citations','validator')
            break
        except ProviderError as exc:
            if repair:raise
            instruction+='\nRepair failed provenance validation ('+exc.code+'). For citations, use source chunk IDs and copy quotes exactly. For evidenceRefs, use only state.evidence IDs; if none were supplied, return []. If sources is empty, citations must be []. Do not cite state keys as documents.'
    used={c.chunkId for c in data.citations}
    sources=[{k:p.get(k) for k in ('id','documentId','source','page','section','title','trust')} for p in passages if p['id'] in used]
    trace={'requestId':new_id('brain'),'jobId':job_id,'studentId':student_id,'provider':result.provider,'model':result.model,
        'latency':result.latency,'tokens':result.tokens,'retrievedDocumentIds':list({p['documentId'] for p in passages}),
        'stateVersion':s.stateVersion,'status':'Completed','createdAt':iso_now(),'fallbackAttempts':attempts}
    await col('intelligence_traces').insert_one(trace)
    return {'answer':data.model_dump(),'sources':sources,'facts':facts,'stateVersion':s.stateVersion,
        'provider':result.provider,'model':result.model,'fallbackUsed':bool(attempts),'advisoryOnly':True,'abstained':False}
