import logging
import typing
import warnings
from typing import Literal, Union

import pandas as pd
import streamlit as st
import streamlit.components.v2 as components

from streamlit_aggrid.AgGridReturn import AgGridReturn
from streamlit_aggrid.aggrid_utils import (
    _parse_data_and_grid_options,
    compute_data_hash,
    parse_update_mode,
)
from streamlit_aggrid.shared import (
    AgGridTheme,
    DataReturnMode,
    GridUpdateMode,
    JsCode,
    StAggridTheme,
)

# Track shown deprecation warnings to avoid repetition in Streamlit
_shown_deprecation_warnings = set()

# Registered lazily on the first AgGrid() call: registration validates the
# component manifest against Streamlit's runtime registry, which only exists
# inside a running Streamlit app. Importing this module from plain Python
# (e.g. unit tests) must not fail.
_component_funcs = {}


def _get_component_func(isolate_styles=True):
    if isolate_styles not in _component_funcs:
        _component_funcs[isolate_styles] = components.component(
            name="streamlit-aggrid.agGrid",
            js="index-*.mjs",
            css="index-*.css",
            isolate_styles=isolate_styles,
        )
    return _component_funcs[isolate_styles]


def AgGrid(
    data: Union[pd.DataFrame, str] = None,
    gridOptions: typing.Dict = None,
    height: int = 400,
    update_mode: GridUpdateMode
    | Literal[
        "MANUAL", "MODEL_CHANGED", "VALUE_CHANGED", "SELECTION_CHANGED", "GRID_CHANGED"
    ] = GridUpdateMode.NO_UPDATE,
    data_return_mode: str | DataReturnMode
    | Literal[
        "AS_INPUT", "FILTERED", "FILTERED_AND_SORTED", "MINIMAL", "CUSTOM"
    ] = DataReturnMode.FILTERED_AND_SORTED,
    allow_unsafe_jscode: bool = False,
    enable_enterprise_modules: bool
    | Literal["enterpriseOnly", "enterprise+AgCharts"] = False,
    license_key: str = None,
    columns_state=None,
    theme: str
    | StAggridTheme
    | Literal["streamlit", "light", "dark", "blue", "fresh", "material"] = "streamlit",
    custom_css=None,
    key: typing.Any = None,
    update_on=["cellValueChanged", "selectionChanged", "filterChanged", "sortChanged"],
    callback=None,
    show_toolbar: bool = True,
    show_search: bool = True,
    show_download_button: bool = True,
    custom_jscode_for_grid_return: JsCode = None,
    should_grid_return: JsCode = None,
    use_json_serialization: bool | Literal["auto"] = "auto",
    server_sync_strategy: Literal["client_wins", "server_wins"] = "client_wins",
    isolate_styles=True,
    **default_column_parameters,
) -> AgGridReturn:
    """Renders a DataFrame using AgGrid.

    Parameters
    ----------
    data : pd.DataFrame | pl.DataFrame | str | Path, optional
        The data to be displayed on the grid. Accepts:
            - Pandas or Polars DataFrames
            - Json string data in records format (list like [{column -> value}, … , {column -> value}])
            - Path to a json file with records

        Defaults to None.

    gridOptions : dict, optional
        Dictionary of AG Grid options. Full documentation at https://www.ag-grid.com/javascript-data-grid/grid-options/
        If None, default grid options will be infered with GridOptionsBuilder.from_dataframe().
        Defaults to None.

    key : Any, optional
        Streamlit widget key for maintaining state across reruns.
        It is highly recommended setting it for each grid.
        Defaults to None.

    height : int, optional
        Grid height in pixels. If None, Auto Height is enabled.
        See: https://www.ag-grid.com/react-data-grid/grid-size/#dom-layout
        Defaults to 400.

    update_mode : GridUpdateMode, optional
        DEPRECATED. Use update_on parameter instead.
        Defines how the grid sends results back to Streamlit.
        Defaults to GridUpdateMode.NO_UPDATE.

    data_return_mode : str | DataReturnMode, optional
        Defines how the data property of the grid return behaves:
            - 'AS_INPUT': data in the same order as supplied
            - 'FILTERED': respects the grid filters
            - 'FILTERED_AND_SORTED': respects the grid filters and sorting
            - 'CUSTOM': the grid return is built by custom_jscode_for_grid_return
        Defaults to DataReturnMode.FILTERED_AND_SORTED.

    allow_unsafe_jscode : bool, optional
        Allows JavaScript code injection in gridOptions. Required when using JsCode.
        Defaults to False.

    enable_enterprise_modules : bool | Literal['enterpriseOnly', 'enterprise+AgCharts'], optional
        Enables AG Grid Enterprise features (requires license):
            - True or 'enterpriseOnly': Enterprise modules only
            - 'enterprise+AgCharts': Enterprise + AgCharts modules
            - False: Community features only
        Defaults to False.

    license_key : str, optional
        License key for AG Grid Enterprise features.
        Defaults to None.

    columns_state : dict, optional
        Initial column state (visibility, order, width, etc.).
        Format follows https://www.ag-grid.com/javascript-data-grid/column-state/#reference-state-applyColumnState
        Defaults to None.

    theme : str | StAggridTheme, optional
        Grid theme:
            - 'streamlit': Matches Streamlit's default styling
            - 'light': AG Grid balham-light theme
            - 'dark': AG Grid balham-dark theme
            - 'blue': AG Grid blue theme
            - 'fresh': AG Grid fresh theme
            - 'material': AG Grid material theme
        Defaults to 'streamlit'.

    custom_css : dict, optional
        DEPRECATED. Not needed in Components V2.
        Use st.markdown() and isolate_styles=False to inject CSS instead.
        See streamlit_aggrid.styles for ready-made helpers.
        Defaults to None.

    update_on : list[str | tuple[str, int]], optional
        AG Grid events that trigger data return to Streamlit.
        Events: https://www.ag-grid.com/javascript-data-grid/grid-events/
        Use tuple (event_name, debounce_ms) for debounced events.

        Example: ['cellValueChanged', ('columnResized', 500)]
        Defaults to ['cellValueChanged', 'selectionChanged', 'filterChanged', 'sortChanged'].

    callback : callable, optional
        Function called when the grid returns data to Streamlit. Receives the
        AgGridReturn object as its single argument.
        Requires key parameter to be set.
        Defaults to None.

    show_toolbar : bool, optional
        Show toolbar above the grid.
        Defaults to True.

    show_search : bool, optional
        Show search bar in toolbar.
        Defaults to True.

    show_download_button : bool, optional
        Show CSV download button in toolbar.
        Defaults to True.

    custom_jscode_for_grid_return : JsCode, optional
        JavaScript function for custom data collection. When set, data_return_mode
        becomes DataReturnMode.CUSTOM and the function's return value is available
        in AgGridReturn.grid_response.
        Receives: {streamlitRerunEventTriggerName, eventData}

        Example:
            JsCode('''
            function({streamlitRerunEventTriggerName, eventData}) {
                let api = eventData.api;
                return {
                    columnNames: api.getAllDisplayedColumns().map(c => c.colDef.headerName),
                    rowCount: api.getDisplayedRowCount(),
                    selectedCount: api.getSelectedRows().length
                };
            }
            ''')

        Defaults to None.

    should_grid_return : JsCode, optional
        JavaScript function that determines whether the grid should return data to Streamlit.
        This function is called before each potential data return and can be used to
        conditionally prevent updates based on grid state or event data.
        The function receives: {streamlitRerunEventTriggerName, eventData}
        Should return: boolean (true to proceed with data return, false to skip)

        Example:
        should_return = JsCode('''
        function should_return({streamlitRerunEventTriggerName, eventData}){
                //returns only if column Move has finished
                if (streamlitRerunEventTriggerName == 'columnMoved'){
                    return eventData.finished;
                }
            return true;
            }
        ''')

        Defaults to None.

    use_json_serialization : bool | Literal['auto'], optional
        Controls JSON serialization behavior for complex data types:

        - 'auto' (default): Automatically detect PyArrow conversion errors and fallback
          to JSON serialization. User-friendly option that handles complex data seamlessly.
        - True: Always use JSON serialization for non-primitive data types (lists, dicts, sets).
          Converts complex objects to JSON strings before rendering.
        - False: Never use JSON serialization. Will raise PyArrow conversion errors
          for non-hashable or mixed-type data.

        Use 'auto' for best user experience, True for consistent JSON behavior,
        or False for strict type checking.
        Defaults to 'auto'.

    server_sync_strategy : Literal['client_wins', 'server_wins'], optional
        Controls data synchronization behavior between server and client:

        - 'client_wins' (default): After first edit, grid ignores server data updates
          and maintains local edits. Standard behavior for interactive editing.
        - 'server_wins': Server data always overwrites the grid, including edited cells.
          Useful when server data should be the single source of truth.

        When using 'server_wins', consider intercepting grid results with session_state
        to preserve user edits before re-rendering.
        Defaults to 'client_wins'.

    isolate_styles : bool, optional
        Whether to sandbox the component styles in a shadow root.
        Set to False to allow CSS injected with st.markdown() to style the grid.
        Defaults to True.

    **default_column_parameters
        Additional parameters passed to gridOptions.defaultColDef.

    Returns
    -------
    AgGridReturn
        Object with the grid response. Main properties:
            - .data: grid data (with edits applied), shaped by data_return_mode
            - .selected_data: selected rows (alias: .selected_rows)
            - .dataGroups / .selected_dataGroups: grouped data as {group_key_tuple: DataFrame}
            - .grid_state: grid state (for use with gridOptions initialState)
            - .columns_state: column configuration state
            - .event_data: event that triggered the response
            - .grid_response: raw response from the component (with
              data_return_mode=CUSTOM, holds the custom JsCode return value)
    """

    # Parse theme
    if isinstance(theme, StAggridTheme):
        themeObj = theme
    elif isinstance(theme, (str, AgGridTheme)) or theme is None:
        themeObj = StAggridTheme(None)
        if isinstance(theme, AgGridTheme):
            themeObj["themeName"] = theme.value
        else:
            themeObj["themeName"] = theme or "streamlit"
    else:
        raise ValueError(
            f"{theme} is not valid. Available options: {AgGridTheme.__members__}"
        )

    # Parse data return mode
    if isinstance(data_return_mode, str):
        try:
            data_return_mode = DataReturnMode(data_return_mode.upper())
        except ValueError:
            raise ValueError(f"{data_return_mode} is not a valid DataReturnMode.")
    elif not isinstance(data_return_mode, DataReturnMode):
        raise ValueError(
            "data_return_mode should be either a valid DataReturnMode enum value or string"
        )

    # Parse update mode (deprecated)
    if not isinstance(update_mode, (str, GridUpdateMode)):
        raise ValueError(
            "GridUpdateMode should be either a valid GridUpdateMode enum value or string"
        )
    elif isinstance(update_mode, str):
        try:
            update_mode = GridUpdateMode[update_mode.upper()]
        except Exception:
            raise ValueError(f"{update_mode} is not valid.")

    if update_mode != GridUpdateMode.NO_UPDATE:
        warning_key = "GridUpdateMode_deprecated"
        if warning_key not in _shown_deprecation_warnings:
            warnings.warn(
                "GridUpdateMode is deprecated and will be removed in a future version. "
                "Use the 'update_on' parameter instead to specify which events should trigger updates.",
                DeprecationWarning,
                stacklevel=2,
            )
            _shown_deprecation_warnings.add(warning_key)

    update_on = list(update_on)
    manual_update = update_mode == GridUpdateMode.MANUAL
    if not manual_update:
        update_on.extend(parse_update_mode(update_mode))

    # Process JsCode for the CUSTOM return mode
    if custom_jscode_for_grid_return is not None:
        custom_jscode_for_grid_return_str = custom_jscode_for_grid_return.js_code
        allow_unsafe_jscode = True
        data_return_mode = DataReturnMode.CUSTOM
    else:
        custom_jscode_for_grid_return_str = None
        if data_return_mode == DataReturnMode.CUSTOM:
            raise ValueError(
                "data_return_mode=CUSTOM requires custom_jscode_for_grid_return to be set."
            )

    if should_grid_return is not None:
        should_grid_return_str = should_grid_return.js_code
        allow_unsafe_jscode = True
    else:
        should_grid_return_str = None

    # Pop options that travel outside defaultColDef before building grid options
    pro_assets = default_column_parameters.pop("pro_assets", None)
    debug = default_column_parameters.pop("debug", False)
    fit_columns_on_grid_load = default_column_parameters.pop(
        "fit_columns_on_grid_load", False
    )

    # Parse data and gridOptions
    data, gridOptions = _parse_data_and_grid_options(
        data,
        gridOptions,
        default_column_parameters,
        allow_unsafe_jscode,
        use_json_serialization,
    )

    # Deprecate custom_css parameter (not needed in Components V2)
    if custom_css is not None:
        warnings.warn(
            "The 'custom_css' parameter is deprecated in Components V2. "
            "Use st.markdown() and isolate_styles=False to inject CSS instead. "
            "See streamlit_aggrid.styles module for helper functions like get_hide_expanders_css().",
            DeprecationWarning,
            stacklevel=2,
        )
    custom_css = custom_css or dict()

    if height is None:
        gridOptions["domLayout"] = "autoHeight"

    if fit_columns_on_grid_load:
        warnings.warn(
            "fit_columns_on_grid_load is deprecated. Use gridOptions autoSizeStrategy instead.",
            DeprecationWarning,
        )
        gridOptions["autoSizeStrategy"] = {"type": "fitGridWidth"}

    # Wire the user callback through the Components V2 state-change callback
    if callback is not None and key is None:
        raise ValueError("Component key must be set to use a callback.")

    if callback is not None:

        def _on_grid_response_change():
            callback(
                AgGridReturn(
                    grid_response=st.session_state.get(key),
                    data_return_mode=data_return_mode,
                )
            )
    else:

        def _on_grid_response_change():
            return None

    # streamlit >= 1.59 silently coerces Arrow-incompatible frames instead of
    # raising, corrupting the whole component payload. Detect it up front and
    # send the data as JSON rowData when use_json_serialization is "auto".
    if use_json_serialization == "auto" and isinstance(data, pd.DataFrame):
        try:
            import pyarrow as pa

            pa.Table.from_pandas(data)
        except Exception:
            gridOptions["rowData"] = data.to_json(orient="records")
            data = None
            use_json_serialization = True

    # Prepare data payload for the component.
    # In Components V2, 'key' is a direct parameter, not part of data.
    _component_data = dict(
        data=data,
        data_hash=compute_data_hash(data),
        gridOptions=gridOptions,
        height=height,
        allow_unsafe_jscode=allow_unsafe_jscode,
        columns_state=columns_state,
        custom_css=custom_css,
        data_return_mode=data_return_mode.value,
        enable_enterprise_modules=enable_enterprise_modules,
        license_key=license_key,
        manual_update=manual_update,
        pro_assets=pro_assets,
        show_download_button=show_download_button,
        show_search=show_search,
        show_toolbar=show_toolbar,
        custom_jscode_for_grid_return=custom_jscode_for_grid_return_str,
        should_grid_return=should_grid_return_str,
        theme=themeObj,
        debug=debug,
        update_on=update_on,
        use_json_serialization=use_json_serialization,
        server_sync_strategy=server_sync_strategy,
    )

    def _call_component():
        return _get_component_func(isolate_styles)(
            key=key,
            data=_component_data,
            on_grid_response_change=_on_grid_response_change,
            default=dict(grid_response={}),
        )

    try:
        component_result = _call_component()
    except Exception as ex:
        error_msg = str(ex)
        is_pyarrow_error = (
            "Could not convert" in error_msg
            or "pyarrow" in error_msg.lower()
            or "ArrowInvalid" in error_msg
            or "Conversion failed" in error_msg
        )

        if is_pyarrow_error and data is not None and use_json_serialization == "auto":
            logging.warning(
                "PyArrow conversion failed, automatically retrying with JSON "
                f"serialization: {error_msg}"
            )
            # Retry once, sending data as a JSON string inside gridOptions.rowData
            # (same shape produced by use_json_serialization=True).
            gridOptions["rowData"] = data.to_json(orient="records")
            _component_data.update(
                data=None, gridOptions=gridOptions, use_json_serialization=True
            )
            component_result = _call_component()
        elif is_pyarrow_error and data is not None:
            # User explicitly disabled JSON serialization, raise the PyArrow error
            raise
        else:
            if ex.args and isinstance(ex.args[0], str):
                args = list(ex.args)
                args[0] += (
                    ". If you're using custom JsCode objects on gridOptions, "
                    "ensure that allow_unsafe_jscode is True."
                )
                raise type(ex)(*args) from ex
            raise

    return AgGridReturn(
        grid_response=component_result, data_return_mode=data_return_mode
    )
