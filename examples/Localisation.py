import streamlit as st
import numpy as np
import pandas as pd

from st_aggrid import AgGrid, GridOptionsBuilder

@st.cache_data()
def get_data():
    df = pd.DataFrame(
        np.random.randint(0, 100, 50).reshape(-1, 5), columns= list("abcde")
    ).applymap(str)
    return df


data = get_data()

gb = GridOptionsBuilder.from_dataframe(data)
gb.configure_side_bar()

go = gb.build()

#locale is a dictionary reference here: https://www.ag-grid.com/examples/localisation/localisation/locale.en.js
go['localeText'] = {'selectAll' : 'Tout séléctionner'}

ag = AgGrid(
    data, 
    gridOptions=go, 
    height=600, 
    key='an_unique_key'
)
