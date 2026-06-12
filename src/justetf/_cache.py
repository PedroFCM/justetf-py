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
    except (OSError, KeyError, TypeError, json.JSONDecodeError):
        # TypeError covers corrupted files whose JSON is not a dict;
        # OSError covers missing files and permission problems alike.
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
    _sweep_stale_tmp()
    target = _path(key)
    # Write-then-rename keeps concurrent readers from seeing partial JSON.
    tmp = target.with_name(f"{target.name}.{os.getpid()}.tmp")
    tmp.write_text(json.dumps({"expires": time.time() + ttl, "data": value}))
    Path.replace(tmp, target)


def _sweep_stale_tmp(max_age: int = 24 * 3600) -> None:
    """Delete temp files orphaned by a crash between write and rename.

    Args:
        max_age: Age in seconds beyond which a ``.tmp`` file is considered
            orphaned; young ones may belong to an in-flight write.
    """
    cutoff = time.time() - max_age
    for tmp in _CACHE_DIR.glob("*.tmp"):
        try:
            if tmp.stat().st_mtime < cutoff:
                tmp.unlink(missing_ok=True)
        except OSError:
            pass  # raced with another process; harmless
