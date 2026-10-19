"""Saved Gmail emails with persistent per-message rate limits."""

from homeassistant.exceptions import ConfigEntryError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.dispatcher import async_dispatcher_send
from homeassistant.util import dt as dt_util

from .const import DOMAIN, PLATFORMS, signal
from .delivery import DeliveryController
from .gmail import GmailTransport
from .models import MailConfig
from .storage import ReservationStore

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup_entry(hass, entry):
    """Load the saved message and limiter history without sending mail."""
    config = MailConfig.from_mapping({**entry.data, **entry.options})
    account = hass.config_entries.async_get_entry(config.google_entry_id)
    if account is None or account.domain != "google_mail":
        raise ConfigEntryError("Configure the linked Google Mail account first")
    store = ReservationStore(hass, entry.entry_id)
    state = await store.async_load() or {}

    async def send():
        transport = await GmailTransport.async_create(hass, config.google_entry_id)
        await transport.async_send(config)

    entry.runtime_data = DeliveryController(
        config,
        state,
        store.async_save,
        send,
        dt_util.now,
        lambda: async_dispatcher_send(hass, signal(entry.entry_id)),
    )
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(async_reload_entry))
    return True


async def async_reload_entry(hass, entry):
    """Options edits keep entry identity and limiter history."""
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass, entry):
    """Drain an active send before any replacement runtime can start."""
    await entry.runtime_data.async_close()
    unloaded = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unloaded:
        entry.runtime_data.closing = False
    return unloaded


async def async_remove_entry(hass, entry):
    """Remove history only when the saved email itself is explicitly deleted."""
    await ReservationStore(hass, entry.entry_id).async_remove()
