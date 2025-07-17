import streamlit as st
import os
import json
import smtplib
from email.message import EmailMessage
from datetime import datetime, date, timedelta
import hashlib
import uuid
import pandas as pd

# ---------------------- CONFIG ----------------------
DATA_FILE = 'data.json'
USER_DB = 'users.json'
ORGANIZATION_DB = 'organizations.json'
PAYMENT_DB = 'payments.json'
ROLES = ['staff', 'manager']
UPLOAD_FOLDER = 'uploads'
PAYMENT_UPLOAD_FOLDER = 'payment_receipts'
FILE_STATE = 'file_state.json'

PHASES = {
    "Phase 1: Contract": ["Signed Contract", "Registration Form"],
    "Phase 2: LC Payment (if applicable)": ["LC Document"],
    "Phase 3: Cleaning & Sample Approval": ["Sample Approval", "Bank Permit", "Cleaning Certificate"],
    "Phase 4: Booking & Certification": ["Shipping Line Booking", "Container Seal", "Railway Payment"],
    "Phase 5: Export Docs": ["Commercial Invoice", "Packing List", "Bill of Lading", "Waybill", "VGM", "Truck Info", "Company Certificate"],
    "Phase 6: Buyer Docs": ["Phytosanitary Certificate", "Fumigation Certificate", "Quality Certificate", "Weight Certificate", "ICO Certificate", "COO Certificate", "Beneficiary Certificate"],
    "Phase 7: Payment & Handover": ["Bank Advice", "Transit Agreement", "Final Invoice"]
}

# Initialize data files with proper structure
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
    
if not os.path.exists(PAYMENT_UPLOAD_FOLDER):
    os.makedirs(PAYMENT_UPLOAD_FOLDER)

for db_file in [USER_DB, ORGANIZATION_DB, DATA_FILE, FILE_STATE, PAYMENT_DB]:
    if not os.path.exists(db_file):
        with open(db_file, 'w') as f:
            json.dump({}, f)

if 'logged_in' not in st.session_state:
    st.session_state.update({
        'logged_in': False,
        'username': None,
        'role': None,
        'email': None,
        'organization': None,
        'payment_verified': False
    })

# ---------------------- UTILITY FUNCTIONS ----------------------
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password, hashed):
    return hashlib.sha256(password.encode()).hexdigest() == hashed

def send_email(recipient, subject, body):
    try:
        sender_email = "your_email@gmail.com"
        sender_password = "your_app_password"
        msg = EmailMessage()
        msg['Subject'] = subject
        msg['From'] = sender_email
        msg['To'] = recipient
        msg.set_content(body)

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Email sending failed: {str(e)}")
    return False

# ---------------------- DATA MANAGEMENT ----------------------
def load_organizations():
    try:
        with open(ORGANIZATION_DB, 'r') as f:
            data = json.load(f)
            return {k: v for k, v in data.items() if isinstance(v, dict)}
    except:
        return {}

def save_organizations(orgs):
    with open(ORGANIZATION_DB, 'w') as f:
        json.dump(orgs, f, indent=2)

def load_users():
    try:
        with open(USER_DB, 'r') as f:
            data = json.load(f)
            return {k: v for k, v in data.items() if isinstance(v, dict)}
    except:
        return {}

def save_users(users):
    with open(USER_DB, 'w') as f:
        json.dump(users, f, indent=2)

def load_payments():
    try:
        with open(PAYMENT_DB, 'r') as f:
            data = json.load(f)
            return {k: v for k, v in data.items() if isinstance(v, dict)}
    except:
        return {}

def save_payments(payments):
    with open(PAYMENT_DB, 'w') as f:
        json.dump(payments, f, indent=2)

def load_file_state():
    try:
        with open(FILE_STATE, 'r') as f:
            data = json.load(f)
            return {k: v for k, v in data.items() if isinstance(v, dict)}
    except:
        return {}

def save_file_state(state):
    with open(FILE_STATE, 'w') as f:
        json.dump(state, f, indent=2)

def load_data():
    try:
        with open(DATA_FILE, 'r') as f:
            data = json.load(f)
            return {k: v for k, v in data.items() if isinstance(v, dict)}
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f, indent=2)

# ---------------------- PAYMENT FUNCTIONS ----------------------
def check_payment_status(organization):
    if not organization:
        return False
        
    payments = load_payments()
    org_payment = payments.get(organization, {})
    
    if not org_payment:
        return False
    
    expiry_date_str = org_payment.get('expiry_date')
    if not expiry_date_str:
        return False
    
    try:
        expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d").date()
        return expiry_date >= date.today() and org_payment.get('verified', False)
    except:
        return False

def process_payment(organization, payment_method, receipt_file, amount=100):
    if not organization:
        st.error("Organization information is missing")
        return False
        
    payments = load_payments()
    
    # Generate expiry date 1 year from now
    expiry_date = (date.today() + timedelta(days=365)).strftime("%Y-%m-%d")
    
    # Save receipt file
    receipt_filename = f"{organization}_{uuid.uuid4()}_{receipt_file.name}"
    receipt_path = os.path.join(PAYMENT_UPLOAD_FOLDER, receipt_filename)
    
    with open(receipt_path, "wb") as f:
        f.write(receipt_file.getbuffer())
    
    # Record payment
    payments[organization] = {
        'payment_method': payment_method,
        'amount': amount,
        'receipt_file': receipt_filename,
        'payment_date': date.today().strftime("%Y-%m-%d"),
        'expiry_date': expiry_date,
        'verified': True  # Auto-verify for demo purposes
    }
    
    save_payments(payments)
    return True

# ---------------------- CORE FUNCTIONALITY ----------------------
def create_organization(name, creator_username):
    orgs = load_organizations()
    org_id = str(uuid.uuid4())
    orgs[org_id] = {
        'name': name,
        'creator': creator_username,
        'members': [creator_username],
        'created_at': datetime.now().isoformat(),
        'payment_status': 'pending'
    }
    save_organizations(orgs)
    return org_id

def submit_phase(user, phase, organization):
    data = load_data()
    org_key = f"{organization}_{user}"
    
    if org_key not in data:
        data[org_key] = {'submitted_phases': []}
    if phase not in data[org_key].get('submitted_phases', []):
        data[org_key]['submitted_phases'].append(phase)
        save_data(data)
        st.success(f"{phase} has been submitted.")

# ---------------------- UI COMPONENTS ----------------------
def display_sidebar():
    st.sidebar.title("Navigation")
    if st.session_state.username:
        st.sidebar.write(f"👤 User: {st.session_state.username}")
    if st.session_state.organization:
        st.sidebar.write(f"🏢 Org: {st.session_state.organization}")
    if st.session_state.role:
        st.sidebar.write(f"👔 Role: {st.session_state.role}")
    
    if st.session_state.get('payment_verified', False):
        st.sidebar.success("✅ Payment Verified")
    else:
        st.sidebar.warning("⚠️ Payment Pending")
    
    if st.sidebar.button("Log Out"):
        st.session_state.update({
            'logged_in': False,
            'username': None,
            'role': None,
            'email': None,
            'organization': None,
            'payment_verified': False
        })
        st.rerun()

def payment_verification_page(organization):
    if not organization:
        st.error("Organization information is missing. Please contact support.")
        return
    
    st.title("Payment Verification Required")
    st.warning(f"Your organization ({organization}) needs to complete payment before you can access the system.")
    
    payments = load_payments()
    org_payment = payments.get(organization, {})
    
    if org_payment and org_payment.get('verified', False):
        if check_payment_status(organization):
            st.session_state.payment_verified = True
            st.success("Payment verified! You can now access the system.")
            st.rerun()
        else:
            st.error("Your organization's payment has expired. Please renew.")
    
    st.subheader("Payment Options")
    payment_method = st.radio("Select Payment Method", ["Bank Transfer", "PayPal"])
    
    if payment_method == "Bank Transfer":
        st.markdown("""
        **Bank Transfer Details:**
        - Bank Name: Coffee Export Bank
        - Account Number: 123456789
        - SWIFT Code: CEBKUS33
        - Amount: $100 (1 year subscription)
        """)
    else:  # PayPal
        st.markdown("""
        **PayPal Payment:**
        - Email: payments@coffeeexport.com
        - Amount: $100 (1 year subscription)
        """)
    
    st.subheader("Upload Payment Receipt")
    receipt_file = st.file_uploader("Upload your payment receipt (PDF or Image)", 
                                 type=["pdf", "jpg", "png", "jpeg"])
    
    if st.button("Submit Payment"):
        if not receipt_file:
            st.error("Please upload your payment receipt")
            return
            
        if process_payment(organization, payment_method, receipt_file):
            st.success("Payment receipt submitted! Your access will be activated after verification.")
            st.session_state.payment_verified = True
            st.rerun()
        else:
            st.error("Failed to process payment. Please try again.")

def staff_view(organization):
    if not organization:
        st.error("Organization information is missing")
        return
    
    if not check_payment_status(organization):
        payment_verification_page(organization)
        return
    
    st.session_state.payment_verified = True
    st.header(f"📄 Document Submission - {organization}")
    file_state = load_file_state()
    username = st.session_state.username
    org_key = f"{organization}_{username}"
    
    if org_key not in file_state:
        file_state[org_key] = {}

    # Document Status Alerts
    st.subheader("📢 Document Status")
    alert_cols = st.columns(2)
    
    with alert_cols[0]:
        st.markdown("**✅ Uploaded Documents**")
        uploaded_docs = []
        for phase, docs in file_state.get(org_key, {}).items():
            if isinstance(docs, dict):
                for doc in docs:
                    uploaded_docs.append(f"{doc} ({phase})")
        
        if uploaded_docs:
            for doc in uploaded_docs:
                st.success(f"- {doc}")
        else:
            st.info("No documents uploaded yet")
    
    with alert_cols[1]:
        st.markdown("**❌ Missing Documents**")
        missing_docs = []
        for phase, docs in PHASES.items():
            for doc in docs:
                if not file_state.get(org_key, {}).get(phase, {}).get(doc):
                    missing_docs.append(f"{doc} ({phase})")
        
        if missing_docs:
            for doc in missing_docs:
                st.error(f"- {doc}")
        else:
            st.success("All documents uploaded!")

    # Document Submission Interface
    st.subheader("📤 Submit Documents")
    for phase, docs in PHASES.items():
        with st.expander(phase):
            if phase not in file_state[org_key]:
                file_state[org_key][phase] = {}

            for doc in docs:
                key = f"{org_key}_{phase}_{doc}"
                uploaded_file = st.file_uploader(f"Upload {doc}", type=["pdf", "jpg", "png"], key=key)
                if uploaded_file:
                    save_path = os.path.join(UPLOAD_FOLDER, f"{org_key}_{uuid.uuid4()}_{uploaded_file.name}")
                    with open(save_path, "wb") as f:
                        f.write(uploaded_file.read())
                    file_state[org_key][phase][doc] = {
                        "filename": uploaded_file.name,
                        "upload_date": datetime.now().isoformat()
                    }
                    save_file_state(file_state)
                    st.success(f"Uploaded {doc}")

            # Due Date Tracking
            due_key = f"{org_key}_{phase}_due"
            due_date = st.date_input("Due Date", key=due_key)
            if due_date:
                days_remaining = (due_date - date.today()).days
                if days_remaining < 0:
                    st.error(f"⚠️ Overdue by {-days_remaining} days!")
                elif days_remaining <= 3:
                    st.warning(f"⚠️ Due in {days_remaining} days!")
                else:
                    st.info(f"⏳ Due in {days_remaining} days")

            if st.button(f"Submit {phase}"):
                submit_phase(username, phase, organization)

    # Uploaded Documents List
    st.subheader("📋 Your Uploaded Documents")
    docs_data = []
    for phase, docs in file_state.get(org_key, {}).items():
        if not isinstance(docs, dict):
            continue
        for doc, meta in docs.items():
            if not isinstance(meta, dict):
                continue
            docs_data.append({
                "Phase": phase,
                "Document": doc,
                "Filename": meta.get("filename", "N/A"),
                "Upload Date": meta.get("upload_date", "N/A")[:16]
            })
    
    if docs_data:
        st.table(pd.DataFrame(docs_data))
    else:
        st.info("No documents uploaded yet")

def manager_view(organization):
    if not organization:
        st.error("Organization information is missing")
        return
    
    if not check_payment_status(organization):
        payment_verification_page(organization)
        return
    
    st.session_state.payment_verified = True
    st.header(f"📊 Manager Dashboard - {organization}")
    
    # Get all users in the organization
    users = load_users()
    org_users = [u for u, data in users.items() 
                if isinstance(data, dict) and data.get('organization') == organization]
    
    file_state = load_file_state()
    
    # Organization Overview
    st.subheader("Organization Overview")
    cols = st.columns(3)
    cols[0].metric("Total Members", len(org_users))
    
    # Payment Status
    payments = load_payments()
    org_payment = payments.get(organization, {})
    if org_payment:
        expiry_date = org_payment.get('expiry_date', 'N/A')
        days_left = (datetime.strptime(expiry_date, "%Y-%m-%d").date() - date.today()).days if expiry_date != 'N/A' else 0
        cols[1].metric("Payment Status", "Active" if check_payment_status(organization) else "Expired")
        cols[2].metric("Days Remaining", days_left if days_left > 0 else 0)
    
    # Staff Progress
    st.subheader("Staff Progress")
    progress_data = []
    for user in org_users:
        user_key = f"{organization}_{user}"
        user_phases = file_state.get(user_key, {})
        if not isinstance(user_phases, dict):
            user_phases = {}
        
        completed = len([p for p in PHASES if p in user_phases])
        last_activity = "Never"
        
        for phase in user_phases.values():
            if not isinstance(phase, dict):
                continue
            for meta in phase.values():
                if isinstance(meta, dict) and 'upload_date' in meta:
                    if last_activity == "Never" or meta['upload_date'] > last_activity:
                        last_activity = meta['upload_date']
        
        progress_data.append({
            "Staff": user,
            "Completed": f"{completed}/{len(PHASES)}",
            "Last Activity": last_activity[:16] if last_activity != "Never" else last_activity
        })
    
    st.table(pd.DataFrame(progress_data))
    
    # Document Status
    st.subheader("Document Status")
    
    for phase, docs in PHASES.items():
        st.markdown(f"**{phase}**")
        
        for doc in docs:
            # Count uploaded documents
            uploaded = sum(
                1 for user in org_users 
                if file_state.get(f"{organization}_{user}", {}).get(phase, {}).get(doc)
            )
            
            # Determine status
            if uploaded == len(org_users):
                status_icon = "✅"
                status_color = "green"
                status_text = "All uploaded"
            elif uploaded > 0:
                status_icon = "🟡"
                status_color = "orange"
                status_text = f"{uploaded}/{len(org_users)} uploaded"
            else:
                status_icon = "❌"
                status_color = "red"
                status_text = "None uploaded"
            
            # Display status
            st.markdown(
                f"{status_icon} <span style='color:{status_color}'>{doc}: {status_text}</span>", 
                unsafe_allow_html=True
            )
            
            # Show details if not all uploaded
            if uploaded < len(org_users):
                with st.expander("Details"):
                    submitted = [
                        user for user in org_users 
                        if file_state.get(f"{organization}_{user}", {}).get(phase, {}).get(doc)
                    ]
                    not_submitted = [user for user in org_users if user not in submitted]
                    
                    if submitted:
                        st.markdown("✅ **Submitted by:**")
                        st.write(", ".join(submitted))
                    
                    if not_submitted:
                        st.markdown("❌ **Pending from:**")
                        st.write(", ".join(not_submitted))
        
        st.write("---")

# ---------------------- AUTHENTICATION ----------------------
def signup():
    st.subheader("Create Account")
    tab1, tab2 = st.tabs(["Join Existing Organization", "Create New Organization"])
    
    with tab1:
        st.write("Join an existing organization")
        orgs = load_organizations()
        existing_orgs = [org['name'] for org in orgs.values() 
                        if isinstance(org, dict) and 'name' in org]
        
        if not existing_orgs:
            st.info("No organizations exist yet. Create one using the other tab.")
        else:
            username = st.text_input("Username", key="join_username").strip()
            email = st.text_input("Email", key="join_email").strip()
            password = st.text_input("Password", type="password", key="join_password")
            role = st.selectbox("Role", ROLES, key="join_role")
            organization = st.selectbox("Organization", existing_orgs, key="join_org")
            
            if st.button("Join Organization"):
                if not all([username, email, password]):
                    st.error("Please fill all fields")
                    return
                
                users = load_users()
                if username in users:
                    st.error("Username already exists")
                    return
                
                # Check if email exists
                email_exists = any(
                    isinstance(data, dict) and data.get('email') == email 
                    for data in users.values()
                )
                
                if email_exists:
                    st.error("Email already registered")
                    return
                
                # Create new user
                users[username] = {
                    'password': hash_password(password),
                    'role': role,
                    'email': email,
                    'organization': organization,
                    'active': False
                }
                save_users(users)
                
                # Add to organization members
                for org_id, org_data in orgs.items():
                    if isinstance(org_data, dict) and org_data.get('name') == organization:
                        if 'members' not in org_data:
                            org_data['members'] = []
                        if username not in org_data['members']:
                            org_data['members'].append(username)
                        save_organizations(orgs)
                        break
                
                st.success("Account created! Please login")
    
    with tab2:
        st.write("Create a new organization")
        username = st.text_input("Username", key="create_username").strip()
        email = st.text_input("Email", key="create_email").strip()
        password = st.text_input("Password", type="password", key="create_password")
        organization = st.text_input("Organization Name", key="new_org_name").strip()
        role = st.selectbox("Your Role", ROLES, key="create_role")
        
        if st.button("Create Organization"):
            if not all([username, email, password, organization]):
                st.error("Please fill all fields")
                return
                
            users = load_users()
            if username in users:
                st.error("Username already exists")
                return
                
            # Check if email exists
            email_exists = any(
                isinstance(data, dict) and data.get('email') == email 
                for data in users.values()
            )
            
            if email_exists:
                st.error("Email already registered")
                return
            
            # Create user
            users[username] = {
                'password': hash_password(password),
                'role': role,
                'email': email,
                'organization': organization,
                'active': False
            }
            save_users(users)
            
            # Create organization
            create_organization(organization, username)
            
            st.success(f"Organization {organization} created! Please login and complete payment")

def login():
    st.subheader("Login")
    username = st.text_input("Username").strip()
    password = st.text_input("Password", type="password")
    role = st.selectbox("Role", ROLES, key="login_role")

    if st.button("Login"):
        users = load_users()
        user_data = users.get(username)
        
        if (user_data and isinstance(user_data, dict) and 
            check_password(password, user_data.get('password', '')) and
            user_data.get('role') == role):
            
            organization = user_data.get('organization')
            if not organization:
                st.error("Your account is not associated with any organization")
                return
            
            payment_verified = check_payment_status(organization)
            
            st.session_state.update({
                'logged_in': True,
                'username': username,
                'role': role,
                'email': user_data.get('email'),
                'organization': organization,
                'payment_verified': payment_verified
            })
            st.rerun()
        else:
            st.error("Invalid credentials or role mismatch")

# ---------------------- MAIN APP ----------------------
def main():
    st.set_page_config(
        page_title="Coffee Export Tracker",
        page_icon="☕",
        layout="wide"
    )

    st.title("☕ Multi-Organization Coffee Export Tracker")
    st.markdown("---")

    if not st.session_state.logged_in:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        with tab1:
            login()
        with tab2:
            signup()
    else:
        display_sidebar()
        if not st.session_state.organization:
            st.error("Organization information is missing. Please contact support.")
            if st.button("Log Out"):
                st.session_state.update({
                    'logged_in': False,
                    'username': None,
                    'role': None,
                    'email': None,
                    'organization': None,
                    'payment_verified': False
                })
                st.rerun()
        elif not st.session_state.payment_verified:
            payment_verification_page(st.session_state.organization)
        else:
            if st.session_state.role == 'staff':
                staff_view(st.session_state.organization)
            elif st.session_state.role == 'manager':
                manager_view(st.session_state.organization)

if __name__ == "__main__":
    main()




