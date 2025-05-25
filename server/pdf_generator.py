from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.units import mm
from .pdf_styles import PDFStyles
from .utils.defect_names import DefectNames
from reportlab.lib import colors
from collections import Counter
import json

defect_names = DefectNames()

def create_table_data(defects_data):
    styles = PDFStyles()
    result = []
    first_iteration = True
    ruler = 300
    for i in range(11):

        number1 = i * 300
        number2 = (i+1) * 300
        if i == 10:
            number2 = 0
        
        data = []
        for obj in defects_data:

            if i == 10:
                if (obj['x1'] <= 300 or obj['x1'] >= 30300):
                    data.append(int(obj['className']))
                else:
                    continue

            if (ruler <= obj['x1'] <= ruler + 3000):
                data.append(int(obj['className']))
            else:
                continue

        counter = Counter(data)
        
        text = ''
        for j in range(13):
            clv = counter.get(j, 0)

            if clv != 0:
                text += f"{defect_names.get(j)}({clv}) "

        if text == '':
            text = '-'
        ruler += 3000

        if first_iteration:
            result.append([
                Paragraph("100-400-ЛС", styles.get_style("TableStyle")),
                Paragraph("1020x17", styles.get_style("TableStyle")),
                Paragraph("1CE91939", styles.get_style("TableStyle")),
                Paragraph(f"{number1}-{number2}", styles.get_style("TableStyle")),
                Paragraph("0,50", styles.get_style("TableStyle")),
                Paragraph(text, styles.get_style("TableStyle")),
                Paragraph("н/п", styles.get_style("TableStyle")),
                Paragraph("годен", styles.get_style("TableStyle")),
                Paragraph("н/п", styles.get_style("TableStyle")),
            ])
            first_iteration = False
        else:
            result.append([
                Paragraph("", styles.get_style("TableStyle")),
                Paragraph("", styles.get_style("TableStyle")),
                Paragraph("", styles.get_style("TableStyle")),
                Paragraph(f"{number1}-{number2}", styles.get_style("TableStyle")),
                Paragraph("0,50", styles.get_style("TableStyle")),
                Paragraph(text, styles.get_style("TableStyle")),
                Paragraph("н/п", styles.get_style("TableStyle")),
                Paragraph("годен", styles.get_style("TableStyle")),
                Paragraph("н/п", styles.get_style("TableStyle")),
            ])

    return result

def create_pdf(file_path: str, output_path: str, defects_data: list):
    output = f"{output_path}/{file_path}.pdf"
    styles = PDFStyles()
    
    doc = SimpleDocTemplate(
        output,
        pagesize=A4,
        leftMargin=15*mm,
        rightMargin=15*mm,
        topMargin=10*mm,
        bottomMargin=10*mm
    )

    # Элементы документа
    elements = []

    # Заголовок
    elements.append(Paragraph("СП 392.1325800.2018", styles.get_style("HeaderStyle")))
    elements.append(Spacer(1, 10))
    elements.append(Paragraph("ЗАКЛЮЧЕНИЕ № 100-400-ЛС", styles.get_style("HeaderStyle")))
    elements.append(Paragraph("от 01.03.2021 года", styles.get_style("HeaderStyle")))
    elements.append(Spacer(1, 15))

    # Основной текст
    text = """
    по результатам контроля качества сварных соединений радиографическим методом<br/>
    Тип источника ионизирующего излучения: рентгеновский дефектоскоп непрерывного действия<br/>
    Номер операционной технологической карты контроля: ТК-РК-ЦР-С-1020x17П-00890001<br/>
    <br/>
    РЕЗУЛЬТАТЫ КОНТРОЛЯ
    """

    elements.append(Paragraph(text, styles.get_style("BodyStyle")))
    elements.append(Spacer(1, 10))

    table_data = create_table_data(defects_data)

    headers = [
            Paragraph("Номер сварного соединения по журналу сварки", styles.get_style("TableStyle")),
            Paragraph("Диаметр и толщина (радиационная номинальная) стенки трубы, мм", styles.get_style("TableStyle")),
            Paragraph("Шифр бригады или клеймо сварщика", styles.get_style("TableStyle")),
            Paragraph("Номер участка контроля (координаты мерного пояса)", styles.get_style("TableStyle")),
            Paragraph("Чувствительность контроля, мм", styles.get_style("TableStyle")),
            Paragraph("Описание выявленных дефектов", styles.get_style("TableStyle")),
            Paragraph("Координаты недопустимых дефектов по периметру шва", styles.get_style("TableStyle")),
            Paragraph("Заключение (годен, ремонт, вырезать)", styles.get_style("TableStyle")),
            Paragraph("Примечания", styles.get_style("TableStyle"))
        ]
    data = [headers] + table_data
    
    # Создаем таблицу с указанием шрифта
    table = Table(data, colWidths=[25*mm, 20*mm, 20*mm, 19*mm, 20*mm, 20*mm, 26*mm, 25*mm, 10*mm])
    table.setStyle(TableStyle([
        ('SPAN', (0, 1), (0, len(table_data))),
        ('SPAN', (1, 1), (1, len(table_data))),
        ('SPAN', (2, 1), (2, len(table_data))),
        ("BACKGROUND", (0, 0), (-1, 0), colors.white),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.black),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("FONTSIZE", (0, 0), (-1, -1), 8),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
    ]))

    elements.append(table)
    elements.append(Spacer(1, 10))

    doc.build(elements)