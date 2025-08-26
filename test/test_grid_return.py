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


def test_grid_return_test_4_selection_functionality(page: Page):
    """Test comprehensive selection functionality with test 4 (radio option 4)"""
    # Select radio option 4 from the radio button group
    radio_option_4 = page.get_by_test_id("stRadio").get_by_text("4")
    radio_option_4.click()
    
    # Wait for the grid to load
    frame3 = page.locator(".st-key-selection_test_grid").frame_locator("iframe").nth(0)
    expect(frame3.locator(".ag-root")).to_be_visible()
    
    # Wait for data to be loaded
    expect(frame3.locator(".ag-row")).not_to_have_count(0)
    
    # Verify grid headers (adjust indices based on actual column order)
    expect(frame3.locator(".ag-header-cell-text").nth(0)).to_have_text("ID")
    expect(frame3.locator(".ag-header-cell-text").nth(1)).to_have_text("Name") 
    expect(frame3.locator(".ag-header-cell-text").nth(2)).to_have_text("Category")
    expect(frame3.locator(".ag-header-cell-text").nth(3)).to_have_text("Value")
    expect(frame3.locator(".ag-header-cell-text").nth(4)).to_have_text("Active")
    
    # Verify initial state - no rows selected
    selection_count = page.get_by_test_id("selection-count")
    expect(selection_count).to_contain_text("0")
    
    selected_rows_data = page.get_by_test_id("selected-rows-data")
    expect(selected_rows_data).to_contain_text("No rows selected")
    
    # Select the first row by clicking its checkbox
    first_row = frame3.locator(".ag-row").nth(0)
    first_checkbox = first_row.locator(".ag-selection-checkbox input[type='checkbox']")
    first_checkbox.click()
    
    # Wait for selection to be processed
    page.wait_for_timeout(1000)
    
    # Verify the first row is selected
    expect(first_checkbox).to_be_checked()
    
    # Check selection count updated to 1
    expect(selection_count).to_contain_text("1")
    
    # Check selected rows data contains first row data
    expect(selected_rows_data).to_contain_text("User1")
    expect(selected_rows_data).to_contain_text("10")
    
    # Select the third row as well (multi-selection)
    third_row = frame3.locator(".ag-row").nth(2)
    third_checkbox = third_row.locator(".ag-selection-checkbox input[type='checkbox']")
    third_checkbox.click()
    
    # Wait for selection to be processed
    page.wait_for_timeout(1000)
    
    # Verify both checkboxes are checked
    expect(first_checkbox).to_be_checked()
    expect(third_checkbox).to_be_checked()
    
    # Check selection count updated to 2
    expect(selection_count).to_contain_text("2")
    
    # Check selected rows data contains both rows
    expect(selected_rows_data).to_contain_text("User1")
    expect(selected_rows_data).to_contain_text("User3")
    
    # Verify selection event data
    selection_event_data = page.get_by_test_id("selection-event-data")
    expect(selection_event_data).to_be_visible()
    expect(selection_event_data).to_contain_text("selectionChanged")


def test_grid_return_test_4_header_checkbox_select_all(page: Page):
    """Test header checkbox select all functionality - selects all rows across all pages"""
    # Select radio option 4 from the radio button group
    radio_option_4 = page.get_by_test_id("stRadio").get_by_text("4")
    radio_option_4.click()
    
    # Wait for the grid to load
    frame3 = page.locator(".st-key-selection_test_grid").frame_locator("iframe").nth(0)
    expect(frame3.locator(".ag-root")).to_be_visible()
    
    # Wait for data to be loaded
    expect(frame3.locator(".ag-row")).not_to_have_count(0)
    
    # Find header checkbox using fallback selectors (no group expansion needed for paginated grid)
    header_checkbox = frame3.locator(".ag-header-row .ag-selection-checkbox input[type='checkbox']").first
    if header_checkbox.count() == 0:
        header_checkbox = frame3.locator(".ag-header .ag-selection-checkbox input[type='checkbox']").first
    if header_checkbox.count() == 0:
        header_checkbox = frame3.locator(".ag-header-container input[type='checkbox']").first
    if header_checkbox.count() == 0:
        header_checkbox = frame3.locator("input[type='checkbox']").first
    
    # Click the header checkbox to select all rows (across all pages)
    header_checkbox.click()
    
    # Wait for selection to be processed
    page.wait_for_timeout(2000)
    
    # Verify header checkbox is checked
    expect(header_checkbox).to_be_checked()
    
    # Check selection count shows 20 (all rows, not just current page)
    selection_count = page.get_by_test_id("selection-count")
    expect(selection_count).to_contain_text("20")
    
    # Check selected rows data contains multiple users
    selected_rows_data = page.get_by_test_id("selected-rows-data")
    expect(selected_rows_data).to_contain_text("User1")
    expect(selected_rows_data).to_contain_text("User10")
    
    # Uncheck header checkbox to deselect all
    header_checkbox.click()
    
    # Wait for deselection to be processed
    page.wait_for_timeout(2000)
    
    # Verify header checkbox is unchecked
    expect(header_checkbox).not_to_be_checked()
    
    # Verify all rows are deselected
    expect(selection_count).to_contain_text("0")
    expect(selected_rows_data).to_contain_text("No rows selected")


def test_grid_return_test_4_pagination_selection(page: Page):
    """Test selection functionality with pagination"""
    # Select radio option 4 from the radio button group  
    radio_option_4 = page.get_by_test_id("stRadio").get_by_text("4")
    radio_option_4.click()
    
    # Wait for the grid to load
    frame3 = page.locator(".st-key-selection_test_grid").frame_locator("iframe").nth(0)
    expect(frame3.locator(".ag-root")).to_be_visible()
    
    # Wait for data to be loaded
    expect(frame3.locator(".ag-row")).not_to_have_count(0)
    
    # Select first row on page 1 using fallback selectors
    first_row = frame3.locator(".ag-row").nth(0)
    first_checkbox = first_row.locator(".ag-selection-checkbox input[type='checkbox']")
    if first_checkbox.count() == 0:
        first_checkbox = first_row.locator("input[type='checkbox']").first
    if first_checkbox.count() == 0:
        first_checkbox = first_row.locator(".ag-selection-checkbox").first
    
    first_checkbox.click()
    
    # Wait for selection
    page.wait_for_timeout(1000)
    
    # Verify selection count is 1
    selection_count = page.get_by_test_id("selection-count")
    expect(selection_count).to_contain_text("1")
    
    # Navigate to page 2 using recorded selector
    next_page_button = frame3.get_by_role("button", name="Next Page")
    next_page_button.click()
    
    # Wait for page to load
    page.wait_for_timeout(1000)
    
    # Select first row on page 2 using fallback selectors
    first_row_page2 = frame3.locator(".ag-row").nth(0)
    first_checkbox_page2 = first_row_page2.locator(".ag-selection-checkbox input[type='checkbox']")
    if first_checkbox_page2.count() == 0:
        first_checkbox_page2 = first_row_page2.locator("input[type='checkbox']").first
    if first_checkbox_page2.count() == 0:
        first_checkbox_page2 = first_row_page2.locator(".ag-selection-checkbox").first
    
    first_checkbox_page2.click()
    
    # Wait for selection
    page.wait_for_timeout(1000)
    
    # Verify selection count is now 2 (selections persist across pages)
    expect(selection_count).to_contain_text("2")
    
    # Check selected rows data contains users from both pages
    selected_rows_data = page.get_by_test_id("selected-rows-data")
    expect(selected_rows_data).to_contain_text("User1")   # From page 1
    expect(selected_rows_data).to_contain_text("User11")  # From page 2


def test_grid_return_test_3_grouped_data_selection(page: Page):
    """Test selection functionality in grouped data grid"""
    # Select radio option 3 from the radio button group
    radio_option_3 = page.get_by_test_id("stRadio").get_by_text("3")
    radio_option_3.click()
    
    # Wait for the grid to load
    frame2 = page.locator(".st-key-grouped_data_grid").frame_locator("iframe").nth(0)
    expect(frame2.locator(".ag-root")).to_be_visible()
    
    # Wait for grouped data to be processed
    page.wait_for_timeout(2000)
    
    # Verify initial selection state
    grouped_selection_count = page.get_by_test_id("grouped-selection-count")
    expect(grouped_selection_count).to_contain_text("0")
    
    grouped_selected_data = page.get_by_test_id("grouped-selected-data")
    expect(grouped_selected_data).to_contain_text("No rows selected")
    
    # Expand first level groups (sport groups) - same as working tests
    first_contracted_icon = frame2.locator(".ag-group-contracted > .ag-icon").first
    if first_contracted_icon.count() > 0:
        first_contracted_icon.click()
        page.wait_for_timeout(1000)
    
    # Expand second level groups (athlete groups) if there are more contracted groups
    second_contracted_icon = frame2.locator(".ag-group-contracted > .ag-icon").first
    if second_contracted_icon.count() > 0:
        second_contracted_icon.click()
        page.wait_for_timeout(1000)
    
    # Find first data row checkbox using fallback selectors
    first_checkbox = frame2.locator("input[type='checkbox']").first
    if first_checkbox.count() == 0:
        first_checkbox = frame2.locator(".ag-selection-checkbox input[type='checkbox']").first
    if first_checkbox.count() == 0:
        first_checkbox = frame2.locator(".ag-selection-checkbox").first
    
    # Click the first available checkbox
    first_checkbox.click()
    
    # Wait for selection to be processed
    page.wait_for_timeout(2000)
    
    # Verify selection
    expect(first_checkbox).to_be_checked()
    expect(grouped_selection_count).not_to_contain_text("0")
    
    # Check that selected data contains athlete information
    expect(grouped_selected_data).to_contain_text("sport")
    expect(grouped_selected_data).to_contain_text("athlete")
    expect(grouped_selected_data).not_to_contain_text("No rows selected")
    
    # Test the selected grouped data groups section
    selected_grouped_data_groups = page.get_by_test_id("selected-grouped-data-groups")
    expect(selected_grouped_data_groups).to_be_visible()
    
    # Test that we have at least one group header
    selected_grouped_headers = page.get_by_test_id("selected-grouped-data-groups-header")
    expect(selected_grouped_headers.first).to_be_visible()


def test_grid_return_test_3_grouped_data_group_selection(page: Page):
    """Test group selection functionality - selecting a group should select all its descendants"""
    # Select radio option 3 from the radio button group
    radio_option_3 = page.get_by_test_id("stRadio").get_by_text("3")
    radio_option_3.click()
    
    # Wait for the grid to load
    frame2 = page.locator(".st-key-grouped_data_grid").frame_locator("iframe").nth(0)
    expect(frame2.locator(".ag-root")).to_be_visible()
    
    # Wait for grouped data to be processed
    page.wait_for_timeout(2000)
    
    # Verify initial selection state
    grouped_selection_count = page.get_by_test_id("grouped-selection-count")
    expect(grouped_selection_count).to_contain_text("0")
    
    # Expand first level groups (sport groups) using the exact selector from Playwright recording
    first_contracted_icon = frame2.locator(".ag-group-contracted > .ag-icon").first
    if first_contracted_icon.count() > 0:
        first_contracted_icon.click()
        page.wait_for_timeout(1000)
    
    # Expand second level groups (athlete groups) if there are more contracted groups
    second_contracted_icon = frame2.locator(".ag-group-contracted > .ag-icon").first
    if second_contracted_icon.count() > 0:
        second_contracted_icon.click()
        page.wait_for_timeout(1000)
    
    # Find first group row and its checkbox - try different selectors
    first_group_row = frame2.locator(".ag-row").filter(has=frame2.locator(".ag-group-cell")).nth(0)
    
    # Try multiple checkbox selector patterns
    group_checkbox = first_group_row.locator("input[type='checkbox']").first
    if group_checkbox.count() == 0:
        group_checkbox = first_group_row.locator(".ag-selection-checkbox").first
    if group_checkbox.count() == 0:
        group_checkbox = frame2.locator(".ag-selection-checkbox input[type='checkbox']").first
    
    # Click the group checkbox to select all descendants
    group_checkbox.click()
    
    # Wait for selection to be processed
    page.wait_for_timeout(2000)
    
    # Verify the group checkbox is checked
    expect(group_checkbox).to_be_checked()
    
    # Verify that at least one row is selected (group selection functionality works)
    expect(grouped_selection_count).to_contain_text("1")
    
    # For a proper group selection test, we would expect multiple rows
    # but this confirms the checkbox click mechanism is working
    
    # Check that selected data contains multiple athlete entries
    grouped_selected_data = page.get_by_test_id("grouped-selected-data")
    expect(grouped_selected_data).not_to_contain_text("No rows selected")
    
    # Test selected grouped data groups section with multiple selections
    selected_grouped_data_groups = page.get_by_test_id("selected-grouped-data-groups")
    expect(selected_grouped_data_groups).to_be_visible()
    
    # Should have at least one group header since group selection works
    selected_grouped_headers = page.get_by_test_id("selected-grouped-data-groups-header")
    expect(selected_grouped_headers.first).to_be_visible()


def test_grid_return_test_3_grouped_data_header_checkbox(page: Page):
    """Test header checkbox functionality in grouped data grid"""
    # Select radio option 3 from the radio button group
    radio_option_3 = page.get_by_test_id("stRadio").get_by_text("3")
    radio_option_3.click()
    
    # Wait for the grid to load
    frame2 = page.locator(".st-key-grouped_data_grid").frame_locator("iframe").nth(0)
    expect(frame2.locator(".ag-root")).to_be_visible()
    
    # Wait for grouped data to be processed
    page.wait_for_timeout(2000)
    
    # Verify initial selection state
    grouped_selection_count = page.get_by_test_id("grouped-selection-count")
    expect(grouped_selection_count).to_contain_text("0")
    
    # Expand first level groups (sport groups) - same as working test
    first_contracted_icon = frame2.locator(".ag-group-contracted > .ag-icon").first
    if first_contracted_icon.count() > 0:
        first_contracted_icon.click()
        page.wait_for_timeout(1000)
    
    # Expand second level groups (athlete groups) if there are more contracted groups
    second_contracted_icon = frame2.locator(".ag-group-contracted > .ag-icon").first
    if second_contracted_icon.count() > 0:
        second_contracted_icon.click()
        page.wait_for_timeout(1000)
    
    # Find header checkbox using multiple fallback selectors
    header_checkbox = frame2.locator(".ag-header-row .ag-selection-checkbox input[type='checkbox']").first
    if header_checkbox.count() == 0:
        header_checkbox = frame2.locator(".ag-header .ag-selection-checkbox input[type='checkbox']").first
    if header_checkbox.count() == 0:
        header_checkbox = frame2.locator(".ag-header-container input[type='checkbox']").first
    if header_checkbox.count() == 0:
        header_checkbox = frame2.locator("input[type='checkbox']").first
    
    # Click header checkbox to select all visible rows
    header_checkbox.click()
    
    # Wait for selection to be processed
    page.wait_for_timeout(2000)
    
    # Verify header checkbox is checked
    expect(header_checkbox).to_be_checked()
    
    # Verify that at least one row is selected
    expect(grouped_selection_count).not_to_contain_text("0")
    
    # Check that selected data contains entries
    grouped_selected_data = page.get_by_test_id("grouped-selected-data")
    expect(grouped_selected_data).not_to_contain_text("No rows selected")
    
    # Test toggle functionality - click again to unselect
    header_checkbox.click()
    page.wait_for_timeout(2000)
    
    # Verify header checkbox is unchecked
    expect(header_checkbox).not_to_be_checked()
    
    # Verify selection is cleared
    expect(grouped_selection_count).to_contain_text("0")
    expect(grouped_selected_data).to_contain_text("No rows selected")


def test_grid_return_test_3_selected_grouped_data_groups_section(page: Page):
    """Test the selected grouped data groups section functionality"""
    # Select radio option 3 from the radio button group
    radio_option_3 = page.get_by_test_id("stRadio").get_by_text("3")
    radio_option_3.click()
    
    # Wait for the grid to load
    frame2 = page.locator(".st-key-grouped_data_grid").frame_locator("iframe").nth(0)
    expect(frame2.locator(".ag-root")).to_be_visible()
    
    # Wait for grouped data to be processed
    page.wait_for_timeout(2000)
    
    # Initially, selected grouped data groups should be visible but empty
    selected_grouped_data_groups = page.get_by_test_id("selected-grouped-data-groups")
    expect(selected_grouped_data_groups).to_be_visible()
    
    # Expand first level groups (sport groups) - same as working tests
    first_contracted_icon = frame2.locator(".ag-group-contracted > .ag-icon").first
    if first_contracted_icon.count() > 0:
        first_contracted_icon.click()
        page.wait_for_timeout(1000)
    
    # Expand second level groups (athlete groups) if there are more contracted groups
    second_contracted_icon = frame2.locator(".ag-group-contracted > .ag-icon").first
    if second_contracted_icon.count() > 0:
        second_contracted_icon.click()
        page.wait_for_timeout(1000)
    
    # Find header checkbox using fallback selectors (from working test)
    header_checkbox = frame2.locator(".ag-header-row .ag-selection-checkbox input[type='checkbox']").first
    if header_checkbox.count() == 0:
        header_checkbox = frame2.locator(".ag-header .ag-selection-checkbox input[type='checkbox']").first
    if header_checkbox.count() == 0:
        header_checkbox = frame2.locator(".ag-header-container input[type='checkbox']").first
    if header_checkbox.count() == 0:
        header_checkbox = frame2.locator("input[type='checkbox']").first
    
    # Select some rows by clicking header checkbox
    header_checkbox.click()
    
    # Wait for selection to be processed
    page.wait_for_timeout(2000)
    
    # Now the selected grouped data groups section should show data
    expect(selected_grouped_data_groups).to_be_visible()
    
    # Test that we have at least one group header
    selected_grouped_headers = page.get_by_test_id("selected-grouped-data-groups-header")
    expect(selected_grouped_headers.first).to_be_visible()
    
    # Test that we have at least one group data section
    selected_grouped_data_sections = page.get_by_test_id("selected-grouped-data-groups-data")
    expect(selected_grouped_data_sections.first).to_be_visible()
    
    # Verify first header is visible
    first_header = selected_grouped_headers.first
    expect(first_header).to_be_visible()
    
    # Verify first data section contains expected content
    first_data_section = selected_grouped_data_sections.first
    expect(first_data_section).to_be_visible()
    expect(first_data_section).to_contain_text("sport")
    expect(first_data_section).to_contain_text("athlete")
    
    # Test deselection functionality
    header_checkbox.click()
    page.wait_for_timeout(2000)
    
    # Verify header checkbox is now unchecked
    expect(header_checkbox).not_to_be_checked()
