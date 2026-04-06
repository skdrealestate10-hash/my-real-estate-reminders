import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os
import pytz
import time

# --- 1. CONFIGURATION ---
try:
    GMAIL_USER = st.secrets["GMAIL_USER"]
    GMAIL_PASSWORD = st.secrets["GMAIL_PASSWORD"]
except:
    st.error("Secrets Error: Add GMAIL_USER and GMAIL_PASSWORD to Streamlit Settings.")
    st.stop()

CSV_FILE = 'list.csv'
COLUMNS = ['Task', 'Recipient', 'Deadline', 'Time', 'DaysBefore', 'Status', 'Recurrence', 'CreatedToken']
UAE_TZ = pytz.timezone('Asia/Dubai')

# --- 2. INITIALIZATION ---
if "page" not in st.session_state: st.session_state.page = "dashboard"
# This token identifies THIS specific moment/session
if "session_token" not in st.session_state: 
    st.session_state.session_token = str(time.time())

if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)

# --- 3. UI SETUP ---
st.set_page_config(page_title="SKD Reminder Center", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .card { background: white; padding: 20px; border-radius: 12px; border-left: 6px solid #8B0000; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 15px; }
    .tag-active { background: #FFF5F5; color: #8B0000; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.7rem; }
    .tag-sent { background: #F0FFF4; color: #22543D; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.7rem; }
    .footer { text-align: center; padding: 20px; color: #64748B; font-size: 0.8rem; border-top: 1px solid #EEE; margin-top: 50px; }
    </style>
    """, unsafe_allow_html=True)

df = pd.read_csv(CSV_FILE)

# --- 4. DASHBOARD PAGE ---
if st.session_state.page == "dashboard":
    st.write(f"### SKD Reminder Dashboard | ⏰ {datetime.now(UAE_TZ).strftime('%I:%M %p')}")
    
    if st.button("➕ Create New", type="primary"):
        st.session_state.page = "create"
        st.rerun()

    if len(df) == 0: st.info("No reminders set.")
    for i, row in df[::-1].iterrows():
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns([3, 2, 0.5])
            with c1:
                tag = "tag-active" if str(row['Status']) == 'Active' else "tag-sent"
                st.markdown(f'<span class="{tag}">{str(row["Status"]).upper()}</span> **{row["Task"]}**', unsafe_allow_html=True)
                st.caption(f"To: {row['Recipient']}")
            with c2:
                st.write(f"📅 {row['Deadline']} | ⏰ {row['Time']}")
            with c3:
                if st.button("🗑️", key=f"del_{i}"):
                    df.drop(i).to_csv(CSV_FILE, index=False)
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# --- 5. CREATE PAGE ---
elif st.session_state.page == "create":
    if st.button("← Back"):
        st.session_state.page = "dashboard"
        st.rerun()
    with st.form("add_form"):
        t = st.text_input("Task Name")
        e = st.text_input("Recipient Email")
        d = st.date_input("Date", datetime.now(UAE_TZ))
        tm = st.text_input("Time (e.g. 10:30 AM)", value=(datetime.now(UAE_TZ) + timedelta(minutes=5)).strftime("%I:%M %p"))
        r = st.selectbox("Repeat", ["None", "Weekly", "Monthly"])
        if st.form_submit_button("SAVE"):
            if t and e:
                # We tag this row with the current session token
                new_row = pd.DataFrame([[t, e, str(d), tm, 0, 'Active', r, st.session_state.session_token]], columns=COLUMNS)
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_csv(CSV_FILE, index=False)
                st.session_state.page = "dashboard"
                st.rerun()

# --- 6. THE PRECISION ENGINE (RE-BUILT) ---
def run_automation_engine():
    # Reload DF to get the newly saved row
    df_engine = pd.read_csv(CSV_FILE)
    now_uae = datetime.now(UAE_TZ)
    today_str = now_uae.strftime('%Y-%m-%d')
    current_time_str = now_uae.strftime('%I:%M %p')
    
    changed = False

    for index, row in df_engine.iterrows():
        if str(row['Status']) == 'Active':
            # SAFETY CHECK: If this row was created in THIS exact button click, SKIP IT.
            # It can only be sent on the NEXT refresh.
            if str(row.get('CreatedToken')) == st.session_state.session_token:
                continue

            is_today = str(row['Deadline']) == today_str
            is_past = str(row['Deadline']) < today_str
            
            # Match the exact minute or handle overdue
            if is_past or (is_today and str(row['Time']) == current_time_str):
                try:
                    recipients = [addr.strip() for addr in str(row['Recipient']).split(',')]
                    msg = MIMEText(f"SKD Reminder: {row['Task']}\nDue: {row['Deadline']} at {row['Time']}")
                    msg['Subject'] = f"🔔 SKD REMINDER: {row['Task']}"
                    msg['From'] = GMAIL_USER
                    msg['To'] = ", ".join(recipients)
                    
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                        server.login(GMAIL_USER, GMAIL_PASSWORD)
                        server.send_message(msg)
                    
                    df_engine.at[index, 'Status'] = 'Sent'
                    changed = True
                except: continue
                
    if changed:
        df_engine.to_csv(CSV_FILE, index=False)

# This runs only AFTER the UI is handled
run_automation_engine()

st.markdown('<div class="footer"><strong>SKD REAL ESTATE</strong><br>Developed by Yared</div>', unsafe_allow_html=True)
