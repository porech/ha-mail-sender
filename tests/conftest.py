"""Enable discovery of this custom integration in real HA tests."""

import time

import pytest
from homeassistant.helpers import config_entry_oauth2_flow as oauth
from pytest_homeassistant_custom_component.common import MockConfigEntry


@pytest.fixture(autouse=True)
def custom_integrations(enable_custom_integrations):
    yield


@pytest.fixture
def google_entry(hass):
    entry = MockConfigEntry(
        domain="google_mail",
        entry_id="google-id",
        title="account@gmail.com",
        data={
            "auth_implementation": "google_mail",
            "token": {"access_token": "test-token", "expires_at": time.time() + 3600},
        },
    )
    entry.add_to_hass(hass)
    oauth.async_register_implementation(
        hass,
        "google_mail",
        oauth.LocalOAuth2Implementation(
            hass,
            "google_mail",
            "test-client",
            "test-secret",
            "https://example.com/auth",
            "https://example.com/token",
        ),
    )
    return entry


@pytest.fixture(autouse=True)
def reservation_directory(hass, tmp_path):
    hass.config.config_dir = str(tmp_path)
