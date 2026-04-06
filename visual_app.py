import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os
import pytz # Standard library for timezones

# --- 1. CONFIGURATION ---
GMAIL_USER = 'skdrealestate10@gmail.com'
GMAIL_PASSWORD = 'jukv rsyr breg irzy'
CSV_FILE = 'list.csv'
COLUMNS = ['Task', 'Recipient', 'Deadline', 'Time', 'DaysBefore', 'Status', 'Recurrence']

# --- 2. THE DUBAI-SENSITIVE ENGINE ---
def run_email_engine():
    if not os.path.exists(CSV_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
        return

    df_bg = pd.read_csv(CSV_FILE)
    
    # FORCE DUBAI TIME
    uae_tz = pytz.timezone('Asia/Dubai')
    now = datetime.now(uae_tz)
    today_date = now.date()
    current_time_str = now.strftime("%H:%M")
    
    changed = False

    for index, row in df_bg.iterrows():
        if str(row['Status']) == 'Active':
            deadline = datetime.strptime(str(row['Deadline']), '%Y-%m-%d').date()
            send_on_date = deadline - timedelta(days=int(row['DaysBefore']))
            
            # If date is today/past AND time has reached (or passed)
            if (today_date > send_on_date) or (today_date == send_on_date and current_time_str >= str(row['Time'])):
                recipients = [e.strip() for e in str(row['Recipient']).split(',')]
                msg = MIMEText(f"Reminder: {row['Task']}\nDue: {row['Deadline']}\n\nSKD Real Estate Automation")
                msg['Subject'] = f"🔔 SKD REMINDER: {row['Task']}"
                msg['From'] = GMAIL_USER
                msg['To'] = ", ".join(recipients)
                
                try:
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                        server.login(GMAIL_USER, GMAIL_PASSWORD)
                        server.send_message(msg)
                    
                    if row['Recurrence'] == 'Weekly':
                        df_bg.at[index, 'Deadline'] = str(deadline + timedelta(weeks=1))
                    elif row['Recurrence'] == 'Monthly':
                        df_bg.at[index, 'Deadline'] = str(deadline + timedelta(days=30))
                    else:
                        df_bg.at[index, 'Status'] = 'Sent'
                    changed = True
                except Exception as e:
                    st.error(f"Mail Error: {e}")

    if changed:
        df_bg.to_csv(CSV_FILE, index=False)

# RUN ENGINE
run_email_engine()

# --- 3. PREMIUM UI ---
st.set_page_config(page_title="SKD | Luxury Reminders", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FCFCFC; }
    .header-box { text-align: left; padding: 20px; background: white; border-bottom: 3px solid #D4AF37; margin-bottom: 20px; }
    .reminder-card {
        background: white; padding: 15px; border-radius: 10px;
        border-left: 5px solid #8B0000; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 10px;
    }
    .tag-active { background: #FFF5F5; color: #8B0000; padding: 2px 10px; border-radius: 15px; font-weight: 700; font-size: 0.7rem; border: 1px solid #8B0000; }
    </style>
    """, unsafe_allow_html=True)

if "page" not in st.session_state: st.session_state.page = "dashboard"

# Header with Logo
st.markdown('<div class="header-box">', unsafe_allow_html=True)
if os.path.exists("logo.jpeg"): 
    st.image("logo.jpeg", width=150)
st.markdown('</div>', unsafe_allow_html=True)

df = pd.read_csv(CSV_FILE)

if st.session_state.page == "dashboard":
    c1, c2 = st.columns([3, 1])
    c1.subheader("SKD Real Estate | Active Reminders")
    if c2.button("➕ New Email", type="primary", use_container_width=True):
        st.session_state.page = "create"
        st.rerun()

    for i, row in df[::-1].iterrows():
        if row['Status'] == 'Active':
            st.markdown('<div class="reminder-card">', unsafe_allow_html=True)
            col_tx, col_dt, col_dl = st.columns([3, 2, 0.5])
            with col_tx:
                st.markdown(f'<span class="tag-active">Active</span> **{row["Task"]}**', unsafe_allow_html=True)
                st.caption(f"To: {row['Recipient']}")
            with col_dt:
                st.write(f"📅 {row['Deadline']} | ⏰ {row['Time']}")
            with col_dl:
                if st.button("🗑️", key=f"del_{i}"):
                    df.drop(i).to_csv(CSV_FILE, index=False)
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.page == "create":
    if st.button("← Back"):
        st.session_state.page = "dashboard"
        st.rerun()
    with st.form("new_form"):
        t = st.text_input("Subject")
        e = st.text_input("Email")
        c1, c2 = st.columns(2)
        d = c1.date_input("Date", datetime.now())
        tm = c2.text_input("Time (HH:MM)", "14:45")
        if st.form_submit_button("SAVE"):
            new_row = pd.DataFrame([[t, e, str(d), tm, 0, 'Active', 'None']], columns=COLUMNS)
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(CSV_FILE, index=False)
            st.session_state.page = "dashboard"
            st.rerun()
