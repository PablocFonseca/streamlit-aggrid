import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, DataReturnMode
import pandas as pd

st.set_page_config(page_title="AG Grid Drag and Drop Example")

data = [
    {"id": "1", "v": 1},
    {"id": "2", "v": 2},
    {"id": "3", "v": 3},
    {"id": "4", "v": 4},
]

df = pd.DataFrame(data)

gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_columns("v", rowDrag=True)
gb.configure_grid_options(rowDragManaged=True, getRowId=JsCode("params => params.data.id"))

grid_options = gb.build()

st.markdown('<div class="st-key-drag_grid"></div>', unsafe_allow_html=True)
r = AgGrid(
    df,  # <-- Pass the DataFrame here
    gridOptions=grid_options,
    enable_enterprise_modules=False,
    height=300,
    fit_columns_on_grid_load=True,
    key="drag_grid", 
    allow_unsafe_jscode=True,
    data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
    update_on=['dragStopped']
)
r.data