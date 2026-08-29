from html import escape
from urllib.parse import urlencode

from app.core.config import Settings
from app.core.security import create_email_action_token
from app.db.models import User
from app.integrations.email import EmailSender


def send_verification_email(
    sender: EmailSender,
    settings: Settings,
    user: User,
    email: str,
    purpose: str,
) -> None:
    token = create_email_action_token(
        user.id,
        email,
        purpose,
        settings.secret_key,
        settings.email_token_expire_minutes,
    )
    verification_url = (
        f"{settings.web_base_url.rstrip('/')}/verify-email?{urlencode({'token': token})}"
    )
    changing = purpose == "change_email"
    subject = "Confirm your new SportsHub email" if changing else "Verify your SportsHub email"
    introduction = (
        "Confirm this address to finish changing the email on your SportsHub account."
        if changing
        else "Confirm this address to verify your new SportsHub account."
    )
    text = (
        f"Hi @{user.username},\n\n{introduction}\n\n"
        f"Verify email: {verification_url}\n\n"
        f"This link expires in {settings.email_token_expire_minutes} minutes. "
        "If you did not request this, you can ignore this message."
    )
    html = (
        f"<p>Hi @{escape(user.username)},</p><p>{escape(introduction)}</p>"
        f'<p><a href="{escape(verification_url)}">Verify email</a></p>'
        f"<p>This link expires in {settings.email_token_expire_minutes} minutes. "
        "If you did not request this, you can ignore this message.</p>"
    )
    sender.send(email, subject, text, html)


def send_password_changed_email(sender: EmailSender, user: User) -> None:
    sender.send(
        user.email,
        "Your SportsHub password was changed",
        f"Hi @{user.username},\n\nYour SportsHub password was changed. "
        "If you did not make this change, contact support immediately.",
    )


def send_email_changed_notice(sender: EmailSender, user: User, old_email: str) -> None:
    sender.send(
        old_email,
        "Your SportsHub email was changed",
        f"Hi @{user.username},\n\nYour SportsHub sign-in email was changed to {user.email}. "
        "If you did not make this change, contact support immediately.",
    )
