import os
import smtplib
from email.message import EmailMessage
from typing import List


def require_env(name: str) -> str:
    v = os.environ.get(name)
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v


def smtp_send(to_addrs: List[str], subject: str, body: str) -> None:
    smtp_host = require_env("SMTP_HOST")
    smtp_port = int(os.environ.get("SMTP_PORT", "587"))
    smtp_user = require_env("SMTP_USER")
    smtp_pass = require_env("SMTP_PASS")
    mail_from = require_env("MAIL_FROM")

    msg = EmailMessage()
    msg["From"] = mail_from
    msg["To"] = ", ".join(to_addrs)
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(smtp_host, smtp_port, timeout=30) as s:
        s.starttls()
        s.login(smtp_user, smtp_pass)
        s.send_message(msg)
