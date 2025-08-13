"""
Data interaction tests based on streamlit-aggrid examples
Tests data return modes, selection, editing, grouping and data manipulation features
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from st_aggrid import AgGrid, AgGridReturn, DataReturnMode, GridUpdateMode, GridOptionsBuilder
from st_aggrid.shared import JsCode
from test_example_utils import (
    ExampleDataProvider, 
    AgGridTestHelper, 
    AgGridAssertions,
    olympic_data,
    simple_data,
    datetime_data,
    basic_grid_options,
    selection_grid_options
)


class TestDataReturnModes:
    """Test different data return modes from 21_Getting AgGrid data.py example"""
    
    def test_as_input_mode(self, olympic_data):
        """Test DataReturnMode.AS_INPUT returns data as originally provided"""
        response = AgGrid(
            olympic_data, 
            data_return_mode=DataReturnMode.AS_INPUT
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        # AS_INPUT should return data in the same order as input
        AgGridAssertions.assert_data_equals(response.data, olympic_data, check_order=True)
    
    def test_filtered_mode(self, olympic_data):
        """Test DataReturnMode.FILTERED returns filtered data in original order"""
        response = AgGrid(
            olympic_data,
            data_return_mode=DataReturnMode.FILTERED
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        # Without any filters applied, should return all data
        assert len(response.data) == len(olympic_data)
        # Should maintain original column structure
        assert list(response.data.columns) == list(olympic_data.columns)
    
    def test_filtered_and_sorted_mode(self, olympic_data):
        """Test DataReturnMode.FILTERED_AND_SORTED (default behavior)"""
        response = AgGrid(
            olympic_data,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        # Should return all data when no filters/sorts are applied
        assert len(response.data) == len(olympic_data)
        assert set(response.data.columns) == set(olympic_data.columns)
    
    def test_data_return_mode_consistency(self, simple_data):
        """Test that different return modes are consistent when no filters applied"""
        modes = [DataReturnMode.AS_INPUT, DataReturnMode.FILTERED, DataReturnMode.FILTERED_AND_SORTED]
        responses = []
        
        for mode in modes:
            response = AgGrid(simple_data, data_return_mode=mode)
            responses.append(response)
        
        # All should have the same number of rows and columns when no filtering
        for response in responses:
            AgGridTestHelper.validate_aggrid_return(response)
            assert len(response.data) == len(simple_data)
            assert set(response.data.columns) == set(simple_data.columns)


class TestSelectionFeatures:
    """Test row selection features from 22_Selecting_data.py example"""
    
    def test_single_selection_grid_options(self, simple_data):
        """Test grid with single row selection enabled"""
        grid_options = {
            'rowSelection': 'single',
            'columnDefs': [
                {'field': 'id', 'checkboxSelection': True},
                {'field': 'name'},
                {'field': 'value'}
            ]
        }
        
        response = AgGrid(simple_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert response.grid_options['rowSelection'] == 'single'
        # selected_data should be empty initially
        if response.selected_data is not None:
            assert len(response.selected_data) == 0
    
    def test_multiple_selection_grid_options(self, simple_data):
        """Test grid with multiple row selection enabled"""
        grid_options = {
            'rowSelection': 'multiple',
            'suppressRowClickSelection': True,
            'columnDefs': [
                {'field': 'id', 'headerCheckboxSelection': True, 'checkboxSelection': True},
                {'field': 'name'},
                {'field': 'value'}
            ]
        }
        
        response = AgGrid(simple_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert response.grid_options['rowSelection'] == 'multiple'
        assert response.grid_options['suppressRowClickSelection'] == True
        if response.selected_data is not None:
            assert len(response.selected_data) == 0
    
    def test_selection_with_grouping(self, olympic_data):
        """Test selection behavior with grouped data"""
        grid_options = {
            'rowSelection': 'multiple',
            'groupSelectsChildren': True,
            'columnDefs': [
                {'field': 'athlete', 'checkboxSelection': True},
                {'field': 'country', 'rowGroup': True, 'hide': True},
                {'field': 'sport'},
                {'field': 'gold'},
                {'field': 'silver'},
                {'field': 'bronze'}
            ],
            'autoGroupColumnDef': {
                'headerCheckboxSelection': True
            }
        }
        
        response = AgGrid(olympic_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert response.grid_options['groupSelectsChildren'] == True
        # Should have grouping configuration
        country_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'country'), None)
        assert country_col is not None
        assert country_col['rowGroup'] == True
    
    def test_selection_configuration_builder(self, simple_data):
        """Test selection using GridOptionsBuilder"""
        gb = GridOptionsBuilder.from_dataframe(simple_data)
        gb.configure_selection(
            selection_mode='multiple',
            use_checkbox=True,
            header_checkbox=True
        )
        grid_options = gb.build()
        
        response = AgGrid(simple_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert response.grid_options['rowSelection'] == 'multiple'


class TestDataGrouping:
    """Test data grouping features from examples"""
    
    def test_basic_grouping(self, olympic_data):
        """Test basic row grouping functionality"""
        grid_options = {
            'columnDefs': [
                {'field': 'athlete', 'minWidth': 150},
                {'field': 'country', 'minWidth': 150, 'rowGroup': True, 'hide': True},
                {'field': 'age', 'maxWidth': 90},
                {'field': 'sport', 'minWidth': 150},
                {'field': 'gold'},
                {'field': 'silver'},
                {'field': 'bronze'},
                {'field': 'total'}
            ],
            'autoGroupColumnDef': {
                'minWidth': 200
            },
            'groupDefaultExpanded': -1  # Expand all groups
        }
        
        response = AgGrid(olympic_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        # Check that grouping configuration is preserved
        country_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'country'), None)
        assert country_col is not None
        assert country_col['rowGroup'] == True
        assert country_col['hide'] == True
    
    def test_multiple_grouping_levels(self, olympic_data):
        """Test multiple levels of grouping"""
        grid_options = {
            'columnDefs': [
                {'field': 'athlete', 'minWidth': 150},
                {'field': 'country', 'rowGroup': True, 'hide': True},
                {'field': 'sport', 'rowGroup': True, 'hide': True},
                {'field': 'age', 'maxWidth': 90},
                {'field': 'gold', 'aggFunc': 'sum'},
                {'field': 'silver', 'aggFunc': 'sum'},
                {'field': 'bronze', 'aggFunc': 'sum'},
                {'field': 'total', 'aggFunc': 'sum'}
            ],
            'autoGroupColumnDef': {
                'minWidth': 200
            }
        }
        
        response = AgGrid(olympic_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        # Verify multiple grouping columns
        grouped_columns = [col for col in response.grid_options['columnDefs'] if col.get('rowGroup')]
        assert len(grouped_columns) >= 2
    
    def test_aggregation_functions(self, olympic_data):
        """Test aggregation functions with grouping"""
        grid_options = {
            'columnDefs': [
                {'field': 'country', 'rowGroup': True, 'hide': True},
                {'field': 'athlete'},
                {'field': 'gold', 'aggFunc': 'sum'},
                {'field': 'silver', 'aggFunc': 'avg'},
                {'field': 'bronze', 'aggFunc': 'max'},
                {'field': 'total', 'aggFunc': 'min'}
            ]
        }
        
        response = AgGrid(olympic_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        # Check that aggregation functions are configured
        gold_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'gold'), None)
        assert gold_col is not None
        assert gold_col['aggFunc'] == 'sum'
    
    def test_grouped_data_property(self, olympic_data):
        """Test dataGroups property for grouped data"""
        grid_options = {
            'columnDefs': [
                {'field': 'country', 'rowGroup': True, 'hide': True},
                {'field': 'athlete'},
                {'field': 'gold'},
                {'field': 'silver'},
                {'field': 'bronze'}
            ]
        }
        
        response = AgGrid(olympic_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        # dataGroups should be available for grouped data
        if hasattr(response, 'dataGroups'):
            assert isinstance(response.dataGroups, list)


class TestDataEditing:
    """Test data editing features from 11_Editing_data.py example"""
    
    def test_editable_columns_configuration(self, simple_data):
        """Test configuration of editable columns"""
        grid_options = {
            'columnDefs': [
                {'field': 'id', 'editable': False},
                {'field': 'name', 'editable': True},
                {'field': 'value', 'editable': True, 'type': 'numericColumn'}
            ],
            'defaultColDef': {
                'editable': True
            }
        }
        
        response = AgGrid(simple_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        # Check editable configuration
        id_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'id'), None)
        assert id_col is not None
        assert id_col['editable'] == False
        
        name_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'name'), None)
        assert name_col is not None
        assert name_col['editable'] == True
    
    def test_cell_editing_with_validators(self, simple_data):
        """Test cell editing with value validation"""
        grid_options = {
            'columnDefs': [
                {'field': 'id'},
                {'field': 'name', 'editable': True},
                {
                    'field': 'value', 
                    'editable': True,
                    'type': 'numericColumn',
                    'cellEditor': 'agNumberCellEditor',
                    'cellEditorParams': {
                        'min': 0,
                        'max': 100
                    }
                }
            ]
        }
        
        response = AgGrid(simple_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        value_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'value'), None)
        assert value_col is not None
        assert 'cellEditor' in value_col
        assert 'cellEditorParams' in value_col
    
    def test_dropdown_cell_editor(self, simple_data):
        """Test dropdown cell editor configuration"""
        grid_options = {
            'columnDefs': [
                {'field': 'id'},
                {'field': 'name', 'editable': True},
                {'field': 'value'},
                {
                    'field': 'category',
                    'editable': True,
                    'cellEditor': 'agSelectCellEditor',
                    'cellEditorParams': {
                        'values': ['A', 'B', 'C']
                    }
                }
            ]
        }
        
        # Add category column to test data
        test_data = simple_data.copy()
        test_data['category'] = ['A', 'B', 'A', 'B', 'C']
        
        response = AgGrid(test_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        category_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'category'), None)
        assert category_col is not None
        assert category_col['cellEditor'] == 'agSelectCellEditor'
    
    def test_edit_type_configuration(self, simple_data):
        """Test different edit types and their configurations"""
        grid_options = {
            'editType': 'fullRow',  # Enable full row editing
            'columnDefs': [
                {'field': 'id', 'editable': False},
                {'field': 'name', 'editable': True},
                {'field': 'value', 'editable': True}
            ]
        }
        
        response = AgGrid(simple_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert response.grid_options['editType'] == 'fullRow'


class TestDataFiltering:
    """Test data filtering features"""
    
    def test_column_filters_configuration(self, olympic_data):
        """Test column filter configuration"""
        grid_options = {
            'columnDefs': [
                {'field': 'athlete', 'filter': 'agTextColumnFilter'},
                {'field': 'country', 'filter': 'agSetColumnFilter'},
                {'field': 'age', 'filter': 'agNumberColumnFilter'},
                {'field': 'year', 'filter': 'agNumberColumnFilter'},
                {'field': 'sport', 'filter': 'agTextColumnFilter'},
                {'field': 'gold', 'filter': 'agNumberColumnFilter'}
            ],
            'defaultColDef': {
                'filter': True,
                'sortable': True
            }
        }
        
        response = AgGrid(olympic_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        # Check that filter configurations are preserved
        athlete_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'athlete'), None)
        assert athlete_col is not None
        assert athlete_col['filter'] == 'agTextColumnFilter'
        
        assert response.grid_options['defaultColDef']['filter'] == True
    
    def test_floating_filter(self, olympic_data):
        """Test floating filter configuration"""
        grid_options = {
            'columnDefs': [
                {'field': 'athlete', 'filter': True, 'floatingFilter': True},
                {'field': 'country', 'filter': True, 'floatingFilter': True},
                {'field': 'sport', 'filter': True, 'floatingFilter': True}
            ],
            'floatingFilter': True
        }
        
        response = AgGrid(olympic_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert response.grid_options['floatingFilter'] == True
    
    def test_external_filter_integration(self, olympic_data):
        """Test external filter integration"""
        grid_options = {
            'columnDefs': [
                {'field': 'athlete'},
                {'field': 'country'},
                {'field': 'sport'},
                {'field': 'gold'}
            ],
            'isExternalFilterPresent': True
        }
        
        response = AgGrid(olympic_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert response.grid_options['isExternalFilterPresent'] == True


class TestDataSorting:
    """Test data sorting features"""
    
    def test_column_sorting_configuration(self, olympic_data):
        """Test column sorting configuration"""
        grid_options = {
            'columnDefs': [
                {'field': 'athlete', 'sortable': True},
                {'field': 'country', 'sortable': True, 'sort': 'asc'},
                {'field': 'gold', 'sortable': True, 'sort': 'desc'},
                {'field': 'year', 'sortable': False}
            ],
            'defaultColDef': {
                'sortable': True
            }
        }
        
        response = AgGrid(olympic_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        # Check sorting configurations
        country_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'country'), None)
        assert country_col is not None
        assert country_col['sort'] == 'asc'
        
        year_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'year'), None)
        assert year_col is not None
        assert year_col['sortable'] == False
    
    def test_multi_column_sorting(self, olympic_data):
        """Test multi-column sorting configuration"""
        grid_options = {
            'columnDefs': [
                {'field': 'country', 'sort': 'asc', 'sortIndex': 0},
                {'field': 'gold', 'sort': 'desc', 'sortIndex': 1},
                {'field': 'athlete'},
                {'field': 'sport'}
            ],
            'multiSortKey': 'ctrl'
        }
        
        response = AgGrid(olympic_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert response.grid_options['multiSortKey'] == 'ctrl'
    
    def test_custom_sorting_comparator(self, simple_data):
        """Test custom sorting with comparator function"""
        custom_comparator = JsCode("""
        function(valueA, valueB, nodeA, nodeB, isInverted) {
            if (valueA == valueB) return 0;
            return (valueA > valueB) ? 1 : -1;
        }
        """)
        
        grid_options = {
            'columnDefs': [
                {'field': 'id'},
                {'field': 'name', 'comparator': custom_comparator},
                {'field': 'value'}
            ]
        }
        
        response = AgGrid(simple_data, gridOptions=grid_options, allow_unsafe_jscode=True)
        
        AgGridTestHelper.validate_aggrid_return(response)
        name_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'name'), None)
        assert name_col is not None
        assert 'comparator' in name_col


class TestPagination:
    """Test pagination features"""
    
    def test_basic_pagination(self, olympic_data):
        """Test basic pagination configuration"""
        grid_options = {
            'pagination': True,
            'paginationPageSize': 10,
            'columnDefs': [
                {'field': 'athlete'},
                {'field': 'country'},
                {'field': 'sport'},
                {'field': 'gold'}
            ]
        }
        
        response = AgGrid(olympic_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert response.grid_options['pagination'] == True
        assert response.grid_options['paginationPageSize'] == 10
    
    def test_auto_pagination_size(self, olympic_data):
        """Test automatic pagination size"""
        grid_options = {
            'pagination': True,
            'paginationAutoPageSize': True,
            'columnDefs': [
                {'field': 'athlete'},
                {'field': 'country'},
                {'field': 'sport'}
            ]
        }
        
        response = AgGrid(olympic_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert response.grid_options['pagination'] == True
        assert response.grid_options['paginationAutoPageSize'] == True
    
    def test_pagination_with_selection(self, olympic_data):
        """Test pagination combined with row selection"""
        grid_options = {
            'pagination': True,
            'paginationPageSize': 5,
            'rowSelection': 'multiple',
            'columnDefs': [
                {'field': 'athlete', 'checkboxSelection': True},
                {'field': 'country'},
                {'field': 'sport'},
                {'field': 'gold'}
            ]
        }
        
        response = AgGrid(olympic_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert response.grid_options['pagination'] == True
        assert response.grid_options['rowSelection'] == 'multiple'


class TestDataTypeConversion:
    """Test data type conversion and preservation"""
    
    def test_type_conversion_enabled(self, datetime_data):
        """Test with type conversion enabled (default)"""
        response = AgGrid(
            datetime_data,
            try_to_convert_back_to_original_types=True,
            conversion_errors='coerce'
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(datetime_data)
    
    def test_type_conversion_disabled(self, datetime_data):
        """Test with type conversion disabled"""
        response = AgGrid(
            datetime_data,
            try_to_convert_back_to_original_types=False
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(datetime_data)
    
    def test_conversion_error_handling(self):
        """Test different conversion error handling modes"""
        problematic_data = pd.DataFrame({
            'mixed_col': ['1', '2', 'not_a_number', '4'],
            'date_col': ['2021-01-01', '2021-01-02', 'not_a_date', '2021-01-04']
        })
        
        # Test different error handling modes
        for error_mode in ['coerce', 'ignore']:
            response = AgGrid(
                problematic_data,
                try_to_convert_back_to_original_types=True,
                conversion_errors=error_mode
            )
            AgGridTestHelper.validate_aggrid_return(response)
            assert len(response.data) == len(problematic_data)
    
    def test_preserve_index(self):
        """Test that DataFrame index is handled properly"""
        data_with_index = pd.DataFrame({
            'name': ['A', 'B', 'C'],
            'value': [1, 2, 3]
        }, index=['x', 'y', 'z'])
        
        response = AgGrid(data_with_index)
        
        AgGridTestHelper.validate_aggrid_return(response)
        # Check that data is properly handled regardless of index
        assert len(response.data) == len(data_with_index)


@pytest.mark.parametrize("data_return_mode", list(DataReturnMode))
def test_all_data_return_modes_work(simple_data, data_return_mode):
    """Parametrized test to ensure all data return modes work"""
    response = AgGrid(simple_data, data_return_mode=data_return_mode)
    AgGridTestHelper.validate_aggrid_return(response)
    assert len(response.data) == len(simple_data)


@pytest.mark.parametrize("selection_mode", ['single', 'multiple'])
def test_all_selection_modes_work(simple_data, selection_mode):
    """Parametrized test to ensure all selection modes work"""
    grid_options = {
        'rowSelection': selection_mode,
        'columnDefs': [
            {'field': 'id', 'checkboxSelection': True},
            {'field': 'name'},
            {'field': 'value'}
        ]
    }
    
    response = AgGrid(simple_data, gridOptions=grid_options)
    AgGridTestHelper.validate_aggrid_return(response)
    assert response.grid_options['rowSelection'] == selection_mode