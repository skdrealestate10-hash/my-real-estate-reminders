def run_automation_engine():
    if not os.path.exists(CSV_FILE):
        pd.DataFrame(columns=COLUMNS + ['LastSent']).to_csv(CSV_FILE, index=False)
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
            scheduled_datetime = datetime.strptime(
                f"{row['Deadline']} {row['Time']}",
                "%Y-%m-%d %I:%M %p"
            )
            scheduled_datetime = UAE_TZ.localize(scheduled_datetime)

            last_sent = str(row.get('LastSent', ''))

            # ✅ ONLY send if time reached AND not already sent
            if now_uae >= scheduled_datetime and last_sent != scheduled_datetime.strftime('%Y-%m-%d %H:%M'):

                recipients = [e.strip() for e in str(row['Recipient']).split(',')]

                msg = MIMEText(f"SKD Reminder: {row['Task']}\nDue: {row['Deadline']} at {row['Time']}")
                msg['Subject'] = f"🔔 SKD REMINDER: {row['Task']}"
                msg['From'] = GMAIL_USER
                msg['To'] = ", ".join(recipients)

                with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
                    server.login(GMAIL_USER, GMAIL_PASSWORD)
                    server.send_message(msg)

                # ✅ mark as sent
                df_bg.at[index, 'LastSent'] = scheduled_datetime.strftime('%Y-%m-%d %H:%M')

                # recurrence logic
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
