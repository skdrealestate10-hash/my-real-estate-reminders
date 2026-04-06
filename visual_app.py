import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os
import time
import threading

# --- 1. SECURE CONFIGURATION ---
GMAIL_USER = st.secrets["GMAIL_USER"]
GMAIL_PASSWORD = st.secrets["GMAIL_PASSWORD"]
CSV_FILE = 'list.csv'
COLUMNS = ['Task', 'Recipient', 'Deadline', 'Time', 'DaysBefore', 'Status', 'Recurrence']

# --- 2. THE BACKGROUND ENGINE (REBUILT) ---
def auto_send_engine():
    """ This runs 24/7 in the background to send your SKD emails """
    while True:
        try:
            if os.path.exists(CSV_FILE):
                df_bg = pd.read_csv(CSV_FILE)
                # Use current time
                now = datetime.now()
                today_date = now.date()
                current_time_str = now.strftime("%H:%M")
                changed = False

                for index, row in df_bg.iterrows():
                    if row['Status'] == 'Active':
                        # Convert saved strings back to dates
                        deadline = datetime.strptime(str(row['Deadline']), '%Y-%m-%d').date()
                        send_on_date = deadline - timedelta(days=int(row['DaysBefore']))
                        
                        # CHECK: Is it time to send?
                        if (today_date > send_on_date) or (today_date == send_on_date and current_time_str >= str(row['Time'])):
                            print(f"🚀 ENGINE: Attempting to send '{row['Task']}'")
                            
                            # Multi-recipient support
                            recipients = [e.strip() for e in str(row['Recipient']).split(',')]
                            
                            msg = MIMEText(f"Reminder: {row['Task']}\nDue Date: {row['Deadline']}\n\nSent via SKD Real Estate Automation.")
                            msg['Subject'] = f"🔔 SKD REMINDER: {row['Task']}"
                            msg['From'] = GMAIL_USER
                            msg['To'] = ", ".join(recipients)
                            
                            try:
                                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                                    server.login(GMAIL_USER, GMAIL_PASSWORD)
                                    server.send_message(msg)
                                print(f"✅ ENGINE: Email Sent Successfully!")
                                
                                # Handle Recurrence
                                if row['Recurrence'] == 'Weekly':
                                    df_bg.at[index, 'Deadline'] = str(deadline + timedelta(weeks=1))
                                elif row['Recurrence'] == 'Monthly':
                                    df_bg.at[index, 'Deadline'] = str(deadline + timedelta(days=30))
                                else:
                                    df_bg.at[index, 'Status'] = 'Sent'
                                changed = True
                            except Exception as email_err:
                                print(f"❌ ENGINE ERROR: {email_err}")

                if changed:
                    df_bg.to_csv(CSV_FILE, index=False)
        except Exception as global_err:
            print(f"⚠️ SYSTEM ERROR: {global_err}")
        
        time.sleep(60) # Wait 1 minute before checking again

# Start the engine only once
if "engine_started" not in st.session_state:
    threading.Thread(target=auto_send_engine, daemon=True).start()
    st.session_state.engine_started = True

# --- 3. MODERN UI DESIGN ---
st.set_page_config(page_title="SKD Reminders", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
    .header-container { text-align: center; padding: 20px 0; }
    .header-title { font-size: 2.4rem; font-weight: 700; color: #1E293B; margin-top: 10px; }
    .metric-card { background: white; padding: 20px; border-radius: 12px; border: 1px solid #E2E8F0; text-align: center; }
    .reminder-box { background: white; padding: 20px; border-radius: 16px; border: 1px solid #E2E8F0; margin-bottom: 12px; box-shadow: 0 2px 4px rgba(0,0,0,0.02); }
    .tag-active { background: #E0E7FF; color: #4338CA; padding: 4px 12px; border-radius: 99px; font-size: 0.75rem; font-weight: 700; }
    .tag-sent { background: #DCFCE7; color: #15803D; padding: 4px 12px; border-radius: 99px; font-size: 0.75rem; font-weight: 700; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background: white; color: #64748B; text-align: center; padding: 10px; border-top: 1px solid #E2E8F0; font-size: 0.85rem; font-weight: 600; }
    </style>
    """, unsafe_allow_html=True)

# Load Data
if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
df = pd.read_csv(CSV_FILE)

# Navigation
if "page" not in st.session_state: st.session_state.page = "dashboard"
def go_to_create(): st.session_state.page = "create"
def go_to_dashboard(): st.session_state.page = "dashboard"

# --- BRANDING ---
st.markdown('<div class="header-container">', unsafe_allow_html=True)
if os.path.exists("logo.jpeg"):
    st.image("logo.jpeg", width=200)
st.markdown('<p class="header-title">SKD Reminder Center</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE: DASHBOARD ---
if st.session_state.page == "dashboard":
    c1, c2, c3 = st.columns([1,1,1])
    with c1: st.metric("Active Reminders", len(df[df['Status'] == 'Active']))
    with c2: st.metric("Total History", len(df[df['Status'] == 'Sent']))
    with c3: 
        st.write("")
        st.button("➕ Create New Reminder", on_click=go_to_create, use_container_width=True, type="primary")

    st.markdown("---")
    if len(df) == 0:
        st.info("Your list is empty. Click 'Create New' to start.")
    else:
        for index, row in df[::-1].iterrows():
            with st.container():
                st.markdown('<div class="reminder-box">', unsafe_allow_html=True)
                col_tag, col_info, col_date, col_action = st.columns([0.8, 3, 2, 0.8])
                with col_tag:
                    status_class = "tag-sent" if row['Status'] == 'Sent' else "tag-active"
                    st.markdown(f'<span class="{status_class}">{row["Status"]}</span>', unsafe_allow_html=True)
                with col_info:
                    st.markdown(f"**{row['Task']}**")
                    st.caption(f"👥 To: {row['Recipient']}")
                with col_date:
                    st.markdown(f"📅 **{row['Deadline']}**")
                    st.caption(f"⏰ {row['Time']} | {row['Recurrence']}")
                with col_action:
                    if st.button("Delete", key=f"del_{index}"):
                        df.drop(index).to_csv(CSV_FILE, index=False)
                        st.rerun()
                st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE: CREATE ---
elif st.session_state.page == "create":
    st.button("← Back to Dashboard", on_click=go_to_dashboard)
    with st.expander("Schedule New Task", expanded=True):
        with st.form("add_form", clear_on_submit=True):
            t_name = st.text_input("Task/Project Name")
            r_email = st.text_input("Recipient Email(s)", help="Use commas for multiple people")
            c1, c2, c3 = st.columns(3)
            with c1: d_date = st.date_input("Deadline", datetime.now())
            with c2: d_time = st.text_input("Time (HH:MM)", value="09:00")
            with c3: recur = st.selectbox("Repeat", ["None", "Weekly", "Monthly", "Yearly"])
            rem_days = st.number_input("Days Before Deadline", 0, 30, 0)
            
            if st.form_submit_button("Schedule Now", use_container_width=True):
                if t_name and r_email:
                    new_row = pd.DataFrame([[t_name, r_email, str(d_date), d_time, int(rem_days), 'Active', recur]], columns=COLUMNS)
                    df = pd.concat([df, new_row], ignore_index=True)
                    df.to_csv(CSV_FILE, index=False)
                    st.session_state.page = "dashboard"
                    st.rerun()

# --- FOOTER ---
st.markdown(f'<div class="footer">SKD Real Estate Automation • Created by Yared</div>', unsafe_allow_html=True)
