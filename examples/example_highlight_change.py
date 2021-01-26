import streamlit as st
import numpy as np
import pandas as pd

from st_aggrid import AgGrid, DataReturnMode, GridUpdateMode, GridOptionsBuilder, JsCode

@st.cache()
def get_data():
    df = pd.DataFrame(
        np.random.randint(0, 100, 100).reshape(-1, 5), columns=list("abcde")
    )
    return df

data = get_data()

gb = GridOptionsBuilder.from_dataframe(data)
#make all columns editable
gb.configure_columns(list('abcde'), editable=True)


js = JsCode("""
function(e) {
    let api = e.api;
    let rowIndex = e.rowIndex;
    let col = e.column.colId;
    
    let rowNode = api.getDisplayedRowAtIndex(rowIndex);
    api.flashCells({
      rowNodes: [rowNode],
      columns: [col],
      flashDelay: 10000000000
    });

};
""")

#just found a bug. JsCode at root of gridOption is not converted..
#call .js_code as a workaround. Will be fixed on next version
gb.configure_grid_options(onCellValueChanged=js.js_code) 
go = gb.build()

AgGrid(data, gridOptions=go,  key='grid1', allow_unsafe_jscode=True)