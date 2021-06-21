import smtplib, ssl
import os
import mimetypes
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart


def send_email(receive, subject, text, html, sender, password):
    port = 465  # For SSL

    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = sender
    message["To"] = receive

    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")

    message.attach(part1)
    message.attach(part2)
    # Create a secure SSL context
    context = ssl.create_default_context()

    # Loading images: logo.png and bg.png
    images = {}
    images['logo'] = './img/logo.png'
    images['bg'] = './img/bg.png'
    for i in images:
        filename = os.path.basename(images[i])
        ctype, encoding = mimetypes.guess_type(images[i])
        if ctype is None or encoding is not None:
            ctype = 'application/octet-stream'
        maintype, subtype = ctype.split('/', 1)
        if maintype == 'image':
            with open(images[i], 'rb') as img:
                file = MIMEImage(img.read(), _subtype=subtype)
        file.add_header('Content-Id', i)
        message.attach(file)

    with smtplib.SMTP_SSL("smtp.gmail.com", port, context=context) as server:
        server.login(sender, password)
        server.sendmail(sender, receive, message.as_string())