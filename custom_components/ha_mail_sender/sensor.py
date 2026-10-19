"""Delivery status without message bodies, addresses or OAuth credentials."""

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.helpers.dispatcher import async_dispatcher_connect
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, signal

PARALLEL_UPDATES = 0


async def async_setup_entry(hass, entry, async_add_entities):
    async_add_entities([MailStatusSensor(entry)])


class MailStatusSensor(SensorEntity):
    _attr_has_entity_name = True
    _attr_translation_key = "status"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = ["ready", "pending", "accepted", "failed", "uncertain"]
    _attr_icon = "mdi:email-check-outline"
    _attr_should_poll = False

    def __init__(self, entry):
        self.entry = entry
        self._attr_unique_id = f"{entry.entry_id}_status"
        self._attr_device_info = DeviceInfo(identifiers={(DOMAIN, entry.entry_id)})

    async def async_added_to_hass(self):
        self.async_on_remove(
            async_dispatcher_connect(
                self.hass, signal(self.entry.entry_id), self.async_write_ha_state
            )
        )

    @property
    def native_value(self):
        return self.entry.runtime_data.status

    @property
    def extra_state_attributes(self):
        controller = self.entry.runtime_data
        next_time = controller.next_allowed()
        return {
            "last_result": controller.last_result,
            "last_attempt": controller.state.get("last_attempt"),
            "last_accepted": controller.state.get("last_accepted"),
            "next_allowed": next_time.isoformat() if next_time else None,
            "error": controller.state.get("error"),
        }
