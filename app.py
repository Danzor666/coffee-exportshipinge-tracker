import streamlit as st
import pandas as pd
from datetime import datetime
import io

# ---------------------- LOGIN ---------------------- #
users = {"admin": "coffee123"}

def login():
    st.title("☕ Coffee Export Tracker - Login")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login"):
        if users.get(username) == password:
            st.session_state["logged_in"] = True
        else:
            st.error("Incorrect username or password")

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if not st.session_state.logged_in:
    login()
    st.stop()

# ---------------------- APP ---------------------- #
st.set_page_config(page_title="Coffee Export Tracker", layout="wide")
st.title("📦 Coffee Export Tracker")
st.markdown("---")

# ---------------------- FILE UPLOAD ---------------------- #
st.subheader("1️⃣ Upload Coffee Export Record")

uploaded_file = st.file_uploader("Upload Export Excel file", type=["csv", "xlsx"])
if uploaded_file:
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Check for required columns
    required_cols = ["Shipment ID", "Buyer Name", "ETD", "Contract Date"]
    if not all(col in df.columns for col in required_cols):
        st.error(f"❌ Missing required columns. Must include: {', '.join(required_cols)}")
    else:
        st.success("✅ File uploaded successfully!")
        st.session_state.df = df

# ---------------------- VIEW RECORDS ---------------------- #
st.subheader("2️⃣ View & Filter Records")

if "df" in st.session_state:
    df = st.session_state.df
    with st.expander("🔍 Filter options"):
        buyer_filter = st.text_input("Search by Buyer Name")
        if buyer_filter:
            df = df[df["Buyer Name"].str.contains(buyer_filter, case=False)]

    st.dataframe(df, use_container_width=True)

    # ---------------------- EXPORT ---------------------- #
    st.download_button("📥 Export as CSV", df.to_csv(index=False), file_name="coffee_export_data.csv")

# ---------------------- DOCUMENT CHECKLIST ---------------------- #
st.subheader("3️⃣ Documentation Checklist")

document_list = [
    "Signed Contract",
    "Registration Form",
    "LC / CAD / TT Documents",
    "Commercial Invoice",
    "Coffee Board Approval",
    "Booking Confirmation",
    "Cleaning Certificate",
    "Permit (NBE)",
    "Waybill",
    "VGM",
    "Shipping Instruction",
    "Quality Certificate",
    "Phytosanitary Certificate",
    "Bill of Lading",
    "Packing List",
    "Weight Certificate",
    "Fumigation Certificate",
    "ICO Certificate",
    "COO (if needed)",
    "Customs Clearance (T1, EX1)"
]

checklist = {doc: st.checkbox(doc) for doc in document_list}

if all(checklist.values()):
    st.success("🎉 All documents are complete!")
else:
    st.warning("⚠️ Some documents are missing.")

# ---------------------- ALERTS ---------------------- #
st.subheader("4️⃣ Alerts & Reminders")
if "df" in st.session_state:
    today = pd.to_datetime(datetime.today())
    df["ETD"] = pd.to_datetime(df["ETD"], errors="coerce")
    df["Days to Ship"] = (df["ETD"] - today).dt.days
    upcoming = df[df["Days to Ship"] <= 7]

    if not upcoming.empty:
        st.error("⏰ ALERT: Shipments due within 7 days")
        st.dataframe(upcoming)
    else:
        st.info("📅 No urgent shipments this week.")

# ---------------------- FOOTER ---------------------- #
st.markdown("---")
st.caption("Built by Cha's Logistics Team • Streamlit")




