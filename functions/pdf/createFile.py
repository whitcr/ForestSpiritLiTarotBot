from reportlab.lib.colors import Color
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as ReportLabImage, PageBreak
from reportlab.lib.units import inch

pdfmetrics.registerFont(TTFont('font', './images/tech/fonts/1246-font.otf'))
pdfmetrics.registerFont(TTFont('fontTitle', './images/tech/fonts/KTFJermilov-Solid.ttf'))


def create_pdf(buffer, texts, images, background_color=None, background_image=None):
    doc = SimpleDocTemplate(buffer, pagesize = A4)
    elements = []
    styles = getSampleStyleSheet()
    title_color = Color(18 / 255, 18 / 255, 18 / 255, alpha = 1)

    title_style = ParagraphStyle(
        'TitleStyle',
        parent = styles['Heading1'],
        fontName = 'fontTitle',
        fontSize = 22,
        spaceAfter = 0,
        textColor = title_color
    )

    body_style = ParagraphStyle(
        'BodyStyle',
        parent = styles['Normal'],
        fontName = 'font',
        fontSize = 16,
        alignment = TA_JUSTIFY,
        spaceAfter = 6,
        textColor = title_color
    )

    for text, img in zip(texts, images):

        title, body = text.split("\n\n", 1)

        elements.append(Paragraph(title, title_style))
        elements.append(Spacer(1, 6))

        elements.append(ReportLabImage(img, width = 7 * inch, height = 4 * inch))
        elements.append(Spacer(1, 6))

        paragraphs = body.split("\n")
        for para in paragraphs:
            if para.strip():
                elements.append(Paragraph(para, body_style))
                elements.append(Spacer(1, 6))

        elements.append(PageBreak())

    doc.build(elements,
              onFirstPage = lambda canvas, doc: add_background(canvas, doc, background_color, background_image),
              onLaterPages = lambda canvas, doc: add_background(canvas, doc, background_color, background_image))
    buffer.seek(0)


def add_background(canvas, doc, color=None, image_path=None):
    if color:
        canvas.setFillColor(color)
        canvas.rect(0, 0, doc.width, doc.height, stroke = 0, fill = 1)
    if image_path:
        canvas.drawImage(image_path, 0, 0, width = 595, height = 842)
