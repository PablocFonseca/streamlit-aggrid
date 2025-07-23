from pathlib import Path
import pytest
from playwright.sync_api import Page, expect
from e2e_utils import StreamlitRunner

ROOT_DIRECTORY = Path(__file__).parent.parent.absolute()
BASIC_EXAMPLE_FILE = ROOT_DIRECTORY / "test" / "grid_drag_and_drop_example.py"

@pytest.fixture(autouse=True, scope="module")
def streamlit_app():
    with StreamlitRunner(BASIC_EXAMPLE_FILE) as runner:
        yield runner

@pytest.fixture(autouse=True, scope="function")
def go_to_app(page: Page, streamlit_app: StreamlitRunner):
    page.goto(streamlit_app.server_url)
    page.get_by_role("img", name="Running...").is_hidden()

def test_drag_first_row_to_last(page: Page):
    frame = page.locator(".st-key-drag_grid").frame_locator("iframe").nth(0)
    first_row_handle = frame.locator(".ag-center-cols-container .ag-row").nth(0).locator(".ag-row-drag")
    last_row = frame.locator(".ag-center-cols-container .ag-row").nth(-1)
    first_row_handle.drag_to(last_row)
    page.wait_for_timeout(500)
    rows = frame.locator(".ag-center-cols-container .ag-row")
    ids = [rows.nth(i).locator('[col-id="id"]').inner_text() for i in range(rows.count())]
    row_indices = [int(rows.nth(i).get_attribute("aria-rowindex")) for i in range(rows.count())]
    
    # Pair each id with its aria-rowindex and sort by aria-rowindex
    sorted_ids = [id for _, id in sorted(zip(row_indices, ids))]
    print("Visual order by aria-rowindex:", sorted_ids)
    assert sorted_ids == ["2", "3", "1", "4"]

    # Find the row with id "1" and check its aria-rowindex
    for i in range(rows.count()):
        if rows.nth(i).locator('[col-id="id"]').inner_text() == "1":
            assert rows.nth(i).get_attribute("aria-rowindex") == "4"  # If you expect it to be third visually