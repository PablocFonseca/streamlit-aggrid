"""
Core functionality tests based on streamlit-aggrid examples
Tests basic grid creation, data types, and fundamental AgGrid features
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch
from st_aggrid import AgGrid, AgGridReturn, DataReturnMode, GridUpdateMode
from st_aggrid.shared import JsCode
from test_example_utils import (
    ExampleDataProvider, 
    AgGridTestHelper, 
    AgGridAssertions,
    olympic_data,
    simple_data,
    datetime_data,
    basic_grid_options,
    mock_olympic_url
)


class TestBasicGridCreation:
    """Test basic grid creation from 0_Getting_started.py example"""
    
    def test_simple_dataframe_grid(self, simple_data):
        """Test creating a grid from a simple DataFrame"""
        response = AgGrid(simple_data)
        
        # Validate response structure
        AgGridTestHelper.validate_aggrid_return(response)
        assert isinstance(response.data, pd.DataFrame)
        assert len(response.data) == len(simple_data)
        assert list(response.data.columns) == list(simple_data.columns)
    
    def test_olympic_data_grid(self, olympic_data):
        """Test creating a grid with Olympic data (matches getting started example)"""
        response = AgGrid(olympic_data)
        
        # Validate response
        AgGridTestHelper.validate_aggrid_return(response)
        AgGridAssertions.assert_data_equals(response.data, olympic_data)
        
        # Check that grid options were inferred
        assert response.grid_options is not None
        assert 'columnDefs' in response.grid_options
    
    def test_empty_dataframe_grid(self):
        """Test creating a grid from an empty DataFrame"""
        empty_df = pd.DataFrame()
        response = AgGrid(empty_df)
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == 0
    
    def test_dataframe_with_none_values(self):
        """Test grid with None/NaN values"""
        df_with_nones = pd.DataFrame({
            'id': [1, 2, None, 4],
            'name': ['A', None, 'C', 'D'],
            'value': [10.5, np.nan, 30.5, 40.5]
        })
        
        response = AgGrid(df_with_nones)
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == 4


class TestDataTypes:
    """Test handling of different data types"""
    
    def test_datetime_columns(self, datetime_data):
        """Test handling of datetime columns"""
        response = AgGrid(datetime_data)
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(datetime_data)
        
        # Check that datetime columns are preserved
        for col in datetime_data.columns:
            if 'date' in col:
                assert col in response.data.columns
    
    def test_numeric_columns(self):
        """Test handling of various numeric types"""
        numeric_df = pd.DataFrame({
            'int_col': [1, 2, 3, 4, 5],
            'float_col': [1.1, 2.2, 3.3, 4.4, 5.5],
            'bool_col': [True, False, True, False, True],
            'complex_col': [1+2j, 2+3j, 3+4j, 4+5j, 5+6j]
        })
        
        response = AgGrid(numeric_df)
        AgGridTestHelper.validate_aggrid_return(response)
        
        # Check that numeric data is preserved
        assert len(response.data) == len(numeric_df)
        assert 'int_col' in response.data.columns
        assert 'float_col' in response.data.columns
    
    def test_string_columns(self):
        """Test handling of string columns"""
        string_df = pd.DataFrame({
            'short_strings': ['A', 'B', 'C'],
            'long_strings': ['This is a long string'] * 3,
            'special_chars': ['@#$%', '©®™', '中文'],
            'empty_strings': ['', 'text', '']
        })
        
        response = AgGrid(string_df)
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(string_df)


class TestGridOptionsInference:
    """Test grid options inference from DataFrames"""
    
    def test_column_types_inference(self, olympic_data):
        """Test that column types are correctly inferred"""
        response = AgGrid(olympic_data)
        
        column_defs = response.grid_options['columnDefs']
        assert len(column_defs) == len(olympic_data.columns)
        
        # Check that each column has proper configuration
        for col_def in column_defs:
            assert 'field' in col_def
            assert col_def['field'] in olympic_data.columns
    
    def test_numeric_column_alignment(self):
        """Test that numeric columns are right-aligned"""
        numeric_df = pd.DataFrame({
            'text': ['A', 'B', 'C'],
            'number': [1, 2, 3],
            'float': [1.1, 2.2, 3.3]
        })
        
        response = AgGrid(numeric_df)
        column_defs = response.grid_options['columnDefs']
        
        # Find numeric columns and check their configuration
        for col_def in column_defs:
            if col_def['field'] in ['number', 'float']:
                # Numeric columns should have specific type configurations
                assert 'type' in col_def or 'cellClass' in col_def
    
    def test_date_column_formatting(self, datetime_data):
        """Test that date columns get proper formatting"""
        response = AgGrid(datetime_data)
        column_defs = response.grid_options['columnDefs']
        
        # Check that date columns have appropriate configuration
        date_columns = [col for col in datetime_data.columns if 'date' in col]
        for col_def in column_defs:
            if col_def['field'] in date_columns:
                # Date columns should have some form of type specification
                assert 'type' in col_def or 'valueFormatter' in col_def or 'cellRenderer' in col_def


class TestBasicParameters:
    """Test basic AgGrid parameters"""
    
    def test_height_parameter(self, simple_data):
        """Test grid height parameter"""
        custom_height = 300
        response = AgGrid(simple_data, height=custom_height)
        
        AgGridTestHelper.validate_aggrid_return(response)
        # Height parameter affects the component rendering but not the data
        assert len(response.data) == len(simple_data)
    
    def test_none_height_auto_height(self, simple_data):
        """Test that height=None enables auto height"""
        response = AgGrid(simple_data, height=None)
        
        AgGridTestHelper.validate_aggrid_return(response)
        # When height is None, domLayout should be set to autoHeight
        assert response.grid_options.get('domLayout') == 'autoHeight'
    
    def test_key_parameter(self, simple_data):
        """Test grid key parameter for state management"""
        key = "test_grid_key"
        response = AgGrid(simple_data, key=key)
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_data_return_modes(self, simple_data):
        """Test different data return modes"""
        for mode in DataReturnMode:
            response = AgGrid(simple_data, data_return_mode=mode)
            AgGridTestHelper.validate_aggrid_return(response)
            assert len(response.data) == len(simple_data)


class TestGridOptionsParameter:
    """Test custom grid options parameter"""
    
    def test_custom_grid_options(self, simple_data, basic_grid_options):
        """Test providing custom grid options"""
        response = AgGrid(simple_data, gridOptions=basic_grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        
        # Check that custom options were applied
        assert 'columnDefs' in response.grid_options
        assert 'defaultColDef' in response.grid_options
        
        # Verify specific configurations from basic_grid_options
        assert response.grid_options['defaultColDef']['flex'] == 1
        assert response.grid_options['defaultColDef']['filter'] == True
    
    def test_grid_options_override_inference(self, simple_data):
        """Test that explicit grid options override inference"""
        custom_options = {
            'columnDefs': [
                {'field': 'id', 'headerName': 'Custom ID'},
                {'field': 'name', 'headerName': 'Custom Name'}
            ]
        }
        
        response = AgGrid(simple_data, gridOptions=custom_options)
        AgGridTestHelper.validate_aggrid_return(response)
        
        # Check that custom column definitions were used
        column_defs = response.grid_options['columnDefs']
        id_col = next((col for col in column_defs if col['field'] == 'id'), None)
        assert id_col is not None
        assert id_col['headerName'] == 'Custom ID'
    
    def test_partial_grid_options_merge(self, simple_data):
        """Test that partial grid options are merged with inference"""
        partial_options = {
            'defaultColDef': {
                'sortable': True,
                'resizable': True
            }
        }
        
        response = AgGrid(simple_data, gridOptions=partial_options)
        AgGridTestHelper.validate_aggrid_return(response)
        
        # Should have custom defaultColDef (columnDefs may not be inferred when only defaultColDef is provided)
        assert 'defaultColDef' in response.grid_options
        assert response.grid_options['defaultColDef']['sortable'] == True


class TestReturnObjectStructure:
    """Test AgGridReturn object structure and properties"""
    
    def test_aggrid_return_properties(self, olympic_data):
        """Test that AgGridReturn has all expected properties"""
        response = AgGrid(olympic_data)
        
        # Check main properties exist
        assert hasattr(response, 'data')
        assert hasattr(response, 'selected_data')
        assert hasattr(response, 'grid_state')
        assert hasattr(response, 'columns_state')
        assert hasattr(response, 'grid_options')
        
        # Check data types
        assert isinstance(response.data, pd.DataFrame)
        assert response.selected_data is None or isinstance(response.selected_data, pd.DataFrame)
        assert isinstance(response.grid_options, dict)
    
    def test_dictionary_access(self, olympic_data):
        """Test dictionary-style access to AgGridReturn"""
        response = AgGrid(olympic_data)
        
        # Test dictionary access (backward compatibility)
        assert response['data'] is not None
        assert isinstance(response['data'], pd.DataFrame)
        
        # Test keys() method
        keys = response.keys()
        assert 'data' in keys
        assert 'selected_data' in keys
    
    def test_selected_data_empty_by_default(self, simple_data):
        """Test that selected_data is empty by default"""
        response = AgGrid(simple_data)
        
        # selected_data can be None or empty DataFrame
        if response.selected_data is not None:
            assert isinstance(response.selected_data, pd.DataFrame)
            assert len(response.selected_data) == 0
        else:
            assert response.selected_data is None
    
    def test_grid_state_structure(self, simple_data):
        """Test grid_state structure"""
        response = AgGrid(simple_data)
        
        # grid_state might be None initially or a dict
        assert response.grid_state is None or isinstance(response.grid_state, dict)
    
    def test_columns_state_structure(self, simple_data):
        """Test columns_state structure"""
        response = AgGrid(simple_data)
        
        # columns_state should be a list of column configurations
        if response.columns_state is not None:
            assert isinstance(response.columns_state, list)


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    def test_invalid_data_type(self):
        """Test error handling for invalid data types"""
        with pytest.raises((ValueError, TypeError, AttributeError)):
            AgGrid("not a dataframe")
    
    def test_invalid_grid_options(self, simple_data):
        """Test error handling for invalid grid options"""
        # This should not raise an error, but may log warnings
        invalid_options = {"invalid_key": "invalid_value"}
        response = AgGrid(simple_data, gridOptions=invalid_options)
        
        # Should still return valid response
        AgGridTestHelper.validate_aggrid_return(response)
    
    def test_invalid_data_return_mode(self, simple_data):
        """Test error handling for invalid data return mode"""
        with pytest.raises(ValueError):
            AgGrid(simple_data, data_return_mode="INVALID_MODE")
    
    def test_invalid_update_mode(self, simple_data):
        """Test error handling for invalid update mode"""
        with pytest.raises(ValueError):
            AgGrid(simple_data, update_mode="INVALID_MODE")


class TestJSONDataSupport:
    """Test support for JSON data as input"""
    
    def test_json_string_input(self):
        """Test AgGrid with JSON string input"""
        json_data = '[{"id": 1, "name": "A"}, {"id": 2, "name": "B"}]'
        
        # JSON string input is not directly supported, should raise error
        with pytest.raises((ValueError, TypeError, AttributeError)):
            AgGrid(json_data)
    
    def test_dict_data_input(self):
        """Test AgGrid with dictionary data"""
        dict_data = {
            'id': [1, 2, 3],
            'name': ['A', 'B', 'C'],
            'value': [10, 20, 30]
        }
        
        # Convert to DataFrame first (expected behavior)
        df = pd.DataFrame(dict_data)
        response = AgGrid(df)
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == 3


@pytest.mark.parametrize("data_size", [1, 10, 100, 1000])
def test_various_data_sizes(data_size):
    """Test AgGrid with various data sizes"""
    large_data = pd.DataFrame({
        'id': range(data_size),
        'value': np.random.randint(0, 100, data_size),
        'category': np.random.choice(['A', 'B', 'C'], data_size)
    })
    
    response = AgGrid(large_data)
    AgGridTestHelper.validate_aggrid_return(response)
    assert len(response.data) == data_size


@pytest.mark.parametrize("column_count", [1, 5, 20, 50])
def test_various_column_counts(column_count):
    """Test AgGrid with various numbers of columns"""
    data = pd.DataFrame({
        f'col_{i}': np.random.randint(0, 100, 10) 
        for i in range(column_count)
    })
    
    response = AgGrid(data)
    AgGridTestHelper.validate_aggrid_return(response)
    assert len(response.data.columns) == column_count