from pathlib import Path

import pytest

from playwright.sync_api import Page, expect

from e2e_utils import StreamlitRunner

ROOT_DIRECTORY = Path(__file__).parent.parent.absolute()
DATA_RENDER_FILE = ROOT_DIRECTORY / "test" / "grid_data_render.py"
SCREENSHOT_DIRECTORY = ROOT_DIRECTORY / "test" / "screen_shots"


@pytest.fixture(autouse=True, scope="module")
def streamlit_app():
    with StreamlitRunner(DATA_RENDER_FILE) as runner:
        yield runner


@pytest.fixture(autouse=True, scope="function")
def go_to_app(page: Page, streamlit_app: StreamlitRunner):
    page.goto(streamlit_app.server_url)
    # Wait for app to load
    page.get_by_role("img", name="Running...").is_hidden()


def test_grid_renders_lists(page: Page):
    """Test grid renders lists in DataFrame columns"""
    frame0 = page.locator(".st-key-grid_from_dataframe").frame_locator("iframe").nth(0)
    expect(frame0.locator(".ag-root")).to_be_visible()
    expect(frame0.locator(".ag-header-cell-text").nth(0)).to_have_text("names")
    expect(frame0.locator(".ag-header-cell-text").nth(1)).to_have_text("ages")
    expect(frame0.locator(".ag-header-cell-text").nth(2)).to_have_text("list")
    # Check that data is rendered by verifying at least one row exists
    expect(frame0.locator(".ag-row")).not_to_have_count(0)


def test_unhashable_lists(page: Page):
    """Test rendering of unhashable list types with JSON serialization"""
    frame0 = page.locator(".st-key-test_unhashable_lists").frame_locator("iframe").nth(0)
    expect(frame0.locator(".ag-root")).to_be_visible()
    expect(frame0.locator(".ag-header-cell-text").nth(0)).to_have_text("id")
    expect(frame0.locator(".ag-header-cell-text").nth(1)).to_have_text("simple_list")
    expect(frame0.locator(".ag-header-cell-text").nth(2)).to_have_text("nested_list")
    expect(frame0.locator(".ag-header-cell-text").nth(3)).to_have_text("mixed_list")
    # Verify grid has data rows
    expect(frame0.locator(".ag-row")).to_have_count(3)


def test_unhashable_sets(page: Page):
    """Test rendering of unhashable set types with JSON serialization"""
    frame0 = page.locator(".st-key-test_unhashable_sets").frame_locator("iframe").nth(0)
    expect(frame0.locator(".ag-root")).to_be_visible()
    expect(frame0.locator(".ag-header-cell-text").nth(0)).to_have_text("id")
    expect(frame0.locator(".ag-header-cell-text").nth(1)).to_have_text("simple_set")
    expect(frame0.locator(".ag-header-cell-text").nth(2)).to_have_text("string_set")
    expect(frame0.locator(".ag-header-cell-text").nth(3)).to_have_text("mixed_set")
    # Verify grid has data rows
    expect(frame0.locator(".ag-row")).to_have_count(3)


def test_unhashable_dictionaries(page: Page):
    """Test rendering of unhashable dictionary types with JSON serialization"""
    frame0 = page.locator(".st-key-test_unhashable_dicts").frame_locator("iframe").nth(0)
    expect(frame0.locator(".ag-root")).to_be_visible()
    expect(frame0.locator(".ag-header-cell-text").nth(0)).to_have_text("id")
    expect(frame0.locator(".ag-header-cell-text").nth(1)).to_have_text("simple_dict")
    expect(frame0.locator(".ag-header-cell-text").nth(2)).to_have_text("nested_dict")
    expect(frame0.locator(".ag-header-cell-text").nth(3)).to_have_text("mixed_dict")
    # Verify grid has data rows
    expect(frame0.locator(".ag-row")).to_have_count(3)


def test_complex_nested_unhashable(page: Page):
    """Test rendering of complex nested unhashable structures"""
    frame0 = page.locator(".st-key-test_complex_unhashable").frame_locator("iframe").nth(0)
    expect(frame0.locator(".ag-root")).to_be_visible()
    expect(frame0.locator(".ag-header-cell-text").nth(0)).to_have_text("id")
    expect(frame0.locator(".ag-header-cell-text").nth(1)).to_have_text("complex_nested")
    # Verify grid has data rows
    expect(frame0.locator(".ag-row")).to_have_count(2)


def test_mixed_hashable_unhashable_data(page: Page):
    """Test rendering of mixed hashable and unhashable columns with custom formatters"""
    frame0 = page.locator(".st-key-test_mixed_data").frame_locator("iframe").nth(0)
    expect(frame0.locator(".ag-root")).to_be_visible()
    # Check custom column headers from gridOptions
    expect(frame0.locator(".ag-header-cell-text").nth(0)).to_have_text("Int")
    expect(frame0.locator(".ag-header-cell-text").nth(1)).to_have_text("String")
    expect(frame0.locator(".ag-header-cell-text").nth(2)).to_have_text("List")
    expect(frame0.locator(".ag-header-cell-text").nth(3)).to_have_text("Float")
    expect(frame0.locator(".ag-header-cell-text").nth(4)).to_have_text("Dict")
    # Verify grid has data rows
    expect(frame0.locator(".ag-row")).to_have_count(3)


def test_empty_unhashable_structures(page: Page):
    """Test rendering of empty unhashable structures (lists, sets, dicts)"""
    frame0 = page.locator(".st-key-test_empty_unhashable").frame_locator("iframe").nth(0)
    expect(frame0.locator(".ag-root")).to_be_visible()
    expect(frame0.locator(".ag-header-cell-text").nth(0)).to_have_text("id")
    expect(frame0.locator(".ag-header-cell-text").nth(1)).to_have_text("empty_list")
    expect(frame0.locator(".ag-header-cell-text").nth(2)).to_have_text("empty_set")
    expect(frame0.locator(".ag-header-cell-text").nth(3)).to_have_text("empty_dict")
    # Verify grid has data rows
    expect(frame0.locator(".ag-row")).to_have_count(3)


def test_grid_data_serialization(page: Page):
    """Test that grids with various data types render without errors"""
    # Check that all grids are present and visible
    grids = [
        ".st-key-grid_from_dataframe",
        ".st-key-test_unhashable_lists",
        ".st-key-test_unhashable_sets",
        ".st-key-test_unhashable_dicts",
        ".st-key-test_complex_unhashable",
        ".st-key-test_mixed_data",
        ".st-key-test_empty_unhashable",
    ]
    
    for grid_key in grids:
        frame = page.locator(grid_key).frame_locator("iframe").nth(0)
        expect(frame.locator(".ag-root")).to_be_visible()


def test_json_serialization_functionality(page: Page):
    """Test that JSON serialization works for unhashable data types"""
    # Test that grids with use_json_serialization=True render successfully
    json_serialized_grids = [
        ".st-key-test_unhashable_sets",
        ".st-key-test_unhashable_dicts", 
        ".st-key-test_complex_unhashable",
        ".st-key-test_mixed_data",
        ".st-key-test_empty_unhashable"
    ]
    
    for grid_key in json_serialized_grids:
        frame = page.locator(grid_key).frame_locator("iframe").nth(0)
        expect(frame.locator(".ag-root")).to_be_visible()
        # Verify that data is actually displayed (not just an empty grid)
        expect(frame.locator(".ag-row")).not_to_have_count(0)


def test_auto_serialization_fallback(page: Page):
    """Test that use_json_serialization='auto' works as fallback"""
    frame0 = page.locator(".st-key-test_unhashable_lists").frame_locator("iframe").nth(0)
    expect(frame0.locator(".ag-root")).to_be_visible()
    # This grid uses 'auto' serialization, should still render properly
    expect(frame0.locator(".ag-row")).to_have_count(3)