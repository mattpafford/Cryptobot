import smtplib
from email.message import EmailMessage


def email_alert(email, pword, subject, body, to) -> str:
    msg = EmailMessage()
    msg.set_content(body)
    msg["subject"] = subject
    msg["to"] = to
    msg["from"] = email

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(email, pword)
    server.send_message(msg)

    server.quit()
