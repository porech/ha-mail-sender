"""Validated, immutable saved email and MIME construction."""

import math
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from email.message import EmailMessage
from email.utils import format_datetime, formataddr, make_msgid

_ADDRESS = re.compile(r"[^\s@<>,;]+@[^\s@<>,;]+\.[^\s@<>,;]+\Z")


def addresses(value: str) -> list[str]:
    """Accept comma-separated bare ASCII addresses, rejecting header injection."""
    if not isinstance(value, str) or any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ValueError("invalid_address")
    result = []
    for item in value.split(","):
        item = item.strip()
        if not item:
            continue
        if not item.isascii() or not _ADDRESS.fullmatch(item):
            raise ValueError("invalid_address")
        if item not in result:
            result.append(item)
    return result


@dataclass(frozen=True)
class MailConfig:
    """A saved email references an existing Google Mail entry, never copies tokens."""

    name: str
    google_entry_id: str
    sender: str
    sender_name: str
    to: str
    cc: str
    bcc: str
    subject: str
    body: str
    policy: str
    interval_hours: float

    @classmethod
    def from_mapping(cls, data: dict) -> "MailConfig":
        config = cls(**{key: data[key] for key in cls.__dataclass_fields__})
        for key in ("name", "google_entry_id", "sender", "subject"):
            value = getattr(config, key)
            if not value.strip() or any(ord(c) < 32 or ord(c) == 127 for c in value):
                raise ValueError("invalid_config")
        if any(ord(c) < 32 or ord(c) == 127 for c in config.sender_name):
            raise ValueError("invalid_config")
        if len(addresses(config.sender)) != 1 or not addresses(config.to):
            raise ValueError("invalid_address")
        addresses(config.cc)
        addresses(config.bcc)
        if not config.body.strip():
            raise ValueError("invalid_config")
        if not math.isfinite(config.interval_hours) or not 0 < config.interval_hours <= 8760:
            raise ValueError("invalid_config")
        if config.policy not in ("daily", "interval", "none"):
            raise ValueError("invalid_config")
        return config


def build_message(config: MailConfig) -> EmailMessage:
    """Build Gmail API MIME. Gmail routes and removes the Bcc header on delivery."""
    message = EmailMessage()
    message["From"] = formataddr((config.sender_name, config.sender))
    message["To"] = ", ".join(addresses(config.to))
    if config.cc.strip():
        message["Cc"] = ", ".join(addresses(config.cc))
    if config.bcc.strip():
        message["Bcc"] = ", ".join(addresses(config.bcc))
    message["Subject"] = config.subject
    message["Date"] = format_datetime(datetime.now(timezone.utc))
    message["Message-ID"] = make_msgid()
    message.set_content(config.body)
    return message
