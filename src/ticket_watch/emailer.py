import mimetypes
import smtplib
import ssl
from email.message import EmailMessage
from pathlib import Path


def send_report(
    *, host: str, port: int, username: str, password: str, sender: str,
    recipient: str, subject: str, body: str, attachment: Path, use_ssl: bool = True,
) -> None:
    message = EmailMessage()
    message["From"] = sender
    message["To"] = recipient
    message["Subject"] = subject
    message.set_content(body)
    content_type, _ = mimetypes.guess_type(attachment.name)
    maintype, subtype = (content_type or "text/csv").split("/", 1)
    message.add_attachment(
        attachment.read_bytes(), maintype=maintype, subtype=subtype, filename=attachment.name
    )
    context = ssl.create_default_context()
    if use_ssl:
        with smtplib.SMTP_SSL(host, port, context=context, timeout=30) as smtp:
            smtp.login(username, password)
            smtp.send_message(message)
    else:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.starttls(context=context)
            smtp.login(username, password)
            smtp.send_message(message)

