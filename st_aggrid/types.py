from typing import Any, Literal, TypedDict, Union, List, Optional, Dict, Callable
from st_aggrid import JsCode


class StatusPanelDef(TypedDict, total=False):
    statusPanel: Optional[Any]
    align: Optional[str]
    key: Optional[str]
    statusPanelParams: Optional[Any]


class ToolPanelDef(TypedDict, total=False):
    id: str
    labelKey: str
    labelDefault: str
    minWidth: Optional[int]
    maxWidth: Optional[int]
    width: Optional[int]
    iconKey: str
    toolPanel: Optional[Any]
    toolPanelParams: Optional[Any]


class SideBarDef(TypedDict, total=False):
    toolPanels: Optional[List[Union[ToolPanelDef, str]]]
    defaultToolPanel: Optional[str]
    hiddenByDefault: Optional[bool]
    position: Optional[Literal["left", "right"]]


class ColDef(TypedDict, total=False):
    field: Optional[str]
    colId: Optional[str]
    type: Optional[Union[str, List[str]]]
    cellDataType: Optional[Union[bool, str]]
    valueGetter: Optional[Union[str, JsCode]]  # Callable[..., Any]]]
    valueFormatter: Optional[Union[str, JsCode]]  # Callable[..., str]]]
    refData: Optional[Dict[str, str]]
    keyCreator: Optional[JsCode]  # Callable[..., str]]
    equals: Optional[JsCode]  # Callable[[Any, Any], bool]]
    toolPanelClass: Optional[
        Union[str, List[str], JsCode]  # Callable[..., Union[str, List[str]]]]
    ]
    suppressColumnsToolPanel: Optional[bool]
    columnGroupShow: Optional[str]
    icons: Optional[Dict[str, Union[JsCode]]]  # Callable[..., Any], str]]]
    suppressNavigable: Optional[Union[bool, JsCode]]  # Callable[..., bool]]]
    suppressKeyboardEvent: Optional[JsCode]  # Callable[..., bool]]
    suppressPaste: Optional[Union[bool, JsCode]]  # Callable[..., bool]]]
    suppressFillHandle: Optional[bool]
    contextMenuItems: Optional[
        Union[
            List[Union[str, Dict[str, Any]]], JsCode  # Callable[..., Any]]
        ]
    ]
    context: Optional[Any]


class ColGroupDef(TypedDict, total=False):
    headerName: Optional[str]
    children: List[Union["ColDef", "ColGroupDef"]]
    groupId: Optional[str]
    marryChildren: Optional[bool]
    openByDefault: Optional[bool]
    headerClass: Optional[
        Union[str, List[str], JsCode]
    ]  # Callable[..., Union[str, List[str]]]]]
    headerTooltip: Optional[str]
    headerComponent: Optional[Any]
    headerComponentParams: Optional[Dict[str, Any]]
    headerCheckboxSelection: Optional[Union[bool, JsCode]]  # Callable[..., bool]]]
    suppressColumnsToolPanel: Optional[bool]
    columnGroupShow: Optional[str]


class GridOptions(TypedDict, total=False):
    statusBar: Dict[str, List[StatusPanelDef]]
    sideBar: Union[SideBarDef, str, List[str], bool, None]
    getContextMenuItems: JsCode  # JsCode #Callable[..., GetContextMenuItems]
    suppressContextMenu: bool
    preventDefaultOnContextMenu: bool
    allowContextMenuWithControlKey: bool
    getMainMenuItems: JsCode  # JsCode #Callable[..., Any]
    columnMenu: Union[str, None]
    suppressMenuHide: bool
    popupParent: Optional[Any]
    postProcessPopup: JsCode  # JsCode #Callable[..., Any]
    copyHeadersToClipboard: bool
    copyGroupHeadersToClipboard: bool
    clipboardDelimiter: str
    suppressCutToClipboard: bool
    suppressCopyRowsToClipboard: bool
    suppressCopySingleCellRanges: bool
    suppressLastEmptyLineOnPaste: bool
    suppressClipboardPaste: bool
    suppressClipboardApi: bool
    processCellForClipboard: JsCode  # JsCode #Callable[..., Any]
    processHeaderForClipboard: JsCode  # JsCode #Callable[..., Any]
    processGroupHeaderForClipboard: JsCode  # JsCode #Callable[..., Any]
    processCellFromClipboard: JsCode  # JsCode #Callable[..., Any]
    sendToClipboard: JsCode  # JsCode #Callable[..., Any]
    processDataFromClipboard: JsCode  # JsCode #Callable[..., Any]
    columnDefs: Optional[List[Union[ColDef, ColGroupDef]]]
    defaultColDef: Optional[Dict[str, Any]]
    defaultColGroupDef: Optional[Dict[str, Any]]
    columnTypes: Dict[str, Dict[str, Any]]
    dataTypeDefinitions: Dict[str, Any]
    maintainColumnOrder: bool
    suppressFieldDotNotation: bool
    headerHeight: Optional[int]
    groupHeaderHeight: Optional[int]
    floatingFiltersHeight: Optional[int]
    pivotHeaderHeight: Optional[int]
    pivotGroupHeaderHeight: Optional[int]
    allowDragFromColumnsToolPanel: bool
    suppressMovableColumns: bool
    suppressColumnMoveAnimation: bool
    suppressDragLeaveHidesColumns: bool
    suppressRowGroupHidesColumns: bool
    processUnpinnedColumns: JsCode  # JsCode #Callable[..., Any]
    colResizeDefault: Optional[str]
    autoSizeStrategy: Optional[str]
    suppressAutoSize: bool
    autoSizePadding: Optional[int]
    skipHeaderOnAutoSize: bool
    components: Dict[str, Any]
    editType: Optional[str]
    singleClickEdit: bool
    suppressClickEdit: bool
    stopEditingWhenCellsLoseFocus: Optional[bool]
    enterNavigatesVertically: bool
    enterNavigatesVerticallyAfterEdit: bool
    enableCellEditingOnBackspace: Optional[bool]
    undoRedoCellEditing: Optional[bool]
    undoRedoCellEditingLimit: Optional[int]
    readOnlyEdit: bool
    defaultCsvExportParams: Optional[Dict[str, Any]]
    suppressCsvExport: bool
    defaultExcelExportParams: Optional[Dict[str, Any]]
    suppressExcelExport: bool
    excelStyles: Optional[List[Dict[str, Any]]]
    quickFilterText: Optional[str]
    cacheQuickFilter: Optional[bool]
    includeHiddenColumnsInQuickFilter: bool
    quickFilterParser: JsCode  # JsCode #Callable[..., Any]
    quickFilterMatcher: JsCode  # JsCode #Callable[..., Any]
    isExternalFilterPresent: JsCode  # JsCode #Callable[..., bool]
    doesExternalFilterPass: JsCode  # JsCode #Callable[..., bool]
    excludeChildrenWhenTreeDataFiltering: bool
    enableAdvancedFilter: bool
    includeHiddenColumnsInAdvancedFilter: bool
    advancedFilterParent: Optional[Any]
    advancedFilterBuilderParams: Optional[Dict[str, Any]]
    enableCharts: bool
    suppressChartToolPanelsButton: Optional[bool]
    getChartToolbarItems: JsCode  # JsCode #Callable[..., Any]
    createChartContainer: JsCode  # JsCode #Callable[..., Any]
    chartThemes: List[str]
    customChartThemes: Dict[str, Dict[str, Any]]
    chartThemeOverrides: Optional[Dict[str, Any]]
    chartToolPanelsDef: Optional[Dict[str, Any]]
    chartMenuItems: Union[List[Union[str, Dict[str, Any]]], JsCode, None]
    navigateToNextHeader: JsCode  # JsCode #Callable[..., Any]
    tabToNextHeader: JsCode  # JsCode #Callable[..., Any]
    navigateToNextCell: JsCode  # JsCode #Callable[..., Any]
    tabToNextCell: JsCode  # JsCode #Callable[..., Any]
    loadingCellRenderer: Optional[Any]
    loadingCellRendererParams: Optional[Dict[str, Any]]
    loadingCellRendererSelector: JsCode  # JsCode #Callable[..., Any]
    localeText: Dict[str, str]
    getLocaleText: JsCode  # JsCode #Callable[..., Any]
    masterDetail: bool
    isRowMaster: JsCode  # JsCode #Callable[..., Any]
    detailCellRenderer: Optional[Any]
    detailCellRendererParams: Optional[Dict[str, Any]]
    detailRowHeight: Optional[int]
    detailRowAutoHeight: Optional[bool]
    embedFullWidthRows: bool
    keepDetailRows: bool
    keepDetailRowsCount: Optional[int]
    initialState: Optional[Dict[str, Any]]
    alignedGrids: Optional[List[Any]]
    context: Optional[Any]
    tabIndex: Optional[int]
    rowBuffer: Optional[int]
    valueCache: Optional[bool]
    valueCacheNeverExpires: Optional[bool]
    enableCellExpressions: Optional[bool]
    getDocument: JsCode  # JsCode #Callable[..., Any]
    suppressTouch: Optional[bool]
    suppressFocusAfterRefresh: Optional[bool]
    suppressBrowserResizeObserver: Optional[bool]
    suppressPropertyNamesCheck: Optional[bool]
    suppressChangeDetection: Optional[bool]
    debug: Optional[bool]
    reactiveCustomComponents: Optional[bool]
    overlayLoadingTemplate: Optional[str]
    loadingOverlayComponent: Optional[Any]
    loadingOverlayComponentParams: Optional[Dict[str, Any]]
    suppressLoadingOverlay: Optional[bool]
    overlayNoRowsTemplate: Optional[str]
    noRowsOverlayComponent: Optional[Any]
    noRowsOverlayComponentParams: Optional[Dict[str, Any]]
    suppressNoRowsOverlay: bool
    pagination: bool
    paginationPageSize: Optional[int]
    paginationPageSizeSelector: Union[List[int], bool, None]
    paginationNumberFormatter: JsCode  # JsCode #Callable[..., Any]
    paginationAutoPageSize: bool
    paginateChildRows: bool
    suppressPaginationPanel: bool
    pivotMode: bool
    pivotPanelShow: Optional[str]
    pivotDefaultExpanded: Optional[int]
    pivotColumnGroupTotals: Optional[str]
    pivotRowTotals: Optional[str]
    pivotSuppressAutoColumn: bool
    pivotMaxGeneratedColumns: Optional[int]
    processPivotResultColDef: JsCode  # JsCode #Callable[..., Any]
    processPivotResultColGroupDef: JsCode  # JsCode #Callable[..., Any]
    suppressExpandablePivotGroups: Optional[bool]
    functionsReadOnly: bool
    aggFuncs: Dict[str, JsCode]  # JsCode #Callable[..., Any]]
    getGroupRowAgg: JsCode  # JsCode #Callable[..., Any]
    suppressAggFuncInHeader: Optional[bool]
    alwaysAggregateAtRootLevel: bool
    aggregateOnlyChangedColumns: bool
    suppressAggFilteredOnly: bool
    groupAggFiltering: Union[bool, JsCode]  # JsCode #Callable[..., bool]]
    removePivotHeaderRowWhenSingleValueColumn: Optional[bool]
    animateRows: bool
    cellFlashDuration: Optional[int]
    cellFadeDuration: Optional[int]
    allowShowChangeAfterFilter: Optional[bool]
    domLayout: Optional[str]
    ensureDomOrder: Optional[bool]
    getBusinessKeyForNode: JsCode  # JsCode #Callable[..., Any]
    gridId: Optional[str]
    processRowPostCreate: JsCode  # JsCode #Callable[..., Any]
    enableRtl: Optional[bool]
    suppressColumnVirtualisation: Optional[bool]
    suppressRowVirtualisation: Optional[bool]
    suppressMaxRenderedRowRestriction: Optional[bool]
    rowDragManaged: bool
    rowDragEntireRow: bool
    rowDragMultiRow: bool
    suppressRowDrag: bool
    suppressMoveWhenRowDragging: bool
    rowDragText: JsCode  # JsCode #Callable[..., str]
    fullWidthCellRenderer: Optional[Any]
    fullWidthCellRendererParams: Optional[Dict[str, Any]]
    groupDisplayType: Optional[str]
    groupDefaultExpanded: Optional[int]
    autoGroupColumnDef: Optional[Dict[str, Any]]
    groupMaintainOrder: bool
    groupSelectsChildren: bool
    groupLockGroupColumns: Optional[int]
    groupIncludeFooter: Union[bool, JsCode]  # JsCode #Callable[..., bool]]
    groupIncludeTotalFooter: bool
    groupSuppressBlankHeader: bool
    groupSelectsFiltered: bool
    showOpenedGroup: bool
    isGroupOpenByDefault: JsCode  # JsCode #Callable[..., bool]
    initialGroupOrderComparator: JsCode  # JsCode #Callable[..., Any]
    groupRemoveSingleChildren: bool
    groupRemoveLowestSingleChildren: bool
    groupHideOpenParents: bool
    groupAllowUnbalanced: bool
    rowGroupPanelShow: Optional[str]
    rowGroupPanelSuppressSort: Optional[bool]
    groupRowRenderer: Optional[Any]
    groupRowRendererParams: Optional[Dict[str, Any]]
    suppressGroupRowsSticky: Optional[bool]
    suppressMakeColumnVisibleAfterUnGroup: bool
    treeData: bool
    getDataPath: JsCode  # JsCode #Callable[..., List[str]]
    pinnedTopRowData: Optional[List[Any]]
    pinnedBottomRowData: Optional[List[Any]]
    rowModelType: Optional[str]
    getRowId: JsCode  # JsCode #Callable[..., str]
    rowData: Optional[List[Any]]
    resetRowDataOnUpdate: bool
    asyncTransactionWaitMillis: Optional[int]
    suppressModelUpdateAfterUpdateTransaction: bool
    datasource: Optional[Any]
    cacheOverflowSize: Optional[int]
    maxConcurrentDatasourceRequests: Optional[int]
    cacheBlockSize: Optional[int]
    maxBlocksInCache: Optional[int]
    infiniteInitialRowCount: Optional[int]
    serverSideDatasource: Optional[Any]
    blockLoadDebounceMillis: Optional[int]
    purgeClosedRowNodes: bool
    serverSidePivotResultFieldSeparator: Optional[str]
    serverSideSortAllLevels: bool
    serverSideEnableClientSideSort: bool
    serverSideOnlyRefreshFilteredGroups: Optional[bool]
    serverSideInitialRowCount: Optional[int]
    getChildCount: JsCode  # JsCode #Callable[..., int]
    getServerSideGroupLevelParams: JsCode  # JsCode #Callable[..., Dict[str, Any]]
    isServerSideGroupOpenByDefault: JsCode  # JsCode #Callable[..., bool]
    isApplyServerSideTransaction: JsCode  # JsCode #Callable[..., bool]
    isServerSideGroup: JsCode  # JsCode #Callable[..., bool]
    getServerSideGroupKey: JsCode  # JsCode #Callable[..., str]
    viewportDatasource: Optional[Any]
    viewportRowModelPageSize: Optional[int]
    viewportRowModelBufferSize: Optional[int]
    alwaysShowHorizontalScroll: bool
    alwaysShowVerticalScroll: bool
    debounceVerticalScrollbar: Optional[bool]
    suppressHorizontalScroll: bool
    suppressScrollOnNewData: bool
    suppressScrollWhenPopupsAreOpen: bool
    suppressAnimationFrame: Optional[bool]
    suppressMiddleClickScrolls: bool
    suppressPreventDefaultOnMouseWheel: Optional[bool]
    scrollbarWidth: Optional[int]
    rowSelection: Optional[str]
    rowMultiSelectWithClick: bool
    isRowSelectable: JsCode  # JsCode #Callable[..., bool]
    suppressRowDeselection: bool
    suppressRowClickSelection: bool
    suppressCellFocus: bool
    suppressHeaderFocus: bool
    suppressMultiRangeSelection: bool
    enableCellTextSelection: bool
    enableRangeSelection: bool
    enableRangeHandle: bool
