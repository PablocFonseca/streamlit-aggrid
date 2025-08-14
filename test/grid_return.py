import json
from st_aggrid import AgGrid
import streamlit as st
import pandas as pd


"""grid launches with json data and grid options"""

data = json.dumps([
    {"name": "alice", "age": 25},
    {"name": "bob", "age": 30},
    {"name": "charlie", "age": 35},
    {"name": "diana", "age": 28},
    {"name": "eve", "age": 32},
    {"name": "frank", "age": 27},
    {"name": "grace", "age": 29},
    {"name": "henry", "age": 33},
    {"name": "iris", "age": 26},
    {"name": "jack", "age": 31}
])

go = {
    "columnDefs": [
        {
            "headerName": "First Name",
            "field": "name",
            "editable": True,
            "type": [],
        },
        {
            "headerName": "ages",
            "field": "age",
            "type": ["numericColumn", "numberColumnFilter"],
        },
    ],
    "autoSizeStrategy": {"type": "fitCellContents", "skipHeader": False},
    "rowSelection": {"mode": "singleRow"},
}
r = AgGrid(data, go, key="event_return_grid")

with st.expander("Raw Response"):
    st.write(r.grid_response)

st.code(r.event_data)
st.code(r.data)
st.code(r.selected_data)
