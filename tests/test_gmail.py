"""Gmail request contract: account and From alias remain separate."""

import base64
from email import policy
from email.parser import BytesParser

import pytest

from custom_components.ha_mail_sender.gmail import GmailTransport
from custom_components.ha_mail_sender.models import MailConfig

URL = "https://gmail.googleapis.com/gmail/v1/users/me"


def mail_data():
    return dict(
        name="Saved request",
        google_entry_id="google-id",
        sender="family@example.com",
        sender_name="Family",
        to="office@example.com",
        cc="partner@example.com",
        bcc="archive@example.com",
        subject="Richiesta città",
        body="Buongiorno,\nè una richiesta. Grazie!",
        policy="daily",
        interval_hours=24,
    )


@pytest.mark.asyncio
async def test_api_uses_me_and_verified_from_alias(hass, google_entry, aioclient_mock):
    aioclient_mock.get(
        URL + "/settings/sendAs",
        json={"sendAs": [{"sendAsEmail": "family@example.com", "verificationStatus": "accepted"}]},
    )
    aioclient_mock.post(URL + "/messages/send", json={"id": "message-id"})
    transport = await GmailTransport.async_create(hass, "google-id")
    await transport.async_send(MailConfig.from_mapping(mail_data()))
    request = aioclient_mock.mock_calls[-1]
    raw = request[2]["raw"]
    message = BytesParser(policy=policy.default).parsebytes(base64.urlsafe_b64decode(raw))
    assert message["From"] == "Family <family@example.com>"
    assert message["To"] == "office@example.com"
    assert message["Cc"] == "partner@example.com"
    assert message["Bcc"] == "archive@example.com"
    assert message["Subject"] == "Richiesta città"
    assert message.get_content() == "Buongiorno,\nè una richiesta. Grazie!\n"
    assert str(request[1]) == URL + "/messages/send"


@pytest.mark.asyncio
async def test_unverified_alias_never_submits(hass, google_entry, aioclient_mock):
    aioclient_mock.get(
        URL + "/settings/sendAs",
        json={"sendAs": [{"sendAsEmail": "family@example.com", "verificationStatus": "pending"}]},
    )
    transport = await GmailTransport.async_create(hass, "google-id")
    with pytest.raises(ValueError, match="sender_not_verified"):
        await transport.async_send(MailConfig.from_mapping(mail_data()))
    assert len(aioclient_mock.mock_calls) == 1


@pytest.mark.asyncio
async def test_api_error_is_not_retried(hass, google_entry, aioclient_mock):
    aioclient_mock.get(
        URL + "/settings/sendAs",
        json={"sendAs": [{"sendAsEmail": "family@example.com", "verificationStatus": "accepted"}]},
    )
    aioclient_mock.post(URL + "/messages/send", status=503)
    transport = await GmailTransport.async_create(hass, "google-id")
    with pytest.raises(Exception):
        await transport.async_send(MailConfig.from_mapping(mail_data()))
    assert len(aioclient_mock.mock_calls) == 2
