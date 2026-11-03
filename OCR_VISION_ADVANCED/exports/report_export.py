from pathlib import Path
from datetime import datetime
from docx import Document
from docx.shared import Pt
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib import colors
from reportlab.lib.units import cm
from xml.sax.saxutils import escape

def export_txt(text, path):
    Path(path).write_text(text or "", encoding="utf-8")

def export_docx(path, image_name, extracted_text, metrics=None, evaluation=None):
    doc = Document()
    doc.add_heading("BÁO CÁO KẾT QUẢ NHẬN DIỆN OCR", 0)
    doc.add_paragraph("Đề tài: OCR – Nhận diện văn bản trong hình ảnh")
    doc.add_paragraph(f"Thời gian xuất báo cáo: {datetime.now():%d/%m/%Y %H:%M:%S}")
    doc.add_heading("1. Thông tin xử lý", level=1)
    doc.add_paragraph(f"Tên ảnh / nguồn dữ liệu: {image_name}")
    if metrics:
        for key, value in metrics.items():
            doc.add_paragraph(f"{key}: {value}")
    doc.add_heading("2. Văn bản nhận diện", level=1)
    doc.add_paragraph(extracted_text or "(Không phát hiện văn bản)")
    if evaluation:
        doc.add_heading("3. Đánh giá với văn bản chuẩn", level=1)
        for key, value in evaluation.items():
            doc.add_paragraph(f"{key}: {value:.4f}")
    doc.add_heading("4. Nhận xét", level=1)
    doc.add_paragraph(
        "Kết quả OCR phụ thuộc vào độ phân giải, độ tương phản, góc chụp, "
        "nhiễu và kiểu chữ. CER và WER được tính bằng cách so sánh văn bản "
        "nhận diện với văn bản chuẩn do người dùng cung cấp."
    )
    doc.save(path)

def export_pdf(path, image_name, extracted_text, metrics=None, evaluation=None):
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(
        name="VNTitle", parent=styles["Title"], alignment=TA_CENTER,
        textColor=colors.HexColor("#17365D"), fontSize=17, leading=22
    ))
    styles.add(ParagraphStyle(
        name="VNBody", parent=styles["BodyText"], fontSize=9.5,
        leading=14, spaceAfter=7
    ))
    story = [
        Paragraph("BÁO CÁO KẾT QUẢ NHẬN DIỆN OCR", styles["VNTitle"]),
        Spacer(1, 0.4*cm),
        Paragraph("Đề tài: OCR – Nhận diện văn bản trong hình ảnh", styles["VNBody"]),
        Paragraph(f"Thời gian xuất báo cáo: {datetime.now():%d/%m/%Y %H:%M:%S}", styles["VNBody"]),
        Paragraph("<b>1. Thông tin xử lý</b>", styles["Heading2"]),
        Paragraph("Tên ảnh / nguồn dữ liệu: " + escape(str(image_name)), styles["VNBody"])
    ]
    if metrics:
        for key, value in metrics.items():
            story.append(Paragraph(escape(f"{key}: {value}"), styles["VNBody"]))
    story.append(Paragraph("<b>2. Văn bản nhận diện</b>", styles["Heading2"]))
    safe_text = escape(extracted_text or "(Không phát hiện văn bản)").replace("\n", "<br/>")
    story.append(Paragraph(safe_text, styles["VNBody"]))
    if evaluation:
        story.append(Paragraph("<b>3. Đánh giá với văn bản chuẩn</b>", styles["Heading2"]))
        for key, value in evaluation.items():
            story.append(Paragraph(escape(f"{key}: {value:.4f}"), styles["VNBody"]))
    story.append(Paragraph("<b>4. Nhận xét</b>", styles["Heading2"]))
    story.append(Paragraph(
        "Kết quả OCR phụ thuộc vào độ phân giải, độ tương phản, góc chụp, "
        "nhiễu và kiểu chữ. CER và WER được tính bằng cách so sánh văn bản "
        "nhận diện với văn bản chuẩn do người dùng cung cấp.", styles["VNBody"]
    ))
    SimpleDocTemplate(
        path, pagesize=A4, rightMargin=1.8*cm, leftMargin=1.8*cm,
        topMargin=1.7*cm, bottomMargin=1.7*cm
    ).build(story)
