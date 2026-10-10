"""Live provider smoke checks. Uses synthetic context only, never real student data.
Run after setting the provider key and restarting the API. Calls consume provider quota.
"""
import asyncio
import json
from pathlib import Path
from fastapi import HTTPException
from app.services import llm

async def main():
    result={'provider':llm.provider_name(),'live':True,'checks':[]}
    questions=[('greeting','Hello'),('general','Explain Python recursion in two sentences.'),
        ('follow_up','Give one simple example.', [{'role':'user','content':'Explain SQL joins.'},{'role':'assistant','content':'Joins combine rows using related columns.'}]),
        ('grounded','What is my Python mastery? Cite the supplied source.')]
    for item in questions:
        name,prompt,*history=item
        try:
            answer=await llm.generate(prompt,history=history[0] if history else [],
                context_blocks=['Synthetic QA learner: Python mastery is 35%. [kb-qa-python] Python mastery is 35%; no verified evidence.'] if name=='grounded' else None)
            passed=bool(answer.strip()) and (name!='grounded' or ('35' in answer and '[kb-qa-python]' in answer))
            result['checks'].append({'name':name,'passed':passed,'responseCharacters':len(answer)})
        except HTTPException as exc:
            result['checks'].append({'name':name,'passed':False,'status':exc.status_code,'error':exc.detail})
            break
    result['passed']=len(result['checks'])==4 and all(c['passed'] for c in result['checks'])
    Path('mentor-provider-evaluation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result,indent=2))
    return 0 if result['passed'] else 1

if __name__=='__main__':
    raise SystemExit(asyncio.run(main()))
