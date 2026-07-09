import streamlit as st 
from st_aggrid import AgGrid
import pandas as pd


df = pd.DataFrame({
    'Name': ['Alice', 'Bob', 'Charlie', 'Diana'],
    'Age': [25, 30, 35, 28],
    'City': ['New York', 'London', 'Paris', 'Tokyo'],
    'Salary': [50000, 60000, 70000, 55000]
})

st.write(st.session_state)

text = AgGrid(df, key='grid-1', editable=True)


x = st.components.v2.component(
    html="""<input type="text"> </input>""",
    name='custom_tbox'
)


x()
st.button('rerun')