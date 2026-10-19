"""Each saved email exposes one send button."""

import asyncio

from homeassistant.components.button import ButtonEntity
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN

PARALLEL_UPDATES = 0


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([SendMailButton(entry)])


class SendMailButton(ButtonEntity):
    """A press always passes through the persistent delivery gate."""

    _attr_has_entity_name = True
    _attr_translation_key = "send"
    _attr_icon = "mdi:email-fast-outline"

    def __init__(self, entry):
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_send"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.runtime_data.config.name,
            manufacturer="porech",
            model="Saved Gmail message",
        )

    async def async_press(self):
        # Caller cancellation cannot release the lock while HTTP is still in flight.
        task = self.hass.async_create_task(self.entry.runtime_data.async_send())
        result = await asyncio.shield(task)
        if result == "failed":
            raise HomeAssistantError(
                "Mail submission failed or is uncertain; check the status sensor"
            )
