import pandas as pd
import streamlit as st

from st_aggrid import AgGrid, DataReturnMode, JsCode


INITIAL_ROWS = [
    {"id": "a", "value": "alpha", "revision": 1},
    {"id": "b", "value": "bravo", "revision": 1},
    {"id": "c", "value": "charlie", "revision": 1},
]

UPDATED_ROWS = [
    {"id": "a", "value": "alpha", "revision": 1},
    {"id": "b", "value": "bravo-server", "revision": 2},
    {"id": "d", "value": "delta", "revision": 1},
]


if "server_rows" not in st.session_state:
    st.session_state.server_rows = INITIAL_ROWS
if "runtime_pagination" not in st.session_state:
    st.session_state.runtime_pagination = True

if st.button("Apply server row changes"):
    st.session_state.server_rows = UPDATED_ROWS

if st.button("Reorder server rows"):
    by_id = {row["id"]: row for row in st.session_state.server_rows}
    if set(by_id) == {"a", "b", "d"}:
        st.session_state.server_rows = [by_id["b"], by_id["a"], by_id["d"]]

if st.button("Toggle runtime pagination"):
    st.session_state.runtime_pagination = not st.session_state.runtime_pagination


row_options = {
    "columnDefs": [
        {"field": "id"},
        {
            "field": "value",
            "editable": True,
            "valueGetter": JsCode(
                """
                function(params) {
                    window.__serverWinsRowsEvaluations ??= {};
                    window.__serverWinsRowsObjects ??= {};
                    window.__serverWinsRowsObjectChanges ??= {};
                    const id = params.data.id;
                    window.__serverWinsRowsEvaluations[id] =
                        (window.__serverWinsRowsEvaluations[id] || 0) + 1;
                    if (id in window.__serverWinsRowsObjects &&
                        window.__serverWinsRowsObjects[id] !== params.data) {
                        window.__serverWinsRowsObjectChanges[id] =
                            (window.__serverWinsRowsObjectChanges[id] || 0) + 1;
                    }
                    window.__serverWinsRowsObjects[id] = params.data;
                    return params.data.value;
                }
                """
            ),
            "valueSetter": JsCode(
                "params => { params.data.value = params.newValue; return true; }"
            ),
        },
        {"field": "revision"},
    ],
    "getRowId": JsCode("params => String(params.data.id)"),
    "onGridReady": JsCode(
        """
        function(params) {
            window.__serverWinsRowsApi = params.api;
            window.__serverWinsRowsOptionUpdates = [];
            const updateGridOptions = params.api.updateGridOptions.bind(params.api);
            params.api.updateGridOptions = function(options) {
                window.__serverWinsRowsOptionUpdates.push(Object.keys(options));
                return updateGridOptions(options);
            };
        }
        """
    ),
    "animateRows": False,
}

AgGrid(
    pd.DataFrame(st.session_state.server_rows),
    gridOptions=row_options,
    key="server_wins_rows_grid",
    # Give the transaction regression a harmless component-prop change on the
    # pagination rerun. Components V2 intentionally skips byte-identical
    # component invocations.
    height=400 if st.session_state.runtime_pagination else 401,
    allow_unsafe_jscode=True,
    data_return_mode=DataReturnMode.MINIMAL,
    update_on=["cellValueChanged"],
    use_json_serialization=True,
    server_sync_strategy="server_wins_rows",
)

# Exercise the regular server-authoritative path alongside row reconciliation.
AgGrid(
    pd.DataFrame(st.session_state.server_rows),
    key="server_wins_grid",
    use_json_serialization=True,
    server_sync_strategy="server_wins",
)

AgGrid(
    gridOptions={
        "columnDefs": [{"field": "id"}, {"field": "value"}],
        "rowData": [{"id": "json-row", "value": "from-grid-options"}],
    },
    key="json_row_data_grid",
    use_json_serialization=True,
)

runtime_options = {
    "columnDefs": [{"field": "id"}, {"field": "value"}],
    "paginationPageSize": 2,
}
if st.session_state.runtime_pagination:
    runtime_options["pagination"] = True

AgGrid(
    pd.DataFrame(INITIAL_ROWS),
    gridOptions=runtime_options,
    key="runtime_options_grid",
    server_sync_strategy="server_wins",
)
