import streamlit as st
import pandas as pd 
import numpy as np
import altair as alt

from st_aggrid import GridOptionsBuilder, AgGrid

np.random.seed(42)

@st.cache()
def fetch_data():   
    dummy_data = {
        "date":pd.date_range('2020-01-01', periods=5),
        "apple":np.random.randint(0,10,5),
        "banana":np.random.randint(0,10,5),
        "chocolate":np.random.randint(0,10,5)
    }
    return pd.DataFrame(dummy_data)

df = fetch_data()

#customize gridOptions
gb = GridOptionsBuilder(min_column_width=100, editable_columns=True)
gb.build_columnsDefs_from_dataframe(df)
gb.enableSideBar()
gridOptions = gb.build()

grid_response = AgGrid(df, gridOptions=gridOptions)
df = grid_response['data']

chart_data = pd.melt(df, id_vars='date', var_name="item", value_name="quantity")
chart = alt.Chart(data=chart_data).mark_bar().encode(
    x="item:O",
    y="sum(quantity):Q"
)
st.altair_chart(chart, use_container_width=True)

st.subheader("gridOptions")
st.write(gridOptions)