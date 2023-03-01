
from decimal import InvalidOperation
import os
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import json
import warnings
import typing

from dataclasses import dataclass, field
from decouple import config
from typing import Any, List, Mapping, Union, Any
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode, DataReturnMode, JsCode, walk_gridOptions, ColumnsAutoSizeMode, AgGridTheme, ExcelExportMode
@dataclass
class AgGridReturn(Mapping):
    """Class to hold AgGrid call return"""
    data: Union[pd.DataFrame , str] = None
    selected_rows: List[Mapping] = field(default_factory=list)
    column_state = None
    excel_blob = None

    #Backwards compatibility with dict interface
    def __getitem__(self, __k):
        return self.__dict__.__getitem__(__k)

    def __iter__(self):
        return self.__dict__.__iter__()
    
    def __len__(self):
        return self.__dict__.__len__()

    def keys(self):
        return self.__dict__.keys()
    
    def values(self):
        return self.__dict__.values()

#This function exists because pandas behaviour when converting tz aware datetime to iso format.
def __cast_date_columns_to_iso8601(dataframe: pd.DataFrame):
    """Internal Method to convert tz-aware datetime columns to correct ISO8601 format"""
    for c, d in dataframe.dtypes.items():
        if not d.kind == 'M':
            continue
        else:
            dataframe[c] = dataframe[c].apply(lambda s: s.isoformat()) 

def __parse_row_data(data_parameter):
    """Internal method to process data from data_parameter"""

    if isinstance(data_parameter, pd.DataFrame):
        __cast_date_columns_to_iso8601(data_parameter) 
        row_data = data_parameter.to_json(orient='records', date_format='iso')
        return row_data

    elif isinstance(data_parameter, str):
        import os
        import json
        is_path = data_parameter.endswith('.json') and os.path.exists(data_parameter)
        
        if is_path:
            row_data = json.dumps(json.load(open(os.path.abspath(data_parameter))))
        else:
            row_data = json.dumps(json.loads(data_parameter))
        
        return row_data
    else:
        raise ValueError("Invalid data")
    

def __parse_grid_options(gridOptions_parameter, dataframe, default_column_parameters, unsafe_allow_jscode):
    """Internal method to cast gridOptions parameter to a valid gridoptions"""
    # if no gridOptions is passed, builds a default one.
    if gridOptions_parameter == None:
        gb = GridOptionsBuilder.from_dataframe(dataframe,**default_column_parameters)
        gridOptions = gb.build()

    #if it is a dict-like object, assumes is valid and use it.
    elif isinstance(gridOptions_parameter, Mapping):
        gridOptions = gridOptions_parameter
    
    #if it is a string check if is valid path or a valid json and use it.
    elif isinstance(gridOptions_parameter, str):
        import os
        import json
        is_path = gridOptions_parameter.endswith('.json') and os.path.exists(gridOptions_parameter)
        
        if is_path:
            gridOptions = json.load(open(os.path.abspath(gridOptions_parameter)))
        else:
            gridOptions = json.loads(gridOptions_parameter)
    
    else:
        raise ValueError("gridOptions is invalid.")

    if unsafe_allow_jscode:
        walk_gridOptions(gridOptions, lambda v: v.js_code if isinstance(v, JsCode) else v)

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
    build_dir = os.path.join(parent_dir, "frontend","build")
    _component_func = components.declare_component("agGrid", path=build_dir)

def __parse_update_mode(update_mode: GridUpdateMode):
    update_on = []

    if (update_mode & GridUpdateMode.VALUE_CHANGED):
        update_on.append("cellValueChanged")
    
    if (update_mode & GridUpdateMode.SELECTION_CHANGED):
        update_on.append("selectionChanged")

    if (update_mode & GridUpdateMode.FILTERING_CHANGED):
        update_on.append("filterChanged")
    
    if (update_mode & GridUpdateMode.SORTING_CHANGED):
        update_on.append("sortChanged")
    
    if (update_mode & GridUpdateMode.COLUMN_RESIZED):
        update_on.append(("columnResized", 300))
    
    if (update_mode & GridUpdateMode.COLUMN_MOVED):
        update_on.append(("columnMoved", 500))
    
    if (update_mode & GridUpdateMode.COLUMN_PINNED):
        update_on.append("columnPinned")

    if (update_mode & GridUpdateMode.COLUMN_VISIBLE):
        update_on.append("columnVisible")
        
    return update_on

def AgGrid(
    data: Union[pd.DataFrame,  str],
    gridOptions: typing.Dict=None ,
    height: int = None,
    width=None,
    fit_columns_on_grid_load: bool=False,
    columns_auto_size_mode: ColumnsAutoSizeMode = ColumnsAutoSizeMode.NO_AUTOSIZE,
    update_mode: GridUpdateMode = GridUpdateMode.MODEL_CHANGED,
    data_return_mode: DataReturnMode= DataReturnMode.AS_INPUT,
    allow_unsafe_jscode: bool=False,
    enable_enterprise_modules: bool=True,
    license_key: str=None,
    try_to_convert_back_to_original_types: bool=True,
    conversion_errors: str='coerce',
    reload_data:bool=False,
    columns_state = None,
    theme:str=AgGridTheme.STREAMLIT,
    custom_css=None,
    use_legacy_selected_rows=False,
    key: typing.Any=None,
    update_on = [],
    enable_quicksearch=False,
    excel_export_mode: ExcelExportMode = ExcelExportMode.NONE,
    excel_export_multiple_sheet_params: Mapping = None,
    **default_column_parameters) -> AgGridReturn:
    """Reders a DataFrame using AgGrid.

    Parameters
    ----------
    dataframe : pd.DataFrame
        The underlaying dataframe to be used.

    gridOptions : typing.Dict, optional
        A dictionary of options for ag-grid. Documentation on www.ag-grid.com
        If None default grid options will be created with GridOptionsBuilder.from_dataframe() call.
        Default: None
    
    height : int, optional
        The grid height in pixels.
        If None, grid will enable Auto Height by default https://www.ag-grid.com/react-data-grid/grid-size/#dom-layout
        Default: None

    width : [type], optional
        Deprecated.
    
    fit_columns_on_grid_load : bool, optional
        Deprecated, use columns_auto_size_mode
        Will adjust columns to fit grid width on grid load.
        Default False

    columns_auto_size_mode: ColumnsAutoSizeMode, optional
        Sets columns auto size behavior on grid load event.
        More info: https://www.ag-grid.com/react-data-grid/column-sizing/#auto-size-columns
            ColumnsAutoSizeMode.NO_AUTOSIZE             -> No column resizing. Width defined at gridOptins is used.
            ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW -> Make the currently visible columns fit the screen. The columns will scale (growing or shrinking) to fit the available width.
            ColumnsAutoSizeMode.FIT_CONTENTS    -> Grid will work out the best width to fit the contents of the cells in the column.
        Default: ColumnsAutoSizeMode.NO_AUTOSIZE    

    update_mode : GridUpdateMode, optional
        UPDATE_MODE IS DEPRECATED. USE update_on instead.

        Defines how the grid will send results back to streamlit.
        either a string, one or a combination of:
            GridUpdateMode.NO_UPDATE
            GridUpdateMode.MANUAL
            GridUpdateMode.VALUE_CHANGED
            GridUpdateMode.SELECTION_CHANGED
            GridUpdateMode.FILTERING_CHANGED
            GridUpdateMode.SORTING_CHANGED
            GridUpdateMode.MODEL_CHANGED
        When using manual a save button will be drawn on top of grid.
        modes can be combined with bitwise OR operator |, for instance:
        GridUpdateMode = VALUE_CHANGED | SELECTION_CHANGED | FILTERING_CHANGED | SORTING_CHANGED
        Default: GridUpdateMode.MODEL_CHANGED

    update_on: list[string | tuple[sting, int]], optional
        defines the events that will trigger a refresh and grid return on streamlit app.
        valid string named events are listed in https://www.ag-grid.com/javascript-data-grid/grid-events/.
        If a tuple[string, int] is present on the list, that event will be debounced by x milliseconds.
        for instance:
            if update_on = ['cellValueChanged', ("columnResized", 500)]
            Grid will return when cell values are changed AND when columns are resized, however the later will
            be debounced by 500 ms. More information about debounced functions 
            here: https://www.freecodecamp.org/news/javascript-debounce-example/
    
    data_return_mode : DataReturnMode, optional
        Defines how the data will be retrieved from components client side. One of:
            DataReturnMode.AS_INPUT             -> Returns grid data as inputed. Includes cell editions
            DataReturnMode.FILTERED             -> Returns filtered grid data, maintains input order
            DataReturnMode.FILTERED_AND_SORTED  -> Returns grid data filtered and sorted
        Defaults to DataReturnMode.AS_INPUT.
        
    allow_unsafe_jscode : bool, optional
        Allows jsCode to be injected in gridOptions.
        Defaults to False.

    enable_enterprise_modules : bool, optional
        Loads Ag-Grid enterprise modules (check licensing).
        Defaults to False.

    license_key : str, optional
        Licence key to use for enterprise modules
        By default None

    try_to_convert_back_to_original_types : bool, optional
        Attempts to convert data retrieved from the grid to original types.
        Defaults to True.

    conversion_errors : str, optional
        Behaviour when conversion fails. One of:
            'raise'     -> invalid parsing will raise an exception.
            'coerce'    -> then invalid parsing will be set as NaT/NaN.
            'ignore'    -> invalid parsing will return the input.
        Defaults to 'coerce'.
    
    reload_data : bool, optional
        Force AgGrid to reload data using api calls. Should be false on most use cases
        Default False

    enable_quicksearch: bool, optional
        Adds a quicksearch text field on top of grid.
        Defaults to False
    
    excel_export_mode: ExcelExportMode, optional
        Defines how Excel Export integration behaves:
            NONE -> Nothing Changes. Default grid behaviour.
            MANUAL -> Adds a download button on grid's top that triggers download.
            FILE_BLOB_IN_GRID_RESPONSE -> include in grid's return an ExcelBlob Property with file binary encoded as B64 String
            TRIGGER_DOWNLOAD_AFTER_REFRESH -> Triggers file download before returning results to streamlit.
            SHEET_BLOB_IN_GRID_RESPONSE -> include in grid's return a SheetlBlob Property with sheet binary encoded as B64 String. Meant to be used with MULTIPLE
            MULTIPLE_SHEETS -> Same as TRIGGER_DOWNLOAD_AFTER_REFRESH but will include b64 encoded *SHEETS* returned with SHEET_BLOB_IN_GRID_RESPONSE and supplied to grid's call using excel_export_extra_sheets parameter.
    
    theme : str, optional
        theme used by ag-grid. One of:
            
            'streamlit' -> follows default streamlit colors
            'light'     -> ag-grid balham-light theme
            'dark'      -> ag-grid balham-dark theme
            'blue'      -> ag-grid blue theme
            'fresh'     -> ag-grid fresh theme
            'material'  -> ag-grid material theme
        By default 'light'
    
    custom_css (dict, optional):
        Custom CSS rules to be added to the component's iframe.

    key : typing.Any, optional
        Streamlits key argument. Check streamlit's documentation.
        Defaults to None.
    
    **default_column_parameters:
        Other parameters will be passed as key:value pairs on gripdOptions defaultColDef.

    Returns
    -------
    Dict
        returns a dictionary with grid's data is in dictionary's 'data' key. 
        Other keys may be present depending on gridOptions parameters
    """

    if width:
        warnings.warn(DeprecationWarning("Width parameter is deprecated and will be removed on next version."))

    if fit_columns_on_grid_load:
        warnings.warn(DeprecationWarning("fit_columns_on_grid_load is deprecated and will be removed on next version."))
        columns_auto_size_mode = ColumnsAutoSizeMode.FIT_ALL_COLUMNS_TO_VIEW

    if  not (isinstance(theme, (str, AgGridTheme)) and (theme in AgGridTheme)):
        raise ValueError(f"{theme} is not valid. Available options: {AgGridTheme.__members__}")
    else:
        if isinstance(theme, AgGridTheme):
            theme = theme.value
    
    if (not isinstance(data_return_mode, (str, DataReturnMode))):
        raise ValueError(f"DataReturnMode should be either a DataReturnMode enum value or a string.")
    elif isinstance(data_return_mode, str):
        try:
            data_return_mode = DataReturnMode[data_return_mode.upper()]
        except:
            raise ValueError(f"{data_return_mode} is not valid.")
    
    if (not isinstance(update_mode, (str, GridUpdateMode))):
        raise ValueError(f"GridUpdateMode should be either a valid GridUpdateMode enum value or string")
    elif isinstance(update_mode, str):
        try:
            update_mode = GridUpdateMode[update_mode.upper()]
        except:
            raise ValueError(f"{update_mode} is not valid.")

    if  not (isinstance(excel_export_mode, (str, ExcelExportMode)) and (excel_export_mode in ExcelExportMode)):
        raise ValueError(f"{excel_export_mode} is not valid. Available options: {ExcelExportMode.__members__}")
    else:
        if isinstance(excel_export_mode, ExcelExportMode):
            excel_export_mode = excel_export_mode.value

    if update_mode:
        update_on = list(update_on)
        if update_mode == GridUpdateMode.MANUAL:
            manual_update=True
        else:
            manual_update=False
            update_on.extend(__parse_update_mode(update_mode))

    frame_dtypes = []
    if try_to_convert_back_to_original_types:
        if not isinstance(data, pd.DataFrame):
            try_to_convert_back_to_original_types = False
            #raise InvalidOperation(f"If try_to_convert_back_to_original_types is True, data must be a DataFrame.")

        frame_dtypes = dict(zip(data.columns, (t.kind for t in data.dtypes)))

    gridOptions = __parse_grid_options(gridOptions, data, default_column_parameters, allow_unsafe_jscode)
    row_data = __parse_row_data(data)
    custom_css = custom_css or dict()


    response = AgGridReturn()
    response.data = data

    if height == None:
        gridOptions['domLayout'] ='autoHeight'

    try:
        component_value = _component_func(
            gridOptions=gridOptions,
            row_data=row_data,
            height=height, 
            width=width,
            columns_auto_size_mode=columns_auto_size_mode, 
            data_return_mode=data_return_mode, 
            frame_dtypes=frame_dtypes,
            allow_unsafe_jscode=allow_unsafe_jscode,
            enable_enterprise_modules=enable_enterprise_modules,
            license_key=license_key,
            default=None,
            reload_data=reload_data,
            columns_state=columns_state,
            theme=theme,
            custom_css=custom_css,
            update_on=update_on,
            manual_update=manual_update,
            enable_quicksearch=enable_quicksearch,
            excel_export_mode=excel_export_mode,
            ExcelExportMultipleSheetParams=excel_export_multiple_sheet_params,
            key=key
            )

    except components.components.MarshallComponentException as ex:
        #uses a more complete error message.
        args = list(ex.args)
        args[0] += ". If you're using custom JsCode objects on gridOptions, ensure that allow_unsafe_jscode is True."
        ex = components.components.MarshallComponentException(*args)
        raise(ex)

    if component_value:
        if isinstance(component_value, str):
            component_value = json.loads(component_value)
        frame = pd.DataFrame(component_value["rowData"])
        original_types = component_value["originalDtypes"]

        if not frame.empty:
            if try_to_convert_back_to_original_types:
                numeric_columns = [k for k,v in original_types.items() if v in ['i','u','f']]
                if numeric_columns:
                    frame.loc[:,numeric_columns] = frame.loc[:,numeric_columns] .apply(pd.to_numeric, errors=conversion_errors)

                text_columns = [k for k,v in original_types.items() if v in ['O','S','U']]
                if text_columns:
                    frame.loc[:,text_columns]  = frame.loc[:,text_columns].astype(str)

                date_columns = [k for k,v in original_types.items() if v == "M"]
                if date_columns:
                    frame.loc[:,date_columns] = frame.loc[:,date_columns].apply(pd.to_datetime, errors=conversion_errors)

                timedelta_columns = [k for k,v in original_types.items() if v == "m"]
                if timedelta_columns:
                    def cast_to_timedelta(s):
                        try:
                            return pd.Timedelta(s)
                        except:
                            return s

                    frame.loc[:,timedelta_columns] = frame.loc[:,timedelta_columns].apply(cast_to_timedelta)

        response.data = frame
        
        if use_legacy_selected_rows:
            response.selected_rows = component_value["selectedRows"]
        else:
            response.selected_rows = component_value["selectedItems"]

        response.column_state = component_value["colState"]
        response.excel_blob = component_value['ExcelBlob']

    
    return response
