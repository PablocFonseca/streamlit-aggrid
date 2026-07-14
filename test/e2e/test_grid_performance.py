"""Absolute performance regression smoke checks.

The thresholds here catch severe regressions on a single build. This is not a
comparative v1/v2 benchmark and does not support relative performance claims.
"""

import time
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from e2e_utils import StreamlitRunner

pytestmark = [pytest.mark.e2e, pytest.mark.slow]

HERE = Path(__file__).parent.absolute()
PERFORMANCE_TEST_FILE = HERE / "grid_performance_1m.py"


@pytest.fixture(autouse=True, scope="module")
def streamlit_app():
    """Start the Streamlit app for performance testing."""
    with StreamlitRunner(PERFORMANCE_TEST_FILE) as runner:
        yield runner


@pytest.fixture(autouse=True, scope="function")
def go_to_app(page: Page, streamlit_app: StreamlitRunner):
    """Navigate to the app and wait for it to load."""
    page.goto(streamlit_app.server_url)
    expect(page.get_by_role("img", name="Running...")).to_be_hidden()


def test_grid_performance_1m_records(page: Page):
    """Test grid performance with 1 million records."""
    
    # Wait for the data generation to complete
    page.wait_for_selector("text=Generated 1,000,000 records", timeout=60000)  # 60 second timeout
    
    # Measure time before grid renders
    start_time = time.perf_counter()
    
    # Wait for the grid to be visible
    frame = page.locator(".st-key-performance_grid_1m")
    expect(frame.locator(".ag-root")).to_be_visible(timeout=120000)  # 2 minute timeout
    
    # Record time when grid becomes visible
    grid_visible_time = time.perf_counter()
    
    # The grid row-groups by category + department, so the top level shows a
    # few collapsed group rows (pagination is not configured).
    expect(frame.locator(".ag-row").first).to_be_visible(timeout=30000)

    # Record time when grid is fully loaded
    grid_loaded_time = time.perf_counter()

    rows = frame.locator(".ag-row")
    assert rows.count() > 0
    
    # Calculate performance metrics
    grid_initialization_time = grid_visible_time - start_time
    grid_full_load_time = grid_loaded_time - start_time
    
    print("\n=== Grid Performance Metrics ===")
    print(f"Grid initialization time: {grid_initialization_time:.2f} seconds")
    print(f"Grid full load time: {grid_full_load_time:.2f} seconds")
    
    # Performance assertions. Rendering 1M grouped rows in headless Chromium is
    # slow and machine-dependent; thresholds are generous to catch only regressions.
    assert grid_initialization_time < 90, f"Grid initialization took too long: {grid_initialization_time:.2f}s"
    assert grid_full_load_time < 90, f"Grid full load took too long: {grid_full_load_time:.2f}s"


def test_grid_return_with_1m_records(page: Page):
    """Test grid return functionality with 1 million records."""
    
    # Wait for the data generation and grid loading
    page.wait_for_selector("text=Generated 1,000,000 records", timeout=60000)
    
    frame = page.locator(".st-key-performance_grid_1m")
    expect(frame.locator(".ag-root")).to_be_visible(timeout=120000)
    expect(frame.locator(".ag-row").first).to_be_visible(timeout=30000)

    response = page.get_by_test_id("performance-grid-response")
    expect(response).to_be_visible()
    expect(response).not_to_contain_text("columnMoved")

    # Move a column: unlike a row click, this event is in update_on and causes
    # the CUSTOM collector, WebSocket round trip, and Streamlit rerun. Waiting
    # for its event name measures the observable completion rather than a fixed
    # two-second sleep.
    first_header = frame.get_by_role("columnheader", name="id", exact=True)
    second_header = frame.get_by_role("columnheader", name="name", exact=True)
    expect(first_header).to_be_visible()
    expect(second_header).to_be_visible()
    return_start_time = time.perf_counter()
    first_header.drag_to(second_header)
    expect(response).to_contain_text("columnMoved", timeout=10000)
    return_time = time.perf_counter() - return_start_time

    print("\n=== Grid Return Metrics ===")
    print(f"Grid return processing time: {return_time:.3f} seconds")

    # Performance assertion for return
    assert return_time < 5, f"Grid return took too long: {return_time:.3f}s"


def test_grid_group_expand_performance(page: Page):
    """Test group-row expansion performance with the grouped 1M dataset."""

    # Wait for the grid to load
    page.wait_for_selector("text=Generated 1,000,000 records", timeout=60000)

    frame = page.locator(".st-key-performance_grid_1m")
    expect(frame.locator(".ag-root")).to_be_visible(timeout=120000)
    expect(frame.locator(".ag-row").first).to_be_visible(timeout=30000)

    expand_start_time = time.perf_counter()

    # Expand the first collapsed category group row
    frame.locator(".ag-group-contracted").first.click()
    expect(frame.locator(".ag-group-expanded").first).to_be_visible()

    expand_time = time.perf_counter() - expand_start_time

    print("\n=== Group Expand Performance ===")
    print(f"Group expand time: {expand_time:.3f} seconds")

    assert expand_time < 3, f"Group expand took too long: {expand_time:.3f}s"
