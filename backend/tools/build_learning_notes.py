"""Author versioned original study chapters; never runs in a student request."""
import asyncio, json, sys, os
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from app.seed.catalog import SKILLS
from app.config import settings
from app.services.learning_content import valid_chapter
from datetime import datetime, timezone
import httpx

async def generate(prompt, **kwargs):
    string={"type":"string"}
    def obj(properties): return {"type":"object","properties":properties,"required":list(properties),"additionalProperties":False}
    def arr(item): return {"type":"array","items":item}
    qa=obj({"question":string,"answer":string})
    schema=obj({"introduction":string,"foundations":string,"concepts":arr(obj({"title":string,"explanation":string,"example":string})),"examples":arr(obj({"title":string,"code":string,"explanation":string})),"flow":arr(string),"interview":arr(qa),"summary":string,"practice":arr(qa)})
    competency=json.loads(prompt.split('Competency: ')[-1])
    schema['properties']['concepts']['items']['properties']['title']={'type':'string','enum':competency['relatedConcepts']}
    async with httpx.AsyncClient(timeout=120) as client:
        model=os.environ.get('LEARNING_AUTHOR_MODEL',settings.groq_model)
        payload={"model":model,"messages":[{"role":"user","content":prompt}],"max_completion_tokens":12000,"temperature":.1}
        if model.startswith('openai/gpt-oss'):
            payload.update(reasoning_effort='low',response_format={"type":"json_schema","json_schema":{"name":"learning_chapter","strict":True,"schema":schema}})
        else:payload['response_format']={"type":"json_schema","json_schema":{"name":"learning_chapter","strict":True,"schema":schema}}
        response=await client.post("https://api.groq.com/openai/v1/chat/completions", headers={"Authorization":"Bearer "+settings.groq_api_key},json=payload)
        if response.status_code!=200:
            error=response.json().get('error',{})
            if error.get('code')=='json_validate_failed' and error.get('failed_generation'):
                raw=error['failed_generation']
                # Some providers reject nonessential envelope formatting. The
                # same local validation still gates every recovered chapter.
                try:return json.dumps(json.loads(raw[raw.index('{'):raw.rindex('}')+1]))
                except (ValueError,TypeError):pass
            raise ValueError("Provider HTTP "+str(response.status_code)+' '+str(error.get('code','')))
        result=response.json()["choices"][0]
        if result["finish_reason"]=="length":raise ValueError("Response truncated")
        return result["message"]["content"]

DEST=Path(__file__).resolve().parents[1]/'app'/'assets'/'learning'
PROMPT='''Write an original, self-contained educational chapter in English for the following competency. Do not copy a book, invent citations, URLs, evidence or mastery scores. Explain stable concepts rather than version-specific release claims. This is study material, not a summary or study plan. Teach a beginner the foundations before progressing to advanced material. Cover EVERY named subtopic in depth; add the basic concepts necessary to understand them. Include clear derivations, concrete worked examples, pitfalls, interview preparation and practice solutions. Use plain text and ASCII notation for formulas, no Markdown/LaTeX. Do not invent approximate matrix decompositions. Use diagonal matrices or exact integer examples for numerical solutions; check every numerical answer. Label squared approximation error versus norm error correctly. All Python examples must be syntactically valid and include necessary imports; label pseudocode explicitly. No shell commands that delete files or cloud provisioning commands. Return ONLY a valid JSON object with this schema:
{"introduction":"150-200 words explaining why/how/when", "foundations":"250-350 words of concrete teaching, not an outline", "concepts":[{"title":"exact subtopic name","explanation":"150-220 words of detailed explanation and tradeoffs","example":"concrete numerical/worked example of 80+ words"}], "examples":[{"title":"Worked example","code":"short runnable code or ASCII formula computation, max 18 lines, max 76 characters/line","explanation":"120+ words interpreting output and limitations"},{"title":"Applied example","code":"short code or pseudocode/formulas","explanation":"120+ words"}], "flow":["5-7 specific sequential processing steps with explanations"], "interview":[{"question":"...","answer":"substantive 50+ word answer"}], "summary":"100+ words synthesizing key principles", "practice":[{"question":"a solvable concrete question with given data","answer":"worked solution, not generic advice"}]}
At least 4 interview questions and 6 practice questions (including 2 numerical/code exercises and 1 design tradeoff). At least 1700 words overall. No placeholder/generic repeated text. Keep mathematical identities correct, include assumptions and use realistic small inputs. Every concept must be represented exactly once.
Competency: '''

async def main():
    DEST.mkdir(parents=True,exist_ok=True)
    for skill in SKILLS:
        path=DEST/(skill['id']+'.json')
        if path.exists(): continue
        for attempt in range(4):
            try:
                answer=await generate(PROMPT+json.dumps({k:skill[k] for k in ('name','relatedConcepts','prerequisites')}), max_tokens=7200, temperature=.15)
                doc=json.loads(answer[answer.index('{'):answer.rindex('}')+1])
                (DEST/(skill['id']+'.draft')).write_text(json.dumps(doc,indent=2),encoding='utf-8')
                names={name.casefold():name for name in skill['relatedConcepts']}
                for concept in doc['concepts']:
                    concept['title']=names.get(concept['title'].casefold(),concept['title'])
                assert set(skill['relatedConcepts'])<={c['title'] for c in doc['concepts']}
                assert all(key in doc for key in ('introduction','foundations','examples','flow','interview','summary','practice'))
                assert len(doc['examples'])>=2 and len(doc['practice'])>=6 and len(doc['interview'])>=4
                words=len(json.dumps(doc).split());assert words>=1300,words
                doc.update(id=skill['id'],title=skill['name'],version='learning-v1',source='CareerIQ original AI-assisted educational notes',generatedAt=datetime.now(timezone.utc).date().isoformat(),wordCount=words)
                assert valid_chapter(doc,skill['relatedConcepts']), 'Incomplete chapter structure'
                path.write_text(json.dumps(doc,ensure_ascii=False,indent=2),encoding='utf-8')
                print(skill['id'],words,'words saved',flush=True);break
            except Exception as exc:
                print(skill['id'],'attempt',attempt+1,type(exc).__name__,str(getattr(exc,'detail',str(exc)))[:180],flush=True)
                await asyncio.sleep(35)
        else: print('UNAVAILABLE',skill['id'],flush=True)
        await asyncio.sleep(6)

if __name__=='__main__':asyncio.run(main())



