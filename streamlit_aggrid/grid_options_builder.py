from collections import defaultdict
from streamlit_aggrid.shared import getAllColumnProps, getAllGridOptions
import pandas as pd
class GridOptionsBuilder:
    """Builder for gridOptions dictionary"""

    def __init__(self):
        def ddict():
            return defaultdict(ddict)

        self.__grid_options = ddict()
        self.sideBar: dict = dict()

    @staticmethod
    def from_dataframe(dataframe, parse_multi_index=False, multi_index_column_groups_open=True, **default_column_parameters):
        """
        Creates an instance and initilizes it from a dataframe.
        ColumnDefs are created based on dataframe columns and data types.

        Args:
            dataframe (pd.DataFrame): a pandas DataFrame.
            parse_multi_index (bool, optional): If True, creates column groups from MultiIndex columns
                and row groups from MultiIndex index. Requires AG Grid Enterprise. Defaults to False.
            multi_index_column_groups_open (bool, optional): If True, column groups created from
                MultiIndex columns will be open by default. If False, they will be closed by default.
                Only applies when parse_multi_index=True. Defaults to True.
            **default_column_parameters: Additional parameters for default column configuration.

        Returns:
            GridOptionsBuilder: The instance initialized from the dataframe definition.
        """

        if (
        hasattr(dataframe, '__class__') and 
        dataframe.__class__.__module__ and
        'polars' in dataframe.__class__.__module__ and
        dataframe.__class__.__name__ == 'DataFrame'
        ):
            dataframe = dataframe.to_pandas(use_pyarrow_extension_array=False)

        # numpy types: 'biufcmMOSUV' https://numpy.org/doc/stable/reference/generated/numpy.dtype.kind.html
        type_mapper = {
            "b": ["textColumn"],
            "i": ["numericColumn", "numberColumnFilter"],
            "u": ["numericColumn", "numberColumnFilter"],
            "f": ["numericColumn", "numberColumnFilter"],
            "c": [],
            "m": ["timedeltaFormat"],
            "M": ["dateColumnFilter", "shortDateTimeFormat"],
            "O": [],
            "S": [],
            "U": [],
            "V": [],
        }

        COLUMN_PROPS = [i["name"] for i in getAllColumnProps()]
        GRID_OPTIONS = [i["name"] for i in getAllGridOptions()]

        gb = GridOptionsBuilder()

        # fetch extra args that should go to DefaultColumns
        for k, v in default_column_parameters.items():
            if k in COLUMN_PROPS:
                gb.configure_default_column(**{k: v})
            elif k in GRID_OPTIONS:
                gb.configure_grid_options(**{k: v})
            else:
                print(f"{k} is not a valid gridOption or columnDef.")

        if any("." in col for col in map(str, dataframe.columns)):
            gb.configure_grid_options(suppressFieldDotNotation=True)

        # Handle multi-level structures if requested
        if parse_multi_index:
            # Check if dataframe has MultiIndex structures
            has_multiindex_index = isinstance(dataframe.index, pd.MultiIndex)
            has_multiindex_columns = isinstance(dataframe.columns, pd.MultiIndex)

            if not has_multiindex_index and not has_multiindex_columns:
                raise ValueError("parse_multi_index is True, but DataFrame does not have MultiIndex on index or columns.")

            # Configure MultiIndex structures
            gb._configure_multi_index_structures(dataframe, type_mapper, multi_index_column_groups_open)
        else:
            # Standard column configuration
            for col_name, col_type in zip(map(str, dataframe.columns), dataframe.dtypes):
                gb.configure_column(field=col_name, type=type_mapper.get(col_type.kind, []))

        gb.configure_grid_options(
            autoSizeStrategy={"type": "fitGridWidth"}
        )

        return gb

    def _configure_multi_index_structures(self, dataframe, type_mapper, column_groups_open=True):
        """
        Configure grid options for DataFrames with MultiIndex structures.

        - MultiIndex on index -> Row groups with multipleColumns display
        - MultiIndex on columns -> Column groups with headers

        Args:
            dataframe (pd.DataFrame): Original DataFrame with MultiIndex on index and/or columns.
            type_mapper (dict): Maps numpy dtype kinds to AG Grid column types.
            column_groups_open (bool): If True, column groups are open by default. Defaults to True.
        """
        import pandas as pd

        has_multiindex_index = isinstance(dataframe.index, pd.MultiIndex)
        has_multiindex_columns = isinstance(dataframe.columns, pd.MultiIndex)

        # Configure row groups (MultiIndex index)
        if has_multiindex_index:
            self._configure_row_groups(dataframe.index, dataframe.columns)

        # Configure column groups (MultiIndex columns)
        if has_multiindex_columns:
            self._configure_column_groups(dataframe, type_mapper, dataframe.columns, dataframe.index if has_multiindex_index else None, column_groups_open)

        # Configure regular data columns (when columns are NOT MultiIndex)
        if not has_multiindex_columns:
            self._configure_data_columns(dataframe, type_mapper, dataframe.index if has_multiindex_index else None, has_multiindex_columns)

    def _configure_row_groups(self, original_index, original_columns):
        """
        Configure row grouping with multipleColumns display.
        Creates two columns per group level:
        1. Hidden data column (rowGroup=True, hide=True)
        2. Visible display column (showRowGroup, cellRenderer=agGroupCellRenderer)

        Args:
            original_index (pd.MultiIndex): Original MultiIndex from the index.
            has_multiindex_columns (bool): Whether columns are also MultiIndex.
        """
        for i, level_name in enumerate(original_index.names):
            # Get clean column name for this index level
            col_name = level_name if level_name is not None else f"index_level_{i}"

            # Determine field name based on column structure
            # When columns are MultiIndex, pandas creates tuple field names like ('Region', '')
            field_name = str(tuple([col_name] + [''] * (len(original_columns.names) - 1)))

            # 1. Hidden data column for grouping
            self.configure_column(
                field=field_name,
                header_name=col_name,
                rowGroup=True,
                hide=True
            )

        # Configure grid for multiple column group display
        self.configure_grid_options(
            groupDisplayType='multipleColumns',
            groupDefaultExpanded=-1,
            showOpenedGroup=True,
            suppressAggFuncInHeader=True,
            groupHideOpenParents=True
        )

    def _configure_column_groups(self, dataframe, type_mapper, original_columns, original_index, open_by_default=True):
        """
        Configure column groups from MultiIndex columns.
        Scans all column tuples and infers tree structure.

        Args:
            dataframe (pd.DataFrame): DataFrame with MultiIndex columns.
            type_mapper (dict): Maps numpy dtype kinds to AG Grid column types.
            original_columns (pd.MultiIndex): Original MultiIndex columns.
            original_index (pd.MultiIndex | None): Original MultiIndex index.
            open_by_default (bool): If True, column groups are open by default. Defaults to True.
        """
        # Step 1: Build tree from column tuples
        # Tree structure: dict of dicts, where leaves store the full column tuple
        tree = {}

        for col_tuple in original_columns:
            current = tree

            # Navigate/create path through tree
            for i, level_value in enumerate(col_tuple):
                is_leaf = (i == len(col_tuple) - 1)

                if is_leaf:
                    # Store the full tuple as leaf marker
                    current[level_value] = col_tuple
                else:
                    # Create branch if doesn't exist
                    if level_value not in current:
                        current[level_value] = {}
                    current = current[level_value]

        # Step 2: Recursively build column definitions from tree
        def build_columns(node, parent_path="", depth=0):
            """
            Traverse tree and create column definitions.
            Returns list of colIds for parent groups to reference as children.

            The key insight:
            - Leaf nodes return their field name (used as colId)
            - Branch nodes create a group and return the group's colId
            """
            if node is None or not isinstance(node, dict):
                return []

            children_ids = []

            for idx, (key, value) in enumerate(node.items()):
                if isinstance(value, tuple):
                    # LEAF: value is the full column tuple
                    field_name = str(value)
                    col_type = dataframe[value].dtype

                    # Add columnGroupShow to make groups collapsed by default
                    # First column in group shows when closed, others show when open
                    extra_props = {}
                    if depth > 0:  # Only add if we're inside a group
                        extra_props['columnGroupShow'] = 'closed' if idx == 0 else 'open'

                    self.configure_column(
                        field=field_name,
                        header_name=str(key),
                        type=type_mapper.get(col_type.kind, []),
                        **extra_props
                    )
                    # Leaf columns use their field name as colId
                    children_ids.append(field_name)

                elif isinstance(value, dict):
                    # BRANCH: recursively build sub-tree
                    grandchildren_ids = build_columns(value, f"{parent_path}/{key}", depth + 1)

                    if grandchildren_ids:
                        # Create a column group
                        # Generate unique colId for this group
                        group_col_id = f"__group__{parent_path}/{key}".replace("//", "/")

                        # Add columnGroupShow to make parent groups collapsible
                        # First group shows when parent is closed, others show when open
                        group_props = {
                            'openByDefault': open_by_default
                        }
                        if depth > 0:  # Only add if this group has a parent group
                            group_props['columnGroupShow'] = 'closed' if idx == 0 else 'open'

                        self.configure_column(
                            col_id=group_col_id,
                            header_name=str(key),
                            children=grandchildren_ids,
                            **group_props
                        )

                        # Return this group's colId so parent can reference it
                        children_ids.append(group_col_id)

            return children_ids

        # Step 3: Start building from root
        # Root level groups are configured but not returned
        build_columns(tree)

    def _configure_data_columns(self, dataframe, type_mapper, original_index, has_multiindex_columns):
        """
        Configure regular data columns (when columns are not MultiIndex).
        Skips index columns that are already configured for row grouping.

        Args:
            dataframe (pd.DataFrame): DataFrame to configure.
            type_mapper (dict): Maps numpy dtype kinds to AG Grid column types.
            original_index (pd.MultiIndex | None): Original MultiIndex index (to skip those columns).
            has_multiindex_columns (bool): Whether original columns were MultiIndex.
        """
        # Build set of field names to skip (index columns)
        skip_fields = set()
        if original_index is not None:
            for level_name in original_index.names:
                col_name = level_name if level_name is not None else f"index_level_{level_name}"
                if has_multiindex_columns:
                    skip_fields.add(str((col_name, '')))
                else:
                    skip_fields.add(col_name)

        # Configure all data columns
        for field_name, dtype in zip(map(str, dataframe.columns), dataframe.dtypes):
            if field_name not in skip_fields:
                self.configure_column(
                    field=field_name,
                    type=type_mapper.get(dtype.kind, [])
                )

    def configure_default_column(
        self,
        **other_default_column_properties,
    ):
        """Configure default column.

        Args:
            min_column_width (int, optional):
                Minimum column width. Defaults to 100.

            resizable (bool, optional):
                All columns will be resizable. Defaults to True.

            filterable (bool, optional):
                All columns will be filterable. Defaults to True.

            sortable (bool, optional):
                All columns will be sortable. Defaults to True.

            sorteable (bool, optional):
                Backwards compatibility alias for sortable. Overrides sortable if not None.

            groupable (bool, optional):
                All columns will be groupable based on row values. Defaults to True.

            editable (bool, optional):
                All columns will be editable. Defaults to True.

            groupable (bool, optional):
                All columns will be groupable. Defaults to True.

            **other_default_column_properties:
                Key value pairs that will be merged to defaultColDef dict.
                Chech ag-grid documentation.
        """

        defaultColDef = {}
        if other_default_column_properties:
            defaultColDef = {**defaultColDef, **other_default_column_properties}

        self.__grid_options["defaultColDef"] = {
            **self.__grid_options["defaultColDef"],
            **other_default_column_properties,
        }

    def configure_auto_height(self, autoHeight=True):
        """
        Makes grid autoheight

        Args:
            autoHeight (bool, optional): enable or disable autoheight. Defaults to True.
        """
        if autoHeight:
            self.configure_grid_options(domLayout="autoHeight")
        else:
            self.configure_grid_options(domLayout="normal")

    def configure_grid_options(self, **props):
        """Merges props to gridOptions

        Args:
            props (dict): props dicts will be merged to gridOptions root.
        """
        self.__grid_options.update(props)

    def configure_columns(self, column_names=[], **props):
        """Batch configures columns. Key-pair values from props dict will be merged
        to colDefs which colId (or field name) is in column_names list.

        .. deprecated::
            Use :meth:`configure_column` with a list of field names instead.
            This method will be removed in a future version.

        Args:
            column_names (list, optional):
                List of colIds (usually field names) to configure.
                If any colId matches, **props dict is merged. Defaults to [].
            **props: Properties to apply to the specified columns.

        Examples:
            # Old way (deprecated)
            gb.configure_columns(['age', 'year'], width=80)

            # New way (recommended)
            gb.configure_column(['age', 'year'], width=80)
        """
        import warnings
        warnings.warn(
            "configure_columns() is deprecated. Use configure_column() with a list of field names instead: "
            "gb.configure_column(['col1', 'col2'], width=100)",
            DeprecationWarning,
            stacklevel=2
        )
        for col_id in self.__grid_options.get("columnDefs", {}):
            if col_id in column_names:
                self.__grid_options["columnDefs"][col_id].update(props)

    def configure_column(self, field=None, header_name=None, col_id=None, children=None, **other_column_properties):
        """Configures one or multiple columns.

        This method can configure:
        1. Regular columns: Have a 'field' that maps to data
        2. Virtual columns: No 'field', use 'valueGetter' to compute values
        3. Column groups: No 'field', have 'children' list to group other columns
        4. Batch configuration: Pass a list of field names to apply same properties to multiple columns

        Check https://www.ag-grid.com/javascript-grid-column-properties/ for more information.

        Args:
            field (str | list[str], optional): Field name(s) from data.
                If a list, applies **other_column_properties to all fields (batch mode).
                If a string, configures single column. Omit for virtual columns and groups.
            header_name (str, optional): Display name in column header (single column mode only).
            col_id (str, optional): Explicit unique identifier (single column mode only).
            children (list, optional): List of colIds to group (makes this a column group).
            **other_column_properties: Any AG Grid column properties (width, pinned, valueGetter, etc.)

        Examples:
            # Regular column
            gb.configure_column('athlete', header_name='Athlete Name', minWidth=150)

            # Batch configuration (multiple columns)
            gb.configure_column(['age', 'year'], width=80, filterable=False)
            gb.configure_column(['id', 'internal_code'], hide=True)

            # Virtual column (no field, has valueGetter)
            gb.configure_column(
                header_name='Total Medals',
                valueGetter='Number(data.gold) + Number(data.silver)'
            )

            # Column group (no field, has children)
            gb.configure_column(
                header_name='Medal Counts',
                children=['gold', 'silver', 'bronze'],
                headerClass='medal-header'
            )
        """
        # Batch mode: if field is a list, apply properties to all columns
        if isinstance(field, list):
            for col_id in self.__grid_options.get("columnDefs", {}):
                if col_id in field:
                    self.__grid_options["columnDefs"][col_id].update(other_column_properties)
            return self

        # Single column mode
        # Generate colId if not provided
        if col_id is None:
            if children is not None:
                # Column group: prefix with __group__
                if header_name:
                    col_id = f"__group__{header_name.lower().replace(' ', '_')}"
                else:
                    raise ValueError("Column groups require header_name")
            elif field is not None:
                # Regular column: colId defaults to field name
                col_id = field
            elif header_name is not None:
                # Virtual column: generate colId from header_name
                col_id = header_name.lower().replace(' ', '_').replace('/', '_')
            else:
                raise ValueError("Must provide field, header_name, or col_id")

        # Initialize columnDefs if needed
        if not self.__grid_options.get("columnDefs", None):
            self.__grid_options["columnDefs"] = defaultdict(dict)

        # Build column definition
        colDef = {"colId": col_id}

        # Add field only if provided (not for virtual columns or groups)
        if field is not None:
            colDef["field"] = field

        # Add header name
        if header_name is not None:
            colDef["headerName"] = header_name
        elif field is not None and "headerName" not in self.__grid_options["columnDefs"][col_id]:
            colDef["headerName"] = field  # Default to field name only if not already set

        # Add children if it's a group
        if children is not None:
            colDef["children"] = children

        # Add any other properties
        if other_column_properties:
            colDef.update(other_column_properties)

        # Store using colId as key
        self.__grid_options["columnDefs"][col_id].update(colDef)

        return self

    def configure_side_bar(
        self, filters_panel=True, columns_panel=True, defaultToolPanel=""
    ):
        """configures the side panel of ag-grid.
           Side panels are enterprise features, please check www.ag-grid.com

        Args:
            filters_panel (bool, optional):
                Enable filters side panel. Defaults to True.

            columns_panel (bool, optional):
                Enable columns side panel. Defaults to True.

            defaultToolPanel (str, optional): The default tool panel that should open when grid renders.
                                              Either "filters" or "columns".
                                              If value is blank, panel will start closed (default)
        """
        filter_panel = {
            "id": "filters",
            "labelDefault": "Filters",
            "labelKey": "filters",
            "iconKey": "filter",
            "toolPanel": "agFiltersToolPanel",
        }

        columns_panel = {
            "id": "columns",
            "labelDefault": "Columns",
            "labelKey": "columns",
            "iconKey": "columns",
            "toolPanel": "agColumnsToolPanel",
        }

        if filters_panel or columns_panel:
            sideBar = {"toolPanels": [], "defaultToolPanel": defaultToolPanel}

            if filters_panel:
                sideBar["toolPanels"].append(filter_panel)
            if columns_panel:
                sideBar["toolPanels"].append(columns_panel)

            self.__grid_options["sideBar"] = sideBar

    def configure_selection(
        self,
        selection_mode: str = "single",
        use_checkbox: bool = False,
        header_checkbox: bool = False,
        header_checkbox_filtered_only: bool = True,
        pre_select_all_rows: bool = False,
        pre_selected_rows: list = None,
        rowMultiSelectWithClick: bool = False,
        suppressRowDeselection: bool = False,
        suppressRowClickSelection: bool = False,
        groupSelectsChildren: bool = True,
        groupSelectsFiltered: bool = True,
    ):
        """Configure grid selection features

        Args:
            selection_mode (str, optional):
                Either 'single', 'multiple' or 'disabled'. Defaults to 'single'.

            use_checkbox (bool, optional):
                Set to true to have checkbox next to each row.

            header_checkbox (bool, optional):
                Set to true to have a checkbox in the header to select all rows.

            header_checkbox_filtered_only (bool, optional):
                If header_checkbox is set to True, once the header checkbox is clicked, returned rows depend on this parameter.
                If this is set to True, only filtered (shown) rows will be selected and returned.
                If this is set to False, the whole dataframe (all rows regardless of the applited filter) will be selected and returned.

            pre_selected_rows (list, optional):
                Use list of dataframe row iloc index to set corresponding rows as selected state on load. Defaults to None.

            rowMultiSelectWithClick (bool, optional):
                If False user must hold shift to multiselect. Defaults to True if selection_mode is 'multiple'.

            suppressRowDeselection (bool, optional):
                Set to true to prevent rows from being deselected if you hold down Ctrl and click the row
                (i.e. once a row is selected, it remains selected until another row is selected in its place).
                By default the grid allows deselection of rows.
                Defaults to False.

            suppressRowClickSelection (bool, optional):
                Supress row selection by clicking. Usefull for checkbox selection for instance
                Defaults to False.

            groupSelectsChildren (bool, optional):
                When rows are grouped selecting a group select all children.
                Defaults to True.

            groupSelectsFiltered (bool, optional):
                When a group is selected filtered rows are also selected.
                Defaults to True.
        """
        if selection_mode == "disabled":
            self.__grid_options.pop("rowSelection", None)
            self.__grid_options.pop("rowMultiSelectWithClick", None)
            self.__grid_options.pop("suppressRowDeselection", None)
            self.__grid_options.pop("suppressRowClickSelection", None)
            self.__grid_options.pop("groupSelectsChildren", None)
            self.__grid_options.pop("groupSelectsFiltered", None)
            return

        if use_checkbox:
            suppressRowClickSelection = True
            first_key = next(iter(self.__grid_options["columnDefs"].keys()))
            self.__grid_options["columnDefs"][first_key]["checkboxSelection"] = True
            if header_checkbox:
                self.__grid_options["columnDefs"][first_key][
                    "headerCheckboxSelection"
                ] = True
                if header_checkbox_filtered_only:
                    self.__grid_options["columnDefs"][first_key][
                        "headerCheckboxSelectionFilteredOnly"
                    ] = True

        if pre_selected_rows:
            # self.__grid_options["preSelectedRows"] = pre_selected_rows
            self.__grid_options["initialState"]["rowSelection"] = pre_selected_rows

        self.__grid_options["rowSelection"] = selection_mode
        self.__grid_options["rowMultiSelectWithClick"] = rowMultiSelectWithClick
        self.__grid_options["suppressRowDeselection"] = suppressRowDeselection
        self.__grid_options["suppressRowClickSelection"] = suppressRowClickSelection
        self.__grid_options["groupSelectsChildren"] = (
            groupSelectsChildren and selection_mode == "multiple"
        )
        self.__grid_options["groupSelectsFiltered"] = groupSelectsFiltered
        # self.__grid_options["preSelectAllRows"] = pre_select_all_rows

    def configure_pagination(
        self, enabled=True, paginationAutoPageSize=True, paginationPageSize=10
    ):
        """Configure grid's pagination features

        Args:
            enabled (bool, optional):
                Self explanatory. Defaults to True.

            paginationAutoPageSize (bool, optional):
                Calculates optimal pagination size based on grid Height. Defaults to True.

            paginationPageSize (int, optional):
                Forces page to have this number of rows per page. Defaults to 10.
        """
        if not enabled:
            self.__grid_options.pop("pagination", None)
            self.__grid_options.pop("paginationAutoPageSize", None)
            self.__grid_options.pop("paginationPageSize", None)
            return

        self.__grid_options["pagination"] = True
        if paginationAutoPageSize:
            self.__grid_options["paginationAutoPageSize"] = paginationAutoPageSize
        else:
            self.__grid_options["paginationPageSize"] = paginationPageSize

    def configure_first_column_as_index(
        self,
        suppressMenu: bool = True,
        headerText: str = "",
        resizable=False,
        sortable=True,
    ):
        """
        Configures the first column definition to look as an index column.

        .. deprecated::
            This method is deprecated. Use `configure_column()` directly instead:

            Instead of:
                gb.configure_first_column_as_index(headerText="Index")

            Use:
                first_field = list(df.columns)[0]
                gb.configure_column(
                    first_field,
                    header_name="Index",
                    minWidth=0,
                    cellStyle={"color": "white", "background-color": "gray"},
                    pinned="left",
                    suppressMovable=True,
                    suppressMenu=True
                )

        Args:
            suppressMenu (bool, optional): Suppresses the header menu for the index col. Defaults to True.
            headerText (str, optional): Header for the index column. Defaults to empty string.
            resizable (bool, optional): Make index column resizable. Defaults to False.
            sortable (bool, optional): Make index column sortable. Defaults to True.

        """
        import warnings
        warnings.warn(
            "configure_first_column_as_index() is deprecated. "
            "Use configure_column() directly with the desired column field name.",
            DeprecationWarning,
            stacklevel=2
        )

        index_options = {
            "minWidth": 0,
            "cellStyle": {"color": "white", "background-color": "gray"},
            "pinned": "left",
            "resizable": resizable,
            "sortable": sortable,
            "suppressMovable": True,
            "suppressMenu": suppressMenu,
            "menuTabs": ["filterMenuTab"],
        }

        # Get the first colId
        first_col_id = next(iter(self.__grid_options["columnDefs"]))

        # Get the column definition to check if it has a field
        first_col_def = self.__grid_options["columnDefs"][first_col_id]
        field_name = first_col_def.get("field")

        if field_name:
            # Regular column with field
            self.configure_column(field_name, headerText, **index_options)
        else:
            # Virtual column without field - use colId
            self.configure_column(col_id=first_col_id, header_name=headerText, **index_options)

    def build(self):
        """Builds the gridOptions dictionary with support for regular, virtual, and grouped columns.

        Returns:
            dict: Returns a dictionary containing the configured grid options
        """
        column_defs_dict = self.__grid_options.get("columnDefs", {})

        if not column_defs_dict:
            self.__grid_options["columnDefs"] = []
            return self.__grid_options

        # Separate groups from regular columns
        groups_dict = {}  # colId -> group definition
        regular_columns = {}

        for col_id, col_def in column_defs_dict.items():
            if "children" in col_def:
                groups_dict[col_id] = col_def
            else:
                regular_columns[col_id] = col_def

        # Build final columnDefs structure
        final_column_defs = []
        grouped_col_ids = set()
        processed_groups = set()

        # Process groups recursively (handle nested groups)
        def process_group(group_col_id):
            """Process a group and its children recursively."""
            if group_col_id in processed_groups:
                return None  # Already processed

            if group_col_id not in groups_dict:
                return None  # Not a group

            processed_groups.add(group_col_id)
            group_def = groups_dict[group_col_id]
            group_copy = group_def.copy()

            # Replace child colIds with actual column/group definitions
            children_defs = []
            for child_col_id in group_def["children"]:
                # Check if child is a group or regular column
                if child_col_id in groups_dict:
                    # Child is a group - process it recursively
                    child_group_def = process_group(child_col_id)
                    if child_group_def:
                        children_defs.append(child_group_def)
                        grouped_col_ids.add(child_col_id)
                elif child_col_id in regular_columns:
                    # Child is a regular column
                    child_def = regular_columns[child_col_id].copy()
                    child_def.pop("colId", None)
                    children_defs.append(child_def)
                    grouped_col_ids.add(child_col_id)
                else:
                    print(f"Warning: Column '{child_col_id}' in group '{group_def.get('headerName')}' was not configured")

            group_copy["children"] = children_defs
            group_copy.pop("colId", None)

            return group_copy

        # Process all root-level groups (groups not referenced by other groups)
        all_child_ids = set()
        for group_def in groups_dict.values():
            all_child_ids.update(group_def["children"])

        root_group_ids = set(groups_dict.keys()) - all_child_ids

        for root_group_id in root_group_ids:
            group_def = process_group(root_group_id)
            if group_def:
                final_column_defs.append(group_def)

        # Add ungrouped columns, with special handling for group display columns
        group_display_columns = []  # Will store tuples of (index, col_def)
        row_group_data_columns = []
        other_columns = []

        for col_id, col_def in regular_columns.items():
            if col_id not in grouped_col_ids:
                col_def_copy = col_def.copy()
                # Remove colId (AG Grid doesn't need it if field exists)
                col_def_copy.pop("colId", None)

                # Categorize columns for proper ordering
                if col_id.startswith("__group_display_"):
                    # Extract index from col_id (format: __group_display_{i}_{name})
                    try:
                        parts = col_id.split('_')
                        index = int(parts[3])  # Extract the numeric index
                        group_display_columns.append((index, col_def_copy))
                    except (IndexError, ValueError):
                        # Fallback if format is unexpected
                        group_display_columns.append((999, col_def_copy))
                elif col_def_copy.get("rowGroup") and col_def_copy.get("hide"):
                    row_group_data_columns.append(col_def_copy)
                else:
                    other_columns.append(col_def_copy)

        # Sort group display columns by index to maintain proper order (Region before Product, etc.)
        group_display_columns.sort(key=lambda x: x[0])
        group_display_columns = [col_def for _, col_def in group_display_columns]

        # Order: group display columns (sorted), column groups, other columns, then hidden row group data columns
        final_column_defs.extend(group_display_columns)
        final_column_defs.extend(other_columns)
        final_column_defs.extend(row_group_data_columns)

        self.__grid_options["columnDefs"] = final_column_defs
        return self.__grid_options
