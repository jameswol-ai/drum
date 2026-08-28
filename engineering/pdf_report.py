# engineering/pdf_report.py
from datetime import datetime
import os

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet
    from svglib.svglib import svg2rlg
    from io import BytesIO
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

def generate_analysis_report(data_dict, filename=None):
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.txt"
    try:
        with open(filename, "w") as f:
            f.write("DRUM Studio Analysis Report\n")
            f.write("="*30 + "\n")
            for key, value in data_dict.items():
                f.write(f"{key}: {value}\n")
        return filename, None
    except Exception as e:
        return None, str(e)

def generate_pdf_report(project_data, plan_svg_string=None, analysis_results=None, cost_breakdown=None, filename=None):
    if not PDF_SUPPORT:
        return None, "ReportLab or svglib not installed."
    if not filename:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"report_{timestamp}.pdf"
    try:
        doc = SimpleDocTemplate(filename, pagesize=A4,
                                rightMargin=72, leftMargin=72,
                                topMargin=72, bottomMargin=18)
        styles = getSampleStyleSheet()
        title_style = styles["Title"]
        normal_style = styles["Normal"]
        heading_style = styles["Heading2"]

        story = []
        story.append(Paragraph("DRUM Studio Structural Report", title_style))
        story.append(Spacer(1, 12))
        if project_data:
            for key, value in project_data.items():
                story.append(Paragraph(f"<b>{key}:</b> {value}", normal_style))
            story.append(Spacer(1, 12))

        if plan_svg_string:
            try:
                drawing = svg2rlg(BytesIO(plan_svg_string.encode('utf-8')))
                if drawing:
                    drawing.scale(0.5, 0.5)
                    story.append(Paragraph("Floor Plan", heading_style))
                    story.append(drawing)
                    story.append(Spacer(1, 12))
            except Exception:
                pass

        if analysis_results:
            story.append(Paragraph("Structural Analysis Results", heading_style))
            for key, value in analysis_results.items():
                story.append(Paragraph(f"<b>{key}:</b> {value}", normal_style))
            story.append(Spacer(1, 12))

        if cost_breakdown:
            story.append(Paragraph("Cost Estimate", heading_style))
            table_data = [["Item", "Cost (USD)"]]
            for item, cost in cost_breakdown.items():
                table_data.append([item, f"${cost:,.2f}"])
            table = Table(table_data, colWidths=[200, 100])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0,0), (-1,0), 12),
                ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
            ]))
            story.append(table)

        doc.build(story)
        return filename, None
    except Exception as e:
        return None, str(e)