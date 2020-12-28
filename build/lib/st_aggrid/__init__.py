import os
import streamlit.components.v1 as components
import pandas as pd

_RELEASE = True

class GridOptionsBuilder:

    def __init__(self, min_column_width=100, resizable_columns=True, filterable_columns=True, sorteable_columns=True, pivotable_columns=True, groupable_columns=True, editable_columns=False, side_panel=True):
        self.__grid_options = {}
        self.columnDefs = []
        self.sideBar = {}

        self.min_column_width = min_column_width
        self.resizable_columns = resizable_columns
        self.filterable_columns = filterable_columns
        self.sorteable_columns = sorteable_columns
        self.pivotable_columns = pivotable_columns
        self.groupable_columns = groupable_columns

        self.__col_type_mapper = {
            'datetime64[ns]' :['shortDateColumn'],
        }
        
        self.defaultColDef = {
            'minWidth':  min_column_width,
            'editable': editable_columns,
            'filter':filterable_columns,
            'resizable': resizable_columns,
            'sortable': sorteable_columns,
            'enablePivot': pivotable_columns,
            'enableValue': pivotable_columns,
            'enableRowGroup': groupable_columns,
        }

        if side_panel:
            self.enableSideBar()

    def build_columnsDefs_from_dataframe(self, dataframe):
        self.columnDefs = []
        for col_name, col_type in zip(dataframe.columns, dataframe.dtypes):
            colDef = {
                'headerName': col_name,
                'field': col_name,
                'type': self.__col_type_mapper.get(col_type.name, [])
            }
            self.columnDefs.append(colDef)
    
    def enableSideBar(self, filters_panel=True, columns_panel=True, defaultToolPanel=''):
        filter_panel = {
            'id': 'filters',
            'labelDefault': 'Filters',
            'labelKey': 'filters',
            'iconKey': 'filter',
            'toolPanel': 'agFiltersToolPanel',
                    }
        
        columns_panel = {
            'id': 'filters',
            'labelDefault': 'Filters',
            'labelKey': 'filters',
            'iconKey': 'filter',
            'toolPanel': 'agFiltersToolPanel',
                    }

        self.sideBar = {'toolPanels':[], 'defaultToolPanel':defaultToolPanel}
        if filters_panel:
            self.sideBar['toolPanels'].append(filter_panel)
        if columns_panel:
            self.sideBar['toolPanels'].append(columns_panel)

    def build(self):
        self.__grid_options['columnDefs'] = self.columnDefs
        self.__grid_options['defaultColDef']  = self.defaultColDef
        
        if self.sideBar:
            self.__grid_options['sideBar'] = self.sideBar
        
        return  self.__grid_options

if not _RELEASE:
    _component_func = components.declare_component(
        "agGrid",
        url="http://localhost:3001",
    )
else:
    parent_dir = os.path.dirname(os.path.abspath(__file__))
    build_dir = os.path.join(parent_dir, "frontend/build")
    _component_func = components.declare_component("agGrid", path=build_dir)


def AgGrid(dataframe, gridOptions=None, height=200, key=None):
    """Create a new instance of "AgGrid".
    Parameters
    ----------
    dataframe: Pandas Datafrme
        The dataframe to be displayed on Streamlit
    gridOptions: dict
        A dictionary of options for ag-grid. Documentation on www.ag-grid.com
    key: str or None
        An optional key that uniquely identifies this component. If this is
        None, and the component's arguments are changed, the component will
        be re-mounted in the Streamlit frontend and lose its current state.

    Returns
    -------
    dictionary
        returns a dictionary, grid data is in dictionary's data key. Other keys may be present depending on gridOptions parameters
"""
    response = {}
    response['data'] = dataframe

    #if no gridOptions is passed, builds a default one.
    if gridOptions == None:
        gb = GridOptionsBuilder(min_column_width=100)
        gb.build_columnsDefs_from_dataframe(dataframe)
        gridOptions = gb.build()

    gridData = dataframe.to_json(orient='records', date_format='iso')
    types = [t.name for t in dataframe.dtypes]

    component_value = _component_func(gridOptions=gridOptions, gridData=gridData, key=key, default=None, dtypes=types, height=height)
    if component_value:

        from io import StringIO
        frame = pd.read_csv(StringIO(component_value['csvData']))
        
        dtypes = component_value['dtypes']
        frame = frame.astype({k:v for k,v in zip(frame.columns, dtypes)})

        response['data'] = frame
        response['selected_rows'] = component_value['selectedRows']
    
    return response