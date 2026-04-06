import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os

# --- 1. SETTINGS & AUTH ---
GMAIL_USER = 'skdrealestate10@gmail.com'
GMAIL_PASSWORD = 'jukv rsyr breg irzy'
CSV_FILE = 'list.csv'
COLUMNS = ['Task', 'Recipient', 'Deadline', 'Time', 'DaysBefore', 'Status', 'Recurrence']

# --- 2. RELIABLE ENGINE (RUNS FIRST) ---
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
            if str(row['Deadline']) <= today_str and current_time >= str(row['Time']):
                recipients = [e.strip() for e in str(row['Recipient']).split(',')]
                msg = MIMEText(f"Reminder: {row['Task']}\nDue: {row['Deadline']}\n\nSKD Real Estate Automation")
                msg['Subject'] = f"🔔 SKD REMINDER: {row['Task']}"
                msg['From'] = GMAIL_USER
                msg['To'] = ", ".join(recipients)
                
                try:
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                        server.login(GMAIL_USER, GMAIL_PASSWORD)
                        server.send_message(msg)
                    df.at[index, 'Status'] = 'Sent'
                    changed = True
                except: pass

    if changed:
        df.to_csv(CSV_FILE, index=False)

run_engine()

# --- 3. PREMIUM UI DESIGN ---
st.set_page_config(page_title="SKD Reminders", layout="wide")

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; background-color: #F8FAFC; }
    .main-header { text-align: center; padding: 20px 0; }
    .card { background: white; padding: 20px; border-radius: 12px; border: 1px solid #E2E8F0; margin-bottom: 10px; }
    .stButton>button { border-radius: 8px; font-weight: 600; }
    .footer { text-align: center; color: #94A3B8; font-size: 0.8rem; margin-top: 50px; }
    </style>
    """, unsafe_allow_html=True)

# Branding Header
st.markdown('<div class="main-header">', unsafe_allow_html=True)
if os.path.exists("logo.jpeg"):
    st.image("logo.jpeg", width=220)
st.markdown('<h1 style="color: #1E293B; margin-top:10px;">SKD Reminder Center</h1>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- 4. APP CONTENT ---
df = pd.read_csv(CSV_FILE)

# Layout: Form on the left, List on the right
col_form, col_list = st.columns([1, 2])

with col_form:
    st.subheader("➕ New Reminder")
    with st.form("add_form", clear_on_submit=True):
        t = st.text_input("Task/Property Name", placeholder="e.g. Azizi Mirage Payment")
        e = st.text_input("Recipient Emails", placeholder="client@gmail.com, agent@gmail.com")
        d = st.date_input("Deadline Date", datetime.now())
        tm = st.text_input("Time (HH:MM)", value=datetime.now().strftime("%H:%M"))
        
        if st.form_submit_button("SCHEDULE NOW", use_container_width=True):
            if t and e:
                new_row = pd.DataFrame([[t, e, str(d), tm, 0, 'Active', 'None']], columns=COLUMNS)
                df = pd.concat([df, new_row], ignore_index=True)
                df.to_csv(CSV_FILE, index=False)
                st.rerun()

with col_list:
    st.subheader("📅 Active Schedule")
    active_df = df[df['Status'] == 'Active']
    
    if len(active_df) == 0:
        st.info("No active reminders. Start by adding one on the left.")
    else:
        for i, r in active_df[::-1].iterrows():
            with st.container():
                st.markdown(f"""
                <div class="card">
                    <div style="display: flex; justify-content: space-between;">
                        <b>{r['Task']}</b>
                        <span style="color: #4338CA; font-weight: 700;">ACTIVE</span>
                    </div>
                    <div style="font-size: 0.9rem; color: #64748B;">
                        To: {r['Recipient']}<br>
                        Due: {r['Deadline']} at {r['Time']}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"Delete Task {i}", key=f"del_{i}"):
                    df.drop(i).to_csv(CSV_FILE, index=False)
                    st.rerun()

st.markdown("---")
if st.button("Clear All Sent History"):
    df = df[df['Status'] == 'Active']
    df.to_csv(CSV_FILE, index=False)
    st.rerun()

st.markdown('<div class="footer">SKD Real Estate Internal Tool • Managed by Yared</div>', unsafe_allow_html=True)
