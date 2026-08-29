from __future__ import annotations

import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from typing import List, Protocol


@dataclass(frozen=True)
class DeliveredEmail:
    recipient: str
    subject: str
    text: str
    html: str | None = None


class EmailSender(Protocol):
    def send(
        self, recipient: str, subject: str, text: str, html: str | None = None
    ) -> None: ...


class DisabledEmailSender:
    def send(
        self, recipient: str, subject: str, text: str, html: str | None = None
    ) -> None:
        return None


class RecordingEmailSender:
    """Test sender that records messages without opening a network connection."""

    def __init__(self) -> None:
        self.messages: List[DeliveredEmail] = []

    def send(
        self, recipient: str, subject: str, text: str, html: str | None = None
    ) -> None:
        self.messages.append(DeliveredEmail(recipient, subject, text, html))


class SmtpEmailSender:
    def __init__(self, host: str, port: int, sender: str) -> None:
        self.host = host
        self.port = port
        self.sender = sender

    def send(
        self, recipient: str, subject: str, text: str, html: str | None = None
    ) -> None:
        message = EmailMessage()
        message["From"] = self.sender
        message["To"] = recipient
        message["Subject"] = subject
        message.set_content(text)
        if html is not None:
            message.add_alternative(html, subtype="html")
        with smtplib.SMTP(self.host, self.port, timeout=10) as smtp:
            smtp.send_message(message)
