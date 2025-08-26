import streamlit as st
from st_aggrid import AgGrid, JsCode
import pandas as pd
import json

TESTS = [14]  # list(range(20))

if 1 in TESTS:
    """grid renders lists"""
    test_data = pd.DataFrame(
        {"names": ["alice", "bob"], "ages": [25, 30], "list": [[1, 2, 3], [4, 5, 6]]}
    )
    AgGrid(test_data, key="grid_from_dataframe")

if 10 in TESTS:
    """Test unhashable types - lists"""
    unhashable_lists = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "simple_list": [[1, 2, 3], [4, 5, 6], [7, 8, 9]],
            "nested_list": [[[1, 2], [3, 4]], [[5, 6], [7, 8]], [[9, 10], [11, 12]]],
            "mixed_list": [[1, "a", True], [2, "b", False], [3, "c", None]],
        }
    )
    AgGrid(
        unhashable_lists, key="test_unhashable_lists", use_json_serialization="auto"
    )  # Should automatically fallback

if 11 in TESTS:
    """Test unhashable types - sets"""
    unhashable_sets = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "simple_set": [{1, 2, 3}, {4, 5, 6}, {7, 8, 9}],
            "string_set": [{"a", "b", "c"}, {"d", "e", "f"}, {"g", "h", "i"}],
            "mixed_set": [{1, "a"}, {2, "b"}, {3, "c"}],
        }
    )
    AgGrid(unhashable_sets, key="test_unhashable_sets", use_json_serialization=True)

if 12 in TESTS:
    """Test unhashable types - dictionaries"""
    unhashable_dicts = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "simple_dict": [{"x": 1, "y": 2}, {"x": 3, "y": 4}, {"x": 5, "y": 6}],
            "nested_dict": [
                {"user": {"name": "Alice", "age": 25}},
                {"user": {"name": "Bob", "age": 30}},
                {"user": {"name": "Charlie", "age": 35}},
            ],
            "mixed_dict": [
                {"nums": [1, 2], "text": "hello"},
                {"nums": [3, 4], "text": "world"},
                {"nums": [5, 6], "text": "test"},
            ],
        }
    )
    AgGrid(unhashable_dicts, key="test_unhashable_dicts", use_json_serialization=True)

if 13 in TESTS:
    """Test complex nested unhashable structures"""
    complex_unhashable = pd.DataFrame(
        {
            "id": [1, 2],
            "complex_nested": [
                {
                    "lists": [[1, 2], [3, 4]],
                    "sets": [{1, 2}, {3, 4}],
                    "dict": {"inner": {"deep": [5, 6, 7]}},
                },
                {
                    "lists": [[8, 9], [10, 11]],
                    "sets": [{8, 9}, {10, 11}],
                    "dict": {"inner": {"deep": [12, 13, 14]}},
                },
            ],
        }
    )
    AgGrid(
        complex_unhashable, key="test_complex_unhashable", use_json_serialization=True
    )

if 14 in TESTS:
    """Test mixed hashable and unhashable columns"""
    mixed_data = pd.DataFrame(
        {
            "hashable_int": [1, 2, 3],
            "hashable_str": ["a", "b", "c"],
            "unhashable_list": [[1, 2], [3, 4], [5, 6]],
            "hashable_float": [1.1, 2.2, 3.3],
            "unhashable_dict": [{"key": "val1"}, {"key": "val2"}, {"key": "val3"}],
        }
    )

    # Create a JS formatter for unhashable dict column
    dict_formatter = JsCode("""
    function(params) {
        if (params.value && typeof params.value === 'object') {
            return JSON.stringify(params.value);
        }
        return params.value;
    }
    """)

    dict_formatter = (
        "(value && typeof value === 'object') ? JSON.stringify(value) : value"
    )

    gridOptions = {
        "columnDefs": [
            {"field": "hashable_int", "headerName": "Int"},
            {"field": "hashable_str", "headerName": "String"},
            {"field": "unhashable_list", "headerName": "List"},
            {"field": "hashable_float", "headerName": "Float"},
            {
                "field": "unhashable_dict",
                "headerName": "Dict",
                "valueFormatter": dict_formatter,
            },
        ],
        "autoSizeStrategy": {"type": "fitGridWidth"},
    }
    AgGrid(
        mixed_data,
        gridOptions=gridOptions,
        key="test_mixed_data",
        use_json_serialization=True,
    )

if 15 in TESTS:
    """Test empty unhashable structures"""
    empty_unhashable = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "empty_list": [[], [], []],
            "empty_set": [set(), set(), set()],
            "empty_dict": [{}, {}, {}],
        }
    )
    AgGrid(empty_unhashable, key="test_empty_unhashable", use_json_serialization=True)
