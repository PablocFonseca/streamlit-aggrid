"""Polars-based AG Grid Server-Side Service with embedded FastAPI server."""

import polars as pl
import threading
import uvicorn
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from streamlit_aggrid.server_side_service import (
    ServerSideService,
    ServerSideRequest,
    ServerSideResponse,
    SortModel,
    FilterModel,
    ColumnVO,
)


class _FilterModelAPI(BaseModel):
    filterType: str
    type: Optional[str] = None
    filter: Optional[Any] = None
    filterTo: Optional[Any] = None
    values: Optional[List[Any]] = None
    condition1: Optional[Dict] = None
    condition2: Optional[Dict] = None
    operator: Optional[str] = None


class _SortModelAPI(BaseModel):
    colId: str
    sort: str


class _ColumnVOAPI(BaseModel):
    id: str
    field: str
    displayName: Optional[str] = None
    aggFunc: Optional[str] = None


class _GetRowsRequest(BaseModel):
    startRow: int
    endRow: int
    filterModel: Optional[Dict[str, _FilterModelAPI]] = {}
    sortModel: Optional[List[_SortModelAPI]] = []
    rowGroupCols: Optional[List[_ColumnVOAPI]] = []
    valueCols: Optional[List[_ColumnVOAPI]] = []
    pivotCols: Optional[List[_ColumnVOAPI]] = []
    pivotMode: Optional[bool] = False
    groupKeys: Optional[List[str]] = []


class _GetRowsResponse(BaseModel):
    rows: List[Dict[str, Any]]
    lastRow: Optional[int] = None
    pivotResultFields: Optional[List[str]] = None


class PolarsServerService(ServerSideService):
    """
    Self-contained Polars server-side service with embedded FastAPI server.

    Usage:
        df = pl.DataFrame({...})
        service = PolarsServerService(df, port=8000)
        # Server starts automatically
    """

    def __init__(
        self,
        df: pl.DataFrame,
        port: int = 8000,
        host: str = "127.0.0.1",
        auto_start: bool = True
    ):
        if not isinstance(df, pl.DataFrame):
            raise TypeError(f"Expected pl.DataFrame, got {type(df)}")

        self.df = df
        self._port = port
        self._host = host
        self._lock = threading.Lock()
        self._server_thread = None
        self._running = False
        self._app = self._create_app()

        if auto_start:
            self.start(port, host)

    def _create_app(self) -> FastAPI:
        """Create FastAPI application with endpoints."""
        app = FastAPI(title="AG Grid Server-Side Service")

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        @app.post("/getData", response_model=_GetRowsResponse)
        async def get_data(request: _GetRowsRequest = Body(...)):
            server_request = self._convert_api_request(request)
            response = self.get_rows(server_request)
            return _GetRowsResponse(
                rows=response.data,
                lastRow=response.rowCount,
                pivotResultFields=response.pivotFields
            )

        @app.get("/getUniqueValues/{column}")
        async def get_unique_values(column: str):
            with self._lock:
                if column in self.df.columns:
                    unique = sorted(self.df[column].unique().to_list())
                    return {"values": unique}
                return {"values": []}

        @app.get("/health")
        async def health():
            return {"status": "healthy", "rows": self.df.height}

        return app

    def _convert_api_request(self, api_req: _GetRowsRequest) -> ServerSideRequest:
        """Convert FastAPI request to internal ServerSideRequest."""
        filter_model = {
            col_id: FilterModel(
                filterType=f.filterType,
                type=f.type,
                filter=f.filter,
                filterTo=f.filterTo,
                values=f.values,
                condition1=f.condition1,
                condition2=f.condition2,
                operator=f.operator,
            )
            for col_id, f in (api_req.filterModel or {}).items()
        }

        sort_model = [
            SortModel(colId=s.colId, sort=s.sort) for s in (api_req.sortModel or [])
        ]

        row_group_cols = [
            ColumnVO(id=c.id, displayName=c.displayName, field=c.field, aggFunc=c.aggFunc)
            for c in (api_req.rowGroupCols or [])
        ]

        value_cols = [
            ColumnVO(id=c.id, displayName=c.displayName, field=c.field, aggFunc=c.aggFunc)
            for c in (api_req.valueCols or [])
        ]

        pivot_cols = [
            ColumnVO(id=c.id, displayName=c.displayName, field=c.field, aggFunc=c.aggFunc)
            for c in (api_req.pivotCols or [])
        ]

        return ServerSideRequest(
            startRow=api_req.startRow,
            endRow=api_req.endRow,
            rowGroupCols=row_group_cols,
            valueCols=value_cols,
            pivotCols=pivot_cols,
            pivotMode=api_req.pivotMode or False,
            groupKeys=api_req.groupKeys or [],
            filterModel=filter_model,
            sortModel=sort_model,
        )

    def get_rows(self, request: ServerSideRequest) -> ServerSideResponse:
        """Process AG Grid data request."""
        with self._lock:
            result = self.df

            # Apply filters
            if request.filterModel:
                result = self._apply_filters(result, request.filterModel)

            # Handle pivoting
            is_pivoting = request.pivotMode and len(request.pivotCols) > 0

            # Handle grouping
            is_grouping = len(request.rowGroupCols) > 0
            group_level = len(request.groupKeys)

            if is_pivoting and is_grouping:
                # Pivot mode with grouping
                result, pivot_fields = self._get_pivot_rows(
                    result,
                    request.rowGroupCols,
                    request.pivotCols,
                    request.valueCols,
                    request.groupKeys,
                    group_level
                )

                # Apply sorting
                if request.sortModel:
                    result = self._apply_sorting(result, request.sortModel, request.rowGroupCols, group_level)

                # Get total count
                total = result.height

                # Pagination
                page_size = request.endRow - request.startRow
                result = result.slice(request.startRow, page_size)

                # Determine rowCount
                if request.endRow < total:
                    row_count = -1
                else:
                    row_count = total

                # Convert to dicts and add group metadata
                data = result.to_dicts()

                # Mark as group rows if at group level
                if group_level < len(request.rowGroupCols):
                    group_col_field = request.rowGroupCols[group_level].field
                    for row in data:
                        row['group'] = True
                        if '__group_count__' in row:
                            row['childCount'] = row.pop('__group_count__')

                return ServerSideResponse(data=data, rowCount=row_count, pivotFields=pivot_fields)

            elif is_grouping:
                # Regular grouping without pivot
                # Filter by parent group keys
                for i, key in enumerate(request.groupKeys):
                    if i < len(request.rowGroupCols):
                        col_field = request.rowGroupCols[i].field
                        if col_field in result.columns:
                            result = result.filter(pl.col(col_field) == key)

                # Check if we're at group level or leaf level
                if group_level < len(request.rowGroupCols):
                    # Return group rows
                    result = self._get_group_rows(
                        result, request.rowGroupCols[group_level], request.valueCols
                    )
                # else: return leaf rows (data rows)

                # Apply sorting
                if request.sortModel:
                    result = self._apply_sorting(result, request.sortModel, request.rowGroupCols, group_level)

                # Get total count
                total = result.height

                # Pagination
                page_size = request.endRow - request.startRow
                result = result.slice(request.startRow, page_size)

                # Determine rowCount for infinite scroll
                if request.endRow < total:
                    row_count = -1
                else:
                    row_count = total

                # Convert to dicts and add group metadata if needed
                data = result.to_dicts()

                # If we're returning group rows, add group metadata
                if group_level < len(request.rowGroupCols):
                    group_col_field = request.rowGroupCols[group_level].field
                    for row in data:
                        # Mark as group row
                        row['group'] = True
                        # Add child count if available
                        if '__group_count__' in row:
                            row['childCount'] = row.pop('__group_count__')

                return ServerSideResponse(data=data, rowCount=row_count)
            else:
                # No grouping or pivoting - return regular rows
                # Apply sorting
                if request.sortModel:
                    result = self._apply_sorting(result, request.sortModel, [], 0)

                # Get total count
                total = result.height

                # Pagination
                page_size = request.endRow - request.startRow
                result = result.slice(request.startRow, page_size)

                # Determine rowCount
                if request.endRow < total:
                    row_count = -1
                else:
                    row_count = total

                data = result.to_dicts()
                return ServerSideResponse(data=data, rowCount=row_count)

    def _apply_filters(self, df: pl.DataFrame, filter_model: Dict[str, FilterModel]) -> pl.DataFrame:
        """Apply filters to DataFrame."""
        result = df

        for col_id, filter_obj in filter_model.items():
            if col_id not in result.columns:
                continue

            if filter_obj.filterType == "set" and filter_obj.values:
                result = result.filter(pl.col(col_id).is_in(filter_obj.values))
            elif filter_obj.condition1 and filter_obj.condition2:
                expr1 = self._build_filter_expr(col_id, filter_obj.condition1)
                expr2 = self._build_filter_expr(col_id, filter_obj.condition2)
                if expr1 and expr2:
                    result = result.filter(expr1 | expr2 if filter_obj.operator == "OR" else expr1 & expr2)
            else:
                expr = self._build_filter_expr(col_id, filter_obj)
                if expr is not None:
                    result = result.filter(expr)

        return result

    def _build_filter_expr(self, col_id: str, filter_obj: Any) -> Optional[pl.Expr]:
        """Build Polars filter expression."""
        if isinstance(filter_obj, dict):
            filter_type = filter_obj.get("type")
            filter_value = filter_obj.get("filter")
            filter_to = filter_obj.get("filterTo")
            data_type = filter_obj.get("filterType", "text")
        else:
            filter_type = filter_obj.type
            filter_value = filter_obj.filter
            filter_to = filter_obj.filterTo
            data_type = filter_obj.filterType

        if not filter_type:
            return None

        col = pl.col(col_id)

        if data_type == "text":
            if filter_type == "equals":
                return col == filter_value
            elif filter_type == "notEqual":
                return col != filter_value
            elif filter_type == "contains":
                return col.str.contains(str(filter_value), literal=True)
            elif filter_type == "notContains":
                return ~col.str.contains(str(filter_value), literal=True)
            elif filter_type == "startsWith":
                return col.str.starts_with(str(filter_value))
            elif filter_type == "endsWith":
                return col.str.ends_with(str(filter_value))
        elif data_type in ("number", "date"):
            if filter_type == "equals":
                return col == filter_value
            elif filter_type == "notEqual":
                return col != filter_value
            elif filter_type == "lessThan":
                return col < filter_value
            elif filter_type == "lessThanOrEqual":
                return col <= filter_value
            elif filter_type == "greaterThan":
                return col > filter_value
            elif filter_type == "greaterThanOrEqual":
                return col >= filter_value
            elif filter_type == "inRange":
                return (col >= filter_value) & (col <= filter_to)

        return None

    def _get_group_rows(
        self, df: pl.DataFrame, group_col: ColumnVO, value_cols: List[ColumnVO]
    ) -> pl.DataFrame:
        """Get group rows with aggregations."""
        group_field = group_col.field

        if group_field not in df.columns:
            return pl.DataFrame()

        # Build aggregation expressions (group column is automatically included)
        agg_exprs = [pl.count().alias("__group_count__")]

        for val_col in value_cols:
            if val_col.field not in df.columns:
                continue

            col = pl.col(val_col.field)
            agg_func = val_col.aggFunc or "sum"

            if agg_func == "sum":
                agg_exprs.append(col.sum().alias(val_col.field))
            elif agg_func == "min":
                agg_exprs.append(col.min().alias(val_col.field))
            elif agg_func == "max":
                agg_exprs.append(col.max().alias(val_col.field))
            elif agg_func == "count":
                agg_exprs.append(col.count().alias(val_col.field))
            elif agg_func == "avg":
                agg_exprs.append(col.mean().alias(val_col.field))

        return df.group_by(group_field).agg(agg_exprs)

    def _get_pivot_rows(
        self,
        df: pl.DataFrame,
        row_group_cols: List[ColumnVO],
        pivot_cols: List[ColumnVO],
        value_cols: List[ColumnVO],
        group_keys: List[str],
        group_level: int
    ) -> tuple[pl.DataFrame, Optional[List[str]]]:
        """Get pivot rows with grouping."""
        # Filter by parent group keys
        for i, key in enumerate(group_keys):
            if i < len(row_group_cols):
                col_field = row_group_cols[i].field
                if col_field in df.columns:
                    df = df.filter(pl.col(col_field) == key)

        # At group level, return group rows with pivot columns
        if group_level < len(row_group_cols):
            group_col = row_group_cols[group_level]
            group_field = group_col.field

            if group_field not in df.columns:
                return pl.DataFrame()

            # Get all pivot column fields
            pivot_fields = [col.field for col in pivot_cols if col.field in df.columns]

            if not pivot_fields or not value_cols:
                # No valid pivot columns, fall back to regular grouping
                return self._get_group_rows(df, group_col, value_cols), None

            # For each value column, create aggregations for each pivot value
            # Group by row group column and pivot columns
            group_by_cols = [group_field] + pivot_fields

            agg_exprs = [pl.count().alias("__group_count__")]

            for val_col in value_cols:
                if val_col.field not in df.columns:
                    continue

                col = pl.col(val_col.field)
                agg_func = val_col.aggFunc or "sum"

                if agg_func == "sum":
                    agg_exprs.append(col.sum().alias(val_col.field))
                elif agg_func == "min":
                    agg_exprs.append(col.min().alias(val_col.field))
                elif agg_func == "max":
                    agg_exprs.append(col.max().alias(val_col.field))
                elif agg_func == "count":
                    agg_exprs.append(col.count().alias(val_col.field))
                elif agg_func == "avg":
                    agg_exprs.append(col.mean().alias(val_col.field))

            # Group and aggregate
            result = df.group_by(group_by_cols).agg(agg_exprs)

            # Now pivot: for each row group value, create columns for each pivot value
            # This is a complex operation - we'll use pivot if we have a single pivot column
            if len(pivot_fields) == 1:
                pivot_field = pivot_fields[0]

                # Pivot each value column
                pivot_result = None
                for val_col in value_cols:
                    if val_col.field in result.columns:
                        pivoted = result.pivot(
                            index=group_field,
                            on=pivot_field,
                            values=val_col.field,
                            aggregate_function="first"
                        )

                        # Rename columns to include value column name
                        rename_map = {}
                        for col_name in pivoted.columns:
                            if col_name != group_field:
                                rename_map[col_name] = f"{col_name}_{val_col.field}"

                        if rename_map:
                            pivoted = pivoted.rename(rename_map)

                        if pivot_result is None:
                            pivot_result = pivoted
                        else:
                            pivot_result = pivot_result.join(pivoted, on=group_field, how="outer")

                # Add child count
                if pivot_result is not None:
                    count_pivot = result.pivot(
                        index=group_field,
                        on=pivot_field,
                        values="__group_count__",
                        aggregate_function="sum"
                    )

                    # Sum all count columns to get total child count
                    count_cols = [c for c in count_pivot.columns if c != group_field]
                    if count_cols:
                        count_pivot = count_pivot.with_columns(
                            pl.sum_horizontal(count_cols).alias("__group_count__")
                        ).select([group_field, "__group_count__"])

                        pivot_result = pivot_result.join(count_pivot, on=group_field, how="left")

                    # Get pivot result field names (exclude the group field)
                    result_fields = [col for col in pivot_result.columns if col != group_field and col != '__group_count__']
                    return pivot_result, result_fields

            # Fallback: return grouped data without pivoting
            return result, None
        else:
            # Leaf level - return data rows (no pivot transformation at leaf level)
            return df, None

    def _apply_sorting(
        self,
        df: pl.DataFrame,
        sort_model: List[SortModel],
        row_group_cols: List[ColumnVO],
        group_level: int
    ) -> pl.DataFrame:
        """Apply sorting, respecting grouping hierarchy."""
        if not sort_model:
            return df

        # When in group mode, only sort by group columns
        if row_group_cols and group_level < len(row_group_cols):
            group_fields = {col.field for col in row_group_cols[:group_level + 1]}
            sort_cols = [s for s in sort_model if s.colId in group_fields or s.colId in df.columns]
        else:
            sort_cols = [s for s in sort_model if s.colId in df.columns]

        if sort_cols:
            columns = [s.colId for s in sort_cols]
            descending = [s.sort == "desc" for s in sort_cols]
            return df.sort(columns, descending=descending)

        return df

    def start(self, port: int = None, host: str = None):
        """Start the FastAPI server."""
        if self._running:
            return

        port = port or self._port
        host = host or self._host

        def run_server():
            uvicorn.run(self._app, host=host, port=port, log_level="warning")

        self._server_thread = threading.Thread(target=run_server, daemon=True, name="PolarsServerService")
        self._server_thread.start()
        self._running = True
        print(f"PolarsServerService started on http://{host}:{port}")

    def stop(self):
        """Stop the server (daemon thread will stop with main process)."""
        self._running = False

    def is_running(self) -> bool:
        """Check if service is running."""
        return self._running and self._server_thread and self._server_thread.is_alive()
