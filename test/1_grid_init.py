import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import pandas as pd
import json


# test1: Grid launches on community mode.
def test_1():
    test_data = pd.DataFrame({"names": ["alice", "bob"], "ages": [25, 30]})
    AgGrid(test_data)

    go = GridOptionsBuilder.from_dataframe(test_data)
    st.write(go.build())


# test_1()


def test_2():
    """grid launches with json data and grid options"""
    data = json.dumps([{"name": "alice", "age": 25}, {"name": "bob", "age": 30}])
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
    AgGrid(data, go)


# test_2()


def test_3():
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
    AgGrid(None, go)


test_3()


def test_4():
    """Empty grid is displayed when nothing is sent"""
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
    AgGrid(None, {})


test_4()
