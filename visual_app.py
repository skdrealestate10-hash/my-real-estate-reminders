import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os
import pytz

# --- 1. CONFIGURATION ---
GMAIL_USER = st.secrets["GMAIL_USER"]
GMAIL_PASSWORD = st.secrets["GMAIL_PASSWORD"]
CSV_FILE = 'list.csv'
COLUMNS = ['Task', 'Recipient', 'Deadline', 'Time', 'DaysBefore', 'Status', 'Recurrence']
UAE_TZ = pytz.timezone('Asia/Dubai')

# --- 2. UPDATED SENDING ENGINE (NO IMMEDIATE SEND) ---
def run_automation_engine():
    if not os.path.exists(CSV_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
        return

    df_bg = pd.read_csv(CSV_FILE)
    now_uae = datetime.now(UAE_TZ)
    today_str = now_uae.strftime('%Y-%m-%d')
    # Current time rounded to the minute for a clean comparison
    current_time_str = now_uae.strftime('%I:%M %p')
    
    changed = False

    for index, row in df_bg.iterrows():
        if str(row['Status']) == 'Active':
            # 1. Check if the date is today or in the past
            if str(row['Deadline']) <= today_str:
                try:
                    # 2. Check if the scheduled time matches the current Dubai time
                    # This prevents immediate sending unless the clock actually hits your chosen time
                    if str(row['Deadline']) == today_str:
                        if str(row['Time']) != current_time_str:
                            continue # Skip if it's today but not the right minute yet
                    
                    # 3. If it's a match or truly overdue from a previous day, send it
                    recipients = [e.strip() for e in str(row['Recipient']).split(',')]
                    msg = MIMEText(f"SKD Reminder: {row['Task']}\nDue: {row['Deadline']} at {row['Time']}")
                    msg['Subject'] = f"🔔 SKD REMINDER: {row['Task']}"
                    msg['From'] = GMAIL_USER
                    msg['To'] = ", ".join(recipients)
                    
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                        server.login(GMAIL_USER, GMAIL_PASSWORD)
                        server.send_message(msg)
                    
                    # 4. Handle Recurrence or Mark as Sent
                    deadline_dt = datetime.strptime(str(row['Deadline']), '%Y-%m-%d')
                    if row['Recurrence'] == 'Weekly':
                        df_bg.at[index, 'Deadline'] = (deadline_dt + timedelta(weeks=1)).strftime('%Y-%m-%d')
                    elif row['Recurrence'] == 'Monthly':
                        df_bg.at[index, 'Deadline'] = (deadline_dt + timedelta(days=30)).strftime('%Y-%m-%d')
                    else:
                        df_bg.at[index, 'Status'] = 'Sent'
                    changed = True
                except Exception as e:
                    print(f"Error sending email: {e}")
                    continue
                    
    if changed: 
        df_bg.to_csv(CSV_FILE, index=False)
# --- 3. UI SETUP ---
st.set_page_config(page_title="SKD Reminder Center", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .header-box { text-align: left; padding: 15px; background: white; border-bottom: 3px solid #D4AF37; }
    
    /* Glassmorphism Stats Bar */
    .glass-stats {
        background: rgba(255, 255, 255, 0.4); backdrop-filter: blur(10px); -webkit-backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2); border-radius: 15px; padding: 15px;
        display: flex; justify-content: space-around; margin: 20px 0; box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.07);
    }
    
    .stat-item { font-weight: 600; color: #1E293B; font-size: 0.9rem; }
    .stat-value { color: #8B0000; font-size: 1.1rem; margin-left: 5px; }
    
    .card { background: white; padding: 20px; border-radius: 12px; border-left: 6px solid #8B0000; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 15px; }
    
    .tag-active { background: #FFF5F5; color: #8B0000; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.7rem; border: 1px solid #8B0000; }
    .tag-sent { background: #F0FFF4; color: #22543D; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.7rem; border: 1px solid #22543D; }
    
    /* Professional Footer */
    .footer-container {
        text-align: center;
        padding: 30px 0;
        margin-top: 50px;
        border-top: 1px solid #E2E8F0;
        color: #64748B;
        font-family: 'Inter', sans-serif;
    }
    .footer-main { font-weight: 700; color: #1E293B; letter-spacing: 1px; text-transform: uppercase; font-size: 0.85rem; }
    .footer-sub { font-size: 0.75rem; margin-top: 5px; opacity: 0.8; }
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
    # Stats Calculation
    a_count = len(df[df['Status'] == 'Active'])
    s_count = len(df[df['Status'] == 'Sent'])

    st.markdown(f"""
    <div class="glass-stats">
        <div class="stat-item">🟢 ACTIVE REMINDERS <span class="stat-value">{a_count}</span></div>
        <div class="stat-item">📤 TOTAL EMAILS SENT <span class="stat-value">{s_count}</span></div>
        <div class="stat-item">⏰ DUBAI TIME: <span class="stat-value">{datetime.now(UAE_TZ).strftime('%I:%M %p')}</span></div>
    </div>
    """, unsafe_allow_html=True)

    c1, c2 = st.columns([3, 1])
    c1.subheader("All Communications History")
    if c2.button("➕ New Email", type="primary", use_container_width=True):
        st.session_state.page = "create"
        st.rerun()

    if len(df) == 0:
        st.info("No records found.")
    else:
        # Displaying all rows in reverse order (newest first)
        for i, row in df[::-1].iterrows():
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                col_tx, col_dt, col_dl = st.columns([3, 2, 0.5])
                with col_tx:
                    tag_style = "tag-active" if row['Status'] == 'Active' else "tag-sent"
                    st.markdown(f'<span class="{tag_style}">{row["Status"].upper()}</span> **{row["Task"]}**', unsafe_allow_html=True)
                    st.caption(f"To: {row['Recipient']}")
                with col_dt:
                    st.write(f"📅 {row['Deadline']}")
                    st.caption(f"⏰ {row['Time']} | {row['Recurrence']}")
                with col_dl:
                    if st.button("🗑️", key=f"del_{i}"):
                        df.drop(i).to_csv(CSV_FILE, index=False)
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# --- CREATE PAGE ---
elif st.session_state.page == "create":
    if st.button("← Back"):
        st.session_state.page = "dashboard"
        st.rerun()
    with st.form("add_new"):
        st.write("### Schedule New Email")
        t = st.text_input("Task Name")
        e = st.text_input("Recipient Email")
        c1, c2, c3 = st.columns(3)
        d = c1.date_input("Date", datetime.now(UAE_TZ))
        tm = st.text_input("Time (e.g. 02:30 PM)", value=datetime.now(UAE_TZ).strftime("%I:%M %p"))
        r = c3.selectbox("Repeat", ["None", "Weekly", "Monthly"])
        if st.form_submit_button("SAVE"):
            if t and e:
                new_row = pd.DataFrame([[t, e, str(d), tm, 0, 'Active', r]], columns=COLUMNS)
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_csv(CSV_FILE, index=False)
                st.session_state.page = "dashboard"
                st.rerun()

# --- PROFESSIONAL FOOTER ---
st.markdown("""
    <div class="footer-container">
        <div class="footer-main">SKD Real Estate Reminder Control Center</div>
        <div class="footer-sub">Created by Yared</div>
    </div>
    """, unsafe_allow_html=True)
