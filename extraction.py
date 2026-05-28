import os
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import extract_msg

def parse_email(file_path):
    msg = extract_msg.Message(file_path)

    subject = msg.subject or 'No Subject'
    date = msg.date or 'No Date'
    body = msg.body or 'No Content'

    msg.close()

    return {
        'subject': subject,
        'date': str(date),
        'body': body.strip()
    }

def get_model_data(filepath='data/model_output.xlsx'):
    try:
        return pd.read_excel(filepath)
    except Exception as e:
        print(f"Error reading model data: {e}")
        return pd.DataFrame()

def get_trades_data(filepath='data/trades.xlsx'):
    try:
        return pd.read_excel(filepath)
    except Exception as e:
        print(f"Error reading trades data: {e}")
        return pd.DataFrame()

def create_pdf_report(record_id, email_data, model_df, trades_df, comment, output_path):
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph(f"Compliance Report - Record #{record_id}", styles['Heading1']))
    story.append(Spacer(1, 12))

    # Email Section
    story.append(Paragraph("1. Advisor View (Email)", styles['Heading2']))
    story.append(Paragraph(f"<b>Date:</b> {email_data['date']}", styles['Normal']))
    story.append(Paragraph(f"<b>Subject:</b> {email_data['subject']}", styles['Normal']))
    story.append(Spacer(1, 6))

    body_style = ParagraphStyle('EmailBody', parent=styles['Normal'], backColor=colors.lightgrey, borderPadding=10)
    story.append(Paragraph(email_data['body'].replace('\n', '<br/>'), body_style))
    story.append(Spacer(1, 12))

    # Model Output Section
    story.append(Paragraph("2. Model Output", styles['Heading2']))
    if not model_df.empty:
        model_data = [model_df.columns.tolist()] + model_df.values.tolist()
        t = Table(model_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.beige),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No model data available.", styles['Normal']))
    story.append(Spacer(1, 12))

    # Trades Section
    story.append(Paragraph("3. Executed Trades", styles['Heading2']))
    if not trades_df.empty:
        trades_data = [trades_df.columns.tolist()] + trades_df.values.tolist()
        t = Table(trades_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,0), 12),
            ('BACKGROUND', (0,1), (-1,-1), colors.lightsteelblue),
            ('GRID', (0,0), (-1,-1), 1, colors.black)
        ]))
        story.append(t)
    else:
        story.append(Paragraph("No trade data available/selected.", styles['Normal']))
    story.append(Spacer(1, 12))

    # Justification Section
    story.append(Paragraph("4. Justification / Comments", styles['Heading2']))
    if comment:
        story.append(Paragraph(comment, styles['Normal']))
    else:
        story.append(Paragraph("None provided.", styles['Normal']))

    doc.build(story)
    return output_path

if __name__ == '__main__':
    pass
