import streamlit as st
from st_aggrid import AgGrid, JsCode
import pandas as pd
import json

TESTS = list(range(10))

if 1 in TESTS:
    """grid launches from dataframe"""
    test_data = pd.DataFrame({"names": ["alice", "bob"], "ages": [25, 30]})
    AgGrid(test_data, key="grid_from_dataframe")

if 2 in TESTS:
    """grid launches with json data and grid options"""
    data = json.dumps([{"name": "alice", "age": 25}, {"name": "bob", "age": 30}, {"name": "charlie", "age": 32}])
    go = {
        "columnDefs": [
            {
                "headerName": "First Name",
                "field": "name",
                "type": [],
            },
            {
                "headerName": "ages",
                "field": "age",
                "type": ["numericColumn", "numberColumnFilter"],
            },
        ],
        "autoSizeStrategy": {"type": "fitCellContents", "skipHeader": False},
    }
    AgGrid(data, go, key="grid_from_json")

if 3 in TESTS:
    """Grid Launches an Empty Grid when no data is passed, but grid options are."""
    go = {
        "columnDefs": [
            {
                "headerName": "names",
                "field": "name",
                "type": [],
            },
            {
                "headerName": "ages",
                "field": "age",
                "type": ["numericColumn", "numberColumnFilter"],
            },
        ],
        "autoSizeStrategy": {"type": "fitCellContents", "skipHeader": False},
    }
    AgGrid(None, go, key="gridOptions_only")

if 4 in TESTS:
    """Empty grid is displayed when nothing is set"""
    go = {
        "columnDefs": [
            {
                "headerName": "names",
                "field": "name",
                "type": [],
            },
            {
                "headerName": "ages",
                "field": "age",
                "type": ["numericColumn", "numberColumnFilter"],
            },
        ],
        "autoSizeStrategy": {"type": "fitCellContents", "skipHeader": False},
    }
    AgGrid(None, {}, key="empty_grid")

if 5 in TESTS:
    """Grid loads data from .json file"""
    import pathlib
    data_file = str(pathlib.Path(__file__).parent.joinpath("olympic-winners.json").absolute())
    AgGrid(data_file, key="grid_loads_data_json_from_file")

if 6 in TESTS:
    """Grid loads grid_options from .json file"""
    import pathlib
    data_file = str(pathlib.Path(__file__).parent.joinpath("olympic-winners.json").absolute())
    go_file = str(pathlib.Path(__file__).parent.joinpath("test-gridOptions.json").absolute())
    AgGrid(data_file, gridOptions=go_file, key="grid_loads_data_and_go_json_from_file")