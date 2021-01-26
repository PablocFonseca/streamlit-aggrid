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


use_fixed_key = st.sidebar.checkbox("Use fixed key in AgGrid call")
st.sidebar.markdown("""
Setting a fixed key for the component will prevent the grid to reinitialize.
The data will be updated when: <br> ```AgGrid(..., reload_data=True)```
""", unsafe_allow_html=True)
button = st.sidebar.button("Generate random data")
height = st.sidebar.slider('Height', min_value=100, max_value=800, value=400)
reload_data = False

if button:
    from streamlit import caching
    caching.clear_cache()
    reload_data=True

data = get_data()
gb = GridOptionsBuilder.from_dataframe(data)
#make all columns editable
gb.configure_columns(list('abcde'), editable=True)

#Create a calculated column that updates when data is edited. Use agAnimateShowChangeCellRenderer to show changes   
gb.configure_column('row total', valueGetter='Number(data.a) + Number(data.b) + Number(data.c) + Number(data.d) + Number(data.e)', cellRenderer='agAnimateShowChangeCellRenderer', editable='false', type=['numericColumn'])
go = gb.build()

if use_fixed_key:
    ag = AgGrid(
        data, 
        gridOptions=go, 
        height=height, 
        fit_columns_on_grid_load=True, 
        key='an_unique_key',
        reload_data=reload_data
    )
else:
    ag = AgGrid(
        data, 
        gridOptions=go, 
        height=height, 
        fit_columns_on_grid_load=True
    )

st.subheader("Returned Data")
st.dataframe(ag['data'])

st.write(go)