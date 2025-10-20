from typing import Mapping
from st_aggrid.shared import DataReturnMode

import json
import pandas as pd
import numpy as np
import inspect
import re
import warnings


class AgGridReturn(Mapping):
    """
    Container for AgGrid component response data.

    Provides easy access to grid data, selected rows, grid state, and other
    information returned by the AgGrid component.
    """

    def __init__(
        self,
        originalData,
        grid_response={},
        data_return_mode=DataReturnMode.AS_INPUT,
        conversion_errors="coerce",
        frame_dtypes=None,
    ) -> None:
        super().__init__()

        # Configuration
        self._original_data = originalData
        self._data_return_mode = data_return_mode
        self._conversion_errors = conversion_errors

        # State
        self._component_value_set = grid_response is True
        self.__dict__["grid_response"] = grid_response
        self.frame_dtypes = frame_dtypes

    def _set_component_value(self, component_value):
        """Set the response value from the AgGrid component."""
        self._component_value_set = True
        self.__dict__["grid_response"] = component_value

        # Ensure gridOptions is a dict
        grid_options = self.__dict__["grid_response"].get("gridOptions")
        if grid_options and not isinstance(grid_options, dict):
            self.__dict__["grid_response"]["gridOptions"] = json.loads(grid_options)

    # ==========================================
    # Basic Properties - Direct Grid Response Access
    # ==========================================

    @property
    def grid_response(self):
        """Raw response from component."""
        return self.__dict__["grid_response"]

    @property
    def rows_id_after_sort_and_filter(self):
        """The row indexes after sort and filter is applied"""
        return self.grid_response.get("rowIdsAfterSortAndFilter")

    @property
    def rows_id_after_filter(self):
        """The filtered row indexes"""
        return self.grid_response.get("rowIdsAfterFilter")

    @property
    def grid_options(self):
        """GridOptions as applied on the grid."""
        return self.grid_response.get("gridOptions", {})

    @property
    def columns_state(self):
        """Gets the state of the columns. Typically used when saving column state."""
        return self.grid_response.get("columnsState")

    @property
    def grid_state(self):
        """Gets the grid state. Tipically used on initialState option. (https://ag-grid.com/javascript-data-grid//grid-options/#reference-miscellaneous-initialState)"""
        return self.grid_response.get("gridState")

    @property
    def selected_rows_id(self):
        """Ids of selected rows"""
        return self.grid_state.get("rowSelection")

    # ==========================================
    # Helper Methods - Data Processing
    # ==========================================

    def _convert_column_types(self, data):
        """Convert DataFrame columns back to their original types.

        Args:
            data: DataFrame with columns to convert

        Returns:
            DataFrame with columns converted to original types
        """
        converted_columns = []

        for col_name in data.columns:
            column = data[col_name]

            # Keep UI-created columns as-is (they don't have original dtypes)
            if col_name not in self.frame_dtypes:
                converted_columns.append(column)
                continue

            original_dtype = self.frame_dtypes[col_name]
            dtype_kind = original_dtype.kind

            # Convert based on original dtype kind
            if dtype_kind == "i":  # Integer
                converted_columns.append(
                    self._convert_to_integer(column)
                )
            elif dtype_kind == "f":  # Float
                converted_columns.append(
                    pd.to_numeric(column, errors=self._conversion_errors).astype(
                        original_dtype, copy=False
                    )
                )
            elif dtype_kind in ("O", "S", "U"):  # Object/String/Unicode
                converted_columns.append(
                    column.astype(original_dtype, copy=False)
                )
            elif dtype_kind == "M":  # Datetime
                converted_columns.append(
                    pd.to_datetime(column, errors=self._conversion_errors).astype(
                        original_dtype, copy=False
                    )
                )
            elif dtype_kind == "m":  # Timedelta
                converted_columns.append(
                    self._convert_to_timedelta(column, original_dtype)
                )
            else:  # Other types
                converted_columns.append(
                    column.astype(original_dtype)
                )

        return pd.concat(converted_columns, axis=1, copy=False)

    def _convert_to_integer(self, column):
        """Convert column to Int64, falling back to Float64 on errors.

        Args:
            column: Series to convert

        Returns:
            Series converted to Int64 or Float64
        """
        try:
            return pd.to_numeric(
                column, downcast="integer", errors="coerce"
            ).astype("Int64", copy=False)
        except TypeError:
            warnings.warn(
                f"Error casting {column.name} to Int64. Falling back to Float64"
            )
            return pd.to_numeric(column, errors="coerce").astype(
                "Float64", copy=False
            )

    def _convert_to_timedelta(self, column, original_dtype):
        """Convert column to timedelta, handling errors gracefully.

        Args:
            column: Series to convert
            original_dtype: Target dtype for the column

        Returns:
            Series converted to timedelta
        """
        def safe_timedelta(value):
            """Convert value to Timedelta, returning original on error."""
            try:
                return pd.Timedelta(value)
            except (ValueError, TypeError, pd.errors.OutOfBoundsDatetime):
                return value

        return column.apply(safe_timedelta).astype(original_dtype, copy=False)

    def _create_dataframe_from_nodes(self, nodes):
        """Create a DataFrame from grid nodes."""
        # Extract data from non-group nodes
        data = pd.DataFrame(
            [n.get("data", {}) for n in nodes if not n.get("group", False)],
            dtype=object,
        )

        # Set index from auto_unique_id if available
        if "::auto_unique_id::" in data.columns:
            data.index = pd.Index(data["::auto_unique_id::"], name="index")
            # Remove the internal column - it's only used for indexing
            data = data.drop(columns=["::auto_unique_id::"])

        if self.frame_dtypes is not None:
            data = self._convert_column_types(data)
        return data

    def _process_grouped_response(self, nodes):
        """Process nodes with grouping information."""
        # Create data with parent information
        data_rows = []
        for node in nodes:
            if not node.get("group", False):  # Only leaf nodes
                parent_path = node.get("parentPath", "")
                row_data = {**node.get("data", {}), "parentPath": parent_path}
                data_rows.append(row_data)

        # Set index and clean up
        data = pd.DataFrame(data_rows)
        if "::auto_unique_id::" in data.columns:
            data = data.set_index("::auto_unique_id::")
            # Apply filtering and sorting if needed
            data = self._apply_filtering_and_sorting(data, only_selected=False)
            data.index.name = ""

        # Group by parent path and parse AG-Grid IDs for meaningful group names
        # Use sort=False to preserve original order and improve performance
        groups = []
        for parent_path, group_data in data.groupby("parentPath", sort=False):
            group_key = self._parse_aggrid_group_ids(parent_path)
            clean_data = group_data.drop("parentPath", axis=1)
            groups.append({group_key: clean_data})

        return groups

    def _parse_aggrid_group_ids(self, parent_path: str) -> tuple:
        """Parse AG-Grid auto-generated IDs to extract meaningful group names.

        Based on actual observed structure:
        Example: "ROOT_NODE_ID.row-group-sport-Swimming.row-group-sport-Swimming-athlete-Michael Phelps"

        Pattern analysis:
        - Level 1: "row-group-sport-Swimming" -> key is "Swimming"
        - Level 2: "row-group-sport-Swimming-athlete-Michael Phelps" -> new key is "Michael Phelps"

        Each level adds: -{colId}-{key} to the previous path
        We need to extract just the keys in order: ("Swimming", "Michael Phelps")
        """
        if not parent_path:
            return ()

        # Remove ROOT_NODE_ID prefix if present
        if parent_path.startswith("ROOT_NODE_ID."):
            parent_path = parent_path[13:]  # len("ROOT_NODE_ID.") = 13

        # Split by dots to get each level
        parts = parent_path.split(".")
        group_keys = []

        for i, part in enumerate(parts):
            if part.startswith("row-group-"):
                # Remove 'row-group-' prefix
                content = part[10:]  # len('row-group-') = 10

                if not content:
                    continue

                if i == 0:
                    # First level: row-group-{colId}-{key}
                    # Find the first dash and take everything after it
                    first_dash = content.find("-")
                    if first_dash > 0:
                        key = content[first_dash + 1 :]
                        group_keys.append(key)
                else:
                    # Subsequent levels contain the full path: {previousPath}-{colId}-{key}
                    # We need to find what's new compared to the previous level

                    # Get the previous part to compare
                    prev_part = parts[i - 1]
                    if prev_part.startswith("row-group-"):
                        prev_content = prev_part[10:]

                        # The current content should start with prev_content
                        # followed by -{colId}-{key}
                        if content.startswith(prev_content):
                            # Extract the new part: -{colId}-{key}
                            new_part = content[len(prev_content) :]
                            if new_part.startswith("-"):
                                new_part = new_part[1:]  # Remove leading dash

                                # Find the next dash (after colId) and extract key
                                dash_pos = new_part.find("-")
                                if dash_pos > 0:
                                    key = new_part[dash_pos + 1 :]
                                    group_keys.append(key)
                                else:
                                    # No dash found, the whole thing is the key
                                    group_keys.append(new_part)
                        else:
                            # Fallback: extract the last key-like segment
                            segments = content.split("-")
                            if len(segments) >= 2:
                                group_keys.append(segments[-1])

        return tuple(group_keys)

    def _get_data(self, only_selected=False):
        """Get data from the grid, optionally filtering to selected rows only."""
        if not self._component_value_set:
            return None if only_selected else self._original_data

        nodes = self.grid_response.get("nodes", [])

        # Filter to selected nodes if requested
        if only_selected:
            nodes = [n for n in nodes if n.get("isSelected", False)]
            if not nodes:
                return None

        # Handle DataFrame data
        if (
            isinstance(self._original_data, pd.DataFrame)
            and not self._original_data.empty
        ):
            data = self._create_dataframe_from_nodes(nodes)
            return self._apply_filtering_and_sorting(data, only_selected)

        # Handle JSON/string data or empty DataFrame
        if self._should_return_json_data():
            return self._create_json_response(nodes)

        return self._original_data if not only_selected else None

    def _apply_filtering_and_sorting(self, data, only_selected):
        """Apply grid filtering and sorting to the data."""
        # Get the appropriate row IDs based on data return mode
        if self._data_return_mode == DataReturnMode.FILTERED:
            reindex_ids = self.rows_id_after_filter
        elif self._data_return_mode == DataReturnMode.FILTERED_AND_SORTED:
            reindex_ids = self.rows_id_after_sort_and_filter
        else:
            reindex_ids = None

        if reindex_ids:
            reindex_ids = pd.Index(reindex_ids)
            if only_selected:
                reindex_ids = reindex_ids.intersection(data.index)

            data = data.reindex(index=reindex_ids).reset_index(drop=True)

            # Remove auto_unique_id column if present
            columns = [col for col in data.columns if col != "::auto_unique_id::"]
            return data[columns]

        return data

    def _should_return_json_data(self):
        """Check if we should return JSON data instead of DataFrame."""
        data = self._original_data
        return (
            (isinstance(data, str) and self._is_valid_json(data))
            or (isinstance(data, pd.DataFrame) and data.empty)
            or (data is None)
        )

    def _is_valid_json(self, data_str):
        """Check if a string is valid JSON."""
        try:
            json.loads(data_str)
            return True
        except (json.JSONDecodeError, TypeError):
            return False

    def _create_json_response(self, nodes):
        """Create JSON response from nodes."""
        if self._data_return_mode == DataReturnMode.FILTERED:
            filter_ids = self.rows_id_after_filter or []
        elif self._data_return_mode == DataReturnMode.FILTERED_AND_SORTED:
            filter_ids = self.rows_id_after_sort_and_filter or []
        else:
            filter_ids = None

        sorted_nodes = sorted(nodes, key=lambda n: n.get("rowIndex", 0))

        if filter_ids:
            data_list = [n["data"] for n in sorted_nodes if n["id"] in filter_ids]
        else:
            data_list = [n["data"] for n in sorted_nodes]

        # Remove internal columns from each data item
        data_list = [
            {k: v for k, v in item.items() if not k.startswith("::")}
            for item in data_list
        ]

        return json.dumps(data_list)

    # ==========================================
    # Main Data Access Properties
    # ==========================================

    @property
    def data(self):
        """Data from the grid. If rows are grouped, return only the leaf rows."""
        return self._get_data(only_selected=False)

    @property
    def selected_data(self):
        """Selected data from the grid."""
        return self._get_data(only_selected=True)

    def _get_data_groups(self, only_selected=False):
        """Get grouped data from the grid."""
        if not self._component_value_set:
            return [{(): pd.DataFrame()}]

        nodes = self.grid_response.get("nodes", [])

        if only_selected:
            # Default is True because AgGrid sets undefined for half-selected groups
            nodes = [n for n in nodes if n.get("isSelected", True)]
            if not nodes:
                fallback_data = self._get_data(only_selected)
                return [{(): fallback_data}]

        # Check if response has groups
        has_groups = any(n.get("group", False) for n in nodes)

        if has_groups:
            # Additional safety check: ensure we have leaf nodes with parent paths
            leaf_nodes = [n for n in nodes if not n.get("group", False)]
            leaf_with_parent_path = [n for n in leaf_nodes if n.get("parentPath")]

            if leaf_with_parent_path:
                return self._process_grouped_response(nodes)
            else:
                # Has groups but no proper parent paths - fall back to regular data
                print(
                    "Warning: Grouped data detected but no parentPath found in leaf nodes. Falling back to regular data."
                )

        # No groups or invalid grouped data - return single group with all data
        fallback_data = self._get_data(only_selected)
        return [{(): fallback_data}]

    @property
    def dataGroups(self):
        """
        Returns grouped rows as a dictionary where keys are tuples of
        groupby strings and values are pandas.DataFrame.
        """
        return self._get_data_groups(only_selected=False)

    @property
    def selected_dataGroups(self):
        """
        Returns selected rows as a dictionary where keys are tuples of
        grouped column names and values are pandas.DataFrame.
        """
        return self._get_data_groups(only_selected=True)

    @property
    def selected_rows(self):
        """
        Returns selected rows as a DataFrame.
        If there are grouped rows, returns a dict of {key: pd.DataFrame}.
        """
        nodes = self.grid_response.get("nodes", [])
        selected_items = pd.DataFrame(
            [n.get("data", None) for n in nodes if n.get("isSelected", None) is True]
        )

        if selected_items.empty:
            return None

        # Set pandas index if available and remove the internal column
        if "::auto_unique_id::" in selected_items.columns:
            selected_items.set_index("::auto_unique_id::", inplace=True)
            selected_items.index.name = "index"

        return selected_items

    @property
    def event_data(self):
        """Returns information about the event that triggered AgGrid response."""
        return self.grid_response.get("eventData", None)

    # ==========================================
    # Dictionary Interface for Backwards Compatibility
    # ==========================================
    def __getitem__(self, key):
        """Get item using dict-like access."""
        # Try to get as attribute first
        try:
            return getattr(self, key)
        except AttributeError:
            pass

        # Try to get from grid_response
        grid_response = self.__dict__.get("grid_response", {})
        if isinstance(grid_response, dict) and key in grid_response:
            return grid_response[key]

        # Fall back to __dict__ access
        return self.__dict__[key]

    def __iter__(self):
        """Iterate over public attributes."""
        return (
            name for name, _ in inspect.getmembers(self) if not name.startswith("_")
        )

    def __len__(self):
        """Return number of public attributes."""
        return len(
            [name for name, _ in inspect.getmembers(self) if not name.startswith("_")]
        )

    def keys(self):
        """Return all available keys (attributes + grid_response keys)."""
        # Get public attribute names
        attr_keys = [
            name for name, _ in inspect.getmembers(self) if not name.startswith("_")
        ]

        # Get grid_response keys for backward compatibility
        grid_response = self.__dict__.get("grid_response", {})
        if isinstance(grid_response, dict):
            grid_keys = [k for k in grid_response.keys() if k not in attr_keys]
            return attr_keys + grid_keys

        return attr_keys

    def values(self):
        """Return all values for public attributes."""
        return [value for _, value in inspect.getmembers(self) if not _.startswith("_")]
