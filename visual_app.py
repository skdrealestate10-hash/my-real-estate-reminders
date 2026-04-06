import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os
import pytz
import time

# --- 1. CONFIG & SYSTEM ---
try:
    GMAIL_USER = st.secrets["GMAIL_USER"]
    GMAIL_PASSWORD = st.secrets["GMAIL_PASSWORD"]
except:
    st.error("Missing Secrets!")
    st.stop()

CSV_FILE = 'list.csv'
COLUMNS = ['Task', 'Recipient', 'Deadline', 'Time', 'Status', 'Recurrence', 'AddedAt']
UAE_TZ = pytz.timezone('Asia/Dubai')

# --- 2. ADVANCED STYLING (SKD BRANDING) ---
st.set_page_config(page_title="SKD | Control Center", layout="wide", page_icon="🔔")

st.markdown("""
    <style>
    /* Main Background */
    .stApp { background-color: #0F172A; color: #FFFFFF; }
    
    /* Luxury Card Design */
    .reminder-card {
        background: #1E293B;
        border-radius: 15px;
        padding: 20px;
        margin-bottom: 15px;
        border-left: 5px solid #D4AF37; /* Gold Accent */
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    
    /* Status Badges */
    .status-active {
        background: rgba(212, 175, 55, 0.2);
        color: #D4AF37;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: bold;
        border: 1px solid #D4AF37;
    }
    .status-sent {
        background: rgba(34, 197, 94, 0.2);
        color: #4ADE80;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: bold;
        border: 1px solid #4ADE80;
    }
    
    /* Sidebar & Buttons */
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .time-display {
        font-size: 1.5rem;
        font-weight: 700;
        color: #D4AF37;
        margin-bottom: 20px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. DATA PERSISTENCE ---
if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
df = pd.read_csv(CSV_FILE)

if "page" not in st.session_state: st.session_state.page = "dashboard"

# --- 4. THE RELIABLE ENGINE (AS DISCUSSED) ---
def run_automation_engine():
    df_logic = pd.read_csv(CSV_FILE)
    if df_logic.empty: return
    now_uae = datetime.now(UAE_TZ)
    now_ts = time.time()
    today_str = now_uae.strftime('%Y-%m-%d')
    changed = False

    for index, row in df_logic.iterrows():
        if str(row.get('Status')) == 'Active':
            added_at = float(row.get('AddedAt', 0))
            if (now_ts - added_at) < 120: continue # The 2-minute safety gap

            try:
                sched_time = datetime.strptime(str(row.get('Time')), '%I:%M %p').time()
                is_today = str(row.get('Deadline')) == today_str
                is_past_day = str(row.get('Deadline')) < today_str
                
                if is_past_day or (is_today and now_uae.time() >= sched_time):
                    # Email Logic
                    recipients = [addr.strip() for addr in str(row['Recipient']).split(',')]
                    msg = MIMEText(f"SKD Reminder: {row['Task']}\nDue: {row['Deadline']} at {row['Time']}")
                    msg['Subject'] = f"🔔 SKD URGENT: {row['Task']}"
                    msg['From'] = GMAIL_USER
                    msg['To'] = ", ".join(recipients)
                    
                    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                        server.login(GMAIL_USER, GMAIL_PASSWORD)
                        server.send_message(msg)
                    
                    df_logic.at[index, 'Status'] = 'Sent'
                    changed = True
            except: continue
    if changed: df_logic.to_csv(CSV_FILE, index=False)

# --- 5. PAGE: DASHBOARD ---
if st.session_state.page == "dashboard":
    col_h1, col_h2 = st.columns([2, 1])
    with col_h1:
        st.markdown("<h1 style='margin-bottom:0;'>SKD REAL ESTATE</h1>", unsafe_allow_html=True)
        st.markdown("<p style='color:#94A3B8;'>Digital Marketing Reminder Control</p>", unsafe_allow_html=True)
    with col_h2:
        st.markdown(f"<div class='time-display'>{datetime.now(UAE_TZ).strftime('%I:%M %p')} <small>GST</small></div>", unsafe_allow_html=True)

    st.divider()

    c1, c2, c3 = st.columns(3)
    c1.metric("Active Tasks", len(df[df['Status'] == 'Active']))
    c2.metric("Sent Today", len(df[df['Status'] == 'Sent']))
    if c3.button("➕ CREATE NEW REMINDER", type="primary", use_container_width=True):
        st.session_state.page = "create"
        st.rerun()

    st.write("### Communication Queue")
    
    if len(df) == 0:
        st.info("Your queue is empty. Start by creating a new reminder.")
    else:
        for i, row in df[::-1].iterrows():
            status_class = "status-active" if row['Status'] == 'Active' else "status-sent"
            with st.container():
                st.markdown(f"""
                <div class="reminder-card">
                    <div style="display: flex; justify-content: space-between;">
                        <span class="{status_class}">{row['Status'].upper()}</span>
                        <span style="color:#94A3B8; font-size:0.8rem;">ID: #{i}</span>
                    </div>
                    <h3 style="margin:10px 0;">{row['Task']}</h3>
                    <div style="color:#CBD5E1; font-size:0.9rem;">
                        👤 Recipient: <b>{row['Recipient']}</b><br>
                        📅 Schedule: <b>{row['Deadline']} at {row['Time']}</b>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                if st.button(f"🗑️ Delete #{i}", key=f"del_{i}", use_container_width=True):
                    df.drop(i).to_csv(CSV_FILE, index=False)
                    st.rerun()

# --- 6. PAGE: CREATE ---
elif st.session_state.page == "create":
    st.markdown("## ➕ New Schedule")
    if st.button("← Back to Dashboard"):
        st.session_state.page = "dashboard"
        st.rerun()

    with st.form("luxury_form"):
        t_input = st.text_input("Task Description (e.g., Follow up with Marina Gate Lead)")
        e_input = st.text_input("Recipient Email")
        c1, c2 = st.columns(2)
        d_input = c1.date_input("Scheduled Date", datetime.now(UAE_TZ))
        tm_input = c2.text_input("Scheduled Time", value=(datetime.now(UAE_TZ) + timedelta(minutes=15)).strftime("%I:%M %p"))
        r_input = st.selectbox("Recurrence", ["None", "Weekly", "Monthly"])
        
        if st.form_submit_button("ACTIVATE REMINDER"):
            if t_input and e_input:
                new_entry = pd.DataFrame([[t_input, e_input, str(d_input), tm_input, 'Active', r_input, time.time()]], columns=COLUMNS)
                pd.concat([pd.read_csv(CSV_FILE), new_entry], ignore_index=True).to_csv(CSV_FILE, index=False)
                st.success("Successfully added to the SKD Queue.")
                st.session_state.page = "dashboard"
                st.rerun()

# --- 7. FOOTER & ENGINE ---
run_automation_engine()
st.markdown("<br><div style='text-align:center; color:#475569; font-size:0.8rem;'>SKD Real Estate Brokerage © 2026 | Manager: Yared</div>", unsafe_allow_html=True)
