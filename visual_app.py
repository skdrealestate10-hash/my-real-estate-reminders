import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os
import pytz

# --- 1. CONFIGURATION ---
try:
    GMAIL_USER = st.secrets["GMAIL_USER"]
    GMAIL_PASSWORD = st.secrets["GMAIL_PASSWORD"]
except:
    st.error("Credential Error: Please check Streamlit Secrets.")
    st.stop()

CSV_FILE = 'list.csv'
COLUMNS = ['Task', 'Recipient', 'Deadline', 'Time', 'DaysBefore', 'Status', 'Recurrence']
UAE_TZ = pytz.timezone('Asia/Dubai')

# --- 2. UI & STYLE ---
st.set_page_config(page_title="SKD Reminder Center", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .header-box { text-align: left; padding: 15px; background: white; border-bottom: 3px solid #D4AF37; }
    .card { background: white; padding: 20px; border-radius: 12px; border-left: 6px solid #8B0000; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 15px; }
    .tag-active { background: #FFF5F5; color: #8B0000; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.7rem; border: 1px solid #8B0000; }
    .tag-sent { background: #F0FFF4; color: #22543D; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.7rem; border: 1px solid #22543D; }
    .footer-container { text-align: center; padding: 30px 0; margin-top: 50px; border-top: 1px solid #E2E8F0; color: #64748B; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
df = pd.read_csv(CSV_FILE)

if "page" not in st.session_state: st.session_state.page = "dashboard"

# --- 3. PAGES ---
if st.session_state.page == "dashboard":
    # Header & Stats
    now_uae = datetime.now(UAE_TZ)
    st.subheader(f"SKD Control Center | ⏰ {now_uae.strftime('%I:%M %p')}")
    
    if st.button("➕ New Email", type="primary"):
        st.session_state.page = "create"
        st.rerun()

    for i, row in df[::-1].iterrows():
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns([3, 2, 0.5])
            with c1:
                style = "tag-active" if row['Status'] == 'Active' else "tag-sent"
                st.markdown(f'<span class="{style}">{row["Status"]}</span> **{row["Task"]}**', unsafe_allow_html=True)
                st.caption(f"To: {row['Recipient']}")
            with c2:
                st.write(f"📅 {row['Deadline']} | ⏰ {row['Time']}")
            with c3:
                if st.button("🗑️", key=f"del_{i}"):
                    df.drop(i).to_csv(CSV_FILE, index=False)
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == "create":
    if st.button("← Back"):
        st.session_state.page = "dashboard"
        st.rerun()
    with st.form("add"):
        t = st.text_input("Task Name")
        e = st.text_input("Recipient Email")
        d = st.date_input("Date", datetime.now(UAE_TZ))
        tm = st.text_input("Time (e.g. 04:30 PM)", value=(datetime.now(UAE_TZ) + timedelta(minutes=5)).strftime("%I:%M %p"))
        r = st.selectbox("Repeat", ["None", "Weekly", "Monthly"])
        if st.form_submit_button("SAVE"):
            if t and e:
                new_row = pd.DataFrame([[t, e, str(d), tm, 0, 'Active', r]], columns=COLUMNS)
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_csv(CSV_FILE, index=False)
                st.session_state.page = "dashboard"
                st.rerun()

# --- 4. THE PRECISION ENGINE ---
def run_automation_engine():
    df_bg = pd.read_csv(CSV_FILE)
    now_uae = datetime.now(UAE_TZ)
    today_str = now_uae.strftime('%Y-%m-%d')
    current_time_str = now_uae.strftime('%I:%M %p') # Matches "04:30 PM" format
    
    changed = False

    for index, row in df_bg.iterrows():
        if str(row['Status']) == 'Active':
            # STAGE 1: Check Date
            is_today = str(row['Deadline']) == today_str
            is_past = str(row['Deadline']) < today_str
            
            # STAGE 2: Precision Time Check
            # It ONLY triggers if the strings match exactly (Minute-to-Minute)
            # Or if the date is already passed (Safety for missed emails)
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
                    
                    # Mark as Sent to prevent double-firing within the same minute
                    df_bg.at[index, 'Status'] = 'Sent'
                    changed = True
                except: continue
                
    if changed:
        df_bg.to_csv(CSV_FILE, index=False)

# Run engine after UI finishes rendering
run_automation_engine()

# --- 5. PROFESSIONAL FOOTER ---
st.markdown("""
    <div class="footer-container">
        <strong>SKD REAL ESTATE BROKERAGE</strong><br>
        Digital Reminder Control Center • Developed by Yared
    </div>
    """, unsafe_allow_html=True)
