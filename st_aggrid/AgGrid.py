import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import warnings
import os
import typing
import logging
from decouple import config
from typing import Union, Literal

try:
    import pyarrow.lib
except ImportError:
    pyarrow = None
from st_aggrid.shared import (
    GridUpdateMode,
    DataReturnMode,
    JsCode,
    StAggridTheme,
    AgGridTheme,
)
from st_aggrid.aggrid_utils import (
    parse_update_mode,
    _parse_data_and_grid_options,
)
from st_aggrid.AgGridReturn import AgGridReturn
from io import StringIO

# Track shown deprecation warnings to avoid repetition in Streamlit
_shown_deprecation_warnings = set()

_RELEASE = config("AGGRID_RELEASE", default=True, cast=bool)

if not _RELEASE:
    warnings.warn("WARNING: ST_AGGRID is in development mode.")
    _component_func = components.declare_component(
        "agGrid",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend", "build")
    _component_func = components.declare_component("agGrid", path=build_dir)


def AgGrid(
    data: Union[pd.DataFrame, str] = None,
    gridOptions: typing.Dict = None,
    height: int = 400,
    update_mode: GridUpdateMode
    | Literal[
        "MANUAL", "MODEL_CHANGED", "VALUE_CHANGED", "SELECTION_CHANGED", "GRID_CHANGED"
    ] = GridUpdateMode.NO_UPDATE,
    data_return_mode: DataReturnMode
    | Literal[
        "AS_INPUT", "FILTERED", "FILTERED_AND_SORTED", "MINIMAL", "CUSTOM"
    ] = DataReturnMode.FILTERED_AND_SORTED,
    allow_unsafe_jscode: bool = False,
    enable_enterprise_modules: bool
    | Literal["enterpriseOnly", "enterprise+AgCharts"] = False,
    license_key: str = None,
    conversion_errors: str = "coerce",
    columns_state=None,
    theme: str
    | StAggridTheme
    | Literal["streamlit", "light", "dark", "blue", "fresh", "material"] = "streamlit",
    custom_css=None,
    key: typing.Any = None,
    update_on=["cellValueChanged", "selectionChanged", "filterChanged", "sortChanged"],
    callback=None,
    show_toolbar: bool = False,
    show_search: bool = True,
    show_download_button: bool = True,
    custom_jscode_for_grid_return: JsCode = None,
    should_grid_return: JsCode = None,
    use_json_serialization: bool | Literal["auto"] = "auto",
    server_sync_strategy: Literal["client_wins", "server_wins"] = "client_wins",
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

    data_return_mode : DataReturnMode, optional
        How data is retrieved from the grid:
            - AS_INPUT: Returns data as originally provided, includes edits
            - FILTERED: Returns filtered data in original order
            - FILTERED_AND_SORTED: Returns filtered and sorted data
            - CUSTOM: Returns CustomResponse with user-defined data structure (requires custom_jscode_for_grid_return set)
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

    conversion_errors : str, optional
        How to handle type conversion errors:
            - 'raise': Raises exception on conversion failure
            - 'coerce': Sets invalid values to NaT/NaN
            - 'ignore': Returns input unchanged on failure
        Defaults to 'coerce'.

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
        Custom CSS rules injected into the component iframe.
        Defaults to None.

    update_on : list[str | tuple[str, int]], optional
        AG Grid events that trigger data return to Streamlit.
        Events: https://www.ag-grid.com/javascript-data-grid/grid-events/
        Use tuple (event_name, debounce_ms) for debounced events.

        Example: ['cellValueChanged', ('columnResized', 500)]
        Defaults to ['cellValueChanged', 'selectionChanged', 'filterChanged', 'sortChanged'].

    callback : callable, optional
        Function called when grid data changes. Receives AgGridReturn object.
        Requires key parameter to be set.
        Defaults to None.

    show_toolbar : bool, optional
        Show toolbar above the grid.
        Defaults to False.

    show_search : bool, optional
        Show search bar in toolbar.
        Defaults to True.

    show_download_button : bool, optional
        Show CSV download button in toolbar.
        Defaults to True.

    custom_jscode_for_grid_return : JsCode, optional
        JavaScript function for custom data collection when using DataReturnMode.CUSTOM.
        Receives: {streamlitRerunEventTriggerName, eventData}
        Required when data_return_mode is DataReturnMode.CUSTOM.

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

    **default_column_parameters
        Additional parameters passed to gridOptions.defaultColDef.

    Returns
    -------
    AgGridReturn | CustomResponse
        The return type depends on the data_return_mode:

        - AS_INPUT, FILTERED, FILTERED_AND_SORTED: Returns AgGridReturn object with full grid data
        - MINIMAL: Returns MinimalResponse object with lightweight access to raw data
        - CUSTOM: Returns CustomResponse object with user-defined data structure

        AgGridReturn provides properties like:
            - .data: DataFrame with grid data
            - .selected_data: DataFrame with selected rows
            - .grid_state: Grid state information
            - .columns_state: Column configuration state

        CustomResponse provides safe access methods:
            - .raw_data: Access to the raw returned data
            - .get(key, default): Safe key access with default value
            - Standard dictionary access with helpful error messages
    """

    ###Deprecation Warnings
    # Check for deprecated reload_data parameter
    if "reload_data" in default_column_parameters:
        default_column_parameters.pop("reload_data")
        warning_key = "reload_data_deprecated"
        if warning_key not in _shown_deprecation_warnings:
            warnings.warn(
                "The 'reload_data' parameter has been removed and has no effect.",
                DeprecationWarning,
                stacklevel=2,
            )
            _shown_deprecation_warnings.add(warning_key)

    try_to_convert_back_to_original_types: bool = True
    # Deprecated parameter handling for backward compatibility
    if "try_to_convert_back_to_original_types" in default_column_parameters:
        try_to_convert_back_to_original_types = default_column_parameters.pop(
            "try_to_convert_back_to_original_types"
        )
        warning_key = "try_to_convert_back_to_original_types_deprecated"
        if warning_key not in _shown_deprecation_warnings:
            warnings.warn(
                "The 'try_to_convert_back_to_original_types' parameter is deprecated and will be removed in a future version. "
                "The component now handles type preservation automatically where appropriate.",
                DeprecationWarning,
                stacklevel=2,
            )
            _shown_deprecation_warnings.add(warning_key)

    ##Parses Themes
    if isinstance(theme, (str, AgGridTheme)):
        # Legacy compatibility
        themeObj: StAggridTheme = StAggridTheme(None)
        themeObj["themeName"] = theme if isinstance(theme, str) else theme.value

    elif isinstance(theme, StAggridTheme):
        themeObj = theme

    elif theme is None:
        themeObj = "streamlit"
    else:
        raise ValueError(
            f"{theme} is not valid. Available options: {AgGridTheme.__members__}"
        )

    # Parse return Mode
    if not isinstance(data_return_mode, (str, DataReturnMode)):
        raise ValueError(
            "DataReturnMode should be either a DataReturnMode enum value or a string."
        )
    elif isinstance(data_return_mode, str):
        try:
            data_return_mode = DataReturnMode[data_return_mode.upper()]
        except Exception:
            raise ValueError(f"{data_return_mode} is not valid.")

    # Parse update Mode
    if not isinstance(update_mode, (str, GridUpdateMode)):
        raise ValueError(
            "GridUpdateMode should be either a valid GridUpdateMode enum value or string"
        )
    elif isinstance(update_mode, str):
        try:
            update_mode = GridUpdateMode[update_mode.upper()]
        except Exception:
            raise ValueError(f"{update_mode} is not valid.")

    # Add deprecation warning for GridUpdateMode
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

    if update_mode:
        update_on = list(update_on)
        if update_mode == GridUpdateMode.MANUAL:
            manual_update = True
        else:
            manual_update = False
            update_on.extend(parse_update_mode(update_mode))

    # Validate CUSTOM mode parameters
    if data_return_mode == DataReturnMode.CUSTOM:
        if custom_jscode_for_grid_return is None:
            raise ValueError(
                "custom_jscode_for_grid_return parameter is required when using DataReturnMode.CUSTOM"
            )
        if not isinstance(custom_jscode_for_grid_return, JsCode):
            raise ValueError(
                "custom_jscode_for_grid_return must be a JsCode object when using DataReturnMode.CUSTOM"
            )

    # Process JsCode for CUSTOM mode
    original_custom_jscode_for_grid_return = custom_jscode_for_grid_return
    if custom_jscode_for_grid_return is not None:
        custom_jscode_for_grid_return = custom_jscode_for_grid_return.js_code
        allow_unsafe_jscode = True
    
    # Process JsCode for should_grid_return
    if should_grid_return is not None:
        should_grid_return = should_grid_return.js_code
        allow_unsafe_jscode = True

    # parse data and gridOptions
    data, gridOptions, frame_dtypes = _parse_data_and_grid_options(
        data,
        gridOptions,
        default_column_parameters,
        allow_unsafe_jscode,
        use_json_serialization,
    )

    if not isinstance(data, pd.DataFrame):
        try_to_convert_back_to_original_types = False

    custom_css = custom_css or dict()

    if height is None:
        gridOptions["domLayout"] = "autoHeight"

    if default_column_parameters.pop("fit_columns_on_grid_load", False):
        warnings.warn(
            "fit_columns_on_grid_load is deprecated. Use gridOptions autoSizeStrategy instead.",
            DeprecationWarning,
        )
        gridOptions["autoSizeStrategy"] = {"type": "fitGridWidth"}

    # Create collector based solely on data_return_mode
    if data_return_mode == DataReturnMode.MINIMAL:
        from .collectors.minimal import MinimalCollector

        collector = MinimalCollector()
    elif data_return_mode == DataReturnMode.CUSTOM:
        from .collectors.custom import CustomCollector

        collector = CustomCollector(original_custom_jscode_for_grid_return.js_code)
    else:
        # Use LegacyCollector for AS_INPUT, FILTERED, FILTERED_AND_SORTED
        from .collectors.legacy import LegacyCollector

        collector = LegacyCollector(
            data_return_mode=data_return_mode,
            try_to_convert_back_to_original_types=True,
            conversion_errors=conversion_errors,
            frame_dtypes=frame_dtypes,
        )

    # Create initial response object that callbacks can safely reference
    original_data = None
    if data is not None:
        original_data = (
            data.drop("::auto_unique_id::", axis="columns")
            if "::auto_unique_id::" in data.columns
            else data
        )

    response = collector.create_initial_response(
        original_data=original_data,
        grid_options=gridOptions,
        try_to_convert_back_to_original_types=try_to_convert_back_to_original_types,
        conversion_errors=conversion_errors,
    )

    if callback and not key:
        raise ValueError("Component key must be set to use a callback.")

    elif key and not callback:
        # This allows the table to keep its state up to date (eg #176)
        def _inner_callback():
            component_value = st.session_state.get(key)
            # Update the existing response object with new component value and store the wrapped response
            updated_response = collector.update_response(response, component_value)
            st.session_state[key] = updated_response

    elif callback and key:
        # User defined callback
        def _inner_callback():
            component_value = st.session_state.get(key)
            # Update the existing response object with new component value and store the wrapped response
            updated_response = collector.update_response(response, component_value)
            st.session_state[key] = updated_response
            return callback(updated_response)
    else:
        _inner_callback = None

    pro_assets = default_column_parameters.pop("pro_assets", None)

    def _compute_data_hash(df):
        if df is None:
            return ""

        try:
            return str(pd.util.hash_pandas_object(df).sum())
        except TypeError:
            import logging

            logging.warning(
                "DataFrame contains non-hashable data, attempting type conversion..."
            )

            try:
                df_copy = df.copy()
                for col in df_copy.columns:
                    df_copy[col] = df_copy[col].apply(
                        lambda x: tuple(x)
                        if isinstance(x, list)
                        else frozenset(x)
                        if isinstance(x, set)
                        else frozenset(x.items())
                        if isinstance(x, dict)
                        else x
                    )
                return str(pd.util.hash_pandas_object(df_copy).sum())
            except (TypeError, ValueError, AttributeError) as e:
                logging.warning(
                    f"Type conversion failed ({e}), falling back to string-based hashing..."
                )
                return str(hash(df.to_string()))

    data_hash = _compute_data_hash(data)

    _component_func_args = dict(
        data=data,
        data_hash=data_hash,
        gridOptions=gridOptions,
        height=height,
        data_return_mode=data_return_mode,
        frame_dtypes=str(frame_dtypes),
        allow_unsafe_jscode=allow_unsafe_jscode,
        columns_state=columns_state,
        custom_css=custom_css,
        default=None,
        enable_enterprise_modules=enable_enterprise_modules,
        key=key,
        license_key=license_key,
        manual_update=manual_update,
        on_change=_inner_callback,
        pro_assets=pro_assets,
        show_download_button=show_download_button,
        show_search=show_search,
        show_toolbar=show_toolbar,
        custom_jscode_for_grid_return=custom_jscode_for_grid_return,
        should_grid_return=should_grid_return,
        theme=themeObj,
        debug=default_column_parameters.pop("debug", False),
        update_on=update_on,
        use_json_serialization=use_json_serialization,
        server_sync_strategy=server_sync_strategy,
    )

    try:
        component_value = _component_func(**_component_func_args)
    except Exception as ex:
        # Check if this is a PyArrow conversion error and we should try JSON serialization
        error_msg = str(ex)
        is_pyarrow_error = (
            "Could not convert" in error_msg
            or "pyarrow" in error_msg.lower()
            or "ArrowInvalid" in error_msg
            or "Conversion failed" in error_msg
        )

        if use_json_serialization == "auto" and data is not None and is_pyarrow_error:
            logging.warning(
                f"PyArrow conversion failed, automatically retrying with JSON serialization: {error_msg}"
            )
            # Retry with JSON serialization enabled
            _component_func_args["use_json_serialization"] = True
            return AgGrid(**_component_func_args)
        elif not use_json_serialization and data is not None and is_pyarrow_error:
            # User explicitly disabled JSON serialization, raise the PyArrow error
            raise ex
        else:
            # For other exceptions, add the original error message enhancement
            args = list(ex.args)
            args[0] += (
                ". If you're using custom JsCode objects on gridOptions, ensure that allow_unsafe_jscode is True."
            )
            raise type(ex)(*args)

    # Update the response object with final component data
    try:
        response = collector.update_response(response, component_value)
    except Exception as ex:
        # Enhanced error message for collector issues
        args = list(ex.args)
        args[0] += f". Error in {collector.__class__.__name__} processing."
        if data_return_mode == DataReturnMode.CUSTOM:
            args[0] += (
                " Check your custom_jscode_for_grid_return JsCode implementation."
            )
        raise type(ex)(*args)

    return response
