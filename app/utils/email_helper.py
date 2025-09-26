# app/utils/email_helper.py

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from app.core.config import settings

conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=settings.MAIL_STARTTLS,
    MAIL_SSL_TLS=settings.MAIL_SSL_TLS,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

# --- MODIFIED Function ---
async def send_verification_email(email: str, token: str):
    
    # --- Use the BACKEND_URL from settings ---
    verification_url = f"{settings.FRONTEND_URL}/verify-email?token={token}"
    
    html_content = f"""
    <html><body>
        <p>Welcome! Please click the link below to verify your email address:</p>
        <a href="{verification_url}">Verify Your Email</a>
    </body></html>
    """
    
    message = MessageSchema(
        subject="Account Verification",
        recipients=[email],
        body=html_content,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)


async def send_password_reset_email(email: str, token: str):
    """Sends an email with the password reset link."""

    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

    html_content = f"""
    <html>
        <body>
            <h2>Password Reset Request</h2>
            <p>You requested a password reset. Please click the button below to set a new password. This link is valid for 30 minutes.</p>
            <a href="{reset_url}" style="background-color: #007bff; color: white; padding: 14px 25px; text-align: center; text-decoration: none; display: inline-block;">
                Reset Your Password
            </a>
            <p>If you did not request a password reset, please ignore this email.</p>
        </body>
    </html>
    """

    message = MessageSchema(
        subject="Your Password Reset Link",
        recipients=[email],
        body=html_content,
        subtype="html"
    )
    
    fm = FastMail(conf)
    await fm.send_message(message)