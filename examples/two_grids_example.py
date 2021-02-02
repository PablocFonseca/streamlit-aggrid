import streamlit as st
import numpy as np
import pandas as pd

from st_aggrid import AgGrid, DataReturnMode, GridUpdateMode, GridOptionsBuilder

@st.cache()
def get_data_ex4():
    df = pd.DataFrame(
        np.random.randint(0, 100, 50).reshape(-1, 5), columns=list("abcde")
    )
    return df

df = get_data_ex4()
st.markdown("""
### Two grids 
As in other streamlit components, it is possible to render two components for the same data using distinct ```key``` parameters.
""")

st.subheader("Input data")
st.dataframe(df)

st.subheader("Editable Grids")
c1, c2 = st.beta_columns(2)
with c1:
    grid_return1 = AgGrid(df, key='grid1', editable=True)
    st.text("Grid 1 Return")
    st.write(grid_return1['data'])

with c2:
    grid_return2 = AgGrid(df,  key='grid2', editable=True)
    st.text("Grid 2 Return")
    st.write(grid_return2['data'])