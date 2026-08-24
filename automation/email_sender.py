"""SMTP email delivery for weekly Lotto reports."""

from __future__ import annotations

import mimetypes
import os
import smtplib
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path


class EmailConfigError(Exception):
    """Raised when email delivery is requested without required settings."""


@dataclass(frozen=True, slots=True)
class EmailSettings:
    """Store SMTP settings loaded from environment variables."""

    enabled: bool
    smtp_host: str
    smtp_port: int
    username: str
    password: str
    sender: str
    recipients: tuple[str, ...]
    use_tls: bool = True

    @classmethod
    def from_environment(cls) -> "EmailSettings":
        """Build email settings from environment variables."""
        enabled = _truthy(os.getenv("LOTTO_EMAIL_ENABLED", "false"))
        recipients = tuple(
            item.strip()
            for item in os.getenv("LOTTO_EMAIL_TO", "").replace(";", ",").split(",")
            if item.strip()
        )
        return cls(
            enabled=enabled,
            smtp_host=os.getenv("LOTTO_SMTP_HOST", ""),
            smtp_port=int(os.getenv("LOTTO_SMTP_PORT", "587")),
            username=os.getenv("LOTTO_SMTP_USERNAME", ""),
            password=os.getenv("LOTTO_SMTP_PASSWORD", ""),
            sender=os.getenv("LOTTO_EMAIL_FROM", os.getenv("LOTTO_SMTP_USERNAME", "")),
            recipients=recipients,
            use_tls=_truthy(os.getenv("LOTTO_SMTP_USE_TLS", "true")),
        )

    def validate(self) -> None:
        """Validate required email settings when email sending is enabled."""
        if not self.enabled:
            raise EmailConfigError("Email delivery is disabled.")
        missing = []
        if not self.smtp_host:
            missing.append("LOTTO_SMTP_HOST")
        if not self.username:
            missing.append("LOTTO_SMTP_USERNAME")
        if not self.password:
            missing.append("LOTTO_SMTP_PASSWORD")
        if not self.sender:
            missing.append("LOTTO_EMAIL_FROM")
        if not self.recipients:
            missing.append("LOTTO_EMAIL_TO")
        if missing:
            raise EmailConfigError(f"Missing email settings: {', '.join(missing)}")


def send_email_report(
    subject: str,
    body: str,
    attachments: list[Path],
    settings: EmailSettings | None = None,
    html_body: str | None = None,
) -> None:
    """Send an individual email to each recipient so addresses stay private."""
    active_settings = settings or EmailSettings.from_environment()
    active_settings.validate()

    with smtplib.SMTP(active_settings.smtp_host, active_settings.smtp_port, timeout=30) as smtp:
        if active_settings.use_tls:
            smtp.starttls()
        smtp.login(active_settings.username, active_settings.password)
        for recipient in active_settings.recipients:
            message = EmailMessage()
            message["Subject"] = subject
            message["From"] = active_settings.sender
            message["To"] = recipient
            message.set_content(body)
            if html_body is not None:
                message.add_alternative(html_body, subtype="html")
            for attachment in attachments:
                _attach_file(message, attachment)
            smtp.send_message(message)


def _attach_file(message: EmailMessage, path: Path) -> None:
    """Attach one file to an email message."""
    if not path.exists():
        return
    content_type, _ = mimetypes.guess_type(path.name)
    if content_type:
        maintype, subtype = content_type.split("/", 1)
    else:
        maintype, subtype = "application", "octet-stream"
    message.add_attachment(
        path.read_bytes(),
        maintype=maintype,
        subtype=subtype,
        filename=path.name,
    )


def _truthy(value: str) -> bool:
    """Return whether an environment variable string should be treated as true."""
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}
