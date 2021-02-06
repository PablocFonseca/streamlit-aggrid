import streamlit as st
import numpy as np
import pandas as pd

from st_aggrid import AgGrid, DataReturnMode, GridUpdateMode, GridOptionsBuilder

st.set_page_config(layout='wide')

st.header("A Grid for many inputs")


c1, c2 = st.beta_columns(2)

with c1:
    st.text_input("FTE Cost:")

with c2:
    st.text_input("Consultant Cost:")

input_dataframe = pd.DataFrame(
    '',
    index=range(10),
    columns=[
        'Type',
        'current in min',
        'optimized in min',
        'amount per year',
        'saving in hours',
        'estimated effort for automation',
        'savings yearly'
    ]
)

response = AgGrid(
    input_dataframe, 
    editable=True,
    sortable=False,
    filter=False,
    resizable=False,
    defaultWidth=5,
    fit_columns_on_grid_load=True,
    key='input_frame')

st.header("Output data")

if 'data' in response:
    st.dataframe(response['data'])