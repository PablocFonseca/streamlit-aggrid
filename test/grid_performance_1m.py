import streamlit as st
import pandas as pd
import numpy as np
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import time

st.set_page_config(page_title="Grid Performance Test - 1M Records", layout="wide")

st.title("AG Grid Performance Test - 1 Million Records")


# Generate 1 million datapoints
@st.cache_data
def generate_large_dataset():
    """Generate a dataset with 1 million rows for performance testing."""
    np.random.seed(42)  # For reproducible results

    n_rows = (1_000_000  // 100_000) * 2

    data = {
        "id": range(n_rows),
        "name": [f"User_{i}" for i in range(n_rows)],
        "age": np.random.randint(18, 80, n_rows),
        "score": np.random.uniform(0, 100, n_rows),
        "category": np.random.choice(["A", "B", "C", "D"], n_rows),
        "date": pd.date_range("2020-01-01", periods=n_rows, freq="1min"),
        "value": np.random.normal(50, 15, n_rows),
        "active": np.random.choice([True, False], n_rows),
        "department": np.random.choice(
            ["Sales", "Marketing", "Engineering", "HR", "Finance"], n_rows
        ),
        "salary": np.random.randint(30000, 120000, n_rows),
    }

    return pd.DataFrame(data)

# Add timing information to the page
st.info(
    "This test will measure the time taken for grid initialization and return operations with 1 million records."
)

# Generate the dataset
with st.spinner("Generating 1 million records..."):
    df = generate_large_dataset()

st.success(f"Generated {len(df):,} records")
st.write(len(str(df)))

grid_options = {
    "columnDefs": [
        {
            "headerName": "id",
            "field": "id",
            "filter": True,
            
        },
        {"headerName": "name", "field": "name"},
        {
            "headerName": "age",
            "field": "age",
            
        },
        {
            "headerName": "score",
            "field": "score",
            
        },
        {"headerName": "category", "field": "category", "rowGroup": True},
        {
            "headerName": "date",
            "field": "date",
            
        },
        {
            "headerName": "value",
            "field": "value",
            
        },
        {"headerName": "active", "field": "active", "type": ["textColumn"]},
        {"headerName": "department", "field": "department",         "rowGroup": True},
        {
            "headerName": "salary",
             "field": "salary",
            
        },
    ],
    "autoSizeStrategy": {"type": "fitCellContents", "skipHeader": False},
    "defaultColDef": {"resizable": True, "sortable": True},
    "getRowId": JsCode("(params) =>  params.data.id.toString()")
}

# Add JavaScript to measure grid ready time
grid_ready_js = """
function(params) {
    window.gridReadyTime = Date.now();
    console.log('Grid ready at:', window.gridReadyTime);
}
"""

grid_options["onGridReady"] = JsCode(grid_ready_js)

# Display the grid with timing
st.subheader("Performance Grid Test")

# Record start time
start_time = time.time()
# Create the grid

#This function returns only if onColumnMoved has finished
should_return = JsCode("""
function should_return({streamlitRerunEventTriggerName, eventData}){
        return eventData && eventData.hasOwnProperty('finished') ? eventData.finished : false;
    }
""")

#This functions cotomizes the grid return. In this example we're getting columns order
collect_return = JsCode("""
function collect_return({streamlitRerunEventTriggerName, eventData}){
        let api = eventData.api;
        let colNames = api.getAllDisplayedColumns().map((c) => c.colDef.headerName);
        return colNames   
    }
""")

grid_response = AgGrid(
    df,
    gridOptions=grid_options,
    fit_columns_on_grid_load=True,
    theme="alpine",
    key="performance_grid_1m",
    update_mode="MODEL_CHANGED",
    update_on=['columnMoved'],
    allow_unsafe_jscode=True,
    enable_enterprise_modules=True,
    should_grid_return=should_return,
    #collect_grid_return=collect_return,
)

# Record end time
end_time = time.time()

# Display timing results
st.subheader("Performance Metrics")
col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Grid Creation Time", f"{end_time - start_time:.2f}s")

with col2:
    st.metric("Total Records", f"{len(df):,}")

with col3:
    st.metric("Records per Second", f"{len(df) / (end_time - start_time):,.0f}")

# Display grid return information
if grid_response is not None:
    st.subheader("Grid Return Information")
    
    # Use the proper AgGridReturn interface
    st.write("Grid response data:")
    st.dataframe(grid_response.data)
    # st.write(f"Selected rows: {len(grid_response.get('selected_rows', []))}")
    # st.write(f"Data shape: {grid_response.get('data', df).shape}")

    # Show first few rows of returned data
    if not grid_response.get("data", df).empty:
        st.write("First 5 rows of returned data:")
        st.dataframe(grid_response["data"].head())

# Page Refresh Timing Tracker
st.divider()
st.subheader("Page Refresh Performance")

# Initialize session state for tracking page refreshes
if "page_load_times" not in st.session_state:
    st.session_state.page_load_times = []
if "last_refresh_time" not in st.session_state:
    st.session_state.last_refresh_time = time.time()

# Calculate time since last refresh
current_time = time.time()
time_since_last_refresh = current_time - st.session_state.last_refresh_time

# Only record if this is actually a refresh (more than 1 second difference)
if time_since_last_refresh > 1:
    st.session_state.page_load_times.append(time_since_last_refresh)
    st.session_state.last_refresh_time = current_time

    # Keep only the last 10 refresh times
    if len(st.session_state.page_load_times) > 10:
        st.session_state.page_load_times = st.session_state.page_load_times[-10:]

# Display refresh timing information
col1, col2, col3, col4 = st.columns(4)

with col1:
    if st.session_state.page_load_times:
        avg_refresh_time = sum(st.session_state.page_load_times) / len(
            st.session_state.page_load_times
        )
        st.metric("Avg Refresh Time", f"{avg_refresh_time:.2f}s")
    else:
        st.metric("Avg Refresh Time", "N/A")

with col2:
    if st.session_state.page_load_times:
        last_refresh_time = st.session_state.page_load_times[-1]
        st.metric("Last Refresh Time", f"{last_refresh_time:.2f}s")
    else:
        st.metric("Last Refresh Time", "N/A")

with col3:
    st.metric("Total Refreshes", len(st.session_state.page_load_times))

with col4:
    if st.session_state.page_load_times:
        max_refresh_time = max(st.session_state.page_load_times)
        st.metric("Max Refresh Time", f"{max_refresh_time:.2f}s")
    else:
        st.metric("Max Refresh Time", "N/A")

# Show refresh history
if st.session_state.page_load_times:
    st.write("**Recent Refresh Times (seconds):**")
    refresh_history = [
        f"{t:.2f}s" for t in st.session_state.page_load_times[-5:]
    ]  # Show last 5
    st.write(" → ".join(refresh_history))

# Add a manual refresh button for testing
if st.button(
    "🔄 Manual Refresh Test",
    help="Click to manually trigger a page refresh for testing",
):
    st.rerun()

# JavaScript to track actual page load time
page_load_js = """
<script>
// Track when the page starts loading
window.pageStartTime = window.pageStartTime || Date.now();

// Track when everything is loaded
window.addEventListener('load', function() {
    window.pageLoadTime = Date.now() - window.pageStartTime;
    console.log('Page load time:', window.pageLoadTime + 'ms');
});

// Track when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    window.domReadyTime = Date.now() - window.pageStartTime;
    console.log('DOM ready time:', window.domReadyTime + 'ms');
});
</script>
"""

st.components.v1.html(page_load_js, height=0)
