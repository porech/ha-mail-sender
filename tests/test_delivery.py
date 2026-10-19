"""Behavioral tests: no external mail is sent."""

import asyncio
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from custom_components.ha_mail_sender.delivery import DeliveryController
from custom_components.ha_mail_sender.models import MailConfig, build_message

ROME = ZoneInfo("Europe/Rome")


def data(**updates):
    return dict(
        name="Request",
        google_entry_id="google-id",
        sender_name="Family",
        sender="parent@example.com",
        to="doctor@example.com",
        cc="partner@example.com",
        bcc="archive@example.com",
        subject="Richiesta",
        body="Buongiorno,\nuna richiesta. Grazie!",
        policy="daily",
        interval_hours=24,
        **updates,
    )


def test_recipients_and_utf8_message():
    config = MailConfig.from_mapping(data())
    message = build_message(config)
    assert message["To"] == "doctor@example.com"
    assert message["Cc"] == "partner@example.com"
    assert message["Bcc"] == "archive@example.com"
    assert message.get_content() == "Buongiorno,\nuna richiesta. Grazie!\n"
    assert message["Message-ID"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("to", "bad"),
        ("to", ""),
        ("cc", "valid@example.com\r\nBcc: bad@example.com"),
        ("subject", "hello\nBcc: bad@example.com"),
        ("sender", "bad"),
        ("interval_hours", 0),
        ("interval_hours", float("nan")),
        ("policy", "weird"),
        ("sender_name", "bad\nname"),
        ("body", ""),
        ("google_entry_id", ""),
        ("name", ""),
    ],
)
def test_invalid_configuration(field, value):
    values = data()
    values[field] = value
    with pytest.raises(ValueError):
        MailConfig.from_mapping(values)


class Harness:
    def __init__(self, **updates):
        values = data()
        values.update(updates)
        self.config = MailConfig.from_mapping(values)
        self.clock = datetime(2026, 10, 24, 23, 59, tzinfo=ROME)
        self.disk = {}
        self.calls = 0
        self.error = None
        self.wait = None
        self.controller = self.make()

    def make(self):
        return DeliveryController(
            self.config, dict(self.disk), self.save, self.send, lambda: self.clock, lambda: None
        )

    async def save(self, state):
        self.disk = dict(state)

    async def send(self):
        self.calls += 1
        assert self.disk["status"] == "pending"
        if self.wait:
            await self.wait.wait()
        if self.error:
            raise self.error


@pytest.mark.asyncio
async def test_daily_limit_and_local_midnight_across_dst():
    h = Harness()
    assert await h.controller.async_send() == "accepted"
    assert await h.controller.async_send() == "blocked"
    assert h.calls == 1
    assert h.controller.next_allowed().isoformat() == "2026-10-25T00:00:00+02:00"
    h.clock += timedelta(minutes=2)
    assert await h.controller.async_send() == "accepted"
    h.clock = datetime(2026, 10, 25, 23, 30, tzinfo=ROME)
    assert await h.controller.async_send() == "blocked"
    assert h.controller.next_allowed().isoformat() == "2026-10-26T00:00:00+01:00"


@pytest.mark.asyncio
async def test_interval_means_elapsed_hours_across_dst():
    h = Harness(policy="interval", interval_hours=24)
    await h.controller.async_send()
    h.clock = datetime(2026, 10, 25, 22, 59, tzinfo=ROME)
    assert await h.controller.async_send() == "accepted"
    assert h.calls == 2


@pytest.mark.asyncio
async def test_history_survives_restart():
    h = Harness()
    await h.controller.async_send()
    h.controller = h.make()
    assert await h.controller.async_send() == "blocked"
    assert h.calls == 1


@pytest.mark.asyncio
async def test_pending_after_restart_is_uncertain_and_blocked():
    h = Harness()
    h.disk = {"status": "pending", "last_attempt": h.clock.isoformat()}
    h.controller = h.make()
    assert h.controller.status == "uncertain"
    assert await h.controller.async_send() == "blocked"
    assert h.calls == 0


@pytest.mark.asyncio
async def test_concurrent_requests_are_dropped_even_without_limit():
    h = Harness(policy="none")
    h.wait = asyncio.Event()
    first = asyncio.create_task(h.controller.async_send())
    await asyncio.sleep(0)
    assert await h.controller.async_send() == "blocked"
    h.wait.set()
    assert await first == "accepted"
    assert h.calls == 1


@pytest.mark.asyncio
async def test_transport_error_stays_blocked_until_manual_reset():
    h = Harness()
    h.error = OSError("private server detail")
    assert await h.controller.async_send() == "failed"
    assert h.disk["error"] == "transport_error"
    assert "private" not in str(h.disk)
    assert await h.controller.async_send() == "blocked"
    await h.controller.async_reset()
    h.error = None
    assert await h.controller.async_send() == "accepted"


@pytest.mark.asyncio
async def test_storage_failure_prevents_sending():
    h = Harness()

    async def fail_save(state):
        raise OSError("disk full")

    h.controller.save = fail_save
    with pytest.raises(OSError):
        await h.controller.async_send()
    assert h.calls == 0


@pytest.mark.asyncio
async def test_success_history_is_not_cleared_by_reset():
    h = Harness()
    await h.controller.async_send()
    with pytest.raises(ValueError):
        await h.controller.async_reset()
    assert await h.controller.async_send() == "blocked"


@pytest.mark.asyncio
async def test_interval_does_not_expire_in_first_occurrence_of_repeated_hour():
    h = Harness(policy="interval", interval_hours=2)
    h.clock = datetime(2026, 10, 25, 1, 30, tzinfo=ROME)
    await h.controller.async_send()
    h.clock = datetime(2026, 10, 25, 2, 45, tzinfo=ROME, fold=0)
    assert await h.controller.async_send() == "blocked"
    h.clock = datetime(2026, 10, 25, 2, 30, tzinfo=ROME, fold=1)
    assert await h.controller.async_send() == "accepted"


@pytest.mark.asyncio
async def test_unload_waits_for_send_and_rejects_new_requests():
    h = Harness()
    h.wait = asyncio.Event()
    task = asyncio.create_task(h.controller.async_send())
    await asyncio.sleep(0)
    close = asyncio.create_task(h.controller.async_close())
    await asyncio.sleep(0)
    assert not close.done()
    assert await h.controller.async_send() == "blocked"
    h.wait.set()
    await task
    await close
    assert h.disk["status"] == "accepted"


@pytest.mark.asyncio
async def test_failed_final_save_leaves_durable_reservation():
    h = Harness()

    async def fail_final_save(state):
        if state["status"] != "pending":
            raise OSError("disk full")
        h.disk = dict(state)

    h.controller.save = fail_final_save
    with pytest.raises(OSError):
        await h.controller.async_send()
    assert h.disk["status"] == "pending"
    h.controller = h.make()
    assert h.controller.status == "uncertain"
    assert await h.controller.async_send() == "blocked"
    assert h.calls == 1


@pytest.mark.asyncio
async def test_blocked_request_does_not_erase_success_status():
    h = Harness()
    await h.controller.async_send()
    await h.controller.async_send()
    assert h.controller.status == "accepted"
    assert h.controller.last_result == "blocked"
    assert h.controller.state["last_accepted"]
