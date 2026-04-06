import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os
import pytz

# --- 1. CONFIGURATION ---
GMAIL_USER = 'skdrealestate10@gmail.com'
GMAIL_PASSWORD = 'jukv rsyr breg irzy' 
CSV_FILE = 'list.csv'
COLUMNS = ['Task', 'Recipient', 'Deadline', 'Time', 'DaysBefore', 'Status', 'Recurrence']
UAE_TZ = pytz.timezone('Asia/Dubai')

# --- 2. RELIABLE SENDING ENGINE ---
def run_automation_engine():
    if not os.path.exists(CSV_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
        return

    df_bg = pd.read_csv(CSV_FILE)
    now_uae = datetime.now(UAE_TZ)
    today_str = now_uae.strftime('%Y-%m-%d')
    current_time_obj = now_uae.time()
    
    changed = False

    for index, row in df_bg.iterrows():
        if str(row['Status']) == 'Active':
            if str(row['Deadline']) <= today_str:
                try:
                    # Parse 12-hour time
                    scheduled_time = datetime.strptime(str(row['Time']), '%I:%M %p').time()
                    if str(row['Deadline']) < today_str or current_time_obj >= scheduled_time:
                        recipients = [e.strip() for e in str(row['Recipient']).split(',')]
                        msg = MIMEText(f"SKD Reminder: {row['Task']}\nDue: {row['Deadline']} at {row['Time']}")
                        msg['Subject'] = f"🔔 SKD REMINDER: {row['Task']}"
                        msg['From'] = GMAIL_USER
                        msg['To'] = ", ".join(recipients)
                        
                        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                            server.login(GMAIL_USER, GMAIL_PASSWORD)
                            server.send_message(msg)
                        
                        # Recurrence Logic
                        deadline_dt = datetime.strptime(str(row['Deadline']), '%Y-%m-%d')
                        if row['Recurrence'] == 'Weekly':
                            df_bg.at[index, 'Deadline'] = (deadline_dt + timedelta(weeks=1)).strftime('%Y-%m-%d')
                        elif row['Recurrence'] == 'Monthly':
                            df_bg.at[index, 'Deadline'] = (deadline_dt + timedelta(days=30)).strftime('%Y-%m-%d')
                        else:
                            df_bg.at[index, 'Status'] = 'Sent'
                        changed = True
                except: continue
    if changed: df_bg.to_csv(CSV_FILE, index=False)

run_automation_engine()

# --- 3. UI SETUP & GLASSMORPHISM ---
st.set_page_config(page_title="SKD Reminder Center", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .header-box { text-align: left; padding: 15px; background: white; border-bottom: 3px solid #D4AF37; }
    
    /* Glassmorphism Stats Bar */
    .glass-stats {
        background: rgba(255, 255, 255, 0.4);
        backdrop-filter: blur(10px);
        -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        border-radius: 15px;
        padding: 15px 25px;
        display: flex;
        justify-content: space-around;
        align-items: center;
        margin: 20px 0;
        box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
    }
    .stat-item { font-family: 'Inter', sans-serif; font-size: 0.95rem; color: #1E293B; font-weight: 600; }
    .stat-value { color: #8B0000; font-size: 1.1rem; margin-left: 8px; }
    
    .card { background: white; padding: 20px; border-radius: 12px; border-left: 6px solid #8B0000; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 15px; }
    .tag-active { background: #FFF5F5; color: #8B0000; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.75rem; border: 1px solid #8B0000; }
    </style>
    """, unsafe_allow_html=True)

if os.path.exists("logo.jpeg"):
    st.markdown('<div class="header-box">', unsafe_allow_html=True)
    st.image("logo.jpeg", width=160)
    st.markdown('</div>', unsafe_allow_html=True)

if "page" not in st.session_state: st.session_state.page = "dashboard"
df = pd.read_csv(CSV_FILE)

# --- DASHBOARD ---
if st.session_state.page == "dashboard":
    # Calculate Stats for Glass Bar
    active_count = len(df[df['Status'] == 'Active'])
    sent_count = len(df[df['Status'] == 'Sent'])

    # Glassmorphism Stats Bar
    st.markdown(f"""
    <div class="glass-stats">
        <div class="stat-item">🟢 ACTIVE REMINDERS <span class="stat-value">{active_count}</span></div>
        <div class="stat-item">|</div>
        <div class="stat-item">📤 TOTAL EMAILS SENT <span class="stat-value">{sent_count}</span></div>
        <div class="stat-item">|</div>
        <div class="stat-item">⏰ DUBAI TIME: <span class="stat-value">{datetime.now(UAE_TZ).strftime('%I:%M %p')}</span></div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([3, 1])
    c1.subheader("Scheduled Communications")
    if c2.button("➕ New Email", type="primary", use_container_width=True):
        st.session_state.page = "create"
        st.rerun()

    active_tasks = df[df['Status'] == 'Active']
    if len(active_tasks) == 0:
        st.info("No active tasks.")
    else:
        for i, row in active_tasks[::-1].iterrows():
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                col_tx, col_dt, col_dl = st.columns([3, 2, 0.5])
                with col_tx:
                    st.markdown(f'<span class="tag-active">ACTIVE</span> **{row["Task"]}**', unsafe_allow_html=True)
                    st.caption(f"To: {row['Recipient']}")
                with col_dt:
                    st.write(f"📅 {row['Deadline']}")
                    st.caption(f"⏰ {row['Time']} | {row['Recurrence']}")
                with col_dl:
                    if st.button("🗑️", key=f"del_{i}"):
                        df.drop(i).to_csv(CSV_FILE, index=False)
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# --- CREATE ---
elif st.session_state.page == "create":
    if st.button("← Back"):
        st.session_state.page = "dashboard"
        st.rerun()
    with st.form("add_new"):
        st.write("### Schedule New Email")
        t = st.text_input("Task/Property Name")
        e = st.text_input("Recipient Email")
        c1, c2, c3 = st.columns(3)
        d = c1.date_input("Date", datetime.now(UAE_TZ))
        tm = st.text_input("Time (e.g. 02:30 PM)", value=datetime.now(UAE_TZ).strftime("%I:%M %p"))
        r = c3.selectbox("Repeat", ["None", "Weekly", "Monthly"])
        if st.form_submit_button("SAVE SCHEDULE", use_container_width=True):
            if t and e:
                new_row = pd.DataFrame([[t, e, str(d), tm, 0, 'Active', r]], columns=COLUMNS)
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_csv(CSV_FILE, index=False)
                st.session_state.page = "dashboard"
                st.rerun()
