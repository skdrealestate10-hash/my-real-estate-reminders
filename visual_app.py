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
    st.error("Add Credentials to Streamlit Secrets!")
    st.stop()

CSV_FILE = 'list.csv'
# Strict column order
COLUMNS = ['Task', 'Recipient', 'Deadline', 'Time', 'Status', 'Recurrence', 'AddedAt']
UAE_TZ = pytz.timezone('Asia/Dubai')

# --- 2. THE ENGINE (STRICT LOCK) ---
def run_automation_engine():
    if not os.path.exists(CSV_FILE): return
    
    df_logic = pd.read_csv(CSV_FILE)
    if df_logic.empty: return
    
    now_uae = datetime.now(UAE_TZ)
    now_ts = time.time()
    today_str = now_uae.strftime('%Y-%m-%d')
    current_time_str = now_uae.strftime('%I:%M %p')
    
    changed = False

    for index, row in df_logic.iterrows():
        # ONLY process if Status is 'Active'
        if str(row.get('Status')) == 'Active':
            
            # --- THE SAFETY LOCK ---
            # If the task was added less than 120 seconds ago, SKIP.
            # This prevents the Save button click from triggering the email.
            added_at = float(row.get('AddedAt', 0))
            if (now_ts - added_at) < 120:
                continue

            # --- TRIGGER LOGIC ---
            is_today = str(row.get('Deadline')) == today_str
            is_past = str(row.get('Deadline')) < today_str
            is_exact_time = str(row.get('Time')) == current_time_str

            if is_past or (is_today and is_exact_time):
                try:
                    recipients = [addr.strip() for addr in str(row['Recipient']).split(',')]
                    msg = MIMEText(f"SKD Reminder: {row['Task']}\nDue: {row['Deadline']} at {row['Time']}")
                    msg['Subject'] = f"🔔 SKD REMINDER: {row['Task']}"
                    msg['From'] = GMAIL_USER
                    msg['To'] = ", ".join(recipients)
                    
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                        server.login(GMAIL_USER, GMAIL_PASSWORD)
                        server.send_message(msg)
                    
                    df_logic.at[index, 'Status'] = 'Sent'
                    changed = True
                except: continue
                
    if changed:
        df_logic.to_csv(CSV_FILE, index=False)

# --- 3. UI SETUP ---
st.set_page_config(page_title="SKD Reminders", layout="wide")

# Ensure CSV is healthy
if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
else:
    # Check if columns are correct, if not, reset it
    temp_df = pd.read_csv(CSV_FILE)
    if list(temp_df.columns) != COLUMNS:
        pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)

if "page" not in st.session_state: st.session_state.page = "dashboard"

# --- 4. DASHBOARD ---
if st.session_state.page == "dashboard":
    st.write(f"## SKD Dashboard | ⏰ {datetime.now(UAE_TZ).strftime('%I:%M %p')}")
    
    if st.button("➕ Create New Reminder", type="primary"):
        st.session_state.page = "create"
        st.rerun()

    df_view = pd.read_csv(CSV_FILE)
    for i, row in df_view[::-1].iterrows():
        with st.container():
            st.markdown(f"""
            <div style="background:white; padding:15px; border-radius:10px; border-left: 5px solid #8B0000; margin-bottom:10px; box-shadow: 2px 2px 5px rgba(0,0,0,0.05);">
                <strong>{row['Status'].upper()}</strong>: {row['Task']}<br>
                <small>To: {row['Recipient']} | 📅 {row['Deadline']} | ⏰ {row['Time']}</small>
            </div>
            """, unsafe_allow_html=True)
            if st.button("🗑️ Delete", key=f"del_{i}"):
                df_view.drop(i).to_csv(CSV_FILE, index=False)
                st.rerun()

# --- 5. CREATE PAGE ---
elif st.session_state.page == "create":
    if st.button("← Back"):
        st.session_state.page = "dashboard"
        st.rerun()
    with st.form("new_reminder"):
        t = st.text_input("Task Name")
        e = st.text_input("Recipient Email")
        d = st.date_input("Date", datetime.now(UAE_TZ))
        tm = st.text_input("Time (e.g. 10:00 AM)", value=(datetime.now(UAE_TZ) + timedelta(minutes=15)).strftime("%I:%M %p"))
        r = st.selectbox("Repeat", ["None", "Weekly", "Monthly"])
        if st.form_submit_button("SAVE"):
            if t and e:
                new_row = pd.DataFrame([[t, e, str(d), tm, 'Active', r, time.time()]], columns=COLUMNS)
                # Append to file
                pd.concat([pd.read_csv(CSV_FILE), new_row], ignore_index=True).to_csv(CSV_FILE, index=False)
                st.session_state.page = "dashboard"
                st.rerun()

# --- 6. RUN ENGINE ---
run_automation_engine()
