import streamlit as st
import numpy as np
import pandas as pd

from st_aggrid import AgGrid, DataReturnMode, GridUpdateMode, GridOptionsBuilder

data_file = './json_data.json'
gridOptions_file = './json_data_gridOptions.json'

AgGrid(data_file, gridOptions=gridOptions_file, try_to_convert_back_to_original_types=False)