import streamlit as st
import numpy as np
import pandas as pd

from st_aggrid import AgGrid, DataReturnMode, GridUpdateMode, GridOptionsBuilder, JsCode, grid_options_builder


@st.cache()
def get_data(multiindex=False):
    df = pd.DataFrame(
        np.random.randint(0, 100, 100).reshape(-1, 5),
        columns=list("abcde"),
        index = pd.MultiIndex.from_product([list("xyzw"), list("12345")]) if multiindex else None
    )
    return df

multiindex = st.sidebar.checkbox("Create a Multindexed DataFrame", False)

data = get_data(multiindex)
#converts the multi index to a . separated string :)
if multiindex:
    data.index = [".".join(t) for t in data.index]
data = data.reset_index()


gb = GridOptionsBuilder.from_dataframe(data, minWidth=150)
gb.configure_first_column_as_index()

go = gb.build()
AgGrid(data, go, enable_enterprise_modules=True, fit_columns_on_grid_load=False)