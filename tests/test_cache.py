import json
import time

from justetf import _cache


def test_roundtrip():
    _cache.set("k", {"a": 1}, ttl=60)
    assert _cache.get("k") == {"a": 1}


def test_expired_entry_returns_none():
    _cache.set("k", "v", ttl=-1)
    assert _cache.get("k") is None


def test_corrupted_non_dict_json_returns_none():
    _cache.set("k", "v", ttl=60)
    _cache._path("k").write_text(json.dumps([1, 2]))
    assert _cache.get("k") is None


def test_garbage_file_returns_none():
    _cache.set("k", "v", ttl=60)
    _cache._path("k").write_text("not json at all")
    assert _cache.get("k") is None


def test_stale_tmp_files_are_swept():
    _cache.set("k", "v", ttl=60)
    stale = _cache._CACHE_DIR / "orphan.json.123.tmp"
    stale.write_text("partial")
    old = time.time() - 2 * 24 * 3600
    import os

    os.utime(stale, (old, old))
    _cache.set("k2", "v2", ttl=60)
    assert not stale.exists()
