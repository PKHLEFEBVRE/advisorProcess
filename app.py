from datetime import datetime
import streamlit as st
import pandas as pd
import os
import glob
from database import init_db, add_pending_record, get_pending_records, get_frozen_records, freeze_record
from extraction import parse_email, get_model_data, get_trades_data, create_pdf_report

st.set_page_config(page_title="Compliance Tracker", layout="wide")

# Initialize database
init_db()

# Ensure directories exist
for directory in ["emails", "data", "reports"]:
    os.makedirs(directory, exist_ok=True)

# Sync local emails to database
email_files = glob.glob('emails/*.msg')
for email_file in email_files:
    try:
        parsed = parse_email(email_file)
        add_pending_record(email_file, parsed['subject'], parsed['date'])
    except Exception as e:
        st.error(f"Error parsing {email_file}: {e}")

# Sidebar
st.sidebar.title("Compliance App")
page = st.sidebar.radio("Navigation", ["Pending Views", "Compliance Archive"])

if page == "Pending Views":
    st.header("Pending Advisor Views")

    pending_records = get_pending_records()
    if not pending_records:
        st.info("No pending views to process.")
    else:
        for record in pending_records:
            rec_id, email_file, subject, date_received = record

            with st.expander(f"📬 {subject} ({date_received})", expanded=False):
                # Using form to group "Launch" and "Freeze" interactions
                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button("🚀 Launch", key=f"launch_{rec_id}"):
                        st.session_state[f"launched_{rec_id}"] = True

                if st.session_state.get(f"launched_{rec_id}", False):
                    parsed_email = parse_email(email_file)

                    st.markdown("### 1. Advisor View")
                    st.text_area("Email Content", parsed_email['body'], height=150, disabled=True, key=f"email_{rec_id}")

                    st.markdown("### 2. Model Output")
                    model_df = get_model_data()
                    st.dataframe(model_df, width='stretch')

                    st.markdown("### 3. Trades")
                    trades_df = get_trades_data()

                    if not trades_df.empty:
                        st.write("Select the trades that apply to this view:")

                        # Add a checkbox for each trade row
                        trades_df['Selected'] = False

                        # Use st.data_editor to allow checkbox selection
                        edited_trades = st.data_editor(
                            trades_df,
                            column_config={
                                "Selected": st.column_config.CheckboxColumn(
                                    "Select",
                                    help="Select trade for compliance report",
                                    default=False,
                                )
                            },
                            disabled=trades_df.columns.drop('Selected').tolist(),
                            hide_index=True,
                            key=f"trade_editor_{rec_id}"
                        )
                    else:
                        edited_trades = pd.DataFrame()
                        st.warning("No trades found.")

                    st.markdown("### 4. Justification")
                    comment = st.text_area("Add compliance notes/justification here:", key=f"comment_{rec_id}")

                    if st.button("❄️ Freeze & Generate Report", key=f"freeze_{rec_id}"):
                        # Filter for selected trades only
                        if not edited_trades.empty:
                            selected_trades = edited_trades[edited_trades['Selected'] == True].drop(columns=['Selected'])
                        else:
                            selected_trades = pd.DataFrame()

                        # Generate PDF
                        report_filename = f"report_{rec_id}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
                        report_path = os.path.join('reports', report_filename)

                        create_pdf_report(rec_id, parsed_email, model_df, selected_trades, comment, report_path)

                        # Update database
                        freeze_record(rec_id, report_path)

                        st.success(f"Record Frozen successfully! Report saved to {report_path}")
                        st.rerun()

elif page == "Compliance Archive":
    st.header("Compliance Archive (Frozen Records)")

    frozen_records = get_frozen_records()
    if not frozen_records:
        st.info("No frozen records found.")
    else:
        for record in frozen_records:
            rec_id, email_file, subject, date_received, report_path, frozen_at = record

            with st.container():
                st.markdown(f"#### Record #{rec_id} - {subject}")
                st.write(f"**Frozen At:** {frozen_at}")
                st.write(f"**Email Date:** {date_received}")

                if os.path.exists(report_path):
                    with open(report_path, "rb") as pdf_file:
                        PDFbyte = pdf_file.read()
                        st.download_button(
                            label="Download PDF Report",
                            data=PDFbyte,
                            file_name=os.path.basename(report_path),
                            mime='application/octet-stream',
                            key=f"dl_{rec_id}"
                        )
                else:
                    st.error("Report file not found.")
                st.divider()
