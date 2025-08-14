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
    """Test grid initialization from pandas DataFrame"""
    frame0 = page.locator(".st-key-grid_from_dataframe").frame_locator("iframe").nth(0)
    expect(frame0.locator(".ag-root")).to_be_visible()
    expect(frame0.locator(".ag-header-cell-text").nth(0)).to_have_text("names")
    expect(frame0.locator(".ag-header-cell-text").nth(1)).to_have_text("ages")


def test_initialize_from_json(page: Page):
    """Test grid initialization with JSON data and grid options"""
    frame0 = page.locator(".st-key-grid_from_json").frame_locator("iframe").nth(0)
    expect(frame0.locator(".ag-root")).to_be_visible()
    expect(frame0.locator(".ag-header-cell-text").nth(0)).to_have_text("First Name")
    expect(frame0.locator(".ag-header-cell-text").nth(1)).to_have_text("ages")


def test_initialize_from_grid_options(page: Page):
    """Test grid initialization with grid options only (no data)"""
    frame0 = page.locator(".st-key-gridOptions_only").frame_locator("iframe").nth(0)
    expect(frame0.locator(".ag-root")).to_be_visible()
    expect(frame0.locator(".ag-header-cell-text").nth(0)).to_have_text("names")
    expect(frame0.locator(".ag-header-cell-text").nth(1)).to_have_text("ages")


def test_initialize_empty(page: Page):
    """Test empty grid initialization"""
    frame0 = page.locator(".st-key-empty_grid").frame_locator("iframe").nth(0)
    expect(frame0.locator(".ag-root")).to_be_visible()


def test_initialize_from_json_file(page: Page):
    """Test grid initialization loading data from JSON file"""
    frame0 = page.locator(".st-key-grid_loads_data_json_from_file").frame_locator("iframe").nth(0)
    expect(frame0.locator(".ag-root")).to_be_visible()
    # Check that data is loaded by verifying at least one row exists
    expect(frame0.locator(".ag-row")).not_to_have_count(0)


def test_initialize_from_json_files(page: Page):
    """Test grid initialization loading both data and grid options from JSON files"""
    frame0 = page.locator(".st-key-grid_loads_data_and_go_json_from_file").frame_locator("iframe").nth(0)
    expect(frame0.locator(".ag-root")).to_be_visible()
    # Check that data is loaded by verifying at least one row exists
    expect(frame0.locator(".ag-row")).not_to_have_count(0)
