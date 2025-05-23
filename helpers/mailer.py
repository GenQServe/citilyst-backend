from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pathlib import Path
from dotenv import load_dotenv
import os
import logging
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr, SecretStr
import random
import redis.asyncio as redis
import requests
from helpers.config import settings
from jinja2 import Template
from helpers.redis import set_redis_value, get_redis_value, delete_redis_value

load_dotenv()


def render_otp_template(otp_code: str) -> str:
    with open("templates/otp_email.html", "r") as file:
        template = Template(file.read())
        return template.render(otp_code=otp_code)


def render_status_report_template(
    report_id: str,
    category_name: str,
    status: str,
    updated_at: str,
    feedback: str,
) -> str:
    with open("templates/status_report_email.html", "r") as file:
        template = Template(file.read())
        return template.render(
            report_id=report_id,
            category_name=category_name,
            status=status,
            updated_at=updated_at,
            feedback=feedback,
        )


def render_template(template_name: str, **kwargs) -> str:
    """
    Render a template with the given context.

    Args:
        template_name (str): The name of the template file.
        **kwargs: The context variables to pass to the template.

    Returns:
        str: The rendered HTML content.
    """
    template_path = Path(__file__).parent.parent / "templates" / template_name
    with open(template_path, "r") as file:
        template = Template(file.read())
        return template.render(**kwargs)


config = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USER_NAME or "",
    MAIL_PASSWORD=settings.MAIL_PASSWORD or SecretStr(""),
    MAIL_FROM=settings.MAIL_FROM or "",
    MAIL_PORT=int(settings.MAIL_PORT or 587),
    MAIL_SERVER=settings.MAIL_SERVER or "",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=False,
    TEMPLATE_FOLDER=Path(__file__).parent.parent / "templates/",
)


async def send_otp_email_async(email_to: EmailStr, user_id: str) -> bool:
    otp_code = str(random.randint(100000, 999999))
    redis_key = f"otp:{user_id}"
    await set_redis_value(redis_key, otp_code, ex=300)  # Set OTP with 5 minutes expiry
    message = MessageSchema(
        subject="Your OTP Code",
        recipients=[email_to],
        template_body={"code": otp_code},
        subtype=MessageType.html,
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
        subtype=MessageType.html,
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
        "Authorization": "Basic " + (settings.ONESIGNAL_API_KEY or ""),
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
        await set_redis_value(f"otp:{user_id}", otp, ex=300)

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


async def send_status_report_email(
    email_to: EmailStr,
    report_id: str,
    category_name: str,
    status: str,
    updated_at: str,
    feedback: str,
):
    """
    Send status report email
    """
    url = "https://onesignal.com/api/v1/notifications"
    headers = {
        "Authorization": "Basic " + (settings.ONESIGNAL_API_KEY or ""),
        "Content-Type": "application/json",
    }

    payload = {
        "app_id": settings.ONESIGNAL_APP_ID,
        "include_email_tokens": [email_to],
        "email_subject": f"Laporan {report_id} telah diperbarui",
        "email_body": render_status_report_template(
            report_id=report_id,
            category_name=category_name,
            status=status,
            updated_at=updated_at,
            feedback=feedback,
        ),
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            logging.info(f"Status report email sent successfully to {email_to}")
            return True
        else:
            logging.error(f"Failed to send status report email: {response.text}")
            return False
    except Exception as e:
        logging.error(f"Error sending status report email: {e}")
        return False
