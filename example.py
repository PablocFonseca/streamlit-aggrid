import streamlit as st
import pandas as pd 
import numpy as np

from st_aggrid import GridOptionsBuilder, AgGrid

#fecth some random data from internet 
@st.cache()
def fetch_data():   
    df = pd.read_csv('https://raw.githubusercontent.com/fivethirtyeight/data/master/airline-safety/airline-safety.csv')

    #add a column with random dates just for testing
    df.insert(1,'date', pd.to_datetime(np.random.rand(df.shape[0])*1e18))

    return df
df = fetch_data()

#customize gridOptions
gb = GridOptionsBuilder(min_column_width=100, editable_columns=True)
gb.build_columnsDefs_from_dataframe(df)
gb.enableSideBar()
gridOptions = gb.build()

returned_df = AgGrid(df, gridOptions=gridOptions)
st.write(returned_df)