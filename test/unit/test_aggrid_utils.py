"""Unit tests for aggrid_utils data/gridOptions parsing helpers."""

import json

import pandas as pd
import pytest

from streamlit_aggrid.aggrid_utils import (
    _parse_data_and_grid_options,
    compute_data_hash,
    parse_update_mode,
)
from streamlit_aggrid.shared import GridUpdateMode, JsCode


RECORDS = [{"a": 1, "b": "x"}, {"a": 2, "b": "y"}]


def parse(data=None, grid_options=None, default_column_parameters=None,
          allow_unsafe_jscode=False, use_json_serialization="auto"):
    return _parse_data_and_grid_options(
        data, grid_options, default_column_parameters or {},
        allow_unsafe_jscode, use_json_serialization,
    )


class TestDataInputs:
    def test_dataframe_builds_grid_options_and_auto_id(self):
        data, go = parse(pd.DataFrame(RECORDS))
        assert "::auto_unique_id::" in data.columns
        assert [c["field"] for c in go["columnDefs"]] == ["a", "b"]

    def test_json_string_input(self):
        data, go = parse(json.dumps(RECORDS))
        assert list(data["a"]) == [1, 2]
        assert "columnDefs" in go

    def test_json_file_as_string_path(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text(json.dumps(RECORDS))
        data, _ = parse(str(f))
        assert list(data["b"]) == ["x", "y"]

    def test_json_file_as_path_object(self, tmp_path):
        f = tmp_path / "data.json"
        f.write_text(json.dumps(RECORDS))
        data, _ = parse(f)
        assert len(data) == 2

    def test_invalid_json_file_path_raises(self, tmp_path):
        with pytest.raises(ValueError):
            parse(tmp_path / "missing.json")

    def test_invalid_json_string_raises(self):
        with pytest.raises(ValueError):
            parse("not json at all")

    def test_datetime_columns_converted_to_iso(self):
        df = pd.DataFrame({"d": pd.to_datetime(["2024-01-02"])})
        data, _ = parse(df)
        assert data["d"].iloc[0] == "2024-01-02T00:00:00"

    def test_parsing_does_not_mutate_the_callers_dataframe(self):
        source = pd.DataFrame({"d": pd.to_datetime(["2024-01-02"])})

        data, _ = parse(source)

        assert "::auto_unique_id::" in data.columns
        assert "::auto_unique_id::" not in source.columns
        assert source["d"].dtype.kind == "M"
        assert data["d"].iloc[0] == "2024-01-02T00:00:00"

    def test_get_row_id_suppresses_auto_id(self):
        data, _ = parse(
            pd.DataFrame(RECORDS), grid_options={"getRowId": "x", "columnDefs": []}
        )
        assert "::auto_unique_id::" not in data.columns


class TestGridOptionsInputs:
    def test_dict_grid_options_passthrough(self):
        go_in = {"columnDefs": [{"field": "a"}]}
        data, go = parse(None, go_in)
        assert data is None
        assert go["columnDefs"] == [{"field": "a"}]

    def test_grid_options_as_json_string(self):
        _, go = parse(None, json.dumps({"columnDefs": [{"field": "a"}]}))
        assert go["columnDefs"][0]["field"] == "a"

    def test_grid_options_as_json_file(self, tmp_path):
        f = tmp_path / "go.json"
        f.write_text(json.dumps({"columnDefs": [{"field": "z"}]}))
        _, go = parse(None, str(f))
        assert go["columnDefs"][0]["field"] == "z"

    def test_no_data_and_no_grid_options(self):
        data, go = parse(None, None)
        assert data is None
        assert go == {}

    def test_parsing_does_not_mutate_the_callers_grid_options(self):
        code = JsCode("params => ({ color: 'red' })")
        options = {
            "columnDefs": [{"field": "a"}],
            "getRowStyle": code,
            "rowData": RECORDS,
        }

        _, parsed = parse(None, options, allow_unsafe_jscode=True)

        assert options["rowData"] == RECORDS
        assert options["getRowStyle"] is code
        assert "rowData" not in parsed
        assert parsed["getRowStyle"] == code.js_code


class TestRowDataInGridOptions:
    def test_row_data_as_json_string_moved_to_data(self):
        _, go_in = None, {"columnDefs": [], "rowData": json.dumps(RECORDS)}
        data, go = parse(None, go_in)
        assert list(data["a"]) == [1, 2]
        assert "rowData" not in go

    def test_row_data_as_list_moved_to_data(self):
        data, go = parse(None, {"columnDefs": [], "rowData": RECORDS})
        assert list(data["a"]) == [1, 2]
        assert "rowData" not in go

    def test_data_and_row_data_both_supplied_raises(self):
        with pytest.raises(ValueError, match="both"):
            parse(pd.DataFrame(RECORDS), {"columnDefs": [], "rowData": RECORDS})

    def test_empty_row_data_is_still_a_data_source(self):
        with pytest.raises(ValueError, match="both"):
            parse(pd.DataFrame(RECORDS), {"columnDefs": [], "rowData": []})

    def test_row_data_list_is_normalized_in_json_mode(self):
        data, go = parse(
            None,
            {"columnDefs": [], "rowData": RECORDS},
            use_json_serialization=True,
        )
        assert list(data["a"]) == [1, 2]
        assert "rowData" not in go


class TestJsonSerialization:
    def test_parser_keeps_data_until_initial_return_snapshot_is_captured(self):
        data, go = parse(pd.DataFrame(RECORDS), use_json_serialization=True)
        assert list(data["a"]) == [1, 2]
        assert "rowData" not in go

    def test_true_without_data_does_not_crash(self):
        data, go = parse(None, {"columnDefs": []}, use_json_serialization=True)
        assert data is None


class TestJsCodeProcessing:
    def test_jscode_serialized_when_allowed(self):
        code = JsCode("function(p) { return 1; }")
        _, go = parse(
            pd.DataFrame(RECORDS),
            {"columnDefs": [], "getRowStyle": code},
            allow_unsafe_jscode=True,
        )
        assert go["getRowStyle"] == code.js_code

    def test_jscode_untouched_when_not_allowed(self):
        code = JsCode("function(p) { return 1; }")
        _, go = parse(
            pd.DataFrame(RECORDS),
            {"columnDefs": [], "getRowStyle": code},
            allow_unsafe_jscode=False,
        )
        assert go["getRowStyle"] is code


class TestComputeDataHash:
    def test_none(self):
        assert compute_data_hash(None) is None

    def test_stable_for_same_data(self):
        df = pd.DataFrame(RECORDS)
        assert compute_data_hash(df) == compute_data_hash(df.copy())
        assert len(compute_data_hash(df)) == 64

    def test_changes_with_data(self):
        a = compute_data_hash(pd.DataFrame(RECORDS))
        b = compute_data_hash(pd.DataFrame([{"a": 99}]))
        assert a != b

    def test_row_order_changes_hash(self):
        forward = pd.DataFrame([{"a": 1}, {"a": 2}])
        reversed_rows = pd.DataFrame([{"a": 2}, {"a": 1}])
        assert compute_data_hash(forward) != compute_data_hash(reversed_rows)

    def test_column_schema_changes_hash(self):
        original = pd.DataFrame({"a": [1], "b": [2]})
        renamed = original.rename(columns={"a": "x"})
        reordered = original[["b", "a"]]
        assert compute_data_hash(original) != compute_data_hash(renamed)
        assert compute_data_hash(original) != compute_data_hash(reordered)

    def test_non_hashable_columns(self):
        df = pd.DataFrame({"a": [[1, 2], [3]], "b": [{"k": 1}, {"k": 2}]})
        assert compute_data_hash(df) == compute_data_hash(df.copy())

    def test_non_hashable_mapping_order_is_canonical(self):
        first = pd.DataFrame({"value": [{"a": 1, "b": [2, 3]}]})
        second = pd.DataFrame({"value": [{"b": [2, 3], "a": 1}]})
        assert compute_data_hash(first) == compute_data_hash(second)

    def test_dataframe_index_is_not_part_of_browser_row_hash(self):
        first = pd.DataFrame(RECORDS, index=["first", "second"])
        second = pd.DataFrame(RECORDS, index=[10, 20])
        assert compute_data_hash(first) == compute_data_hash(second)

    def test_json_is_canonical_but_row_order_sensitive(self):
        compact = json.dumps(RECORDS, separators=(",", ":"))
        formatted = json.dumps(RECORDS, indent=2)
        reversed_rows = json.dumps(list(reversed(RECORDS)))

        assert compute_data_hash(compact) == compute_data_hash(formatted)
        assert compute_data_hash(compact) != compute_data_hash(reversed_rows)


class TestParseUpdateMode:
    def test_value_changed(self):
        assert parse_update_mode(GridUpdateMode.VALUE_CHANGED) == ["cellValueChanged"]

    def test_model_changed_expands(self):
        events = parse_update_mode(GridUpdateMode.MODEL_CHANGED)
        assert set(events) == {
            "cellValueChanged",
            "selectionChanged",
            "filterChanged",
            "sortChanged",
        }

    def test_column_changed_includes_debounced_events(self):
        events = parse_update_mode(GridUpdateMode.COLUMN_CHANGED)
        assert ("columnResized", 300) in events
        assert ("columnMoved", 500) in events

    def test_no_update_adds_nothing(self):
        assert parse_update_mode(GridUpdateMode.NO_UPDATE) == []
