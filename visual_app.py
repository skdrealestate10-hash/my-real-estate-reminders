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

# --- 3. HIGH-VISIBILITY LUXURY STYLING ---
st.set_page_config(page_title="SKD Email Schedule App", layout="wide", page_icon="📧")

st.markdown("""
    <style>
    .stApp { background-color: #0F172A; color: #FFFFFF; }
    .reminder-card {
        background: #1E293B; border-radius: 12px; padding: 25px;
        margin-bottom: 20px; border-left: 6px solid #D4AF37;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4);
    }
    h1, h2, h3, p, span, div { color: #FFFFFF !important; }
    .gold-text { color: #D4AF37 !important; font-weight: bold; }
    .sub-text { color: #94A3B8 !important; font-size: 0.95rem; }
    .time-display { font-size: 2.2rem; font-weight: 800; color: #D4AF37 !important; }
    .live-dot {
        height: 10px; width: 10px; background-color: #4ADE80;
        border-radius: 50%; display: inline-block; margin-right: 10px;
        animation: blink 1.5s infinite;
    }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0; } 100% { opacity: 1; } }
    .footer {
        text-align: center; padding: 40px; color: #94A3B8 !important;
        font-size: 0.9rem; border-top: 1px solid #334155; margin-top: 60px;
    }
    .metric-box {
        background: #1E293B; border: 1px solid #334155; border-radius: 10px;
        padding: 15px; text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. THE ENGINE (RESTORED TO WORKING STATE) ---
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
            # 120-second safety buffer
            added_at = float(row.get('AddedAt', 0))
            if (now_ts - added_at) < 120: continue 

            try:
                # Basic string comparison for safety
                sched_time_str = str(row.get('Time'))
                current_time_str = now_uae.strftime('%I:%M %p')
                
                is_today = str(row.get('Deadline')) == today_str
                is_past_day = str(row.get('Deadline')) < today_str
                
                # Check if time has arrived or passed
                if is_past_day or (is_today and sched_time_str <= current_time_str):
                    # SEND EMAIL
                    recipients = [addr.strip() for addr in str(row['Recipient']).split(',')]
                    msg = MIMEText(f"SKD Reminder: {row['Task']}\nDue: {row['Deadline']} at {row['Time']}")
                    msg['Subject'] = f"🔔 SKD SCHEDULED: {row['Task']}"
                    msg['From'] = GMAIL_USER
                    msg['To'] = ", ".join(recipients)
                    
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                        server.login(GMAIL_USER, GMAIL_PASSWORD)
                        server.send_message(msg)
                    
                    # Mark as Sent (Simple Logic)
                    df_logic.at[index, 'Status'] = 'Sent'
                    changed = True
            except: continue
            
    if changed: df_logic.to_csv(CSV_FILE, index=False)

# --- 5. DASHBOARD UI ---
if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
df = pd.read_csv(CSV_FILE)

if "page" not in st.session_state: st.session_state.page = "dashboard"

if st.session_state.page == "dashboard":
    # 1. UPDATE THIS URL IF YOUR REPO NAME CHANGES
    # Currently: YaredAnbesa / my-real-estate-reminders / logo.jpeg
    logo_url = "https://raw.githubusercontent.com/YaredAnbesa/my-real-estate-reminders/main/logo.jpeg"
    
    st.markdown(f"""
    <div style="display: flex; align-items: center; gap: 20px; padding: 20px 0;">
        <div style="flex-shrink: 0;">
            <img src="{logo_url}" width="90" 
                 style="border-radius: 12px; border: 1px solid #334155; display: block;"
                 onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
            <div style="display: none; width: 90px; height: 90px; background: #1E293B; border: 1px solid #D4AF37; border-radius: 12px; align-items: center; justify-content: center;">
                <h2 style="color:#D4AF37; margin:0; font-size: 1.2rem;">SKD</h2>
            </div>
        </div>
        <div>
            <h1 class="modern-h1" style="margin:0; padding:0; line-height:1.1;">SKD EMAIL SCHEDULE APP</h1>
            <div style="display: flex; align-items: center; gap: 8px; margin-top: 8px;">
                <div class="live-dot"></div>
                <span style="color:#4ADE80; font-size:0.75rem; font-weight:800; letter-spacing:1px; text-transform: uppercase;">
                    System Live & Monitoring
                </span>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # --- REST OF THE DASHBOARD (METRICS & CARDS) ---
    active_count = len(df[df['Status'] == 'Active'])
    sent_count = len(df[df['Status'] == 'Sent'])
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"<div class='metric-box'><div class='sub-text'>ACTIVE</div><div class='time-display'>{active_count}</div></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='metric-box'><div class='sub-text'>SENT</div><div class='time-display'>{sent_count}</div></div>", unsafe_allow_html=True)
    with m3:
        st.markdown(f"<div class='metric-box'><div class='sub-text'>DUBAI TIME</div><div class='time-display'>{datetime.now(UAE_TZ).strftime('%I:%M %p')}</div></div>", unsafe_allow_html=True)

    st.divider()
    # (Rest of the loop for cards goes here...)

# --- 6. RUN ENGINE & FOOTER ---
run_automation_engine()
st.markdown(f"<div class='footer'>CREATED BY YARED ANBESA<br>SKD EMAIL SCHEDULE APP © {datetime.now().year}</div>", unsafe_allow_html=True)
