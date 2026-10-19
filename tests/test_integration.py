"""Exercise native HA flows, entities, reload and persistent limits."""

from unittest.mock import patch

import pytest
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from .test_gmail import URL, mail_data

DOMAIN = "ha_mail_sender"


def aliases(aioclient_mock):
    aioclient_mock.get(
        URL + "/settings/sendAs",
        json={
            "sendAs": [
                {
                    "sendAsEmail": "family@example.com",
                    "verificationStatus": "accepted",
                    "displayName": "Family",
                }
            ]
        },
    )


async def setup_entry(hass):
    entry = MockConfigEntry(domain=DOMAIN, title="Saved request", data=mail_data())
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_config_requires_google_account(hass):
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "google_account_missing"


async def test_native_flow_selects_verified_sender(hass, google_entry, aioclient_mock):
    aliases(aioclient_mock)
    result = await hass.config_entries.flow.async_init(DOMAIN, context={"source": "user"})
    assert result["type"] == FlowResultType.FORM
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"name": "Saved request", "google_entry_id": "google-id"}
    )
    assert result["step_id"] == "message"
    values = mail_data()
    values.pop("name")
    values.pop("google_entry_id")
    with patch("custom_components.ha_mail_sender.async_setup_entry", return_value=True):
        result = await hass.config_entries.flow.async_configure(result["flow_id"], values)
        await hass.async_block_till_done()
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert result["data"]["sender"] == "family@example.com"
    assert "token" not in result["data"]
    assert len(aioclient_mock.mock_calls) == 1  # no email on setup


async def test_send_button_and_status_and_reload_limit(hass, google_entry, aioclient_mock):
    aliases(aioclient_mock)
    aioclient_mock.post(URL + "/messages/send", json={"id": "message-id"})
    entry = await setup_entry(hass)
    button = next(s.entity_id for s in hass.states.async_all("button"))
    sensor = next(s.entity_id for s in hass.states.async_all("sensor"))
    await hass.services.async_call("button", "press", {"entity_id": button}, blocking=True)
    assert hass.states.get(sensor).state == "accepted"
    assert hass.states.get(sensor).attributes["last_accepted"]
    assert "sender" not in hass.states.get(sensor).attributes
    await hass.services.async_call("button", "press", {"entity_id": button}, blocking=True)
    assert len(aioclient_mock.mock_calls) == 2
    assert await hass.config_entries.async_reload(entry.entry_id)
    await hass.async_block_till_done()
    await hass.services.async_call("button", "press", {"entity_id": button}, blocking=True)
    assert len(aioclient_mock.mock_calls) == 2
    assert hass.states.get(sensor).state == "accepted"


async def test_edit_preserves_id_and_limit(hass, google_entry, aioclient_mock):
    aliases(aioclient_mock)
    aioclient_mock.post(URL + "/messages/send", json={"id": "message-id"})
    entry = await setup_entry(hass)
    button = next(s.entity_id for s in hass.states.async_all("button"))
    await hass.services.async_call("button", "press", {"entity_id": button}, blocking=True)
    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.MENU
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "edit"}
    )
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"name": "Renamed", "google_entry_id": "google-id"}
    )
    values = {k: v for k, v in mail_data().items() if k not in ("name", "google_entry_id")}
    values["subject"] = "Updated"
    result = await hass.config_entries.options.async_configure(result["flow_id"], values)
    await hass.async_block_till_done()
    assert result["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options["subject"] == "Updated"
    assert hass.states.get(button) is not None
    await hass.services.async_call("button", "press", {"entity_id": button}, blocking=True)
    assert sum(str(c[1]).endswith("/messages/send") for c in aioclient_mock.mock_calls) == 1


async def test_real_storage_write_failure_prevents_any_gmail_request(
    hass, google_entry, aioclient_mock
):
    aliases(aioclient_mock)
    aioclient_mock.post(URL + "/messages/send", json={"id": "message-id"})
    entry = await setup_entry(hass)
    button = next(s.entity_id for s in hass.states.async_all("button"))
    with patch(
        "custom_components.ha_mail_sender.storage.os.replace", side_effect=OSError("disk full")
    ):
        with pytest.raises(Exception):
            await hass.services.async_call("button", "press", {"entity_id": button}, blocking=True)
    assert len(aioclient_mock.mock_calls) == 0
    assert entry.runtime_data.state["status"] == "pending"
