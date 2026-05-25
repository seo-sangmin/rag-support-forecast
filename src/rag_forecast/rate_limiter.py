from __future__ import annotations

import asyncio
import time
from collections import deque
from dataclasses import dataclass
from typing import Iterable


@dataclass
class _Reservation:
    time: float
    amount: int


class _SlidingWindow:
    """Sliding-window counter over a fixed period (default 60s).

    Each entry is a mutable ``_Reservation`` so callers can reserve a
    conservative estimate up front and then ``update`` it once the actual
    usage is known.
    """

    def __init__(self, capacity: int, seconds: float = 60.0) -> None:
        self.capacity = capacity
        self.seconds = seconds
        self.events: deque[_Reservation] = deque()

    def _purge(self, now: float) -> None:
        cutoff = now - self.seconds
        while self.events and self.events[0].time < cutoff:
            self.events.popleft()

    def used(self, now: float) -> int:
        self._purge(now)
        return sum(e.amount for e in self.events)

    def wait_seconds(self, now: float, amount: int) -> float:
        """Seconds until ``amount`` more units fit; 0 if they already fit."""
        if amount <= 0:
            return 0.0
        self._purge(now)
        used = sum(e.amount for e in self.events)
        if used + amount <= self.capacity:
            return 0.0
        if amount > self.capacity:
            # A single request larger than the whole budget will never fit;
            # wait for the window to drain and let the caller try anyway.
            return (self.events[0].time + self.seconds) - now if self.events else 0.0
        deficit = used + amount - self.capacity
        cumulative = 0
        for e in self.events:
            cumulative += e.amount
            if cumulative >= deficit:
                return max(0.0, (e.time + self.seconds) - now)
        return self.seconds

    def reserve(self, now: float, amount: int) -> _Reservation:
        r = _Reservation(time=now, amount=max(0, amount))
        self.events.append(r)
        return r

    @staticmethod
    def update(reservation: _Reservation, amount: int) -> None:
        reservation.amount = max(0, amount)


@dataclass(frozen=True)
class Reservations:
    rpm: _Reservation
    itpm: _Reservation
    otpm: _Reservation


class AsyncRateLimiter:
    """Async rate limiter enforcing requests + token-per-minute budgets.

    Designed for Anthropic per-minute caps (requests, input tokens, output
    tokens). ``acquire`` blocks until a call is allowed, then returns a
    ``Reservations`` handle. After the API call returns, the caller passes
    the real ``usage.input_tokens`` / ``usage.output_tokens`` to ``commit``
    so the window self-corrects from estimates to reality.
    """

    def __init__(
        self,
        *,
        requests_per_minute: int,
        input_tokens_per_minute: int,
        output_tokens_per_minute: int,
        window_seconds: float = 60.0,
    ) -> None:
        if requests_per_minute <= 0 or input_tokens_per_minute <= 0 or output_tokens_per_minute <= 0:
            raise ValueError("rate limits must be positive")
        self._rpm = _SlidingWindow(requests_per_minute, window_seconds)
        self._itpm = _SlidingWindow(input_tokens_per_minute, window_seconds)
        self._otpm = _SlidingWindow(output_tokens_per_minute, window_seconds)
        self._lock = asyncio.Lock()
        self._now = time.monotonic

    async def acquire(self, input_estimate: int, output_estimate: int) -> Reservations:
        while True:
            async with self._lock:
                now = self._now()
                wait = max(
                    self._rpm.wait_seconds(now, 1),
                    self._itpm.wait_seconds(now, input_estimate),
                    self._otpm.wait_seconds(now, output_estimate),
                )
                if wait <= 0:
                    return Reservations(
                        rpm=self._rpm.reserve(now, 1),
                        itpm=self._itpm.reserve(now, input_estimate),
                        otpm=self._otpm.reserve(now, output_estimate),
                    )
            await asyncio.sleep(wait + 0.05)

    async def commit(
        self,
        reservations: Reservations,
        *,
        input_actual: int,
        output_actual: int,
    ) -> None:
        async with self._lock:
            _SlidingWindow.update(reservations.itpm, int(input_actual))
            _SlidingWindow.update(reservations.otpm, int(output_actual))

    async def penalize(self, seconds: float) -> None:
        """Reserve dummy budget that expires after ``seconds`` from now.

        Used when the server returns a 429 despite proactive throttling, to
        ensure no further calls go out for at least the requested cool-down.
        """
        if seconds <= 0:
            return
        async with self._lock:
            now = self._now()
            # Park a request reservation that won't expire until ``seconds`` later.
            # We model this by placing it ``window - seconds`` in the past so the
            # purge keeps it for exactly ``seconds`` more.
            offset = self._rpm.seconds - seconds
            anchor = now - max(0.0, offset)
            self._rpm.events.append(_Reservation(time=anchor, amount=self._rpm.capacity))


def estimate_input_tokens(*texts: str) -> int:
    """Rough char-to-token approximation (~4 chars/token + small overhead)."""
    total_chars = sum(len(t) for t in texts)
    return max(1, (total_chars + 3) // 4) + 16


def parse_retry_after(headers: object, default: float) -> float:
    """Pull a ``retry-after`` / ``retry-after-ms`` value from response headers."""
    if headers is None or not hasattr(headers, "get"):
        return default
    for key in ("retry-after-ms", "Retry-After-Ms", "Retry-After-MS"):
        v = headers.get(key)
        if v is not None:
            try:
                return max(0.0, float(v) / 1000.0)
            except (TypeError, ValueError):
                pass
    for key in ("retry-after", "Retry-After"):
        v = headers.get(key)
        if v is not None:
            try:
                return max(0.0, float(v))
            except (TypeError, ValueError):
                pass
    return default


__all__: Iterable[str] = (
    "AsyncRateLimiter",
    "Reservations",
    "estimate_input_tokens",
    "parse_retry_after",
)
