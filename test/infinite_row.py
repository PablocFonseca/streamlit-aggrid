from st_aggrid import AgGrid, JsCode

"""Gets rows from an api as the row scrolls."""

dataSource = JsCode("""
    function(x){
        return {
            rowCount: undefined,
            getRows: (params) => {
                    const {startRow, endRow} = params;
                    let url = `http://localhost:8080/records/?start=${startRow}&count=${endRow-startRow}`;
                    fetch(url)
                    .then((response) => response.json())
                    .then(function (data) {
                        params.successCallback(data, -1)
                    });
            }
        };
    }()
""")

go = {
    "defaultColDef": {"sortable": False},
    "columnDefs": [
        {
            "headerName": "row #",
            "field": "row",
            "flex": 0.5,
        },
        {"headerName": "Measurement Date", "field": "date", "type": [], "flex": 1},
        {"headerName": "City", "field": "city", "type": [], "flex": 1},
        {
            "headerName": "Temperature",
            "field": "temperature",
            "valueFormatter": " value && value.toFixed(2)",
            "type": ["numericColumn"],
            "flex": 2,
        },
    ],
    # "autoSizeStrategy": {"type": "fitCellContents", "skipHeader": False},
    "rowModelType": "infinite",
    "datasource": dataSource,
}


AgGrid(None, go, key="gridOptions_only", allow_unsafe_jscode=True)
