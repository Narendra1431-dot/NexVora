"""A4 landscape PDFs, generated only from server-issued immutable snapshots."""
from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.colors import HexColor
from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.graphics.barcode import qr
from reportlab.graphics.shapes import Drawing
from reportlab.graphics import renderPDF

def render_certificate(doc: dict, *, sample: bool = False) -> bytes:
    buffer = BytesIO()
    w, h = landscape(A4)
    c = canvas.Canvas(buffer, pagesize=(w,h), pageCompression=1)
    c.setTitle('NexVora Certificate - '+doc['certificateId'])
    c.setAuthor(doc['issuer'])
    c.setFillColor(HexColor('#fffefb')); c.rect(0,0,w,h,fill=1,stroke=0)
    c.setStrokeColor(HexColor('#0f766e')); c.setLineWidth(1.4); c.rect(23,23,w-46,h-46)
    c.setStrokeColor(HexColor('#cbd5e1')); c.setLineWidth(.5); c.rect(30,30,w-60,h-60)
    def text(value,y,size=12,color='#0f172a',bold=False):
        style=ParagraphStyle('line',fontName='Helvetica-Bold' if bold else 'Helvetica',fontSize=size,leading=size*1.25,textColor=HexColor(color),alignment=1)
        p=Paragraph(escape(str(value)),style); _,height=p.wrap(w-130,110)
        p.drawOn(c,65,y-height)
    text('NexVora  /  LEARNING & CAREER INTELLIGENCE',h-51,12,'#0f766e',True)
    if doc['type']=='premium':
        c.setStrokeColor(HexColor('#0f766e')); c.circle(w-76,h-88,25)
        c.setFillColor(HexColor('#0f766e')); c.setFont('Helvetica-Bold',7)
        c.drawCentredString(w-76,h-86,'PREMIUM'); c.drawCentredString(w-76,h-97,'EDITION')
    text('CERTIFICATE OF COMPLETION',h-88,25,bold=True)
    text(('PREMIUM VERIFIED CERTIFICATE' if doc['type']=='premium' else 'STANDARD CERTIFICATE') if sample else 'PREMIUM EDITION' if doc['type']=='premium' else 'COURSE ACHIEVEMENT',h-126,10,'#0f766e')
    if sample: text('DEMO / SAMPLE - NOT VALID FOR VERIFICATION',h-143,9,'#92400e',True)
    text('Presented to',h-157,11,'#64748b')
    name=doc['studentName']
    text(name,h-181, min(31, max(16, 750/max(len(name),1))),bold=True)
    if doc.get('displaySubtitle'): text(doc['displaySubtitle'],h-217,10,'#475569')
    text('for successful completion of',h-233,11,'#64748b')
    text(doc['courseName'],h-259,14 if len(doc['courseName'])>95 else 18,bold=True)
    text(doc['achievementDescription'],h-323,10,'#475569')
    if doc['type']=='premium':
        text('Assessment score: '+str(doc['assessmentScore'])+'%  |  Verified skills: '+(', '.join(doc['skills']) or 'See assessment evidence; full competency verification pending'),h-354,10,'#0f766e')
        text('Sample competency evidence only - no real assessment, project or credential is issued.' if sample else 'Proof references: '+str(len(doc['evidenceIds']))+' assessment / project records. Certificate adds no independent mastery credit.',h-389,9,'#64748b')
        if doc['paymentStatus']=='demo_confirmed': text('DEMO PURCHASE - NO MONEY CHARGED',h-413,9,'#92400e',True)
    code=qr.QrCodeWidget(doc['publicUrl']); bounds=code.getBounds(); size=78
    drawing=Drawing(size,size,transform=[size/(bounds[2]-bounds[0]),0,0,size/(bounds[3]-bounds[1]),0,0]); drawing.add(code)
    renderPDF.draw(drawing,c,w-143,58)
    c.linkURL(doc['publicUrl'],(w-143,58,w-65,136),relative=0)
    c.setFillColor(HexColor('#475569')); c.setFont('Helvetica',9)
    c.drawString(57,118,'Issued: '+(doc['issuedAt'] if sample else doc['issuedAt'][:10])); c.drawString(57,100,'ID: '+doc['certificateId'])
    c.drawString(57,82,'Issuer: '+doc['issuer'])
    c.drawString(57,64,'Completed: '+(doc.get('completedAt',doc['issuedAt']) if sample else doc.get('completedAt',doc['issuedAt'])[:10]))
    c.setStrokeColor(HexColor('#0f766e')); c.line(350,102,580,102)
    c.setFont('Helvetica',10); c.drawCentredString(465,111,'NexVora Certificate Service')
    c.setFont('Helvetica',8); c.drawCentredString(465,87,'Sample issuer signature - not an issued credential' if sample else 'Electronically issued - verify using the QR code')
    c.drawCentredString(465,73,'Issuer signature area (not a cryptographic PDF signature)')
    c.setFont('Helvetica',7); c.drawRightString(w-55,46,'Demo verification QR - sample only' if sample else 'Scan to verify the original registry record')
    c.showPage(); c.save(); return buffer.getvalue()
