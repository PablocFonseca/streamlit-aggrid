# Migrating to streamlit-aggrid 2.0

Version 2.0 migrates the component to **Streamlit Components V2** (requires
`streamlit >= 1.51`) and slims down the codebase. Most apps will keep working
unchanged — `from st_aggrid import AgGrid` and the v1-style return object
(`.data`, `.selected_rows`, `data_return_mode`) are preserved.

## What stays the same

```python
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, DataReturnMode

response = AgGrid(df, data_return_mode=DataReturnMode.FILTERED_AND_SORTED, key="grid")
response.data           # DataFrame with edits/filter/sort applied
response.selected_rows  # selected rows (alias of response.selected_data)
response.dataGroups     # grouped data as {group_key_tuple: DataFrame}
response.grid_state     # for gridOptions initialState
response.columns_state
```

## Behavior changes

### Automatic dtype conversion was removed
The grid no longer converts returned columns back to the original DataFrame
dtypes, and the `conversion_errors` parameter is gone. Edited data comes back
as plain objects; convert types yourself when you need them:

```python
data = response.data
data["my_int"] = pd.to_numeric(data["my_int"], errors="coerce").astype("Int64")
```

### JSON input now returns DataFrames
In 1.x, passing a JSON string to `AgGrid(data=...)` made the return also a JSON
string. In 2.0 the return is always a `pandas.DataFrame` (or `None` when the
grid is empty). Use `response.data.to_json(orient="records")` if you need JSON
back.

### `custom_css` is deprecated
Components V2 can render without an iframe, so CSS can be injected directly:

```python
from st_aggrid import AgGrid
from streamlit_aggrid.styles import get_zebra_stripes_css

st.markdown(get_zebra_stripes_css(), unsafe_allow_html=True)
AgGrid(df, isolate_styles=False, key="grid")
```

`streamlit_aggrid.styles` ships helpers: `get_hide_expanders_css()`,
`get_compact_grid_css()`, `get_zebra_stripes_css()`.

### Deprecated parameters
| Deprecated | Use instead |
|---|---|
| `update_mode=GridUpdateMode.*` | `update_on=["cellValueChanged", ...]` |
| `fit_columns_on_grid_load=True` | `gridOptions["autoSizeStrategy"] = {"type": "fitGridWidth"}` |
| `custom_css={...}` | `st.markdown(css)` + `isolate_styles=False` |
| `try_to_convert_back_to_original_types` | removed — convert dtypes yourself |
| `conversion_errors` | removed — convert dtypes yourself |

### Custom return mode
`data_return_mode=DataReturnMode.CUSTOM` with `custom_jscode_for_grid_return`
runs your JsCode on the frontend and puts its return value in
`response.grid_response` (the old `CustomResponse` wrapper no longer exists).
Setting `custom_jscode_for_grid_return` automatically selects CUSTOM mode.

### Callbacks
`callback=` receives the `AgGridReturn` object and requires `key=` to be set:

```python
def on_change(response):
    st.session_state["last_selection"] = response.selected_rows

AgGrid(df, key="grid", callback=on_change)
```

## Packaging notes

- The implementation package is `streamlit_aggrid`; `st_aggrid` remains as a
  compatibility alias (both `from st_aggrid import ...` and
  `from streamlit_aggrid import ...` work, including submodules).
- `python-decouple` is no longer a dependency.
