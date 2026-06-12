"""HTTP session factory for justETF requests.

Each top-level lookup uses its own ``requests.Session`` so that cookies set by
justETF's Wicket framework are preserved between the initial page load and the
subsequent AJAX request, without sharing Wicket state across lookups or
between threads.
"""

import requests

# Shared request timeout (seconds) for all justETF calls.
TIMEOUT = 15

_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/136.0.0.0 Safari/537.36"
)


def new_session() -> requests.Session:
    """Create a fresh session with browser headers pre-configured.

    Returns:
        A ``requests.Session`` intended to live for a single lookup.
    """
    s = requests.Session()
    s.headers.update({"User-Agent": _UA, "Accept-Language": "en"})
    return s
