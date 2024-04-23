import {
  Streamlit,
  ComponentProps,
  withStreamlitConnection,
} from "streamlit-component-lib"

import React, { ReactNode } from "react"
import { AgGridReact } from "@ag-grid-community/react"

import {
  ModuleRegistry,
  GridApi,
  DetailGridInfo,
  GridReadyEvent,
  GridOptions,
  GetRowIdParams,
  GridSizeChangedEvent,
  CellValueChangedEvent,
  IRowNode,
} from "@ag-grid-community/core"

import { CsvExportModule } from "@ag-grid-community/csv-export"
import { ClientSideRowModelModule } from "@ag-grid-community/client-side-row-model"
import { LicenseManager } from "@ag-grid-enterprise/core"

import { GridChartsModule } from "@ag-grid-enterprise/charts"
import { SparklinesModule } from "@ag-grid-enterprise/sparklines"
import { ClipboardModule } from "@ag-grid-enterprise/clipboard"
import { ColumnsToolPanelModule } from "@ag-grid-enterprise/column-tool-panel"
import { ExcelExportModule } from "@ag-grid-enterprise/excel-export"
import { FiltersToolPanelModule } from "@ag-grid-enterprise/filter-tool-panel"
import { MasterDetailModule } from "@ag-grid-enterprise/master-detail"
import { MenuModule } from "@ag-grid-enterprise/menu"
import { RangeSelectionModule } from "@ag-grid-enterprise/range-selection"
import { RichSelectModule } from "@ag-grid-enterprise/rich-select"
import { RowGroupingModule } from "@ag-grid-enterprise/row-grouping"
import { SetFilterModule } from "@ag-grid-enterprise/set-filter"
import { MultiFilterModule } from "@ag-grid-enterprise/multi-filter"
import { SideBarModule } from "@ag-grid-enterprise/side-bar"
import { StatusBarModule } from "@ag-grid-enterprise/status-bar"

import { parseISO, compareAsc, format } from "date-fns"

import {deepMap} from "./utils"
import { duration } from "moment"

import _, { debounce, throttle } from "lodash"

import { encode, decode } from "base64-arraybuffer"
import { Buffer } from "buffer"

import "./agGridStyle.scss"
import "@fontsource/source-sans-pro"
import { eventDataWhiteList } from "./constants"

type CSSDict = { [key: string]: { [key: string]: string } }

function getCSS(styles: CSSDict): string {
  var css = []
  for (let selector in styles) {
    let style = selector + " {"

    for (let prop in styles[selector]) {
      style += prop + ": " + styles[selector][prop] + ";"
    }

    style += "}"

    css.push(style)
  }

  return css.join("\n")
}

function addCustomCSS(custom_css: CSSDict): void {
  var css = getCSS(custom_css)
  var styleSheet = document.createElement("style")
  styleSheet.type = "text/css"
  styleSheet.innerText = css
  document.head.appendChild(styleSheet)
}

function parseJsCodeFromPython(v: string) {
  const JS_PLACEHOLDER = "::JSCODE::"
  let funcReg = new RegExp(
    `${JS_PLACEHOLDER}\\s*((function|class)\\s*.*)\\s*${JS_PLACEHOLDER}`
  )

  let match = funcReg.exec(v)

  if (match) {

    const funcStr = match[1]
    // eslint-disable-next-line
    return new Function("return " + funcStr)()
  } else {
    return v
  }
}

//TODO: mover formaters to gridOptionsBuilder options
function dateFormatter(isoString: string, formaterString: string): String {
  try {
    let date = parseISO(isoString)
    return format(date, formaterString)
  } catch {
    return isoString
  } finally {
  }
}

function currencyFormatter(number: any, currencySymbol: string): String {
  let n = Number.parseFloat(number)
  if (!Number.isNaN(n)) {
    return currencySymbol + n.toFixed(2)
  } else {
    return number
  }
}

function numberFormatter(number: any, precision: number): String {
  let n = Number.parseFloat(number)
  if (!Number.isNaN(n)) {
    return n.toFixed(precision)
  } else {
    return number
  }
}

const columnFormaters = {
  dateColumnFilter: {
    filter: "agDateColumnFilter",
    filterParams: {
      comparator: (filterValue: any, cellValue: string) =>
        compareAsc(parseISO(cellValue), filterValue),
    },
  },
  numberColumnFilter: {
    filter: "agNumberColumnFilter",
  },
  shortDateTimeFormat: {
    valueFormatter: (params: any) =>
      dateFormatter(params.value, "dd/MM/yyyy HH:mm"),
  },
  customDateTimeFormat: {
    valueFormatter: (params: any) =>
      dateFormatter(params.value, params.column.colDef.custom_format_string),
  },
  customNumericFormat: {
    valueFormatter: (params: any) =>
      numberFormatter(params.value, params.column.colDef.precision ?? 2),
  },
  customCurrencyFormat: {
    valueFormatter: (params: any) =>
      currencyFormatter(
        params.value,
        params.column.colDef.custom_currency_symbol
      ),
  },
  timedeltaFormat: {
    valueFormatter: (params: any) => duration(params.value).humanize(true),
  },
}

function GridToolBar(props: any) {
  if (props.enabled) {
    return (
      <div id="gridToolBar" style={{ paddingBottom: 30 }}>
        <div className="ag-row-odd ag-row-no-focus ag-row ag-row-level-0 ag-row-position-absolute">
          <div className="">
            <div className="ag-cell-wrapper">{props.children}</div>
          </div>
        </div>
      </div>
    )
  }
  return <></>
}

function QuickSearch(props: any) {
  if (props.enableQuickSearch) {
    return (
      <input
        className="ag-cell-value"
        type="text"
        onChange={props.onChange}
        onKeyUp={props.showOverlay}
        placeholder="quickfilter..."
        style={{ marginLeft: 5, marginRight: 5 }}
      />
    )
  }
  return <></>
}

function ManualUpdateButton(props: any) {
  if (props.manualUpdate) {
    return (
      <button onClick={props.onClick} style={{ marginLeft: 5, marginRight: 5 }}>
        Update
      </button>
    )
  }
  return <></>
}

function ManualDownloadButton(props: any) {
  if (props.enabled) {
    return (
      <button onClick={props.onClick} style={{ marginLeft: 5, marginRight: 5 }}>
        Download
      </button>
    )
  }
  return <></>
}

interface State {
  gridHeight: number
  gridOptions: GridOptions
  isRowDataEdited: Boolean
  api?: GridApi
}
class AgGrid extends React.Component<ComponentProps, State> {
  public state: State
  private gridContainerRef: React.RefObject<HTMLDivElement>
  private isGridAutoHeightOn: boolean
  private renderedGridHeightPrevious: number = 0

  constructor(props: ComponentProps) {
    super(props)
    this.gridContainerRef = React.createRef()

    if (props.args.custom_css) {
      addCustomCSS(props.args.custom_css)
    }

    ModuleRegistry.register(ClientSideRowModelModule)
    ModuleRegistry.register(CsvExportModule)

    if (props.args.enable_enterprise_modules) {
      ModuleRegistry.registerModules([
        ExcelExportModule,
        GridChartsModule,
        SparklinesModule,
        ColumnsToolPanelModule,
        FiltersToolPanelModule,
        MasterDetailModule,
        MenuModule,
        RangeSelectionModule,
        RichSelectModule,
        RowGroupingModule,
        SetFilterModule,
        MultiFilterModule,
        SideBarModule,
        StatusBarModule,
        ClipboardModule,
      ])

      if ("license_key" in props.args) {
        LicenseManager.setLicenseKey(props.args["license_key"])
      }
    }

    this.isGridAutoHeightOn =
      this.props.args.gridOptions?.domLayout === "autoHeight"

    var go = this.parseGridoptions()
    this.state = {
      gridHeight: this.props.args.height,
      gridOptions: go,
      isRowDataEdited: false,
      api: undefined,
    } as State
  }

  private parseGridoptions() {
    let gridOptions: GridOptions = _.cloneDeep(this.props.args.gridOptions)

    if (this.props.args.allow_unsafe_jscode) {
      console.warn("flag allow_unsafe_jscode is on.")
      gridOptions = deepMap(gridOptions, parseJsCodeFromPython, ["rowData"])
    }

    //Sets getRowID if data came from a pandas dataframe like object. (has __pandas_index)
    //console.log("all rows have __pandas_index:", (_.every(gridOptions.rowData, (o) => '__pandas_index' in o)))
    if (_.every(gridOptions.rowData, (o) => "__pandas_index" in o)) {
      if (!("getRowId" in gridOptions)) {
        gridOptions["getRowId"] = (params: GetRowIdParams) =>
          params.data.__pandas_index as string
        //console.info("gridRowId() function set as underlying pandas dataframe index.", gridOptions['getRowId'])
      }
    }
    if (!("getRowId" in gridOptions)) {
      console.warn("getRowId was not set. Grid may behave bad when updating.")
    }

    //console.log("GridOptions for", this.props.args.key, ":", gridOptions)

    //adds custom columnFormatters
    gridOptions.columnTypes = Object.assign(
      gridOptions.columnTypes || {},
      columnFormaters
    )
    return gridOptions
  }

  private attachStreamlitRerunToEvents(api: GridApi) {
    const updateEvents = this.props.args.update_on

    updateEvents.forEach((element: any) => {
      //if element is a tuple (eventName,timeout) apply debounce func for timeout seconds.
      if (Array.isArray(element)) {
        api.addEventListener(element[0], debounce((e: any) => this.returnGridValue(e, element[0]), element[1]))
      } else {
        api.addEventListener(element, (e: any) => this.returnGridValue(e, element))
      }
      console.log("Attached grid return event %s", element)
    })
  }

  private loadColumnsState() {
    const columnsState = this.props.args.columns_state
    if (columnsState != null) {
      this.state.api?.applyColumnState({
        state: columnsState,
        applyOrder: true,
      })
    }
  }

  private DownloadAsExcelIfRequested() {
    if (this.state.api) {
      if (
        this.props.args.excel_export_mode === "MULTIPLE_SHEETS" &&
        this.props.args.ExcelExportMultipleSheetParams
      ) {
        let params = this.props.args.ExcelExportMultipleSheetParams

        let data = params.data.map((v: string) =>
          Buffer.from(decode(v)).toString("latin1")
        )
        params.data = data

        this.state.api?.exportMultipleSheetsAsExcel(params)
      }
      if (this.props.args.excel_export_mode === "TRIGGER_DOWNLOAD") {
        this.state.api?.exportDataAsExcel()
      }
    }
  }

  private handleExcelExport() {
    if (this.props.args.excel_export_mode === "FILE_BLOB_IN_GRID_RESPONSE") {
      let blob = this.state.api?.getDataAsExcel() as Blob
      let buffer
      ;(async () => {
        await new Promise((resolve, reject) => {
          blob.arrayBuffer().then((v) => {
            buffer = encode(v)
            resolve(buffer)
          })
        })
      })()
      return buffer
    }

    if (this.props.args.excel_export_mode === "SHEET_BLOB_IN_GRID_RESPONSE") {
      let blob = this.state.api?.getSheetDataForExcel({
        sheetName: Math.round(Date.now() / 1000).toString(),
      })
      if (blob) return encode(Buffer.from(blob, "latin1")) ///Buffer.from(blob).toString('base64')
    }
    return null
  }

  private resizeGridContainer() {
    const renderedGridHeight = this.gridContainerRef.current?.clientHeight
    if (
      renderedGridHeight &&
      renderedGridHeight > 0 &&
      renderedGridHeight !== this.renderedGridHeightPrevious
    ) {
      this.renderedGridHeightPrevious = renderedGridHeight
      Streamlit.setFrameHeight(renderedGridHeight)
    }
  }

  private async getGridReturnValue(
    e: any,
    streamlitRerunEventTriggerName: string
  ) {
    function fetch_node_props(n: IRowNode | null): any {
      if (n == null) {
        return null
      }
      return {
        id: n.id,
        data: n.data,
        rowIndex: n.rowIndex,
        rowTop: n.rowTop,
        displayed: n.displayed,
        isHovered: n.isHovered(),
        isFullWidthCell: n.isFullWidthCell(),
        expanded: n.expanded,
        isExpandable: n.expanded,
        group: n.group,
        groupData: n.groupData,
        aggData: n.aggData,
        key: n.key,
        field: n.field,
        rowGroupColumn: n.rowGroupColumn?.getColId(),
        rowGroupIndex: n.rowIndex,
        footer: n.footer,
        parent: fetch_node_props(n.parent),
        firstChild: n.firstChild,
        lastChild: n.lastChild,
        childIndex: n.childIndex,
        level: n.level,
        uiLevel: n.uiLevel,
        //allLeafChildren: n.allLeafChildren.map(v=> fetch_node_props(v)),
        //childrenAfterGroup: n.childrenAfterGroup?.map(v => fetch_node_props(v)),
        //childrenAfterFilter: n.childrenAfterFilter?.map(v => fetch_node_props(v)),
        //childrenAfterSort: n.childrenAfterSort?.map(v => fetch_node_props(v)),
        allChildrenCount: n.allChildrenCount,
        leafGroup: n.leafGroup,
        sibling: fetch_node_props(n.sibling),
        rowHeight: n.rowHeight,
        master: n.master,
        detail: n.detail,
        rowPinned: n.rowPinned,
        isRowPinned: n.isRowPinned(),
        selectable: n.selectable,
        isSelected: n.isSelected(),
      }
    }
    let nodes: any[] = []
    this.state.api?.forEachNode((n, i) => {
      nodes.push(fetch_node_props(n))
    })

    let rowsAfterFilter: any[] = []
    this.state.api?.forEachNodeAfterFilter((row) => {
      if (!row.group) {
        rowsAfterFilter.push(row.id)
      }
    })

    let rowsAfterSortAndFilter: any[] = []
    this.state.api?.forEachNodeAfterFilterAndSort((row) => {
      if (!row.group) {
        rowsAfterSortAndFilter.push(row.id)
      }
    })

    let selected: any = []
    this.state.api?.forEachDetailGridInfo((d: DetailGridInfo) => {
      //console.log(d);
      d.api?.forEachNode((n) => {
        if (n.isSelected()) {
          selected.push(n.id)
        }
      })
    })

    //function to recursively walk through object keys and drop then based on value, avoids circular references
    function cleanEventKeys(obj: any, root = "", level = 0) {
      if (Array.isArray(obj)) {
        obj.forEach((v) => {
          return cleanEventKeys(v, root, level + 1)
        })
      } else if (typeof obj === "object") {
        Object.keys(obj).forEach(function (key) {
          if (level > 3) return
          if (key === "data") return 
          let fullKey = [root, key].filter((v) => v !== "").join(".")

          if (!eventDataWhiteList.includes(fullKey)) {
            delete obj[key]
          } else if (typeof obj[key] === "object" && obj[key] !== null) {
            cleanEventKeys(obj[key], fullKey, level + 1)
          }
        })
      }
      return obj
    }
    
    let cleanEventData = cleanEventKeys(_.cloneDeep(e))
    cleanEventData["streamlitRerunEventTriggerName"] =
      streamlitRerunEventTriggerName

    let returnValue = {
      originalDtypes: this.props.args.frame_dtypes,
      nodes: nodes,
      selectedItems: this.state.api?.getSelectedRows(),
      gridState: this.state.api?.getState(),
      columnsState: this.state.api?.getColumnState(),
      gridOptions: JSON.stringify(this.state.gridOptions),
      //ExcelBlob: this.handleExcelExport(),
      rowIdsAfterFilter: rowsAfterFilter,
      rowIdsAfterSortAndFilter: rowsAfterSortAndFilter,
      eventData: cleanEventData,
    }

    return returnValue
  }

  private returnGridValue(e: any, streamlitRerunEventTriggerName: string) {
    this.getGridReturnValue(e, streamlitRerunEventTriggerName).then((v) =>
      Streamlit.setComponentValue(v)
    )
  }

  private defineContainerHeight() {
    if (this.isGridAutoHeightOn) {
      return {
        width: this.props.width,
      }
    } else {
      return {
        width: this.props.width,
        height: this.props.args.height,
      }
    }
  }

  private getThemeClass() {
    const themeName = this.props.args.theme
    const themeBase = this.props.theme?.base

    var themeClass = "ag-theme-" + themeName

    if (themeBase === "dark" && themeName !== "material") {
      themeClass = themeClass + "-dark"
    }
    return themeClass
  }

  public componentDidUpdate(prevProps: any, prevState: State, snapshot?: any) {
    const prevGridOptions = prevProps.args.gridOptions
    const currGridOptions = this.props.args.gridOptions

    //const objectDiff = (a: any, b: any) => _.fromPairs(_.differenceWith(_.toPairs(a), _.toPairs(b), _.isEqual))
    if (!_.isEqual(prevGridOptions, currGridOptions)) {
      //console.dir(objectDiff(prevGridOptions, currGridOptions))
      let go = this.parseGridoptions()
      let row_data = go.rowData

      if (!this.state.isRowDataEdited) {
        this.state.api?.updateGridOptions({ rowData: row_data })
      }

      delete go.rowData
      this.state.api?.updateGridOptions(go)
    }

    if (
      !_.isEqual(prevProps.args.columns_state, this.props.args.columns_state)
    ) {
      this.loadColumnsState()
    }
  }

  private onGridReady(event: GridReadyEvent) {
    this.setState({ api: event.api })

    //Is it ugly? Yes. Does it work? Yes.
    this.state.api = event.api

    this.state.api?.addEventListener("rowGroupOpened", (e: any) =>
      this.resizeGridContainer()
    )

    this.state.api?.addEventListener("firstDataRendered", (e: any) => {
      this.resizeGridContainer()
    })

    this.state.api.addEventListener(
      "GridSizeChanged",
      (e: GridSizeChangedEvent) => this.onGridSizeChanged(e)
    )
    this.state.api.addEventListener(
      "cellValueChanged",
      (e: CellValueChangedEvent) => this.cellValueChanged(e)
    )

    this.attachStreamlitRerunToEvents(this.state.api)
    this.state.api?.forEachDetailGridInfo((i: DetailGridInfo) => {
      if (i.api !== undefined) {
        this.attachStreamlitRerunToEvents(i.api)
      }
    })
  }

  private onGridSizeChanged(event: GridSizeChangedEvent) {
    this.resizeGridContainer()
  }

  private cellValueChanged(event: CellValueChangedEvent) {
    console.log(
      "Data edited on Grid. Ignoring further changes from data paramener (AgGrid(data=dataframe))"
    )
    this.setState({ isRowDataEdited: true })
  }

  private processPreselection() {
    //TODO: do not pass grid Options that doesn't exist in aggrid (preSelectAllRows,  preSelectedRows)
    var preSelectAllRows =
      this.props.args.gridOptions["preSelectAllRows"] || false

    if (preSelectAllRows) {
      this.state.api?.selectAll()
    } else {
      var preselectedRows = this.props.args.gridOptions["preSelectedRows"]
      if (preselectedRows || preselectedRows?.length() > 0) {
        for (var idx in preselectedRows) {
          this.state.api
            ?.getRowNode(preselectedRows[idx])
            ?.setSelected(true, false)
        }
      }
    }
  }

  public render = (): ReactNode => {
    let shouldRenderGridToolbar =
      this.props.args.enable_quicksearch === true ||
      this.props.args.manual_update ||
      this.props.args.excelExportMode === "MANUAL"

    return (
      <div
        id="gridContainer"
        className={this.getThemeClass()}
        ref={this.gridContainerRef}
        style={this.defineContainerHeight()}
      >
        <GridToolBar enabled={shouldRenderGridToolbar}>
          <ManualUpdateButton
            manualUpdate={this.props.args.manual_update}
            onClick={(e: any) => this.returnGridValue(e, "ManualUpdate")}
          />
          <ManualDownloadButton
            enabled={this.props.args.excelExportMode === "MANUAL"}
            onClick={(e: any) => this.state.api?.exportDataAsExcel()}
          />
          <QuickSearch
            enableQuickSearch={this.props.args.enable_quicksearch}
            showOverlay={throttle(
              () => this.state.api?.showLoadingOverlay(),
              1000,
              {
                trailing: false,
              }
            )}
            onChange={debounce((e) => {
              this.state.api?.setQuickFilter(e.target.value)
              this.state.api?.hideOverlay()
            }, 1000)}
          />
        </GridToolBar>
        <AgGridReact
          onGridReady={(e: GridReadyEvent) => this.onGridReady(e)}
          gridOptions={this.state.gridOptions}
        ></AgGridReact>
      </div>
    )
  }
}

export default withStreamlitConnection(AgGrid)
