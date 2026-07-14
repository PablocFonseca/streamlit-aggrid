from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread

import pytest
from playwright.sync_api import Page, expect

from e2e_utils import StreamlitRunner


pytestmark = pytest.mark.e2e

HERE = Path(__file__).parent.absolute()
SERVER_SYNC_FILE = HERE / "grid_server_sync.py"


@pytest.fixture(scope="module")
def streamlit_app():
    with StreamlitRunner(SERVER_SYNC_FILE) as runner:
        yield runner


@pytest.fixture(scope="module")
def outer_iframe_url(streamlit_app: StreamlitRunner):
    """Serve a real outer page on a second localhost origin."""
    document = (
        "<!doctype html><html><body>"
        f'<iframe id="streamlit-app" src="{streamlit_app.server_url}/?embed=true" '
        'style="width: 1200px; height: 900px"></iframe>'
        "</body></html>"
    ).encode()

    class OuterPageHandler(BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(document)))
            self.end_headers()
            self.wfile.write(document)

        def log_message(self, _format, *args):
            return

    server = ThreadingHTTPServer(("127.0.0.1", 0), OuterPageHandler)
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://localhost:{server.server_port}"
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


@pytest.fixture(autouse=True)
def go_to_app(page: Page, streamlit_app: StreamlitRunner):
    page.goto(streamlit_app.server_url)
    page.get_by_role("img", name="Running...").is_hidden()


def _row(grid, row_id: str):
    return grid.locator(f".ag-row[row-id='{row_id}']")


def _value_cell(grid, row_id: str):
    return _row(grid, row_id).locator(".ag-cell[col-id='value']")


def _object_change_count(page: Page, row_id: str) -> int:
    return page.evaluate(
        "rowId => window.__serverWinsRowsObjectChanges?.[rowId] || 0", row_id
    )


def test_server_wins_rows_reconciles_only_changed_rows(page: Page):
    row_grid = page.locator(".st-key-server_wins_rows_grid")
    full_grid = page.locator(".st-key-server_wins_grid")
    json_row_data_grid = page.locator(".st-key-json_row_data_grid")
    expect(row_grid.locator(".ag-root")).to_be_visible()
    expect(full_grid.locator(".ag-root")).to_be_visible()
    expect(json_row_data_grid.locator(".ag-root")).to_be_visible()
    expect(json_row_data_grid.locator(".ag-cell[col-id='value']")).to_have_text(
        "from-grid-options"
    )

    # A client edit is rolled back even though the server data hash is unchanged.
    alpha = _value_cell(row_grid, "a")
    expect(alpha).to_have_text("alpha")
    alpha.dblclick()
    editor = alpha.locator("input")
    expect(editor).to_be_visible()
    editor.fill("client-only")
    editor.press("Enter")
    expect(_value_cell(row_grid, "a")).to_have_text("alpha")

    # A client-side transaction does not emit cellValueChanged. It must still
    # mark the grid dirty so an otherwise unrelated rerun restores the same-hash
    # authoritative server snapshot.
    page.evaluate(
        """
        () => {
            window.__serverWinsRowsApi.applyTransaction({
                update: [{id: "a", value: "transaction-only", revision: 1}]
            })
        }
        """
    )
    expect(_value_cell(row_grid, "a")).to_have_text("transaction-only")
    page.get_by_role("button", name="Toggle runtime pagination").click()
    expect(_value_cell(row_grid, "a")).to_have_text("alpha")

    a_before = _object_change_count(page, "a")
    b_before = _object_change_count(page, "b")
    _row(row_grid, "a").evaluate(
        "element => element.dataset.unchangedRow = 'preserved'"
    )
    page.evaluate("window.__serverWinsRowsOptionUpdates = []")

    page.get_by_role("button", name="Apply server row changes").click()

    expect(_value_cell(row_grid, "b")).to_have_text("bravo-server")
    expect(_row(row_grid, "b").locator(".ag-cell[col-id='revision']")).to_have_text(
        "2"
    )
    expect(_row(row_grid, "c")).to_have_count(0)
    expect(_value_cell(row_grid, "d")).to_have_text("delta")
    expect(_row(row_grid, "a")).to_have_attribute("data-unchanged-row", "preserved")

    # The unchanged row keeps its exact data object, while the changed row gets
    # the new server object that tells AG Grid to refresh it.
    assert _object_change_count(page, "a") == a_before
    assert _object_change_count(page, "b") > b_before

    # A row-only Components V2 invocation must not reapply column definitions,
    # theme, or other semantically unchanged options. That work would rebuild
    # cells and erase most of the benefit of preserving unchanged row objects.
    option_updates = page.evaluate("window.__serverWinsRowsOptionUpdates")
    assert option_updates
    assert all("rowData" in keys for keys in option_updates)
    assert all(
        not {"columnDefs", "defaultColDef", "theme", "getRowId"}.intersection(keys)
        for keys in option_updates
    )

    # The ordinary server_wins path also receives JSON-serialized rerun data.
    full_values = full_grid.locator(".ag-cell[col-id='value']")
    expect(full_values).to_have_text(["alpha", "bravo-server", "delta"])

    # This update changes order only, guarding the order-sensitive data hash.
    page.get_by_role("button", name="Reorder server rows").click()
    expect(_row(row_grid, "b")).to_have_attribute("row-index", "0")
    expect(_row(row_grid, "a")).to_have_attribute("row-index", "1")
    expect(_row(row_grid, "d")).to_have_attribute("row-index", "2")


def test_component_assets_and_state_work_inside_an_outer_iframe(
    page: Page, outer_iframe_url: str
):
    # The outer document and Streamlit use different localhost ports, so this
    # exercises a genuine iframe origin boundary without triggering Chromium's
    # opaque-origin Local Network Access block for about:blank.
    page.goto(outer_iframe_url)

    embedded = page.frame_locator("#streamlit-app")
    row_grid = embedded.locator(".st-key-server_wins_rows_grid")
    expect(row_grid.locator(".ag-root")).to_be_visible()
    expect(_value_cell(row_grid, "b")).to_have_text("bravo")

    embedded.get_by_role("button", name="Apply server row changes").click()
    expect(_value_cell(row_grid, "b")).to_have_text("bravo-server")
    expect(_value_cell(row_grid, "d")).to_have_text("delta")


def test_removed_runtime_grid_option_is_reset(page: Page):
    grid = page.locator(".st-key-runtime_options_grid")
    expect(grid.locator(".ag-root")).to_be_visible()
    paging_panel = grid.locator(".ag-paging-panel")
    expect(paging_panel).to_be_visible()

    page.get_by_role("button", name="Toggle runtime pagination").click()
    expect(paging_panel).to_be_hidden()

    page.get_by_role("button", name="Toggle runtime pagination").click()
    expect(paging_panel).to_be_visible()
