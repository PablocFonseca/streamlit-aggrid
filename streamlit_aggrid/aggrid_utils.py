import hashlib
import json
import logging
import os
from collections.abc import Mapping
from datetime import date, datetime, time
from decimal import Decimal
from pathlib import Path
from uuid import UUID

import pandas as pd

from streamlit_aggrid.grid_options_builder import GridOptionsBuilder
from streamlit_aggrid.shared import JsCode, walk_gridOptions, GridUpdateMode
from io import StringIO


def _copy_grid_option_containers(value):
    """Copy JSON-like containers while preserving special leaf objects."""
    if isinstance(value, Mapping):
        return {key: _copy_grid_option_containers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_copy_grid_option_containers(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_copy_grid_option_containers(item) for item in value)
    return value


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
            # Parsing adds the internal row-ID column and may normalize date
            # columns. A shallow frame copy keeps those assignments private to
            # the component without duplicating every underlying data block.
            data = data.copy(deep=False)
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

    elif grid_options is not None:
        # rowData is popped and nested JsCode leaves are replaced below. Keep
        # those implementation details from mutating the caller's options.
        grid_options = {
            key: (
                value
                if key == "rowData"
                else _copy_grid_option_containers(value)
            )
            for key, value in grid_options.items()
        }

    if grid_options is None:
        grid_options = {}

    # Normalize gridOptions.rowData through the same DataFrame path as data=.
    # This keeps Arrow/JSON modes consistent and detects dual sources even for
    # empty row arrays (whose truth value is false).
    if "rowData" in grid_options:
        row_data = grid_options.pop("rowData")
        if data is not None and row_data is not None:
            raise ValueError(
                "Data was supplied by both data and gridOptions rowData. "
                "Use only one to load data into the grid."
            )
        if data is None and row_data is not None:
            if isinstance(row_data, str):
                data = pd.read_json(StringIO(row_data))
            else:
                data = pd.DataFrame(row_data)

    # if rowId is not defined, create a unique row id
    if "getRowId" not in grid_options and data is not None:
        data['::auto_unique_id::'] = list(map(str, range(data.shape[0])))

    # process the JsCode objects
    if unsafe_allow_jscode:
        walk_gridOptions(
            grid_options, lambda v: v.js_code if isinstance(v, JsCode) else v
        )

    return data, grid_options


def _normalize_hash_value(value):
    """Convert common row values to a deterministic JSON-compatible shape."""
    if value is None:
        return None
    if value is pd.NA or value is pd.NaT:
        return {"__missing__": type(value).__name__}
    if isinstance(value, dict):
        items = [
            [_normalize_hash_value(key), _normalize_hash_value(item)]
            for key, item in value.items()
        ]
        items.sort(
            key=lambda pair: json.dumps(
                pair[0], sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
        )
        return {"__mapping__": items}
    if isinstance(value, (list, tuple)):
        return [_normalize_hash_value(item) for item in value]
    if isinstance(value, (set, frozenset)):
        items = [_normalize_hash_value(item) for item in value]
        items.sort(
            key=lambda item: json.dumps(
                item, sort_keys=True, separators=(",", ":"), ensure_ascii=False
            )
        )
        return {"__set__": items}
    if isinstance(value, (pd.Timestamp, pd.Timedelta, datetime, date, time)):
        return {"__type__": type(value).__name__, "value": value.isoformat()}
    if isinstance(value, (Decimal, UUID)):
        return {"__type__": type(value).__name__, "value": str(value)}
    if isinstance(value, bytes):
        return {"__bytes__": value.hex()}
    if isinstance(value, float):
        if pd.isna(value):
            return {"__float__": "nan"}
        if value == float("inf"):
            return {"__float__": "inf"}
        if value == float("-inf"):
            return {"__float__": "-inf"}
        return value
    if isinstance(value, (str, int, bool)):
        return value

    # NumPy and Arrow scalar objects generally expose a stable Python scalar.
    item_method = getattr(value, "item", None)
    if callable(item_method):
        try:
            scalar = item_method()
            if scalar is not value:
                return _normalize_hash_value(scalar)
        except (TypeError, ValueError, OverflowError):
            pass

    return {
        "__type__": f"{type(value).__module__}.{type(value).__qualname__}",
        "value": str(value),
    }


def _canonical_json_bytes(value):
    normalized = _normalize_hash_value(value)
    return json.dumps(
        normalized,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def compute_data_hash(data):
    """Return an order-sensitive content signature for component row data.

    DataFrames use pandas' stable vectorized row hashing and include schema
    metadata. JSON rowData is canonicalized so insignificant whitespace and
    mapping-key order do not change the signature, while row order does.
    """
    if data is None:
        return None

    digest = hashlib.sha256()

    if isinstance(data, pd.DataFrame):
        digest.update(b"streamlit-aggrid:dataframe:v1\0")
        try:
            metadata = {
                "columns": [_normalize_hash_value(column) for column in data.columns],
                "dtypes": [str(dtype) for dtype in data.dtypes],
                "shape": list(data.shape),
            }
            digest.update(_canonical_json_bytes(metadata))
            digest.update(b"\0")
            # Pandas indices are removed by the frontend Arrow parser, so hash
            # only the row values that AG Grid actually receives.
            row_hashes = pd.util.hash_pandas_object(data, index=False)
            # Pin byte order so the digest is stable across architectures.
            digest.update(row_hashes.to_numpy(dtype="uint64").astype("<u8").tobytes())
        except (TypeError, ValueError, AttributeError) as ex:
            logging.warning(
                "DataFrame contains values unsupported by pandas hashing; "
                "using deterministic JSON hashing instead: %s",
                ex,
            )
            fallback = {
                "columns": [_normalize_hash_value(column) for column in data.columns],
                "dtypes": [str(dtype) for dtype in data.dtypes],
                "data": [
                    [_normalize_hash_value(value) for value in row]
                    for row in data.itertuples(index=False, name=None)
                ],
            }
            digest.update(_canonical_json_bytes(fallback))
        return digest.hexdigest()

    digest.update(b"streamlit-aggrid:row-data:v1\0")
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except (TypeError, ValueError, json.JSONDecodeError):
            pass
    digest.update(_canonical_json_bytes(data))
    return digest.hexdigest()


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
