"""Persistent reservation and rate limits, independent of Home Assistant."""

import asyncio
from datetime import datetime, time, timedelta, timezone


class DeliveryController:
    """Serialize one saved email and reserve durably before submission."""

    def __init__(self, config, state, save, send, now, changed):
        self.config = config
        self.state = state
        if state.get("status") == "pending":
            state["status"] = "uncertain"
        self.save = save
        self.send = send
        self.now = now
        self.changed = changed
        self.lock = asyncio.Lock()
        self.closing = False
        self.last_result = None

    @property
    def status(self):
        return self.state.get("status", "ready")

    def next_allowed(self) -> datetime | None:
        """Calendar-day policy follows local dates; interval uses UTC elapsed time."""
        value = self.state.get("last_attempt")
        if not value or self.config.policy == "none":
            return None
        previous = datetime.fromisoformat(value).astimezone(self.now().tzinfo)
        if self.config.policy == "daily":
            return datetime.combine(previous.date() + timedelta(days=1), time(), self.now().tzinfo)
        return (
            previous.astimezone(timezone.utc) + timedelta(hours=self.config.interval_hours)
        ).astimezone(self.now().tzinfo)

    async def async_send(self) -> str:
        if self.closing or self.lock.locked():
            self.last_result = "blocked"
            self.changed()
            return "blocked"
        async with self.lock:
            next_time = self.next_allowed()
            if next_time and self.now().timestamp() < next_time.timestamp():
                self.last_result = "blocked"
                self.changed()
                return "blocked"
            self.state.update(status="pending", last_attempt=self.now().isoformat(), error=None)
            await self.save(dict(self.state))
            self.changed()
            try:
                await self.send()
            except Exception:
                self.state.update(status="failed", error="transport_error")
            else:
                self.state.update(
                    status="accepted", last_accepted=self.now().isoformat(), error=None
                )
            await self.save(dict(self.state))
            self.last_result = self.status
            self.changed()
            return self.status

    async def async_reset(self) -> None:
        """Only failed/uncertain reservations can be reset deliberately."""
        async with self.lock:
            if self.status not in ("failed", "uncertain"):
                raise ValueError("reset_not_allowed")
            self.state.update(status="ready", last_attempt=None, error=None)
            await self.save(dict(self.state))
            self.changed()

    async def async_close(self) -> None:
        """Wait for executor-backed sends before allowing a replacement runtime."""
        self.closing = True
        async with self.lock:
            pass
