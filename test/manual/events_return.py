import json
from st_aggrid import AgGrid, JsCode
import streamlit as st
import pandas as pd


"""grid launches with json data and grid options"""

data = json.dumps([{"name": "alice", "age": 25}, {"name": "bob", "age": 30}])
# data = pd.DataFrame([{"name": "alice", "age": 25}, {"name": "bob", "age": 30}])

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
    "onCellClicked": JsCode("function(){console.log('onCellClicked!')}"),
    # "onGridReady": JsCode("function(){console.log('onGridReady!')}"),
}
r = AgGrid(data, go, key="event_return_grid", allow_unsafe_jscode=True)

st.json(r.event_data)
