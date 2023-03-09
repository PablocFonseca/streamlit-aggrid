import {
  Streamlit,
  ComponentProps,
  withStreamlitConnection,
} from "streamlit-component-lib"

import React, { ReactNode } from "react"
import { AgGridReact } from "@ag-grid-community/react"

import {
  ModuleRegistry,
  ColumnApi,
  GridApi,
  DetailGridInfo
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

import { parseISO, compareAsc } from "date-fns"
import { format } from "date-fns-tz"
import deepMap from "./utils"
import { duration } from "moment"

import { debounce, throttle } from "lodash"

import { encode, decode } from "base64-arraybuffer"
import { Buffer} from 'buffer'

import "./agGridStyle.scss"

import "@fontsource/source-sans-pro"

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
  },
}

function parseJsCodeFromPython(v: string) {
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

function GridToolBar(props: any) {
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
class AgGrid<S = {}> extends React.Component<ComponentProps, S> {
  private api!: GridApi
  private columnApi!: ColumnApi
  private columnFormaters: any
  private gridOptions: any
  private gridContainerRef: React.RefObject<HTMLDivElement>
  private isGridAutoHeightOn: boolean

  constructor(props: any) {
    super(props)
    //console.log("Grid INIT called", props)

    this.gridContainerRef = React.createRef()

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

    this.isGridAutoHeightOn =
      this.props.args.gridOptions?.domLayout === "autoHeight"

    this.parseGridoptions()
  }

  private parseGridoptions() {
    let gridOptions = Object.assign(
      {},
      columnFormaters,
      this.props.args.gridOptions
    )

    if (this.props.args.allow_unsafe_jscode) {
      console.warn("flag allow_unsafe_jscode is on.")
      gridOptions = deepMap(gridOptions, parseJsCodeFromPython)
    }
    this.gridOptions = gridOptions
  }

  private attachStreamlitRerunToEvents(api: GridApi) {
    const updateEvents = this.props.args.update_on
    const doReturn = (e: any) => this.returnGridValue()

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

  private DownloadAsExcelIfRequested() {
    if (this.api) {

      if (
        this.props.args.excel_export_mode === "MULTIPLE_SHEETS" &&
        this.props.args.ExcelExportMultipleSheetParams
      ) {
        let params = this.props.args.ExcelExportMultipleSheetParams

        let data = params.data.map((v: string) =>
          Buffer.from(decode(v)).toString("latin1")
        )
        params.data = data
        
        this.api.exportMultipleSheetsAsExcel(params)
      }
      if (this.props.args.excel_export_mode === "TRIGGER_DOWNLOAD") {
        this.api.exportDataAsExcel()
      }
    }
  }

  private handleExcelExport() {
    if (this.props.args.excel_export_mode === "FILE_BLOB_IN_GRID_RESPONSE") {
      let blob = this.api.getDataAsExcel() as Blob
      let buffer;
      (async () => {
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
      let blob = this.api.getSheetDataForExcel({
        sheetName: Math.round(Date.now() / 1000).toString(),
      })
      if (blob) return encode(Buffer.from(blob, 'latin1')) ///Buffer.from(blob).toString('base64')
    }

    return null
  }

  private resizeGridContainer() {
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

  private async getGridReturnValue() {
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
      d.api?.forEachNode((n) => {
        if (n.isSelected()) {
          selected[d.id].push(n)
        }
      })
    })

    let returnValue = {
      originalDtypes: this.props.args.frame_dtypes,
      rowData: returnData,
      selectedRows: this.api.getSelectedRows(),
      selectedItems: this.api.getSelectedNodes().map((n, i) => ({
        _selectedRowNodeInfo: { nodeRowIndex: n.rowIndex, nodeId: n.id },
        ...n.data,
      })),
      colState: this.columnApi.getColumnState(),
      ExcelBlob: this.handleExcelExport(),
    }
    //console.dir(returnValue)
    return returnValue
  }

  private returnGridValue() {
    this.getGridReturnValue().then((v) => Streamlit.setComponentValue(v))
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

  public componentDidUpdate(prevProps: any, prevState: S, snapshot?: any) {

    const previous_export_mode = prevProps.args.excel_export_mode
    const current_export_mode = this.props.args.excel_export_mode

    if (
      ((previous_export_mode !== "TRIGGER_DOWNLOAD") && (current_export_mode === "TRIGGER_DOWNLOAD")) ||
      ((previous_export_mode !== "MULTIPLE_SHEETS") && (current_export_mode === "MULTIPLE_SHEETS"))
    ) {
      this.DownloadAsExcelIfRequested()
    }

    if ((this.props.args.reload_data) && (this.api)){
        this.api.setRowData(JSON.parse(this.props.args.row_data))
    }


    this.resizeGridContainer()
  }

  private onGridReady(event: any) {
    this.api = event.api
    this.columnApi = event.columnApi

    this.api.addEventListener(
      "rowGroupOpened",
      (e: any) => this.resizeGridContainer()
    )

    this.api.addEventListener("firstDataRendered", (e: any) => {
      this.resizeGridContainer();
      this.fitColumns()
    })

    this.attachStreamlitRerunToEvents(this.api)
    this.api.forEachDetailGridInfo((i: DetailGridInfo) => {
      if (i.api !== undefined) {
        this.attachStreamlitRerunToEvents(i.api)
      }
    })

    this.api.setRowData(JSON.parse(this.props.args.row_data))

    this.processPreselection()
  }

  private processPreselection() {
    var preSelectAllRows =
      this.props.args.gridOptions["preSelectAllRows"] || false
    if (preSelectAllRows) {
      this.api.selectAll()
      this.returnGridValue()
    } else {
      if (
        this.gridOptions["preSelectedRows"] ||
        this.gridOptions["preSelectedRows"]?.length() > 0
      ) {
        for (var idx in this.gridOptions["preSelectedRows"]) {
          this.api.getRowNode(idx)?.setSelected(true, false, true)
          this.returnGridValue()
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
            onClick={(e: any) => this.returnGridValue()}
          />
          <ManualDownloadButton
            enabled={this.props.args.excelExportMode === "MANUAL"}
            onClick={(e: any) => this.api?.exportDataAsExcel()}
          />
          <QuickSearch
            enableQuickSearch={this.props.args.enable_quicksearch}
            showOverlay={throttle(() => this.api.showLoadingOverlay(), 1000, {
              trailing: false,
            })}
            onChange={debounce((e) => {
              this.api.setQuickFilter(e.target.value)
              this.api.hideOverlay()
            }, 1000)}
          />
        </GridToolBar>
        <AgGridReact
          onGridReady={(e) => this.onGridReady(e)}
          gridOptions={this.gridOptions}
        ></AgGridReact>
      </div>
    )
  }
}

export default withStreamlitConnection(AgGrid)
