"""Real filesystem behavior, including atomic replacement and fail-closed load."""

import json
from unittest.mock import patch

import pytest

from custom_components.ha_mail_sender.storage import ReservationStore


async def test_atomic_roundtrip_and_remove(hass):
    store = ReservationStore(hass, "message-id")
    assert await store.async_load() == {}
    state = {"status": "pending", "last_attempt": "2026-10-19T14:00:00+02:00"}
    await store.async_save(state)
    assert await ReservationStore(hass, "message-id").async_load() == state
    assert store.path.stat().st_mode & 0o777 == 0o600
    await store.async_remove()
    assert await store.async_load() == {}


async def test_failed_replace_keeps_old_reservation(hass):
    store = ReservationStore(hass, "message-id")
    old = {"status": "pending", "last_attempt": "2026-10-19T14:00:00+02:00"}
    await store.async_save(old)
    with patch(
        "custom_components.ha_mail_sender.storage.os.replace", side_effect=OSError("disk full")
    ):
        with pytest.raises(OSError):
            await store.async_save({"status": "accepted"})
    assert await store.async_load() == old
    assert len(list(store.path.parent.iterdir())) == 1


async def test_corrupt_storage_is_not_treated_as_empty(hass):
    store = ReservationStore(hass, "message-id")
    store.path.parent.mkdir(parents=True)
    store.path.write_text("broken")
    with pytest.raises(json.JSONDecodeError):
        await store.async_load()
