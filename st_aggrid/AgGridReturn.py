from dataclasses import dataclass, field
from typing import Any, List, Mapping, Union, Any
from collections import defaultdict
from st_aggrid.shared import DataReturnMode

import json
import pandas as pd
import numpy as np
import inspect


class AgGridReturn(Mapping):
    """Class to hold AgGrid call return"""

    # selected_rows: List[Mapping] = field(default_factory=list)
    # column_state = None
    # excel_blob = None

    def __init__(
        self,
        originalData,
        gridOptions=None,
        data_return_mode=DataReturnMode.AS_INPUT,
        try_to_convert_back_to_original_types=True,
        conversion_errors="corce"
    ) -> None:
        super().__init__()

        # def ddict():
        #     return defaultdict(ddict)

        # self.__dict__ = ddict()

        self.__component_value_set = False

        self.__original_data = originalData
        self.__try_to_convert_back_to_original_types = (
            try_to_convert_back_to_original_types
        )
        self.__conversion_errors = conversion_errors
        self.__data_return_mode = data_return_mode

        self.__dict__["grid_response"] = {"gridOptions": gridOptions}
    

    def _set_component_value(self, component_value):
        self.__component_value_set = True

        self.__dict__["grid_response"] = component_value
        self.__dict__["grid_response"]["gridOptions"] = json.loads(
        self.__dict__["grid_response"]["gridOptions"]
            )

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

    def __process_vanilla_df_response(
        self, nodes, __try_to_convert_back_to_original_types
    ):
        data = pd.DataFrame([n.get("data", {}) for n in nodes if not n.get("group", False) == True])

        if "__pandas_index" in data.columns:
            data.index = pd.Index(data["__pandas_index"], name="index")
            del data["__pandas_index"]

        if __try_to_convert_back_to_original_types:
            original_types = self.grid_response["originalDtypes"]
            try:
                original_types.pop("__pandas_index")
            except:
                pass

            numeric_columns = [
                k for k, v in original_types.items() if v in ["i", "u", "f"]
            ]
            if numeric_columns:
                data.loc[:, numeric_columns] = data.loc[:, numeric_columns].apply(
                    pd.to_numeric, errors=self.__conversion_errors
                )

            text_columns = [
                k for k, v in original_types.items() if v in ["O", "S", "U"]
            ]

            if text_columns:
                data.loc[:, text_columns] = data.loc[:, text_columns].applymap(
                    lambda x: np.nan if x is None else str(x)
                )

            date_columns = [k for k, v in original_types.items() if v == "M"]
            if date_columns:
                data.loc[:, date_columns] = data.loc[:, date_columns].apply(
                    pd.to_datetime, errors=self.__conversion_errors
                )

            timedelta_columns = [k for k, v in original_types.items() if v == "m"]
            if timedelta_columns:

                def cast_to_timedelta(s):
                    try:
                        return pd.Timedelta(s)
                    except:
                        return s

                data.loc[:, timedelta_columns] = data.loc[:, timedelta_columns].apply(
                    cast_to_timedelta
                )
  
        return data

    def __process_grouped_response(
        self, nodes, __try_to_convert_back_to_original_types, __data_return_mode
    ):
        def travel_parent(o):

            if o.get("parent", None) == None:
                return ""

            return rf"""{travel_parent(o.get("parent"))}.{o.get("parent").get('key')}""".lstrip(
                "."
            )

        data = [
            {**i.get("data"), **{"parent": travel_parent(i)}}
            for i in nodes
            if i.get("group", False) == False
        ]
        data = pd.DataFrame(data).set_index("__pandas_index")
        data.index.name = ''
        groups = [{tuple(v1.split(".")[1:]): v2.drop('parent', axis=1)} for v1, v2 in data.groupby("parent")]
        return groups

    def __get_data(self, onlySelected):
        data = self.__original_data if not onlySelected else None

        if self.__component_value_set:
            nodes = self.grid_response.get("nodes",[])

            if onlySelected:
                nodes = list(filter(lambda n: n.get('isSelected', False) == True, nodes))

                if not nodes:
                    return None

            data = self.__process_vanilla_df_response(
                    nodes,
                    self.__try_to_convert_back_to_original_types and onlySelected
                )
            

            reindex_ids_map = {
                DataReturnMode.FILTERED: self.rows_id_after_filter,
                DataReturnMode.FILTERED_AND_SORTED:self.rows_id_after_sort_and_filter
            }

            reindex_ids = reindex_ids_map.get(self.__data_return_mode, None)

            if reindex_ids:
                reindex_ids = pd.Index(reindex_ids)
                
                if onlySelected:
                    reindex_ids = reindex_ids.intersection(data.index)

                data = data.reindex(index=reindex_ids)   

        return data
    
    @property
    def data(self):
        "Data from the grid. If rows are grouped, return only the leaf rows"

        return self.__get_data(onlySelected=False)
    
    @property
    def selected_data(self):
        "Selected Data from the grid."
        
        return self.__get_data(onlySelected=True)
        
    def __get_dataGroups(self, onlySelected):
        if self.__component_value_set:
            nodes = self.grid_response.get("nodes",[])

            if onlySelected:
                #n.get('isSelected', True). Default is true bc agGrid sets undefined for half selected groups   
                nodes = list(filter(lambda n: n.get('isSelected', True) == True, nodes))
                
                if not nodes:
                    return [{(''):self.__get_data(onlySelected)}]

            response_has_groups = any((n.get("group", False) for n in nodes))

            if response_has_groups:
                data = self.__process_grouped_response(
                    nodes,
                    self.__try_to_convert_back_to_original_types,
                    self.__data_return_mode,
                )
                return data
        
        return [{(''):self.__get_data(onlySelected)}]
    
    @property
    def dataGroups(self):
        "returns grouped rows as a dictionary where keys are tuples of groupby strings and values are pandas.DataFrame"

        return self.__get_dataGroups(onlySelected=False)
    
    @property
    def selected_dataGroups(self):
        "returns selected rows as a dictionary where keys are tuples of grouped column names and values are pandas.DataFrame"

        return self.__get_dataGroups(onlySelected=True)

    @property
    def selected_rows(self):
        """Returns with selected rows. If there are grouped rows return a dict of {key:pd.DataFrame}"""
        selected_items = pd.DataFrame(self.grid_response.get("selectedItems", {}))
        
        if selected_items.empty:
            return None
        
        if "__pandas_index" in selected_items.columns:
            selected_items.set_index("__pandas_index", inplace=True)
            selected_items.index.name = "index"
        
        return selected_items
    
    #TODO: implement event returns
    @property
    def event_data(self):
        """Returns information about the event that triggered AgGrid Response"""
        return self.grid_response.get("eventData",None)

    # Backwards compatibility with dict interface
    def __getitem__(self, __k):

        try:
            return getattr(self, __k)
        except AttributeError:
             return self.__dict__.__getitem__(__k)

    def __iter__(self):
        attrs = (x for x in inspect.getmembers(self) if not x[0].startswith('_'))
        return attrs.__iter__()

    def __len__(self):
        attrs = [x for x in inspect.getmembers(self) if not x[0].startswith('_')]
        return attrs.__len__()

    def keys(self):
        return [x[0] for x in inspect.getmembers(self) if not x[0].startswith('_')]

    def values(self):
        return [x[1] for x in inspect.getmembers(self) if not x[0].startswith('_')]
