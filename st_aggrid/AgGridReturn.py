from dataclasses import dataclass, field
from typing import Any, List, Mapping, Union, Any
from collections import defaultdict
from st_aggrid.shared import DataReturnMode

import json
import pandas as pd
import numpy as np

class AgGridReturn(Mapping):
    """Class to hold AgGrid call return"""
    __grid_response = {}
    __original_data: Union[pd.DataFrame , str] = pd.DataFrame()
    # selected_rows: List[Mapping] = field(default_factory=list)
    # column_state = None
    # excel_blob = None

    def __init__(self, originalData, component_value=None, data_return_mode=DataReturnMode.AS_INPUT, try_to_convert_back_to_original_types=True, conversion_errors='corce') -> None:
        super().__init__()
        def ddict():
            return defaultdict(ddict)

        self.__dict__= ddict()

        self.__original_data = originalData
        self.__try_to_convert_back_to_original_types = try_to_convert_back_to_original_types
        self.__conversion_errors = conversion_errors
        self.__data_return_mode = data_return_mode


        
        if component_value:
            self.__dict__['grid_response'] = component_value
            self.__dict__['grid_response']['gridOptions'] = json.loads(self.__dict__['grid_response']['gridOptions'])

    @property
    def grid_response(self):
         return self.__dict__['grid_response']
    
    @property
    def rows_id_after_sort_and_filter(self):
        return self.grid_response.get("rowIdsAfterSortAndFilter")
    
    @property
    def rows_id_after_filter(self):
        return self.grid_response.get("rowIdsAfterFilter")
    
    @property
    def grid_options(self):
        return self.grid_response.get("gridOptions",{})
    
    @property
    def columns_state(self):
        return self.grid_response.get("columnsState")
    
    @property
    def grid_state(self):
        return self.grid_response.get("gridState")
    
    @property
    def selected_rows_id(self):
        return self.grid_state.get("rowSelection")
    
    @property
    def data(self):
        data = self.__original_data

        if  self.grid_response :
            data = pd.DataFrame(self.grid_options.get("rowData"))
            
            if "__pandas_index" in data.columns:
                index = pd.Index(data["__pandas_index"].map(str), dtype='str', name='index')
                data.index = index
                del data["__pandas_index"]

            if self.__try_to_convert_back_to_original_types:
                original_types = self.grid_response['originalDtypes']
                try:
                    original_types.pop("__pandas_index")
                except:
                    pass

                numeric_columns = [k for k,v in original_types.items() if v in ['i','u','f']]
                if numeric_columns:
                    data.loc[:,numeric_columns] = data.loc[:,numeric_columns] .apply(pd.to_numeric, errors=self.__conversion_errors )

                text_columns = [k for k,v in original_types.items() if v in ['O','S','U']]

                if text_columns:
                    data.loc[:,text_columns]  = data.loc[:,text_columns].applymap(lambda x: np.nan if x is None else str(x))

                date_columns = [k for k,v in original_types.items() if v == "M"]
                if date_columns:
                    data.loc[:,date_columns] = data.loc[:,date_columns].apply(pd.to_datetime, errors=self.__conversion_errors)

                timedelta_columns = [k for k,v in original_types.items() if v == "m"]
                if timedelta_columns:
                    def cast_to_timedelta(s):
                        try:
                            return pd.Timedelta(s)
                        except:
                            return s

                    data.loc[:,timedelta_columns] = data.loc[:,timedelta_columns].apply(cast_to_timedelta)

        if self.__data_return_mode == DataReturnMode.FILTERED:
            data = data.reindex(index=self.rows_id_after_filter)
        elif self.__data_return_mode == DataReturnMode.FILTERED_AND_SORTED:
            data = data.reindex(index=self.rows_id_after_sort_and_filter)      
        
        return data
    
    #Needs Backwards compatibility 
    #    //selectedRows: this.state.api?.getSelectedRows(),
    # //selectedItems: this.state.api?.getSelectedNodes()?.map((n, i) => ({
    #  //  _selectedRowNodeInfo: { nodeRowIndex: n.rowIndex, nodeId: n.id },
    #  //  ...n.data,
    #  // })),
    
    @property
    def selected_rows(self):
        data = self.__original_data

        if  self.grid_response :
            data = pd.DataFrame(self.grid_options.get("rowData"))

        return data.reindex(index=self.selected_rows_id)



    #Backwards compatibility with dict interface
    def __getitem__(self, __k):
        
        if __k == "data":
            return self.data
        
        return self.__dict__.__getitem__(__k)

    def __iter__(self):
        return self.__dict__.__iter__()
    
    def __len__(self):
        return self.__dict__.__len__()

    def keys(self):
        return self.__dict__.keys()
    
    def values(self):
        return self.__dict__.values()


# @dataclass
# class AgGridReturn(Mapping):
#     """Class to hold AgGrid call return"""
#     data: Union[pd.DataFrame , str] = None
#     selected_rows: List[Mapping] = field(default_factory=list)
#     column_state = None
#     excel_blob = None
#     grid_response = {}

#     @property
#     def columns_state(self)-> List[Mapping]:
#         return self.grid_response.get("columnsState", {})