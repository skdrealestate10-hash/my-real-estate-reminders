import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os
import pytz

# --- CONFIG ---
GMAIL_USER = 'skdrealestate10@gmail.com'
GMAIL_PASSWORD = 'jukv rsyr breg irzy'
CSV_FILE = 'list.csv'

UAE_TZ = pytz.timezone('Asia/Dubai')

COLUMNS = ['Task', 'Recipient', 'ScheduledAt', 'Status', 'Recurrence', 'LastSent']

# --- AUTOMATION ENGINE (NEW CLEAN VERSION) ---
def run_automation_engine():
    if not os.path.exists(CSV_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
        return

    df = pd.read_csv(CSV_FILE)

    if 'LastSent' not in df.columns:
        df['LastSent'] = ''

    now = datetime.now(UAE_TZ)

    changed = False

    for i, row in df.iterrows():
        if row['Status'] != 'Active':
            continue

        try:
            scheduled = datetime.fromisoformat(row['ScheduledAt'])
            scheduled = UAE_TZ.localize(scheduled) if scheduled.tzinfo is None else scheduled

            last_sent = str(row['LastSent'])

            # difference in seconds
            diff = (now - scheduled).total_seconds()

            # ✅ send only within 2-minute window
            if 0 <= diff <= 120 and last_sent != scheduled.isoformat():

                recipients = [e.strip() for e in row['Recipient'].split(',')]

                msg = MIMEText(f"Reminder: {row['Task']}\nScheduled at: {scheduled.strftime('%Y-%m-%d %I:%M %p')}")
                msg['Subject'] = f"🔔 Reminder: {row['Task']}"
                msg['From'] = GMAIL_USER
                msg['To'] = ", ".join(recipients)

                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                    server.login(GMAIL_USER, GMAIL_PASSWORD)
                    server.send_message(msg)

                # mark sent
                df.at[i, 'LastSent'] = scheduled.isoformat()

                # recurrence
                if row['Recurrence'] == 'Weekly':
                    new_time = scheduled + timedelta(weeks=1)
                    df.at[i, 'ScheduledAt'] = new_time.isoformat()

                elif row['Recurrence'] == 'Monthly':
                    new_time = scheduled + timedelta(days=30)
                    df.at[i, 'ScheduledAt'] = new_time.isoformat()

                else:
                    df.at[i, 'Status'] = 'Sent'

                changed = True

        except Exception as e:
            print("ERROR:", e)

    if changed:
        df.to_csv(CSV_FILE, index=False)


# RUN ENGINE
run_automation_engine()

# --- UI ---
st.set_page_config(page_title="Reminder System", layout="wide")

if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)

df = pd.read_csv(CSV_FILE)

if "page" not in st.session_state:
    st.session_state.page = "dashboard"

# --- DASHBOARD ---
if st.session_state.page == "dashboard":

    st.title("📅 Reminder Dashboard")

    active = len(df[df['Status'] == 'Active'])
    sent = len(df[df['Status'] == 'Sent'])

    st.write(f"Active: {active} | Sent: {sent}")
    st.write(f"Dubai Time: {datetime.now(UAE_TZ).strftime('%Y-%m-%d %I:%M %p')}")

    if st.button("➕ New Reminder"):
        st.session_state.page = "create"
        st.rerun()

    if len(df) == 0:
        st.info("No reminders yet")
    else:
        for i, row in df[::-1].iterrows():
            scheduled = datetime.fromisoformat(row['ScheduledAt'])

            st.write("---")
            st.write(f"**{row['Task']}**")
            st.write(f"To: {row['Recipient']}")
            st.write(f"📅 {scheduled.strftime('%Y-%m-%d %I:%M %p')}")
            st.write(f"Status: {row['Status']}")

            if st.button("Delete", key=f"del_{i}"):
                df.drop(i).to_csv(CSV_FILE, index=False)
                st.rerun()

# --- CREATE PAGE ---
elif st.session_state.page == "create":

    if st.button("← Back"):
        st.session_state.page = "dashboard"
        st.rerun()

    with st.form("form"):
        task = st.text_input("Task")
        email = st.text_input("Recipients (comma separated)")

        date = st.date_input("Date", datetime.now(UAE_TZ))
        time = st.time_input("Time", datetime.now(UAE_TZ).time())

        repeat = st.selectbox("Repeat", ["None", "Weekly", "Monthly"])

        if st.form_submit_button("Save"):

            # ✅ combine properly
            scheduled = datetime.combine(date, time)
            scheduled = UAE_TZ.localize(scheduled)

            new = pd.DataFrame([[
                task,
                email,
                scheduled.isoformat(),
                'Active',
                repeat,
                ''
            ]], columns=COLUMNS)

            df = pd.concat([df, new], ignore_index=True)
            df.to_csv(CSV_FILE, index=False)

            st.success("Scheduled successfully!")
            st.session_state.page = "dashboard"
            st.rerun()
