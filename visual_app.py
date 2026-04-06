import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os

# --- 1. CONFIGURATION ---
GMAIL_USER = 'skdrealestate10@gmail.com'
GMAIL_PASSWORD = 'jukv rsyr breg irzy'
CSV_FILE = 'list.csv'
COLUMNS = ['Task', 'Recipient', 'Deadline', 'Time', 'DaysBefore', 'Status', 'Recurrence']

# --- 2. THE GUARANTEED ENGINE ---
def run_email_engine():
    """This function runs every time the page is loaded or pinged"""
    if not os.path.exists(CSV_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
        return

    df_bg = pd.read_csv(CSV_FILE)
    now = datetime.now()
    today_date = now.date()
    current_time_str = now.strftime("%H:%M")
    changed = False

    for index, row in df_bg.iterrows():
        if str(row['Status']) == 'Active':
            deadline = datetime.strptime(str(row['Deadline']), '%Y-%m-%d').date()
            send_on_date = deadline - timedelta(days=int(row['DaysBefore']))
            
            # TRIGGER: If date is today/past AND time has reached
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
                    
                    # Handle Recurrence
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

# RUN ENGINE IMMEDIATELY ON EVERY LOAD
run_email_engine()

# --- 3. UI & LUXURY STYLING ---
st.set_page_config(page_title="SKD | Luxury Reminders", layout="wide")

st.markdown("""
    <style>
    .stApp { background-color: #FCFCFC; }
    .header-box { text-align: center; padding: 20px; background: white; border-bottom: 2px solid #D4AF37; margin-bottom: 30px; }
    .reminder-card {
        background: white; padding: 20px; border-radius: 12px;
        border-left: 5px solid #8B0000; box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 15px;
    }
    .tag-active { background: #FFF5F5; color: #8B0000; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.7rem; border: 1px solid #8B0000; }
    .tag-sent { background: #F0FFF4; color: #22543D; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.7rem; border: 1px solid #22543D; }
    .footer { text-align: center; padding: 30px; color: #A0AEC0; font-size: 0.8rem; }
    </style>
    """, unsafe_allow_html=True)

# Navigation
if "page" not in st.session_state: st.session_state.page = "dashboard"

# Branding Header
st.markdown('<div class="header-box">', unsafe_allow_html=True)
if os.path.exists("logo.jpeg"): st.image("logo.jpeg", width=220)
st.markdown('</div>', unsafe_allow_html=True)

df = pd.read_csv(CSV_FILE)

# --- DASHBOARD ---
if st.session_state.page == "dashboard":
    c1, c2 = st.columns([3, 1])
    c1.subheader("SKD Real Estate | Active Reminders")
    if c2.button("➕ New Email", type="primary", use_container_width=True):
        st.session_state.page = "create"
        st.rerun()

    if len(df) == 0:
        st.info("No reminders scheduled.")
    else:
        for i, row in df[::-1].iterrows():
            with st.container():
                st.markdown('<div class="reminder-card">', unsafe_allow_html=True)
                col_st, col_tx, col_dt, col_dl = st.columns([0.8, 3, 2, 0.5])
                with col_st:
                    status_class = "tag-active" if row['Status'] == 'Active' else "tag-sent"
                    st.markdown(f'<span class="{status_class}">{row["Status"]}</span>', unsafe_allow_html=True)
                with col_tx:
                    st.markdown(f"**{row['Task']}**")
                    st.caption(f"To: {row['Recipient']}")
                with col_dt:
                    st.markdown(f"📅 **{row['Deadline']}**")
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
    
    with st.form("new_form"):
        st.markdown("### Schedule New Communication")
        t = st.text_input("Subject")
        e = st.text_input("Recipient(s)")
        c1, c2, c3 = st.columns(3)
        d = c1.date_input("Date", datetime.now())
        tm = c2.text_input("Time (HH:MM)", "09:00")
        r = c3.selectbox("Repeat", ["None", "Weekly", "Monthly"])
        db = st.number_input("Days Before", 0, 30, 0)
        
        if st.form_submit_button("SAVE SCHEDULE", use_container_width=True):
            new_row = pd.DataFrame([[t, e, str(d), tm, int(db), 'Active', r]], columns=COLUMNS)
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(CSV_FILE, index=False)
            st.session_state.page = "dashboard"
            st.rerun()

st.markdown(f'<div class="footer">SKD Real Estate • Managed by Yared</div>', unsafe_allow_html=True)
