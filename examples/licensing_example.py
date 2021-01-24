import streamlit as st
import numpy as np
import pandas as pd

from st_aggrid import AgGrid, DataReturnMode, GridUpdateMode, GridOptionsBuilder

license_key = "For_Trialing_ag-Grid_Only-Not_For_Real_Development_Or_Production_Projects-Valid_Until-18_March_2021_[v2]_MTYxNjAyNTYwMDAwMA==948d8f51e73a17b9d78e03e12b9bf934"

@st.cache()
def get_data():
    df = pd.DataFrame(
        np.random.randint(0, 100, 100).reshape(-1, 5), columns=list("abcde")
    )
    return df

df = get_data()
AgGrid(df, key='grid1', enable_enterprise_modules=True, license_key=license_key)