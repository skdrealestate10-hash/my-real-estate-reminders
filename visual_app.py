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
    st.error("Secrets missing! Add GMAIL_USER and GMAIL_PASSWORD to Streamlit Settings.")
    st.stop()

CSV_FILE = 'list.csv'
COLUMNS = ['Task', 'Recipient', 'Deadline', 'Time', 'DaysBefore', 'Status', 'Recurrence']
UAE_TZ = pytz.timezone('Asia/Dubai')

# --- 2. UI SETUP ---
st.set_page_config(page_title="SKD Reminder Center", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .header-box { text-align: left; padding: 15px; background: white; border-bottom: 3px solid #D4AF37; }
    .glass-stats {
        background: rgba(255, 255, 255, 0.4); backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 15px; padding: 15px;
        display: flex; justify-content: space-around; margin: 20px 0; box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
    }
    .stat-item { font-weight: 600; color: #1E293B; font-size: 0.9rem; }
    .stat-value { color: #8B0000; font-size: 1.1rem; margin-left: 5px; }
    .card { background: white; padding: 20px; border-radius: 12px; border-left: 6px solid #8B0000; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 15px; }
    .tag-active { background: #FFF5F5; color: #8B0000; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.7rem; border: 1px solid #8B0000; }
    .tag-sent { background: #F0FFF4; color: #22543D; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.7rem; border: 1px solid #22543D; }
    .footer-container { text-align: center; padding: 30px 0; margin-top: 50px; border-top: 1px solid #E2E8F0; color: #64748B; }
    .footer-main { font-weight: 700; color: #1E293B; letter-spacing: 1px; text-transform: uppercase; font-size: 0.85rem; }
    </style>
    """, unsafe_allow_html=True)

if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
df = pd.read_csv(CSV_FILE)

if "page" not in st.session_state: st.session_state.page = "dashboard"
if "block_engine" not in st.session_state: st.session_state.block_engine = False

# --- 3. PAGES ---
if st.session_state.page == "dashboard":
    a_count = len(df[df['Status'] == 'Active'])
    s_count = len(df[df['Status'] == 'Sent'])
    
    st.markdown(f"""
    <div class="glass-stats">
        <div class="stat-item">🟢 ACTIVE <span class="stat-value">{a_count}</span></div>
        <div class="stat-item">📤 SENT <span class="stat-value">{s_count}</span></div>
        <div class="stat-item">⏰ DUBAI: <span class="stat-value">{datetime.now(UAE_TZ).strftime('%I:%M %p')}</span></div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("➕ Create New Reminder", type="primary"):
        st.session_state.page = "create"
        st.rerun()

    for i, row in df[::-1].iterrows():
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            col_tx, col_dt, col_dl = st.columns([3, 2, 0.5])
            with col_tx:
                status_val = str(row['Status'])
                tag = "tag-active" if status_val == 'Active' else "tag-sent"
                st.markdown(f'<span class="{tag}">{status_val.upper()}</span> **{row["Task"]}**', unsafe_allow_html=True)
                st.caption(f"To: {row['Recipient']}")
            with col_dt:
                st.write(f"📅 {row['Deadline']}")
                st.caption(f"⏰ {row['Time']}")
            with col_dl:
                if st.button("🗑️", key=f"del_{i}"):
                    df.drop(i).to_csv(CSV_FILE, index=False)
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == "create":
    if st.button("← Back"):
        st.session_state.page = "dashboard"
        st.rerun()
    with st.form("new_task"):
        t = st.text_input("Task Name")
        e = st.text_input("Recipient Email")
        d = st.date_input("Date", datetime.now(UAE_TZ))
        tm = st.text_input("Time (e.g. 10:30 AM)", value=(datetime.now(UAE_TZ) + timedelta(minutes=10)).strftime("%I:%M %p"))
        r = st.selectbox("Repeat", ["None", "Weekly", "Monthly"])
        if st.form_submit_button("SAVE REMINDER"):
            if t and e:
                new_row = pd.DataFrame([[t, e, str(d), tm, 0, 'Active', r]], columns=COLUMNS)
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_csv(CSV_FILE, index=False)
                # IMPORTANT: BLOCK the engine for this specific session run
                st.session_state.block_engine = True
                st.session_state.page = "dashboard"
                st.rerun()

# --- 4. THE ENGINE (ONLY RUNS IF NOT BLOCKED) ---
def run_automation_engine():
    # If we just saved a task, skip the engine run this time
    if st.session_state.block_engine:
        st.session_state.block_engine = False # Reset for next time
        return

    df_bg = pd.read_csv(CSV_FILE)
    now_uae = datetime.now(UAE_TZ)
    today_str = now_uae.strftime('%Y-%m-%d')
    current_time_str = now_uae.strftime('%I:%M %p')
    changed = False

    for index, row in df_bg.iterrows():
        if str(row['Status']) == 'Active':
            try:
                is_past_date = str(row['Deadline']) < today_str
                is_today = str(row['Deadline']) == today_str
                # Only send if it's the exact minute
                is_correct_minute = str(row['Time']) == current_time_str

                if is_past_date or (is_today and is_correct_minute):
                    recipients = [em.strip() for em in str(row['Recipient']).split(',')]
                    msg = MIMEText(f"SKD Reminder: {row['Task']}\nDue: {row['Deadline']} at {row['Time']}")
                    msg['Subject'] = f"🔔 SKD REMINDER: {row['Task']}"
                    msg['From'] = GMAIL_USER
                    msg['To'] = ", ".join(recipients)
                    
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                        server.login(GMAIL_USER, GMAIL_PASSWORD)
                        server.send_message(msg)
                    
                    df_bg.at[index, 'Status'] = 'Sent'
                    changed = True
            except: continue
    
    if changed: df_bg.to_csv(CSV_FILE, index=False)

run_automation_engine()

# --- 5. FOOTER ---
st.markdown("""
    <div class="footer-container">
        <div class="footer-main">SKD Real Estate Reminder Control Center</div>
        <div class="footer-sub">Created by Yared</div>
    </div>
    """, unsafe_allow_html=True)
