"""Unit tests for GridOptionsBuilder."""

import pandas as pd
import pytest

from streamlit_aggrid import GridOptionsBuilder


@pytest.fixture
def df():
    return pd.DataFrame(
        {
            "i": [1, 2],
            "f": [1.5, 2.5],
            "s": ["a", "b"],
            "d": pd.to_datetime(["2024-01-01", "2024-01-02"]),
        }
    )


class TestFromDataframe:
    def test_creates_column_defs_for_all_columns(self, df):
        go = GridOptionsBuilder.from_dataframe(df).build()
        assert [c["field"] for c in go["columnDefs"]] == ["i", "f", "s", "d"]

    def test_maps_dtypes_to_column_types(self, df):
        go = GridOptionsBuilder.from_dataframe(df).build()
        types = {c["field"]: c.get("type") for c in go["columnDefs"]}
        assert "numericColumn" in types["i"]
        assert "numericColumn" in types["f"]
        assert types["s"] == []
        assert "dateColumnFilter" in types["d"]

    def test_default_column_parameters_applied(self, df):
        go = GridOptionsBuilder.from_dataframe(df, editable=True).build()
        assert go["defaultColDef"]["editable"] is True


class TestConfigureMethods:
    def test_configure_selection_multiple(self, df):
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_selection("multiple", use_checkbox=True)
        go = gb.build()
        assert go["rowSelection"] == "multiple"

    def test_configure_pagination(self, df):
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_pagination(enabled=True, paginationAutoPageSize=False,
                                paginationPageSize=25)
        go = gb.build()
        assert go["pagination"] is True
        assert go["paginationPageSize"] == 25

    def test_configure_side_bar(self, df):
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_side_bar()
        go = gb.build()
        panel_ids = [p["id"] for p in go["sideBar"]["toolPanels"]]
        assert "filters" in panel_ids
        assert "columns" in panel_ids

    def test_configure_column_overrides(self, df):
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_column("s", header_name="Texto", editable=True)
        go = gb.build()
        col = next(c for c in go["columnDefs"] if c["field"] == "s")
        assert col["headerName"] == "Texto"
        assert col["editable"] is True

    def test_configure_grid_options_passthrough(self, df):
        gb = GridOptionsBuilder.from_dataframe(df)
        gb.configure_grid_options(rowHeight=42)
        go = gb.build()
        assert go["rowHeight"] == 42

    def test_configure_columns_bulk_deprecated_but_works(self, df):
        gb = GridOptionsBuilder.from_dataframe(df)
        with pytest.warns(DeprecationWarning):
            gb.configure_columns(["i", "f"], hide=True)
        go = gb.build()
        cols = {c["field"]: c for c in go["columnDefs"]}
        assert cols["i"]["hide"] is True
        assert cols["f"]["hide"] is True
        assert "hide" not in cols["s"]


class TestBuild:
    def test_build_returns_plain_dict(self, df):
        go = GridOptionsBuilder.from_dataframe(df).build()
        assert isinstance(go, dict)
        assert isinstance(go["columnDefs"], list)
