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
    st.error("Missing Secrets! Please add GMAIL_USER and GMAIL_PASSWORD in Streamlit Settings.")
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
    /* Deep Navy Background */
    .stApp { background-color: #0F172A; color: #FFFFFF; }
    
    /* High Contrast Cards */
    .reminder-card {
        background: #1E293B; 
        border-radius: 12px; 
        padding: 25px;
        margin-bottom: 20px; 
        border-left: 6px solid #D4AF37;
        box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.4);
    }
    
    /* Force Text Visibility */
    h1, h2, h3, p, span, div { color: #FFFFFF !important; }
    .gold-text { color: #D4AF37 !important; font-weight: bold; }
    .sub-text { color: #94A3B8 !important; font-size: 0.95rem; }
    
    /* Live Clock */
    .time-display { 
        font-size: 2.5rem; 
        font-weight: 800; 
        color: #D4AF37 !important; 
        text-shadow: 2px 2px 4px rgba(0,0,0,0.5);
    }
    
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
    </style>
    """, unsafe_allow_html=True)

# --- 4. THE RELIABLE BACKGROUND ENGINE ---
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
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("<h1>SKD EMAIL SCHEDULE APP</h1>", unsafe_allow_html=True)
        st.markdown("<div><span class='live-dot'></span>SYSTEM MONITORING ACTIVE</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='time-display'>{datetime.now(UAE_TZ).strftime('%I:%M %p')}</div>", unsafe_allow_html=True)
        st.markdown("<div style='text-align:right; color:#94A3B8 !important;'>DUBAI, GST</div>", unsafe_allow_html=True)

    st.divider()

    if st.button("➕ CREATE NEW EMAIL SCHEDULE", type="primary", use_container_width=True):
        st.session_state.page = "create"
        st.rerun()

    st.markdown("### Active Schedule Queue")
    if len(df) == 0:
        st.info("No scheduled emails found.")
    else:
        for i, row in df[::-1].iterrows():
            status = str(row['Status'])
            border_color = "#D4AF37" if status == 'Active' else "#4ADE80"
            with st.container():
                st.markdown(f"""
                <div class="reminder-card" style="border-left-color: {border_color};">
                    <div style="display:flex; justify-content:space-between;">
                        <span class="gold-text">{status.upper()}</span>
                        <span class="sub-text">Record #{i}</span>
                    </div>
                    <h2 style="margin:10px 0;">{row['Task']}</h2>
                    <p><b>Recipient:</b> {row['Recipient']}</p>
                    <p>📅 <b>{row['Deadline']}</b> at <span class="gold-text">{row['Time']}</span></p>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"🗑️ Remove Schedule #{i}", key=f"del_{i}", use_container_width=True):
                    df.drop(i).to_csv(CSV_FILE, index=False)
                    st.rerun()

elif st.session_state.page == "create":
    st.markdown("## 📅 Schedule New Email")
    if st.button("← Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()
    
    with st.form("skd_form"):
        task = st.text_input("Property / Task Description")
        email = st.text_input("Recipient Email (use commas for multiple)")
        c1, c2 = st.columns(2)
        date_sel = c1.date_input("Target Date", datetime.now(UAE_TZ))
        time_sel = c2.text_input("Target Time (e.g., 02:30 PM)", value=(datetime.now(UAE_TZ) + timedelta(minutes=15)).strftime("%I:%M %p"))
        
        if st.form_submit_button("ACTIVATE SCHEDULE"):
            if task and email:
                new_entry = pd.DataFrame([[task, email, str(date_sel), time_sel, 'Active', 'None', time.time()]], columns=COLUMNS)
                pd.concat([pd.read_csv(CSV_FILE), new_entry], ignore_index=True).to_csv(CSV_FILE, index=False)
                st.session_state.page = "dashboard"
                st.rerun()

# --- 6. RUN ENGINE & FOOTER ---
run_automation_engine()

st.markdown(f"""
    <div class="footer">
        CREATED BY YARED ANBESA<br>
        SKD EMAIL SCHEDULE APP © {datetime.now().year}
    </div>
    """, unsafe_allow_html=True)
