from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

class PDFStyles:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self._create_styles()
    
    def register_fonts(self):
        try:
            # Путь к папке, где лежат arialmt.ttf и arial_bolditalicmt.ttf
            FONT_PATH = os.path.join(os.path.dirname(__file__), 'utils')
            arial_path = os.path.join(FONT_PATH, 'arialmt.ttf')
            arial_bold_path = os.path.join(FONT_PATH, 'arial_bolditalicmt.ttf')

            pdfmetrics.registerFont(TTFont('Arial', arial_path))
            pdfmetrics.registerFont(TTFont('Arial-Bold', arial_bold_path))

            return 'Arial', 'Arial-Bold'
        except Exception as e:
            print("Ошибка при регистрации Arial:", e)
            from reportlab.pdfbase.cidfonts import UnicodeCIDFont
            pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
            return 'STSong-Light', 'STSong-Light'


    def _create_styles(self):
        main_font, bold_font = self.register_fonts()

        self.styles.add(ParagraphStyle(
            name="HeaderStyle",
            fontName=bold_font,
            fontSize=12,
            leading=14,
            alignment=TA_CENTER,
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name="BodyStyle",
            fontName=main_font,
            fontSize=10,
            leading=12,
            alignment=TA_CENTER,
            spaceAfter=12
        ))

        self.styles.add(ParagraphStyle(
            name="TableStyle",
            fontName=main_font,  # или main_font, если не нужен жирный
            fontSize=8,
            leading=9,
            alignment=TA_CENTER,
            spaceBefore=2,
            spaceAfter=2
        ))

    def get_style(self, style_name):
        return self.styles[style_name]