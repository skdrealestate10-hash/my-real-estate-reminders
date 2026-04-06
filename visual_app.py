import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os
import time
import threading

# --- CONFIGURATION ---
GMAIL_USER = 'skdrealestate10@gmail.com'
GMAIL_PASSWORD = 'jukv rsyr breg irzy' 
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
                            msg = MIMEText(f"Hello,\n\nReminder for '{row['Task']}' scheduled for {row['Deadline']} at {row['Time']}.")
                            msg['Subject'] = f"🔔 AUTO-REMINDER: {row['Task']}"
                            msg['From'] = GMAIL_USER
                            msg['To'] = row['Recipient']
                            
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
                            except:
                                pass

                if changed:
                    df_bg.to_csv(CSV_FILE, index=False)
        except:
            pass
        time.sleep(60)

# Start Engine
if "engine_started" not in st.session_state:
    threading.Thread(target=auto_send_engine, daemon=True).start()
    st.session_state.engine_started = True

# --- APP INTERFACE SETUP ---
st.set_page_config(page_title="SendRecurring", layout="wide")

# Load Data
if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
df = pd.read_csv(CSV_FILE)

# Navigation Logic
if "page" not in st.session_state:
    st.session_state.page = "dashboard"

def go_to_create(): st.session_state.page = "create"
def go_to_dashboard(): st.session_state.page = "dashboard"

# --- PAGE 1: DASHBOARD ---
if st.session_state.page == "dashboard":
    col_logo, col_new = st.columns([3, 1])
    with col_logo:
        st.title("S SendRecurring")
        st.caption("Automatic background sending is ACTIVE 🟢")
    with col_new:
        st.button("➕ New Email", on_click=go_to_create, type="primary")

    st.markdown("### Scheduled Reminders")
    if len(df) == 0:
        st.info("No reminders yet. Click 'New Email' to start.")
    else:
        for index, row in df[::-1].iterrows():
            with st.container():
                c1, c2, c3, c4 = st.columns([1, 4, 3, 1])
                with c1:
                    st.markdown(f"## {'✅' if row['Status'] == 'Sent' else '⏳'}")
                with c2:
                    st.markdown(f"**{row['Task']}**")
                    st.caption(f"To: {row['Recipient']}")
                with c3:
                    st.write(f"📅 Due: {row['Deadline']}")
                    st.caption(f"⏰ {row['Time']} | {row['Recurrence']}")
                with c4:
                    if st.button("❌", key=f"del_{index}"):
                        df.drop(index).to_csv(CSV_FILE, index=False)
                        st.rerun()
                st.markdown("---")

# --- PAGE 2: CREATE ---
elif st.session_state.page == "create":
    st.button("← Back", on_click=go_to_dashboard)
    st.header("Schedule New Email")
    
    with st.form("new_form"):
        task_name = st.text_input("Subject / Task")
        target_email = st.text_input("Recipient Email")
        
        col_d, col_t, col_r = st.columns(3)
        with col_d:
            d_date = st.date_input("Deadline Date", datetime.now() + timedelta(days=7))
        with col_t:
            d_time = st.text_input("Time (HH:MM)", value="09:00")
        with col_r:
            recur = st.selectbox("Repeat", ["None", "Weekly", "Monthly"])
        
        remind_days = st.number_input("Days before deadline", 0, 30, 1)
        
        if st.form_submit_button("Schedule Now"):
            new_row = pd.DataFrame([[task_name, target_email, str(d_date), d_time, int(remind_days), 'Active', recur]], columns=COLUMNS)
            df = pd.concat([df, new_row], ignore_index=True)
            df.to_csv(CSV_FILE, index=False)
            st.session_state.page = "dashboard"
            st.rerun()
