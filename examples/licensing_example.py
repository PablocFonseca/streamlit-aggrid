import streamlit as st
import numpy as np
import pandas as pd

from st_aggrid import AgGrid, DataReturnMode, GridUpdateMode, GridOptionsBuilder

license_key = "For_Trialing_ag-Grid_Only-Not_For_Real_Development_Or_Production_Projects-Valid_Until-18_March_2021_[v2]_MTYxNjAyNTYwMDAwMA==948d8f51e73a17b9d78e03e12b9bf934"

@st.cache()
def get_data_ex3():
    df = pd.DataFrame(
        np.random.randint(0, 100, 100).reshape(-1, 5), columns=list("abcde")
    )
    return df

df = get_data_ex3()
st.subheader("Setting a license")
st.markdown("""
Ag-grid (not this component, which is free) has its own [licensing options](https://www.ag-grid.com/documentation/react/licensing/). If you do have an license,
you can load it though ```license_key``` parameter on grid call.  
""")
AgGrid(df, key='grid1', enable_enterprise_modules=True, license_key=license_key)

st.markdown("""On this example enterprise features are enabled (advanced column menus) and no watermak is displayed. 
However, it will only work until 2021-03-18 (When my trial license used on the code expires)""")