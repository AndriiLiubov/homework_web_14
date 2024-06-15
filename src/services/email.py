from pathlib import Path
import os
from dotenv import load_dotenv

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from src.services.auth import auth_service
from src.conf.config import settings

# load_dotenv()

email_from = settings.MAIL_FROM
email_port = settings.MAIL_PORT

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=email_from,
    MAIL_PORT=email_port,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_FROM_NAME="Check-check",
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    TEMPLATE_FOLDER=Path(__file__).parent / 'templates',
)


async def send_email(email: EmailStr, username: str, host: str):
    """
    Send a confirmation email to the user.

    This function generates an email verification token and sends a confirmation email to the user using FastMail.

    :param email: EmailStr: The recipient's email address
    :param username: str: The recipient's username
    :param host: str: The host URL for the confirmation link
    :raises ConnectionErrors: If there is an error while sending the email
    :return: None
    """
    try:
        token_verification = auth_service.create_email_token({"sub": email})
        message = MessageSchema(
            subject="Confirm your email ",
            recipients=[email],
            template_body={"host": host, "username": username, "token": token_verification},
            subtype=MessageType.html
        )

        fm = FastMail(conf)
        await fm.send_message(message, template_name="email_template.html")
    except ConnectionErrors as err:
        print(err)

