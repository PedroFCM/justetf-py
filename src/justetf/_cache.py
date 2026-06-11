"""Disk-based cache for ISIN lookups and sector data.

Entries are stored as individual JSON files under ``~/.cache/justetf-py/``,
keyed by the SHA1 of the cache key string. Each file holds an expiry timestamp
and the cached value; expired entries are deleted on next read.
"""

import hashlib
import json
import os
import time
from pathlib import Path

_CACHE_DIR = Path.home() / ".cache" / "justetf-py"


def _path(key: str) -> Path:
    """Return the cache file path for a given key."""
    digest = hashlib.sha1(key.encode()).hexdigest()
    return _CACHE_DIR / f"{digest}.json"


def get(key: str) -> object | None:
    """Read a cached value if it exists and has not expired.

    Args:
        key: Cache key string.

    Returns:
        The cached value, or ``None`` if missing or expired.
    """
    p = _path(key)
    try:
        entry = json.loads(p.read_text())
        if time.time() < entry["expires"]:
            return entry["data"]
        p.unlink(missing_ok=True)
    except (FileNotFoundError, KeyError, json.JSONDecodeError):
        pass
    return None


def set(key: str, value: object, ttl: int) -> None:
    """Write a value to the cache with a TTL.

    Args:
        key: Cache key string.
        value: JSON-serialisable value to store.
        ttl: Time-to-live in seconds.
    """
    _CACHE_DIR.mkdir(parents=True, exist_ok=True)
    target = _path(key)
    # Write-then-rename keeps concurrent readers from seeing partial JSON.
    tmp = target.with_name(f"{target.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps({"expires": time.time() + ttl, "data": value}))
    os.replace(tmp, target)
