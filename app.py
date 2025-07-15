# app.py
import streamlit as st
import os
import json
from datetime import datetime, date

DATA_FILE = 'data.json'
UPLOAD_DIR = 'uploads'

REQUIRED_DOCS = [
    'Signed Contract',
    'Registration Form',
    'LC Application / Undertaking Letter',
    'Commercial Invoice',
    'Packing List',
    'Bill of Lading',
    'Phytosanitary Certificate',
    'Fumigation Certificate',
    'Quality Certificate',
    'Weight Certificate',
    'ICO Certificate',
    'COO Certificate',
    'Beneficiary’s Certificate',
    'Submission Form',
    'Cover Letter',
    'Bank Permit',
    'Transit Agreement',
    'Bank Advice'
]

PAYMENT_TERMS = ['LC', 'CAD', 'TT']

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r') as f:
            return json.load(f)
    return []

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=4)

def make_folder(path):
    if not os.path.exists(path):
        os.makedirs(path)

def upload_doc(shipment_id, doc_type):
    file = st.file_uploader(f"Upload {doc_type}", type=['pdf', 'jpg', 'png'], key=f"{shipment_id}_{doc_type}")
    if file:
        path = os.path.join(UPLOAD_DIR, shipment_id)
        make_folder(path)
        ext = file.name.split('.')[-1]
        file_path = os.path.join(path, f"{doc_type.replace(' ', '_')}.{ext}")
        with open(file_path, 'wb') as f:
            f.write(file.getbuffer())
        st.success(f"{doc_type} uploaded.")

def check_uploaded(shipment_id):
    path = os.path.join(UPLOAD_DIR, shipment_id)
    uploaded = []
    if os.path.exists(path):
        uploaded = [f.split('.')[0].replace('_', ' ') for f in os.listdir(path)]
    return uploaded

def validate_shipment_input(shipment_id, buyer, contract_date, etd, payment_term):
    errors = []
    today = date.today()
    if not shipment_id.strip():
        errors.append("Shipment ID cannot be empty.")
    if not buyer.strip():
        errors.append("Buyer name cannot be empty.")
    if contract_date > today:
        errors.append("Contract date cannot be in the future.")
    if etd < today:
        errors.append("ETD must be today or a future date.")
    if contract_date > etd:
        errors.append("Contract date cannot be after ETD.")
    if payment_term not in PAYMENT_TERMS:
        errors.append("Payment term must be one of LC, CAD, or TT.")
    return errors

st.set_page_config(page_title="Coffee Export Tracker", layout="wide")
st.title("📦 Coffee Export Documentation Tracker with Validation")

menu = ["Add Shipment", "View Shipments"]
choice = st.sidebar.selectbox("Menu", menu)

all_data = load_data()

if choice == "Add Shipment":
    st.subheader("➕ Add New Shipment")
    with st.form(key='add_form'):
        shipment_id = st.text_input("Shipment ID")
        buyer = st.text_input("Buyer Name")
        contract_date = st.date_input("Contract Date")
        etd = st.date_input("Estimated Time of Departure (ETD)")
        payment_term = st.selectbox("Payment Term", PAYMENT_TERMS)
        submitted = st.form_submit_button("Save Shipment")

        if submitted:
            errors = validate_shipment_input(shipment_id, buyer, contract_date, etd, payment_term)
            if errors:
                for err in errors:
                    st.error(err)
            else:
                shipment = {
                    "shipment_id": shipment_id.strip(),
                    "buyer": buyer.strip(),
                    "contract_date": contract_date.strftime('%Y-%m-%d'),
                    "etd": etd.strftime('%Y-%m-%d'),
                    "payment_term": payment_term,
                    "created_at": datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                all_data.append(shipment)
                save_data(all_data)
                st.success("Shipment added successfully.")

elif choice == "View Shipments":
    st.subheader("📄 Shipment List")
    if not all_data:
        st.info("No shipments yet.")
    else:
        for shipment in all_data:
            with st.expander(f"🚢 {shipment['shipment_id']} - {shipment['buyer']}"):
                st.write(f"**Contract Date:** {shipment['contract_date']}")
                st.write(f"**ETD:** {shipment['etd']}")
                st.write(f"**Payment Term:** {shipment.get('payment_term', 'N/A')}")

                uploaded = check_uploaded(shipment['shipment_id'])
                missing_docs = []

                for doc in REQUIRED_DOCS:
                    col1, col2 = st.columns([3,1])
                    with col1:
                        upload_doc(shipment['shipment_id'], doc)
                    with col2:
                        if doc in uploaded:
                            st.success("Uploaded")
                        else:
                            st.error("Missing")
                            missing_docs.append(doc)

                if missing_docs:
                    st.warning(f"🚨 Missing documents: {', '.join(missing_docs)}")
                else:
                    st.success("✅ All required documents uploaded.")

