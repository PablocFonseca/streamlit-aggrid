from pathlib import Path

import pytest

from playwright.sync_api import Page, expect

from e2e_utils import StreamlitRunner

ROOT_DIRECTORY = Path(__file__).parent.parent.absolute()
BASIC_EXAMPLE_FILE = ROOT_DIRECTORY / "test" / "grid_initialization.py"
SCREENSHOT_DIRECTORY = ROOT_DIRECTORY / "test" / "screen_shots"


@pytest.fixture(autouse=True, scope="module")
def streamlit_app():
    with StreamlitRunner(BASIC_EXAMPLE_FILE) as runner:
        yield runner


@pytest.fixture(autouse=True, scope="function")
def go_to_app(page: Page, streamlit_app: StreamlitRunner):
    page.goto(streamlit_app.server_url)
    # Wait for app to load
    page.get_by_role("img", name="Running...").is_hidden()


def test_initialize_from_dataframe(page: Page):
    frame0 = page.locator(".st-key-grid_from_dataframe").frame_locator("iframe").nth(0)
    expect(frame0.locator(".ag-root")).to_be_visible()
    expect(frame0.locator(".ag-header-cell-text").nth(0)).to_have_text("names")


def test_initialize_from_json(page: Page):
    frame0 = page.locator(".st-key-grid_from_json").frame_locator("iframe").nth(0)
    expect(frame0.locator(".ag-root")).to_be_visible()
    expect(frame0.locator(".ag-header-cell-text").nth(0)).to_have_text("First Name")


def test_initialize_from_grid_options(page: Page):
    frame0 = page.locator(".st-key-gridOptions_only").frame_locator("iframe").nth(0)
    expect(frame0.locator(".ag-root")).to_be_visible()


def test_initialize_empty(page: Page):
    frame0 = page.locator(".st-key-empty_grid").frame_locator("iframe").nth(0)
    expect(frame0.locator(".ag-root")).to_be_visible()
