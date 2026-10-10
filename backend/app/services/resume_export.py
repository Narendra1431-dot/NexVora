"""Plain, ATS-readable exports from the same ordered blocks as the editor."""
from io import BytesIO
from xml.sax.saxutils import escape
from zipfile import ZipFile, ZIP_DEFLATED
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from .learning_pdf import fonts

THEMES={'Modern Professional':{'color':'0F766E','size':10.5,'spacing':7},'ATS Minimal':{'color':'111827','size':11,'spacing':5},'Technical Engineer':{'color':'1E3A5F','size':10,'spacing':6}}

def lines(doc):
    result=[('Title',doc['name']),('Subtitle',('[Self-reported] ' if doc.get('headlineState')=='UNVERIFIED' else '')+doc['headline'])]
    if doc.get('contact'):result.append(('Normal',doc['contact']))
    for section in doc['sections']:
        if not section['blocks']:continue
        result.append(('Heading1',section['id'].title()))
        for b in section['blocks']:
            prefix='[Self-reported] ' if b['state']=='UNVERIFIED' else ''
            result.append(('Normal',prefix+b['text']))
    return result

def plain(doc):return '\n\n'.join(text for _,text in lines(doc) if text)

def pdf(doc):
    fonts();out=BytesIO();theme=THEMES[doc['template']]
    styles={k:ParagraphStyle(k,fontName='StudyBold' if k in ['Title','Heading1'] else 'Study',fontSize=24 if k=='Title' else 12 if k in ['Subtitle','Heading1'] else theme['size'],leading=29 if k=='Title' else 16 if k in ['Subtitle','Heading1'] else theme['size']*1.4,textColor=HexColor('#'+(theme['color'] if k=='Heading1' else '111827')),spaceBefore=10 if k=='Heading1' else 0,spaceAfter=theme['spacing'],keepWithNext=k in ['Title','Heading1']) for k in ['Title','Subtitle','Heading1','Normal']}
    story=[Paragraph(escape(text).replace('\n','<br/>'),styles[k]) for k,text in lines(doc) if text]
    SimpleDocTemplate(out,pagesize=A4,leftMargin=42,rightMargin=42,topMargin=38,bottomMargin=38,title=doc['name']+' Resume',author=doc['name']).build(story or [Spacer(1,1)])
    return out.getvalue()

def docx(doc):
    theme=THEMES[doc['template']];out=BytesIO()
    paragraphs=[]
    for style,text in lines(doc):
        if not text:continue
        runs='<w:br/>'.join('<w:t xml:space="preserve">'+escape(line)+'</w:t>' for line in text.split('\n'))
        paragraphs.append(f'<w:p><w:pPr><w:pStyle w:val="{style}"/></w:pPr><w:r>{runs}</w:r></w:p>')
    ns='http://schemas.openxmlformats.org/wordprocessingml/2006/main'
    document=f'<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="{ns}"><w:body>'+''.join(paragraphs)+'<w:sectPr><w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="760" w:right="840" w:bottom="760" w:left="840"/></w:sectPr></w:body></w:document>'
    styles=f'<w:styles xmlns:w="{ns}"><w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Arial" w:hAnsi="Arial"/><w:sz w:val="{int(theme["size"]*2)}"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="{theme["spacing"]*20}" w:line="336" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>'
    for name,size in [('Normal',int(theme['size']*2)),('Title',48),('Subtitle',24),('Heading1',24)]:
        styles+=f'<w:style w:type="paragraph" w:styleId="{name}"><w:name w:val="{name}"/><w:pPr>'+('<w:keepNext/>' if name in ['Title','Heading1'] else '')+'</w:pPr><w:rPr>'+('<w:b/>' if name in ['Title','Heading1'] else '')+f'<w:sz w:val="{size}"/><w:color w:val="{theme["color"] if name=="Heading1" else "111827"}"/></w:rPr></w:style>'
    styles+='</w:styles>'
    with ZipFile(out,'w',ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/><Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/></Types>')
        z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>')
        z.writestr('word/_rels/document.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        z.writestr('word/document.xml',document);z.writestr('word/styles.xml',styles)
    return out.getvalue()
