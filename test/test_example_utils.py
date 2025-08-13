"""
Test utilities for streamlit-aggrid examples testing
Provides common data, fixtures, and helper functions for example validation
"""

import pandas as pd
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch
from st_aggrid import AgGridReturn, JsCode
from st_aggrid.collectors.custom import CustomResponse


class ExampleDataProvider:
    """Provides test data that matches the examples"""
    
    @staticmethod
    def get_olympic_data():
        """Returns Olympic data used in many examples"""
        # Mock data that matches the structure of olympic-winners.json
        return pd.DataFrame({
            'athlete': ['Michael Phelps', 'Usain Bolt', 'Katie Ledecky', 'Allyson Felix'],
            'age': [23, 22, 19, 27],
            'country': ['United States', 'Jamaica', 'United States', 'United States'],
            'year': [2008, 2008, 2016, 2012],
            'date': ['24/08/2008', '16/08/2008', '12/08/2016', '11/08/2012'],
            'sport': ['Swimming', 'Athletics', 'Swimming', 'Athletics'],
            'gold': [8, 3, 4, 1],
            'silver': [0, 0, 1, 1],
            'bronze': [0, 0, 1, 0],
            'total': [8, 3, 6, 2]
        })
    
    @staticmethod
    def get_simple_test_data():
        """Returns simple test data for basic tests"""
        return pd.DataFrame({
            'id': range(5),
            'name': [f'User_{i}' for i in range(5)],
            'value': [10, 20, 30, 40, 50],
            'category': ['A', 'B', 'A', 'B', 'A']
        })
    
    @staticmethod
    def get_datetime_test_data():
        """Returns data with various datetime types"""
        return pd.DataFrame({
            'date_time_naive': pd.date_range('2021-01-01', periods=5),
            'date_only': pd.date_range('2020-01-01', periods=5).date,
            'date_tz_aware': pd.date_range('2022-01-01', periods=5, tz='UTC'),
            'value': [10.5, 20.3, 30.7, 40.2, 50.9]
        })


class AgGridTestHelper:
    """Helper methods for testing AgGrid functionality"""
    
    @staticmethod
    def validate_aggrid_return(response, expected_type=AgGridReturn):
        """Validates basic AgGridReturn structure"""
        assert response is not None
        assert isinstance(response, expected_type)
        
        if isinstance(response, AgGridReturn):
            # Check standard AgGridReturn properties
            assert hasattr(response, 'data')
            assert hasattr(response, 'selected_data')
            assert hasattr(response, 'grid_state')
            assert hasattr(response, 'columns_state')
            assert isinstance(response.data, pd.DataFrame)
        elif isinstance(response, CustomResponse):
            # Check CustomResponse properties
            assert hasattr(response, 'raw_data')
            assert hasattr(response, 'get')
            assert callable(response.get)
    
    @staticmethod
    def create_basic_grid_options():
        """Creates basic grid options for testing"""
        return {
            'columnDefs': [
                {'field': 'id', 'maxWidth': 90},
                {'field': 'name', 'minWidth': 150},
                {'field': 'value', 'type': 'numericColumn'}
            ],
            'defaultColDef': {
                'flex': 1,
                'minWidth': 100,
                'filter': True
            }
        }
    
    @staticmethod
    def create_selection_grid_options():
        """Creates grid options with selection enabled"""
        options = AgGridTestHelper.create_basic_grid_options()
        options.update({
            'rowSelection': 'multiple',
            'suppressRowClickSelection': True
        })
        # Add checkbox selection to first column
        options['columnDefs'][0]['headerCheckboxSelection'] = True
        options['columnDefs'][0]['checkboxSelection'] = True
        return options


class MockDataProvider:
    """Provides mock data for external dependencies"""
    
    @staticmethod
    def mock_olympic_json_url():
        """Returns mock Olympic data for URL requests"""
        return ExampleDataProvider.get_olympic_data().to_json(orient='records')
    
    @staticmethod
    def create_temp_olympic_file():
        """Creates a temporary Olympic data file for testing"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        data = ExampleDataProvider.get_olympic_data().to_json(orient='records')
        temp_file.write(data)
        temp_file.close()
        return temp_file.name


class JsCodeExamples:
    """Common JsCode examples used in tests"""
    
    @staticmethod
    def get_cell_style_js():
        """Returns cell styling JsCode from examples"""
        return JsCode("""
        function(params) {
            if (params.value == 'A') {
                return {
                    'color': 'white',
                    'backgroundColor': 'darkred'
                }
            } else {
                return {
                    'color': 'black',
                    'backgroundColor': 'white'
                }
            }
        };
        """)
    
    @staticmethod
    def get_custom_collector_js():
        """Returns custom collector JsCode from examples"""
        return JsCode("""
        function collect_return({streamlitRerunEventTriggerName, eventData}){
            let api = eventData.api;
            if (api) {
                let colNames = api.getAllDisplayedColumns().map((c) => c.colDef.headerName);
                return {
                    columns: colNames,
                    rowCount: api.getDisplayedRowCount(),
                    selectedCount: api.getSelectedRows().length
                };
            }
            return { error: 'No API available' };
        }
        """)
    
    @staticmethod
    def get_should_return_js():
        """Returns should_grid_return JsCode example"""
        return JsCode("""
        function({streamlitRerunEventTriggerName, eventData}) {
            return eventData?.finished === true;
        }
        """)


@pytest.fixture
def olympic_data():
    """Pytest fixture for Olympic data"""
    return ExampleDataProvider.get_olympic_data()


@pytest.fixture
def simple_data():
    """Pytest fixture for simple test data"""
    return ExampleDataProvider.get_simple_test_data()


@pytest.fixture
def datetime_data():
    """Pytest fixture for datetime test data"""
    return ExampleDataProvider.get_datetime_test_data()


@pytest.fixture
def basic_grid_options():
    """Pytest fixture for basic grid options"""
    return AgGridTestHelper.create_basic_grid_options()


@pytest.fixture
def selection_grid_options():
    """Pytest fixture for selection grid options"""
    return AgGridTestHelper.create_selection_grid_options()


@pytest.fixture
def mock_olympic_url():
    """Pytest fixture that mocks Olympic data URL"""
    with patch('pandas.read_json') as mock_read_json:
        mock_read_json.return_value = ExampleDataProvider.get_olympic_data()
        yield "https://www.ag-grid.com/example-assets/olympic-winners.json"


@pytest.fixture
def temp_olympic_file():
    """Pytest fixture that creates a temporary Olympic data file"""
    temp_file = MockDataProvider.create_temp_olympic_file()
    yield temp_file
    # Cleanup
    Path(temp_file).unlink(missing_ok=True)


class AgGridAssertions:
    """Custom assertion methods for AgGrid testing"""
    
    @staticmethod
    def assert_data_equals(response_data, expected_data, check_order=True):
        """Assert that AgGrid response data matches expected data"""
        assert isinstance(response_data, pd.DataFrame)
        assert len(response_data) == len(expected_data)
        
        if check_order:
            pd.testing.assert_frame_equal(
                response_data.reset_index(drop=True),
                expected_data.reset_index(drop=True),
                check_dtype=False
            )
        else:
            # Check that all rows are present regardless of order
            assert set(response_data.columns) == set(expected_data.columns)
            for col in response_data.columns:
                assert sorted(response_data[col].tolist()) == sorted(expected_data[col].tolist())
    
    @staticmethod
    def assert_collector_response(response, collector_type='legacy'):
        """Assert that response matches expected collector type"""
        if collector_type == 'legacy':
            assert isinstance(response, AgGridReturn)
            AgGridTestHelper.validate_aggrid_return(response)
        elif collector_type == 'custom':
            assert isinstance(response, CustomResponse)
            AgGridTestHelper.validate_aggrid_return(response, CustomResponse)
        else:
            raise ValueError(f"Unknown collector type: {collector_type}")
    
    @staticmethod
    def assert_grid_options_valid(grid_options):
        """Assert that grid options are valid"""
        assert isinstance(grid_options, dict)
        # Basic validation that critical properties exist
        assert 'columnDefs' in grid_options or 'rowData' in grid_options