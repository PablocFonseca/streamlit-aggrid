import json
from st_aggrid import AgGrid, JsCode
import streamlit as st
import pandas as pd


TESTS = st.radio(
    "Select Test",
    options=range(1, 5),
)

"""grid launches with json data and grid options"""

data = json.dumps(
    [
        {"name": "alice", "age": 25},
        {"name": "bob", "age": 30},
        {"name": "charlie", "age": 35},
        {"name": "diana", "age": 28},
        {"name": "eve", "age": 32},
        {"name": "frank", "age": 27},
        {"name": "grace", "age": 29},
        {"name": "henry", "age": 33},
        {"name": "iris", "age": 26},
        {"name": "jack", "age": 31},
    ]
)


def make_grid():
    go = {
        "columnDefs": [
            {
                "headerName": "First Name",
                "field": "name",
                "editable": True,
                "type": [],
            },
            {
                "headerName": "ages",
                "field": "age",
                "type": ["numericColumn", "numberColumnFilter"],
            },
        ],
        "autoSizeStrategy": {"type": "fitCellContents", "skipHeader": False},
        "rowSelection": {"mode": "multiRow", "checkboxes": True},
    }
    r = AgGrid(data, go, key="event_return_grid")

    st.html(f"""
    <span>
    <h1> Returned Grid Data </h1>
    <pre data-testid='returned-grid-data'>{r.data.to_string()}</pre>
    </span>
    """)

    st.html(f"""
    <span>
    <h1> Event Return Data </h1>
    <pre data-testid='event-return-data'>{str(r.event_data)}</pre>
    </span>
    """)

    st.html(f"""
    <span>
    <h1> Selected Data </h1>
    <pre data-testid='selected-data'>{str(r.selected_data)}</pre>
    </span>
    """)

    st.html(f"""
    <span>
    <h1> Full Grid Response </h1>
    <pre data-testid='full-grid-response'>{str(r.grid_response)}</pre>
    </span>
    """)


@st.cache_resource
def get_dummy_data():
    dummy_data = []
    for i in range(300_00):
        row = {
            "employee_id": f"EMP{i + 1:03d}",
            "first_name": f"FirstName{i + 1}",
            "last_name": f"LastName{i + 1}",
            "email": f"user{i + 1}@company.com",
            "phone": f"555-{1000 + i:04d}",
            "department": ["Engineering", "Sales", "Marketing", "HR", "Finance"][i % 5],
            "position": f"Position{i + 1}",
            "salary": 50000 + (i * 2500),
            "hire_date": f"2023-{(i % 12) + 1:02d}-{(i % 28) + 1:02d}",
            "age": 25 + (i % 40),
            "years_experience": i % 15,
            "performance_rating": round(3.0 + (i % 3) * 0.5, 1),
            "bonus": (i % 5) * 1000,
            "vacation_days": 15 + (i % 10),
            "sick_days": i % 8,
            "training_hours": (i % 20) * 2,
            "projects_completed": i % 12,
            "customer_rating": round(4.0 + (i % 2) * 0.5, 1),
            "office_location": ["New York", "Los Angeles", "Chicago", "Houston"][i % 4],
            "remote_work": i % 2 == 0,
        }
        dummy_data.append(row)
    return json.dumps(dummy_data)


def make_grid2():
    # This functions cotomizes the grid return. In this example we're getting only columns order
    custom_return = JsCode("""
    function collect_return({streamlitRerunEventTriggerName, eventData}){
            let api = eventData.api;
            let colNames = api.getAllDisplayedColumns().map((c) => c.colDef.field);
            return colNames   
        }
    """)

    data = get_dummy_data()
    r = AgGrid(
        data,
        key="custom_event_return_grid",
        data_return_mode="CUSTOM",
        update_on=["columnMoved", "sortChanged"],
        custom_jscode_for_grid_return=custom_return,
        rowSelection={"mode": "singleRow"},
    )

    st.html(f"""
    <span>
    <h1> Custom Grid Return Data (only column names) </h1>
    <pre data-testid='custom-grid-return-data'>{str(r)}</pre>
    </span>
    """)


def make_grid3():
    # Test grouped data functionality with Olympic winners data
    import pathlib

    data_file = str(
        pathlib.Path(__file__).parent.joinpath("olympic-winners.json").absolute()
    )
    go = {
        "columnDefs": [
            {"field": "sport", "rowGroup": True},
            {"field": "athlete", "rowGroup": True},
            {"field": "age", "checkboxSelection": True, "headerCheckboxSelection": True},
        ],
        "defaultColDef": {"width": 150, "cellStyle": {"fontWeight": "bold"}},
        "groupDisplayType": "groupRows",
        "autoGroupColumnDef": {
            "headerName": "Sport",
            "field": "sport",
            "cellRenderer": "agGroupCellRenderer",
            "checkboxSelection": True,
        },
        "rowSelection": "multiple",
    }
    r = AgGrid(
        data_file,
        go,
        key="grouped_data_grid",
        update_on=[
            "gridReady",
            "rowGroupOpened",
            "sortChanged",
            "selectionChanged",
        ],  
        enable_enterprise_modules=True,
    )

    st.html(f"""
    <span>
    <h1> Grouped Data Groups (first 5) </h1>
    <pre data-testid='grouped-data-groups'>{"".join([f"<h4 data-testid='grouped-data-groups-header'>{k}</h4><pre data-testid='grouped-data-groups-data'>{e[k].to_string()}</pre>" for e in r.dataGroups[:5] for k in e])}</pre>
    </span>
    """)

    st.html(f"""
    <span>
    <h1> Grouped Grid Response </h1>
    <pre data-testid='grouped-grid-response'>{str(r.grid_response)}</pre>
    </span>
    """)

    st.html(f"""
    <span>
    <h1> Grouped Grid Selected Data </h1>
    <pre data-testid='grouped-selected-data'>{r.selected_data.to_string() if r.selected_data is not None and len(r.selected_data) > 0 else 'No rows selected'}</pre>
    </span>
    """)

    st.html(f"""
    <span>
    <h1> Grouped Grid Selection Count </h1>
    <pre data-testid='grouped-selection-count'>{len(r.selected_data) if r.selected_data is not None else 0}</pre>
    </span>
    """)

    st.html(f"""
    <span>
    <h1> Selected Grouped Data Groups (first 5) </h1>
    <pre data-testid='selected-grouped-data-groups'>{"".join([f"<h4 data-testid='selected-grouped-data-groups-header'>{k}</h4><pre data-testid='selected-grouped-data-groups-data'>{e[k].to_string()}</pre>" for e in r.selected_dataGroups[:5] for k in e])}</pre>
    </span>
    """)


def make_grid4():
    # Test comprehensive selection functionality
    selection_data = pd.DataFrame({
        'id': range(1, 21),
        'name': [f'User{i}' for i in range(1, 21)],
        'category': ['A', 'B', 'C', 'D', 'E'] * 4,
        'value': [i * 10 for i in range(1, 21)],
        'active': [i % 2 == 0 for i in range(1, 21)]
    })
    
    go = {
        "columnDefs": [
            {"headerName": "ID", "field": "id", "width": 80},
            {"headerName": "Name", "field": "name", "width": 100},
            {"headerName": "Category", "field": "category", "width": 100, "checkboxSelection": True, "headerCheckboxSelection": True},
            {"headerName": "Value", "field": "value", "width": 100},
            {"headerName": "Active", "field": "active", "width": 100}
        ],
        "autoSizeStrategy": {"type": "fitGridWidth"},
        "rowSelection": "multiple",
        "pagination": True,
        "paginationPageSize": 10
    }
    
    r = AgGrid(selection_data, go, key="selection_test_grid")

    st.html(f"""
    <span>
    <h1> Selection Test Grid Data </h1>
    <pre data-testid='selection-grid-data'>{r.data.to_string()}</pre>
    </span>
    """)

    st.html(f"""
    <span>
    <h1> Selected Rows </h1>
    <pre data-testid='selected-rows-data'>{r.selected_data.to_string() if r.selected_data is not None and len(r.selected_data) > 0 else 'No rows selected'}</pre>
    </span>
    """)

    st.html(f"""
    <span>
    <h1> Selection Event Data </h1>
    <pre data-testid='selection-event-data'>{str(r.event_data)}</pre>
    </span>
    """)

    st.html(f"""
    <span>
    <h1> Selection Count </h1>
    <pre data-testid='selection-count'>{len(r.selected_data) if r.selected_data is not None else 0}</pre>
    </span>
    """)


if TESTS == 1:
    make_grid()

if TESTS == 2:
    make_grid2()

if TESTS == 3:
    make_grid3()

if TESTS == 4:
    make_grid4()
