"""Unicode, paginated study books assembled from the same chapters as the reader."""
from io import BytesIO
from pathlib import Path
import re, textwrap
from xml.sax.saxutils import escape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Preformatted, Table, TableStyle
from reportlab.platypus.tableofcontents import TableOfContents

def fonts():
    if 'Study' in pdfmetrics.getRegisteredFontNames(): return
    # Windows development and common Linux deployment paths.
    candidates=[('C:/Windows/Fonts/arial.ttf','C:/Windows/Fonts/arialbd.ttf','C:/Windows/Fonts/consola.ttf'),
      ('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf','/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf')]
    for normal,bold,mono in candidates:
        if all(Path(p).exists() for p in (normal,bold,mono)):
            for name,path in [('Study',normal),('StudyBold',bold),('StudyMono',mono)]:pdfmetrics.registerFont(TTFont(name,path))
            return
    raise RuntimeError('Install Arial or DejaVu Sans fonts for learning PDFs.')

def clean(value):
    return str(value).replace('\u2011','-').replace('\u2013','-').replace('\u2014',' - ').replace('\u2212','-').replace('\u00a0',' ')

class StudyBook(SimpleDocTemplate):
    def afterFlowable(self,flowable):
        if isinstance(flowable,Paragraph) and flowable.style.name=='Chapter':
            key='chapter-'+str(self.page)
            self.canv.bookmarkPage(key);self.canv.addOutlineEntry(flowable.getPlainText(),key,0)
            self.notify('TOCEntry',(0,flowable.getPlainText(),self.page,key))

def render_book(title,chapters,scope):
    fonts();out=BytesIO();styles=getSampleStyleSheet()
    styles.add(ParagraphStyle('StudyBody',fontName='Study',fontSize=10,leading=15,spaceAfter=9,textColor=colors.HexColor('#25334a')))
    styles.add(ParagraphStyle('Chapter',fontName='StudyBold',fontSize=21,leading=27,spaceAfter=16,textColor=colors.HexColor('#0c3442'),keepWithNext=True))
    styles.add(ParagraphStyle('Cover',parent=styles['Chapter']))
    styles.add(ParagraphStyle('Section',fontName='StudyBold',fontSize=13,leading=18,spaceBefore=14,spaceAfter=8,textColor=colors.HexColor('#087a7b'),keepWithNext=True))
    styles.add(ParagraphStyle('StudyCode',fontName='StudyMono',fontSize=8,leading=11,backColor=colors.HexColor('#f3f6f8'),borderPadding=8,spaceBefore=6,spaceAfter=12))
    styles.add(ParagraphStyle('SmallStudy',parent=styles['StudyBody'],fontSize=8,leading=12))
    story=[]
    def p(text,style='StudyBody'):
        lines=escape(clean(text)).split('\n')
        lines=[re.sub(r'^ +',lambda match:'&#160;'*len(match.group()),line) for line in lines]
        return Paragraph('<br/>'.join(lines),styles[style])
    def paragraph(text,style='StudyBody'):
        for part in re.split(r'\n\s*\n',str(text)):story.append(p(part,style))
    def heading(text):story.append(p(text,'Section'))
    story.extend([Spacer(1,64),p('CAREERIQ / TARGET OBJECTIVE LEARNING HUB','SmallStudy'),Spacer(1,28),p(title,'Cover'),p('Complete Learning Notes','Cover'),Spacer(1,20),p(f'{len(chapters)} topics | Foundations, worked examples and practice solutions'),p('Scope: '+scope),Spacer(1,24),p('Use this book in prerequisite order. Start with Foundations if a topic is new, then work through the detailed concepts and examples. Experienced learners can focus on tradeoffs, interview questions and applied practice.'),p('These are original AI-assisted study notes, not an accredited textbook or evidence of mastery. Validate software examples against the linked primary documentation and complete the existing assessments or reviewed projects.'),p('Reference books are listed by title and author only. No third-party textbook PDFs are included.'),PageBreak()])
    heading('Contents')
    toc=TableOfContents();toc.levelStyles=[ParagraphStyle('TOCStudy',fontName='Study',fontSize=10,leading=15,spaceBefore=5)]
    story.extend([toc,PageBreak()])
    for index,chapter in enumerate(chapters):
        notes=chapter['notes']
        story.append(p(f"{index+1}. {chapter['name']}",'Chapter'))
        paragraph('Prerequisites: '+(', '.join(chapter['prerequisiteNames']) or 'No prerequisites in the current competency catalog.'),'SmallStudy')
        paragraph(notes['introduction']);heading('Foundations');paragraph(notes['foundations'])
        for concept in notes['concepts']:
            heading(concept['title']);paragraph(concept['explanation']);paragraph('Worked reasoning: '+concept['example'])
        heading('Worked examples')
        for example in notes['examples']:
            paragraph(example['title'],'Section')
            lines=[]
            for line in clean(example['code']).splitlines():lines.extend(textwrap.wrap(line,width=85,replace_whitespace=False,drop_whitespace=False,subsequent_indent='    ') or [''])
            story.append(Preformatted('\n'.join(lines),styles['StudyCode']))
            paragraph(example['explanation'])
        heading('Process flow')
        for step,description in enumerate(notes['flow'],1):
            table=Table([[p(str(step),'Section'),p(description)]],colWidths=[28,453],hAlign='LEFT')
            table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),colors.HexColor('#f1f8f8')),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),8),('RIGHTPADDING',(0,0),(-1,-1),8)]))
            story.extend([table,Spacer(1,5)])
        heading('Interview and exam checkpoints')
        for item in notes['interview']:paragraph(item['question'],'Section');paragraph(item['answer'])
        heading('Summary');paragraph(notes['summary'])
        heading('Practice questions')
        for number,item in enumerate(notes['practice'],1):paragraph(f"{number}. {item['question']}")
        heading('Practice solutions')
        for number,item in enumerate(notes['practice'],1):paragraph(f"{number}. {item['answer']}")
        heading('Reference textbooks')
        for book in chapter['textbooks']:paragraph(book['title']+' - '+book['author'])
        heading('Primary documentation');paragraph(chapter['referenceUrl'],'SmallStudy')
        paragraph('Content version: '+notes['version']+' | '+notes['source'],'SmallStudy')
        if index<len(chapters)-1:story.append(PageBreak())
    def footer(canvas,doc):
        canvas.saveState();canvas.setStrokeColor(colors.HexColor('#dbe5e8'));canvas.line(56,44,539,44)
        canvas.setFont('Study',8);canvas.setFillColor(colors.HexColor('#526375'));canvas.drawString(56,31,'NexVora | '+clean(title)[:67]);canvas.drawRightString(539,31,str(doc.page));canvas.restoreState()
    doc=StudyBook(out,pagesize=A4,leftMargin=56,rightMargin=56,topMargin=48,bottomMargin=62,title=title+' Complete Learning Notes',author='NexVora')
    doc.multiBuild(story,onFirstPage=footer,onLaterPages=footer)
    return out.getvalue()
