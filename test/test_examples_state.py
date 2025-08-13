"""
State management tests based on streamlit-aggrid examples
Tests column state persistence, fixed key handling, and session state integration
"""

import pytest
import pandas as pd
import uuid
from unittest.mock import Mock, patch, MagicMock
from st_aggrid import AgGrid, AgGridReturn, GridOptionsBuilder
from st_aggrid.shared import JsCode
from test_example_utils import (
    ExampleDataProvider, 
    AgGridTestHelper, 
    AgGridAssertions,
    olympic_data,
    simple_data
)


class TestColumnStatePersistence:
    """Test column state persistence from 80_saving_columns_state.py example"""
    
    def test_columns_state_property(self, olympic_data):
        """Test that AgGridReturn has columns_state property"""
        response = AgGrid(
            olympic_data,
            update_on=['stateUpdated'],
            key="test_columns_state"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        
        # columns_state should be accessible
        assert hasattr(response, 'columns_state')
        # Should be None initially or a list
        assert response.columns_state is None or isinstance(response.columns_state, list)
    
    def test_columns_state_with_enterprise_features(self, olympic_data):
        """Test columns state with enterprise features enabled"""
        grid_options = {
            'columnDefs': [
                {'field': 'athlete', 'minWidth': 150, 'enableRowGroup': True},
                {'field': 'country', 'minWidth': 150, 'enableRowGroup': True},
                {'field': 'sport', 'minWidth': 150, 'enableRowGroup': True},
                {'field': 'gold', 'enableValue': True},
                {'field': 'silver', 'enableValue': True},
                {'field': 'bronze', 'enableValue': True}
            ],
            'defaultColDef': {
                'flex': 1,
                'minWidth': 100,
                'filter': True,
                'enableRowGroup': True,
                'enablePivot': True,
                'enableValue': True
            },
            'enableRangeSelection': True,
            'sideBar': True,
            'pagination': True,
            'rowSelection': 'multiple',
            'suppressRowClickSelection': True,
            'suppressColumnMoveAnimation': True
        }
        
        response = AgGrid(
            olympic_data,
            gridOptions=grid_options,
            height=400,
            update_on=['stateUpdated'],
            enable_enterprise_modules=True,
            key="test_enterprise_columns_state"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert hasattr(response, 'columns_state')
        assert response.grid_options['sideBar'] == True
        assert response.grid_options['enableRangeSelection'] == True
    
    def test_columns_state_restore(self, olympic_data):
        """Test restoring columns state"""
        # Mock columns state data
        mock_columns_state = [
            {
                'colId': 'athlete',
                'width': 200,
                'hide': False,
                'pinned': None,
                'sort': None,
                'sortIndex': None
            },
            {
                'colId': 'country',
                'width': 150,
                'hide': True,  # Hidden column
                'pinned': None,
                'sort': None,
                'sortIndex': None
            },
            {
                'colId': 'gold',
                'width': 80,
                'hide': False,
                'pinned': 'right',  # Pinned column
                'sort': 'desc',     # Sorted column
                'sortIndex': 0
            }
        ]
        
        grid_options = {
            'columnDefs': [
                {'field': 'athlete', 'minWidth': 150},
                {'field': 'country', 'minWidth': 150},
                {'field': 'sport', 'minWidth': 150},
                {'field': 'gold'},
                {'field': 'silver'},
                {'field': 'bronze'}
            ]
        }
        
        response = AgGrid(
            olympic_data,
            gridOptions=grid_options,
            height=400,
            update_on=['stateUpdated'],
            columns_state=mock_columns_state,
            key="test_restore_columns_state"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(olympic_data)
    
    def test_columns_state_with_custom_configuration(self, olympic_data):
        """Test columns state with custom column configuration"""
        custom_grid_options = {
            'columnDefs': [
                {
                    'field': 'athlete',
                    'headerName': 'Athlete Name',
                    'minWidth': 150,
                    'headerCheckboxSelection': True,
                    'checkboxSelection': True
                },
                {'field': 'age', 'maxWidth': 90},
                {'field': 'country', 'minWidth': 150},
                {'field': 'year', 'maxWidth': 90},
                {'field': 'date', 'minWidth': 150},
                {'field': 'sport', 'minWidth': 150},
                {'field': 'gold'},
                {'field': 'silver'},
                {'field': 'bronze'},
                {'field': 'total'}
            ],
            'defaultColDef': {
                'flex': 1,
                'minWidth': 100,
                'filter': True,
                'enableRowGroup': True,
                'enablePivot': True,
                'enableValue': True
            },
            'enableRangeSelection': True,
            'sideBar': True,
            'pagination': True,
            'rowSelection': 'multiple',
            'suppressRowClickSelection': True,
            'suppressColumnMoveAnimation': True
        }
        
        response = AgGrid(
            olympic_data,
            gridOptions=custom_grid_options,
            height=400,
            update_on=['stateUpdated'],
            enable_enterprise_modules=True,
            key="test_custom_columns_state"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        
        # Check that custom configurations are preserved
        athlete_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'athlete'), None)
        assert athlete_col is not None
        assert athlete_col['headerName'] == 'Athlete Name'
        assert athlete_col['headerCheckboxSelection'] == True
    
    def test_columns_state_none_value(self, simple_data):
        """Test providing None as columns_state"""
        response = AgGrid(
            simple_data,
            columns_state=None,
            key="test_none_columns_state"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_columns_state_empty_list(self, simple_data):
        """Test providing empty list as columns_state"""
        response = AgGrid(
            simple_data,
            columns_state=[],
            key="test_empty_columns_state"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)


class TestFixedKeyHandling:
    """Test fixed key handling from fixed_key_example.py"""
    
    def test_fixed_key_basic(self, simple_data):
        """Test using a fixed key for state persistence"""
        fixed_key = "my_fixed_grid_key"
        
        response = AgGrid(
            simple_data,
            key=fixed_key,
            update_on=['selectionChanged']
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_fixed_key_with_selection(self, olympic_data):
        """Test fixed key with selection functionality"""
        grid_options = {
            'rowSelection': 'multiple',
            'columnDefs': [
                {'field': 'athlete', 'checkboxSelection': True},
                {'field': 'country'},
                {'field': 'sport'},
                {'field': 'gold'},
                {'field': 'silver'},
                {'field': 'bronze'}
            ]
        }
        
        fixed_key = "olympic_selection_grid"
        
        response = AgGrid(
            olympic_data,
            gridOptions=grid_options,
            key=fixed_key,
            update_on=['selectionChanged']
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert response.grid_options['rowSelection'] == 'multiple'
    
    def test_dynamic_vs_fixed_key_behavior(self, simple_data):
        """Test difference between dynamic and fixed keys"""
        # Test with dynamic key (generated each time)
        dynamic_key = f"dynamic_{uuid.uuid4()}"
        
        response_dynamic = AgGrid(
            simple_data,
            key=dynamic_key
        )
        
        AgGridTestHelper.validate_aggrid_return(response_dynamic)
        
        # Test with fixed key (same across runs)
        fixed_key = "persistent_grid"
        
        response_fixed = AgGrid(
            simple_data,
            key=fixed_key
        )
        
        AgGridTestHelper.validate_aggrid_return(response_fixed)
        
        # Both should work, but fixed key enables state persistence
        assert len(response_dynamic.data) == len(simple_data)
        assert len(response_fixed.data) == len(simple_data)
    
    def test_key_with_special_characters(self, simple_data):
        """Test keys with special characters"""
        special_keys = [
            "grid_with_underscores",
            "grid-with-dashes",
            "grid.with.dots",
            "grid123with456numbers"
        ]
        
        for key in special_keys:
            response = AgGrid(
                simple_data,
                key=key
            )
            AgGridTestHelper.validate_aggrid_return(response)
            assert len(response.data) == len(simple_data)
    
    def test_none_key_behavior(self, simple_data):
        """Test behavior when key is None"""
        response = AgGrid(
            simple_data,
            key=None
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)


class TestSessionStateIntegration:
    """Test session state integration and management"""
    
    @patch('streamlit.session_state')
    def test_session_state_access_pattern(self, mock_session_state, simple_data):
        """Test session state access pattern"""
        # Mock session state behavior
        mock_session_state.get.return_value = None
        mock_session_state.__contains__ = Mock(return_value=False)
        
        response = AgGrid(
            simple_data,
            key="test_session_state"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    @patch('streamlit.session_state')
    def test_session_state_with_callback(self, mock_session_state, simple_data):
        """Test session state interaction with callbacks"""
        mock_session_state.__getitem__ = Mock(return_value={'data': 'test'})
        
        callback_func = Mock()
        
        response = AgGrid(
            simple_data,
            callback=callback_func,
            key="test_session_callback"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
    
    def test_state_persistence_across_reruns(self, simple_data):
        """Test state persistence simulation across reruns"""
        key = "persistent_test_grid"
        
        # First "run"
        response1 = AgGrid(
            simple_data,
            key=key,
            update_on=['selectionChanged']
        )
        
        AgGridTestHelper.validate_aggrid_return(response1)
        
        # Second "run" with same key (simulates Streamlit rerun)
        response2 = AgGrid(
            simple_data,
            key=key,
            update_on=['selectionChanged']
        )
        
        AgGridTestHelper.validate_aggrid_return(response2)
        
        # Both responses should have same structure
        assert len(response1.data) == len(response2.data)
        assert list(response1.data.columns) == list(response2.data.columns)
    
    def test_state_isolation_different_keys(self, simple_data):
        """Test that different keys maintain separate state"""
        response1 = AgGrid(
            simple_data,
            key="grid_one"
        )
        
        response2 = AgGrid(
            simple_data,
            key="grid_two"
        )
        
        AgGridTestHelper.validate_aggrid_return(response1)
        AgGridTestHelper.validate_aggrid_return(response2)
        
        # Both should work independently
        assert len(response1.data) == len(simple_data)
        assert len(response2.data) == len(simple_data)


class TestGridResetMechanisms:
    """Test grid reset mechanisms from examples"""
    
    def test_key_change_resets_grid(self, simple_data):
        """Test that changing key resets grid state"""
        # Simulate changing session state key to reset grid
        initial_key = "initial_grid_key"
        reset_key = f"reset_{uuid.uuid4()}"
        
        # Initial grid
        response1 = AgGrid(
            simple_data,
            key=initial_key,
            update_on=['stateUpdated']
        )
        
        AgGridTestHelper.validate_aggrid_return(response1)
        
        # Reset grid with new key
        response2 = AgGrid(
            simple_data,
            key=reset_key,
            update_on=['stateUpdated']
        )
        
        AgGridTestHelper.validate_aggrid_return(response2)
        
        # Both should have fresh state
        assert len(response1.data) == len(simple_data)
        assert len(response2.data) == len(simple_data)
    
    def test_uuid_based_key_generation(self, simple_data):
        """Test UUID-based key generation for resets"""
        # Simulate session state key management
        session_key = str(uuid.uuid4())
        
        response = AgGrid(
            simple_data,
            key=session_key,
            update_on=['stateUpdated']
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_conditional_key_reset(self, simple_data):
        """Test conditional key reset mechanism"""
        # Simulate button-triggered reset
        reset_triggered = True  # Would be st.button() result in real app
        
        if reset_triggered:
            reset_key = f"reset_{uuid.uuid4()}"
        else:
            reset_key = "stable_key"
        
        response = AgGrid(
            simple_data,
            key=reset_key
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)


class TestStateWithDataChanges:
    """Test state management when data changes"""
    
    def test_same_key_different_data(self, simple_data):
        """Test same key with different data"""
        key = "consistent_key"
        
        # First data set
        response1 = AgGrid(
            simple_data,
            key=key
        )
        
        AgGridTestHelper.validate_aggrid_return(response1)
        
        # Different data, same key
        different_data = pd.DataFrame({
            'col1': [1, 2, 3],
            'col2': ['A', 'B', 'C'],
            'col3': [10.1, 20.2, 30.3]
        })
        
        response2 = AgGrid(
            different_data,
            key=key
        )
        
        AgGridTestHelper.validate_aggrid_return(response2)
        
        # Should handle data change gracefully
        assert len(response2.data) == len(different_data)
        assert list(response2.data.columns) == list(different_data.columns)
    
    def test_data_update_preserves_state(self, simple_data):
        """Test that data updates preserve grid state when possible"""
        key = "data_update_test"
        
        # Original data
        response1 = AgGrid(
            simple_data,
            key=key,
            update_on=['stateUpdated']
        )
        
        AgGridTestHelper.validate_aggrid_return(response1)
        
        # Updated data (same structure, different values)
        updated_data = simple_data.copy()
        updated_data['value'] = updated_data['value'] * 2
        
        response2 = AgGrid(
            updated_data,
            key=key,
            update_on=['stateUpdated']
        )
        
        AgGridTestHelper.validate_aggrid_return(response2)
        
        # Should have updated data
        assert len(response2.data) == len(updated_data)
        # Values should be updated (assuming no filtering/sorting applied)
        pd.testing.assert_frame_equal(
            response2.data.reset_index(drop=True),
            updated_data.reset_index(drop=True),
            check_dtype=False
        )
    
    def test_column_addition_with_state(self, simple_data):
        """Test adding columns while preserving state"""
        key = "column_addition_test"
        
        # Original data
        response1 = AgGrid(
            simple_data,
            key=key
        )
        
        AgGridTestHelper.validate_aggrid_return(response1)
        
        # Add new column
        extended_data = simple_data.copy()
        extended_data['new_column'] = ['new'] * len(extended_data)
        
        response2 = AgGrid(
            extended_data,
            key=key
        )
        
        AgGridTestHelper.validate_aggrid_return(response2)
        
        # Should include new column
        assert 'new_column' in response2.data.columns
        assert len(response2.data.columns) == len(simple_data.columns) + 1
    
    def test_column_removal_with_state(self, simple_data):
        """Test removing columns while preserving state"""
        key = "column_removal_test"
        
        # Original data
        response1 = AgGrid(
            simple_data,
            key=key
        )
        
        AgGridTestHelper.validate_aggrid_return(response1)
        
        # Remove a column
        reduced_data = simple_data.drop(columns=['value'])
        
        response2 = AgGrid(
            reduced_data,
            key=key
        )
        
        AgGridTestHelper.validate_aggrid_return(response2)
        
        # Should not include removed column
        assert 'value' not in response2.data.columns
        assert len(response2.data.columns) == len(simple_data.columns) - 1


class TestAdvancedStateManagement:
    """Test advanced state management scenarios"""
    
    def test_state_with_custom_grid_options(self, olympic_data):
        """Test state management with complex grid options"""
        key = "complex_state_test"
        
        complex_options = {
            'columnDefs': [
                {'field': 'athlete', 'pinned': 'left', 'width': 200},
                {'field': 'country', 'rowGroup': True, 'hide': True},
                {'field': 'sport', 'filter': 'agSetColumnFilter'},
                {'field': 'gold', 'sort': 'desc', 'aggFunc': 'sum'},
                {'field': 'silver', 'sort': 'asc', 'aggFunc': 'sum'},
                {'field': 'bronze', 'aggFunc': 'sum'}
            ],
            'defaultColDef': {
                'flex': 1,
                'minWidth': 100,
                'filter': True,
                'sortable': True,
                'resizable': True
            },
            'autoGroupColumnDef': {
                'minWidth': 200
            },
            'groupDefaultExpanded': 1,
            'pagination': True,
            'paginationPageSize': 10
        }
        
        response = AgGrid(
            olympic_data,
            gridOptions=complex_options,
            key=key,
            update_on=['stateUpdated']
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        
        # Verify complex configurations are preserved
        assert response.grid_options['pagination'] == True
        assert response.grid_options['paginationPageSize'] == 10
        assert response.grid_options['groupDefaultExpanded'] == 1
    
    def test_state_with_enterprise_and_callbacks(self, olympic_data):
        """Test state management with enterprise features and callbacks"""
        key = "enterprise_callback_state"
        callback_func = Mock()
        
        response = AgGrid(
            olympic_data,
            enable_enterprise_modules=True,
            callback=callback_func,
            key=key,
            update_on=['stateUpdated', 'selectionChanged']
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(olympic_data)
    
    def test_state_consistency_across_parameters(self, simple_data):
        """Test state consistency when other parameters change"""
        key = "consistency_test"
        
        # First call with basic parameters
        response1 = AgGrid(
            simple_data,
            key=key,
            height=300
        )
        
        AgGridTestHelper.validate_aggrid_return(response1)
        
        # Second call with different height but same key
        response2 = AgGrid(
            simple_data,
            key=key,
            height=500  # Different height
        )
        
        AgGridTestHelper.validate_aggrid_return(response2)
        
        # Data should remain consistent
        pd.testing.assert_frame_equal(
            response1.data.reset_index(drop=True),
            response2.data.reset_index(drop=True),
            check_dtype=False
        )


@pytest.mark.parametrize("key_type", [
    "string_key",
    "key_with_123_numbers",
    "key-with-dashes",
    "key.with.dots",
    "key_with_underscores"
])
def test_various_key_formats(simple_data, key_type):
    """Parametrized test for various key formats"""
    response = AgGrid(
        simple_data,
        key=key_type
    )
    
    AgGridTestHelper.validate_aggrid_return(response)
    assert len(response.data) == len(simple_data)


@pytest.mark.parametrize("state_feature", [
    'columns_state',
    'grid_state',
    'selected_data'
])
def test_state_properties_exist(simple_data, state_feature):
    """Parametrized test to ensure state properties exist"""
    response = AgGrid(
        simple_data,
        key="test_state_properties"
    )
    
    AgGridTestHelper.validate_aggrid_return(response)
    assert hasattr(response, state_feature)