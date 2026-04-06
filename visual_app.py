import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os
import pytz

# --- 1. SETTINGS & AUTH ---
GMAIL_USER = 'skdrealestate10@gmail.com'
GMAIL_PASSWORD = 'jukv rsyr breg irzy' 
CSV_FILE = 'list.csv'
COLUMNS = ['Task', 'Recipient', 'Deadline', 'Time', 'DaysBefore', 'Status', 'Recurrence']
UAE_TZ = pytz.timezone('Asia/Dubai')

# --- 2. THE ULTIMATE SENDING ENGINE ---
def run_automation_engine():
    """Checks the CSV and sends emails based on Dubai Time."""
    if not os.path.exists(CSV_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
        return

    df_bg = pd.read_csv(CSV_FILE)
    # Get current Dubai time
    now_uae = datetime.now(UAE_TZ)
    today_str = now_uae.strftime('%Y-%m-%d')
    current_time_str = now_uae.strftime('%H:%M')
    
    changed = False

    for index, row in df_bg.iterrows():
        if str(row['Status']) == 'Active':
            # Logic: If date is today/past AND time has reached
            if str(row['Deadline']) < today_str or (str(row['Deadline']) == today_str and current_time_str >= str(row['Time'])):
                
                # Send Process
                recipients = [e.strip() for e in str(row['Recipient']).split(',')]
                msg = MIMEText(f"SKD Reminder: {row['Task']}\nScheduled for: {row['Deadline']} at {row['Time']}\n\nAutomated by SKD Real Estate.")
                msg['Subject'] = f"🔔 SKD REMINDER: {row['Task']}"
                msg['From'] = GMAIL_USER
                msg['To'] = ", ".join(recipients)
                
                try:
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                        server.login(GMAIL_USER, GMAIL_PASSWORD)
                        server.send_message(msg)
                    
                    # Handle Recurrence Logic
                    deadline_dt = datetime.strptime(str(row['Deadline']), '%Y-%m-%d')
                    if row['Recurrence'] == 'Weekly':
                        df_bg.at[index, 'Deadline'] = (deadline_dt + timedelta(weeks=1)).strftime('%Y-%m-%d')
                    elif row['Recurrence'] == 'Monthly':
                        df_bg.at[index, 'Deadline'] = (deadline_dt + timedelta(days=30)).strftime('%Y-%m-%d')
                    else:
                        df_bg.at[index, 'Status'] = 'Sent'
                    
                    changed = True
                except Exception as e:
                    st.error(f"Failed to send '{row['Task']}': {e}")

    if changed:
        df_bg.to_csv(CSV_FILE, index=False)

# TRIGGER ENGINE ON EVERY LOAD
run_automation_engine()

# --- 3. LUXURY UI SETUP ---
st.set_page_config(page_title="SKD Reminder Center", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FCFCFC; }
    .header-box { text-align: left; padding: 20px; background: white; border-bottom: 3px solid #D4AF37; margin-bottom: 20px; }
    .card { background: white; padding: 20px; border-radius: 12px; border-left: 6px solid #8B0000; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 15px; }
    .tag-active { background: #FFF5F5; color: #8B0000; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.75rem; border: 1px solid #8B0000; }
    .tag-sent { background: #F0FFF4; color: #22543D; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.75rem; border: 1px solid #22543D; }
    .footer { text-align: center; color: #94A3B8; font-size: 0.8rem; margin-top: 50px; border-top: 1px solid #EEE; padding-top: 20px; }
    </style>
    """, unsafe_allow_html=True)

# Branding Header
st.markdown('<div class="header-box">', unsafe_allow_html=True)
if os.path.exists("logo.jpeg"):
    st.image("logo.jpeg", width=180)
st.markdown('</div>', unsafe_allow_html=True)

# Navigation State
if "page" not in st.session_state: st.session_state.page = "dashboard"

# --- PAGE 1: DASHBOARD ---
if st.session_state.page == "dashboard":
    col_t, col_b = st.columns([3, 1])
    with col_t:
        st.subheader("Active Real Estate Reminders")
        now_display = datetime.now(UAE_TZ).strftime("%I:%M %p")
        st.caption(f"Current Dubai Time: {now_display} 🇦🇪")
    with col_b:
        if st.button("➕ Create New Reminder", type="primary", use_container_width=True):
            st.session_state.page = "create"
            st.rerun()

    st.divider()
    df = pd.read_csv(CSV_FILE)
    
    if len(df) == 0:
        st.info("No tasks scheduled yet.")
    else:
        for i, row in df[::-1].iterrows():
            with st.container():
                st.markdown('<div class="card">', unsafe_allow_html=True)
                c_status, c_main, c_time, c_del = st.columns([0.8, 3, 2, 0.5])
                
                with c_status:
                    tag = "tag-active" if row['Status'] == 'Active' else "tag-sent"
                    st.markdown(f'<span class="{tag}">{row["Status"]}</span>', unsafe_allow_html=True)
                with c_main:
                    st.markdown(f"**{row['Task']}**")
                    st.caption(f"Recipient: {row['Recipient']}")
                with c_time:
                    st.write(f"📅 {row['Deadline']}")
                    st.caption(f"⏰ {row['Time']} | {row['Recurrence']}")
                with c_del:
                    if st.button("🗑️", key=f"del_{i}"):
                        df.drop(i).to_csv(CSV_FILE, index=False)
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE 2: CREATE ---
elif st.session_state.page == "create":
    if st.button("← Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()
    
    st.markdown("## Schedule New Communication")
    with st.form("new_reminder_form"):
        task_name = st.text_input("Task/Property Name")
        target_email = st.text_input("Recipient Email(s)")
        
        col1, col2, col3 = st.columns(3)
        with col1: d_date = st.date_input("Target Date", datetime.now(UAE_TZ))
        with col2: d_time = st.text_input("Time (24h Format, e.g., 14:30)", value="09:00")
        with col3: d_recur = st.selectbox("Recurrence", ["None", "Weekly", "Monthly"])
        
        d_before = st.number_input("Days Before Deadline to Send", 0, 30, 0)
        
        if st.form_submit_button("SAVE AND SCHEDULE", use_container_width=True):
            if task_name and target_email:
                new_data = pd.DataFrame([[task_name, target_email, str(d_date), d_time, int(d_before), 'Active', d_recur]], columns=COLUMNS)
                df = pd.read_csv(CSV_FILE)
                df = pd.concat([df, new_data], ignore_index=True)
                df.to_csv(CSV_FILE, index=False)
                st.session_state.page = "dashboard"
                st.rerun()
            else:
                st.error("Please fill in the Task Name and Email.")

st.markdown('<div class="footer">SKD Real Estate Automation • Created by Yared Anbesa</div>', unsafe_allow_html=True)
