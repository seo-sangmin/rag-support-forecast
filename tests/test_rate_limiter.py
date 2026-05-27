from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag_forecast.rate_limiter import (  # noqa: E402
    AsyncRateLimiter,
    estimate_input_tokens,
    parse_retry_after,
)


class FakeClock:
    def __init__(self, start: float = 1000.0) -> None:
        self.t = start

    def __call__(self) -> float:
        return self.t

    def advance(self, dt: float) -> None:
        self.t += dt


def _limiter(rpm: int = 10, itpm: int = 1000, otpm: int = 200) -> tuple[AsyncRateLimiter, FakeClock]:
    lim = AsyncRateLimiter(
        requests_per_minute=rpm,
        input_tokens_per_minute=itpm,
        output_tokens_per_minute=otpm,
    )
    clock = FakeClock()
    lim._now = clock  # type: ignore[assignment]
    return lim, clock


async def test_acquire_passes_under_capacity() -> None:
    lim, clock = _limiter(rpm=5, itpm=1000, otpm=200)
    res = await lim.acquire(input_estimate=100, output_estimate=50)
    assert res.rpm.amount == 1
    assert res.itpm.amount == 100
    assert res.otpm.amount == 50


async def test_full_request_window_reports_wait_for_oldest_to_expire() -> None:
    lim, clock = _limiter(rpm=2, itpm=10_000, otpm=10_000)
    await lim.acquire(input_estimate=10, output_estimate=10)
    clock.advance(20.0)
    await lim.acquire(input_estimate=10, output_estimate=10)
    # Window is now full. A 3rd request must wait ~40s for the oldest to age out.
    wait = lim._rpm.wait_seconds(clock(), 1)
    assert 39.9 <= wait <= 40.1
    # After the oldest expires, the wait drops to zero.
    clock.advance(40.5)
    assert lim._rpm.wait_seconds(clock(), 1) == 0.0


async def test_commit_replaces_estimate_with_actual() -> None:
    lim, clock = _limiter(rpm=100, itpm=1000, otpm=500)
    res = await lim.acquire(input_estimate=400, output_estimate=400)
    # Output window almost full from the conservative estimate.
    assert lim._otpm.used(clock()) == 400
    await lim.commit(res, input_actual=80, output_actual=100)
    # After committing the real usage, the window has more room.
    assert lim._otpm.used(clock()) == 100
    assert lim._itpm.used(clock()) == 80


async def test_window_expires_old_reservations() -> None:
    lim, clock = _limiter(rpm=2, itpm=1000, otpm=200)
    await lim.acquire(input_estimate=10, output_estimate=10)
    await lim.acquire(input_estimate=10, output_estimate=10)
    assert lim._rpm.used(clock()) == 2
    clock.advance(60.5)
    assert lim._rpm.used(clock()) == 0


async def test_penalize_blocks_until_cooldown_elapses() -> None:
    lim, clock = _limiter(rpm=10, itpm=10_000, otpm=10_000)
    await lim.penalize(seconds=30.0)

    # No requests are tracked yet because penalize parks a synthetic full-budget
    # reservation. wait_seconds for a new request should be ~30.
    wait = lim._rpm.wait_seconds(clock(), 1)
    assert 29.0 < wait <= 30.0


async def test_acquire_is_concurrency_safe() -> None:
    lim, clock = _limiter(rpm=5, itpm=10_000, otpm=10_000)
    results = await asyncio.gather(
        *(lim.acquire(input_estimate=1, output_estimate=1) for _ in range(5))
    )
    assert len(results) == 5
    assert lim._rpm.used(clock()) == 5


def test_estimate_input_tokens_grows_with_length() -> None:
    short = estimate_input_tokens("hi")
    long = estimate_input_tokens("x" * 4000)
    assert long > short
    # Sanity: ~4 chars per token plus overhead.
    assert 950 < long < 1100


def test_parse_retry_after_prefers_ms_header() -> None:
    headers = {"retry-after-ms": "1500", "retry-after": "5"}
    assert parse_retry_after(headers, default=0.0) == pytest.approx(1.5)


def test_parse_retry_after_falls_back_to_seconds() -> None:
    headers = {"retry-after": "7"}
    assert parse_retry_after(headers, default=0.0) == pytest.approx(7.0)


def test_parse_retry_after_handles_missing() -> None:
    assert parse_retry_after({}, default=2.5) == pytest.approx(2.5)
    assert parse_retry_after(None, default=4.0) == pytest.approx(4.0)
