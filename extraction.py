from config import MODEL_FILE, TRADES_FILE, MODEL_NAMED_RANGE
import openpyxl
import os
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
import extract_msg

import glob
from config import EMAILS_DIR

def get_recent_emails(limit=10):
    email_files = glob.glob(os.path.join(EMAILS_DIR, '*.msg'))
    # Sort files by modification time (newest first)
    email_files.sort(key=os.path.getmtime, reverse=True)

    recent_emails = []
    for f in email_files[:limit]:
        try:
            parsed = parse_email(f)
            parsed['filepath'] = f
            recent_emails.append(parsed)
        except Exception as e:
            print(f"Error parsing {f}: {e}")

    return recent_emails

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

def get_model_data(filepath=MODEL_FILE):
    try:
        # Load the workbook with openpyxl to find the named range
        wb = openpyxl.load_workbook(filepath, data_only=True)

        if MODEL_NAMED_RANGE in wb.defined_names:
            # Extract the coordinates for the named range
            destinations = list(wb.defined_names[MODEL_NAMED_RANGE].destinations)
            if destinations:
                sheet_name, coord = destinations[0]
                sheet = wb[sheet_name]

                # Extract the data from the specific cells
                data = []
                for row in sheet[coord]:
                    data.append([cell.value for cell in row])

                if data:
                    # Assume first row is headers
                    df = pd.DataFrame(data[1:], columns=data[0])
                    # Drop entirely empty rows or columns just in case
                    df.dropna(how='all', inplace=True)
                    df.dropna(axis=1, how='all', inplace=True)
                    return df

        # Fallback if named range not found or not parsable
        print(f"Named range '{MODEL_NAMED_RANGE}' not found, falling back to reading first sheet.")
        return pd.read_excel(filepath)
    except Exception as e:
        print(f"Error reading model data: {e}")
        return pd.DataFrame()

def get_trades_data(filepath=TRADES_FILE):
    try:
        return pd.read_excel(filepath)
    except Exception as e:
        print(f"Error reading trades data: {e}")
        return pd.DataFrame()

def create_pdf_report(record_id, email_data, model_df, trades_df, comment, output_path, funds):
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    story.append(Paragraph(f"Compliance Report - Record #{record_id}", styles['Heading1']))
    story.append(Spacer(1, 12))


    story.append(Paragraph(f"<b>Applicable Funds:</b> {', '.join(funds)}", styles['Normal']))
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

    story.append(Spacer(1, 40))
    story.append(Paragraph("<b>Compliance / Portfolio Manager Signature:</b> ___________________________", styles['Normal']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"<b>Timestamp:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))

    doc.build(story)
    return output_path

if __name__ == '__main__':
    pass
