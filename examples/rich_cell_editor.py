import streamlit as st
import pandas as pd
import numpy as np

from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

df = pd.DataFrame(
    "",
    index=range(10),
    columns=list("abcde"),
)

gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_default_column(editable=True)

gb.configure_column('a',
    cellEditor='agRichSelectCellEditor',
    cellEditorParams={'values':['a','b','c']}
)

gb.configure_grid_options(enableRangeSelection=True)


response = AgGrid(
    df,
    gridOptions=gb.build(),
    fit_columns_on_grid_load=True,
    allow_unsafe_jscode=True,
    enable_enterprise_modules=True
)