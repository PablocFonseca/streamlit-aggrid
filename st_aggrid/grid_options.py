from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Union
from typing import Iterable, Literal, TypedDict

from typing_extensions import NotRequired, TypeAlias


class ColumnDefinition(TypedDict):
    # Columns: Basic Properties
    field: Optional[str] = (
        None  # The field of the row object to get the cell's data from
    )
    colId: Optional[str] = (
        None  # Unique ID for the column; defaults to field if not provided
    )
    type: Optional[Union[str, List[str]]] = None  # Column type or array of types
    cellDataType: Union[bool, str] = (
        True  # Data type of the cell values; can infer or be specified
    )

    # Columns: Value Getters & Formatters
    valueGetter: Optional[Union[str, Callable]] = (
        None  # Function or expression for value retrieval
    )
    valueFormatter: Optional[Union[str, Callable]] = (
        None  # Function or expression to format value
    )
    refData: Optional[Dict[str, str]] = None  # Reference data map for value mapping
    keyCreator: Optional[Callable] = None  # Function to return a string key for a value
    equals: Optional[Callable[[Any, Any], bool]] = None  # Custom comparator for values

    # Columns: Tool Panel
    toolPanelClass: Optional[Union[str, List[str], Callable]] = (
        None  # CSS class for the tool panel cell
    )
    suppressColumnsToolPanel: bool = (
        False  # Suppress this column in the Columns Tool Panel
    )

    # Columns: Column Grouping
    columnGroupShow: Optional[str] = (
        None  # Show the column when the group is open/closed
    )

    # Columns: Icons
    icons: Optional[Dict[str, Union[Callable, str]]] = (
        None  # Custom icons for the column
    )

    # Columns: Navigation
    suppressNavigable: Union[bool, Callable] = False  # Whether this column is navigable
    suppressKeyboardEvent: Optional[Callable] = None  # Suppress certain keyboard events
    suppressPaste: Union[bool, Callable] = False  # Pasting is on by default as long as cells are editable (non-editable cells cannot be modified, even with a paste operation). Set to true turn paste operations off.
    suppressFillHandle: Union[bool, Callable] = False  # Set to true to prevent the fillHandle from being rendered in any cell that belongs to this column

    # Columns: Header
    headerName: Optional[str] = None  # Header name of the column
    headerTooltip: Optional[str] = None  # Tooltip for the column header
    headerClass: Optional[Union[str, List[str], Callable]] = (
        None  # CSS class for the header
    )
    headerValueGetter: Optional[Union[str, Callable]] = None  # Logic for header value
    headerComponent: Optional[Union[str, Callable]] = None  # Custom header component
    headerComponentParams: Optional[Dict[str, Any]] = (
        None  # Parameters for the header component
    )
    headerCheckboxSelection: Union[bool, Callable] = False  # Checkbox in the header
    headerCheckboxSelectionFilteredOnly: bool = (
        False  # Apply checkbox only to filtered rows
    )

    # Columns: Cell Rendering
    cellRenderer: Optional[Union[str, Callable]] = None  # Custom cell renderer
    cellRendererParams: Optional[Dict[str, Any]] = (
        None  # Parameters for the cell renderer
    )

    # Columns: Cell Styling
    cellClass: Optional[Union[str, List[str], Callable]] = (
        None  # CSS class for the cell
    )
    cellStyle: Optional[Union[Dict[str, Any], Callable]] = None  # Style for the cell
    cellClassRules: Optional[Dict[str, Callable]] = (
        None  # Rules for applying cell classes
    )

    # Columns: Cell Editing
    editable: Union[bool, Callable] = False  # Enable or disable cell editing
    cellEditor: Optional[Union[str, Callable]] = None  # Custom cell editor
    cellEditorParams: Optional[Dict[str, Any]] = None  # Parameters for the cell editor

    # Columns: Filtering
    filter: Optional[Union[str, Callable]] = None  # Type of filter to apply
    filterParams: Optional[Dict[str, Any]] = None  # Parameters for the filter
    floatingFilter: bool = False  # Enable floating filters

    # Columns: Aggregation
    aggFunc: Optional[Union[str, Callable]] = None  # Function to aggregate this column

    # Columns: Row Dragging
    rowDrag: bool = False  # Enable dragging rows via the column

    # Columns: Selection
    checkboxSelection: Union[bool, Callable] = False  # Enable checkbox selection

    # Columns: Resizing
    resizable: bool = True  # Allow resizing of the column
    initialWidth: Optional[int] = None  # Initial width of the column
    initialFlex: Optional[int] = None  # Initial flex value for the column

    # Columns: Sorting
    sortable: bool = True  # Allow sorting of the column
    initialSort: Optional[str] = None  # Initial sort direction ('asc' or 'desc')
    initialSortIndex: Optional[int] = None  # Initial sort order when multi-sorting

    # Columns: Pinning
    pinned: Optional[str] = None  # Pinning position ('left', 'right', or None)
    initialPinned: Optional[str] = None  # Initial pinning position

    # Columns: Visibility
    hide: bool = False  # Hide or show the column
    initialHide: bool = False  # Initial visibility state

    # Columns: Width
    width: Optional[int] = None  # Width of the column
    minWidth: Optional[int] = None  # Minimum width for the column
    maxWidth: Optional[int] = None  # Maximum width for the column
    flex: Optional[int] = None  # Flex grow factor

    # Columns: Miscellaneous
    tooltipField: Optional[str] = None  # Field to use for cell tooltips
    tooltipComponent: Optional[Union[str, Callable]] = None  # Custom tooltip component
    tooltipComponentParams: Optional[Dict[str, Any]] = (
        None  # Parameters for the tooltip component
    )
    lockPinned: bool = False  # Prevent unpinning of the column
    suppressMenu: bool = False  # Suppress the column menu
    suppressMovable: bool = False  # Prevent moving the column
    suppressSizeToFit: bool = False  # Prevent the column from being resized to fit
    suppressAutoSize: bool = False  # Prevent the column from being auto-sized
    suppressCellFlash: bool = False  # Prevent cell flashing
    suppressFillHandle: bool = False  # Suppress the fill handle
