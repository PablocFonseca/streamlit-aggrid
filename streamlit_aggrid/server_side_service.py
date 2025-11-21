"""AG Grid Server-Side Row Model Service Base."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional
from dataclasses import dataclass
from enum import Enum


class FilterType(Enum):
    TEXT = "text"
    NUMBER = "number"
    DATE = "date"
    SET = "set"


@dataclass
class SortModel:
    colId: str
    sort: str


@dataclass
class FilterModel:
    filterType: str
    type: Optional[str] = None
    filter: Optional[Any] = None
    filterTo: Optional[Any] = None
    values: Optional[List[Any]] = None
    condition1: Optional[Dict] = None
    condition2: Optional[Dict] = None
    operator: Optional[str] = None


@dataclass
class ColumnVO:
    id: str
    field: str
    displayName: Optional[str] = None
    aggFunc: Optional[str] = None


@dataclass
class ServerSideRequest:
    startRow: int
    endRow: int
    rowGroupCols: List[ColumnVO]
    valueCols: List[ColumnVO]
    pivotCols: List[ColumnVO]
    pivotMode: bool
    groupKeys: List[str]
    filterModel: Dict[str, FilterModel]
    sortModel: List[SortModel]


@dataclass
class ServerSideResponse:
    data: List[Dict[str, Any]]
    rowCount: Optional[int] = None
    pivotFields: Optional[List[str]] = None


class ServerSideService(ABC):
    """Abstract base for AG Grid Server-Side Row Model services."""

    @abstractmethod
    def get_rows(self, request: ServerSideRequest) -> ServerSideResponse:
        """Process AG Grid data request."""
        raise NotImplementedError

    @abstractmethod
    def start(self, port: int = 8000, host: str = "127.0.0.1"):
        """Start the server-side service."""
        raise NotImplementedError

    @abstractmethod
    def stop(self):
        """Stop the server-side service."""
        raise NotImplementedError

    def is_running(self) -> bool:
        """Check if service is running."""
        return False
