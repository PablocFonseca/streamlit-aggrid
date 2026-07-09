import os
import subprocess
import sys

import pytest
from playwright.sync_api import expect, sync_playwright


@pytest.fixture(scope="session", autouse=True)
def _ensure_chromium():
    with sync_playwright() as p:
        exe = p.chromium.executable_path
    if not os.path.exists(exe):
        subprocess.run(
            [sys.executable, "-m", "playwright", "install", "chromium"], check=True
        )


@pytest.fixture(autouse=True)
def _sane_timeouts(page):
    # First grid mount loads a ~7MB bundle; the 5s expect default is too tight.
    page.set_default_timeout(15_000)
    expect.set_options(timeout=15_000)
