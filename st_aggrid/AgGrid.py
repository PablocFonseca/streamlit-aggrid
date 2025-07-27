import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import warnings
import os
import typing
from decouple import config
from typing import Union
from st_aggrid.shared import (
    GridUpdateMode,
    DataReturnMode,
    JsCode,
    StAggridTheme,
    AgGridTheme,
)
from st_aggrid.aggrid_utils import (
    parse_row_data,
    parse_grid_options,
    parse_update_mode,
)
from st_aggrid.AgGridReturn import AgGridReturn




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
    fit_columns_on_grid_load=False,
    update_mode: GridUpdateMode = GridUpdateMode.MODEL_CHANGED,
    data_return_mode: DataReturnMode = DataReturnMode.FILTERED_AND_SORTED,
    allow_unsafe_jscode: bool = False,
    enable_enterprise_modules: bool = False,
    license_key: str = None,
    try_to_convert_back_to_original_types: bool = True,
    conversion_errors: str = "coerce",
    columns_state=None,
    theme: str | StAggridTheme = "streamlit",
    custom_css=None,
    key: typing.Any = None,
    update_on=[],
    callback=None,
    show_toolbar: bool = False,
    show_search: bool = True,
    show_download_button: bool = True,
    should_grid_return: JsCode = None,
    collect_grid_return: JsCode = None,
    **default_column_parameters,
) -> AgGridReturn:
    """Renders a DataFrame using AgGrid.

    Parameters
    ----------
    dataframe : pd.DataFrame
        The underlying dataframe to be used.

    gridOptions : typing.Dict, optional
        A dictionary of options for ag-grid. Documentation on www.ag-grid.com
        If None, default grid options will be created with GridOptionsBuilder.from_dataframe() call.
        Default: None

    height : int, optional
        The grid height in pixels.
        If None, grid will enable Auto Height by default https://www.ag-grid.com/react-data-grid/grid-size/#dom-layout
        Default: None

    width : [type], optional
        Deprecated.

    fit_columns_on_grid_load : bool, optional
        DEPRECATED, use columns_auto_size_mode
        Use gridOptions autoSizeStrategy (https://www.ag-grid.com/javascript-data-grid/column-sizing/#auto-sizing-columns)

    columns_auto_size_mode: ColumnsAutoSizeMode, optional
        DEPRECATED.
        Use gridOptions autoSizeStrategy (https://www.ag-grid.com/javascript-data-grid/column-sizing/#auto-sizing-columns)

    update_mode : GridUpdateMode, optional
        DEPRECATED. USE update_on instead.

        Defines how the grid will send results back to streamlit.
        either a string, one or a combination of:
            GridUpdateMode.NO_UPDATE
            GridUpdateMode.MANUAL
            GridUpdateMode.VALUE_CHANGED
            GridUpdateMode.SELECTION_CHANGED
            GridUpdateMode.FILTERING_CHANGED
            GridUpdateMode.SORTING_CHANGED
            GridUpdateMode.MODEL_CHANGED
        When using manual, a save button will be drawn on top of the grid.
        Modes can be combined with bitwise OR operator |, for instance:
        GridUpdateMode = VALUE_CHANGED | SELECTION_CHANGED | FILTERING_CHANGED | SORTING_CHANGED
        Default: GridUpdateMode.MODEL_CHANGED

    update_on: list[string | tuple[string, int]], optional
        Defines the events that will trigger a refresh and grid return on the Streamlit app.
        Valid string-named events are listed in https://www.ag-grid.com/javascript-data-grid/grid-events/.
        If a tuple[string, int] is present on the list, that event will be debounced by x milliseconds.
        For instance:
            if update_on = ['cellValueChanged', ("columnResized", 500)]
            The grid will return when cell values are changed AND when columns are resized, however the latter will
            be debounced by 500 ms. More information about debounced functions
            here: https://www.freecodecamp.org/news/javascript-debounce-example/

    callback: callable, optional
        Defines a function that will be called on change. One argument will be passed to the function
        which will be an AgGridReturn object in the same fashion as what is returned by this class.
        Requires key to be set.

    data_return_mode : DataReturnMode, optional
        Defines how the data will be retrieved from the component's client side. One of:
            DataReturnMode.AS_INPUT             -> Returns grid data as inputted. Includes cell edits.
            DataReturnMode.FILTERED             -> Returns filtered grid data, maintains input order.
            DataReturnMode.FILTERED_AND_SORTED  -> Returns grid data filtered and sorted.
        Defaults to DataReturnMode.FILTERED_AND_SORTED.

    allow_unsafe_jscode : bool, optional
        Allows jsCode to be injected in gridOptions.
        Defaults to False.

    enable_enterprise_modules : bool, optional
        Loads Ag-Grid enterprise modules (check licensing).
        Defaults to False.

    license_key : str, optional
        License key to use for enterprise modules.
        By default None.

    try_to_convert_back_to_original_types : bool, optional
        Attempts to convert data retrieved from the grid to original types.
        Defaults to True.

    conversion_errors : str, optional
        Behavior when conversion fails. One of:
            'raise'     -> Invalid parsing will raise an exception.
            'coerce'    -> Invalid parsing will be set as NaT/NaN.
            'ignore'    -> Invalid parsing will return the input.
        Defaults to 'coerce'.

    columns_state : dict, optional
        Allows setting the initial state of columns (e.g., visibility, order, etc.).
        Defaults to None.

    theme : str | StAggridTheme, optional
        Theme used by ag-grid. One of:

            'streamlit' -> Follows default Streamlit colors.
            'light'     -> Ag-grid balham-light theme.
            'dark'      -> Ag-grid balham-dark theme.
            'blue'      -> Ag-grid blue theme.
            'fresh'     -> Ag-grid fresh theme.
            'material'  -> Ag-grid material theme.
        By default 'streamlit'.

    custom_css : dict, optional
        Custom CSS rules to be added to the component's iframe.
        Defaults to None.

    key : typing.Any, optional
        Streamlit's key argument. Check Streamlit's documentation.
        Defaults to None.

    show_toolbar : bool, optional
        Whether to show the toolbar above the grid.
        Defaults to True.

    show_search : bool, optional
        Whether to show the search bar in the toolbar.
        Defaults to True.

    show_download_button : bool, optional
        Whether to show the download button in the toolbar.
        Defaults to True.

    **default_column_parameters:
        Other parameters will be passed as key:value pairs on gridOptions defaultColDef.

    Returns
    -------
    AgGridReturn
        Returns an AgGridReturn object containing the grid's data and other metadata.
    """

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

    if update_mode:
        update_on = list(update_on)
        if update_mode == GridUpdateMode.MANUAL:
            manual_update = True
        else:
            manual_update = False
            update_on.extend(parse_update_mode(update_mode))

    if should_grid_return is not None:
        if not isinstance(should_grid_return, JsCode):
            raise ValueError("If set, should_grid_return must be a JsCode Object.")
        should_grid_return = should_grid_return.js_code
        allow_unsafe_jscode = True

    if collect_grid_return is not None:
        if not isinstance(collect_grid_return, JsCode):
            raise ValueError("If set, collect_grid_return must be a JsCode Object.")
        collect_grid_return = collect_grid_return.js_code
        allow_unsafe_jscode = True

    # Parse gridOptions
    gridOptions = parse_grid_options(
        gridOptions, data, default_column_parameters, allow_unsafe_jscode
    )

    frame_dtypes = []

    # rowData in grid options have precedence and are assumed to be correct json.
    if "rowData" not in gridOptions:
        row_data, frame_dtypes = parse_row_data(data)
        gridOptions["rowData"] = row_data

    if not isinstance(data, pd.DataFrame):
        try_to_convert_back_to_original_types = False

    custom_css = custom_css or dict()

    if height is None:
        gridOptions["domLayout"] = "autoHeight"

    if fit_columns_on_grid_load:
        warnings.warn(
            DeprecationWarning(
                "fit_columns_on_grid_load is deprecated and will be removed on next version."
            )
        )
        gridOptions["autoSizeStrategy"] = {"type": "fitGridWidth"}

    
    response = AgGridReturn(
            data,
            gridOptions,
            data_return_mode,
            try_to_convert_back_to_original_types,
            conversion_errors,
        )


    if callback and not key:
        raise ValueError("Component key must be set to use a callback.")
    
    elif key and not callback:
        # This allows the table to keep its state up to date (eg #176)
        def _inner_callback():
            component_value = st.session_state[key]
            if isinstance(response, AgGridReturn):
                response._set_component_value(component_value)

    elif callback and key:
        # User defined callback
        def _inner_callback():
            component_value = st.session_state[key]
            if isinstance(response, AgGridReturn):
                response._set_component_value(component_value)
                return callback(response)
            else:
                return callback(component_value)
    else:
        _inner_callback = None

    pro_assets = default_column_parameters.pop("pro_assets", None)

    try:
        component_value = _component_func(
            allow_unsafe_jscode=allow_unsafe_jscode,
            columns_state=columns_state,
            custom_css=custom_css,
            data_return_mode=data_return_mode,
            default=None,
            enable_enterprise_modules=enable_enterprise_modules,
            frame_dtypes=frame_dtypes,
            gridOptions=gridOptions,
            height=height,
            key=key,
            license_key=license_key,
            manual_update=manual_update,
            on_change=_inner_callback,
            pro_assets=pro_assets,
            show_download_button=show_download_button,
            show_search=show_search,
            show_toolbar=show_toolbar,
            should_grid_return=should_grid_return,
            collect_grid_return=collect_grid_return,
            theme=themeObj,
            update_on=update_on,
        )

    except Exception as ex:  # components.components.MarshallComponentException as ex:
        # uses a more complete error message.
        args = list(ex.args)
        args[0] += (
            ". If you're using custom JsCode objects on gridOptions, ensure that allow_unsafe_jscode is True."
        )
        # ex = components.components.MarshallComponentException(*args)
        raise (ex)

    if collect_grid_return:
        response = component_value

    elif component_value:
        response._set_component_value(component_value)
    
    return response
