# This line enables conditional row formatting in AgGrid.
# ✅ What you can achieve:
# - Visually highlight rows based on specific column values (e.g., status)
# - Improve user experience by making important records (like INPROGRESS tasks) stand out
# - Quickly identify different states like 'FAILED', 'INPROGRESS', 'COMPLETED', etc., using colors
# - Great for dashboards or status monitoring tools


from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import pandas as pd

# Sample DataFrame
df = pd.DataFrame({
    "ID": [1, 2, 3],
    "STATUS": ["COMPLETED", "INPROGRESS", "FAILED"]
})

# Create the JS function using JsCode
row_style_code = JsCode("""
function(params) {
    if (params.data.STATUS === 'INPROGRESS') {
        return { backgroundColor: 'orange' };
    }
    return {};
}
""")

# Build grid options
gb = GridOptionsBuilder.from_dataframe(df)
gb.configure_grid_options(getRowStyle=row_style_code)
gridOptions = gb.build()

# Render AgGrid
AgGrid(df, gridOptions=gridOptions, allow_unsafe_jscode=True)