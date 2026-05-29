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

def filter_columns(df):
    if len(df.columns) >= 5:
        # Keep first two columns and last three columns
        import pandas as pd
        return pd.concat([df.iloc[:, :2], df.iloc[:, -3:]], axis=1)
    return df

def get_model_data(filepath=MODEL_FILE):
    try:
        wb = openpyxl.load_workbook(filepath, data_only=True)
        if MODEL_NAMED_RANGE in wb.defined_names:
            destinations = list(wb.defined_names[MODEL_NAMED_RANGE].destinations)
            if destinations:
                sheet_name, coord = destinations[0]
                sheet = wb[sheet_name]
                data = []
                for row in sheet[coord]:
                    data.append([cell.value for cell in row])
                if data:
                    df = pd.DataFrame(data[1:], columns=data[0])
                    df.dropna(how='all', inplace=True)
                    df.dropna(axis=1, how='all', inplace=True)
                    return filter_columns(df)

        print(f"Named range '{MODEL_NAMED_RANGE}' not found, falling back to reading first sheet.")
        return filter_columns(pd.read_excel(filepath))
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
    story.append(Spacer(1, 12))

    body_style = ParagraphStyle('EmailBody', parent=styles['Normal'], backColor=colors.lightgrey, borderPadding=10)
    story.append(Paragraph(email_data['body'].replace('\n', '<br/>'), body_style))
    story.append(Spacer(1, 12))

    # Model Output Section
    story.append(Paragraph("2. Model Output", styles['Heading2']))
    if not model_df.empty:
        formatted_df = model_df.copy()
        # Format the last 3 columns as percentages if they are numeric
        if len(formatted_df.columns) >= 3:
            for col in formatted_df.columns[-3:]:
                formatted_df[col] = pd.to_numeric(formatted_df[col], errors='ignore')
                # If numeric, apply formatting
                if pd.api.types.is_numeric_dtype(formatted_df[col]):
                    formatted_df[col] = formatted_df[col].apply(lambda x: f"{x:.2%}" if pd.notnull(x) else x)

        model_data = [formatted_df.columns.tolist()] + formatted_df.values.tolist()
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
        wrap_style = ParagraphStyle('TradeWrap', parent=styles['Normal'], fontSize=8, leading=10, alignment=0)
        header_style = ParagraphStyle('TradeHeader', parent=styles['Normal'], fontSize=9, leading=11, fontName='Helvetica-Bold', textColor=colors.whitesmoke, alignment=0)

        # Extract headers (fields) and values
        fields = list(trades_df.columns)
        trades_values = trades_df.values.tolist() # Each inner list is a trade

        num_trades = len(trades_values)
        trades_per_table = 4 # Maximum number of trades to show side-by-side

        for i in range(0, num_trades, trades_per_table):
            chunk_trades = trades_values[i:i + trades_per_table]

            # Build the transposed rows for this chunk
            table_data = []
            for col_idx, field_name in enumerate(fields):
                row = [Paragraph(str(field_name), header_style)]
                for trade in chunk_trades:
                    row.append(Paragraph(str(trade[col_idx]), wrap_style))
                table_data.append(row)

            # Create Table
            first_col_w = 120
            remaining_w = 468 - first_col_w
            trade_col_w = remaining_w / len(chunk_trades) if len(chunk_trades) > 0 else 0
            col_widths = [first_col_w] + [trade_col_w] * len(chunk_trades)

            t = Table(table_data, colWidths=col_widths)

            t.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (0,-1), colors.grey),
                ('TEXTCOLOR', (0,0), (0,-1), colors.whitesmoke),
                ('FONTNAME', (0,0), (0,-1), 'Helvetica-Bold'),
                ('BACKGROUND', (1,0), (-1,-1), colors.lightsteelblue),
                ('GRID', (0,0), (-1,-1), 1, colors.black),
                ('VALIGN', (0,0), (-1,-1), 'TOP')
            ]))

            story.append(t)
            story.append(Spacer(1, 15))

    # Justification Section
    story.append(Paragraph("4. Justification / Comments", styles['Heading2']))
    if comment:
        story.append(Paragraph(comment, styles['Normal']))
    else:
        story.append(Paragraph("None provided.", styles['Normal']))

    story.append(Spacer(1, 40))
    story.append(Paragraph(f"<b>Timestamp:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))

    doc.build(story)
    return output_path

if __name__ == '__main__':
    pass
