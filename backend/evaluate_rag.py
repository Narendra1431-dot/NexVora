"""Retrieval evaluation against curated query/document judgments."""
import asyncio
import json
from pathlib import Path
from app.db import connect, close
from app.services.rag import retrieve
CASES=[('scaled dot product attention softmax square root','kb-attention'),('rotary position embeddings RoPE rotations','kb-rope'),('hybrid retrieval reciprocal rank fusion','kb-hybrid-rag'),('QLoRA low rank quantized fine tuning','kb-peft'),('validation leakage imbalanced calibration','kb-eval-general')]
async def main():
    await connect()
    results=[]
    for query, expected in CASES:
        passages=await retrieve(query)
        ids=[p['documentId'] for p in passages]
        rank=ids.index(expected)+1 if expected in ids else None
        results.append({'query':query,'expected':expected,'rank':rank,'retrieved':ids})
    report={'queries':len(results),'recallAt5':sum(r['rank'] is not None for r in results)/len(results),'MRR':sum(1/r['rank'] if r['rank'] else 0 for r in results)/len(results),'groundedness':'BLOCKED: live generation requires valid OpenRouter credentials','answerRelevance':'BLOCKED: generation unverified','citationCorrectness':'retrieval citations are constructed only from retrieved source metadata','results':results}
    Path('rag-evaluation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps({k:v for k,v in report.items() if k!='results'}))
    await close()
if __name__=='__main__': asyncio.run(main())
