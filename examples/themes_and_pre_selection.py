import streamlit as st
import pandas as pd
import numpy as np

from st_aggrid import AgGrid, GridOptionsBuilder

df = pd.DataFrame(
    np.random.randint(0, 100, 50).reshape(-1, 5),
    index=range(10),
    columns=list("abcde"),
)

available_themes = ["streamlit", "light", "dark", "blue", "fresh", "material"]
selected_theme = st.selectbox("Theme", available_themes)

gb = GridOptionsBuilder.from_dataframe(df)
if st.checkbox('Pre-select rows 4 and 6 when loading.'):
    gb.configure_selection('multiple', pre_selected_rows=[3,5])

response = AgGrid(
    df,
    editable=True,
    gridOptions=gb.build(),
    data_return_mode="filtered_and_sorted",
    update_mode="no_update",
    fit_columns_on_grid_load=True,
    theme=selected_theme
)
