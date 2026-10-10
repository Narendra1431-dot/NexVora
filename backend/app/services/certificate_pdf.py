"""Single locked premium composition shared by draft, issued PDF and image previews."""
from io import BytesIO
from pathlib import Path
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from .certificate_standard_pdf import render_certificate as render_standard

TEMPLATE_VERSION='nexvora-premium-locked-v1'
BACKGROUND=Path(__file__).resolve().parents[1]/'assets'/'certificates'/'premium-locked-v1.png'

def render_certificate(doc:dict,*,sample:bool=False,draft:bool=False)->bytes:
    if doc['type']!='premium':
        return render_standard(doc,sample=sample or draft)
    out=BytesIO();w,h=landscape(A4)
    c=canvas.Canvas(out,pagesize=(w,h),pageCompression=1)
    c.setTitle('NexVora Certificate - '+doc['certificateId']);c.setAuthor(doc['issuer'])
    c.drawImage(str(BACKGROUND),0,0,width=w,height=h)
    # Searchable text for static headings already printed in the locked artwork.
    c.saveState()
    heading=c.beginText(40,h-40);heading.setTextRenderMode(3);heading.setFont('Times-Bold',12)
    heading.textLine('CERTIFICATE OF COMPLETION');heading.textLine('PREMIUM VERIFIED CERTIFICATE');c.drawText(heading);c.restoreState()
    c.saveState();c.scale(w/1491,h/1055)
    # Replace only baked-in former-brand lettering; preserve the locked ornament/layout.
    c.setFillColor(HexColor('#faf9f5'))
    c.rect(483,1055-122,565,34,fill=1,stroke=0)
    c.rect(650,1055-873,235,69,fill=1,stroke=0)
    c.setStrokeColor(HexColor('#b88b2e'));c.setLineWidth(1)
    c.line(595,1055-869,953,1055-869)
    c.rect(645,1055-899,259,24,fill=1,stroke=0)
    c.setFillColor(HexColor('#005864'));c.setFont('Helvetica-Bold',22)
    c.drawCentredString(768,1055-115,'NexVora / LEARNING & CAREER INTELLIGENCE')
    c.setFillColor(HexColor('#07162e'));c.setFont('Times-Italic',48)
    c.drawCentredString(774,1055-857,'NexVora')
    c.setFont('Times-Roman',21)
    c.drawCentredString(774,1055-894,'NexVora Certificate Service')

    def centered(value,baseline,size=22,color='#00172d',font='Times-Roman',width=1070):
        value=str(value)
        size=min(size,size*width/max(stringWidth(value,font,size),1))
        c.setFont(font,size);c.setFillColor(HexColor(color));c.drawCentredString(745.5,1055-baseline,value)
    def block(value,top,size=22,width=1080,color='#00172d',font='Times-Roman'):
        style=ParagraphStyle('locked',fontName=font,fontSize=size,leading=size*1.12,alignment=1,textColor=HexColor(color))
        p=Paragraph(escape(str(value)),style);_,height=p.wrap(width,110)
        p.drawOn(c,(1491-width)/2,1055-top-height)
    if sample: centered('DEMO / SAMPLE - NOT VALID FOR VERIFICATION',305,19,'#a44509','Helvetica-Bold')
    elif draft: centered('PREVIEW - NOT ISSUED',305,18,'#a44509','Helvetica-Bold')
    centered(doc['studentName'],443,86,font='Times-Bold',width=1050)
    if doc.get('displaySubtitle'): centered(doc['displaySubtitle'],465,18,'#475569',width=960)
    course=doc['courseName']
    if stringWidth(course,'Times-Bold',56)<=1100: centered(course,597,56,font='Times-Bold',width=1100)
    else: block(course,548,size=34 if len(course)<150 else 28,width=1100,font='Times-Bold')
    if sample:
        centered('Demonstration of the final certificate design. All displayed names, scores and skills are sample data.',680,22,'#475569')
    else:
        centered('Completed the course requirements and passed the required assessment.',680,22,'#475569')
    score=f"{doc['assessmentScore']:g}" if isinstance(doc.get('assessmentScore'),(int,float)) else str(doc.get('assessmentScore',''))
    skills=', '.join(doc['skills']) or 'Full competency verification pending'
    block('Assessment score: '+score+'%  |  Verified skills: '+skills,708,size=23 if len(skills)<90 else 19,width=1100,color='#00717a',font='Times-Bold')
    if sample: centered('Sample competency evidence only - no real assessment, project or credential is issued.',771,21,'#475569')
    elif not draft: centered('Achievement supported by recorded assessment and competency evidence.',771,20,'#475569')
    fields=[('Issued',doc['issuedAt'] if sample or draft else doc['issuedAt'][:10]),('ID',doc['certificateId']),('Issuer',doc['issuer']),('Completed',doc.get('completedAt',doc['issuedAt']) if sample else doc.get('completedAt',doc['issuedAt'])[:10])]
    for index,(label,value) in enumerate(fields):
        size=18;full=f'{label}:  {value}';size=min(size,18*360/max(stringWidth(full,'Times-Roman',18),1))
        c.setFillColor(HexColor('#07162e'));c.setFont('Times-Bold',size);c.drawString(107,1055-(840+31*index),label+':')
        offset=stringWidth(label+':  ','Times-Bold',size)
        c.setFont('Times-Roman',size);c.drawString(107+offset,1055-(840+31*index),str(value))
    # Position and proportions are locked to the reference's bottom-right QR block.
    code=qr.QrCodeWidget(doc['publicUrl']);bounds=code.getBounds();size=112
    drawing=Drawing(size,size,transform=[size/(bounds[2]-bounds[0]),0,0,size/(bounds[3]-bounds[1]),0,0]);drawing.add(code)
    renderPDF.draw(drawing,c,1191,1055-918)
    c.linkURL(doc['publicUrl'],(1191,1055-918,1303,1055-806),relative=1)
    c.setFont('Helvetica',13);c.setFillColor(HexColor('#475569'))
    c.drawCentredString(1247,1055-937,'Demo verification QR - sample only' if sample else 'Preview QR - not issued' if draft else 'Scan to verify this certificate')
    c.setFont('Times-Roman',16)
    c.drawCentredString(774,1055-921,'Sample issuer signature - not an issued credential' if sample else 'Electronically issued by NexVora' if not draft else 'Signature applied on issuance')
    c.restoreState();c.showPage();c.save();return out.getvalue()

def pdf_preview(pdf:bytes)->bytes:
    import pymupdf
    with pymupdf.open(stream=pdf,filetype='pdf') as doc:
        return doc[0].get_pixmap(matrix=pymupdf.Matrix(2,2)).tobytes('png')
