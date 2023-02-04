import {
  Streamlit,
  StreamlitComponentBase,
  withStreamlitConnection,
} from "streamlit-component-lib"

import React, { ReactNode } from "react"
import { AgGridReact } from "@ag-grid-community/react"

import { ModuleRegistry, ColumnApi, GridApi, DetailGridInfo, RowNode } from "@ag-grid-community/core"
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

import { parseISO, compareAsc } from "date-fns"
import { format } from "date-fns-tz"
import deepMap from "./utils"
import { duration } from "moment"

import { debounce } from "lodash"

import"./agGridStyle.scss"

import "@fontsource/source-sans-pro"
interface State {
  rowData: any
  gridHeight: number
  should_update: boolean
}

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

class AgGrid extends StreamlitComponentBase<State> {
  private frameDtypes: any
  private api!: GridApi
  private columnApi!: ColumnApi
  private columnFormaters: any
  private manualUpdateRequested: boolean = false
  private allowUnsafeJsCode: boolean = false
  private gridOptions: any
  private gridContainerRef: React.RefObject<HTMLDivElement>
  private isGridAutoHeightOn: boolean

  constructor(props: any) {
    super(props)
    //console.log(props)

    ModuleRegistry.register(ClientSideRowModelModule)
    ModuleRegistry.register(CsvExportModule)
    if (props.args.custom_css) {
      addCustomCSS(props.args.custom_css)
    }

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

    this.frameDtypes = this.props.args.frame_dtypes
    this.manualUpdateRequested = this.props.args.update_mode === 1
    this.allowUnsafeJsCode = this.props.args.allow_unsafe_jscode
    this.gridContainerRef = React.createRef()
    this.isGridAutoHeightOn =
      this.props.args.gridOptions?.domLayout === "autoHeight"

    this.columnFormaters = {
      columnTypes: {
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
            this.dateFormatter(params.value, "dd/MM/yyyy HH:mm"),
        },
        customDateTimeFormat: {
          valueFormatter: (params: any) =>
            this.dateFormatter(
              params.value,
              params.column.colDef.custom_format_string
            ),
        },
        customNumericFormat: {
          valueFormatter: (params: any) =>
            this.numberFormatter(
              params.value,
              params.column.colDef.precision ?? 2
            ),
        },
        customCurrencyFormat: {
          valueFormatter: (params: any) =>
            this.currencyFormatter(
              params.value,
              params.column.colDef.custom_currency_symbol
            ),
        },
        timedeltaFormat: {
          valueFormatter: (params: any) =>
            duration(params.value).humanize(true),
        },
      },
    }

    let gridOptions = Object.assign(
      {},
      this.columnFormaters,
      this.props.args.gridOptions
    )

    if (this.allowUnsafeJsCode) {
      console.warn("flag allow_unsafe_jscode is on.")
      gridOptions = this.convertJavascriptCodeOnGridOptions(gridOptions)
    }
    this.gridOptions = gridOptions

    this.state = {
      rowData: JSON.parse(props.args.row_data),
      gridHeight: this.props.args.height,
      should_update: false,
    }
  }

  static getDerivedStateFromProps(props: any, state: any) {
    if (props.args.reload_data) {
      let new_row_data = JSON.parse(props.args.row_data)

      return {
        rowData: new_row_data,
        gridHeight: props.args.height,
        should_update: true,
      }
    } else {
      return {
        gridHeight: props.args.height,
      }
    }
  }

  private convertStringToFunction(v: string) {
    const JS_PLACEHOLDER = "--x_x--0_0--"
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

  private convertJavascriptCodeOnGridOptions = (obj: object) => {
    return deepMap(obj, this.convertStringToFunction)
  }

  private attachUpdateEvents(api: GridApi) {
    let updateEvents = this.props.args.update_on
    const doReturn = (e: any) => this.returnGridValue(e)

    updateEvents.forEach((element: any) => {
      if (Array.isArray(element)) {
        api.addEventListener(element[0], debounce(doReturn, element[1]))
      } else {
        api.addEventListener(element, doReturn)
      }
    })
  }

  private loadColumnsState() {
    const columnsState = this.props.args.columns_state

    if (columnsState != null) {
      this.columnApi.applyColumnState({ state: columnsState, applyOrder: true })
    }
  }

  private onGridReady(event: any) {
    this.api = event.api
    this.columnApi = event.columnApi

    this.attachUpdateEvents(this.api)
    this.api.forEachDetailGridInfo((i: DetailGridInfo) => {
      if (i.api !== undefined) {
        this.attachUpdateEvents(i.api)
      }
    })

    this.api.addEventListener("rowGroupOpened", (e: any) =>
      this.resizeGridContainer(e)
    )

    this.api.addEventListener("firstDataRendered", (e: any) =>
      this.fitColumns()
    )

    this.api.setRowData(this.state.rowData)

    var preSelectAllRows =
      this.props.args.gridOptions["preSelectAllRows"] || false
    if (preSelectAllRows) {
      this.api.selectAll()
      this.returnGridValue(event)
    } else {
      if (
        this.gridOptions["preSelectedRows"] ||
        this.gridOptions["preSelectedRows"]?.length() > 0
      ) {
        for (var idx in this.gridOptions["preSelectedRows"]) {
          this.api.getRowNode(idx)?.setSelected(true, false, true)
          this.returnGridValue(event)
        }
      }
    }

    if (this.isGridAutoHeightOn) {
      this.resizeGridContainer(null)
    }
  }

  private resizeGridContainer(event: any) {
    const renderedGridHeight = this.gridContainerRef.current?.clientHeight
    Streamlit.setFrameHeight(renderedGridHeight)
  }

  private fitColumns() {
    const columns_auto_size_mode = this.props.args.columns_auto_size_mode

    switch (columns_auto_size_mode) {
      case 1:
      case "FIT_ALL_COLUMNS_TO_VIEW":
        this.api.sizeColumnsToFit()
        break

      case 2:
      case "FIT_CONTENTS":
        this.columnApi.autoSizeAllColumns()
        break

      default:
        break
    }
  }

  private dateFormatter(isoString: string, formaterString: string): String {
    try {
      let date = parseISO(isoString)
      return format(date, formaterString)
    } catch {
      return isoString
    } finally {
    }
  }

  private currencyFormatter(number: any, currencySymbol: string): String {
    let n = Number.parseFloat(number)
    if (!Number.isNaN(n)) {
      return currencySymbol + n.toFixed(2)
    } else {
      return number
    }
  }

  private numberFormatter(number: any, precision: number): String {
    let n = Number.parseFloat(number)
    if (!Number.isNaN(n)) {
      return n.toFixed(precision)
    } else {
      return number
    }
  }

  private returnGridValue(e: any) {
    let returnData: any[] = []
    let returnMode = this.props.args.data_return_mode

    switch (returnMode) {
      case 0: //ALL_DATA
        this.api.forEachLeafNode((row) => returnData.push(row.data))
        break

      case 1: //FILTERED_DATA
        this.api.forEachNodeAfterFilter((row) => {
          if (!row.group) {
            returnData.push(row.data)
          }
        })
        break

      case 2: //FILTERED_SORTED_DATA
        this.api.forEachNodeAfterFilterAndSort((row) => {
          if (!row.group) {
            returnData.push(row.data)
          }
        })
        break
    }

    let selected: any = {}
    this.api.forEachDetailGridInfo((d: DetailGridInfo) => {
      selected[d.id] = []
      d.api?.forEachNode((n: RowNode<any>) => {
        if (n.isSelected()) {
          selected[d.id].push(n)
        }
      })
    })

    let returnValue = {
      originalDtypes: this.frameDtypes,
      rowData: returnData,
      selectedRows: this.api.getSelectedRows(),
      selectedItems: this.api.getSelectedNodes().map((n, i) => ({
        _selectedRowNodeInfo: { nodeRowIndex: n.rowIndex, nodeId: n.id },
        ...n.data,
      })),
      colState: this.columnApi.getColumnState(),
    }

    Streamlit.setComponentValue(returnValue)
  }

  private ManualUpdateButton(props: any) {
    if (props.manualUpdate) {
      return (
        <button onClick={props.onClick} style={{ marginLeft: 10 }}>
          Update
        </button>
      )
    }
    return <></>
  }

  private defineContainerHeight() {
    if (this.isGridAutoHeightOn) {
      return {
        width: this.props.width,
      }
    } else {
      return {
        width: this.props.width,
        height: this.state.gridHeight,
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

  private QuickSearch(props: any) {
    if (props.enableQuickSearch) {
      return (
        <input
          className="ag-cell-value"
          type="text"
          onChange={props.onChange}
          placeholder="quickfilter..."
        />
      )
    }
    return <></>
  }

  private GridToolBar(props: any) {
    if (true) {
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

  public render = (): ReactNode => {
    if (this.api !== undefined) {
      if (this.state.should_update) {
        this.api.setRowData(this.state.rowData)
      }
    }
    this.loadColumnsState()
    let shouldRenderGridToolbar =
      this.props.args.enable_quicksearch === true ||
      this.props.args.manual_update

    return (
      <div
        id="gridContainer"
        className={this.getThemeClass()}
        ref={this.gridContainerRef}
        style={this.defineContainerHeight()}
      >
        <this.GridToolBar enabled={shouldRenderGridToolbar}>
          <this.ManualUpdateButton
            manualUpdate={this.props.args.manual_update}
            onClick={(e: any) => this.returnGridValue(e)}
          />
          <this.QuickSearch
            enableQuickSearch={this.props.args.enable_quicksearch}
            onChange={(e: any) => this.api.setQuickFilter(e.target.value)}
          />
        </this.GridToolBar>
        <AgGridReact
          onGridReady={(e) => this.onGridReady(e)}
          gridOptions={this.gridOptions}
        ></AgGridReact>
      </div>
    )
  }
}

export default withStreamlitConnection(AgGrid)


