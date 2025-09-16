from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

from homeassistant.helpers.storage import Store


class ApiUsageTracker:
    """Track monthly API usage based on timestamps returned by Imou."""

    def __init__(self, store: Store, *, save_delay: float = 30.0) -> None:
        self._store = store
        self._save_delay = save_delay
        self._period: str | None = None
        self._count: int = 0
        self._last_reset: datetime | None = None
        self._last_call: datetime | None = None
        self._listeners: set[Callable[[], None]] = set()

    async def async_load(self) -> None:
        """Load persisted usage data from storage."""

        data = await self._store.async_load()
        if not data:
            return

        self._period = data.get("period")
        self._count = int(data.get("count", 0))

        last_reset = data.get("last_reset")
        if last_reset:
            self._last_reset = self._parse_iso_datetime(last_reset)

        last_call = data.get("last_call")
        if last_call:
            self._last_call = self._parse_iso_datetime(last_call)

    @property
    def count(self) -> int:
        """Return the number of API calls performed in the current period."""

        return self._count

    @property
    def period(self) -> str | None:
        """Return the identifier of the current period (YYYY-MM)."""

        return self._period

    @property
    def last_reset(self) -> datetime | None:
        """Return when the counter was last reset."""

        return self._last_reset

    @property
    def last_call(self) -> datetime | None:
        """Return when the last API call was observed."""

        return self._last_call

    def note_call(self, date_header: str | None = None) -> None:
        """Record a single API call using the server-provided timestamp."""

        moment = self._parse_date_header(date_header)
        period = self._period_key(moment)

        if self._period != period:
            self._period = period
            self._count = 0
            self._last_reset = moment

        self._count += 1
        self._last_call = moment
        self._store.async_delay_save(self._as_dict, self._save_delay)
        self._notify_listeners()

    def async_add_listener(self, listener: Callable[[], None]) -> Callable[[], None]:
        """Register a callback invoked whenever usage changes."""

        self._listeners.add(listener)

        def _remove() -> None:
            self._listeners.discard(listener)

        return _remove

    def _notify_listeners(self) -> None:
        for listener in list(self._listeners):
            listener()

    def _as_dict(self) -> dict[str, Any]:
        return {
            "period": self._period,
            "count": self._count,
            "last_reset": self._format_datetime(self._last_reset),
            "last_call": self._format_datetime(self._last_call),
        }

    @staticmethod
    def _period_key(moment: datetime) -> str:
        return f"{moment.year:04d}-{moment.month:02d}"

    @staticmethod
    def _parse_iso_datetime(value: str) -> datetime:
        dt = datetime.fromisoformat(value)
        if dt.tzinfo is None:
            return dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)

    @staticmethod
    def _format_datetime(value: datetime | None) -> str | None:
        if value is None:
            return None
        return value.astimezone(timezone.utc).isoformat()

    @staticmethod
    def _parse_date_header(value: str | None) -> datetime:
        if value:
            try:
                parsed = parsedate_to_datetime(value)
            except (TypeError, ValueError, IndexError):
                parsed = None
            if parsed is not None:
                if parsed.tzinfo is None:
                    return parsed.replace(tzinfo=timezone.utc)
                return parsed.astimezone(timezone.utc)

        return datetime.now(timezone.utc)

