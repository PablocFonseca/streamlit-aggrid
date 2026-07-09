from pathlib import Path
import pytest
from playwright.sync_api import Page, expect
from e2e_utils import StreamlitRunner

pytestmark = pytest.mark.e2e

HERE = Path(__file__).parent.absolute()
BASIC_EXAMPLE_FILE = HERE / "grid_drag_and_drop_example.py"

@pytest.fixture(autouse=True, scope="module")
def streamlit_app():
    with StreamlitRunner(BASIC_EXAMPLE_FILE) as runner:
        yield runner

@pytest.fixture(autouse=True, scope="function")
def go_to_app(page: Page, streamlit_app: StreamlitRunner):
    page.goto(streamlit_app.server_url)
    page.get_by_role("img", name="Running...").is_hidden()

def test_drag_first_row_to_last(page: Page):
    frame = page.locator(".st-key-drag_grid")
    rows = frame.locator(".ag-center-cols-container .ag-row")
    expect(rows.first).to_be_visible()

    first_row_handle = rows.nth(0).locator(".ag-row-drag")
    last_row = rows.nth(-1)

    # AG Grid row dragging is mouse-driven, not native HTML5 drag-and-drop, so
    # Playwright's drag_to() won't trigger it. Simulate the real pointer sequence.
    rows.nth(0).hover()
    src = first_row_handle.bounding_box()
    dst = last_row.bounding_box()
    page.mouse.move(src["x"] + src["width"] / 2, src["y"] + src["height"] / 2)
    page.mouse.down()
    page.mouse.move(src["x"] + src["width"] / 2, src["y"] + src["height"] / 2 + 5)
    page.mouse.move(dst["x"] + dst["width"] / 2, dst["y"] + dst["height"] / 2, steps=15)
    page.mouse.up()
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