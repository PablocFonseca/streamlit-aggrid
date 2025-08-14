"""
Tests for the collector factory and the new DataReturnMode-based collector selection
"""

import pytest
import pandas as pd
from st_aggrid.shared import DataReturnMode, JsCode
from st_aggrid.collectors.factory import determine_collector, get_collector_info
from st_aggrid.collectors.legacy import LegacyCollector
from st_aggrid.collectors.custom import CustomCollector
from st_aggrid.collectors.minimal import MinimalCollector, MinimalResponse
from st_aggrid.AgGridReturn import AgGridReturn


class TestCollectorFactory:
    """Test the collector factory function"""
    
    def test_determine_collector_minimal_mode(self):
        """Test that MINIMAL mode returns MinimalCollector"""
        collector = determine_collector(data_return_mode=DataReturnMode.MINIMAL)
        assert isinstance(collector, MinimalCollector)
    
    def test_determine_collector_legacy_modes(self):
        """Test that first 3 modes return LegacyCollector"""
        for mode in [DataReturnMode.AS_INPUT, DataReturnMode.FILTERED, DataReturnMode.FILTERED_AND_SORTED]:
            collector = determine_collector(data_return_mode=mode)
            assert isinstance(collector, LegacyCollector)
            assert collector.data_return_mode == mode
    
    def test_determine_collector_custom_js_with_legacy_modes(self):
        """Test that custom JsCode with legacy modes still uses CustomCollector for backward compatibility"""
        custom_js = JsCode("function() { return {}; }")
        
        for mode in [DataReturnMode.AS_INPUT, DataReturnMode.FILTERED, DataReturnMode.FILTERED_AND_SORTED]:
            collector = determine_collector(
                collect_grid_return=custom_js,
                data_return_mode=mode
            )
            assert isinstance(collector, CustomCollector)
    
    def test_determine_collector_custom_js_with_minimal_ignored(self):
        """Test that custom JsCode is ignored when using MINIMAL mode"""
        custom_js = JsCode("function() { return {}; }")
        collector = determine_collector(
            collect_grid_return=custom_js,
            data_return_mode=DataReturnMode.MINIMAL
        )
        # Should still use MinimalCollector, ignoring the custom JS
        assert isinstance(collector, MinimalCollector)
    
    def test_determine_collector_invalid_mode(self):
        """Test that invalid DataReturnMode raises ValueError"""
        with pytest.raises(ValueError, match="Unsupported DataReturnMode"):
            determine_collector(data_return_mode=999)  # Invalid enum value
    
    def test_get_collector_info_minimal(self):
        """Test collector info for MinimalCollector"""
        collector = MinimalCollector()
        info = get_collector_info(collector)
        
        assert info["type"] == "MinimalCollector"
        assert info["return_type"] == "MinimalResponse"
        assert info["data_return_mode"] == "MINIMAL"
        assert info["lightweight"] is True
        assert info["has_custom_logic"] is False
    
    def test_get_collector_info_legacy(self):
        """Test collector info for LegacyCollector"""
        collector = LegacyCollector(
            data_return_mode=DataReturnMode.FILTERED,
            try_to_convert_back_to_original_types=True,
            conversion_errors="coerce"
        )
        info = get_collector_info(collector)
        
        assert info["type"] == "LegacyCollector"
        assert info["return_type"] == "AgGridReturn"
        assert "FILTERED" in str(info["data_return_mode"])  # DataReturnMode.FILTERED shows as '1'
        assert info["try_convert_types"] is True
        assert info["conversion_errors"] == "coerce"
        assert info["has_custom_logic"] is False


class TestMinimalCollector:
    """Test the MinimalCollector functionality"""
    
    def setup_method(self):
        """Set up test data"""
        self.test_data = pd.DataFrame({
            'id': [1, 2, 3],
            'name': ['A', 'B', 'C'],
            'value': [10, 20, 30]
        })
        self.grid_options = {}
        self.collector = MinimalCollector()
    
    def test_create_initial_response(self):
        """Test creating initial MinimalResponse"""
        response = self.collector.create_initial_response(self.test_data, self.grid_options)
        assert isinstance(response, MinimalResponse)
        assert response.raw_data is None
    
    def test_process_response(self):
        """Test processing component value"""
        component_value = {
            'data': [{'id': 1, 'name': 'A', 'value': 10}],
            'selectedRows': [{'id': 1, 'name': 'A', 'value': 10}],
            'customProperty': 'test'
        }
        
        response = self.collector.process_response(component_value, self.test_data, self.grid_options)
        assert isinstance(response, MinimalResponse)
        assert response.raw_data == component_value
    
    def test_update_response(self):
        """Test updating response with component value"""
        response = MinimalResponse()
        component_value = {'data': [{'id': 1}]}
        
        updated_response = self.collector.update_response(response, component_value)
        assert updated_response is response  # Same object
        assert response.raw_data == component_value
    
    def test_get_return_type(self):
        """Test return type description"""
        assert self.collector.get_return_type() == "MinimalResponse"
    
    def test_validate_response(self):
        """Test response validation"""
        assert self.collector.validate_response(MinimalResponse()) is True
        # Create AgGridReturn with required parameters  
        legacy_response = AgGridReturn(originalData=self.test_data)
        assert self.collector.validate_response(legacy_response) is False
        assert self.collector.validate_response("invalid") is False


class TestMinimalResponse:
    """Test the MinimalResponse functionality"""
    
    def setup_method(self):
        """Set up test data"""
        self.component_value = {
            'data': [
                {'id': 1, 'name': 'A', 'value': 10},
                {'id': 2, 'name': 'B', 'value': 20}
            ],
            'selectedRows': [{'id': 1, 'name': 'A', 'value': 10}],
            'customProperty': 'test_value',
            'gridState': {'some': 'state'}
        }
        self.response = MinimalResponse(self.component_value)
    
    def test_raw_data_access(self):
        """Test raw data property"""
        assert self.response.raw_data == self.component_value
    
    def test_data_property(self):
        """Test data property access"""
        assert self.response.data == self.component_value['data']
    
    def test_selected_rows_property(self):
        """Test selected_rows property access"""
        assert self.response.selected_rows == self.component_value['selectedRows']
    
    def test_get_method(self):
        """Test get method with default"""
        assert self.response.get('customProperty') == 'test_value'
        assert self.response.get('nonexistent', 'default') == 'default'
        assert self.response.get('nonexistent') is None
    
    def test_dict_access(self):
        """Test dictionary-style access"""
        assert self.response['customProperty'] == 'test_value'
        assert self.response['data'] == self.component_value['data']
        
        with pytest.raises(KeyError):
            _ = self.response['nonexistent']
    
    def test_contains(self):
        """Test contains operator"""
        assert 'customProperty' in self.response
        assert 'data' in self.response
        assert 'nonexistent' not in self.response
    
    def test_empty_response(self):
        """Test MinimalResponse with no component value"""
        empty_response = MinimalResponse()
        
        assert empty_response.raw_data is None
        assert empty_response.data is None
        assert empty_response.selected_rows == []
        assert empty_response.get('anything') is None
        assert 'anything' not in empty_response
        
        with pytest.raises(KeyError):
            _ = empty_response['anything']
    
    def test_non_dict_component_value(self):
        """Test MinimalResponse with non-dict component value"""
        response = MinimalResponse("not a dict")
        
        assert response.raw_data == "not a dict"
        assert response.data is None
        assert response.selected_rows == []
        assert response.get('anything') is None
        assert 'anything' not in response


if __name__ == "__main__":
    pytest.main([__file__])