"""Acknowledged atomic reservations: failed writes must stop submission."""

import json
import os
import tempfile
from datetime import datetime
from pathlib import Path

from .const import DOMAIN


class ReservationStore:
    """Small versioned JSON store whose writes propagate filesystem failures.

    HA Store.async_save intentionally logs some write failures instead of raising;
    it cannot acknowledge the pre-submission reservation this integration needs.
    """

    def __init__(self, hass, entry_id):
        self.hass = hass
        self.path = Path(hass.config.path(".storage", f"{DOMAIN}.{entry_id}"))

    async def async_load(self):
        return await self.hass.async_add_executor_job(self._load)

    def _load(self):
        try:
            with self.path.open(encoding="utf-8") as file:
                payload = json.load(file)
        except FileNotFoundError:
            return {}
        if payload.get("version") != 1 or not isinstance(payload.get("data"), dict):
            raise ValueError("invalid_reservation_storage")
        data = payload["data"]
        for key in ("last_attempt", "last_accepted"):
            if data.get(key) and datetime.fromisoformat(data[key]).tzinfo is None:
                raise ValueError("invalid_reservation_timestamp")
        return data

    async def async_save(self, data):
        await self.hass.async_add_executor_job(self._save, data)

    def _save(self, data):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps({"version": 1, "data": data}, ensure_ascii=False)
        descriptor, temp_name = tempfile.mkstemp(prefix=f".{self.path.name}.", dir=self.path.parent)
        try:
            with os.fdopen(descriptor, "w", encoding="utf-8") as file:
                file.write(payload)
                file.flush()
                os.fsync(file.fileno())
            os.replace(temp_name, self.path)
            directory = os.open(self.path.parent, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            Path(temp_name).unlink(missing_ok=True)

    async def async_remove(self):
        await self.hass.async_add_executor_job(self.path.unlink, True)
