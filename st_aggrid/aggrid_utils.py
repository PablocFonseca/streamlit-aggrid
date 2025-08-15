import os
import json
import pandas as pd

from typing import Any, Mapping, Tuple
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import JsCode, walk_gridOptions, GridUpdateMode
from io import StringIO


def _parse_data_and_grid_options(
    data, grid_options, default_column_parameters, unsafe_allow_jscode
):

    if isinstance(data, str):
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

    if isinstance(data, pd.DataFrame):
        #converts date columns to iso format:
        for c, d in data.dtypes.items():
            if d.kind == "M":
                data[c] = data[c].apply(lambda s: s.isoformat())
    
    #if there is data and no grid options, create grid options from the data
    if (data is not None) and (not grid_options):
        gb = GridOptionsBuilder.from_dataframe(data, **default_column_parameters)
        grid_options = gb.build()

    #if grid options is supplied as a dictionary, assume it is valid and use it
    elif isinstance(grid_options, Mapping):
        grid_options = grid_options

    elif isinstance(grid_options, str):
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
    if (grid_options.get('rowData', None)):
        if data:
            raise ValueError("Data was supplied by both data and gridOptions rowData. Use only one to load data into the grid.")
        else:
            data = grid_options.pop("rowData")
            data = pd.read_json(StringIO(data))

    #if rowId is not defined, create an unique row_id as the rows_hash
    if "getRowId" not in grid_options and data is not None:
        data['::auto_unique_id::'] = list(map(str, range(data.shape[0]))) ##pd.util.hash_pandas_object(data).astype(str)

            
    #process the JsCode Objects
    if unsafe_allow_jscode:
        walk_gridOptions(
            grid_options, lambda v: v.js_code if isinstance(v, JsCode) else v
        )
    
    return data, grid_options

def parse_update_mode(update_mode: GridUpdateMode):
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
