from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from pathlib import Path
from dotenv import load_dotenv
import os
import logging
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr
import random
import redis.asyncio as redis
import requests
from helpers.config import settings
from jinja2 import Template

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
redis_client = redis.from_url(REDIS_URL, decode_responses=True)


def render_otp_template(otp_code: str) -> str:
    with open("templates/otp_email.html", "r") as file:
        template = Template(file.read())
        return template.render(otp_code=otp_code)


config = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USER_NAME"),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD"),
    MAIL_FROM=os.getenv("MAIL_FROM"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", "587")),
    MAIL_SERVER=os.getenv("MAIL_SERVER"),
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / "templates/",
)


async def send_otp_email_async(email_to: EmailStr, user_id: str) -> bool:
    otp_code = str(random.randint(100000, 999999))
    redis_key = f"otp:{user_id}"
    await redis_client.set(redis_key, otp_code, ex=300)  # Set OTP with 5 minutes expiry
    message = MessageSchema(
        subject="Your OTP Code",
        recipients=[email_to],
        template_body={"code": otp_code},
        subtype="html",
    )

    fm = FastMail(config)
    try:
        await fm.send_message(message, template_name="otp_email.html")
        logging.info(f"OTP email sent to {email_to}")
        return True
    except Exception as e:
        logging.error(f"Failed to send OTP email: {e}")
        return False


async def send_email_async(subject: str, email_to: EmailStr, body: dict, template: str):
    if not config:
        logging.error("Email configuration is not initialized")
        return False

    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        template_body=body,
        subtype="html",
    )

    fm = FastMail(config)
    try:
        await fm.send_message(message, template_name=template)
        logging.info(f"Email sent successfully to {email_to}")
        return True
    except ConnectionErrors as e:
        logging.error(f"Failed to send email: {e}")
        return False
    except Exception as e:
        logging.error(f"Unexpected error sending email: {e}")
        return False


async def send_otp_email(email_to: EmailStr, user_id: str):
    """
    Send OTP email

    Args:
        email_to: Recipient email
        otp: OTP code

    Returns:
        bool: True if email sent successfully, False otherwise
    """

    otp = str(random.randint(100000, 999999))

    url = "https://onesignal.com/api/v1/notifications"
    headers = {
        "Authorization": "Basic " + settings.ONESIGNAL_API_KEY,
        "Content-Type": "application/json",
    }
    otp_html_content = render_otp_template(otp)

    payload = {
        "app_id": settings.ONESIGNAL_APP_ID,
        "include_email_tokens": [email_to],
        "email_subject": "Kode OTP Anda",
        "email_body": otp_html_content,
    }
    try:
        await redis_client.set(f"otp:{user_id}", otp, ex=300)

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            logging.info(f"OTP email sent successfully to {email_to}")
            return True
        else:
            logging.error(f"Failed to send OTP email: {response.text}")
            return False
    except Exception as e:
        logging.error(f"Error sending OTP email: {e}")
        return False
