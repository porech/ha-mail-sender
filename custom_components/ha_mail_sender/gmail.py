"""Gmail API transport reusing HA's existing Google Mail OAuth credentials."""

import base64

from aiohttp import ClientTimeout
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2Session,
    async_get_config_entry_implementation,
)

from .models import MailConfig, build_message

BASE_URL = "https://gmail.googleapis.com/gmail/v1/users/me"


class GmailTransport:
    """Account identity always stays `me`; sender alias belongs in MIME From."""

    def __init__(self, session):
        self.session = session

    @classmethod
    async def async_create(cls, hass, entry_id):
        entry = hass.config_entries.async_get_entry(entry_id)
        if entry is None or entry.domain != "google_mail":
            raise ValueError("google_account_missing")
        implementation = await async_get_config_entry_implementation(hass, entry)
        return cls(OAuth2Session(hass, entry, implementation))

    async def async_aliases(self) -> dict[str, str]:
        response = await self.session.async_request(
            "GET", BASE_URL + "/settings/sendAs", timeout=ClientTimeout(total=30)
        )
        async with response:
            response.raise_for_status()
            data = await response.json()
        return {
            alias["sendAsEmail"]: alias.get("displayName", "")
            for alias in data.get("sendAs", [])
            if alias.get("verificationStatus") == "accepted"
        }

    async def async_send(self, config: MailConfig) -> None:
        aliases = await self.async_aliases()
        if config.sender not in aliases:
            raise ValueError("sender_not_verified")
        raw = base64.urlsafe_b64encode(build_message(config).as_bytes()).decode("ascii")
        response = await self.session.async_request(
            "POST", BASE_URL + "/messages/send", json={"raw": raw}, timeout=ClientTimeout(total=60)
        )
        async with response:
            response.raise_for_status()
            result = await response.json()
            if not result.get("id"):
                raise ValueError("missing_message_id")
