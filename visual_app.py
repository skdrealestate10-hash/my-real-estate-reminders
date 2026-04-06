import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os
import pytz
import time

# --- 1. CONFIGURATION ---
try:
    GMAIL_USER = st.secrets["GMAIL_USER"]
    GMAIL_PASSWORD = st.secrets["GMAIL_PASSWORD"]
except:
    st.error("Please add GMAIL_USER and GMAIL_PASSWORD to Streamlit Secrets.")
    st.stop()

CSV_FILE = 'list.csv'
# 'AddedAt' is the secret key to stopping the instant send
COLUMNS = ['Task', 'Recipient', 'Deadline', 'Time', 'Status', 'Recurrence', 'AddedAt']
UAE_TZ = pytz.timezone('Asia/Dubai')

# --- 2. INITIALIZE FILE ---
if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)

if "page" not in st.session_state: st.session_state.page = "dashboard"

# --- 3. THE "GOLDEN" SENDING ENGINE ---
def run_automation_engine():
    # We load the data fresh every time
    df_logic = pd.read_csv(CSV_FILE)
    now_uae = datetime.now(UAE_TZ)
    now_ts = time.time()
    today_str = now_uae.strftime('%Y-%m-%d')
    current_time_str = now_uae.strftime('%I:%M %p')
    
    changed = False

    for index, row in df_logic.iterrows():
        if str(row['Status']) == 'Active':
            # --- THE SAFETY LOCK ---
            # If the task was added less than 60 seconds ago, SKIP IT.
            # This stops the "Save" button from triggering the email.
            added_at = float(row['AddedAt']) if 'AddedAt' in row else 0
            if (now_ts - added_at) < 60:
                continue

            # --- THE TIME CHECK ---
            is_today = str(row['Deadline']) == today_str
            is_past = str(row['Deadline']) < today_str
            # Only trigger if the minute matches EXACTLY or it is from a past day
            if is_past or (is_today and str(row['Time']) == current_time_str):
                try:
                    recipients = [addr.strip() for addr in str(row['Recipient']).split(',')]
                    msg = MIMEText(f"SKD Reminder: {row['Task']}\nDue: {row['Deadline']} at {row['Time']}")
                    msg['Subject'] = f"🔔 SKD REMINDER: {row['Task']}"
                    msg['From'] = GMAIL_USER
                    msg['To'] = ", ".join(recipients)
                    
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                        server.login(GMAIL_USER, GMAIL_PASSWORD)
                        server.send_message(msg)
                    
                    # Mark as Sent so it never fires again
                    df_logic.at[index, 'Status'] = 'Sent'
                    changed = True
                except:
                    continue
                
    if changed:
        df_logic.to_csv(CSV_FILE, index=False)

# --- 4. UI SETUP ---
st.set_page_config(page_title="SKD Reminder Center", layout="wide")
st.markdown("""
    <style>
    .stApp { background-color: #F8F9FA; }
    .card { background: white; padding: 20px; border-radius: 12px; border-left: 6px solid #8B0000; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 15px; }
    .tag-active { background: #FFF5F5; color: #8B0000; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.7rem; }
    .tag-sent { background: #F0FFF4; color: #22543D; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.7rem; }
    </style>
    """, unsafe_allow_html=True)

df = pd.read_csv(CSV_FILE)

# --- 5. DASHBOARD ---
if st.session_state.page == "dashboard":
    st.write(f"## SKD Reminder Center")
    st.write(f"⏰ **Dubai Time:** {datetime.now(UAE_TZ).strftime('%I:%M %p')}")
    
    if st.button("➕ Create New Reminder", type="primary"):
        st.session_state.page = "create"
        st.rerun()

    for i, row in df[::-1].iterrows():
        with st.container():
            st.markdown('<div class="card">', unsafe_allow_html=True)
            c1, c2, c3 = st.columns([3, 2, 0.5])
            with c1:
                status_text = str(row['Status'])
                tag_class = "tag-active" if status_text == 'Active' else "tag-sent"
                st.markdown(f'<span class="{tag_class}">{status_text.upper()}</span> **{row["Task"]}**', unsafe_allow_html=True)
                st.caption(f"Recipient: {row['Recipient']}")
            with c2:
                st.write(f"📅 {row['Deadline']} | ⏰ {row['Time']}")
            with c3:
                if st.button("🗑️", key=f"del_{i}"):
                    df.drop(i).to_csv(CSV_FILE, index=False)
                    st.rerun()
            st.markdown('</div>', unsafe_allow_html=True)

# --- 6. CREATE PAGE ---
elif st.session_state.page == "create":
    if st.button("← Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()
        
    with st.form("reminder_form"):
        st.write("### Schedule New Email")
        task_name = st.text_input("Task Name")
        email_to = st.text_input("Recipient Email")
        col_d, col_t = st.columns(2)
        date_val = col_d.date_input("Date", datetime.now(UAE_TZ))
        # We default to 10 minutes in the future for safety
        time_val = col_t.text_input("Time (e.g. 03:30 PM)", value=(datetime.now(UAE_TZ) + timedelta(minutes=10)).strftime("%I:%M %p"))
        repeat_val = st.selectbox("Repeat", ["None", "Weekly", "Monthly"])
        
        if st.form_submit_button("SAVE AND ACTIVATE"):
            if task_name and email_to:
                # IMPORTANT: Record the exact second it was saved
                now_unix = time.time()
                new_data = pd.DataFrame([[task_name, email_to, str(date_val), time_val, 'Active', repeat_val, now_unix]], columns=COLUMNS)
                df = pd.concat([df, new_data], ignore_index=True)
                df.to_csv(CSV_FILE, index=False)
                
                st.success("Task Saved! It will stay locked for 60 seconds to prevent instant sending.")
                st.session_state.page = "dashboard"
                st.rerun()

# --- 7. START THE ENGINE ---
# We run the engine at the end of every page load
run_automation_engine()

st.markdown("<br><hr><center><small>SKD Real Estate Brokerage | Developed by Yared</small></center>", unsafe_allow_html=True)
