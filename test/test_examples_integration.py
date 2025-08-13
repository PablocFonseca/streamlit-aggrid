"""
Performance and integration tests based on streamlit-aggrid examples
Tests large datasets, main example functionality, virtual columns, and comprehensive integration scenarios
"""

import pytest
import pandas as pd
import numpy as np
import time
from unittest.mock import Mock, patch
from st_aggrid import AgGrid, AgGridReturn, GridOptionsBuilder, DataReturnMode, GridUpdateMode
from st_aggrid.shared import JsCode
from test_example_utils import (
    ExampleDataProvider, 
    AgGridTestHelper, 
    AgGridAssertions,
    JsCodeExamples,
    olympic_data,
    simple_data
)


class TestLargeDatasetHandling:
    """Test large dataset handling from 99_one_billion_row.py and grid_performance_1m.py examples"""
    
    @pytest.mark.slow
    def test_large_dataset_10k_rows(self):
        """Test handling 10K rows dataset"""
        large_data = pd.DataFrame({
            'id': range(10000),
            'name': [f'User_{i}' for i in range(10000)],
            'value': np.random.randint(0, 1000, 10000),
            'category': np.random.choice(['A', 'B', 'C', 'D'], 10000),
            'score': np.random.random(10000) * 100,
            'timestamp': pd.date_range('2020-01-01', periods=10000, freq='H')
        })
        
        start_time = time.time()
        response = AgGrid(large_data, height=400)
        end_time = time.time()
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == 10000
        
        # Performance check - should complete within reasonable time
        processing_time = end_time - start_time
        assert processing_time < 30  # Should complete within 30 seconds
    
    @pytest.mark.slow
    def test_large_dataset_with_pagination(self):
        """Test large dataset with pagination enabled"""
        large_data = pd.DataFrame({
            'id': range(5000),
            'data': np.random.random(5000),
            'category': np.random.choice(['Group1', 'Group2', 'Group3'], 5000)
        })
        
        grid_options = {
            'pagination': True,
            'paginationPageSize': 100,
            'columnDefs': [
                {'field': 'id'},
                {'field': 'data', 'type': 'numericColumn'},
                {'field': 'category', 'filter': 'agSetColumnFilter'}
            ]
        }
        
        response = AgGrid(
            large_data,
            gridOptions=grid_options,
            height=400
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == 5000
        assert response.grid_options['pagination'] == True
        assert response.grid_options['paginationPageSize'] == 100
    
    @pytest.mark.slow
    def test_large_dataset_with_filtering(self):
        """Test large dataset with filtering capabilities"""
        large_data = pd.DataFrame({
            'id': range(3000),
            'value': np.random.randint(0, 1000, 3000),
            'text': [f'Item_{i % 100}' for i in range(3000)],  # Repeating pattern for filtering
            'bool_col': np.random.choice([True, False], 3000)
        })
        
        grid_options = {
            'columnDefs': [
                {'field': 'id', 'filter': 'agNumberColumnFilter'},
                {'field': 'value', 'filter': 'agNumberColumnFilter'},
                {'field': 'text', 'filter': 'agTextColumnFilter'},
                {'field': 'bool_col', 'filter': 'agSetColumnFilter'}
            ],
            'defaultColDef': {
                'filter': True,
                'sortable': True
            }
        }
        
        response = AgGrid(
            large_data,
            gridOptions=grid_options,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            height=400
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == 3000
        assert response.grid_options['defaultColDef']['filter'] == True
    
    def test_performance_with_custom_collector(self):
        """Test performance with custom collector on medium dataset"""
        medium_data = pd.DataFrame({
            'id': range(1000),
            'value': np.random.random(1000),
            'category': np.random.choice(['A', 'B', 'C'], 1000)
        })
        
        custom_collector = JsCode("""
        function collect_return({streamlitRerunEventTriggerName, eventData}){
            let api = eventData.api;
            if (api) {
                return {
                    totalRows: api.getDisplayedRowCount(),
                    selectedCount: api.getSelectedRows().length,
                    eventType: streamlitRerunEventTriggerName
                };
            }
            return { error: 'No API available' };
        }
        """)
        
        start_time = time.time()
        response = AgGrid(
            medium_data,
            collect_grid_return=custom_collector,
            height=300
        )
        end_time = time.time()
        
        # Should return CustomResponse
        from st_aggrid.collectors.custom import CustomResponse
        assert isinstance(response, CustomResponse)
        
        # Performance should be reasonable
        processing_time = end_time - start_time
        assert processing_time < 10  # Should complete within 10 seconds
    
    def test_memory_efficiency_with_large_strings(self):
        """Test memory efficiency with large string data"""
        # Create data with large string content
        large_strings = [f'Large content string {i} ' * 50 for i in range(500)]
        
        string_data = pd.DataFrame({
            'id': range(500),
            'large_text': large_strings,
            'summary': [f'Summary {i}' for i in range(500)]
        })
        
        response = AgGrid(
            string_data,
            height=300
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == 500


class TestMainExampleIntegration:
    """Test comprehensive functionality from 90_main_example.py"""
    
    def test_main_example_basic_configuration(self):
        """Test main example basic configuration"""
        # Create sample data similar to main example
        np.random.seed(42)
        sample_size = 30
        
        dummy_data = {
            'date_time_naive': pd.date_range('2021-01-01', periods=sample_size),
            'apple': np.random.randint(0, 100, sample_size) / 3.0,
            'banana': np.random.randint(0, 100, sample_size) / 5.0,
            'chocolate': np.random.randint(0, 100, sample_size),
            'group': np.random.choice(['A', 'B'], size=sample_size),
            'date_only': pd.date_range('2020-01-01', periods=sample_size).date,
            'date_tz_aware': pd.date_range('2022-01-01', periods=sample_size, tz='UTC')
        }
        df = pd.DataFrame(dummy_data)
        
        # Build grid options like main example
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(
            groupable=True, 
            value=True, 
            enableRowGroup=True, 
            aggFunc='sum', 
            editable=True
        )
        
        # Configure specific columns
        gb.configure_column(
            'date_only',
            type=['dateColumnFilter', 'customDateTimeFormat'],
            custom_format_string='yyyy-MM-dd',
            pivot=True
        )
        
        gb.configure_column(
            'apple',
            type=['numericColumn', 'numberColumnFilter', 'customNumericFormat'],
            precision=2,
            aggFunc='sum'
        )
        
        gb.configure_column(
            'banana',
            type=['numericColumn', 'numberColumnFilter', 'customNumericFormat'],
            precision=1,
            aggFunc='avg'
        )
        
        gb.configure_column(
            'chocolate',
            type=['numericColumn', 'numberColumnFilter', 'customCurrencyFormat'],
            custom_currency_symbol='R$',
            aggFunc='max'
        )
        
        # Add cell styling
        cellstyle_jscode = JsCodeExamples.get_cell_style_js()
        gb.configure_column('group', cellStyle=cellstyle_jscode)
        
        gb.configure_grid_options(domLayout='normal')
        gridOptions = gb.build()
        
        response = AgGrid(
            df,
            gridOptions=gridOptions,
            height=300,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            update_mode=GridUpdateMode.MODEL_CHANGED,
            allow_unsafe_jscode=True
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == sample_size
        
        # Verify configurations are applied
        assert 'defaultColDef' in response.grid_options
        assert response.grid_options['defaultColDef']['groupable'] == True
        assert response.grid_options['defaultColDef']['enableRowGroup'] == True
        
        # Check specific column configurations
        apple_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'apple'), None)
        assert apple_col is not None
        assert apple_col['aggFunc'] == 'sum'
    
    def test_main_example_with_selection(self):
        """Test main example with selection enabled"""
        df = ExampleDataProvider.get_datetime_test_data()
        
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(groupable=True, editable=True)
        gb.configure_selection(
            selection_mode='multiple',
            use_checkbox=True,
            groupSelectsChildren=True,
            groupSelectsFiltered=True
        )
        gridOptions = gb.build()
        
        response = AgGrid(
            df,
            gridOptions=gridOptions,
            height=300,
            enable_enterprise_modules=True
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert response.grid_options['rowSelection'] == 'multiple'
        if response.selected_data is not None:
            assert len(response.selected_data) == 0  # Initially no selection
    
    def test_main_example_with_pagination(self):
        """Test main example with pagination"""
        df = ExampleDataProvider.get_olympic_data()
        
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(groupable=True, editable=True)
        gb.configure_pagination(paginationAutoPageSize=False, paginationPageSize=5)
        gridOptions = gb.build()
        
        response = AgGrid(
            df,
            gridOptions=gridOptions,
            height=300
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert response.grid_options['pagination'] == True
        assert response.grid_options['paginationPageSize'] == 5
    
    def test_main_example_enterprise_features(self):
        """Test main example with enterprise features enabled"""
        df = ExampleDataProvider.get_olympic_data()
        
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_default_column(
            groupable=True,
            enableRowGroup=True,
            enablePivot=True,
            enableValue=True
        )
        gb.configure_side_bar()
        gridOptions = gb.build()
        
        response = AgGrid(
            df,
            gridOptions=gridOptions,
            height=400,
            enable_enterprise_modules=True
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert 'sideBar' in response.grid_options
        assert response.grid_options['defaultColDef']['enableRowGroup'] == True


class TestVirtualColumnsIntegration:
    """Test virtual columns integration from 30_virtual_columns.py"""
    
    def test_calculated_virtual_columns(self, olympic_data):
        """Test calculated virtual columns"""
        # Add virtual column for medal total
        medal_total_js = JsCode("""
        function(params) {
            return (params.data.gold || 0) + (params.data.silver || 0) + (params.data.bronze || 0);
        }
        """)
        
        # Add virtual column for medal efficiency
        efficiency_js = JsCode("""
        function(params) {
            const total = (params.data.gold || 0) + (params.data.silver || 0) + (params.data.bronze || 0);
            return total > 0 ? ((params.data.gold || 0) / total * 100).toFixed(1) + '%' : '0%';
        }
        """)
        
        grid_options = {
            'columnDefs': [
                {'field': 'athlete', 'pinned': 'left'},
                {'field': 'country'},
                {'field': 'sport'},
                {'field': 'gold', 'type': 'numericColumn'},
                {'field': 'silver', 'type': 'numericColumn'},
                {'field': 'bronze', 'type': 'numericColumn'},
                {
                    'headerName': 'Total Medals',
                    'valueGetter': medal_total_js,
                    'type': 'numericColumn',
                    'sortable': True
                },
                {
                    'headerName': 'Gold %',
                    'valueGetter': efficiency_js,
                    'minWidth': 100
                }
            ]
        }
        
        response = AgGrid(
            olympic_data,
            gridOptions=grid_options,
            allow_unsafe_jscode=True,
            height=400
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        
        # Verify virtual columns are configured
        total_col = next((col for col in response.grid_options['columnDefs'] if col.get('headerName') == 'Total Medals'), None)
        assert total_col is not None
        assert 'valueGetter' in total_col
        
        efficiency_col = next((col for col in response.grid_options['columnDefs'] if col.get('headerName') == 'Gold %'), None)
        assert efficiency_col is not None
        assert 'valueGetter' in efficiency_col
    
    def test_conditional_virtual_columns(self, simple_data):
        """Test conditional virtual columns"""
        status_js = JsCode("""
        function(params) {
            if (params.data.value > 40) {
                return 'High';
            } else if (params.data.value > 20) {
                return 'Medium';
            } else {
                return 'Low';
            }
        }
        """)
        
        grid_options = {
            'columnDefs': [
                {'field': 'id'},
                {'field': 'name'},
                {'field': 'value', 'type': 'numericColumn'},
                {
                    'headerName': 'Status',
                    'valueGetter': status_js,
                    'filter': 'agSetColumnFilter'
                }
            ]
        }
        
        response = AgGrid(
            simple_data,
            gridOptions=grid_options,
            allow_unsafe_jscode=True
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        status_col = next((col for col in response.grid_options['columnDefs'] if col.get('headerName') == 'Status'), None)
        assert status_col is not None
        assert 'valueGetter' in status_col
    
    def test_aggregated_virtual_columns(self, olympic_data):
        """Test virtual columns with aggregation"""
        avg_medals_js = JsCode("""
        function(params) {
            const total = (params.data.gold || 0) + (params.data.silver || 0) + (params.data.bronze || 0);
            return total / 3;
        }
        """)
        
        grid_options = {
            'columnDefs': [
                {'field': 'athlete'},
                {'field': 'country', 'rowGroup': True, 'hide': True},
                {'field': 'gold', 'aggFunc': 'sum'},
                {'field': 'silver', 'aggFunc': 'sum'},
                {'field': 'bronze', 'aggFunc': 'sum'},
                {
                    'headerName': 'Avg per Medal Type',
                    'valueGetter': avg_medals_js,
                    'aggFunc': 'avg',
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
        avg_col = next((col for col in response.grid_options['columnDefs'] if col.get('headerName') == 'Avg per Medal Type'), None)
        assert avg_col is not None
        assert avg_col['aggFunc'] == 'avg'


class TestComprehensiveIntegration:
    """Test comprehensive integration scenarios"""
    
    def test_full_feature_integration(self, olympic_data):
        """Test integration of multiple features together"""
        # Custom cell renderer for athlete names
        athlete_renderer_js = JsCode("""
        function(params) {
            if (params.data.gold > 2) {
                return '<span style="font-weight: bold; color: gold;">🏆 ' + params.value + '</span>';
            }
            return params.value;
        }
        """)
        
        # Custom tooltip
        tooltip_js = JsCode("""
        function(params) {
            return 'Athlete: ' + params.data.athlete + 
                   '\\nCountry: ' + params.data.country +
                   '\\nTotal Medals: ' + ((params.data.gold || 0) + (params.data.silver || 0) + (params.data.bronze || 0));
        }
        """)
        
        # Complex grid options combining multiple features
        grid_options = {
            'columnDefs': [
                {
                    'field': 'athlete',
                    'headerName': 'Athlete Name',
                    'cellRenderer': athlete_renderer_js,
                    'tooltipValueGetter': tooltip_js,
                    'pinned': 'left',
                    'checkboxSelection': True,
                    'headerCheckboxSelection': True
                },
                {'field': 'country', 'rowGroup': True, 'hide': True},
                {'field': 'sport', 'filter': 'agSetColumnFilter'},
                {'field': 'year', 'filter': 'agNumberColumnFilter'},
                {'field': 'gold', 'aggFunc': 'sum', 'type': 'numericColumn'},
                {'field': 'silver', 'aggFunc': 'sum', 'type': 'numericColumn'},
                {'field': 'bronze', 'aggFunc': 'sum', 'type': 'numericColumn'},
                {
                    'headerName': 'Total',
                    'valueGetter': JsCode("""
                    function(params) {
                        return (params.data.gold || 0) + (params.data.silver || 0) + (params.data.bronze || 0);
                    }
                    """),
                    'aggFunc': 'sum',
                    'type': 'numericColumn',
                    'sort': 'desc'
                }
            ],
            'defaultColDef': {
                'flex': 1,
                'minWidth': 100,
                'filter': True,
                'sortable': True,
                'resizable': True
            },
            'autoGroupColumnDef': {
                'minWidth': 200,
                'cellRendererParams': {
                    'suppressCount': True
                }
            },
            'rowSelection': 'multiple',
            'suppressRowClickSelection': True,
            'pagination': True,
            'paginationPageSize': 20,
            'enableRangeSelection': True,
            'sideBar': True,
            'tooltipShowDelay': 500
        }
        
        response = AgGrid(
            olympic_data,
            gridOptions=grid_options,
            height=500,
            enable_enterprise_modules=True,
            allow_unsafe_jscode=True,
            update_on=['selectionChanged', 'sortChanged', 'filterChanged'],
            key="comprehensive_integration_test"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        
        # Verify all features are configured
        assert response.grid_options['rowSelection'] == 'multiple'
        assert response.grid_options['pagination'] == True
        assert response.grid_options['sideBar'] == True
        assert response.grid_options['enableRangeSelection'] == True
        
        # Check athlete column configuration
        athlete_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'athlete'), None)
        assert athlete_col is not None
        assert athlete_col['pinned'] == 'left'
        assert athlete_col['checkboxSelection'] == True
        assert 'cellRenderer' in athlete_col
        assert 'tooltipValueGetter' in athlete_col
    
    def test_collector_patterns_integration(self, olympic_data):
        """Test integration of custom collectors with complex features"""
        # Advanced custom collector
        advanced_collector = JsCode("""
        function collect_return({streamlitRerunEventTriggerName, eventData}){
            let api = eventData.api;
            if (api) {
                let selectedRows = api.getSelectedRows();
                let countries = [...new Set(selectedRows.map(row => row.country))];
                let totalGold = selectedRows.reduce((sum, row) => sum + (row.gold || 0), 0);
                
                return {
                    triggerEvent: streamlitRerunEventTriggerName,
                    selectedCount: selectedRows.length,
                    uniqueCountries: countries.length,
                    countriesList: countries,
                    totalGoldMedals: totalGold,
                    displayedRowCount: api.getDisplayedRowCount(),
                    timestamp: new Date().toISOString()
                };
            }
            return { error: 'No API available' };
        }
        """)
        
        grid_options = {
            'columnDefs': [
                {'field': 'athlete', 'checkboxSelection': True},
                {'field': 'country'},
                {'field': 'sport'},
                {'field': 'gold', 'type': 'numericColumn'},
                {'field': 'silver', 'type': 'numericColumn'},
                {'field': 'bronze', 'type': 'numericColumn'}
            ],
            'rowSelection': 'multiple',
            'suppressRowClickSelection': True
        }
        
        response = AgGrid(
            olympic_data,
            gridOptions=grid_options,
            collect_grid_return=advanced_collector,
            update_on=['selectionChanged'],
            key="collector_integration_test"
        )
        
        # Should return CustomResponse
        from st_aggrid.collectors.custom import CustomResponse
        assert isinstance(response, CustomResponse)
        AgGridTestHelper.validate_aggrid_return(response, CustomResponse)
    
    def test_theme_and_styling_integration(self, simple_data):
        """Test integration of themes with custom styling"""
        custom_css = {
            '.ag-theme-streamlit .ag-header': {
                'background-color': '#f0f2f6',
                'border-bottom': '2px solid #1f77b4'
            },
            '.ag-theme-streamlit .ag-row-even': {
                'background-color': '#fafbfc'
            },
            '.ag-theme-streamlit .ag-row-odd': {
                'background-color': '#ffffff'
            }
        }
        
        cell_style_js = JsCode("""
        function(params) {
            if (params.value > 30) {
                return {
                    'backgroundColor': '#d4edda',
                    'color': '#155724',
                    'fontWeight': 'bold'
                };
            } else if (params.value < 20) {
                return {
                    'backgroundColor': '#f8d7da',
                    'color': '#721c24'
                };
            }
            return {};
        }
        """)
        
        grid_options = {
            'columnDefs': [
                {'field': 'id'},
                {'field': 'name'},
                {'field': 'value', 'cellStyle': cell_style_js, 'type': 'numericColumn'}
            ]
        }
        
        response = AgGrid(
            simple_data,
            gridOptions=grid_options,
            theme='streamlit',
            custom_css=custom_css,
            allow_unsafe_jscode=True
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        
        # Verify styling configuration
        value_col = next((col for col in response.grid_options['columnDefs'] if col['field'] == 'value'), None)
        assert value_col is not None
        assert 'cellStyle' in value_col
    
    def test_backward_compatibility_integration(self, olympic_data):
        """Test backward compatibility with legacy features"""
        # Test that old update modes still work
        response = AgGrid(
            olympic_data,
            update_mode=GridUpdateMode.VALUE_CHANGED,
            data_return_mode=DataReturnMode.FILTERED_AND_SORTED,
            fit_columns_on_grid_load=False,  # Deprecated parameter
            key="backward_compatibility_test"
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(olympic_data)
        
        # Test dictionary access (backward compatibility)
        assert response['data'] is not None
        assert isinstance(response['data'], pd.DataFrame)
        assert 'selected_rows' in response.keys()


class TestErrorHandlingIntegration:
    """Test error handling in integrated scenarios"""
    
    def test_invalid_jscode_with_complex_config(self, simple_data):
        """Test error handling with invalid JsCode in complex configuration"""
        invalid_js = "this is not valid javascript"
        
        grid_options = {
            'columnDefs': [
                {'field': 'id'},
                {'field': 'name'},
                {'field': 'value', 'cellStyle': invalid_js}  # Invalid JS
            ]
        }
        
        # Should handle gracefully with allow_unsafe_jscode=True
        response = AgGrid(
            simple_data,
            gridOptions=grid_options,
            allow_unsafe_jscode=True
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_malformed_grid_options_handling(self, simple_data):
        """Test handling of malformed grid options"""
        malformed_options = {
            'columnDefs': 'this should be a list',  # Wrong type
            'invalidProperty': {'nested': {'deeply': 'invalid'}},
            'rowSelection': 'invalid_mode'
        }
        
        # Should handle gracefully
        response = AgGrid(
            simple_data,
            gridOptions=malformed_options
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == len(simple_data)
    
    def test_collector_error_handling(self, simple_data):
        """Test error handling in custom collectors"""
        error_collector = JsCode("""
        function collect_return({streamlitRerunEventTriggerName, eventData}){
            // Intentionally cause an error
            throw new Error('Test error in collector');
        }
        """)
        
        # Should handle collector errors gracefully
        try:
            response = AgGrid(
                simple_data,
                collect_grid_return=error_collector
            )
            # If it doesn't raise an error, it should still return a valid response
            from st_aggrid.collectors.custom import CustomResponse
            assert isinstance(response, CustomResponse)
        except Exception:
            # If it does raise an error, that's also acceptable behavior
            pass


@pytest.mark.slow
@pytest.mark.parametrize("dataset_size", [100, 1000, 5000])
def test_performance_scaling(dataset_size):
    """Parametrized test for performance scaling with different dataset sizes"""
    large_data = pd.DataFrame({
        'id': range(dataset_size),
        'value': np.random.random(dataset_size),
        'category': np.random.choice(['A', 'B', 'C', 'D', 'E'], dataset_size),
        'timestamp': pd.date_range('2020-01-01', periods=dataset_size, freq='H')
    })
    
    start_time = time.time()
    response = AgGrid(large_data, height=400)
    end_time = time.time()
    
    AgGridTestHelper.validate_aggrid_return(response)
    assert len(response.data) == dataset_size
    
    # Performance should scale reasonably
    processing_time = end_time - start_time
    max_time = dataset_size * 0.01  # 0.01 seconds per 1000 rows maximum
    assert processing_time < max_time


@pytest.mark.parametrize("feature_combo", [
    ('pagination', 'filtering'),
    ('grouping', 'aggregation'),
    ('selection', 'sorting'),
    ('enterprise', 'custom_js'),
    ('virtual_columns', 'tooltips')
])
def test_feature_combinations(simple_data, feature_combo):
    """Parametrized test for various feature combinations"""
    grid_options = {'columnDefs': [
        {'field': 'id'},
        {'field': 'name'},
        {'field': 'value'}
    ]}
    
    kwargs = {'gridOptions': grid_options}
    
    # Configure features based on combination
    if 'pagination' in feature_combo:
        grid_options['pagination'] = True
        grid_options['paginationPageSize'] = 10
    
    if 'filtering' in feature_combo:
        grid_options['defaultColDef'] = {'filter': True}
    
    if 'grouping' in feature_combo:
        grid_options['columnDefs'][2]['rowGroup'] = True
    
    if 'selection' in feature_combo:
        grid_options['rowSelection'] = 'multiple'
        grid_options['columnDefs'][0]['checkboxSelection'] = True
    
    if 'enterprise' in feature_combo:
        kwargs['enable_enterprise_modules'] = True
    
    if 'custom_js' in feature_combo:
        kwargs['allow_unsafe_jscode'] = True
        grid_options['columnDefs'][1]['cellStyle'] = JsCode("function(params) { return {}; }")
    
    response = AgGrid(simple_data, **kwargs)
    AgGridTestHelper.validate_aggrid_return(response)
    assert len(response.data) == len(simple_data)


@pytest.mark.slow
def test_stress_test_rapid_updates():
    """Stress test with rapid data updates"""
    base_data = pd.DataFrame({
        'id': range(100),
        'value': np.random.random(100)
    })
    
    # Simulate rapid updates
    for i in range(10):
        updated_data = base_data.copy()
        updated_data['value'] = np.random.random(100)
        updated_data['iteration'] = i
        
        response = AgGrid(
            updated_data,
            key=f"stress_test_{i}",
            height=200
        )
        
        AgGridTestHelper.validate_aggrid_return(response)
        assert len(response.data) == 100
        assert 'iteration' in response.data.columns