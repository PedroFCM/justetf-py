import pytest

from justetf import _cache


@pytest.fixture(autouse=True)
def isolated_cache(tmp_path, monkeypatch):
    """Point the disk cache at a per-test temp dir.

    Keeps mocked tests from reading values cached by earlier live runs, and
    keeps fixture data out of the user's real ~/.cache/justetf-py/.
    """
    monkeypatch.setattr(_cache, "_CACHE_DIR", tmp_path / "justetf-cache")
