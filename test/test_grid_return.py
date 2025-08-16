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
    radio_option_1 = page.get_by_test_id("stRadio").get_by_text("1")
    radio_option_1.click()
    
    # Wait for the grid to load
    frame0 = page.locator(".st-key-event_return_grid").frame_locator("iframe").nth(0)
    expect(frame0.locator(".ag-root")).to_be_visible()
    
    # Verify the grid headers
    expect(frame0.locator(".ag-header-cell-text").nth(1)).to_have_text("First Name")
    expect(frame0.locator(".ag-header-cell-text").nth(2)).to_have_text("ages")

    #click the First Name to sort it and trigger grid response
    frame0.locator(".ag-header-cell-text").nth(1).click()
    
    # Verify that data is loaded by checking for at least one row
    expect(frame0.locator(".ag-row")).not_to_have_count(0)
    
    # Verify that the first data row contains expected data (alice, 25)
    first_row = frame0.locator(".ag-row").nth(0)
    expect(first_row.locator(".ag-cell").nth(1)).to_have_text("alice")
    expect(first_row.locator(".ag-cell").nth(2)).to_have_text("25")
    
    # Verify grid return data using data-testid elements
    returned_grid_data = page.get_by_test_id("returned-grid-data")
    expect(returned_grid_data).to_be_visible()
    expect(returned_grid_data).to_contain_text("alice")
    expect(returned_grid_data).to_contain_text("bob")
    expect(returned_grid_data).to_contain_text("charlie")
    
    # Verify event return data
    event_return_data = page.get_by_test_id("event-return-data")
    expect(event_return_data).to_be_visible()
    
    # Verify selected data (should be empty initially)
    selected_data = page.get_by_test_id("selected-data")
    expect(selected_data).to_be_visible()
    
    # Verify full grid response
    full_grid_response = page.get_by_test_id("full-grid-response")
    expect(full_grid_response).to_be_visible()
    expect(full_grid_response).to_contain_text("nodes")

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
    
    # Wait for selection to be processed and data to update
    page.wait_for_timeout(2000)
    
    # Verify the returned grid data contains all data
    returned_grid_data = page.get_by_test_id("returned-grid-data")
    expect(returned_grid_data).to_be_visible()
    expect(returned_grid_data).to_contain_text("alice")
    expect(returned_grid_data).to_contain_text("bob") 
    expect(returned_grid_data).to_contain_text("charlie")
    
    # Verify the selected data contains only charlie's data
    selected_data = page.get_by_test_id("selected-data")
    expect(selected_data).to_be_visible()
    expect(selected_data).to_contain_text("charlie")
    expect(selected_data).to_contain_text("35")
    # Verify it doesn't contain other names (should only contain selected row)
    expect(selected_data).not_to_contain_text("alice")
    expect(selected_data).not_to_contain_text("bob")
    
    # Verify that the event data contains selection information
    event_return_data = page.get_by_test_id("event-return-data")
    expect(event_return_data).to_be_visible()
    expect(event_return_data).to_contain_text("selectionChanged")

    # Verify that the full grid response contains the selection data
    full_grid_response = page.get_by_test_id("full-grid-response")
    expect(full_grid_response).to_be_visible()
    expect(full_grid_response).to_contain_text("'isSelected': True")


def test_grid_return_test_2_custom_return(page: Page):
    """Test custom grid return functionality with test 2 (radio option 2)"""
    # Select radio option 2 from the radio button group
    radio_option_2 = page.get_by_test_id("stRadio").get_by_text("2")
    radio_option_2.click()
    
    # Wait for the grid to load
    frame1 = page.locator(".st-key-custom_event_return_grid").frame_locator("iframe").nth(0)
    expect(frame1.locator(".ag-root")).to_be_visible()
    
    # Verify that data is loaded by checking for at least one row
    expect(frame1.locator(".ag-row")).not_to_have_count(0)
    
    # Verify custom grid return data using data-testid
    custom_grid_return_data = page.get_by_test_id("custom-grid-return-data")
    expect(custom_grid_return_data).to_be_visible()

    #Should contain none, as the grid didn`t return
    expect(custom_grid_return_data).to_contain_text("None")

    first_column = frame1.get_by_role("columnheader", name="employee_id")
    thrid_column = frame1.get_by_role("columnheader", name="email")

    #trigger a response
    first_column.click()
    expect(custom_grid_return_data).to_contain_text("[None, 'employee_id', 'first_name', 'last_name', 'email'")

    first_column.drag_to(thrid_column)
    
    expect(custom_grid_return_data).to_contain_text("[None, 'first_name', 'last_name', 'email', 'employee_id'")


def test_grid_return_test_3_grouped_data(page: Page):
    """Test grouped data functionality with test 3 (radio option 3)"""
    # Select radio option 3 from the radio button group
    radio_option_3 = page.get_by_test_id("stRadio").get_by_text("3")
    radio_option_3.click()
    
    # Wait for the grid to load
    frame2 = page.locator(".st-key-grouped_data_grid").frame_locator("iframe").nth(0)
    expect(frame2.locator(".ag-root")).to_be_visible()
    
    # Wait for grouped data to be processed
    page.wait_for_timeout(2000)

    first_column = frame2.get_by_role("columnheader", name="Sport")
    first_column.click()
    
    # Verify grouped data groups using data-testid
    grouped_data_groups = page.get_by_test_id("grouped-data-groups")
    expect(grouped_data_groups).to_be_visible()
    
    # Verify grouped grid response
    grouped_grid_response = page.get_by_test_id("grouped-grid-response")
    expect(grouped_grid_response).to_be_visible()
    expect(grouped_grid_response).to_contain_text("row-group-sport-Swimming")
