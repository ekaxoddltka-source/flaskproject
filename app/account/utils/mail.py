# app/account/utils/mail.py
import smtplib
from email.mime.text import MIMEText

def send_email(to, subject, text):
    msg = MIMEText(text)
    msg["Subject"] = subject
    msg["From"] = "your_email@gmail.com"
    msg["To"] = to

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
        smtp.login("crimson0070@gmail.com", "fbgl elkr tmjo cbwl")
        smtp.send_message(msg)
