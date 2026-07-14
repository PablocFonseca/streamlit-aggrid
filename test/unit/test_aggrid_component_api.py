"""Regression tests for the public Components V2 boundary.

These tests deliberately replace the Streamlit component callable. They cover
the Python/component contract without requiring a browser or built frontend.
"""

import importlib
import json
from types import SimpleNamespace

import pandas as pd
import pytest

from streamlit_aggrid.AgGridReturn import AgGridReturn
from streamlit_aggrid.aggrid_utils import compute_data_hash
from streamlit_aggrid.shared import (
    AgGridTheme,
    DataReturnMode,
    GridUpdateMode,
    JsCode,
)


aggrid_module = importlib.import_module("streamlit_aggrid.AgGrid")


@pytest.fixture
def component_calls(monkeypatch):
    calls = []

    def get_component_func(isolate_styles=True):
        def component(**kwargs):
            calls.append(
                {
                    "isolate_styles": isolate_styles,
                    **kwargs,
                }
            )
            return {"grid_response": {}}

        return component

    monkeypatch.setattr(aggrid_module, "_get_component_func", get_component_func)
    return calls


def test_component_registration_is_lazy_and_cached_per_style_mode(monkeypatch):
    registrations = []

    def register(**kwargs):
        registrations.append(kwargs)
        return object()

    monkeypatch.setattr(aggrid_module.components, "component", register)

    # Reloading is the closest unit-level approximation of importing the wheel.
    # Import itself must not ask Streamlit to validate the component manifest.
    reloaded = importlib.reload(aggrid_module)
    assert registrations == []

    isolated = reloaded._get_component_func(True)
    assert reloaded._get_component_func(True) is isolated
    unisolated = reloaded._get_component_func(False)
    assert unisolated is not isolated
    assert registrations == [
        {
            "name": "streamlit-aggrid.agGrid",
            "js": "index-*.mjs",
            "css": "index-*.css",
            "isolate_styles": True,
        },
        {
            "name": "streamlit-aggrid.agGrid",
            "js": "index-*.mjs",
            "css": "index-*.css",
            "isolate_styles": False,
        },
    ]


def test_default_toolbar_and_compatibility_css_reach_component(component_calls):
    css = {".ag-header": {"font-weight": "700"}}

    aggrid_module.AgGrid(
        pd.DataFrame({"value": [1]}),
        key="grid",
        custom_css=css,
    )

    call = component_calls[0]
    assert call["key"] == "grid"
    assert call["isolate_styles"] is True
    assert call["data"]["show_toolbar"] is False
    assert call["data"]["custom_css"] == css


def test_initial_legacy_response_exposes_input_data(component_calls):
    data = pd.DataFrame({"value": [1, 2]}, index=["first", "second"])
    expected = data.copy()

    response = aggrid_module.AgGrid(data, key="grid")

    pd.testing.assert_frame_equal(response.data, expected)
    assert response.selected_data is None
    assert "::auto_unique_id::" not in response.data.columns


def test_callback_requires_a_component_key(component_calls):
    with pytest.raises(ValueError, match="key must be set"):
        aggrid_module.AgGrid(gridOptions={}, callback=lambda response: None)

    assert component_calls == []


def test_callback_receives_same_aggrid_return_shape(monkeypatch, component_calls):
    payload = {
        "nodes": [],
        "eventData": {"type": "cellValueChanged", "value": 42},
    }
    callback_values = []
    monkeypatch.setattr(
        aggrid_module,
        "st",
        SimpleNamespace(session_state={"grid": {"grid_response": payload}}),
    )

    aggrid_module.AgGrid(
        gridOptions={},
        key="grid",
        callback=callback_values.append,
    )
    component_calls[0]["on_grid_response_change"]()

    assert len(callback_values) == 1
    callback_response = callback_values[0]
    assert isinstance(callback_response, AgGridReturn)
    assert callback_response.grid_response == payload
    assert callback_response.event_data["type"] == "cellValueChanged"


def test_callback_normalizes_non_string_key_for_session_state(
    monkeypatch, component_calls
):
    payload = {"eventData": {"type": "selectionChanged"}}
    callback_values = []
    monkeypatch.setattr(
        aggrid_module,
        "st",
        SimpleNamespace(session_state={"7": {"grid_response": payload}}),
    )

    aggrid_module.AgGrid(
        gridOptions={},
        key=7,
        callback=callback_values.append,
    )
    component_calls[0]["on_grid_response_change"]()

    assert component_calls[0]["key"] == "7"
    assert callback_values[0].grid_response == payload


def test_custom_return_payload_is_exposed_directly(component_calls, monkeypatch):
    custom_payload = {"rowCount": 3, "editedField": "price"}

    def get_component_func(isolate_styles=True):
        def component(**kwargs):
            component_calls.append(kwargs)
            return {"grid_response": custom_payload}

        return component

    monkeypatch.setattr(aggrid_module, "_get_component_func", get_component_func)
    response = aggrid_module.AgGrid(
        gridOptions={},
        key="grid",
        custom_jscode_for_grid_return=JsCode(
            "function({eventData}) { return {rowCount: eventData.api.getDisplayedRowCount()}; }"
        ),
    )

    assert response.data_return_mode is DataReturnMode.CUSTOM
    assert response.grid_response == custom_payload
    assert component_calls[0]["data"]["data_return_mode"] == "CUSTOM"
    assert component_calls[0]["data"]["allow_unsafe_jscode"] is True


def test_explicit_toolbar_and_style_isolation_are_forwarded(component_calls):
    aggrid_module.AgGrid(
        gridOptions={},
        key="grid",
        show_toolbar=True,
        isolate_styles=False,
    )

    assert component_calls[0]["isolate_styles"] is False
    assert component_calls[0]["data"]["show_toolbar"] is True


@pytest.mark.parametrize(
    ("theme", "expected_name"),
    [
        ("streamlit", "streamlit"),
        ("alpine", "alpine"),
        ("balham", "balham"),
        ("material", "material"),
        (AgGridTheme.BALHAM, "balham"),
        (None, "streamlit"),
    ],
)
def test_supported_theme_names_are_forwarded(theme, expected_name, component_calls):
    aggrid_module.AgGrid(gridOptions={}, key="grid", theme=theme)

    assert component_calls[0]["data"]["theme"]["themeName"] == expected_name


@pytest.mark.parametrize("theme", ["light", "dark", "blue", "fresh", "typo"])
def test_unimplemented_or_unknown_theme_names_are_rejected(theme, component_calls):
    with pytest.raises(ValueError, match="not a valid theme"):
        aggrid_module.AgGrid(gridOptions={}, key="grid", theme=theme)

    assert component_calls == []


def test_omitted_update_on_uses_modern_default_events(component_calls):
    aggrid_module.AgGrid(gridOptions={}, key="grid")

    assert component_calls[0]["data"]["update_on"] == [
        "cellValueChanged",
        "selectionChanged",
        "filterChanged",
        "sortChanged",
    ]


def test_manual_update_mode_disables_automatic_events_when_omitted(component_calls):
    aggrid_module.AgGrid(
        gridOptions={},
        key="grid",
        update_mode=GridUpdateMode.MANUAL,
    )

    payload = component_calls[0]["data"]
    assert payload["manual_update"] is True
    assert payload["update_on"] == []


def test_manual_update_mode_respects_explicit_update_events(component_calls):
    aggrid_module.AgGrid(
        gridOptions={},
        key="grid",
        update_mode=GridUpdateMode.MANUAL,
        update_on=[("cellValueChanged", 250)],
    )

    payload = component_calls[0]["data"]
    assert payload["manual_update"] is True
    assert payload["update_on"] == [("cellValueChanged", 250)]


def test_legacy_update_mode_replaces_modern_defaults_when_update_on_omitted(
    component_calls,
):
    aggrid_module.AgGrid(
        gridOptions={},
        key="grid",
        update_mode=GridUpdateMode.VALUE_CHANGED,
    )

    payload = component_calls[0]["data"]
    assert payload["manual_update"] is False
    assert payload["update_on"] == ["cellValueChanged"]


def test_explicit_event_specs_are_deduplicated_and_override_legacy_defaults(
    component_calls,
):
    aggrid_module.AgGrid(
        gridOptions={},
        key="grid",
        update_mode=GridUpdateMode.GRID_CHANGED,
        update_on=[
            "cellValueChanged",
            ("cellValueChanged", 250),
            ("columnMoved", 900),
            ("columnPinned", 700),
            "columnPinned",
        ],
    )

    update_on = component_calls[0]["data"]["update_on"]
    assert update_on.count(("cellValueChanged", 250)) == 1
    assert "cellValueChanged" not in update_on
    assert update_on.count(("columnMoved", 900)) == 1
    assert ("columnMoved", 500) not in update_on
    assert update_on.count(("columnPinned", 700)) == 1
    assert "columnPinned" not in update_on
    assert [_event[0] if isinstance(_event, tuple) else _event for _event in update_on] == [
        "cellValueChanged",
        "columnMoved",
        "columnPinned",
        "selectionChanged",
        "filterChanged",
        "sortChanged",
        "columnResized",
        "columnVisible",
    ]


@pytest.mark.parametrize(
    "strategy",
    ["client_wins", "server_wins"],
)
def test_server_sync_strategy_is_forwarded(strategy, component_calls):
    aggrid_module.AgGrid(
        gridOptions={},
        key="grid",
        server_sync_strategy=strategy,
    )

    assert component_calls[0]["data"]["server_sync_strategy"] == strategy


def test_server_wins_rows_is_forwarded_with_stable_row_id(component_calls):
    get_row_id = JsCode("function(params) { return String(params.data.id); }")

    aggrid_module.AgGrid(
        pd.DataFrame({"id": ["a"], "value": [1]}),
        gridOptions={"getRowId": get_row_id},
        key="grid",
        allow_unsafe_jscode=True,
        server_sync_strategy="server_wins_rows",
    )

    payload = component_calls[0]["data"]
    assert payload["server_sync_strategy"] == "server_wins_rows"
    assert payload["gridOptions"]["getRowId"] == get_row_id.js_code
    assert "::auto_unique_id::" not in payload["data"].schema.names


def test_unknown_server_sync_strategy_fails_before_component_call(component_calls):
    with pytest.raises(ValueError, match="not a valid server_sync_strategy"):
        aggrid_module.AgGrid(
            gridOptions={},
            key="grid",
            server_sync_strategy="last_writer_wins",
        )

    assert component_calls == []


def test_server_wins_rows_requires_explicit_stable_row_id(component_calls):
    with pytest.raises(ValueError, match="requires an explicit, stable"):
        aggrid_module.AgGrid(
            pd.DataFrame({"id": ["a"], "value": [1]}),
            key="grid",
            server_sync_strategy="server_wins_rows",
        )

    assert component_calls == []


def test_server_wins_rows_requires_jscode_execution(component_calls):
    with pytest.raises(ValueError, match="allow_unsafe_jscode=True"):
        aggrid_module.AgGrid(
            pd.DataFrame({"id": ["a"], "value": [1]}),
            gridOptions={
                "getRowId": JsCode("params => String(params.data.id)")
            },
            key="grid",
            server_sync_strategy="server_wins_rows",
        )

    assert component_calls == []


def test_server_wins_rows_rejects_non_jscode_row_id(component_calls):
    with pytest.raises(ValueError, match="to be a JsCode callback"):
        aggrid_module.AgGrid(
            pd.DataFrame({"id": ["a"], "value": [1]}),
            gridOptions={"getRowId": "params => String(params.data.id)"},
            key="grid",
            allow_unsafe_jscode=True,
            server_sync_strategy="server_wins_rows",
        )

    assert component_calls == []


@pytest.mark.parametrize("row_model", ["serverSide", "infinite", "viewport"])
def test_server_wins_rows_requires_client_side_row_model(row_model, component_calls):
    with pytest.raises(ValueError, match="only supports the client-side row model"):
        aggrid_module.AgGrid(
            gridOptions={
                "rowModelType": row_model,
                "getRowId": JsCode(
                    "function(params) { return String(params.data.id); }"
                ),
            },
            key="grid",
            allow_unsafe_jscode=True,
            server_sync_strategy="server_wins_rows",
        )

    assert component_calls == []


def test_json_serialized_row_data_has_a_content_hash(component_calls):
    aggrid_module.AgGrid(
        pd.DataFrame({"id": ["a", "b"], "value": [1, 2]}),
        gridOptions={"getRowId": JsCode("params => String(params.data.id)")},
        key="grid",
        allow_unsafe_jscode=True,
        use_json_serialization=True,
        server_sync_strategy="server_wins_rows",
    )

    payload = component_calls[0]["data"]
    row_data = payload["gridOptions"]["rowData"]
    assert payload["data"] is None
    assert payload["data_hash"] == compute_data_hash(row_data)
    assert payload["data_hash"] is not None


def test_json_serialization_preserves_initial_return_data(component_calls):
    result = aggrid_module.AgGrid(
        pd.DataFrame({"id": ["a", "b"], "value": [1, 2]}),
        key="grid",
        use_json_serialization=True,
    )

    assert result.data is not None
    assert result.data.to_dict(orient="records") == [
        {"id": "a", "value": 1},
        {"id": "b", "value": 2},
    ]


def test_list_row_data_is_serialized_and_forwarded_in_json_mode(component_calls):
    result = aggrid_module.AgGrid(
        gridOptions={
            "columnDefs": [{"field": "id"}, {"field": "value"}],
            "rowData": [{"id": "a", "value": 1}],
        },
        key="grid",
        use_json_serialization=True,
    )

    payload = component_calls[0]["data"]
    assert payload["data"] is None
    assert isinstance(payload["gridOptions"]["rowData"], str)
    assert json.loads(payload["gridOptions"]["rowData"])[0]["id"] == "a"
    assert result.data is not None
    assert result.data.iloc[0]["value"] == 1


def test_dual_data_sources_raise_in_json_mode(component_calls):
    with pytest.raises(ValueError, match="both"):
        aggrid_module.AgGrid(
            pd.DataFrame({"id": ["a"]}),
            gridOptions={"rowData": []},
            key="grid",
            use_json_serialization=True,
        )

    assert component_calls == []


def test_auto_serialization_preflight_falls_back_before_streamlit_coercion(
    component_calls,
):
    aggrid_module.AgGrid(
        pd.DataFrame({"mixed": [1, "two"]}),
        key="grid",
        use_json_serialization="auto",
    )

    payload = component_calls[0]["data"]
    assert payload["data"] is None
    assert payload["use_json_serialization"] is True
    assert [
        row["mixed"] for row in json.loads(payload["gridOptions"]["rowData"])
    ] == [1, "two"]


def test_valid_arrow_preflight_reuses_the_validated_table(component_calls):
    import pyarrow as pa

    source = pd.DataFrame({"id": ["a", "b"], "value": [1, 2]})

    result = aggrid_module.AgGrid(source, key="grid")

    payload = component_calls[0]["data"]
    assert isinstance(payload["data"], pa.Table)
    assert payload["data"].column("value").to_pylist() == [1, 2]
    assert result.data.to_dict(orient="records") == [
        {"id": "a", "value": 1},
        {"id": "b", "value": 2},
    ]
    assert "::auto_unique_id::" not in source.columns


def test_false_serialization_preflight_raises_original_arrow_error(component_calls):
    with pytest.raises(Exception, match="convert|Conversion|Arrow"):
        aggrid_module.AgGrid(
            pd.DataFrame({"mixed": [1, "two"]}),
            key="grid",
            use_json_serialization=False,
        )

    assert component_calls == []


def test_unknown_json_serialization_mode_is_rejected(component_calls):
    with pytest.raises(ValueError, match="must be 'auto', True, or False"):
        aggrid_module.AgGrid(
            gridOptions={},
            key="grid",
            use_json_serialization="sometimes",
        )

    assert component_calls == []


@pytest.mark.parametrize("value", [0, 1])
def test_integer_json_serialization_modes_are_rejected(value, component_calls):
    with pytest.raises(ValueError, match="must be 'auto', True, or False"):
        aggrid_module.AgGrid(
            gridOptions={},
            key="grid",
            use_json_serialization=value,
        )

    assert component_calls == []
