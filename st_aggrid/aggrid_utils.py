import os
import json
import pandas as pd

from typing import Any, Mapping, Tuple
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import JsCode, walk_gridOptions, GridUpdateMode
from io import StringIO
from pathlib import Path

def _parse_data_and_grid_options(
    data, grid_options, default_column_parameters, unsafe_allow_jscode, use_json_serialization
):
    column_types = None

    if data is not None:

        if isinstance(data, (str, Path)):
            if isinstance(data, Path):
                data = Path(data).resolve().absolute()

            #if data is a path to a json file. Validate and load it as string.
            if data.endswith(".json") and os.path.exists(data):
                try:
                    with open(os.path.abspath(data)) as f:
                        data = json.dumps(json.load(f))
                except Exception as ex:
                    raise Exception(f"Error reading {data}. {ex}")
                
            #if data is a json string load is as as data frame
            try:
                data = pd.read_json(StringIO(data))
            except Exception:
                raise Exception("Error parsing data parameter as raw json.")
        #handles the case where dataframe is a polars dataframe without add dependency on polars
        if (
            hasattr(data, '__class__') and 
            data.__class__.__module__ and
            'polars' in data.__class__.__module__ and
            data.__class__.__name__ == 'DataFrame'
        ):
            data = data.to_pandas(use_pyarrow_extension_array=False)

        if isinstance(data, pd.DataFrame):
            #converts date columns to iso format:
            for c, d in data.dtypes.items():
                if d.kind == "M":
                    data[c] = data[c].apply(lambda s: s.isoformat())
        
        #if there is data and no grid options, create grid options from the data
        if (data is not None) and (not grid_options):
            gb = GridOptionsBuilder.from_dataframe(data, **default_column_parameters)
            grid_options = gb.build()

        #computes rows data types before adding id column
        column_types = data.dtypes
    
    #if grid options is supplied as a dictionary, assume it is valid and use it
    elif isinstance(grid_options, Mapping):
        grid_options = grid_options

    elif isinstance(grid_options, (str, Path)):
        if isinstance(grid_options, Path):
            grid_options = Path(data).resolve().absolute()
        #if grid_options is a path to a json file. Validate and load it as dictionary.
        if grid_options.endswith(".json") and os.path.exists(grid_options):
            try:
                with open(os.path.abspath(grid_options)) as f:
                    grid_options = json.dumps(json.load(f))
            except Exception as ex:
                raise Exception(f"Error reading {grid_options}. {ex}")
        
        #if grid_options is a json string load is as as dict
        try:
            grid_options = json.loads(grid_options)
        except Exception:
            raise Exception("Error parsing data parameter as raw json.")
        
    
    #if data is supplied via gridOptions.rowData move it to data parameter
    if (grid_options.get('rowData', None)) and use_json_serialization is not True:
        if data:
            raise ValueError("Data was supplied by both data and gridOptions rowData. Use only one to load data into the grid.")
        else:
            data = grid_options.pop("rowData")
            data = pd.read_json(StringIO(data))


    #if rowId is not defined, create an unique row_id as the rows_hash
    if "getRowId" not in grid_options and data is not None:
        data['::auto_unique_id::'] = list(map(str, range(data.shape[0]))) ##pd.util.hash_pandas_object(data).astype(str)

    if use_json_serialization is True:
        grid_options['rowData'] = data.to_json(orient='records')
        data = None
        
    #process the JsCode Objects
    if unsafe_allow_jscode:
        walk_gridOptions(
            grid_options, lambda v: v.js_code if isinstance(v, JsCode) else v
        )
    
    return data, grid_options, column_types

def parse_update_mode(update_mode: GridUpdateMode, update_on=None):
    def add_unique_update_event(update_on, event):
        if event not in update_on:
            update_on.append(event)
    if update_on is None:
        update_on = []

    if update_mode & GridUpdateMode.VALUE_CHANGED:
        add_unique_update_event(update_on, "cellValueChanged")
    if update_mode & GridUpdateMode.SELECTION_CHANGED:
        add_unique_update_event(update_on, "selectionChanged")
    if update_mode & GridUpdateMode.FILTERING_CHANGED:
        add_unique_update_event(update_on, "filterChanged")
    if update_mode & GridUpdateMode.SORTING_CHANGED:
        add_unique_update_event(update_on, "sortChanged")
    if update_mode & GridUpdateMode.COLUMN_RESIZED:
        add_unique_update_event(update_on, ("columnResized", 300))
    if update_mode & GridUpdateMode.COLUMN_MOVED:
        add_unique_update_event(update_on, ("columnMoved", 500))
    if update_mode & GridUpdateMode.COLUMN_PINNED:
        add_unique_update_event(update_on, "columnPinned")
    if update_mode & GridUpdateMode.COLUMN_VISIBLE:
        add_unique_update_event(update_on, "columnVisible")
    return update_on
