import streamlit as st
import pandas as pd
import datetime

st.set_page_config(page_title="Coffee Export Tracker", layout="wide")
st.title("☕ Coffee Export Documentation Tracker")

st.markdown("---")

# Initialize session state if not set
if "records" not in st.session_state:
    st.session_state.records = []

with st.form("shipment_form", clear_on_submit=True):
    st.subheader("📦 New Shipment Entry")

    col1, col2, col3 = st.columns(3)
    with col1:
        shipment_id = st.text_input("Shipment ID")
        etd = st.date_input("ETD (Estimated Time of Departure)", datetime.date.today())
        contract_date = st.date_input("Contract Date")
    with col2:
        buyer_name = st.text_input("Buyer Name")
        payment_term = st.selectbox("Payment Term", ["LC", "CAD", "TT"])
        price_approved = st.radio("Price Above Minimum?", ["Yes", "No"])
    with col3:
        status = st.selectbox("Shipment Status", ["Pending", "In Progress", "Completed"])
        remarks = st.text_area("Remarks")

    st.markdown("### 📄 Upload Required Documents")

    docs = {
        "Signed Contract": st.file_uploader("Signed Contract"),
        "Registration Form (Amharic)": st.file_uploader("Registration Form"),
        "LC/Undertaking Letter": st.file_uploader("LC Copy / Undertaking Letter"),
        "Commercial Invoice": st.file_uploader("Commercial Invoice"),
        "Permit": st.file_uploader("Permit from NBE"),
        "Cleaning Certificate": st.file_uploader("Cleaning Certificate"),
        "Company Certificate": st.file_uploader("Company Certificate"),
        "Booking Confirmation": st.file_uploader("Booking Confirmation"),
        "Packing List": st.file_uploader("Packing List"),
        "Waybill": st.file_uploader("Waybill"),
        "Quality Certificate": st.file_uploader("Quality Certificate"),
        "VGM": st.file_uploader("VGM Document"),
        "T1 Document": st.file_uploader("T1 Document"),
        "EX1 / EX8": st.file_uploader("EX1 / EX8"),
        "Bill of Lading": st.file_uploader("Bill of Lading"),
        "Phytosanitary Certificate": st.file_uploader("Phytosanitary Certificate"),
        "Fumigation Certificate": st.file_uploader("Fumigation Certificate"),
        "ICO Certificate": st.file_uploader("ICO Certificate"),
        "Weight Certificate": st.file_uploader("Weight Certificate"),
        "COO Certificate": st.file_uploader("COO / Annex III / DFT/SPTT"),
        "Submission Form": st.file_uploader("Submission Form"),
        "Settlement Advice": st.file_uploader("Settlement Advice")
    }

    submitted = st.form_submit_button("Save Entry")
    if submitted:
        st.session_state.records.append({
            "Shipment ID": shipment_id,
            "Buyer": buyer_name,
            "ETD": etd,
            "Contract Date": contract_date,
            "Payment Term": payment_term,
            "Price Approved": price_approved,
            "Status": status,
            "Remarks": remarks,
            "Docs Uploaded": [k for k, v in docs.items() if v is not None]
        })
        st.success("Shipment record saved.")

st.markdown("---")

st.subheader("📊 Tracked Shipments")

if st.session_state.records:
    df = pd.DataFrame(st.session_state.records)
    st.dataframe(df)
else:
    st.info("No shipments tracked yet. Use the form above to add one.")


