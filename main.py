import streamlit as st
from datetime import date
from new_test import get_records
import pandas as pd
import json
import base64
from io import BytesIO

# App Title
st.title("📋 User Info Input App")

# Default Dates
today = date.today()
one_year_ago = date(today.year - 1, today.month, today.day)

# Input Form
with st.form("user_input_form"):
    st.header("🔍 Enter User Details")

    col1, col2 = st.columns(2)
    with col1:
        first_name = st.text_input("First Name", value="ben")
    with col2:
        last_name = st.text_input("Last Name", value="smith")

    st.markdown("### 📅 Select Date Range")
    col3, col4 = st.columns(2)
    with col3:
        from_date = st.date_input("From Date", value=one_year_ago)
    with col4:
        thru_date = st.date_input("Thru Date", value=today)

    submitted = st.form_submit_button("Submit")

# Handle Submission
if submitted:
    if not first_name or not last_name:
        st.warning("⚠️ Please fill in both first and last names.")
    else:
        from_date_str = from_date.strftime('%m/%d/%Y')
        thru_date_str = thru_date.strftime('%m/%d/%Y')

        output = get_records(first_name, last_name, from_date_str, thru_date_str)

        if isinstance(output, list) and output:
            st.subheader("📄 Output Records")
            st.write(f"🔢 Total Records Found: {len(output)}")

            # Prepare data for download
            df = pd.DataFrame(output)
            json_data = json.dumps(output, indent=2)

            # Excel download
            excel_buffer = BytesIO()
            df.to_excel(excel_buffer, index=False, engine='openpyxl')
            excel_bytes = excel_buffer.getvalue()
            b64_excel = base64.b64encode(excel_bytes).decode()
            st.download_button("📥 Download Excel", data=excel_bytes, file_name="records.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

            # JSON download
            st.download_button("📥 Download JSON", data=json_data, file_name="records.json", mime="application/json")

            # Display records
            for record in output:
                st.markdown("---")
                col1, col2 = st.columns([2, 3])

                with col1:
                    st.markdown(f"**Instrument Number:** {record.get('instrument_number', 'N/A')}")
                    st.markdown(f"**From:** {record.get('from', 'N/A')}")
                    st.markdown(f"**To:** {record.get('to', 'N/A')}")
                    st.markdown(f"**Record Date:** {record.get('record_date', 'N/A')}")
                    st.markdown(f"**Doc Type:** {record.get('doc_type', 'N/A')}")

                with col2:
                    images = record.get("image_links", [])
                    if images:
                        st.markdown("**Images:**")
                        for url in images:
                            st.image(url, caption="Document Image", use_container_width=True)
        else:
            st.info("ℹ️ No records found for the given criteria.")


