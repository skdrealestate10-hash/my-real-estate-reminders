import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os
import pytz

# --- 1. CONFIGURATION ---
GMAIL_USER = 'skdrealestate10@gmail.com'
GMAIL_PASSWORD = 'jukv rsyr breg irzy'
CSV_FILE = 'list.csv'

COLUMNS = ['Task', 'Recipient', 'Deadline', 'Time', 'DaysBefore', 'Status', 'Recurrence', 'LastSent']
UAE_TZ = pytz.timezone('Asia/Dubai')

# --- 2. AUTOMATION ENGINE (FINAL FIXED) ---
def run_automation_engine():
    if not os.path.exists(CSV_FILE):
        pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
        return

    df_bg = pd.read_csv(CSV_FILE)

    if 'LastSent' not in df_bg.columns:
        df_bg['LastSent'] = ''

    now_uae = datetime.now(UAE_TZ)
    now_str = now_uae.strftime('%Y-%m-%d %H:%M')

    changed = False

    for index, row in df_bg.iterrows():
        if str(row['Status']) != 'Active':
            continue

        try:
            # combine date + time
            scheduled_datetime = datetime.strptime(
                f"{row['Deadline']} {row['Time']}",
                "%Y-%m-%d %I:%M %p"
            )
            scheduled_datetime = UAE_TZ.localize(scheduled_datetime)

            scheduled_str = scheduled_datetime.strftime('%Y-%m-%d %H:%M')
            last_sent = str(row.get('LastSent', ''))

            # ✅ ONLY send at exact scheduled minute
            if now_str == scheduled_str and last_sent != scheduled_str:

                recipients = [e.strip() for e in str(row['Recipient']).split(',')]

                msg = MIMEText(f"SKD Reminder: {row['Task']}\nDue: {row['Deadline']} at {row['Time']}")
                msg['Subject'] = f"🔔 SKD REMINDER: {row['Task']}"
                msg['From'] = GMAIL_USER
                msg['To'] = ", ".join(recipients)

                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                    server.login(GMAIL_USER, GMAIL_PASSWORD)
                    server.send_message(msg)

                # mark as sent
                df_bg.at[index, 'LastSent'] = now_str

                # recurrence
                deadline_dt = datetime.strptime(str(row['Deadline']), '%Y-%m-%d')

                if row['Recurrence'] == 'Weekly':
                    df_bg.at[index, 'Deadline'] = (deadline_dt + timedelta(weeks=1)).strftime('%Y-%m-%d')

                elif row['Recurrence'] == 'Monthly':
                    df_bg.at[index, 'Deadline'] = (deadline_dt + timedelta(days=30)).strftime('%Y-%m-%d')

                else:
                    df_bg.at[index, 'Status'] = 'Sent'

                changed = True

        except Exception as e:
            print("Error:", e)
            continue

    if changed:
        df_bg.to_csv(CSV_FILE, index=False)


# RUN ENGINE
run_automation_engine()

# --- 3. UI SETUP ---
st.set_page_config(page_title="SKD Reminder Center", layout="wide")

if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)

df = pd.read_csv(CSV_FILE)

if "page" not in st.session_state:
    st.session_state.page = "dashboard"

# --- DASHBOARD ---
if st.session_state.page == "dashboard":

    active = len(df[df['Status'] == 'Active'])
    sent = len(df[df['Status'] == 'Sent'])

    st.title("📅 SKD Reminder Dashboard")
    st.write(f"Active: {active} | Sent: {sent}")
    st.write(f"Dubai Time: {datetime.now(UAE_TZ).strftime('%I:%M %p')}")

    if st.button("➕ New Email"):
        st.session_state.page = "create"
        st.rerun()

    if len(df) == 0:
        st.info("No records")
    else:
        for i, row in df[::-1].iterrows():
            st.write("---")
            st.write(f"**{row['Task']}**")
            st.write(f"To: {row['Recipient']}")
            st.write(f"📅 {row['Deadline']} | ⏰ {row['Time']}")
            st.write(f"Status: {row['Status']}")

            if st.button("Delete", key=f"del_{i}"):
                df.drop(i).to_csv(CSV_FILE, index=False)
                st.rerun()

# --- CREATE PAGE ---
elif st.session_state.page == "create":

    if st.button("← Back"):
        st.session_state.page = "dashboard"
        st.rerun()

    with st.form("add"):
        task = st.text_input("Task")
        email = st.text_input("Recipient (comma separated)")
        date = st.date_input("Date", datetime.now(UAE_TZ))
        time_input = st.text_input("Time (02:30 PM)", datetime.now(UAE_TZ).strftime("%I:%M %p"))
        repeat = st.selectbox("Repeat", ["None", "Weekly", "Monthly"])

        if st.form_submit_button("Save"):
            new = pd.DataFrame([[task, email, str(date), time_input, 0, 'Active', repeat, '']], columns=COLUMNS)
            df = pd.concat([df, new], ignore_index=True)
            df.to_csv(CSV_FILE, index=False)

            st.success("Saved!")
            st.session_state.page = "dashboard"
            st.rerun()
