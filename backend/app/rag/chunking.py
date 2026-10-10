import re
from hashlib import sha256
from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunks(pages, document):
    splitter=RecursiveCharacterTextSplitter(chunk_size=1200,chunk_overlap=160,
        separators=['\n\n','\n','. ',' ',''])
    result=[]
    for page in pages:
        text=re.sub(r'[ \t]+',' ',page['text']).replace('\x00','').strip()
        section=page.get('section') or next((s.strip()[:120] for s in text.splitlines() if s.strip()),'Body')
        for i,part in enumerate(splitter.split_text(text)):
            if len(part.strip())<20:continue
            key=sha256((document['id']+':'+str(page['page'])+':'+str(i)+':'+part).encode()).hexdigest()[:32]
            result.append({'id':'chunk-'+key,'documentId':document['id'],'studentId':document['studentId'],
                'source':document['fileName'],'title':document.get('title') or document['fileName'],
                'documentType':document['documentType'],'page':page['page'],'section':section,
                'chapter':page.get('chapter',''),'topic':document.get('subject',''),
                'text':part,'timestamp':document['createdAt'],'trust':'user-provided'})
    return result
