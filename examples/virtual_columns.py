import streamlit as st
import numpy as np
import pandas as pd

from st_aggrid import AgGrid, DataReturnMode, GridUpdateMode, GridOptionsBuilder

@st.cache()
def get_data_ex5():
    rows=10
    df = pd.DataFrame(
        np.random.randint(0, 100, 2*rows).reshape(-1, 2), columns= list("ab")
    )
    return df

reload_data = False

data = get_data_ex5()
gb = GridOptionsBuilder.from_dataframe(data)

#make all columns editable
gb.configure_columns(list('abcde'), editable=True)

#Create a calculated column that updates when data is edited. Use agAnimateShowChangeCellRenderer to show changes   
gb.configure_column('virtual column a + b', valueGetter='Number(data.a) + Number(data.b)', cellRenderer='agAnimateShowChangeCellRenderer', editable='false', type=['numericColumn'])
go = gb.build()
st.markdown("""
### Virtual columns
it's possible to configure calculated columns an below.
input data only has columns a and b. column c is calculated as:  
``` 
gb.configure_column(  
    "virtual column a + b",  
    valueGetter="Number(data.a) + Number(data.b)"  
    ) 
```  
a cellRenderer is also configured to display changes
""")
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