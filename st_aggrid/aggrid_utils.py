import os
import json
import pandas as pd
from typing import Any, Mapping, Tuple
from st_aggrid.grid_options_builder import GridOptionsBuilder
from st_aggrid.shared import JsCode, walk_gridOptions, GridUpdateMode

def cast_date_columns_to_iso8601(dataframe: pd.DataFrame):
    """Internal Method to convert tz-aware datetime columns to correct ISO8601 format"""
    for c, d in dataframe.dtypes.items():
        if d.kind == "M":
            dataframe[c] = dataframe[c].apply(lambda s: s.isoformat())


def parse_row_data(data) -> Tuple[Any, Any]:
    """Internal method to process data from data_parameter"""
    if data is None:
        return [], None

    if isinstance(data, pd.DataFrame):
        data_parameter = data.copy()
        cast_date_columns_to_iso8601(data_parameter)
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
        if data.endswith(".json") and os.path.exists(data):
            try:
                with open(os.path.abspath(data)) as f:
                    return json.loads(json.dumps(json.load(f))), None
            except Exception as ex:
                raise Exception(f"Error reading {data}. {ex}")
        try:
            return json.loads(data), None
        except Exception:
            raise Exception("Error parsing data parameter as raw json.")

    raise ValueError("Invalid data")


def parse_grid_options(
    gridOptions_parameter, data, default_column_parameters, unsafe_allow_jscode
):
    """Internal method to cast gridOptions parameter to a valid gridoptions"""
    if (gridOptions_parameter == None) and not (data is None):
        gb = GridOptionsBuilder.from_dataframe(data, **default_column_parameters)
        gridOptions = gb.build()
    elif isinstance(gridOptions_parameter, Mapping):
        gridOptions = gridOptions_parameter
    elif isinstance(gridOptions_parameter, str):
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
        walk_gridOptions(
            gridOptions, lambda v: v.js_code if isinstance(v, JsCode) else v
        )
    return gridOptions


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
