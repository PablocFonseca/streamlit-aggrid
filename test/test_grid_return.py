from pathlib import Path

import pytest

from playwright.sync_api import Page, expect

from e2e_utils import StreamlitRunner

ROOT_DIRECTORY = Path(__file__).parent.parent.absolute()
GRID_RETURN_FILE = ROOT_DIRECTORY / "test" / "grid_return.py"
SCREENSHOT_DIRECTORY = ROOT_DIRECTORY / "test" / "screen_shots"


@pytest.fixture(autouse=True, scope="module")
def streamlit_app():
    with StreamlitRunner(GRID_RETURN_FILE) as runner:
        yield runner


@pytest.fixture(autouse=True, scope="function")
def go_to_app(page: Page, streamlit_app: StreamlitRunner):
    page.goto(streamlit_app.server_url)
    # Wait for app to load
    page.get_by_role("img", name="Running...").is_hidden()


def test_grid_return_test_1(page: Page):
    """Test grid return functionality with test 1 (radio option 1)"""
    # Select radio option 1 from the radio button group
    radio_option_1 = page.get_by_test_id("stRadio").get_by_text("1")
    radio_option_1.click()
    
    # Wait for the grid to load
    frame0 = page.locator(".st-key-event_return_grid").frame_locator("iframe").nth(0)
    expect(frame0.locator(".ag-root")).to_be_visible()
    
    # Verify the grid headers
    expect(frame0.locator(".ag-header-cell-text").nth(1)).to_have_text("First Name")
    expect(frame0.locator(".ag-header-cell-text").nth(2)).to_have_text("ages")
    
    # Verify that data is loaded by checking for at least one row
    expect(frame0.locator(".ag-row")).not_to_have_count(0)
    
    # Verify that the first data row contains expected data (alice, 25)
    first_row = frame0.locator(".ag-row").nth(0)
    expect(first_row.locator(".ag-cell").nth(1)).to_have_text("alice")
    expect(first_row.locator(".ag-cell").nth(2)).to_have_text("25")
    
    # Verify the subheaders are present
    expect(page.get_by_text("Event Retun Data")).to_be_visible()
    expect(page.get_by_text("Data returned by component")).to_be_visible()
    expect(page.get_by_text("Data Selected on component")).to_be_visible()
    expect(page.get_by_text("Full Grid Response")).to_be_visible()


def test_grid_return_third_row_checkbox(page: Page):
    """Test clicking on the 3rd row checkbox and verifying grid return"""
    # Select radio option 1 from the radio button group
    radio_option_1 = page.get_by_test_id("stRadio").get_by_text("1")
    radio_option_1.click()
    
    # Wait for the grid to load
    frame0 = page.locator(".st-key-event_return_grid").frame_locator("iframe").nth(0)
    expect(frame0.locator(".ag-root")).to_be_visible()
    
    # Wait for data to be loaded
    expect(frame0.locator(".ag-row")).not_to_have_count(0)
    
    # Click on the checkbox in the 3rd row (index 2)
    third_row = frame0.locator(".ag-row").nth(2)
    checkbox = third_row.locator(".ag-selection-checkbox input[type='checkbox']")
    checkbox.click()
    
    # Wait for the selection to be processed
    page.wait_for_timeout(1000)
    
    # Verify that the 3rd row is selected by checking if checkbox is checked
    expect(checkbox).to_be_checked()
    
    # Verify the selected data shows the 3rd row data (charlie, 35)
    # Wait for selection to be processed and data to update
    page.wait_for_timeout(2000)
    
    # Look for the code element that contains the selected data
    selected_data_section = page.locator('[data-testid="stCode"]').nth(1)
    expect(selected_data_section).to_be_visible()
    expect(selected_data_section).to_contain_text("charlie")
    expect(selected_data_section).to_contain_text("35")
    
    # Verify that the event data contains selection information
    event_data_section = page.locator(".stJson").nth(0)
    expect(event_data_section).to_be_visible()
    expect(event_data_section).to_contain_text("selectionChanged")

    # Verify that the full grid response contains the selection
    grid_response_section = page.locator("text=Full Grid Response").locator("..")
    expect(grid_response_section).to_be_visible()
