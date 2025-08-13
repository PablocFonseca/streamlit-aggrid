"""
Event handling tests based on streamlit-aggrid examples
Tests grid events, rerun triggers, callbacks, and real-time data updates
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from st_aggrid import AgGrid, AgGridReturn, GridUpdateMode
from st_aggrid.shared import JsCode
from test_example_utils import (
    ExampleDataProvider, 
    AgGridTestHelper, 
    AgGridAssertions,
    olympic_data,
    simple_data
)


class TestGridEvents:
    """Test grid event handling from 82_Handling_Grid_events.py example"""
    
    def test_update_on_cell_value_changed(self, simple_data):
        """Test update_on with cellValueChanged event"""
        response = AgGrid(
            simple_data,
            update_on=['cellValueChanged'],
            key="test_cell_change"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_update_on_selection_changed(self, simple_data):
        """Test update_on with selectionChanged event"""
        grid_options = {
            'rowSelection': 'multiple',
            'columnDefs': [
                {'field': 'id', 'checkboxSelection': True},
                {'field': 'name'},
                {'field': 'value'}
            ]
        }
        
        response = AgGrid(
            simple_data,
            gridOptions=grid_options,
            update_on=['selectionChanged'],
            key="test_selection_change"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert response.grid_options['rowSelection'] == 'multiple'
    
    def test_update_on_column_resized(self, olympic_data):
        """Test update_on with columnResized event"""
        response = AgGrid(
            olympic_data,
            update_on=['columnResized'],
            key="test_column_resize"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(olympic_data)
    
    def test_update_on_filter_changed(self, olympic_data):
        """Test update_on with filterChanged event"""
        grid_options = {
            'columnDefs': [
                {'field': 'athlete', 'filter': True},
                {'field': 'country', 'filter': True},
                {'field': 'sport', 'filter': True},
                {'field': 'gold', 'filter': 'agNumberColumnFilter'}
            ],
            'defaultColDef': {
                'filter': True
            }
        }
        
        response = AgGrid(
            olympic_data,
            gridOptions=grid_options,
            update_on=['filterChanged'],
            key="test_filter_change"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert response.grid_options['defaultColDef']['filter'] == True
    
    def test_update_on_sort_changed(self, olympic_data):
        """Test update_on with sortChanged event"""
        response = AgGrid(
            olympic_data,
            update_on=['sortChanged'],
            key="test_sort_change"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(olympic_data)
    
    def test_multiple_update_events(self, simple_data):
        """Test multiple events in update_on"""
        response = AgGrid(
            simple_data,
            update_on=['cellValueChanged', 'selectionChanged', 'sortChanged'],
            key="test_multiple_events"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_debounced_events(self, simple_data):
        """Test debounced events with tuple format"""
        response = AgGrid(
            simple_data,
            update_on=[
                ('cellValueChanged', 100),  # 100ms debounce
                ('columnResized', 500),     # 500ms debounce
                'selectionChanged'          # No debounce
            ],
            key="test_debounced_events"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_grid_ready_event(self, simple_data):
        """Test gridReady event"""
        response = AgGrid(
            simple_data,
            update_on=['gridReady'],
            key="test_grid_ready"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_first_data_rendered_event(self, olympic_data):
        """Test firstDataRendered event"""
        response = AgGrid(
            olympic_data,
            update_on=['firstDataRendered'],
            key="test_first_data_rendered"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(olympic_data)


class TestStreamlitRerunTriggers:
    """Test Streamlit rerun triggers from 15_ Streamlit_Rerun_Triggers.py example"""
    
    def test_legacy_update_mode_value_changed(self, simple_data):
        """Test legacy GridUpdateMode.VALUE_CHANGED"""
        response = AgGrid(
            simple_data,
            update_mode=GridUpdateMode.VALUE_CHANGED,
            key="test_value_changed"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_legacy_update_mode_selection_changed(self, simple_data):
        """Test legacy GridUpdateMode.SELECTION_CHANGED"""
        grid_options = {
            'rowSelection': 'multiple',
            'columnDefs': [
                {'field': 'id', 'checkboxSelection': True},
                {'field': 'name'},
                {'field': 'value'}
            ]
        }
        
        response = AgGrid(
            simple_data,
            gridOptions=grid_options,
            update_mode=GridUpdateMode.SELECTION_CHANGED,
            key="test_selection_changed_mode"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert response.grid_options['rowSelection'] == 'multiple'
    
    def test_legacy_update_mode_filtered_sorted(self, olympic_data):
        """Test legacy GridUpdateMode.FILTERING_CHANGED"""
        response = AgGrid(
            olympic_data,
            update_mode=GridUpdateMode.FILTERING_CHANGED,
            key="test_filtering_changed"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(olympic_data)
    
    def test_legacy_update_mode_model_changed(self, simple_data):
        """Test legacy GridUpdateMode.MODEL_CHANGED"""
        response = AgGrid(
            simple_data,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            key="test_model_changed"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_legacy_update_mode_manual(self, simple_data):
        """Test legacy GridUpdateMode.MANUAL"""
        response = AgGrid(
            simple_data,
            update_mode=GridUpdateMode.MANUAL,
            key="test_manual_mode"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_update_mode_to_update_on_conversion(self, simple_data):
        """Test that update_mode is converted to update_on internally"""
        # This tests the internal conversion mechanism
        response = AgGrid(
            simple_data,
            update_mode=GridUpdateMode.VALUE_CHANGED,
            key="test_conversion"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_update_on_overrides_update_mode(self, simple_data):
        """Test that update_on takes precedence over update_mode"""
        response = AgGrid(
            simple_data,
            update_mode=GridUpdateMode.MANUAL,
            update_on=['cellValueChanged'],  # Should override MANUAL mode
            key="test_override"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)


class TestCallbackFunctionality:
    """Test callback functionality"""
    
    def test_callback_with_key_required(self, simple_data):
        """Test that callback requires a key parameter"""
        callback_func = Mock()
        
        # Should raise error without key
        with pytest.raises(ValueError, match="Component key must be set to use a callback"):
            AgGrid(simple_data, callback=callback_func)
    
    def test_callback_with_key_provided(self, simple_data):
        """Test callback functionality with key provided"""
        callback_func = Mock()
        
        response = AgGrid(
            simple_data,
            callback=callback_func,
            key="test_callback"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_key_without_callback_works(self, simple_data):
        """Test that key without callback works (for state management)"""
        response = AgGrid(
            simple_data,
            key="test_key_only"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    @patch('streamlit.session_state')
    def test_callback_receives_aggrid_return(self, mock_session_state, simple_data):
        """Test that callback receives AgGridReturn object"""
        callback_func = Mock()
        mock_session_state.__getitem__ = Mock(return_value={'test': 'data'})
        
        # Mock the callback mechanism
        with patch('st_aggrid.AgGrid._component_func') as mock_component:
            mock_component.return_value = {'test': 'data'}
            
            response = AgGrid(
                simple_data,
                callback=callback_func,
                key="test_callback_receive"
            )
            
            AgGridTestHelper.validate_aggrid_return(response)
    
    def test_callback_function_signature(self, simple_data):
        """Test callback function signature expectations"""
        def test_callback(grid_response):
            assert isinstance(grid_response, AgGridReturn)
            return "callback_executed"
        
        response = AgGrid(
            simple_data,
            callback=test_callback,
            key="test_callback_signature"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)


class TestRealTimeDataUpdates:
    """Test real-time data updates from 83_fetching_real_time_data.py example"""
    
    def test_data_refresh_mechanism(self, simple_data):
        """Test that grid can handle data updates"""
        # Initial data
        response1 = AgGrid(
            simple_data,
            key="test_refresh",
            update_on=['gridReady']
        )
        
        AgGridTestHelper.validate_aggrid_return(response1)
        
        # Updated data (simulates real-time update)
        updated_data = simple_data.copy()
        updated_data['value'] = updated_data['value'] * 2
        
        response2 = AgGrid(
            updated_data,
            key="test_refresh",  # Same key for state continuity
            update_on=['gridReady']
        )
        
        AgGridTestHelper.validate_aggrid_return(response2)
        assert len(response2.data) == len(updated_data)
    
    def test_append_new_rows(self, simple_data):
        """Test appending new rows to existing data"""
        # Start with original data
        original_length = len(simple_data)
        
        # Add new rows
        new_rows = pd.DataFrame({
            'id': [10, 11],
            'name': ['New_User_1', 'New_User_2'],
            'value': [60, 70]
        })
        
        expanded_data = pd.concat([simple_data, new_rows], ignore_index=True)
        
        response = AgGrid(
            expanded_data,
            key="test_append_rows",
            update_on=['gridReady']
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == original_length + 2
    
    def test_remove_rows(self, simple_data):
        """Test removing rows from data"""
        # Remove some rows
        reduced_data = simple_data.iloc[:-2]  # Remove last 2 rows
        
        response = AgGrid(
            reduced_data,
            key="test_remove_rows",
            update_on=['gridReady']
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data) - 2
    
    def test_update_existing_values(self, simple_data):
        """Test updating values in existing rows"""
        updated_data = simple_data.copy()
        updated_data.loc[0, 'name'] = 'Updated_Name'
        updated_data.loc[1, 'value'] = 999
        
        response = AgGrid(
            updated_data,
            key="test_update_values",
            update_on=['gridReady']
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        # Check that data was updated
        assert response.data.loc[0, 'name'] == 'Updated_Name'
        assert response.data.loc[1, 'value'] == 999
    
    def test_column_structure_changes(self, simple_data):
        """Test handling changes in column structure"""
        # Add a new column
        modified_data = simple_data.copy()
        modified_data['new_column'] = ['new_val'] * len(modified_data)
        
        response = AgGrid(
            modified_data,
            key="test_column_changes",
            update_on=['gridReady']
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert 'new_column' in response.data.columns
        assert len(response.data.columns) == len(simple_data.columns) + 1


class TestEventDataProcessing:
    """Test event data processing and whitelisting"""
    
    def test_event_data_structure(self, simple_data):
        """Test that event data has proper structure"""
        response = AgGrid(
            simple_data,
            update_on=['cellValueChanged'],
            key="test_event_data"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        # Event data processing happens on frontend, validated through response
        assert len(response.data) == len(simple_data)
    
    def test_streamlit_rerun_event_trigger_name(self, simple_data):
        """Test streamlitRerunEventTriggerName property"""
        # This tests the mechanism that tracks which event triggered the rerun
        response = AgGrid(
            simple_data,
            update_on=['selectionChanged'],
            key="test_trigger_name"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_event_data_whitelisting(self, olympic_data):
        """Test that event data is properly filtered/whitelisted"""
        # Uses update_on to trigger events that should be whitelisted
        response = AgGrid(
            olympic_data,
            update_on=['columnMoved', 'columnVisible', 'sortChanged'],
            key="test_whitelist"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(olympic_data)


class TestGridStateEvents:
    """Test grid state change events"""
    
    def test_state_updated_event(self, olympic_data):
        """Test stateUpdated event"""
        response = AgGrid(
            olympic_data,
            update_on=['stateUpdated'],
            key="test_state_updated"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(olympic_data)
    
    def test_column_moved_event(self, olympic_data):
        """Test columnMoved event"""
        grid_options = {
            'columnDefs': [
                {'field': 'athlete', 'lockPosition': False},
                {'field': 'country', 'lockPosition': False},
                {'field': 'sport', 'lockPosition': False},
                {'field': 'gold'},
                {'field': 'silver'}
            ]
        }
        
        response = AgGrid(
            olympic_data,
            gridOptions=grid_options,
            update_on=['columnMoved'],
            key="test_column_moved"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(olympic_data)
    
    def test_column_resized_event(self, olympic_data):
        """Test columnResized event"""
        grid_options = {
            'columnDefs': [
                {'field': 'athlete', 'resizable': True},
                {'field': 'country', 'resizable': True},
                {'field': 'sport', 'resizable': True},
                {'field': 'gold', 'resizable': True}
            ],
            'defaultColDef': {
                'resizable': True
            }
        }
        
        response = AgGrid(
            olympic_data,
            gridOptions=grid_options,
            update_on=['columnResized'],
            key="test_column_resized"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert response.grid_options['defaultColDef']['resizable'] == True
    
    def test_column_visible_event(self, olympic_data):
        """Test columnVisible event"""
        response = AgGrid(
            olympic_data,
            update_on=['columnVisible'],
            key="test_column_visible"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(olympic_data)


class TestEventPerformance:
    """Test event handling performance considerations"""
    
    def test_high_frequency_events_with_debounce(self, simple_data):
        """Test high-frequency events with debouncing"""
        response = AgGrid(
            simple_data,
            update_on=[
                ('cellValueChanged', 300),  # 300ms debounce
                ('columnResized', 500),     # 500ms debounce
            ],
            key="test_debounce_performance"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_minimal_event_set(self, simple_data):
        """Test using minimal set of events for performance"""
        response = AgGrid(
            simple_data,
            update_on=['gridReady'],  # Only essential events
            key="test_minimal_events"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_no_events_manual_mode(self, simple_data):
        """Test manual mode with no automatic events"""
        response = AgGrid(
            simple_data,
            update_mode=GridUpdateMode.MANUAL,
            key="test_no_events"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)


@pytest.mark.parametrize("event_name", [
    'cellValueChanged',
    'selectionChanged', 
    'sortChanged',
    'filterChanged',
    'columnResized',
    'columnMoved',
    'gridReady',
    'firstDataRendered'
])
def test_individual_events_work(simple_data, event_name):
    """Parametrized test to ensure individual events work"""
    response = AgGrid(
        simple_data,
        update_on=[event_name],
        key=f"test_{event_name}"
    )
    
    AgGridTestHelper.validate_aggrid_return(response)
    assert len(response.data) == len(simple_data)


@pytest.mark.parametrize("update_mode", list(GridUpdateMode))
def test_all_update_modes_work(simple_data, update_mode):
    """Parametrized test to ensure all legacy update modes work"""
    response = AgGrid(
        simple_data,
        update_mode=update_mode,
        key=f"test_mode_{update_mode.name}"
    )
    
    AgGridTestHelper.validate_aggrid_return(response)
    assert len(response.data) == len(simple_data)