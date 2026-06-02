from config import EMAILS_DIR, REPORTS_DIR
from datetime import datetime
import streamlit as st
import pandas as pd
import os
import subprocess
from database import init_db, get_frozen_trade_ids, get_frozen_events, freeze_event, get_trades_for_event, unfreeze_event, get_audit_log, get_events_between_dates
from extraction import get_model_data, get_trades_data, create_pdf_report, get_recent_emails, create_committee_report

st.set_page_config(page_title="Compliance Tracker", layout="wide")

# Initialize database
init_db()

# Ensure directories exist
for directory in [EMAILS_DIR, REPORTS_DIR]:
    os.makedirs(directory, exist_ok=True)

# Sidebar
st.sidebar.title("Compliance App")
page = st.sidebar.radio("Navigation", ["Pending Trades", "Compliance Archive", "Committee Report", "Audit Log"])

if page == "Pending Trades":
    st.header("Pending Trades to Review")

    # 1. Get all trades
    all_trades_df = get_trades_data()

    if all_trades_df.empty:
        st.info("No trades found in the file.")
    else:
        # Trade Data Validation: Ensure 'Id' exists, otherwise generate one
        if 'Id' not in all_trades_df.columns:
            st.warning("⚠️ 'Id' column missing from trades file. Auto-generating unique IDs based on row data.")
            # Create a synthetic ID from all column values
            all_trades_df['Id'] = all_trades_df.apply(lambda row: 'AUTO-' + str(abs(hash(''.join(str(val) for val in row.values)))), axis=1)

        # 2. Get frozen trade IDs
        frozen_ids = get_frozen_trade_ids()

        # 3. Filter for pending trades
        pending_trades_df = all_trades_df[~all_trades_df['Id'].astype(str).isin(frozen_ids)].copy()

        if pending_trades_df.empty:
            st.success("No pending trades to freeze. You're all caught up!")
        else:
            st.write("Select the trades you want to freeze in a single compliance event:")
            pending_trades_df.insert(0, 'Selected', False)

            edited_trades = st.data_editor(
                pending_trades_df,
                column_config={
                    "Selected": st.column_config.CheckboxColumn(
                        "Select",
                        help="Select trade for compliance report",
                        default=False,
                    )
                },
                disabled=pending_trades_df.columns.drop('Selected').tolist(),
                hide_index=True,
                key="trade_editor"
            )

            selected_trades = edited_trades[edited_trades['Selected'] == True].drop(columns=['Selected'])

            if not selected_trades.empty:
                st.divider()
                st.subheader("Compliance Event Details")

                # --- Email Selection ---
                st.markdown("### 1. Select Advisor View")
                email_limit = st.number_input("How many recent emails to show?", min_value=1, max_value=50, value=10, step=1)
                recent_emails = get_recent_emails(limit=email_limit)

                if not recent_emails:
                    st.warning("No emails found in the directory.")
                else:
                    # Format options for selectbox
                    email_options = {e['filepath']: f"{e['date']} - {e['subject']}" for e in recent_emails}
                    selected_email_path = st.selectbox("Choose Email", options=list(email_options.keys()), format_func=lambda x: email_options[x])

                    # Show preview
                    selected_email_data = next((e for e in recent_emails if e['filepath'] == selected_email_path), None)
                    if selected_email_data:
                        st.text_area("Email Preview", selected_email_data['body'], height=350, disabled=True)

                # --- Model Data ---
                st.markdown("### 2. Model Output")
                col1, col2 = st.columns([1, 5])
                with col1:
                    if st.button("🔄 Refresh Model Data"):
                        st.rerun()
                model_df = get_model_data()
                if len(model_df.columns) >= 3:
                    # Build format dict dynamically to avoid errors on string columns
                        format_dict = {}
                        if pd.api.types.is_numeric_dtype(model_df[model_df.columns[0]]):
                            format_dict[model_df.columns[0]] = "{:.0f}"
                        for col in model_df.columns[-3:]:
                            format_dict[col] = "{:.2%}"
                        st.dataframe(model_df.style.format(format_dict, na_rep=''), width='stretch', hide_index=True)
                else:
                    st.dataframe(model_df, width='stretch', hide_index=True)

                # --- Fund & Status Selection ---
                col_fund, col_status = st.columns(2)
                with col_fund:
                    st.markdown("### 3. Fund Selection")
                    selected_funds = st.multiselect(
                        "Which fund(s) does this view apply to?",
                        ["MFOF", "MLSU"],
                        default=["MFOF", "MLSU"]
                    )
                with col_status:
                    st.markdown("### 4. Decision Status")
                    trade_status = st.radio(
                        "What is the decision for these trades?",
                        ["Approve", "Reject", "Postpone"],
                        horizontal=True
                    )

                # --- Justification ---
                st.markdown("### 5. Justification")
                comment = st.text_area("Add compliance notes/justification here:")

                # --- Freeze ---
                if st.button("❄️ Freeze & Generate Report", type="primary"):
                    if not recent_emails:
                        st.error("Cannot freeze without an advisor email.")
                    else:
                        report_filename = f"report_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
                        report_path = os.path.join(REPORTS_DIR, report_filename)

                        # Generate PDF
                        create_pdf_report("NEW", selected_email_data, model_df, selected_trades, comment, report_path, selected_funds, trade_status)

                        # Update database
                        trade_ids = selected_trades['Id'].tolist()
                        freeze_event(
                            selected_email_data['filepath'],
                            selected_email_data['subject'],
                            selected_email_data['date'],
                            comment,
                            selected_funds,
                            trade_status,
                            report_path,
                            trade_ids
                        )

                        # Auto-open the PDF
                        try:
                            os.startfile(report_path)
                        except AttributeError:
                            try:
                                subprocess.call(['open', report_path])
                            except Exception:
                                pass

                        st.success("Trades successfully frozen!")
                        st.rerun()

elif page == "Compliance Archive":
    st.header("Compliance Archive (Frozen Events)")

    frozen_events = get_frozen_events()
    if not frozen_events:
        st.info("No frozen events found.")
    else:
        for record in frozen_events:
            event_id, subject, date_received, funds, trade_status, report_path, frozen_at = record

            with st.container():
                st.markdown(f"#### Event: {subject}")
                st.write(f"**Frozen At:** {frozen_at}")
                st.write(f"**Email Date:** {date_received}")
                st.write(f"**Funds:** {funds if funds else 'N/A'} | **Status:** {trade_status}")

                trades = get_trades_for_event(event_id)
                st.write(f"**Associated Trades:** {', '.join(trades) if trades else 'None'}")

                if os.path.exists(report_path):
                    with open(report_path, "rb") as pdf_file:
                        PDFbyte = pdf_file.read()
                        st.download_button(
                            label="Download PDF Report",
                            data=PDFbyte,
                            file_name=os.path.basename(report_path),
                            mime='application/octet-stream',
                            key=f"dl_{event_id}"
                        )
                else:
                    st.error("Report file not found.")

                with st.expander("⚠️ Unfreeze Event", expanded=False):
                    st.warning("Unfreezing will return these trades to the Pending queue.")
                    unfreeze_just = st.text_input("Reason for unfreezing:", key=f"unfreeze_reason_{event_id}")
                    if st.button("Confirm Unfreeze", key=f"btn_unfreeze_{event_id}", type="primary"):
                        if not unfreeze_just:
                            st.error("You must provide a justification to unfreeze.")
                        else:
                            unfreeze_event(event_id, unfreeze_just)
                            st.success("Event unfrozen.")
                            st.rerun()

                st.divider()

elif page == "Audit Log":
    st.header("Security & Compliance Audit Log")
    st.write("This log tracks all freeze and unfreeze actions for permanent record.")

    logs = get_audit_log()
    if not logs:
        st.info("No audit logs found.")
    else:
        log_data = []
        for l in logs:
            event_id, status, subject, frozen_at, just, unfrozen_at, unfreeze_just = l
            log_data.append({
                "Event ID": event_id,
                "Status": status,
                "Advisor View": subject,
                "Frozen At": frozen_at,
                "Freeze Justification": just,
                "Unfrozen At": unfrozen_at if unfrozen_at else "-",
                "Unfreeze Reason": unfreeze_just if unfreeze_just else "-"
            })
        st.dataframe(pd.DataFrame(log_data), width='stretch')

elif page == "Committee Report":
    st.header("Committee Summary Generator")
    st.write("Generate a high-level PDF summary of all compliance events and trades within a specific date range.")

    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Start Date")
    with col2:
        end_date = st.date_input("End Date")

    if st.button("Generate Summary", type="primary"):
        if start_date > end_date:
            st.error("Start Date must be before or equal to End Date.")
        else:
            # Format dates for SQL comparison
            start_str = start_date.strftime("%Y-%m-%d")
            end_str = end_date.strftime("%Y-%m-%d")

            raw_events = get_events_between_dates(start_str, end_str)

            # Augment events with their associated trades
            events_data = []
            for ev in raw_events:
                event_id, subject, email_date, funds, trade_status, just, frozen_at = ev
                trades = get_trades_for_event(event_id)
                events_data.append((event_id, subject, email_date, funds, trade_status, just, frozen_at, trades))

            report_filename = f"committee_summary_{start_str}_to_{end_str}.pdf"
            report_path = os.path.join(REPORTS_DIR, report_filename)

            create_committee_report(events_data, start_str, end_str, report_path)

            st.success("Summary Generated Successfully!")

            if os.path.exists(report_path):
                with open(report_path, "rb") as pdf_file:
                    PDFbyte = pdf_file.read()
                    st.download_button(
                        label="Download Committee Report (PDF)",
                        data=PDFbyte,
                        file_name=report_filename,
                        mime='application/octet-stream',
                        key="dl_committee"
                    )

                # Auto open it for convenience
                try:
                    os.startfile(report_path)
                except AttributeError:
                    try:
                        subprocess.call(['open', report_path])
                    except Exception:
                        pass
