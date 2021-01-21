import streamlit as st
import numpy as np
import pandas as pd

from st_aggrid import AgGrid, DataReturnMode, GridUpdateMode, GridOptionsBuilder

@st.cache()
def get_data():
    df = pd.DataFrame(
        np.random.randint(0, 100, 100).reshape(-1, 5), columns=list("abcde")
    )
    return df

df = get_data()
AgGrid(df, key='grid1')
AgGrid(df,  key='grid2')