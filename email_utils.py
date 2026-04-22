import os
import smtplib
from email.mime.text import MIMEText
from dotenv import load_dotenv

load_dotenv()


def send_low_stock_email(product_name: str, stock: int, amount: int):
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    admin_email = os.getenv("ADMIN_EMAIL")

    if not smtp_user or not smtp_password or not admin_email:
        print("Email settings missing. Skipping email send.")
        return

    subject = f"Low Stock Alert: {product_name}"
    body = f"""
Inventory Alert

Product: {product_name}
Current Stock: {stock}
Total Amount: {amount}

This item has reached 25% or less of its total amount.
"""

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = smtp_user
    msg["To"] = admin_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
        print(f"Low stock email sent for {product_name}")
    except Exception as e:
        print("Email error:", e)