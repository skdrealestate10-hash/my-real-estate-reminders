import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
import os
import time
import threading

# --- 1. CONFIGURATION ---
# Using your provided credentials directly for reliability
GMAIL_USER = 'skdrealestate10@gmail.com'
GMAIL_PASSWORD = 'jukv rsyr breg irzy' 
CSV_FILE = 'list.csv'
COLUMNS = ['Task', 'Recipient', 'Deadline', 'Time', 'DaysBefore', 'Status', 'Recurrence']

# --- 2. BACKGROUND ENGINE ---
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
                            msg = MIMEText(f"Hello,\n\nReminder for '{row['Task']}' scheduled for {row['Deadline']} at {row['Time']}.\n\nSent via SKD Automation.")
                            msg['Subject'] = f"🔔 SKD REMINDER: {row['Task']}"
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
                            except: pass

                if changed:
                    df_bg.to_csv(CSV_FILE, index=False)
        except: pass
        time.sleep(60)

# Start Engine Thread
if "engine_started" not in st.session_state:
    threading.Thread(target=auto_send_engine, daemon=True).start()
    st.session_state.engine_started = True

# --- 3. UI SETUP & STYLING ---
st.set_page_config(page_title="SKD | Luxury Reminders", layout="wide")

# Professional Styling
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@700&family=Inter:wght@400;600&display=swap');
    
    /* Main Background */
    .stApp { background-color: #FCFCFC; }
    
    /* Top Header Styling */
    .header-box { text-align: center; padding: 20px; background: white; border-bottom: 2px solid #D4AF37; margin-bottom: 30px; }
    .header-title { font-family: 'Playfair Display', serif; color: #8B0000; font-size: 2.5rem; margin-bottom: 0; }
    
    /* Cards & Containers */
    .reminder-card {
        background: white; padding: 25px; border-radius: 12px;
        border-left: 5px solid #8B0000; 
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
        margin-bottom: 15px; transition: 0.3s;
    }
    .reminder-card:hover { transform: translateY(-3px); box-shadow: 0 8px 20px rgba(0,0,0,0.1); }
    
    /* Buttons */
    .stButton>button { border-radius: 8px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; }
    
    /* Status Tags */
    .tag-active { background: #FFF5F5; color: #8B0000; padding: 5px 15px; border-radius: 20px; font-weight: 700; font-size: 0.8rem; border: 1px solid #8B0000; }
    .tag-sent { background: #F0FFF4; color: #22543D; padding: 5px 15px; border-radius: 20px; font-weight: 700; font-size: 0.8rem; border: 1px solid #22543D; }
    
    .footer { text-align: center; padding: 40px; color: #A0AEC0; font-size: 0.85rem; border-top: 1px solid #EEE; margin-top: 50px; }
    </style>
    """, unsafe_allow_html=True)

# Navigation
if "page" not in st.session_state: st.session_state.page = "dashboard"
def navigate_to(page_name): st.session_state.page = page_name

# Data Init
if not os.path.exists(CSV_FILE):
    pd.DataFrame(columns=COLUMNS).to_csv(CSV_FILE, index=False)
df = pd.read_csv(CSV_FILE)

# --- BRANDING HEADER ---
st.markdown('<div class="header-box">', unsafe_allow_html=True)
if os.path.exists("logo.jpeg"):
    st.image("logo.jpeg", width=250)
else:
    st.markdown('<h1 class="header-title">SKD REAL ESTATE</h1>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE 1: DASHBOARD ---
if st.session_state.page == "dashboard":
    # Top Action Bar
    c_title, c_btn = st.columns([3, 1])
    with c_title:
        st.subheader("Your Scheduled Communications")
        st.caption("Background Monitoring Active 🟢")
    with c_btn:
        st.button("➕ Create New Reminder", on_click=navigate_to, args=("create",), type="primary", use_container_width=True)

    st.write("")
    
    if len(df) == 0:
        st.info("No tasks currently scheduled. Add your first reminder to get started.")
    else:
        # Show items in reverse order (newest first)
        for index, row in df[::-1].iterrows():
            with st.container():
                st.markdown(f'<div class="reminder-card">', unsafe_allow_html=True)
                col_status, col_main, col_details, col_del = st.columns([0.8, 3, 2, 0.5])
                
                with col_status:
                    if row['Status'] == 'Active':
                        st.markdown('<span class="tag-active">ACTIVE</span>', unsafe_allow_html=True)
                    else:
                        st.markdown('<span class="tag-sent">SENT ✅</span>', unsafe_allow_html=True)
                
                with col_main:
                    st.markdown(f"<h3 style='margin:0; font-size:1.2rem;'>{row['Task']}</h3>", unsafe_allow_html=True)
                    st.markdown(f"<span style='color:#718096;'>To: {row['Recipient']}</span>", unsafe_allow_html=True)
                
                with col_details:
                    st.markdown(f"📅 **{row['Deadline']}**")
                    st.markdown(f"<span style='font-size:0.9rem;'>⏰ {row['Time']} | {row['Recurrence']}</span>", unsafe_allow_html=True)
                
                with col_del:
                    if st.button("🗑️", key=f"del_{index}"):
                        df.drop(index).to_csv(CSV_FILE, index=False)
                        st.rerun()
                
                st.markdown('</div>', unsafe_allow_html=True)

# --- PAGE 2: CREATE ---
elif st.session_state.page == "create":
    st.button("← Back to Dashboard", on_click=navigate_to, args=("dashboard",))
    
    st.markdown("<h2 style='color:#8B0000; text-align:center;'>Schedule New Reminder</h2>", unsafe_allow_html=True)
    
    with st.container():
        # Center the form
        _, form_col, _ = st.columns([1, 2, 1])
        with form_col:
            with st.form("new_schedule_form", clear_on_submit=True):
                task = st.text_input("Task/Project Name (e.g., Payment Follow-up)")
                emails = st.text_input("Recipient Email(s)", help="Separate multiple with commas")
                
                c1, c2, c3 = st.columns(3)
                with c1: date_val = st.date_input("Deadline", datetime.now() + timedelta(days=1))
                with c2: time_val = st.text_input("Time (HH:MM)", value="09:00")
                with c3: repeat_val = st.selectbox("Frequency", ["None", "Weekly", "Monthly"])
                
                days_b = st.number_input("Days Before Deadline to Send", 0, 30, 0)
                
                st.write("")
                if st.form_submit_button("CONFIRM SCHEDULE", use_container_width=True):
                    if task and emails:
                        new_entry = pd.DataFrame([[task, emails, str(date_val), time_val, int(days_b), 'Active', repeat_val]], columns=COLUMNS)
                        df = pd.concat([df, new_entry], ignore_index=True)
                        df.to_csv(CSV_FILE, index=False)
                        navigate_to("dashboard")
                        st.rerun()
                    else:
                        st.warning("Please fill in the Task and Email fields.")

# --- FOOTER ---
st.markdown(f"""
    <div class="footer">
        © {datetime.now().year} SKD Real Estate • Digital Marketing Division<br>
        Built by Yared Anbesa
    </div>
    """, unsafe_allow_html=True)
