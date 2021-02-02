import streamlit as st
import numpy as np
import pandas as pd

from st_aggrid import AgGrid, DataReturnMode, GridUpdateMode, GridOptionsBuilder

@st.cache()
def get_data_ex6(rows=None):
    if not rows:
        rows = np.random.randint(1,10)
    df = pd.DataFrame(
        np.random.randint(0, 100, 5*rows).reshape(-1, 5), columns= list("abcde")
    )
    return df

st.sidebar.markdown("example controls:")
use_fixed_key = st.sidebar.checkbox("Use fixed key in AgGrid call", value=True)

button = st.sidebar.button("Generate random data")
use_10_rows = st.sidebar.checkbox("Fix data to 10 rows.", value=True)
if use_10_rows:
    rows = 10
else:
    rows = None


height = st.sidebar.slider('Height', min_value=100, max_value=800, value=400)
reload_data = False

if button:
    from streamlit import caching
    caching.clear_cache()
    reload_data=True

data = get_data_ex6(rows)
gb = GridOptionsBuilder.from_dataframe(data)
#make all columns editable
gb.configure_columns(list('abcde'), editable=True)

#Create a calculated column that updates when data is edited. Use agAnimateShowChangeCellRenderer to show changes   
#gb.configure_column('row total', valueGetter='Number(data.a) + Number(data.b) + Number(data.c) + Number(data.d) + Number(data.e)', cellRenderer='agAnimateShowChangeCellRenderer', editable='false', type=['numericColumn'])
go = gb.build()

st.subheader("Fixing key parameter")
st.markdown("""
Setting a fixed key for the component will prevent the grid to reinitialize when dataframe parameter change, simulated here 
by pressing the button on the side bar.  
Data will only be refreshed when the parameter reload_data is set to True
""")


if use_fixed_key:
    st.markdown(f"Grid was called as: <br>```AgGrid(..., reload_data={reload_data})``` <br>", unsafe_allow_html=True)
    ag = AgGrid(
        data, 
        gridOptions=go, 
        height=height, 
        fit_columns_on_grid_load=True, 
        key='an_unique_key',
        reload_data=reload_data
    )
else:
    st.markdown(f"Grid was called as: <br>```AgGrid(...)``` <br>", unsafe_allow_html=True)
    ag = AgGrid(
        data, 
        gridOptions=go, 
        height=height, 
        fit_columns_on_grid_load=True
    )

st.subheader("Returned Data")
st.dataframe(ag['data'])

st.subheader("Grid Options")
st.write(go)