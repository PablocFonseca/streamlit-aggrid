"""Unit tests for AgGridReturn (no browser or Streamlit runtime required)."""

from collections.abc import Mapping

import pandas as pd
import pytest

from streamlit_aggrid.AgGridReturn import AgGridReturn
from streamlit_aggrid.shared import DataReturnMode


def make_response(nodes, **extra):
    """Wrap nodes in the component result shape AgGridReturn expects."""
    return {"grid_response": {"nodes": nodes, **extra}}


@pytest.fixture
def simple_nodes():
    """Three rows; grid sorted so display order is reversed (via rowIndex)."""
    return [
        {
            "id": "0",
            "data": {"Name": "Alice", "Age": 25, "::auto_unique_id::": "0"},
            "rowIndex": 2,
            "isSelected": True,
            "group": False,
        },
        {
            "id": "1",
            "data": {"Name": "Bob", "Age": 30, "::auto_unique_id::": "1"},
            "rowIndex": 1,
            "isSelected": False,
            "group": False,
        },
        {
            "id": "2",
            "data": {"Name": "Charlie", "Age": 35, "::auto_unique_id::": "2"},
            "rowIndex": 0,
            "isSelected": True,
            "group": False,
        },
    ]


@pytest.fixture
def grouped_nodes():
    """Two leaf rows grouped under sport groups (AG Grid parentPath format)."""
    return [
        {"id": "g0", "data": {}, "group": True, "isSelected": False},
        {
            "id": "0",
            "data": {"sport": "Swimming", "athlete": "Phelps"},
            "rowIndex": 0,
            "group": False,
            "isSelected": False,
            "parentPath": "ROOT_NODE_ID.row-group-sport-Swimming",
        },
        {
            "id": "1",
            "data": {"sport": "Judo", "athlete": "Silva"},
            "rowIndex": 1,
            "group": False,
            "isSelected": False,
            "parentPath": "ROOT_NODE_ID.row-group-sport-Judo",
        },
    ]


class TestEmptyResponse:
    def test_default_construction(self):
        r = AgGridReturn()
        assert r.data is None
        assert r.selected_data is None
        assert r.selected_rows is None
        assert r.grid_state is None
        assert r.event_data == {}

    def test_empty_grid_response_value(self):
        r = AgGridReturn(grid_response={"grid_response": {}})
        assert r.data is None

    def test_grid_response_key_none(self):
        r = AgGridReturn(grid_response={"grid_response": None})
        assert r.data is None


class TestCustomResponse:
    @pytest.mark.parametrize("payload", [0, False, "", [], ["a", "b"]])
    def test_falsy_and_non_mapping_payloads_are_preserved(self, payload):
        r = AgGridReturn(
            grid_response={"grid_response": payload},
            data_return_mode=DataReturnMode.CUSTOM,
        )

        assert r.grid_response == payload
        assert r.raw_data == payload
        assert r.data is None
        assert r.selected_data is None
        assert r.event_data == {}

    def test_mapping_payload_supports_mapping_compatibility(self):
        payload = {"rowCount": 3, "editedField": "price"}
        r = AgGridReturn(
            grid_response={"grid_response": payload},
            data_return_mode=DataReturnMode.CUSTOM,
        )

        assert r.grid_response == payload
        assert r.raw_data == payload
        assert r["rowCount"] == 3
        assert r.get("editedField") == "price"
        assert r.get("missing", "fallback") == "fallback"

    def test_custom_payload_keys_take_precedence_over_public_properties(self):
        payload = {
            "data": "custom data",
            "grid_state": "custom grid state",
            "raw_data": "custom raw data",
        }
        r = AgGridReturn(
            grid_response={"grid_response": payload},
            data_return_mode=DataReturnMode.CUSTOM,
        )

        assert r["data"] == "custom data"
        assert r["grid_state"] == "custom grid state"
        assert r["raw_data"] == "custom raw data"
        assert dict(r)["data"] == "custom data"


class TestMinimalResponse:
    def test_compact_event_data_has_no_dataframe_snapshot(self):
        event = {
            "streamlitRerunEventTriggerName": "cellValueChanged",
            "newValue": 11,
            "data": {"id": "row-1", "quantity": 11},
            "node": {"id": "row-1", "rowIndex": 0},
            "column": {"colId": "quantity"},
        }
        r = AgGridReturn(
            grid_response={"grid_response": {"eventData": event}},
            data_return_mode=DataReturnMode.MINIMAL,
        )

        assert r.event_data == event
        assert r.data is None
        assert r.selected_data is None
        assert "nodes" not in r.grid_response


class TestDataReturnModes:
    def test_as_input_keeps_node_order(self, simple_nodes):
        r = AgGridReturn(make_response(simple_nodes), DataReturnMode.AS_INPUT)
        assert list(r.data["Name"]) == ["Alice", "Bob", "Charlie"]

    def test_filtered_excludes_rows_without_row_index(self, simple_nodes):
        simple_nodes[1] = {**simple_nodes[1], "rowIndex": None}
        r = AgGridReturn(make_response(simple_nodes), DataReturnMode.FILTERED)
        assert list(r.data["Name"]) == ["Alice", "Charlie"]

    def test_filtered_and_sorted_orders_by_row_index(self, simple_nodes):
        r = AgGridReturn(
            make_response(simple_nodes), DataReturnMode.FILTERED_AND_SORTED
        )
        assert list(r.data["Name"]) == ["Charlie", "Bob", "Alice"]

    def test_mode_accepts_string(self, simple_nodes):
        r = AgGridReturn(make_response(simple_nodes), "FILTERED_AND_SORTED")
        assert r.data_return_mode == DataReturnMode.FILTERED_AND_SORTED
        assert list(r.data["Name"]) == ["Charlie", "Bob", "Alice"]

    def test_group_nodes_are_excluded(self, grouped_nodes):
        r = AgGridReturn(make_response(grouped_nodes), DataReturnMode.AS_INPUT)
        assert len(r.data) == 2

    def test_auto_unique_id_becomes_index(self, simple_nodes):
        r = AgGridReturn(make_response(simple_nodes), DataReturnMode.AS_INPUT)
        assert "::auto_unique_id::" not in r.data.columns
        assert list(r.data.index) == ["0", "1", "2"]


class TestSelection:
    def test_selected_data(self, simple_nodes):
        r = AgGridReturn(make_response(simple_nodes), DataReturnMode.AS_INPUT)
        assert list(r.selected_data["Name"]) == ["Alice", "Charlie"]

    def test_selected_rows_is_alias(self, simple_nodes):
        r = AgGridReturn(make_response(simple_nodes), DataReturnMode.AS_INPUT)
        assert list(r.selected_rows["Name"]) == list(r.selected_data["Name"])

    def test_no_selection_returns_none(self, simple_nodes):
        nodes = [{**n, "isSelected": False} for n in simple_nodes]
        r = AgGridReturn(make_response(nodes), DataReturnMode.AS_INPUT)
        assert r.selected_data is None

    def test_selected_rows_id_from_grid_state(self, simple_nodes):
        r = AgGridReturn(
            make_response(simple_nodes, gridState={"rowSelection": ["0", "2"]})
        )
        assert r.selected_rows_id == ["0", "2"]


class TestGroups:
    def test_data_groups_keys(self, grouped_nodes):
        r = AgGridReturn(make_response(grouped_nodes), DataReturnMode.AS_INPUT)
        groups = r.dataGroups
        assert ("Swimming",) in groups
        assert ("Judo",) in groups
        assert list(groups[("Swimming",)]["athlete"]) == ["Phelps"]

    def test_data_groups_without_groups_falls_back(self, simple_nodes):
        r = AgGridReturn(make_response(simple_nodes), DataReturnMode.AS_INPUT)
        groups = r.dataGroups
        assert list(groups.keys()) == [()]
        assert len(groups[()]) == 3


class TestBasicProperties:
    def test_states_and_ids(self, simple_nodes):
        r = AgGridReturn(
            make_response(
                simple_nodes,
                gridState={"a": 1},
                columnsState=[{"colId": "Name"}],
                rowIdsAfterFilter=["0"],
                rowIdsAfterSortAndFilter=["2", "0"],
                eventData={"type": "selectionChanged"},
            )
        )
        assert r.grid_state == {"a": 1}
        assert r.columns_state == [{"colId": "Name"}]
        assert r.rows_id_after_filter == ["0"]
        assert r.rows_id_after_sort_and_filter == ["2", "0"]
        assert r.event_data == {"type": "selectionChanged"}


class TestMappingInterface:
    def test_is_collections_mapping(self):
        assert isinstance(AgGridReturn(), Mapping)

    def test_getitem_attribute(self, simple_nodes):
        r = AgGridReturn(make_response(simple_nodes), DataReturnMode.AS_INPUT)
        assert list(r["data"]["Name"]) == ["Alice", "Bob", "Charlie"]

    def test_getitem_grid_response_key(self, simple_nodes):
        r = AgGridReturn(make_response(simple_nodes))
        assert r["nodes"] == simple_nodes

    def test_getitem_missing_raises_key_error(self):
        with pytest.raises(KeyError, match="nope"):
            AgGridReturn()["nope"]

    def test_get_missing_returns_exact_default(self):
        sentinel = object()
        assert AgGridReturn().get("nope", sentinel) is sentinel

    def test_keys_iteration_len(self, simple_nodes):
        r = AgGridReturn(make_response(simple_nodes))
        keys = r.keys()
        assert "data" in keys and "selected_rows" in keys and "nodes" in keys
        assert len(list(iter(r))) == len(r) == len(keys)

    def test_values_matches_keys(self):
        r = AgGridReturn()
        assert len(r.values()) == len(r.keys())

    def test_mapping_mixins_expose_items_and_build_a_dict(self):
        r = AgGridReturn(grid_response={"grid_response": {"answer": 42}})

        materialized = dict(r)
        from_items = dict(r.items())
        assert tuple(from_items) == tuple(materialized)
        assert materialized["answer"] == 42
        assert from_items["answer"] == 42
        assert list(r)[: len(r._PUBLIC_KEYS)] == list(r._PUBLIC_KEYS)

    def test_mapping_equality_for_scalar_values(self):
        r = AgGridReturn(
            grid_response={"grid_response": {"answer": 42}},
            data_return_mode=DataReturnMode.CUSTOM,
        )

        expected = dict(r)
        assert r == expected
        assert expected == r

    def test_mapping_equality_handles_dataframe_values(self):
        original = pd.DataFrame({"value": [1, 2]})
        r = AgGridReturn(original_data=original)
        expected = dict(r)

        assert r == expected
        assert expected == r

        changed = dict(expected)
        changed["data"] = pd.DataFrame({"value": [1, 3]})
        assert r != changed
