import os
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import json

from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import GridUpdateMode, DataReturnMode, JsCode, walk_gridOptions

_RELEASE = True

if not _RELEASE:
    _component_func = components.declare_component(
        "agGrid",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("agGrid", path=build_dir)

def AgGrid(
    dataframe,
    gridOptions=None,
    height=200,
    width='100%',
    fit_columns_on_grid_load=False,
    update_mode=GridUpdateMode.VALUE_CHANGED,
    data_return_mode=DataReturnMode.AS_INPUT,
    allow_unsafe_jscode=False,
    enable_enterprise_modules=False,
    try_to_convert_back_to_original_types=True,
    conversion_errors='coerce',
    key=None):
    """Shows a cusomizable grid based on a pandas DataFrame

    Args:
        dataframe (pandas.DataFrame): 
            The underlaying dataframe to be used.

        gridOptions (dictionary, optional): 
            A dictionary of options for ag-grid. Documentation on www.ag-grid.com
            Defaults to None. If None defaul grid options will be created with GridOptionsBuilder.from_dataframe() call.

        height (int, optional): 
            The grid height.
            Defaults to 200.

        fit_columns_on_grid_load (bool, optional): 
            Will adjust columns to fit grid width on grid load. 
            Defaults to False.

        update_mode (GridUpdateMode enumerator, optional): 
            Defines how the grid will send results back to streamlit.
            One of:
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
            Defaults to GridUpdateMode.VALUE_CHANGED.

        data_return_mode (DataReturnMode enum, optional): 
            Defines how the data will be retrieved from components client side. One of:
                DataReturnMode.AS_INPUT             -> Returns grid data as inputed. Includes cell editions
                DataReturnMode.FILTERED             -> Returns filtered grid data, maintains input order
                DataReturnMode.FILTERED_AND_SORTED  -> Returns grid data filtered and sorted
            Defaults to DataReturnMode.AS_INPUT.

        allow_unsafe_jscode (bool, optional): 
            Allows jsCode to be injected in gridOptions.
            Defaults to False.

        enable_enterprise_modules (bool, optional):
            Loads Ag-Grid enterprise modules (check licensing).
            Defaults to False.
        
        try_to_convert_back_to_original_types (bool, optional):
            Attempts to convert data retrieved from the grid to original types.
            Defaults to True.

        conversion_errors (str, optional): 
            Behaviour when conversion fails. One of:
                'raise'     -> invalid parsing will raise an exception.
                'coerce'    -> then invalid parsing will be set as NaT/NaN.
                'ignore'    -> invalid parsing will return the input.
            Defaults to 'coerce'.

        key ([type], optional): 
            Streamlits key argument. Check streamlit's documentation.
            Defaults to None.

    Returns:
        dictionary
        returns a dictionary with grid's data is in dictionary's 'data' key. 
        Other keys may be present depending on gridOptions parameters

    """
    response = {}
    response["data"] = dataframe
    response["selected_rows"] = []
    
    #basic numpy types of dataframe
    frame_dtypes = dict(zip(dataframe.columns, (t.kind for t in dataframe.dtypes)))

    # if no gridOptions is passed, builds a default one.
    if gridOptions == None:
        gb = GridOptionsBuilder.from_dataframe(dataframe)
        gridOptions = gb.build()

    #this is a hack because pandas to_json doesn't convert tzaware to iso dates properly https://github.com/pandas-dev/pandas/issues/12997
    date_cols = dataframe.select_dtypes([pd.DatetimeTZDtype, np.datetime64])
    date_cols = date_cols.applymap(lambda s: s.isoformat()) #slow!!

    json_frame = dataframe.copy() #avoids cache mutation
    json_frame.loc[:,date_cols.columns] = date_cols
    gridData = json_frame.to_json(orient="records")
    
    if allow_unsafe_jscode:
        walk_gridOptions(gridOptions, lambda v: v.js_code if isinstance(v, JsCode) else v )
    
    try:
        component_value = _component_func(
            gridOptions=gridOptions,
            gridData=gridData, key=key,
            default=None,
            height=height, 
            width=width,
            fit_columns_on_grid_load=fit_columns_on_grid_load, 
            update_mode=update_mode, 
            data_return_mode=data_return_mode, 
            frame_dtypes=frame_dtypes,
            allow_unsafe_jscode=allow_unsafe_jscode,
            enable_enterprise_modules=enable_enterprise_modules
            )
    except components.components.MarshallComponentException as ex:
        #a more complete error message.
        args = list(ex.args)
        args[0] += ". If you're using custom JsCode objects on gridOptions, ensure that allow_unsafe_jscode is True."
        ex = components.components.MarshallComponentException(*args)
        raise(ex)
        
        
    if component_value:
        
        frame = pd.DataFrame(component_value["gridData"])
        original_types = component_value["original_dtypes"]

        if not frame.empty:
            #maybe this is not the best solution. Should it store original types? What happens when grid pivots?
            #convert frame back to original types, except datetimes.
            if try_to_convert_back_to_original_types:
                numeric_columns = {k:v for k,v in original_types.items() if not v in ['i','u','f']}
                frame.loc[:,numeric_columns] = frame.loc[:,numeric_columns] .apply(pd.to_numeric, errors=conversion_errors)

                text_columns = {k:v for k,v in original_types.items() if not v in ['O','S','U']}
                frame.loc[:,text_columns]  = frame.loc[:,text_columns] .astype('string')

                date_columns = {k:v for k,v in original_types.items() if not v in ['M']}
                frame.loc[:,date_columns] = frame.loc[:,date_columns].apply(pd.to_datetime, errors=conversion_errors)

        response["data"] = frame
        response["selected_rows"] = component_value["selectedRows"]

    return response
