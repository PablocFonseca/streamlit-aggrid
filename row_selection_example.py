import streamlit as st
import pandas as pd 
import numpy as np
import altair as alt

from st_aggrid import GridOptionsBuilder, AgGrid

np.random.seed(42)

@st.cache()
def fetch_data():   
    nrows = 50
    dummy_data = {
        "date":pd.date_range('2020-01-01', periods=nrows),
        "group": np.random.choice(['A','B'], size=nrows) ,
        "apple":np.random.randint(0,10,nrows),
        "banana":np.random.randint(0,10,nrows),
        "chocolate":np.random.randint(0,10,nrows)
    }
    return pd.DataFrame(dummy_data)

df = fetch_data()

#customize gridOptions
gb = GridOptionsBuilder(min_column_width=100, editable_columns=True, side_panel=False)
gb.build_columnsDefs_from_dataframe(df)
gridOptions = gb.build()


st.sidebar.subheader("Selection options")
selection_type = st.sidebar.radio("Selection Options", ['single','multiple'])

rowMultiSelectWithClick = st.sidebar.checkbox('rowMultiSelectWithClick')
suppressRowDeselection = st.sidebar.checkbox('suppressRowDeselection')
suppressRowClickSelection = st.sidebar.checkbox('suppressRowClickSelection')

checkbox_selection = st.sidebar.checkbox("checkbox selection")

headerCheckboxSelection = st.sidebar.checkbox("headerCheckboxSelection")

gridOptions['rowSelection'] = selection_type
gridOptions['rowMultiSelectWithClick'] = rowMultiSelectWithClick
gridOptions['suppressRowDeselection'] = suppressRowDeselection
gridOptions['suppressRowClickSelection'] = suppressRowClickSelection

if checkbox_selection:
    gridOptions['columnDefs'][0]['checkboxSelection'] = True

if headerCheckboxSelection:
    gridOptions['columnDefs'][0]['headerCheckboxSelection'] = True
    gridOptions['columnDefs'][0]['checkboxSelection'] = True

st.markdown("""
## Selection example
gridOptions selection documentation on [https://www.ag-grid.com/javascript-grid-selection/](https://www.ag-grid.com/javascript-grid-selection/)
""")

st.subheader("Dummy data")
grid_response = AgGrid(df, gridOptions=gridOptions)

df = grid_response['data']
st.dataframe(df)

st.subheader("Selected Rows")
selected_rows = grid_response.get('selected_rows', None)
if selected_rows:
    st.write(selected_rows)
else:
    st.write("No rows selected.")

st.subheader("Used gridOptions")
st.write(gridOptions)

