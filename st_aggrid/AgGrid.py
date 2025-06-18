import os
import json
import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import warnings
import typing

from decouple import config
from typing import Any, Mapping, Tuple, Union
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import (
    GridUpdateMode,
    DataReturnMode,
    JsCode,
    StAggridTheme,
    walk_gridOptions,
    AgGridTheme,
)
from st_aggrid.AgGridReturn import AgGridReturn


# This function exists because pandas behaviour when converting tz aware datetime to iso format.
def __cast_date_columns_to_iso8601(dataframe: pd.DataFrame):
    """Internal Method to convert tz-aware datetime columns to correct ISO8601 format"""
    for c, d in dataframe.dtypes.items():
        if d.kind == "M":
            dataframe[c] = dataframe[c].apply(lambda s: s.isoformat())


def __parse_row_data(data) -> Tuple[Any, Any]:
    """Internal method to process data from data_parameter"""
    # no data received, render an empty grid if gridOptions is present
    if data is None:
        return [], None

    if isinstance(data, pd.DataFrame):
        data_parameter = data.copy()
        __cast_date_columns_to_iso8601(data_parameter)
        # creates an index column that uniquely identify the rows, this index will be used in AgGrid getRowId call on the Javascript side.
        data_parameter["__pandas_index"] = [
            str(i) for i in range(data_parameter.shape[0])
        ]
        row_data = data_parameter.to_json(orient="records", date_format="iso")
        frame_dtypes = dict(
            zip(data_parameter.columns, (t.kind for t in data_parameter.dtypes))
        )
        del data_parameter["__pandas_index"]
        return json.loads(row_data), frame_dtypes

    if isinstance(data, str):
        # is data the path to a local json file?
        if data.endswith(".json") and os.path.exists(data):
            try:
                with open(os.path.abspath(data)) as f:
                    return json.loads(json.dumps(json.load(f))), None
            except Exception as ex:
                raise Exception(f"Error reading {data}. {ex}")

        # is data raw valid json?
        try:
            return json.loads(data), None
        except Exception:
            raise Exception("Error parsing data parameter as raw json.")

    raise ValueError("Invalid data")


def __parse_grid_options(
    gridOptions_parameter, data, default_column_parameters, unsafe_allow_jscode
):
    """Internal method to cast gridOptions parameter to a valid gridoptions"""
    # if no gridOptions is passed, builds a default one.
    if (gridOptions_parameter == None) and not (data is None):
        gb = GridOptionsBuilder.from_dataframe(data, **default_column_parameters)
        gridOptions = gb.build()

    # if it is a dict-like object, assumes is valid and use it.
    elif isinstance(gridOptions_parameter, Mapping):
        gridOptions = gridOptions_parameter

    # if it is a string check if is valid path or a valid json and use it.
    elif isinstance(gridOptions_parameter, str):
        import os
        import json

        is_path = gridOptions_parameter.endswith(".json") and os.path.exists(
            gridOptions_parameter
        )

        if is_path:
            gridOptions = json.load(open(os.path.abspath(gridOptions_parameter)))
        else:
            gridOptions = json.loads(gridOptions_parameter)

    else:
        raise ValueError("gridOptions is invalid.")

    if unsafe_allow_jscode:
        # NOTE: Streamlit should allow passing a class to its inner component dumps, this way any class could serialized on AgGrid call.
        walk_gridOptions(
            gridOptions, lambda v: v.js_code if isinstance(v, JsCode) else v
        )

    return gridOptions


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


def __parse_update_mode(update_mode: GridUpdateMode):
    update_on = []

    if update_mode & GridUpdateMode.VALUE_CHANGED:
        update_on.append("cellValueChanged")

    if update_mode & GridUpdateMode.SELECTION_CHANGED:
        update_on.append("selectionChanged")

    if update_mode & GridUpdateMode.FILTERING_CHANGED:
        update_on.append("filterChanged")

    if update_mode & GridUpdateMode.SORTING_CHANGED:
        update_on.append("sortChanged")

    if update_mode & GridUpdateMode.COLUMN_RESIZED:
        update_on.append(("columnResized", 300))

    if update_mode & GridUpdateMode.COLUMN_MOVED:
        update_on.append(("columnMoved", 500))

    if update_mode & GridUpdateMode.COLUMN_PINNED:
        update_on.append("columnPinned")

    if update_mode & GridUpdateMode.COLUMN_VISIBLE:
        update_on.append("columnVisible")

    return update_on


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

    # if not (isinstance(theme, (str, AgGridTheme)) and (theme in AgGridTheme)):
    #     raise ValueError(
    #         f"{theme} is not valid. Available options: {AgGridTheme.__members__}"
    #     )
    # else:
    #     if isinstance(theme, AgGridTheme):
    #         theme = theme.value

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
        except:
            raise ValueError(f"{data_return_mode} is not valid.")

    # Parse update Mode
    if not isinstance(update_mode, (str, GridUpdateMode)):
        raise ValueError(
            "GridUpdateMode should be either a valid GridUpdateMode enum value or string"
        )
    elif isinstance(update_mode, str):
        try:
            update_mode = GridUpdateMode[update_mode.upper()]
        except:
            raise ValueError(f"{update_mode} is not valid.")

    if update_mode:
        update_on = list(update_on)
        if update_mode == GridUpdateMode.MANUAL:
            manual_update = True
        else:
            manual_update = False
            update_on.extend(__parse_update_mode(update_mode))

    # Parse gridOptions
    gridOptions = __parse_grid_options(
        gridOptions, data, default_column_parameters, allow_unsafe_jscode
    )

    frame_dtypes = []

    # rowData in grid options have precedence and are assumed to be correct json.
    if "rowData" not in gridOptions:
        row_data, frame_dtypes = __parse_row_data(data)
        gridOptions["rowData"] = row_data

    if not isinstance(data, pd.DataFrame):
        try_to_convert_back_to_original_types = False

    custom_css = custom_css or dict()

    if height == None:
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
            response._set_component_value(st.session_state[key])
    elif callback and key:
        # User defined callback
        def _inner_callback():
            response._set_component_value(st.session_state[key])
            return callback(response)
    else:
        _inner_callback = None

    pro_assets = default_column_parameters.pop("pro_assets", None)

    try:
        component_value = _component_func(
            gridOptions=gridOptions,
            height=height,
            data_return_mode=data_return_mode,
            frame_dtypes=frame_dtypes,
            allow_unsafe_jscode=allow_unsafe_jscode,
            enable_enterprise_modules=enable_enterprise_modules,
            license_key=license_key,
            default=None,
            columns_state=columns_state,
            theme=themeObj,
            custom_css=custom_css,
            update_on=update_on,
            manual_update=manual_update,
            key=key,
            on_change=_inner_callback,
            show_toolbar=show_toolbar,
            show_search=show_search,
            show_download_button=show_download_button,
            pro_assets=pro_assets,
        )

    except Exception as ex:  # components.components.MarshallComponentException as ex:
        # uses a more complete error message.
        args = list(ex.args)
        args[0] += (
            ". If you're using custom JsCode objects on gridOptions, ensure that allow_unsafe_jscode is True."
        )
        # ex = components.components.MarshallComponentException(*args)
        raise (ex)

    if component_value:
        response._set_component_value(component_value)

    # if component_value:
    # response.grid_response = component_value

    # if isinstance(component_value, str):
    #     component_value = json.loads(component_value)
    # frame = pd.DataFrame(component_value["rowData"])
    # original_types = component_value["originalDtypes"]

    return response
