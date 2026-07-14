"""Regression tests for the public Components V2 boundary.

These tests deliberately replace the Streamlit component callable. They cover
the Python/component contract without requiring a browser or built frontend.
"""

import importlib
from types import SimpleNamespace

import pandas as pd
import pytest

from streamlit_aggrid.AgGridReturn import AgGridReturn
from streamlit_aggrid.shared import DataReturnMode, JsCode


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
