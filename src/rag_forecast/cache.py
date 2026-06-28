from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def _key(payload: dict[str, Any]) -> str:
    blob = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def cache_namespace(date: str, stage: str, backend: str) -> str:
    """Folder (under the cache root) for a stage's entries: ``<date>/<stage>/<backend>``.

    Keeping the ordering here means it is defined in exactly one place; callers pass
    ``(date, stage, backend)`` and never build the path by hand.
    """
    return f"{date}/{stage}/{backend}"


class JsonCache:
    """Content-hash-keyed JSON cache backed by one file per entry.

    Entries optionally nest under a ``namespace`` subdirectory (see
    ``cache_namespace``) so the on-disk layout is human-readable; the file name
    itself stays the content hash, which is what guarantees correctness.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root)

    def _path(self, key: str, namespace: str | None = None) -> Path:
        base = self.root if not namespace else self.root / namespace
        base.mkdir(parents=True, exist_ok=True)
        return base / f"{key}.json"

    def get(self, payload: dict[str, Any], namespace: str | None = None) -> Any | None:
        path = self._path(_key(payload), namespace)
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def put(
        self, payload: dict[str, Any], value: Any, namespace: str | None = None
    ) -> None:
        path = self._path(_key(payload), namespace)
        path.write_text(json.dumps(value, default=str))
