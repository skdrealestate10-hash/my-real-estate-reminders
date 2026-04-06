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

# --- 2. HEARTBEAT ---
st_autorefresh(interval=60 * 1000, key="skd_heartbeat")

CSV_FILE = 'list.csv'
COLUMNS = ['Task', 'Recipient', 'Deadline', 'Time', 'Status', 'Recurrence', 'AddedAt']
UAE_TZ = pytz.timezone('Asia/Dubai')

# --- 3. CSV REPAIR ---
def load_and_fix_csv():
    if not os.path.exists(CSV_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
    try:
        df = pd.read_csv(CSV_FILE)
        if 'Deadline' not in df.columns:
            os.remove(CSV_FILE)
            df = pd.DataFrame(columns=COLUMNS)
            df.to_csv(CSV_FILE, index=False)
        return df
    except:
        return pd.DataFrame(columns=COLUMNS)

# --- 4. LUXURY STYLING ---
st.set_page_config(page_title="SKD | Email Schedule App", layout="wide", page_icon="📧")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;700;800&display=swap');
    .stApp { background-color: #0F172A; color: #FFFFFF; font-family: 'Inter', sans-serif; }
    
    .modern-h1 { 
        font-size: 2.8rem; font-weight: 800; letter-spacing: -1px; margin-bottom: 10px;
        background: linear-gradient(90deg, #FFFFFF, #D4AF37);
        -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    }
    
    .reminder-card {
        background: #1E293B; border-radius: 16px; padding: 25px;
        margin-bottom: 20px; border-left: 8px solid #D4AF37;
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.3);
    }
    .metric-box {
        background: rgba(30, 41, 59, 0.6); border: 1px solid #334155;
        border-radius: 12px; padding: 20px; text-align: center;
    }
    .time-display { font-size: 2.5rem; font-weight: 800; color: #D4AF37 !important; line-height: 1; }
    .gold-text { color: #D4AF37 !important; font-weight: 600; }
    .sub-text { color: #94A3B8 !important; font-size: 0.8rem; letter-spacing: 1px; font-weight: 700; }
    
    .live-dot {
        height: 10px; width: 10px; background-color: #4ADE80;
        border-radius: 50%; display: inline-block; margin-right: 8px;
        animation: blink 1.5s infinite;
    }
    @keyframes blink { 0% { opacity: 1; } 50% { opacity: 0; } 100% { opacity: 1; } }

    .footer {
        text-align: center; padding: 40px; color: #64748B !important;
        font-size: 0.85rem; border-top: 1px solid #1E293B; margin-top: 50px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 5. ENGINE ---
def run_automation_engine():
    df_logic = load_and_fix_csv()
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
                
                if (str(row.get('Deadline')) < today_str) or (is_today and sched_time_str <= current_time_str):
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

# --- 6. DASHBOARD UI ---
df = load_and_fix_csv()

if "page" not in st.session_state: st.session_state.page = "dashboard"

if st.session_state.page == "dashboard":
    # --- BRAND HEADER ---
    logo_url = "https://raw.githubusercontent.com/YaredAnbesa/my-real-estate-reminders/main/logo.jpeg"
    
    # Left column for the logo, wider space for the title
    c_logo, c_title = st.columns([1, 3])
    with c_logo:
        st.image(logo_url, use_container_width=True)
    
    st.markdown("<h1 class='modern-h1'>SKD EMAIL SCHEDULE APP</h1>", unsafe_allow_html=True)
    st.markdown("""
        <div style="display: flex; align-items: center; gap: 8px; margin-bottom: 25px;">
            <div class="live-dot"></div>
            <span style="color:#4ADE80; font-size:0.75rem; font-weight:800; text-transform: uppercase;">System Monitoring Active</span>
        </div>
    """, unsafe_allow_html=True)

    st.divider()

    # METRICS
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"<div class='metric-box'><div class='sub-text'>ACTIVE</div><div class='time-display'>{len(df[df['Status'] == 'Active'])}</div></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='metric-box'><div class='sub-text'>SENT</div><div class='time-display'>{len(df[df['Status'] == 'Sent'])}</div></div>", unsafe_allow_html=True)
    with m3:
        st.markdown(f"<div class='metric-box'><div class='sub-text'>DUBAI TIME</div><div class='time-display'>{datetime.now(UAE_TZ).strftime('%I:%M %p')}</div></div>", unsafe_allow_html=True)

    st.divider()

    if st.button("➕ CREATE NEW EMAIL SCHEDULE", type="primary", use_container_width=True):
        st.session_state.page = "create"
        st.rerun()

    for i, row in df[::-1].iterrows():
        status = str(row['Status'])
        border_color = "#D4AF37" if status == 'Active' else "#4ADE80"
        with st.container():
            st.markdown(f"""
            <div class="reminder-card" style="border-left-color: {border_color};">
                <div style="display:flex; justify-content:space-between; margin-bottom:12px;">
                    <span class="gold-text">{status.upper()}</span>
                    <span class="sub-text">{row['Recurrence']}</span>
                </div>
                <h2 style="color:white; margin:0;">{row['Task']}</h2>
                <p style="color:#CBD5E1; margin:10px 0;">To: {row['Recipient']}<br>Due: {row['Deadline']} @ {row['Time']}</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"🗑️ Delete #{i}", key=f"del_{i}", use_container_width=True):
                df.drop(i).to_csv(CSV_FILE, index=False)
                st.rerun()

elif st.session_state.page == "create":
    st.markdown("<h1 class='modern-h1'>New Schedule</h1>", unsafe_allow_html=True)
    if st.button("← Back"):
        st.session_state.page = "dashboard"
        st.rerun()
    
    with st.form("skd_form"):
        task = st.text_input("Task Description")
        email = st.text_input("Recipient Email")
        c1, c2 = st.columns(2)
        date_sel = c1.date_input("Date", datetime.now(UAE_TZ))
        time_sel = c2.text_input("Time (e.g. 02:00 PM)", value=(datetime.now(UAE_TZ) + timedelta(minutes=15)).strftime("%I:%M %p"))
        recur = st.selectbox("Label", ["One-Time", "Weekly", "Monthly"])
        
        if st.form_submit_button("ACTIVATE"):
            if task and email:
                new = pd.DataFrame([[task, email, str(date_sel), time_sel, 'Active', recur, time.time()]], columns=COLUMNS)
                pd.concat([load_and_fix_csv(), new], ignore_index=True).to_csv(CSV_FILE, index=False)
                st.session_state.page = "dashboard"
                st.rerun()

run_automation_engine()
st.markdown(f"<div class='footer'>CREATED BY YARED ANBESA<br>SKD APP © {datetime.now().year}</div>", unsafe_allow_html=True)
