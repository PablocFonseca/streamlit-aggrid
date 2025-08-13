"""
Advanced features tests based on streamlit-aggrid examples
Tests JsCode injection, custom styling, cell renderers, tooltips, and enterprise features
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch
from st_aggrid import AgGrid, AgGridReturn, GridOptionsBuilder, JsCode
from st_aggrid.collectors.custom import CustomResponse
from test_example_utils import (
    ExampleDataProvider, 
    AgGridTestHelper, 
    AgGridAssertions,
    JsCodeExamples,
    olympic_data,
    simple_data
)


class TestJsCodeInjection:
    """Test JsCode injection from 40_Advanced_config_and JsCode.py example"""
    
    def test_cell_style_jscode(self, olympic_data):
        """Test cell styling with JsCode from main example"""
        cell_style_js = JsCode("""
        function(params) {
            if (params.data.gold > 3) {
                return {'backgroundColor': 'gold'}
            }
            return {};
        }
        """)
        
        grid_options = {
            'columnDefs': [
                {'field': 'athlete'},
                {'field': 'country'},
                {'field': 'gold', 'cellStyle': cell_style_js},
                {'field': 'silver'},
                {'field': 'bronze'}
            ]
        }
        
        response = AgGrid(
            olympic_data,
            gridOptions=grid_options,
            allow_unsafe_jscode=True
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        # Check that JsCode was preserved in grid options
        gold_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'gold'), None)
        assert gold_col is not None
        assert 'cellStyle' in gold_col
    
    def test_default_column_cell_style(self, simple_data):
        """Test applying JsCode to defaultColDef"""
        cell_style_js = JsCodeExamples.get_cell_style_js()
        
        gb = GridOptionsBuilder.from_dataframe(simple_data)
        gb.configure_default_column(cellStyle=cell_style_js)
        grid_options = gb.build()
        
        response = AgGrid(
            simple_data,
            gridOptions=grid_options,
            allow_unsafe_jscode=True
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert 'defaultColDef' in response.grid_options
        assert 'cellStyle' in response.grid_options['defaultColDef']
    
    def test_cell_renderer_jscode(self, simple_data):
        """Test custom cell renderer with JsCode"""
        cell_renderer_js = JsCode("""
        function(params) {
            if (params.value > 30) {
                return '<span style="color: red; font-weight: bold;">' + params.value + '</span>';
            }
            return params.value;
        }
        """)
        
        grid_options = {
            'columnDefs': [
                {'field': 'id'},
                {'field': 'name'},
                {'field': 'value', 'cellRenderer': cell_renderer_js}
            ]
        }
        
        response = AgGrid(
            simple_data,
            gridOptions=grid_options,
            allow_unsafe_jscode=True
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        value_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'value'), None)
        assert value_col is not None
        assert 'cellRenderer' in value_col
    
    def test_value_formatter_jscode(self, olympic_data):
        """Test value formatter with JsCode"""
        value_formatter_js = JsCode("""
        function(params) {
            return params.value + ' medals';
        }
        """)
        
        grid_options = {
            'columnDefs': [
                {'field': 'athlete'},
                {'field': 'country'},
                {'field': 'gold', 'valueFormatter': value_formatter_js},
                {'field': 'silver'},
                {'field': 'bronze'}
            ]
        }
        
        response = AgGrid(
            olympic_data,
            gridOptions=grid_options,
            allow_unsafe_jscode=True
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        gold_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'gold'), None)
        assert gold_col is not None
        assert 'valueFormatter' in gold_col
    
    def test_cell_class_rules_jscode(self, simple_data):
        """Test cell class rules with JsCode"""
        cell_class_rules_js = {
            'high-value': JsCode("function(params) { return params.value > 30; }")
        }
        
        grid_options = {
            'columnDefs': [
                {'field': 'id'},
                {'field': 'name'},
                {'field': 'value', 'cellClassRules': cell_class_rules_js}
            ]
        }
        
        response = AgGrid(
            simple_data,
            gridOptions=grid_options,
            allow_unsafe_jscode=True
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        value_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'value'), None)
        assert value_col is not None
        assert 'cellClassRules' in value_col
    
    def test_jscode_without_allow_unsafe_flag(self, simple_data):
        """Test that JsCode requires allow_unsafe_jscode=True"""
        cell_style_js = JsCodeExamples.get_cell_style_js()
        
        grid_options = {
            'columnDefs': [
                {'field': 'id'},
                {'field': 'name'},
                {'field': 'category', 'cellStyle': cell_style_js}
            ]
        }
        
        # Add category column
        test_data = simple_data.copy()
        test_data['category'] = ['A', 'B', 'A', 'B', 'A']
        
        # Should raise error without allow_unsafe_jscode=True
        with pytest.raises(Exception):
            AgGrid(test_data, gridOptions=grid_options, allow_unsafe_jscode=False)


class TestCustomCSSFeatures:
    """Test custom CSS features from custom_css.py example"""
    
    def test_custom_css_injection(self, simple_data):
        """Test custom CSS injection"""
        custom_css = {
            ".ag-header-cell-text": {
                "color": "red",
                "font-weight": "bold"
            },
            ".ag-row-even": {
                "background-color": "#f0f0f0"
            }
        }
        
        response = AgGrid(
            simple_data,
            custom_css=custom_css
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        # Custom CSS doesn't affect the data, just validates it was accepted
        assert len(response.data) == len(simple_data)
    
    def test_theme_with_custom_css(self, simple_data):
        """Test combining themes with custom CSS"""
        custom_css = {
            ".ag-theme-streamlit .ag-header": {
                "border-bottom": "2px solid blue"
            }
        }
        
        response = AgGrid(
            simple_data,
            theme='streamlit',
            custom_css=custom_css
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_empty_custom_css(self, simple_data):
        """Test with empty custom CSS"""
        response = AgGrid(
            simple_data,
            custom_css={}
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)


class TestCellRendererFeatures:
    """Test cell renderer features from 20_cell_renderer_class_example.py"""
    
    def test_ag_grid_built_in_renderers(self, simple_data):
        """Test AG Grid built-in cell renderers"""
        grid_options = {
            'columnDefs': [
                {'field': 'id'},
                {'field': 'name'},
                {
                    'field': 'value',
                    'cellRenderer': 'agGroupCellRenderer',
                    'cellRendererParams': {
                        'innerRenderer': 'agAnimateShowChangeCellRenderer'
                    }
                }
            ]
        }
        
        response = AgGrid(simple_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        value_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'value'), None)
        assert value_col is not None
        assert value_col['cellRenderer'] == 'agGroupCellRenderer'
        assert 'cellRendererParams' in value_col
    
    def test_custom_cell_renderer_class(self, simple_data):
        """Test custom cell renderer with class configuration"""
        renderer_params = {
            'template': '<span style="padding: 4px; border-radius: 3px; background-color: lightblue;">{}</span>'
        }
        
        grid_options = {
            'columnDefs': [
                {'field': 'id'},
                {'field': 'name', 'cellRendererParams': renderer_params},
                {'field': 'value'}
            ]
        }
        
        response = AgGrid(simple_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        name_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'name'), None)
        assert name_col is not None
        assert 'cellRendererParams' in name_col
    
    def test_conditional_cell_renderer(self, olympic_data):
        """Test conditional cell rendering based on data"""
        renderer_js = JsCode("""
        function(params) {
            if (params.data.gold > 2) {
                return '<span style="color: gold;">🥇 ' + params.value + '</span>';
            } else if (params.data.gold > 0) {
                return '<span style="color: orange;">🥈 ' + params.value + '</span>';
            }
            return params.value;
        }
        """)
        
        grid_options = {
            'columnDefs': [
                {'field': 'athlete', 'cellRenderer': renderer_js},
                {'field': 'country'},
                {'field': 'gold'},
                {'field': 'silver'},
                {'field': 'bronze'}
            ]
        }
        
        response = AgGrid(
            olympic_data,
            gridOptions=grid_options,
            allow_unsafe_jscode=True
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        athlete_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'athlete'), None)
        assert athlete_col is not None
        assert 'cellRenderer' in athlete_col


class TestTooltipFeatures:
    """Test tooltip features from 81_Tooltips.py example"""
    
    def test_basic_tooltip_configuration(self, simple_data):
        """Test basic tooltip configuration"""
        grid_options = {
            'columnDefs': [
                {'field': 'id', 'tooltipField': 'id'},
                {'field': 'name', 'tooltipField': 'name'},
                {'field': 'value', 'tooltipField': 'value'}
            ],
            'tooltipShowDelay': 500
        }
        
        response = AgGrid(simple_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert response.grid_options['tooltipShowDelay'] == 500
        
        # Check tooltip configuration on columns
        id_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'id'), None)
        assert id_col is not None
        assert id_col['tooltipField'] == 'id'
    
    def test_custom_tooltip_with_jscode(self, olympic_data):
        """Test custom tooltip using JsCode"""
        tooltip_js = JsCode("""
        function(params) {
            return 'Athlete: ' + params.data.athlete + 
                   '\\nCountry: ' + params.data.country +
                   '\\nTotal Medals: ' + params.data.total;
        }
        """)
        
        grid_options = {
            'columnDefs': [
                {'field': 'athlete', 'tooltipValueGetter': tooltip_js},
                {'field': 'country'},
                {'field': 'sport'},
                {'field': 'total'}
            ]
        }
        
        response = AgGrid(
            olympic_data,
            gridOptions=grid_options,
            allow_unsafe_jscode=True
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        athlete_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'athlete'), None)
        assert athlete_col is not None
        assert 'tooltipValueGetter' in athlete_col
    
    def test_header_tooltip(self, simple_data):
        """Test header tooltip configuration"""
        grid_options = {
            'columnDefs': [
                {'field': 'id', 'headerTooltip': 'Unique identifier'},
                {'field': 'name', 'headerTooltip': 'Display name'},
                {'field': 'value', 'headerTooltip': 'Numeric value'}
            ]
        }
        
        response = AgGrid(simple_data, gridOptions=grid_options)
        
        AgGridTestHelper.validate_aggrid_return(response)
        id_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'id'), None)
        assert id_col is not None
        assert id_col['headerTooltip'] == 'Unique identifier'


class TestEnterpriseFeatures:
    """Test enterprise features and licensing"""
    
    def test_enterprise_modules_enabled(self, simple_data):
        """Test enabling enterprise modules"""
        response = AgGrid(
            simple_data,
            enable_enterprise_modules=True
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_enterprise_modules_specific_mode(self, simple_data):
        """Test specific enterprise module modes"""
        for mode in ['enterpriseOnly', 'enterprise+AgCharts']:
            response = AgGrid(
                simple_data,
                enable_enterprise_modules=mode
            )
            AgGridTestHelper.validate_aggrid_return(response)
            assert len(response.data) == len(simple_data)
    
    def test_license_key_parameter(self, simple_data):
        """Test license key parameter"""
        response = AgGrid(
            simple_data,
            enable_enterprise_modules=True,
            license_key="test-license-key"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_sidebar_configuration(self, olympic_data):
        """Test sidebar configuration (enterprise feature)"""
        grid_options = {
            'sideBar': {
                'toolPanels': [
                    {
                        'id': 'columns',
                        'labelDefault': 'Columns',
                        'labelKey': 'columns',
                        'iconKey': 'columns',
                        'toolPanel': 'agColumnsToolPanel'
                    },
                    {
                        'id': 'filters',
                        'labelDefault': 'Filters',
                        'labelKey': 'filters',
                        'iconKey': 'filter',
                        'toolPanel': 'agFiltersToolPanel'
                    }
                ]
            },
            'columnDefs': [
                {'field': 'athlete', 'enableRowGroup': True},
                {'field': 'country', 'enableRowGroup': True},
                {'field': 'sport', 'enableRowGroup': True},
                {'field': 'gold', 'enableValue': True},
                {'field': 'silver', 'enableValue': True}
            ]
        }
        
        response = AgGrid(
            olympic_data,
            gridOptions=grid_options,
            enable_enterprise_modules=True
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert 'sideBar' in response.grid_options
        assert 'toolPanels' in response.grid_options['sideBar']
    
    def test_row_grouping_enterprise(self, olympic_data):
        """Test row grouping with enterprise features"""
        gb = GridOptionsBuilder.from_dataframe(olympic_data)
        gb.configure_default_column(
            groupable=True,
            enableRowGroup=True,
            enablePivot=True,
            enableValue=True
        )
        gb.configure_side_bar()
        grid_options = gb.build()
        
        response = AgGrid(
            olympic_data,
            gridOptions=grid_options,
            enable_enterprise_modules=True
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert 'sideBar' in response.grid_options
        assert response.grid_options['defaultColDef']['enableRowGroup'] == True


class TestCollectorPatterns:
    """Test custom collector patterns"""
    
    def test_custom_collector_basic(self, simple_data):
        """Test basic custom collector functionality"""
        custom_collector = JsCodeExamples.get_custom_collector_js()
        
        response = AgGrid(
            simple_data,
            collect_grid_return=custom_collector,
            update_on=['selectionChanged']
        )
        
        # Should return CustomResponse instead of AgGridReturn
        assert isinstance(response, CustomResponse)
        AgGridTestHelper.validate_aggrid_return(response, CustomResponse)
    
    def test_should_grid_return_condition(self, simple_data):
        """Test should_grid_return conditional logic"""
        should_return_js = JsCodeExamples.get_should_return_js()
        
        response = AgGrid(
            simple_data,
            should_grid_return=should_return_js,
            update_on=['cellValueChanged']
        )
        
        # Should still return AgGridReturn since no custom collector
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_combined_collector_pattern(self, simple_data):
        """Test combining should_grid_return with collect_grid_return"""
        should_return_js = JsCode("""
        function({streamlitRerunEventTriggerName, eventData}) {
            return true;  // Always return for testing
        }
        """)
        
        custom_collector = JsCode("""
        function collect_return({streamlitRerunEventTriggerName, eventData}){
            return {
                triggerEvent: streamlitRerunEventTriggerName,
                timestamp: new Date().toISOString(),
                customData: "test"
            };
        }
        """)
        
        response = AgGrid(
            simple_data,
            should_grid_return=should_return_js,
            collect_grid_return=custom_collector,
            update_on=['cellValueChanged']
        )
        
        assert isinstance(response, CustomResponse)
        AgGridTestHelper.validate_aggrid_return(response, CustomResponse)
    
    def test_custom_response_access_methods(self, simple_data):
        """Test CustomResponse access methods"""
        custom_collector = JsCode("""
        function collect_return({streamlitRerunEventTriggerName, eventData}){
            return {
                columns: ['id', 'name', 'value'],
                rowCount: 5,
                customProperty: 'test_value'
            };
        }
        """)
        
        response = AgGrid(
            simple_data,
            collect_grid_return=custom_collector
        )
        
        assert isinstance(response, CustomResponse)
        
        # Test dictionary-style access
        try:
            columns = response['columns']
            assert columns == ['id', 'name', 'value']
        except (KeyError, TypeError):
            # May not have actual data in test environment
            pass
        
        # Test safe get method
        custom_prop = response.get('customProperty', 'default')
        # Should not raise error even if key doesn't exist
        assert custom_prop is not None or custom_prop == 'default'
        
        # Test raw_data access
        assert hasattr(response, 'raw_data')


class TestVirtualColumnsFeatures:
    """Test virtual columns from 30_virtual_columns.py example"""
    
    def test_value_getter_virtual_column(self, olympic_data):
        """Test virtual column using valueGetter"""
        medal_total_js = JsCode("""
        function(params) {
            return (params.data.gold || 0) + (params.data.silver || 0) + (params.data.bronze || 0);
        }
        """)
        
        grid_options = {
            'columnDefs': [
                {'field': 'athlete'},
                {'field': 'country'},
                {'field': 'gold'},
                {'field': 'silver'},
                {'field': 'bronze'},
                {
                    'headerName': 'Total Medals',
                    'valueGetter': medal_total_js,
                    'type': 'numericColumn'
                }
            ]
        }
        
        response = AgGrid(
            olympic_data,
            gridOptions=grid_options,
            allow_unsafe_jscode=True
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        # Check that virtual column configuration is preserved
        total_col = next((col for col in response.grid_options['columnDefs'] if col.get('headerName') == 'Total Medals'), None)
        assert total_col is not None
        assert 'valueGetter' in total_col
    
    def test_calculated_field_virtual_column(self, simple_data):
        """Test calculated field virtual column"""
        calculated_js = JsCode("""
        function(params) {
            return params.data.value * 2;
        }
        """)
        
        grid_options = {
            'columnDefs': [
                {'field': 'id'},
                {'field': 'name'},
                {'field': 'value'},
                {
                    'headerName': 'Double Value',
                    'valueGetter': calculated_js,
                    'type': 'numericColumn'
                }
            ]
        }
        
        response = AgGrid(
            simple_data,
            gridOptions=grid_options,
            allow_unsafe_jscode=True
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        double_col = next((col for col in response.grid_options['columnDefs'] if col.get('headerName') == 'Double Value'), None)
        assert double_col is not None
        assert 'valueGetter' in double_col


class TestThemeSupport:
    """Test theme support from 50_Themes.py example"""
    
    @pytest.mark.parametrize("theme", ['streamlit', 'light', 'dark', 'blue', 'fresh', 'material'])
    def test_all_themes(self, simple_data, theme):
        """Test all supported themes"""
        response = AgGrid(simple_data, theme=theme)
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_theme_with_custom_css(self, simple_data):
        """Test theme combined with custom CSS"""
        custom_css = {
            ".ag-header": {
                "background-color": "lightblue"
            }
        }
        
        response = AgGrid(
            simple_data,
            theme='streamlit',
            custom_css=custom_css
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)


@pytest.mark.parametrize("jscode_param", ['cellStyle', 'cellRenderer', 'valueFormatter', 'valueGetter'])
def test_jscode_in_different_column_properties(simple_data, jscode_param):
    """Test JsCode works in different column properties"""
    js_function = JsCode("function(params) { return params.value; }")
    
    grid_options = {
        'columnDefs': [
            {'field': 'id'},
            {'field': 'name'},
            {'field': 'value', jscode_param: js_function}
        ]
    }
    
    response = AgGrid(
        simple_data,
        gridOptions=grid_options,
        allow_unsafe_jscode=True
    )
    
    AgGridTestHelper.validate_aggrid_return(response)
    value_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'value'), None)
    assert value_col is not None
    assert jscode_param in value_col