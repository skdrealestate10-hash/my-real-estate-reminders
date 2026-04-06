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

# --- 4. THE ENGINE (UNCHANGED CORE LOGIC + RECURRENCE) ---
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
                sched_time = datetime.strptime(str(row.get('Time')), '%I:%M %p').time()
                is_today = str(row.get('Deadline')) == today_str
                is_past_day = str(row.get('Deadline')) < today_str
                
                if is_past_day or (is_today and now_uae.time() >= sched_time):
                    # SEND EMAIL
                    recipients = [addr.strip() for addr in str(row['Recipient']).split(',')]
                    msg = MIMEText(f"SKD Reminder: {row['Task']}\nDue: {row['Deadline']} at {row['Time']}")
                    msg['Subject'] = f"🔔 SKD SCHEDULED: {row['Task']}"
                    msg['From'] = GMAIL_USER
                    msg['To'] = ", ".join(recipients)
                    
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                        server.login(GMAIL_USER, GMAIL_PASSWORD)
                        server.send_message(msg)
                    
                    # RECURRENCE LOGIC
                    repeat_type = str(row.get('Recurrence'))
                    if repeat_type != "None":
                        current_deadline = datetime.strptime(str(row['Deadline']), '%Y-%m-%d')
                        if repeat_type == "Weekly":
                            new_deadline = current_deadline + timedelta(days=7)
                        elif repeat_type == "Monthly":
                            # Simple 30-day add for Monthly rent
                            new_deadline = current_deadline + timedelta(days=30)
                        
                        df_logic.at[index, 'Deadline'] = new_deadline.strftime('%Y-%m-%d')
                        # Stay 'Active' for next cycle
                    else:
                        df_logic.at[index, 'Status'] = 'Sent'
                    
                    changed = True
            except: continue
    if changed: df_logic.to_csv(CSV_FILE, index=False)

# --- 5. DASHBOARD UI ---
if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
df = pd.read_csv(CSV_FILE)

if "page" not in st.session_state: st.session_state.page = "dashboard"

# LOGO LOAD (Safe Check)
logo_path = "logo.jpeg" # Matches your GitHub file name
if st.session_state.page == "dashboard":
    col_logo, col_title = st.columns([1, 4])
    with col_logo:
        if os.path.exists(logo_path):
            st.image(logo_path, width=120)
        else:
            st.markdown("<h2 style='color:#D4AF37;'>SKD</h2>", unsafe_allow_html=True)
    with col_title:
        st.markdown("<h1 style='margin-bottom:0;'>SKD EMAIL SCHEDULE APP</h1>", unsafe_allow_html=True)
        st.markdown("<div><span class='live-dot'></span>SYSTEM MONITORING ACTIVE</div>", unsafe_allow_html=True)

    st.divider()

    # COUNTERS
    active_count = len(df[df['Status'] == 'Active'])
    sent_count = len(df[df['Status'] == 'Sent'])
    
    m1, m2, m3 = st.columns(3)
    with m1:
        st.markdown(f"<div class='metric-box'><span class='sub-text'>ACTIVE</span><br><span class='time-display'>{active_count}</span></div>", unsafe_allow_html=True)
    with m2:
        st.markdown(f"<div class='metric-box'><span class='sub-text'>TOTAL SENT</span><br><span class='time-display'>{sent_count}</span></div>", unsafe_allow_html=True)
    with m3:
        st.markdown(f"<div class='metric-box'><span class='sub-text'>DUBAI TIME</span><br><span class='time-display'>{datetime.now(UAE_TZ).strftime('%I:%M %p')}</span></div>", unsafe_allow_html=True)

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
                <div style="display:flex; justify-content:space-between;">
                    <span class="gold-text">{status.upper()}</span>
                    <span class="sub-text">Repeat: {row['Recurrence']}</span>
                </div>
                <h2 style="margin:10px 0;">{row['Task']}</h2>
                <p>👤 <b>{row['Recipient']}</b> | 📅 <b>{row['Deadline']}</b> at <span class="gold-text">{row['Time']}</span></p>
            </div>
            """, unsafe_allow_html=True)
            if st.button(f"🗑️ Remove #{i}", key=f"del_{i}", use_container_width=True):
                df.drop(i).to_csv(CSV_FILE, index=False)
                st.rerun()

elif st.session_state.page == "create":
    st.markdown("## 📅 Schedule New Email")
    if st.button("← Back"):
        st.session_state.page = "dashboard"
        st.rerun()
    
    with st.form("skd_form"):
        task = st.text_input("Property / Task Description")
        email = st.text_input("Recipient Email")
        c1, c2 = st.columns(2)
        date_sel = c1.date_input("Target Date", datetime.now(UAE_TZ))
        time_sel = c2.text_input("Target Time (e.g., 02:30 PM)", value=(datetime.now(UAE_TZ) + timedelta(minutes=15)).strftime("%I:%M %p"))
        recur_sel = st.selectbox("Repeat Schedule", ["None", "Weekly", "Monthly"])
        
        if st.form_submit_button("ACTIVATE SCHEDULE"):
            if task and email:
                new_entry = pd.DataFrame([[task, email, str(date_sel), time_sel, 'Active', recur_sel, time.time()]], columns=COLUMNS)
                pd.concat([pd.read_csv(CSV_FILE), new_entry], ignore_index=True).to_csv(CSV_FILE, index=False)
                st.session_state.page = "dashboard"
                st.rerun()

# --- 6. RUN ENGINE & FOOTER ---
run_automation_engine()
st.markdown(f"<div class='footer'>CREATED BY YARED ANBESA<br>SKD EMAIL SCHEDULE APP © {datetime.now().year}</div>", unsafe_allow_html=True)
