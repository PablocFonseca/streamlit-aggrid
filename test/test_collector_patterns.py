"""
Test file demonstrating proper ways to access AgGrid response data
with both LegacyCollector and CustomCollector patterns
"""

import streamlit as st
import pandas as pd
from st_aggrid import AgGrid, JsCode

st.title("Collector Patterns Test")

# Create test data
df = pd.DataFrame({
    'id': range(5),
    'name': [f'User_{i}' for i in range(5)],
    'value': [10, 20, 30, 40, 50]
})

# Test 1: Legacy Collector (default behavior)
st.subheader("1. Legacy Collector (Default)")

grid_response_legacy = AgGrid(
    df,
    key="test_legacy",
    height=200
)

if grid_response_legacy is not None:
    st.write("**Response type:**", type(grid_response_legacy).__name__)
    
    # Proper way to access data with LegacyCollector
    st.write("**Available properties:**", list(grid_response_legacy.keys()))
    
    # Access nodes through grid_response property
    if hasattr(grid_response_legacy, 'grid_response') and 'nodes' in grid_response_legacy.grid_response:
        nodes = grid_response_legacy.grid_response['nodes']
        st.write(f"**Nodes count:** {len(nodes)}")
        st.write("**First node:**", nodes[0] if nodes else "No nodes")
    
    # Access data through the data property (recommended)
    if hasattr(grid_response_legacy, 'data') and grid_response_legacy.data is not None:
        st.write("**Data shape:**", grid_response_legacy.data.shape)
        st.dataframe(grid_response_legacy.data.head())

# Test 2: Custom Collector
st.subheader("2. Custom Collector")

custom_collector = JsCode("""
function collect_return({streamlitRerunEventTriggerName, eventData}){
    let api = eventData.api;
    if (api) {
        let colNames = api.getAllDisplayedColumns().map((c) => c.colDef.headerName);
        return {
            columns: colNames,
            rowCount: api.getDisplayedRowCount(),
            selectedCount: api.getSelectedRows().length
        };
    }
    return { error: 'No API available' };
}
""")

grid_response_custom = AgGrid(
    df,
    key="test_custom",
    height=200,
    collect_grid_return=custom_collector,
    update_on=['selectionChanged']
)

if grid_response_custom is not None:
    st.write("**Response type:**", type(grid_response_custom).__name__)
    
    # For custom collectors, access the raw_data property
    if hasattr(grid_response_custom, 'raw_data'):
        custom_data = grid_response_custom.raw_data
        st.write("**Custom collector data:**", custom_data)
    else:
        # Direct access for custom response
        st.write("**Custom collector response:**", grid_response_custom)

st.subheader("How to Handle Both Cases")

st.code('''
# Safe way to handle both collector types:

if isinstance(grid_response, AgGridReturn):
    # Legacy collector - use AgGridReturn methods
    data = grid_response.data
    nodes = grid_response.grid_response.get('nodes', [])
    
elif hasattr(grid_response, 'raw_data'):
    # Custom collector with CustomResponse wrapper
    custom_data = grid_response.raw_data
    
else:
    # Direct custom collector response
    custom_data = grid_response
''')