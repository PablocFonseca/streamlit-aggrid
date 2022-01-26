import streamlit as st
import numpy as np
import pandas as pd

from st_aggrid import AgGrid, DataReturnMode, GridUpdateMode, GridOptionsBuilder

@st.cache()
def get_data_ex5():
    rows=100
    df = pd.DataFrame(
        np.random.randint(0, 100, 2*rows).reshape(-1, 2), columns= list("ab")
    )
    return df

reload_data = False

data = get_data_ex5()
gb = GridOptionsBuilder.from_dataframe(data)

#make all columns editable
gb.configure_columns(list('abcde'), editable=False)

go = gb.build()
st.markdown("""
### Pinned Rows
Pin columns using either pinnedTopRowData or pinnedBottomRowData
``` 
gb = GridOptionsBuilder.from_dataframe(data)
go = gb.build()
go['pinnedTopRowData'] = [{'a':'100', 'b':'200'}]
go['pinnedBottomRowData'] = [{'a':'pinned', 'b':'down'}]

```  
""")
go['pinnedTopRowData'] = [{'a':'100', 'b':'200'}]
go['pinnedBottomRowData'] = [{'a':'pinned', 'b':'down'}]
ag = AgGrid(
    data, 
    gridOptions=go, 
    height=400, 
    fit_columns_on_grid_load=True, 
    key='an_unique_key_xZs151',
    reload_data=reload_data
)

st.subheader("Returned Data")
st.dataframe(ag['data'])

st.subheader("Grid Options")
st.write(go)