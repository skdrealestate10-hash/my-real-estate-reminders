import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os
import time
import threading

# --- SECURE CONFIGURATION ---
GMAIL_USER = st.secrets["GMAIL_USER"]
GMAIL_PASSWORD = st.secrets["GMAIL_PASSWORD"]
CSV_FILE = 'list.csv'
COLUMNS = ['Task', 'Recipient', 'Deadline', 'Time', 'DaysBefore', 'Status', 'Recurrence']

# --- BACKGROUND AUTOMATION ENGINE ---
def auto_send_engine():
    while True:
        try:
            if os.path.exists(CSV_FILE):
                df_bg = pd.read_csv(CSV_FILE)
                now = datetime.now()
                today_date = now.date()
                current_time_str = now.strftime("%H:%M")
                changed = False

                for index, row in df_bg.iterrows():
                    if row['Status'] == 'Active':
                        deadline = datetime.strptime(str(row['Deadline']), '%Y-%m-%d').date()
                        send_on_date = deadline - timedelta(days=int(row['DaysBefore']))
                        
                        if (today_date > send_on_date) or (today_date == send_on_date and current_time_str >= str(row['Time'])):
                            recipient_list = [e.strip() for e in str(row['Recipient']).split(',')]
                            msg = MIMEText(f"Hello,\n\nReminder: '{row['Task']}'\nDue: {row['Deadline']}\n\nSKD Real Estate Automation")
                            msg['Subject'] = f"🔔 SKD REMINDER: {row['Task']}"
                            msg['From'] = GMAIL_USER
                            msg['To'] = ", ".join(recipient_list)
                            
                            try:
                                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                                    server.login(GMAIL_USER, GMAIL_PASSWORD)
                                    server.send_message(msg)
                                if row['Recurrence'] == 'Weekly': df_bg.at[index, 'Deadline'] = str(deadline + timedelta(weeks=1))
                                elif row['Recurrence'] == 'Monthly': df_bg.at[index, 'Deadline'] = str(deadline + timedelta(days=30))
                                else: df_bg.at[index, 'Status'] = 'Sent'
                                changed = True
                            except: pass
                if changed: df_bg.to_csv(CSV_FILE, index=False)
        except: pass
        time.sleep(60)

if "engine_started" not in st.session_state:
    threading.Thread(target=auto_send_engine, daemon=True).start()
    st.session_state.engine_started = True

# --- MODERN UI STYLING ---
st.set_page_config(page_title="SKD Reminders", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F3F4F6; }
    
    .main-container { padding: 2rem; max-width: 1000px; margin: auto; }
    
    /* Logo Center Styling */
    .logo-container { display: flex; justify-content: center; margin-bottom: 10px; }
    .header-title { text-align: center; font-size: 2.2rem; font-weight: 700; color: #111827; margin-bottom: 5px; }
    .header-sub { text-align: center; color: #6B7280; font-size: 1rem; margin-bottom: 30px; }
    
    /* Dashboard Stats */
    .stMetric { background: white; padding: 15px; border-radius: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); border: 1px solid #E5E7EB; }
    
    /* List Items */
    .reminder-box { background: white; padding: 20px; border-radius: 16px; border: 1px solid #E5E7EB; margin-bottom: 12px; }
    .tag-active { background: #EEF2FF; color: #4338CA; padding: 4px 12px; border-radius: 99px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
    .tag-sent { background: #ECFDF5; color: #065F46; padding: 4px 12px; border-radius: 99px; font-size: 0.75rem; font-weight: 600; text-transform: uppercase; }
    
    /* Custom Footer */
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background: rgba(255, 255, 255, 0.8); backdrop-filter: blur(10px); color: #374151; text-align: center; padding: 12px; font-size: 0.85rem; border-top: 1px solid #E5E7EB; font-weight: 500; }
    </style>
    """, unsafe_allow_html=True)

# Load Data
if not os.path.exists(CSV_FILE): pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
df = pd.read_csv(CSV_FILE)

# Navigation
if "page" not in st.session_state: st.session_state.page = "dashboard"
def go_to_create(): st.session_state.page = "create"
def go_to_dashboard(): st.session_state.page = "dashboard"

# --- HEADER SECTION ---
st.markdown('<div class="logo-container">', unsafe_allow_html=True)
if os.path.exists("logo.jpeg"):
    st.image("logo.jpeg", width=180) # Centered and sized professionally
st.markdown('</div>', unsafe_allow_html=True)

st.markdown('<p class="header-title">SKD Reminder Center</p>', unsafe_allow_html=True)
st.markdown('<p class="header-sub">Luxury Real Estate Notification Engine • Active 24/7</p>', unsafe_allow_html=True)

# --- DASHBOARD ---
if st.session_state.page == "dashboard":
    c1, c2, c3 = st.columns([1,1,1])
    with c1: st.metric("Active Reminders", len(df[df['Status'] == 'Active']))
    with c2: st.metric("Total History", len(df[df['Status'] == 'Sent']))
    with c3: 
        st.write("")
        st.button("➕ New Reminder", on_click=go_to_create, use_container_width=True, type="primary")

    st.markdown("<br>", unsafe_allow_html=True)
    
    if len(df) ==
