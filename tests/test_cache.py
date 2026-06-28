from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from rag_forecast.cache import JsonCache, cache_namespace


def test_cache_namespace_orders_date_stage_backend() -> None:
    assert (
        cache_namespace("2025-10-26", "retrieval", "asknews")
        == "2025-10-26/retrieval/asknews"
    )


def test_namespaced_put_get_round_trips(tmp_path: Path) -> None:
    cache = JsonCache(tmp_path)
    ns = cache_namespace("2025-10-26", "prompt", "claude-haiku-4-5-20251001")
    payload = {"q": "hi"}

    cache.put(payload, {"probability": 0.5}, namespace=ns)

    # Stored under the namespaced subdirectory, file named by content hash.
    files = list((tmp_path / ns).glob("*.json"))
    assert len(files) == 1
    assert cache.get(payload, namespace=ns) == {"probability": 0.5}


def test_same_payload_isolated_across_namespaces(tmp_path: Path) -> None:
    cache = JsonCache(tmp_path)
    payload = {"q": "hi"}
    a = cache_namespace("2025-10-26", "prompt", "model-a")
    b = cache_namespace("2025-10-26", "prompt", "model-b")

    cache.put(payload, "from-a", namespace=a)

    assert cache.get(payload, namespace=a) == "from-a"
    # Same payload, different namespace -> miss (namespaces are isolated).
    assert cache.get(payload, namespace=b) is None


def test_namespaced_get_does_not_fall_back_to_flat(tmp_path: Path) -> None:
    cache = JsonCache(tmp_path)
    payload = {"q": "hi"}

    cache.put(payload, "flat")  # legacy flat write, no namespace

    ns = cache_namespace("2025-10-26", "retrieval", "asknews")
    # No fallback: a namespaced lookup does not see the flat entry, and vice versa.
    assert cache.get(payload, namespace=ns) is None
    assert cache.get(payload) == "flat"
