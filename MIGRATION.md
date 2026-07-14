# Migrating to streamlit-aggrid 2.0

Version 2.0 migrates the component to **Streamlit Components V2** (requires
`streamlit >= 1.59`) and currently supports `pandas >= 1.4,<3`. Most apps will
keep working unchanged — `from st_aggrid import AgGrid` and the v1-style return object
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

### Styling and `custom_css`
`custom_css` remains supported as a compatibility API. Its selector rules are
installed with the grid, including when Components V2 style isolation is on:

```python
AgGrid(
    df,
    custom_css={
        ".ag-header-cell-label": {"font-weight": "700"},
    },
    key="grid",
)
```

For new global CSS, render a stylesheet in the app and opt out of the component
shadow root explicitly:

```python
from st_aggrid import AgGrid
from streamlit_aggrid.styles import get_zebra_stripes_css

st.markdown(get_zebra_stripes_css(), unsafe_allow_html=True)
AgGrid(df, isolate_styles=False, key="grid")
```

`streamlit_aggrid.styles` ships helpers: `get_hide_expanders_css()`,
`get_compact_grid_css()`, `get_zebra_stripes_css()`.

AG Grid now automatically inherits the app font selected by Streamlit's
`[theme] font` setting, including fonts registered with `[[theme.fontFaces]]`.
The component references Streamlit's Components V2 `--st-font` CSS variable,
so theme changes cascade without JavaScript style reads or per-cell work. An
explicit `fontFamily` in a custom AG Grid theme still takes precedence.

### Deprecated parameters
| Deprecated | Use instead |
|---|---|
| `update_mode=GridUpdateMode.*` | `update_on=["cellValueChanged", ...]` |
| `fit_columns_on_grid_load=True` | `gridOptions["autoSizeStrategy"] = {"type": "fitGridWidth"}` |
| `try_to_convert_back_to_original_types` | removed — convert dtypes yourself |
| `conversion_errors` | removed — convert dtypes yourself |

When legacy `update_mode=GridUpdateMode.MANUAL` is retained temporarily, omit
`update_on` to disable automatic reruns and use only the manual update button.
An explicitly supplied `update_on` remains active. Other deprecated update
modes now contribute only their matching events when `update_on` is omitted;
the four modern default events apply to a normal call with neither option set.

### Custom return mode
`data_return_mode=DataReturnMode.CUSTOM` with `custom_jscode_for_grid_return`
runs your JsCode on the frontend and puts its return value in
`response.grid_response` (the old `CustomResponse` wrapper no longer exists).
Setting `custom_jscode_for_grid_return` automatically selects CUSTOM mode.

The custom value is exposed directly; do not expect an additional `data` or
`value` wrapper:

```python
response = AgGrid(
    df,
    key="grid",
    custom_jscode_for_grid_return=JsCode(
        "function({eventData}) { return {rowCount: eventData.api.getDisplayedRowCount()}; }"
    ),
)
st.write(response.grid_response["rowCount"])
```

For compatibility with the 1.x `CustomResponse` wrapper,
`response.raw_data` aliases the same custom payload.

### Minimal return mode
`DataReturnMode.MINIMAL` no longer walks or serializes the grid row model. Its
response contains only a compact `eventData` mapping: the triggering event
name, primitive event fields, the affected row's data and small node/column
identifiers when available.

```python
response = AgGrid(
    df,
    key="grid",
    data_return_mode=DataReturnMode.MINIMAL,
    update_on=["cellValueChanged"],
)
st.write(response.event_data)
```

MINIMAL intentionally does not populate `response.data` or include `nodes`,
grid state, column state, filters, or the complete dataset. Use one of the
legacy data return modes when the Python rerun needs a DataFrame snapshot.

### Callbacks
`callback=` receives the `AgGridReturn` object and requires `key=` to be set:

```python
def on_change(response):
    st.session_state["last_selection"] = response.selected_rows

AgGrid(df, key="grid", callback=on_change)
```

The callback is invoked after the `grid_response` state value changes. It gets
the same `AgGridReturn` shape as the value returned by `AgGrid`; callback users
should therefore read custom payloads from `response.grid_response` too.

### Toolbar default
The toolbar remains off by default for compatibility with 1.x. Enable it with
`show_toolbar=True`; `show_search` and `show_download_button` only affect the
toolbar when it is enabled.

### Row-level server synchronization
For large client-side datasets where the server remains authoritative but only
a small number of rows change per rerun, `server_wins_rows` avoids refreshing
unchanged rows in AG Grid:

```python
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

builder = GridOptionsBuilder.from_dataframe(df)
builder.configure_grid_options(
    getRowId=JsCode("params => String(params.data.id)")
)
options = builder.build()

response = AgGrid(
    df,
    gridOptions=options,
    key="grid",
    allow_unsafe_jscode=True,
    server_sync_strategy="server_wins_rows",
)
```

This mode requires the default client-side row model and an explicit `getRowId`
that returns a stable, unique string for every logical row. The positional IDs
that streamlit-aggrid creates automatically are deliberately rejected: they do
not remain attached to the same row after an insert, removal, or reorder.

The optimization preserves browser objects for structurally unchanged rows and
then lets AG Grid's immutable row-data path reconcile additions, updates,
removals, and order. It still sends the complete dataset to the browser and
performs an O(n) comparison, so it reduces AG Grid refresh/render work rather
than Streamlit transport size. Continue using `server_wins` for non-client-side
row models or when row-level reconciliation is unnecessary.

### Outer iframes and reverse proxies
Components V2 removes the component's own nested iframe and its legacy
`postMessage` bridge. An iframe around the complete Streamlit app is still a
normal deployment boundary: the browser must be able to load the whole
Streamlit base path, open its `/_stcore/stream` WebSocket, and fetch component
assets under `/_stcore/bidi-components/`. Preserve WebSocket upgrade headers,
the configured `server.baseUrlPath`, and session affinity when a proxy or load
balancer is involved.

Streamlit 1.59 uses its Starlette/Uvicorn server directly; the earlier
experimental `server.useStarlette` switch is no longer a valid 1.59 config
option. Components V2 can remove an AgGrid-specific iframe communication layer,
but it cannot repair a blocked outer Streamlit WebSocket or an incorrectly
routed proxy path.

## Packaging notes

- The implementation package is `streamlit_aggrid`; `st_aggrid` remains as a
  compatibility alias (both `from st_aggrid import ...` and
  `from streamlit_aggrid import ...` work, including submodules).
- `python-decouple` is no longer a dependency.
- Release wheels and source distributions contain both import packages, the
  component manifest, and its built `.mjs` and `.css` assets. Maintainers should
  run the artifact contract described in the README before publishing; testing
  only the source checkout does not validate those files.
