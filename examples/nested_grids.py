import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, GridUpdateMode
import pandas as pd
import numpy as np
import requests


url = "https://www.ag-grid.com/example-assets/master-detail-data.json"
df = pd.read_json(url)
df["callRecords"] = df["callRecords"].apply(lambda x: pd.json_normalize(x))

gridOptions = {
    # enable Master / Detail
    "masterDetail": True,
    "rowSelection": "single",
    # the first Column is configured to use agGroupCellRenderer
    "columnDefs": [
        {
            "field": "name",
            "cellRenderer": "agGroupCellRenderer",
            "checkboxSelection": True,
        },
        {"field": "account"},
        {"field": "calls"},
        {"field": "minutes", "valueFormatter": "x.toLocaleString() + 'm'"},
    ],
    "defaultColDef": {
        "flex": 1,
    },
    # provide Detail Cell Renderer Params
    "detailCellRendererParams": {
        # provide the Grid Options to use on the Detail Grid
        "detailGridOptions": {
            "rowSelection": "multiple",
            "suppressRowClickSelection": True,
            "enableRangeSelection": True,
            "pagination": True,
            "paginationAutoPageSize": True,
            "columnDefs": [
                {"field": "callId", "checkboxSelection": True},
                {"field": "direction"},
                {"field": "number", "minWidth": 150},
                {"field": "duration", "valueFormatter": "x.toLocaleString() + 's'"},
                {"field": "switchCode", "minWidth": 150},
            ],
            "defaultColDef": {
                "sortable": True,
                "flex": 1,
            },
        },
        # get the rows for each Detail Grid
        "getDetailRowData": JsCode(
            """function (params) {
                console.log(params);
                params.successCallback(params.data.callRecords);
    }"""
        ).js_code,
    },
}


r = AgGrid(
    df,
    gridOptions=gridOptions,
    height=500,
    allow_unsafe_jscode=True,
    enable_enterprise_modules=True,
    update_mode=GridUpdateMode.SELECTION_CHANGED
)