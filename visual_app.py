import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os

# --- 1. SETTINGS ---
GMAIL_USER = st.secrets["GMAIL_USER"]
GMAIL_PASSWORD = st.secrets["GMAIL_PASSWORD"]
CSV_FILE = 'list.csv'
COLUMNS = ['Task', 'Recipient', 'Deadline', 'Time', 'DaysBefore', 'Status', 'Recurrence']

# --- 2. THE ENGINE (RUNS EVERY TIME THE APP LOADS) ---
def process_reminders():
    if not os.path.exists(CSV_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
        return

    df = pd.read_csv(CSV_FILE)
    now = datetime.now()
    today_date = now.date()
    current_time_str = now.strftime("%H:%M")
    updates_made = False

    for index, row in df.iterrows():
        if str(row['Status']) == 'Active':
            # Calculate when to send
            target_date = datetime.strptime(str(row['Deadline']), '%Y-%m-%d').date()
            send_date = target_date - timedelta(days=int(row['DaysBefore']))
            
            # CONDITION: Is it time or past time?
            if (today_date > send_date) or (today_date == send_date and current_time_str >= str(row['Time'])):
                
                # SEND EMAIL
                recipients = [e.strip() for e in str(row['Recipient']).split(',')]
                msg = MIMEText(f"REMINDER: {row['Task']}\nDue Date: {row['Deadline']}\n\nAutomated by SKD System.")
                msg['Subject'] = f"🔔 SKD: {row['Task']}"
                msg['From'] = GMAIL_USER
                msg['To'] = ", ".join(recipients)
                
                try:
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                        server.login(GMAIL_USER, GMAIL_PASSWORD)
                        server.send_message(msg)
                    
                    # UPDATE STATUS
                    if row['Recurrence'] == 'Weekly':
                        df.at[index, 'Deadline'] = str(target_date + timedelta(weeks=1))
                    elif row['Recurrence'] == 'Monthly':
                        df.at[index, 'Deadline'] = str(target_date + timedelta(days=30))
                    else:
                        df.at[index, 'Status'] = 'Sent'
                    
                    updates_made = True
                except Exception as e:
                    print(f"Mail Error: {e}")

    if updates_made:
        df.to_csv(CSV_FILE, index=False)

# EXECUTE ENGINE IMMEDIATELY
process_reminders()

# --- 3. SIMPLE WORKABLE INTERFACE ---
st.title("SKD Reminder Tool")

# Quick Stats
if os.path.exists(CSV_FILE):
    data = pd.read_csv(CSV_FILE)
    st.write(f"Active: {len(data[data['Status']=='Active'])} | Sent: {len(data[data['Status']=='Sent'])}")
    
    # NEW REMINDER FORM
    with st.form("add_new", clear_on_submit=True):
        st.subheader("Add New Reminder")
        t = st.text_input("Task Name")
        e = st.text_input("Emails (comma separated)")
        col1, col2, col3 = st.columns(3)
        d = col1.date_input("Deadline", datetime.now())
        tm = col2.text_input("Time (24h format)", "09:00")
        r = col3.selectbox("Repeat", ["None", "Weekly", "Monthly"])
        db = st.number_input("Days Before", 0, 30, 0)
        
        if st.form_submit_button("SAVE REMINDER"):
            new_row = pd.DataFrame([[t, e, str(d), tm, int(db), 'Active', r]], columns=COLUMNS)
            data = pd.concat([data, new_row], ignore_index=True)
            data.to_csv(CSV_FILE, index=False)
            st.rerun()

    st.divider()
    
    # SIMPLE LIST VIEW
    st.subheader("Current Schedule")
    for i, r in data[::-1].iterrows():
        col_info, col_del = st.columns([5, 1])
        status_color = "🟢" if r['Status'] == 'Active' else "⚪"
        col_info.write(f"{status_color} **{r['Task']}** | To: {r['Recipient']} | Due: {r['Deadline']} @ {r['Time']}")
        if col_del.button("Delete", key=f"d_{i}"):
            data.drop(i).to_csv(CSV_FILE, index=False)
            st.rerun()
