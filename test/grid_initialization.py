import streamlit as st
from st_aggrid import AgGrid
import pandas as pd
import json

"""grid launches from dataframe"""
test_data = pd.DataFrame({"names": ["alice", "bob"], "ages": [25, 30]})
AgGrid(test_data, key="grid_from_dataframe")


"""grid launches with json data and grid options"""
data = json.dumps([{"name": "alice", "age": 25}, {"name": "bob", "age": 30}])
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
