from collections import defaultdict
from typing import List
import pandas as pd


class GridOptionsBuilder:
    """
    Auxiliary class that builds gridOptions dictionary.

    Use this class to help AgGrid configuration. Any configuration supported by the 
    gridOptions dictionary can be configured using this class. check https://www.ag-grid.com/javascript-grid-properties/ for more information.
    """

    def __init__(self):
        self.__grid_options = defaultdict(dict)
        self.sideBar = {}

    @staticmethod
    def from_dataframe(dataframe: pd.DataFrame, **default_column_parameters):
        r"""Initializes a GridOptionsBuilder from a pandas dataframe.

        This method creates a column definition for each column in the dataframe and tries to ifer
        correct columnTypes from dataframe's dtypes. 

        Args:
            dataframe:
                Dataframe to be used to create the GridOptionsBuilder.

            ``**default_column_parameters``: 
                Key-pair values that will be merged to defaultColDef dict.

        Returns:
            A GridOptionsBuilder instance.

        **Example:**

        .. code-block:: python

            #builds a gridOptions dictionary using a GridOptionsBuilder instance.
            builder = GridOptionsBuilder.from_dataframe(df)
            builder.configure_column("first_column", header_name="First", editable=True)
            go = builder.build()

            #uses the gridOptions dictionary to configure AgGrid behavior.    
            AgGrid(df, gridOptions=go)
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

        gb = GridOptionsBuilder()
        gb.configure_default_column(**default_column_parameters)

        if any('.' in col for col in dataframe.columns):
            gb.configure_grid_options(suppressFieldDotNotation = True)

        for col_name, col_type in zip(dataframe.columns, dataframe.dtypes):
            gb.configure_column(field=col_name, type=type_mapper.get(col_type.kind, []))

        return gb

    def configure_default_column(
        self,
        min_column_width: int = 5,
        resizable: bool = True,
        filterable: bool = True,
        sorteable: bool = True,
        editable: bool = False,
        groupable: bool = False,
        **other_default_column_properties: dict
    ):
        """Sets default columns definitions.

        More info `here <https://www.ag-grid.com/javascript-data-grid/column-definitions/#default-column-definitions>`_

        Args:
            min_column_width:
                minimum column width.
                Defaults to 5.

            resizable:
                sets columns as resizable.
                Defaults to True.

            filterable:
                sets columns as filterable.
                Defaults to True.

            sorteable:
                sets columns as sorteable.
                Defaults to True.

            editable:
                sets columns as editable.
                Defaults to False.

            groupable:
                sets columns as groupable.
                Defaults to False.

            ``**other_default_column_properties``:
                Aditional keyword arguments values will be added as default columns definition.

        Returns:
            None
        """
        defaultColDef = {
            "minWidth": min_column_width,
            "editable": editable,
            "filter": filterable,
            "resizable": resizable,
            "sortable": sorteable,
        }
        if groupable:
            defaultColDef["enableRowGroup"] = groupable

        if other_default_column_properties:
            defaultColDef = {**defaultColDef, **other_default_column_properties}

        self.__grid_options["defaultColDef"] = defaultColDef

    def configure_auto_height(self, autoHeight: bool = True):
        """Configures auto height behavior.

        Args:
            autoHeight (bool, optional): enable or disable auto height. Defaults to True.

        Returns:
            None            
        """

        if autoHeight:
            self.configure_grid_options(domLayout="autoHeight")
        else:
            self.configure_grid_options(domLayout="normal")

    def configure_columns(self, column_names: List[str] = [], **props):
        """Batch configures columns. 
        
        Key-pair values from props dict will be merged
        to colDefs which field property is present in column_names list.

        Args:
            column_names:
                Columns field properties. 
                If any of colDefs mathces ``**props`` dict is merged.
                Defaults to [].

        Returns:
            None
        """
        for k in self.__grid_options["columnDefs"]:
            if k in column_names:
                self.__grid_options["columnDefs"][k].update(props)

    def configure_column(
        self, field: str, header_name: str = None, **other_column_properties
    ):
        """Configures an individual column
        check https://www.ag-grid.com/javascript-grid-column-properties/ for more information.

        Args:
            field (str): Field name, usually equals the column header.
            header_name (str, optional): [description]. Defaults to None.
        
        Returns:
            None        
        """

        if not self.__grid_options.get("columnDefs", None):
            self.__grid_options["columnDefs"] = defaultdict(dict)

        colDef = {"headerName": header_name if header_name else field, "field": field}

        if other_column_properties:
            colDef = {**colDef, **other_column_properties}

        self.__grid_options["columnDefs"][field].update(colDef)

    def configure_side_bar(
        self,
        filters_panel: bool = True,
        columns_panel: bool = True,
        defaultToolPanel: str = "",
    ):
        """Configures the side bar.

        Args:
            filters_panel (bool, optional): enable or disable filters panel. Defaults to True.
            columns_panel (bool, optional): enable or disable columns panel. Defaults to True.
            defaultToolPanel (str, optional): sets default tool panel either 'columns' or 'filters'. Defaults to panel closed ("")
        
        Returns:
            None
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
        pre_selected_rows: List[int] = [],
        rowMultiSelectWithClick: bool = False,
        suppressRowDeselection: bool = False,
        suppressRowClickSelection: bool = False,
        groupSelectsChildren: bool = True,
        groupSelectsFiltered: bool = True,
    ):
        """Configure the grid selection behavior.

        Args:
            selection_mode:
                Either 'single', 'multiple' or 'disabled'. Defaults to 'single'.

            use_checkbox: 
                Enable or disable checkbox selection. Defaults to False.

            pre_selected_rows:
                List of row indexes to be pre-selected. Defaults to [].

            rowMultiSelectWithClick:
                If False user must hold shift to multiselect. 
                Defaults to True if selection_mode is 'multiple'.

            suppressRowDeselection:
                Set to true to prevent rows from being deselected if you hold down Ctrl and click the row
                (once a row is selected, it remains selected until another row is selected in its place).
                By default the grid allows deselection of rows.
                Defaults to False.

            suppressRowClickSelection:
                Supress row selection by clicking. 
                Usefull for checkbox selection.
                Defaults to False.

            groupSelectsChildren:
                When rows are grouped selecting a group select all children.
                Defaults to True.

            groupSelectsFiltered:
                When a group is selected filtered rows are also selected.
                Defaults to True.

        Returns:
            None
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

        if pre_selected_rows:
            self.__grid_options["preSelectedRows"] = pre_selected_rows

        self.__grid_options["rowSelection"] = selection_mode
        self.__grid_options["rowMultiSelectWithClick"] = rowMultiSelectWithClick
        self.__grid_options["suppressRowDeselection"] = suppressRowDeselection
        self.__grid_options["suppressRowClickSelection"] = suppressRowClickSelection
        self.__grid_options["groupSelectsChildren"] = groupSelectsChildren and selection_mode == "multiple"
        self.__grid_options["groupSelectsFiltered"] = groupSelectsChildren
    
    def configure_pagination(self, enabled=True, paginationAutoPageSize=True, paginationPageSize=10):
        """Configure grid's pagination features

        Args:
            enabled:
                enable or disable pagination.
                Defaults to True.

            paginationAutoPageSize:
                Automatically sets optimal pagination size based on grid Height.
                Defaults to True.

            paginationPageSize:
                Forces page to have this number of rows per page.
                Defaults to 10.
        Returns:
            None
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

    def configure_grid_options(self, **props: dict):
        """Merges key-pair values to gridOptions dictionary.

        Use this method to add any other key-pair values to gridOptions dictionary.
        A complete list of available options can be found in https://www.ag-grid.com/javascript-data-grid/grid-properties/
        
        Returns:
            None
        """
        self.__grid_options.update(props)

    def build(self):
        """Builds the gridOptions dictionary

        Returns:
            dict: Returns a dicionary containing the configured grid options
        """
        self.__grid_options["columnDefs"] = list(
            self.__grid_options["columnDefs"].values()
        )

        return self.__grid_options
