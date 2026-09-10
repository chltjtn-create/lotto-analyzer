"""Keep the Streamlit dashboard awake by opening it in a real browser.

Streamlit Community Cloud sleeps an app after 12 quiet hours, and only a real
session counts as traffic: the browser has to run the page's JavaScript and open
a websocket to /_stcore/stream, which is what starts the Python process. A plain
HTTP GET returns the static HTML shell and starts nothing, so the curl ping this
replaces never kept anything awake — it just returned 200 (when it wasn't stuck
in a redirect loop) while the app slept on.

Success here means that websocket actually opened. Anything else exits non-zero
so a broken ping shows up as a failed run instead of hiding.
"""

from __future__ import annotations

import os
import sys
import time

from playwright.sync_api import TimeoutError as PlaywrightTimeout
from playwright.sync_api import sync_playwright

URL = os.environ.get("APP_URL", "https://lotto007.streamlit.app")

# Shown instead of the dashboard once the app has gone to sleep.
WAKE_BUTTON = "Yes, get this app back up!"

# The websocket Streamlit opens once the page's JS runs. Its presence is the
# proof that the Python process is up — this is the thing being counted.
STREAM_PATH = "_stcore/stream"

NAV_TIMEOUT_MS = 60_000
BUTTON_WAIT_S = 15
STREAM_WAIT_S = 240  # a cold start pulls the whole environment back up


def find_wake_button(page):
    """Look for the wake button in every frame; the app renders inside an iframe."""
    for frame in page.frames:
        try:
            button = frame.get_by_text(WAKE_BUTTON, exact=False)
            if button.count() > 0:
                return button.first
        except Exception:  # noqa: BLE001 - a frame can detach mid-scan
            continue
    return None


def wait_for(predicate, timeout_s: int, poll_s: float = 1.0) -> bool:
    """Poll `predicate` until it is true or the timeout runs out."""
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(poll_s)
    return False


def main() -> int:
    sockets: list[str] = []

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch()
        context = browser.new_context(viewport={"width": 1280, "height": 900})
        page = context.new_page()
        page.on("websocket", lambda ws: sockets.append(ws.url))

        print(f"opening {URL}")
        started = time.monotonic()
        try:
            page.goto(URL, timeout=NAV_TIMEOUT_MS, wait_until="domcontentloaded")
        except PlaywrightTimeout:
            print(f"FAIL: {URL} did not respond within {NAV_TIMEOUT_MS // 1000}s")
            return 1

        streamed = lambda: any(STREAM_PATH in url for url in sockets)  # noqa: E731

        # If the app is already awake the websocket opens on its own, so give it
        # a moment before deciding the wake button is missing.
        if not wait_for(lambda: streamed() or find_wake_button(page) is not None, BUTTON_WAIT_S):
            print("no wake button and no websocket yet; waiting it out")

        button = find_wake_button(page)
        if button is not None:
            print("app was asleep — clicking the wake button")
            try:
                button.click(timeout=10_000)
            except Exception as exc:  # noqa: BLE001 - report, then keep waiting
                print(f"could not click the wake button: {type(exc).__name__}: {exc}")
        else:
            print("app was already awake")

        print(f"waiting up to {STREAM_WAIT_S}s for the Streamlit session")
        ok = wait_for(streamed, STREAM_WAIT_S)
        elapsed = time.monotonic() - started

        if ok:
            stream_urls = [u for u in sockets if STREAM_PATH in u]
            print(f"OK: session established in {elapsed:.0f}s")
            print(f"   websocket: {stream_urls[0]}")
        else:
            print(f"FAIL: no {STREAM_PATH} websocket after {elapsed:.0f}s")
            print(f"   websockets seen: {sockets or 'none'}")
            page.screenshot(path="keep_awake_failure.png", full_page=True)
            print("   saved keep_awake_failure.png")

        context.close()
        browser.close()

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
