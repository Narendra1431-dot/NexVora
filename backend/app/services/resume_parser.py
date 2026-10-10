"""Conservative section extraction from resume headings, without generated text."""
import re

HEADINGS={'summary':'summary','profile':'summary','education':'education','work experience':'experience','professional experience':'experience','experience':'experience','employment':'experience','projects':'projects','technical skills':'skills','skills':'skills','certifications':'certifications','certificates':'certifications','achievements':'achievements','publications':'publications','certifications & achievements':'certifications','career objective & self-reported skills':'summary','career objective':'summary'}
PATTERN=re.compile(r'^('+'|'.join(map(re.escape,sorted(HEADINGS,key=len,reverse=True)))+r')(?:\s*:\s*(.*)|\s*)$',re.I)

def extract_sections(text):
    sections=[]
    current={'name':'unclassified','lines':[]}
    for line in text.splitlines():
        match=PATTERN.match(line.strip().lstrip('#').strip().strip('*').strip())
        if match:
            if current['lines']: sections.append(current)
            current={'name':HEADINGS[match[1].lower()],'lines':[match[2]] if match[2] else []}
        elif line.strip(): current['lines'].append(line.strip())
    if current['lines']: sections.append(current)
    return [{'name':item['name'],'text':'\n'.join(item['lines'])} for item in sections]
