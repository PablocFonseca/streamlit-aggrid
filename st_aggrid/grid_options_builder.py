from collections import defaultdict
import pandas as pd
from st_aggrid.shared import getAllColumnProps, getAllGridOptions


class GridOptionsBuilder:
    """Builder for gridOptions dictionary"""

    def __init__(self):
        
        def ddict():
            return defaultdict(ddict)

        self.__grid_options = ddict()
        self.sideBar: dict = dict()

    @staticmethod
    def from_dataframe(dataframe, **default_column_parameters):
        """
        Creates an instance and initilizes it from a dataframe.
        ColumnDefs are created based on dataframe columns and data types.

        Args:
            dataframe (pd.DataFrame): a pandas DataFrame.

        Returns:
            GridOptionsBuilder: The instance initialized from the dataframe definition.
        """

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

        COLUMN_PROPS = [i['name'] for i in getAllColumnProps()]
        GRID_OPTIONS = [i['name'] for i in getAllGridOptions()]

        gb = GridOptionsBuilder()

        # fetch extra args that should go to DefaultColumns
        for k,v in default_column_parameters.items():
            
            if k in COLUMN_PROPS:
               gb.configure_default_column(**{k:v})
            elif k in GRID_OPTIONS:
                gb.configure_grid_options(**{k:v})
            else:
                print(f"{k} is not a valid gridOption or columnDef.")

        if any("." in col for col in dataframe.columns):
            gb.configure_grid_options(suppressFieldDotNotation=True)

        for col_name, col_type in zip(dataframe.columns, dataframe.dtypes):
            gb.configure_column(field=col_name, type=type_mapper.get(col_type.kind, []))

        gb.configure_grid_options(autoSizeStrategy={'type':'fitCellContents', 'skipHeader':False})

        return gb

    def configure_default_column(
        self,
        # min_column_width=5,
        # resizable=True,
        # filterable=True,
        # sortable=True,
        # editable=False,
        # groupable=False,
        # sorteable=None,
        **other_default_column_properties
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
        # if sorteable is not None:
        #     sortable = sorteable

        # defaultColDef = {
        #     "minWidth": min_column_width,
        #     "editable": editable,
        #     "filter": filterable,
        #     "resizable": resizable,
        #     "sortable": sortable,
        # }
        # if groupable:
        #     defaultColDef["enableRowGroup"] = groupable
        defaultColDef = {}
        if other_default_column_properties:
            defaultColDef = {**defaultColDef, **other_default_column_properties}

        self.__grid_options["defaultColDef"] = {**self.__grid_options["defaultColDef"], **other_default_column_properties}

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
        to colDefs which field property is in column_names list.

        Args:
            column_names (list, optional):
                columns field properties. If any of colDefs matches **props dict is merged.
                Defaults to [].
        """
        for k in self.__grid_options["columnDefs"]:
            if k in column_names:
                self.__grid_options["columnDefs"][k].update(props)

    def configure_column(self, field, header_name=None, **other_column_properties):
        """Configures an individual column
        check https://www.ag-grid.com/javascript-grid-column-properties/ for more information.

        Args:
            field (String): field name, usually equals the column header.
            header_name (String, optional): [description]. Defaults to None.
        """
        if not self.__grid_options.get("columnDefs", None):
            self.__grid_options["columnDefs"] = defaultdict(dict)

        colDef = {
            "headerName": field if header_name is None else header_name,
            "field": field,
        }

        if other_column_properties:
            colDef = {**colDef, **other_column_properties}

        self.__grid_options["columnDefs"][field].update(colDef)

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
            #self.__grid_options["preSelectedRows"] = pre_selected_rows
            self.__grid_options['initialState']['rowSelection'] = pre_selected_rows

        self.__grid_options["rowSelection"] = selection_mode
        self.__grid_options["rowMultiSelectWithClick"] = rowMultiSelectWithClick
        self.__grid_options["suppressRowDeselection"] = suppressRowDeselection
        self.__grid_options["suppressRowClickSelection"] = suppressRowClickSelection
        self.__grid_options["groupSelectsChildren"] = (
            groupSelectsChildren and selection_mode == "multiple"
        )
        self.__grid_options["groupSelectsFiltered"] = groupSelectsFiltered
        #self.__grid_options["preSelectAllRows"] = pre_select_all_rows

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

        Args:
            suppressMenu (bool, optional): Suppresses the header menu for the index col. Defaults to True.
            headerText (str, optional): Header for the index column. Defaults to empty string.
            resizable (bool, optional): Make index column resizable. Defaults to False.
            sortable (bool, optional): Make index column sortable. Defaults to True.

        """

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
        first_col_def = next(iter(self.__grid_options["columnDefs"]))

        self.configure_column(first_col_def, headerText, **index_options)

    def build(self):
        """Builds the gridOptions dictionary

        Returns:
            dict: Returns a dicionary containing the configured grid options
        """
        self.__grid_options["columnDefs"] = list(
            self.__grid_options["columnDefs"].values()
        )

        return self.__grid_options
