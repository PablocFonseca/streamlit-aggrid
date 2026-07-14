"""
Container for AgGrid component response data.

This module provides the AgGridReturn class, which is a simplified data container
for accessing grid data, selected rows, grid state, and other information returned
by the AgGrid component.
"""

from collections.abc import Mapping
from typing import Any, Dict, List, Optional, TypedDict

import pandas as pd

from streamlit_aggrid.shared import DataReturnMode


class GridResponse(TypedDict, total=False):
    """TypedDict for the grid response structure from the frontend."""

    nodes: List[Dict[str, Any]]
    gridOptions: Optional[Dict[str, Any]]
    gridState: Optional[Dict[str, Any]]
    columnsState: Optional[Dict[str, Any]]
    rowIdsAfterFilter: Optional[List[Any]]
    rowIdsAfterSortAndFilter: Optional[List[Any]]
    eventData: Dict[str, Any]


class AgGridReturn(Mapping):
    """
    Container for AgGrid component response data.

    Provides easy access to grid data, selected rows, grid state, and other
    information returned by the AgGrid component.

    This class maintains backward compatibility by implementing the Mapping interface,
    but the recommended way to access data is through the provided methods and properties.
    """

    def __init__(
        self,
        grid_response=None,
        data_return_mode=DataReturnMode.AS_INPUT,
        original_data: Optional[pd.DataFrame] = None,
    ) -> None:
        """Initialize AgGridReturn with the component response.

        Args:
            grid_response: The response from the AgGrid component (a mapping
                with a 'grid_response' key).
            data_return_mode: How the data property is shaped (see DataReturnMode).
            original_data: Input data returned before the frontend has emitted
                its first legacy grid response.
        """
        if isinstance(data_return_mode, str):
            data_return_mode = DataReturnMode(data_return_mode.upper())

        # Component V2 returns a flat state mapping whose ``grid_response``
        # value is whatever the selected collector produced.  CUSTOM collectors
        # may legitimately return any JSON value, including falsy values, so do
        # not normalize the payload with ``or {}``.
        if grid_response is None:
            self.grid_response: Any = {}
        elif isinstance(grid_response, AgGridReturn):
            self.grid_response = grid_response.grid_response
            if original_data is None:
                original_data = grid_response._original_data
        elif isinstance(grid_response, Mapping):
            self.grid_response = grid_response.get("grid_response", {})
        else:
            self.grid_response = {}
        self.data_return_mode = data_return_mode
        self._original_data = original_data

    def _response_mapping(self) -> Mapping[str, Any]:
        """Return a mapping view for legacy accessors.

        A CUSTOM collector is allowed to return a list, scalar, or ``None``.
        Those payloads remain available through ``grid_response``/``raw_data``;
        legacy grid-state accessors simply behave as if no legacy response was
        returned.
        """
        if isinstance(self.grid_response, Mapping):
            return self.grid_response
        return {}

    # ==========================================
    # Basic Properties - Direct Grid Response Access
    # ==========================================

    @property
    def rows_id_after_sort_and_filter(self) -> Optional[List[Any]]:
        """The row indexes after sort and filter is applied."""
        return self._response_mapping().get("rowIdsAfterSortAndFilter")

    @property
    def rows_id_after_filter(self) -> Optional[List[Any]]:
        """The filtered row indexes."""
        return self._response_mapping().get("rowIdsAfterFilter")

    @property
    def grid_options(self) -> Dict[str, Any]:
        """GridOptions as applied on the grid."""
        value = self._response_mapping().get("gridOptions", {})
        return value if isinstance(value, dict) else {}

    @property
    def columns_state(self) -> Optional[Dict[str, Any]]:
        """Gets the state of the columns. Typically used when saving column state."""
        return self._response_mapping().get("columnsState")

    @property
    def grid_state(self) -> Optional[Dict[str, Any]]:
        """Gets the grid state. Typically used on initialState option.

        See: https://ag-grid.com/javascript-data-grid/grid-options/#reference-miscellaneous-initialState
        """
        return self._response_mapping().get("gridState")

    @property
    def selected_rows_id(self) -> Optional[List[Any]]:
        """IDs of selected rows."""
        grid_state = self.grid_state
        if isinstance(grid_state, Mapping):
            return grid_state.get("rowSelection")
        return None

    @property
    def event_data(self) -> Dict[str, Any]:
        """Returns information about the event that triggered AgGrid response."""
        value = self._response_mapping().get("eventData", {})
        return value if isinstance(value, dict) else {}

    @property
    def raw_data(self) -> Any:
        """The unmodified collector payload.

        This is a compatibility alias for the ``CustomResponse.raw_data`` API
        used by streamlit-aggrid 1.x.
        """
        return self.grid_response

    # ==========================================
    # Data Access Methods
    # ==========================================

    @property
    def data(self) -> Optional[pd.DataFrame | str]:
        if self.data_return_mode == DataReturnMode.CUSTOM:
            return None

        data = self._get_data(
            selected_only=False, data_return_mode=self.data_return_mode
        )

        return None if data.empty else data

    @property
    def selected_data(self) -> Optional[pd.DataFrame | str]:
        if self.data_return_mode == DataReturnMode.CUSTOM:
            return None

        data = self._get_data(
            selected_only=True, data_return_mode=self.data_return_mode
        )
        return None if data.empty else data

    @property
    def selected_rows(self) -> Optional[pd.DataFrame | str]:
        """Alias for selected_data for backward compatibility with old API."""
        return self.selected_data

    @property
    def dataGroups(self) -> Dict[tuple, pd.DataFrame]:
        """
        Returns grouped rows as a dict where keys are tuples of group values
        and values are pandas.DataFrame.

        Example:
            When data is grouped by 'sport' and 'athlete', returns:
            {
                ('Swimming',): DataFrame(...),           # All Swimming rows
                ('Swimming', 'Michael Phelps'): DataFrame(...),  # Specific athlete
                ('Gymnastics',): DataFrame(...),         # All Gymnastics rows
                ...
            }

        Usage:
            # Simple iteration
            for group_key, group_df in response.dataGroups.items():
                print(f"{group_key}: {len(group_df)} rows")

            # Direct access
            swimming_data = response.dataGroups[('Swimming',)]

            # Filter by group level
            sports = {k: v for k, v in response.dataGroups.items() if len(k) == 1}
        """
        if self.data_return_mode in (DataReturnMode.CUSTOM, DataReturnMode.MINIMAL):
            return {}

        groups = {}
        for group_dict in self._get_data_groups(only_selected=False):
            groups.update(group_dict)
        return groups

    @property
    def selected_dataGroups(self) -> Dict[tuple, pd.DataFrame]:
        """
        Returns selected grouped rows as a dict where keys are tuples of
        group values and values are pandas.DataFrame.

        Only returns rows/groups that are selected in the grid.

        Example:
            {
                ('North',): DataFrame(...),                    # Selected North rows
                ('North', 'Product A'): DataFrame(...),        # Selected North Product A
                ('South', 'Product B', 'Blue'): DataFrame(...),  # Selected specific item
            }
        """
        if self.data_return_mode in (DataReturnMode.CUSTOM, DataReturnMode.MINIMAL):
            return {}

        groups = {}
        for group_dict in self._get_data_groups(only_selected=True):
            groups.update(group_dict)
        return groups

    # ==========================================
    # Internal Helper Methods
    # ==========================================

    def _get_data(
        self, selected_only: bool, data_return_mode: DataReturnMode
    ) -> Optional[pd.DataFrame | str]:
        """Internal method to get data with various filters applied.

        Args:
            filtered: Whether to apply grid filtering
            sorted: Whether to apply grid sorting (requires filtered=True)
            selected_only: Whether to return only selected rows

        Returns:
            DataFrame or JSON string with requested data
        """

        response = self._response_mapping()
        nodes = response.get("nodes", [])
        if not isinstance(nodes, list):
            nodes = []

        # Components V2 starts with an empty state value. Preserve the 1.x
        # behavior of exposing the input DataFrame until the first legacy
        # collector response arrives, without serializing a duplicate dataset
        # into the component's default state.
        if (
            "nodes" not in response
            and not selected_only
            and data_return_mode not in (DataReturnMode.CUSTOM, DataReturnMode.MINIMAL)
            and isinstance(self._original_data, pd.DataFrame)
        ):
            return self._original_data

        # Filter to selected nodes if requested
        if selected_only:
            nodes = [n for n in nodes if n.get("isSelected", False)]

        data = pd.DataFrame(
            [n.get("data", {}) for n in nodes if not n.get("group", False)],
            dtype=object,
        )

        if data_return_mode == DataReturnMode.FILTERED:
            data = pd.DataFrame(
                [
                    n.get("data", {})
                    for n in nodes
                    if not n.get("group", False) and (n.get("rowIndex", None) is not None)
                ],
                dtype=object,
            )

        if data_return_mode == DataReturnMode.FILTERED_AND_SORTED:
            data = pd.DataFrame(
                [
                    n.get("data", {})
                    for n in sorted(nodes, key=lambda k: k.get("rowIndex") or -1)
                    if (not n.get("group", False))
                    and (n.get("rowIndex", None) is not None)
                ],
                dtype=object,
            )

        # Set index from auto_unique_id if available
        if "::auto_unique_id::" in data.columns:
            data.set_index("::auto_unique_id::", drop=True, inplace=True)
            data.index.name = 'index'

        return data

    # ==========================================
    # Grouped Data Support
    # ==========================================

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
                        key = content[first_dash + 1:]
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
                            new_part = content[len(prev_content):]
                            if new_part.startswith("-"):
                                new_part = new_part[1:]  # Remove leading dash

                                # Find the next dash (after colId) and extract key
                                dash_pos = new_part.find("-")
                                if dash_pos > 0:
                                    key = new_part[dash_pos + 1:]
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

    def _process_grouped_response(self, nodes: List[Dict[str, Any]]) -> List[Dict[tuple, pd.DataFrame]]:
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
            data.index.name = ""

        # Group by parent path and parse AG-Grid IDs for meaningful group names
        # Use sort=False to preserve original order and improve performance
        groups = []
        for parent_path, group_data in data.groupby("parentPath", sort=False):
            group_key = self._parse_aggrid_group_ids(parent_path)
            clean_data = group_data.drop("parentPath", axis=1)
            groups.append({group_key: clean_data})

        return groups

    def _get_data_groups(self, only_selected: bool = False) -> List[Dict[tuple, pd.DataFrame]]:
        """Get grouped data from the grid.

        Args:
            only_selected: If True, return only selected groups/rows

        Returns:
            List of dictionaries where keys are tuples of group values and values are DataFrames
        """
        response = self._response_mapping()
        if "nodes" not in response:
            return [{(): pd.DataFrame()}]

        nodes = response.get("nodes", [])
        if not isinstance(nodes, list):
            nodes = []

        if only_selected:
            # Default is True because AgGrid sets undefined for half-selected groups
            nodes = [n for n in nodes if n.get("isSelected", True)]
            if not nodes:
                fallback_data = self._get_data(selected_only=True, data_return_mode=self.data_return_mode)
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
        fallback_data = self._get_data(selected_only=only_selected, data_return_mode=self.data_return_mode)
        return [{(): fallback_data}]

    # ==========================================
    # Dictionary Interface for Backwards Compatibility
    # ==========================================

    # Static list of the public attributes exposed through the dict-like
    # interface. Kept explicit so keys()/iteration never need to evaluate
    # every (potentially expensive) property.
    _PUBLIC_KEYS = (
        "data",
        "selected_data",
        "selected_rows",
        "dataGroups",
        "selected_dataGroups",
        "grid_response",
        "raw_data",
        "grid_options",
        "grid_state",
        "columns_state",
        "event_data",
        "rows_id_after_filter",
        "rows_id_after_sort_and_filter",
        "selected_rows_id",
        "data_return_mode",
    )

    def __getitem__(self, key):
        """Get item using dict-like access."""
        # Preserve the streamlit-aggrid 1.x CustomResponse behavior: custom
        # dictionary keys take precedence over the unified return object's
        # convenience properties.
        grid_response = self.__dict__.get("grid_response", {})
        if (
            self.data_return_mode == DataReturnMode.CUSTOM
            and isinstance(grid_response, Mapping)
            and key in grid_response
        ):
            return grid_response[key]

        # Only the documented public attributes participate in the Mapping.
        # This keeps iteration and lookup consistent and avoids exposing
        # implementation details such as ``_original_data``.
        if key in self._PUBLIC_KEYS:
            return getattr(self, key)

        # Try to get from grid_response
        if isinstance(grid_response, Mapping) and key in grid_response:
            return grid_response[key]

        raise KeyError(key)

    def __iter__(self):
        """Iterate over public attributes."""
        yield from self._PUBLIC_KEYS

        grid_response = self.__dict__.get("grid_response", {})
        if isinstance(grid_response, Mapping):
            yield from (key for key in grid_response if key not in self._PUBLIC_KEYS)

    def __len__(self):
        """Return number of public attributes."""
        return sum(1 for _ in self)

    def __contains__(self, key):
        """Return whether a public or raw response key is available."""
        if key in self._PUBLIC_KEYS:
            return True

        grid_response = self.__dict__.get("grid_response", {})
        return isinstance(grid_response, Mapping) and key in grid_response

    @staticmethod
    def _mapping_values_equal(left, right) -> bool:
        """Compare nested return values without pandas' ambiguous truth value."""
        if left is right:
            return True
        if isinstance(left, (pd.DataFrame, pd.Series, pd.Index)):
            return isinstance(right, type(left)) and left.equals(right)
        if isinstance(left, Mapping) and isinstance(right, Mapping):
            if left.keys() != right.keys():
                return False
            return all(
                AgGridReturn._mapping_values_equal(left[key], right[key])
                for key in left
            )
        if isinstance(left, (list, tuple)) and isinstance(right, (list, tuple)):
            return len(left) == len(right) and all(
                AgGridReturn._mapping_values_equal(a, b)
                for a, b in zip(left, right)
            )

        try:
            result = left == right
            if isinstance(result, bool):
                return result
            # NumPy/Arrow-like comparison results expose an all() reduction.
            reduce_all = getattr(result, "all", None)
            if callable(reduce_all):
                return bool(reduce_all())
            return bool(result)
        except (TypeError, ValueError):
            return False

    def __eq__(self, other):
        """Compare mapping contents, including DataFrame-valued properties."""
        if not isinstance(other, Mapping):
            return NotImplemented
        if self.keys() != other.keys():
            return False
        return all(
            self._mapping_values_equal(self[key], other[key]) for key in self
        )

    def is_dict_like(self) -> bool:
        """Whether the raw collector payload supports mapping access."""
        return isinstance(self.grid_response, Mapping)
