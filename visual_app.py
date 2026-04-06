import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os
import pytz
import time
from streamlit_autorefresh import st_autorefresh

# --- 1. CONFIG & SYSTEM ---
try:
    GMAIL_USER = st.secrets["GMAIL_USER"]
    GMAIL_PASSWORD = st.secrets["GMAIL_PASSWORD"]
except:
    st.error("Missing Secrets!")
    st.stop()

# --- 2. THE HEARTBEAT (AUTO-REFRESH EVERY 60 SECONDS) ---
st_autorefresh(interval=60 * 1000, key="skd_heartbeat")

CSV_FILE = 'list.csv'
COLUMNS = ['Task', 'Recipient', 'Deadline', 'Time', 'Status', 'Recurrence', 'AddedAt']
UAE_TZ = pytz.timezone('Asia/Dubai')

# --- 3. MODERN LUXURY STYLING ---
st.set_page_config(page_title="SKD | Email Schedule App", layout="wide", page_icon="📧")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');

    .stApp { 
        background-color: #0F172A; 
        color: #FFFFFF;
        font-family: 'Inter', sans-serif;
    }
    
    /* Modern Header Container */
    .header-container {
        display: flex;
        align-items: center;
        gap: 20px;
        padding: 20px 0;
        margin-bottom: 10px;
    }
    
    .logo-img {
        border-radius: 8px;
        object-fit: contain;
    }

    .modern-h1 {
        font-size: 2.2rem;
        font-weight: 800;
        letter-spacing: -1px;
        margin: 0;
        background: linear-gradient(90deg, #FFFFFF, #D4AF37);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    
    .reminder-card {
        background: #1E293B; 
        border-radius: 16px; 
        padding: 25px;
        margin-bottom: 20px; 
        border-left: 8px solid #D4AF37;
        box-shadow: 0 20px 25px -5px rgba(0, 0, 0, 0.2);
        transition: transform 0.2s;
    }
    
    .reminder-card:hover {
        transform: translateY(-5px);
    }

    .metric-box {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
    }

    .time-display { 
        font-size: 2.8rem; 
        font-weight: 800; 
        color: #D4AF37 !important;
        line-height: 1;
    }

    .gold-text { color: #D4AF37 !important; font-weight: 600; }
    .sub-text { color: #94A3B8 !important; font-size: 0.85rem; letter-spacing: 1px; font-weight: 700; }
    
    .footer {
        text-align: center; padding: 50px; color: #64748B !important;
        font-size: 0.8rem; border-top: 1px solid #1E293B; margin-top: 80px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. THE ENGINE (WORKING STATE) ---
def run_automation_engine():
    if not os.path.exists(CSV_FILE): return
    df_logic = pd.read_csv(CSV_FILE)
    if df_logic.empty: return
    
    now_uae = datetime.now(UAE_TZ)
    now_ts = time.time()
    today_str = now_uae.strftime('%Y-%m-%d')
    changed = False

    for index, row in df_logic.iterrows():
        if str(row.get('Status')) == 'Active':
            added_at = float(row.get('AddedAt', 0))
            if (now_ts - added_at) < 120: continue 

            try:
                sched_time_str = str(row.get('Time'))
                current_time_str = now_uae.strftime('%I:%M %p')
                
                is_today = str(row.get('Deadline')) == today_str
                is_past_day = str(row.get('Deadline')) < today_str
                
                if is_past_day or (is_today and sched_time_str <= current_time_str):
                    recipients = [addr.strip() for addr in str(row['Recipient']).split(',')]
                    msg = MIMEText(f"SKD Reminder: {row['Task']}\nDue: {row['Deadline']} at {row['Time']}")
                    msg['Subject'] = f"🔔 SKD SCHEDULED: {row['Task']}"
                    msg['From'] = GMAIL_USER
                    msg['To'] = ", ".join(recipients)
                    
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                        server.login(GMAIL_USER, GMAIL_PASSWORD)
                        server.send_message(msg)
                    
                    df_logic.at[index, 'Status'] = 'Sent'
                    changed = True
            except: continue
            
    if changed: df_logic.to_csv(CSV_FILE, index=False)

# --- 5. DASHBOARD UI ---
if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
df = pd.read_csv(CSV_FILE)

if "page" not in st.session_state: st.session_state.page = "dashboard"

# Modern Header with Logo
if st.session_state.page == "dashboard":
    logo_file = "logo.jpeg" # Ensure this exists in your GitHub root
    
    # Header Layout
    st.markdown(f"""
    <div class="header-container">
        <img src="https://raw.githubusercontent.com/YaredAnbesa/SKD_Email_App/main/logo.jpeg" width="80" class="logo-img">
        <div>
            <h1 class="modern-h1">SKD EMAIL SCHEDULE APP</h1>
            <div style="color:#4ADE80; font-size:0.8rem; font-weight:bold; letter-spacing:1px;">
                ● SYSTEM LIVE & MONITORING
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # COUNTERS
    active_count = len(df[df['Status'] == 'Active'])
    sent_count = len(df[df['Status'] == 'Sent'])
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"<div class='metric-box'><div class='sub-text'>ACTIVE TASKS</div><div class='time-display'>{active_count}</div></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='metric-box'><div class='sub-text'>EMAILS SENT</div><div class='time-display'>{sent_count}</div></div>", unsafe_allow_html=True)
    with m3:
        st.
