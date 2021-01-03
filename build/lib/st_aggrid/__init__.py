import os
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import json

from st_aggrid.grid_options_builder import GridOptionsBuilder

from enum import IntEnum
class GridUpdateMode(IntEnum):
    NO_UPDATE = 0b0000
    MANUAL = 0b0001
    VALUE_CHANGED = 0b0010
    SELECTION_CHANGED = 0b0100
    FILTERING_CHANGED = 0b1000
    SORTING_CHANGED = 0b10000
    MODEL_CHANGED = 0b11111

class DataReturnMode(IntEnum):
    AS_INPUT = 0
    FILTERED = 1
    FILTERED_AND_SORTED = 2

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


def AgGrid(dataframe, gridOptions=None, height=200,fit_columns_on_grid_load=False, update_mode=GridUpdateMode.VALUE_CHANGED, data_return_mode=DataReturnMode.AS_INPUT,  key=None):
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

    component_value = _component_func(gridOptions=gridOptions, gridData=gridData, key=key, default=None, height=height, fit_columns_on_grid_load=fit_columns_on_grid_load, update_mode=update_mode, data_return_mode=data_return_mode, frame_dtypes=frame_dtypes)
    if component_value:
        
        frame = pd.DataFrame(component_value["gridData"])
        original_types = component_value["original_dtypes"]

        if not frame.empty:
            #maybe this is not the best solution. Should it store original types? What happens when grid pivots?
            #convert frame back to original types, except datetimes.
            non_date_cols = {k:v for k,v in original_types.items() if not v == "M"}
            frame = frame.astype(non_date_cols)
            
            #this is the hack to convert back tz aware iso dates to pandas dtypes'
            date_cols = set(frame.columns) - set(non_date_cols.keys())
            frame.loc[:, date_cols] = frame.loc[:, date_cols].apply(pd.to_datetime)

        response["data"] = frame
        response["selected_rows"] = component_value["selectedRows"]

    return response
