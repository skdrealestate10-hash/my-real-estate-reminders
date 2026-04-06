import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os

# --- 1. SETTINGS ---
GMAIL_USER = 'skdrealestate10@gmail.com'
GMAIL_PASSWORD = 'jukv rsyr breg irzy'
CSV_FILE = 'list.csv'
COLUMNS = ['Task', 'Recipient', 'Deadline', 'Time', 'DaysBefore', 'Status', 'Recurrence']

# --- 2. THE ENGINE ---
def run_engine():
    if not os.path.exists(CSV_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
        return

    df = pd.read_csv(CSV_FILE)
    now = datetime.now()
    today_str = now.strftime('%Y-%m-%d')
    current_time = now.strftime('%H:%M')
    
    changed = False

    for index, row in df.iterrows():
        if str(row['Status']) == 'Active':
            # Simplified Logic: If Deadline <= Today AND Time <= Now
            if str(row['Deadline']) <= today_str and current_time >= str(row['Time']):
                
                # SEND EMAIL
                recipients = [e.strip() for e in str(row['Recipient']).split(',')]
                msg = MIMEText(f"REMINDER: {row['Task']}\nDue: {row['Deadline']}\n\nSKD System.")
                msg['Subject'] = f"🔔 SKD: {row['Task']}"
                msg['From'] = GMAIL_USER
                msg['To'] = ", ".join(recipients)
                
                try:
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                        server.login(GMAIL_USER, GMAIL_PASSWORD)
                        server.send_message(msg)
                    
                    # Update row
                    df.at[index, 'Status'] = 'Sent'
                    changed = True
                    st.success(f"Email Sent: {row['Task']}")
                except Exception as e:
                    st.error(f"Error: {e}")

    if changed:
        df.to_csv(CSV_FILE, index=False)

# START ENGINE
run_engine()

# --- 3. UI ---
st.title("SKD Automation")

if os.path.exists(CSV_FILE):
    df = pd.read_csv(CSV_FILE)
    
    # FORM TO ADD
    with st.form("add"):
        t = st.text_input("Task Name")
        e = st.text_input("Emails")
        d = st.date_input("Date", datetime.now())
        tm = st.text_input("Time (HH:MM)", "14:20")
        if st.form_submit_button("ADD"):
            new = pd.DataFrame([[t, e, str(d), tm, 0, 'Active', 'None']], columns=COLUMNS)
            df = pd.concat([df, new], ignore_index=True)
            df.to_csv(CSV_FILE, index=False)
            st.rerun()

    st.write("### Scheduled Reminders")
    st.table(df[df['Status'] == 'Active'])
    
    if st.button("Delete All History"):
        pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
        st.rerun()
