import time
from pathlib import Path

import pytest
from playwright.sync_api import Page, expect

from e2e_utils import StreamlitRunner

ROOT_DIRECTORY = Path(__file__).parent.parent.absolute()
PERFORMANCE_TEST_FILE = ROOT_DIRECTORY / "test" / "grid_performance_1m.py"


@pytest.fixture(autouse=True, scope="module")
def streamlit_app():
    """Start the Streamlit app for performance testing."""
    with StreamlitRunner(PERFORMANCE_TEST_FILE) as runner:
        yield runner


@pytest.fixture(autouse=True, scope="function")
def go_to_app(page: Page, streamlit_app: StreamlitRunner):
    """Navigate to the app and wait for it to load."""
    page.goto(streamlit_app.server_url)
    # Wait for app to load
    page.get_by_role("img", name="Running...").is_hidden()


def test_grid_performance_1m_records(page: Page):
    """Test grid performance with 1 million records."""
    
    # Wait for the data generation to complete
    page.wait_for_selector("text=Generated 1,000,000 records", timeout=60000)  # 60 second timeout
    
    # Measure time before grid renders
    start_time = time.time()
    
    # Wait for the grid to be visible
    frame = page.locator(".st-key-performance_grid_1m").frame_locator("iframe").nth(0)
    expect(frame.locator(".ag-root")).to_be_visible(timeout=120000)  # 2 minute timeout
    
    # Record time when grid becomes visible
    grid_visible_time = time.time()
    
    # Wait for grid to be fully loaded (pagination should be visible for large datasets)
    expect(frame.locator(".ag-paging-panel")).to_be_visible(timeout=30000)
    
    # Wait for rows to be rendered
    expect(frame.locator(".ag-row")).to_be_visible(timeout=30000)
    
    # Record time when grid is fully loaded
    grid_loaded_time = time.time()
    
    # Verify we have pagination controls (indicates large dataset is properly handled)
    expect(frame.locator(".ag-paging-button")).to_be_visible()
    
    # Verify we have some data rows visible
    rows = frame.locator(".ag-row")
    expect(rows.count()).to_be_greater_than(0)
    
    # Test interaction - click on first row to measure response time
    interaction_start_time = time.time()
    rows.first.click()
    interaction_end_time = time.time()
    
    # Calculate performance metrics
    grid_initialization_time = grid_visible_time - start_time
    grid_full_load_time = grid_loaded_time - start_time
    interaction_time = interaction_end_time - interaction_start_time
    
    print(f"\n=== Grid Performance Metrics ===")
    print(f"Grid initialization time: {grid_initialization_time:.2f} seconds")
    print(f"Grid full load time: {grid_full_load_time:.2f} seconds")
    print(f"Row interaction time: {interaction_time:.3f} seconds")
    
    # Performance assertions (adjust thresholds as needed)
    assert grid_initialization_time < 30, f"Grid initialization took too long: {grid_initialization_time:.2f}s"
    assert grid_full_load_time < 60, f"Grid full load took too long: {grid_full_load_time:.2f}s"
    assert interaction_time < 1, f"Row interaction took too long: {interaction_time:.3f}s"


def test_grid_return_with_1m_records(page: Page):
    """Test grid return functionality with 1 million records."""
    
    # Wait for the data generation and grid loading
    page.wait_for_selector("text=Generated 1,000,000 records", timeout=60000)
    
    frame = page.locator(".st-key-performance_grid_1m").frame_locator("iframe").nth(0)
    expect(frame.locator(".ag-root")).to_be_visible(timeout=120000)
    expect(frame.locator(".ag-row")).to_be_visible(timeout=30000)
    
    # Measure time for return operation
    return_start_time = time.time()
    
    # Click on a row to trigger selection and return
    frame.locator(".ag-row").first.click()
    
    # Wait for the return information to be processed
    # This might trigger a re-render in Streamlit
    page.wait_for_timeout(2000)  # Give time for the return to be processed
    
    return_end_time = time.time()
    return_time = return_end_time - return_start_time
    
    print(f"\n=== Grid Return Metrics ===")
    print(f"Grid return processing time: {return_time:.3f} seconds")
    
    # Verify return information is displayed
    expect(page.locator("text=Grid Return Information")).to_be_visible(timeout=10000)
    
    # Performance assertion for return
    assert return_time < 5, f"Grid return took too long: {return_time:.3f}s"


def test_grid_pagination_performance(page: Page):
    """Test pagination performance with large dataset."""
    
    # Wait for the grid to load
    page.wait_for_selector("text=Generated 1,000,000 records", timeout=60000)
    
    frame = page.locator(".st-key-performance_grid_1m").frame_locator("iframe").nth(0)
    expect(frame.locator(".ag-root")).to_be_visible(timeout=120000)
    expect(frame.locator(".ag-paging-panel")).to_be_visible(timeout=30000)
    
    # Test pagination navigation
    pagination_start_time = time.time()
    
    # Click next page
    next_button = frame.locator("[aria-label='Next Page']")
    if next_button.is_visible():
        next_button.click()
        page.wait_for_timeout(1000)  # Wait for page change
    
    pagination_end_time = time.time()
    pagination_time = pagination_end_time - pagination_start_time
    
    print(f"\n=== Pagination Performance ===")
    print(f"Page navigation time: {pagination_time:.3f} seconds")
    
    # Performance assertion for pagination
    assert pagination_time < 3, f"Pagination took too long: {pagination_time:.3f}s"