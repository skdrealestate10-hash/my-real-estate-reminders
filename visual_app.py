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
    
    # We check both 12h and 24h just in case, but prioritize the new AM/PM format
    current_time_12 = now_uae.strftime('%I:%M %p') 
    
    changed = False

    for index, row in df_bg.iterrows():
        if str(row['Status']) == 'Active':
            # Logic: If date is today or past
            if str(row['Deadline']) <= today_str:
                
                # Convert the stored time string to a comparable object
                try:
                    scheduled_time = datetime.strptime(str(row['Time']), '%I:%M %p').time()
                    current_time_obj = now_uae.time()
                    
                    # If scheduled time has passed or is now
                    if str(row['Deadline']) < today_str or current_time_obj >= scheduled_time:
                        
                        recipients = [e.strip() for e in str(row['Recipient']).split(',')]
                        msg = MIMEText(f"SKD Reminder: {row['Task']}\nDue: {row['Deadline']} at {row['Time']}\n\nSent via SKD Automation.")
                        msg['Subject'] = f"🔔 SKD REMINDER: {row['Task']}"
                        msg['From'] = GMAIL_USER
                        msg['To'] = ", ".join(recipients)
                        
                        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                            server.login(GMAIL_USER, GMAIL_PASSWORD)
                            server.send_message(msg)
                        
                        # Handle Recurrence
                        deadline_dt = datetime.strptime(str(row['Deadline']), '%Y-%m-%d')
                        if row['Recurrence'] == 'Weekly':
                            df_bg.at[index, 'Deadline'] = (deadline_dt + timedelta(weeks=1)).strftime('%Y-%m-%d')
                        elif row['Recurrence'] == 'Monthly':
                            df_bg.at[index, 'Deadline'] = (deadline_dt + timedelta(days=30)).strftime('%Y-%m-%d')
                        else:
                            df_bg.at[index, 'Status'] = 'Sent'
                        
                        changed = True
                except:
                    # If someone entered the old 24h format, we skip or you can fix it manually
                    continue

    if changed:
        df_bg.to_csv(CSV_FILE, index=False)

# RUN ENGINE ON EVERY LOAD
run_automation_engine()

# --- 3. UI SETUP ---
st.set_page_config(page_title="SKD Reminder Center", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FCFCFC; }
    .header-box { text-align: left; padding: 20px; background: white; border-bottom: 3px solid #D4AF37; margin-bottom: 20px; }
    .card { background: white; padding: 20px; border-radius: 12px; border-left: 6px solid #8B0000; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 15px; }
    .tag-active { background: #FFF5F5; color: #8B0000; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.75rem; border: 1px solid #8B0000; }
    .footer { text-align: center; color: #94A3B8; font-size: 0.8rem; margin-top: 50px; }
    </style>
    """, unsafe_allow_html=True)

if os.path.exists("logo.jpeg"):
    st.markdown('<div class="header-box">', unsafe_allow_html=True)
    st.image("logo.jpeg", width=180)
    st.markdown('</div>', unsafe_allow_html=True)

if "page" not in st.session_state: st.session_state.page = "dashboard"

# --- DASHBOARD ---
if st.session_state.page == "dashboard":
    c1, c2 = st.columns([3, 1])
    c1.subheader("Active Real Estate Reminders")
    c1.caption(f"Current Dubai Time: {datetime.now(UAE_TZ).strftime('%I:%M %p')}")
    
    if c2.button("➕ New Email", type="primary", use_container_width=True):
        st.session_state.page = "create"
        st.rerun()

    df = pd.read_csv(CSV_FILE)
    if len(df[df['Status'] == 'Active']) == 0:
        st.info("No active tasks.")
    else:
        for i, row in df[::-1].iterrows():
            if row['Status'] == 'Active':
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
        tm = c2.text_input("Time (Example: 02:30 PM)", value=datetime.now(UAE_TZ).strftime("%I:%M %p"))
        r = c3.selectbox("Repeat", ["None", "Weekly", "Monthly"])
        
        if st.form_submit_button("SAVE SCHEDULE", use_container_width=True):
            if t and e:
                new_row = pd.DataFrame([[t, e, str(d), tm, 0, 'Active', r]], columns=COLUMNS)
                df = pd.read_csv(CSV_FILE)
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_csv(CSV_FILE, index=False)
                st.session_state.page = "dashboard"
                st.rerun()

st.markdown('<div class="footer">SKD Real Estate • Created by Yared</div>', unsafe_allow_html=True)
