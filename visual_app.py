import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os
import time
import threading

# --- SECURE CONFIGURATION ---
# These pull from the "Secrets" we set up in Streamlit Cloud
GMAIL_USER = st.secrets["GMAIL_USER"]
GMAIL_PASSWORD = st.secrets["GMAIL_PASSWORD"]
CSV_FILE = 'list.csv'
COLUMNS = ['Task', 'Recipient', 'Deadline', 'Time', 'DaysBefore', 'Status', 'Recurrence']

# --- BACKGROUND AUTOMATION ENGINE ---
def auto_send_engine():
    """Checks for due emails every 60 seconds in the background."""
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
                            # Multi-recipient split logic
                            recipient_list = [email.strip() for email in str(row['Recipient']).split(',')]
                            
                            msg = MIMEText(f"Hello,\n\nThis is an automated reminder for: '{row['Task']}'\nDue Date: {row['Deadline']}\n\nRegards,\nSKD Real Estate Digital Assistant")
                            msg['Subject'] = f"🔔 SKD REMINDER: {row['Task']}"
                            msg['From'] = GMAIL_USER
                            msg['To'] = ", ".join(recipient_list)
                            
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
                            except: pass

                if changed:
                    df_bg.to_csv(CSV_FILE, index=False)
        except: pass
        time.sleep(60)

# Start Engine
if "engine_started" not in st.session_state:
    threading.Thread(target=auto_send_engine, daemon=True).start()
    st.session_state.engine_started = True

# --- UI SETUP & MODERN CSS ---
st.set_page_config(page_title="SKD Reminder Center", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F9FAFB; }
    .main-header { font-size: 2.2rem; font-weight: 700; color: #111827; margin-bottom: 0px; }
    .tag-active { background: #DBEAFE; color: #1E40AF; padding: 4px 12px; border-radius: 99px; font-size: 0.8rem; font-weight: 600; }
    .tag-sent { background: #D1FAE5; color: #065F46; padding: 4px 12px; border-radius: 99px; font-size: 0.8rem; font-weight: 600; }
    .footer { position: fixed; left: 0; bottom: 0; width: 100%; background-color: white; color: #6B7280; text-align: center; padding: 10px; border-top: 1px solid #E5E7EB; font-size: 0.9rem; }
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

# --- TOP BRANDING SECTION ---
with st.container():
    c_logo, c_title = st.columns([1, 4])
    with c_logo:
        # Ensure your logo file is named 'logo.jpeg' in your GitHub repo
        if os.path.exists("logo.jpeg"):
            st.image("logo.jpeg", use_container_width=True)
    with c_title:
        st.markdown('<p class="main-header" style="margin-top:25px;">SKD Reminder Center</p>', unsafe_allow_html=True)
        st.caption("Automated Real Estate Notification Engine • Active 24/7")
    st.markdown("---")

# --- PAGE 1: DASHBOARD ---
if st.session_state.page == "dashboard":
    col_stat1, col_stat2, col_new = st.columns([1,1,1])
    with col_stat1: st.metric("Active Reminders", len(df[df['Status'] == 'Active']))
    with col_stat2: st.metric("Total History", len(df[df['Status'] == 'Sent']))
    with col_new: 
        st.write("") # Spacer
        st.button("➕ Create New Reminder", on_click=go_to_create, use_container_width=True, type="primary")

    st.markdown("### Scheduled Tasks")
    if len(df) == 0:
        st.info("No reminders scheduled yet.")
    else:
        for index, row in df[::-1].iterrows():
            with st.container():
                c1, c2, c3, c4 = st.columns([0.8, 3.5, 2.5, 1])
                with c1:
                    status_class = "tag-sent" if row['Status'] == 'Sent' else "tag-active"
                    st.markdown(f'<span class="{status_class}">{row["Status"]}</span>', unsafe_allow_html=True)
                with c2:
                    st.markdown(f"**{row['Task']}**")
                    st.caption(f"👥 To: {row['Recipient']}")
                with c3:
                    st.markdown(f"📅 **{row['Deadline']}**")
                    st.caption(f"⏰ {row['Time']} | {row['Recurrence']}")
                with c4:
                    if st.button("Delete", key=f"del_{index}"):
                        df.drop(index).to_csv(CSV_FILE, index=False)
                        st.rerun()
                st.markdown('<div style="height:15px"></div>', unsafe_allow_html=True)

# --- PAGE 2: CREATE ---
elif st.session_state.page == "create":
    st.button("← Back to Dashboard", on_click=go_to_dashboard)
    st.markdown('<p class="main-header">Schedule Official Reminder</p>', unsafe_allow_html=True)
    
    with st.expander("Setup Details", expanded=True):
        with st.form("modern_form", clear_on_submit=True):
            t_name = st.text_input("Project / Task Name", placeholder="e.g. Al Waleed Gardens 2 Expiry")
            r_email = st.text_input("Recipient Email(s)", placeholder="email1@gmail.com, email2@gmail.com")
            st.caption("Separate multiple emails with a comma ( , )")
            
            c_d, c_t, c_r = st.columns(3)
            with c_d: d_date = st.date_input("Deadline Date", datetime.now() + timedelta(days=7))
            with c_t: d_time = st.text_input("Send Time (HH:MM)", value="09:00")
            with c_r: recur = st.selectbox("Recurrence", ["None", "Weekly", "Monthly", "Yearly"])
            
            rem_days = st.number_input("Remind X days before", 0, 30, 0)
            
            if st.form_submit_button("Schedule Reminder", use_container_width=True):
                if t_name and r_email:
                    new_row = pd.DataFrame([[t_name, r_email, str(d_date), d_time, int(rem_days), 'Active', recur]], columns=COLUMNS)
                    df = pd.concat([df, new_row], ignore_index=True)
                    df.to_csv(CSV_FILE, index=False)
                    st.session_state.page = "dashboard"
                    st.rerun()

# --- FOOTER ---
st.markdown('<div class="footer">Built for SKD Real Estate • Created by Yared Anbesa</div>', unsafe_allow_html=True)
