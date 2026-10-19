"""Integration constants."""

DOMAIN = "ha_mail_sender"
PLATFORMS = ["button", "sensor"]


def signal(entry_id):
    return f"{DOMAIN}_{entry_id}_updated"
