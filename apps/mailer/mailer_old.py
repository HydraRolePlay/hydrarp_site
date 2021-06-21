import smtplib, ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


def send_email(receive, subject, text, sender, password, html=''):
    port = 465  # For SSL

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = receive

    part1 = MIMEText(text, "plain")
    #part2 = MIMEText(html, "html")

    message.attach(part1)
    #message.attach(part2)
    # Create a secure SSL context
    context = ssl.create_default_context()

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, receive, message.as_string())