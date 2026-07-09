import json
import logging
import os
import pandas as pd

from streamlit_aggrid.grid_options_builder import GridOptionsBuilder
from streamlit_aggrid.shared import JsCode, walk_gridOptions, GridUpdateMode
from io import StringIO
from pathlib import Path


def _load_json_file(path: Path) -> str:
    """Read a .json file and return its content as a normalized json string."""
    path = path.resolve().absolute()
    if not (path.exists() and path.suffix == ".json"):
        raise ValueError(f"Path {path} is not a valid json file.")
    try:
        return json.dumps(json.loads(path.read_text()))
    except Exception as ex:
        raise ValueError(f"Error reading {path}. {ex}") from ex


def _parse_data_and_grid_options(
    data, grid_options, default_column_parameters, unsafe_allow_jscode, use_json_serialization
):
    if data is not None:
        if isinstance(data, (str, Path)):
            # data is a path to a json file
            if isinstance(data, str) and Path(data).suffix == ".json":
                data = Path(data)

            if isinstance(data, Path):
                data = _load_json_file(data)

            # if data is a json string load it as a data frame
            try:
                data = pd.read_json(StringIO(data))
            except Exception as ex:
                raise ValueError(f"Error parsing data parameter as raw json. {ex}") from ex

        # handles the case where dataframe is a polars dataframe without adding a dependency on polars
        if (
            hasattr(data, '__class__') and
            data.__class__.__module__ and
            'polars' in data.__class__.__module__ and
            data.__class__.__name__ == 'DataFrame'
        ):
            data = data.to_pandas(use_pyarrow_extension_array=False)

        if isinstance(data, pd.DataFrame):
            # converts date columns to iso format:
            for c, d in data.dtypes.items():
                if d.kind == "M":
                    data[c] = data[c].apply(lambda s: s.isoformat())

        # if there is data and no grid options, create grid options from the data
        if not grid_options:
            gb = GridOptionsBuilder.from_dataframe(data, **default_column_parameters)
            grid_options = gb.build()

    if isinstance(grid_options, (str, Path)):
        # grid_options is a path to a json file or a raw json string
        if isinstance(grid_options, str) and Path(grid_options).suffix == ".json" and os.path.exists(grid_options):
            grid_options = Path(grid_options)

        if isinstance(grid_options, Path):
            grid_options = _load_json_file(grid_options)

        try:
            grid_options = json.loads(grid_options)
        except Exception as ex:
            raise ValueError(f"Error parsing gridOptions parameter as raw json. {ex}") from ex

    if grid_options is None:
        grid_options = {}

    # if data is supplied via gridOptions.rowData move it to the data parameter
    if grid_options.get('rowData') and use_json_serialization is not True:
        if data is not None:
            raise ValueError(
                "Data was supplied by both data and gridOptions rowData. "
                "Use only one to load data into the grid."
            )
        row_data = grid_options.pop("rowData")
        if isinstance(row_data, str):
            data = pd.read_json(StringIO(row_data))
        else:
            data = pd.DataFrame(row_data)

    # if rowId is not defined, create a unique row id
    if "getRowId" not in grid_options and data is not None:
        data['::auto_unique_id::'] = list(map(str, range(data.shape[0])))

    if use_json_serialization is True and data is not None:
        grid_options['rowData'] = data.to_json(orient='records')
        data = None

    # process the JsCode objects
    if unsafe_allow_jscode:
        walk_gridOptions(
            grid_options, lambda v: v.js_code if isinstance(v, JsCode) else v
        )

    return data, grid_options


def compute_data_hash(df):
    """Hash a DataFrame so the frontend can detect data changes between reruns."""
    if df is None:
        return None

    try:
        return str(pd.util.hash_pandas_object(df).sum())
    except TypeError:
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
