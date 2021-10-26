import {
  Streamlit,
  StreamlitComponentBase,
  withStreamlitConnection
} from "streamlit-component-lib";

import { ReactNode } from "react"

import { AgGridReact } from '@ag-grid-community/react';
import { ColumnApi, GridApi } from '@ag-grid-community/core'
import { ModuleRegistry } from '@ag-grid-community/core';
import { AllCommunityModules } from '@ag-grid-community/all-modules'
import { AllModules } from '@ag-grid-enterprise/all-modules'
import { LicenseManager } from "@ag-grid-enterprise/core";

import { parseISO, compareAsc } from 'date-fns'
import { format } from 'date-fns-tz'
import deepMap from "./utils"
import { duration } from "moment";

import '@ag-grid-community/core/dist/styles/ag-theme-blue.css';
import '@ag-grid-community/core/dist/styles/ag-theme-fresh.css';
import '@ag-grid-community/core/dist/styles/ag-theme-material.css';

import './AgGrid.scss'
import './scrollbar.css'

interface State {
  rowData: any
  gridHeight: number
  should_update: boolean
}

class AgGrid extends StreamlitComponentBase<State> {
  private frameDtypes: any
  private api!: GridApi;
  private columnApi!: ColumnApi
  private columnFormaters: any
  private manualUpdateRequested: boolean = false
  private allowUnsafeJsCode: boolean = false
  private fitColumnsOnGridLoad: boolean = false
  private gridOptions: any

  constructor(props: any) {
    super(props)

    if (props.args.enable_enterprise_modules) {
      ModuleRegistry.registerModules(AllModules);
      if ('license_key' in props.args) {
        LicenseManager.setLicenseKey(props.args['license_key']);
      }
    } else {
      ModuleRegistry.registerModules(AllCommunityModules);
    }

    this.frameDtypes = this.props.args.frame_dtypes
    this.manualUpdateRequested = (this.props.args.update_mode === 1)
    this.allowUnsafeJsCode = this.props.args.allow_unsafe_jscode
    this.fitColumnsOnGridLoad = this.props.args.fit_columns_on_grid_load
    
    this.columnFormaters = {
      columnTypes: {
        'dateColumnFilter': {
          filter: 'agDateColumnFilter',
          filterParams: {
            comparator: (filterValue: any, cellValue: string) => compareAsc(parseISO(cellValue), filterValue)
          }
        },
        'numberColumnFilter': {
          filter: 'agNumberColumnFilter'
        },
        'shortDateTimeFormat': {
          valueFormatter: (params: any) => this.dateFormatter(params.value, "dd/MM/yyyy HH:mm"),
        },
        'customDateTimeFormat': {
          valueFormatter: (params: any) => this.dateFormatter(params.value, params.column.colDef.custom_format_string),
        },
        'customNumericFormat': {
          valueFormatter: (params: any) => this.numberFormatter(params.value, params.column.colDef.precision ?? 2),
        },
        'customCurrencyFormat': {
          valueFormatter: (params: any) => this.currencyFormatter(params.value, params.column.colDef.custom_currency_symbol),
        },
        'timedeltaFormat': {
          valueFormatter: (params: any) => duration(params.value).humanize(true)
        },
      }
    }

    let gridOptions = Object.assign({}, this.columnFormaters, this.props.args.gridOptions)

    if (this.allowUnsafeJsCode) {
      console.warn("flag allow_unsafe_jscode is on.")
      gridOptions = this.convertJavascriptCodeOnGridOptions(gridOptions)
    }
    this.gridOptions = gridOptions

    this.state = {
      rowData: JSON.parse(props.args.row_data),
      gridHeight: this.props.args.height,
      should_update: false
    }
  }

  static getDerivedStateFromProps(props: any, state: any) {
    if (props.args.reload_data) {

      let new_row_data = JSON.parse(props.args.row_data)

      return {
        rowData: new_row_data,
        gridHeight: props.args.height,
        should_update: true
      }
    } else {
      return {
        gridHeight: props.args.height
      }
    }
  }

  private convertStringToFunction(v: string) {
    const JS_PLACEHOLDER = "--x_x--0_0--"

    let funcReg = new RegExp(
      `${JS_PLACEHOLDER}\\s*(function\\s*.*)\\s*${JS_PLACEHOLDER}`
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

  private setUpdateMode() {
    if (this.manualUpdateRequested) {
      return //If manual update is set, no listeners will be added
    }

    let updateMode = this.props.args.update_mode

    if ((updateMode & 2) === 2) {
      this.api.addEventListener('cellValueChanged', (e: any) => this.returnGridValue(e))
    }

    if ((updateMode & 4) === 4) {
      this.api.addEventListener('selectionChanged', (e: any) => this.returnGridValue(e))
    }

    if ((updateMode & 8) === 8) {
      this.api.addEventListener('filterChanged', (e: any) => this.returnGridValue(e))
    }

    if ((updateMode & 16) === 16) {
      this.api.addEventListener('sortChanged', (e: any) => this.returnGridValue(e))
    }
  }

  private onGridReady(event: any) {
    this.api = event.api
    this.columnApi = event.columnApi

    this.setUpdateMode()
    this.api.addEventListener('firstDataRendered', (e: any) => this.fitColumns())

    this.api.setRowData(this.state.rowData)

    for (var idx in this.gridOptions['preSelectedRows']) {
      this.api.selectIndex(this.gridOptions['preSelectedRows'][idx], true, true)
    }
  }

  private fitColumns() {
    if (this.fitColumnsOnGridLoad) {
      this.api.sizeColumnsToFit()
    }
    else {
      this.columnApi.autoSizeAllColumns()
    }
  }

  private dateFormatter(isoString: string, formaterString: string): String {
    try {
      let date = parseISO(isoString)
      return format(date, formaterString)
    } catch {
      return isoString
    }
    finally { }
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
        break;

      case 1: //FILTERED_DATA
        this.api.forEachNodeAfterFilter((row) => { if (!row.group) { returnData.push(row.data) } })
        break;

      case 2: //FILTERED_SORTED_DATA
        this.api.forEachNodeAfterFilterAndSort((row) => { if (!row.group) { returnData.push(row.data) } })
        break;
    }

    let returnValue = {
      originalDtypes: this.frameDtypes,
      rowData: returnData,
      selectedRows: this.api.getSelectedRows()
    }

    Streamlit.setComponentValue(returnValue)
  }

  private ManualUpdateButton(props: any) {
    if (props.manual_update) {
      return (<button onClick={props.onClick}>Update</button>)
    }
    else {
      return (<span></span>)
    }
  }

  private defineContainerHeight() {
    if ('domLayout' in this.gridOptions) {
      if (this.gridOptions['domLayout'] === 'autoHeight') {
        return ({
          width: this.props.width
        })
      }
    }
    return ({
      width: this.props.width,
      height: this.state.gridHeight
    })
  }

  public render = (): ReactNode => {

    if (this.api !== undefined) {
      if (this.state.should_update) {
        this.api.setRowData(this.state.rowData)
      }
    }

    return (
      <div className={"ag-theme-"+ this.props.args.theme} style={this.defineContainerHeight()} >
        <this.ManualUpdateButton manual_update={this.manualUpdateRequested} onClick={(e: any) => this.returnGridValue(e)} />
        <AgGridReact
          onGridReady={(e) => this.onGridReady(e)}
          gridOptions={this.gridOptions}
        >
        </AgGridReact>
      </div >
    )
  }
}

export default withStreamlitConnection(AgGrid)
