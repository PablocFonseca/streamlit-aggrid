import streamlit as st
import pandas as pd

from st_aggrid import AgGrid
from streamlit.components.v2.get_bidi_component_manager import get_bidi_component_manager


df = pd.DataFrame([[1,2,3], [4,5,6]], columns=list('abc'))


st.subheader("Header above the grid")
result = AgGrid(df, key="test_grid", show_toolbar=True)

st.subheader("Grid Return Value")
st.write(result.data)

