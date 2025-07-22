import { AgGridReact } from "ag-grid-react"
import React, { ReactNode } from "react"

import {
  ComponentProps,
  Streamlit,
  withStreamlitConnection,
} from "streamlit-component-lib"

import {
  AllCommunityModule,
  CellValueChangedEvent,
  DetailGridInfo,
  GetRowIdParams,
  GridApi,
  GridOptions,
  GridReadyEvent,
  GridSizeChangedEvent,
  ModuleRegistry,
} from "ag-grid-community"

import { AgChartsEnterpriseModule } from "ag-charts-enterprise"
import { AllEnterpriseModule, LicenseManager } from "ag-grid-enterprise"

import {debounce, cloneDeep, every, isEqual} from "lodash"

import { columnFormaters } from "./customColumns"
import { deepMap } from "./utils"
import { ThemeParser } from "./ThemeParser"
import { getGridReturnValue } from "./utils/agGridReturnUtils"

import "@fontsource/source-sans-pro"
import "./AgGrid.css"

import GridToolBar from "./components/GridToolBar"
// import ManualUpdateButton from "./components/ManualUpdateButton"
// import ManualDownloadButton from "./components/ManualDownloadButton"
// import QuickSearch from "./components/QuickSearch"

import { addCustomCSS, injectProAssets, parseJsCodeFromPython } from "./utils/gridUtils"

import { State } from "./types/AgGridTypes"

class AgGrid extends React.Component<ComponentProps, State> {
  public state: State

  private gridContainerRef: React.RefObject<HTMLDivElement>
  private isGridAutoHeightOn: boolean
  private renderedGridHeightPrevious: number = 0
  private themeParser: ThemeParser | undefined = undefined

  constructor(props: ComponentProps) {
    super(props)
    this.gridContainerRef = React.createRef()

    if (props.args.custom_css) {
      addCustomCSS(props.args.custom_css)
    }

    if (props.args.pro_assets && Array.isArray(props.args.pro_assets)) {
      props.args.pro_assets.forEach((asset: any) => {
      //console.log(asset);
      injectProAssets(asset?.js, asset?.css)
      })
    }
    const enableEnterpriseModules = props.args.enable_enterprise_modules
    if (
      enableEnterpriseModules === true ||
      enableEnterpriseModules === "enterprise+AgCharts"
    ) {
      ModuleRegistry.registerModules([
      AllEnterpriseModule.with(AgChartsEnterpriseModule),
      ])
      if ("license_key" in props.args) {
      LicenseManager.setLicenseKey(props.args["license_key"])
      }
    } else if (enableEnterpriseModules === "enterpriseOnly") {
      ModuleRegistry.registerModules([AllEnterpriseModule])
      if ("license_key" in props.args) {
      LicenseManager.setLicenseKey(props.args["license_key"])
      }
    } else {
      ModuleRegistry.registerModules([AllCommunityModule])
    }


    this.isGridAutoHeightOn =
      this.props.args.gridOptions?.domLayout === "autoHeight"

    var go = this.parseGridoptions()

    const StreamlitAgGridPro = (window as any)?.StreamlitAgGridPro
    if (StreamlitAgGridPro) {
      StreamlitAgGridPro.returnGridValue = this.returnGridValue.bind(this)

      if (StreamlitAgGridPro.extenders && Array.isArray(StreamlitAgGridPro.extenders)) {
        StreamlitAgGridPro.extenders.forEach((extender: (go: any) => void) => {
          if (typeof extender === "function") {
            extender(go)
          }
        })
      }
    }

    this.state = {
      gridHeight: this.props.args.height,
      gridOptions: go,
      isRowDataEdited: false,
      api: undefined,
      enterprise_features_enabled: props.args.enable_enterprise_modules,
      debug: false,
    } as State

    if (this.state.debug) {
      console.log("***Received Props", props)
      console.log("*** Processed State", this.state)
    }
  }

  private parseGridoptions() {
    let gridOptions: GridOptions = cloneDeep(this.props.args.gridOptions)

    if (this.props.args.allow_unsafe_jscode) {
      console.warn("flag allow_unsafe_jscode is on.")
      gridOptions = deepMap(gridOptions, parseJsCodeFromPython, ["rowData"])
    }

    //Sets getRowID if data came from a pandas dataframe like object. (has __pandas_index)
    if (every(gridOptions.rowData, (o) => "__pandas_index" in o)) {
      if (!("getRowId" in gridOptions)) {
        gridOptions["getRowId"] = (params: GetRowIdParams) =>
          params.data.__pandas_index as string
      }
    }

    if (!("getRowId" in gridOptions)) {
      console.warn("getRowId was not set. Grid may behave bad when updating.")
    }

    //adds custom columnFormatters
    gridOptions.columnTypes = Object.assign(
      gridOptions.columnTypes || {},
      columnFormaters
    )

    //processTheming
    this.themeParser = new ThemeParser()
    let streamlitTheme = this.props.theme
    let agGridTheme = this.props.args.theme

    gridOptions.theme = this.themeParser.parse(agGridTheme, streamlitTheme)

    return gridOptions
  }

  private attachStreamlitRerunToEvents(api: GridApi) {
    const updateEvents = this.props.args.update_on;

    updateEvents.forEach((element: any) => {
        if (Array.isArray(element)) {
            // If element is a tuple (eventName, timeout), apply debounce for the timeout duration
            const [eventName, timeout] = element;
            api.addEventListener(
                eventName,
                debounce(
                    (e: any) => {
                        this.returnGridValue(e, eventName);
                    },
                    timeout,
                    {
                        leading: false,
                        trailing: true,
                        maxWait: timeout,
                    }
                )
            );
        } else {
            // Attach event listener for non-tuple events
            api.addEventListener(element, (e: any) => {
                this.returnGridValue(e, element);
            });
        }
        console.log(`Attached grid return event: ${element}`);
    });
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
    return getGridReturnValue(
      this.state.api,
      this.state.enterprise_features_enabled,
      this.state.gridOptions,
      this.props,
      e,
      streamlitRerunEventTriggerName
    )
  }

  private returnGridValue(e: any, streamlitRerunEventTriggerName: string) {
    if (this.state.debug) {
      console.log(`refreshing grid from ${streamlitRerunEventTriggerName}`)
    }
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

  public componentDidUpdate(prevProps: any, prevState: State, snapshot?: any) {
    const prevGridOptions = prevProps.args.gridOptions
    const currGridOptions = this.props.args.gridOptions

    //Theme object Changes here
    if (
      !isEqual(prevProps.theme, this.props.theme) ||
      !isEqual(this.props.args.theme, prevProps.args.theme)
    ) {
      let streamlitTheme = this.props.theme
      let agGridTheme = this.props.args.theme

      this.state.api?.updateGridOptions({
        theme: this.themeParser?.parse(agGridTheme, streamlitTheme),
      })
    }

    //const objectDiff = (a: any, b: any) => fromPairs(differenceWith(toPairs(a), toPairs(b), isEqual))
    if (!isEqual(prevGridOptions, currGridOptions)) {
      let go = this.parseGridoptions()
      let row_data = go.rowData

      if (!this.state.isRowDataEdited) {
        this.state.api?.updateGridOptions({ rowData: row_data })
      }

      delete go.rowData
      this.state.api?.updateGridOptions(go)
    }

    if (
      !isEqual(prevProps.args.columns_state, this.props.args.columns_state)
    ) {
      this.loadColumnsState()
    }
  }

  private onGridReady(event: GridReadyEvent) {
    this.setState({ api: event.api })

    //Is it ugly? Yes. Does it work? Yes. Why? IDK
    // eslint-disable-next-line
    this.state.api = event.api

    this.state.api?.addEventListener("rowGroupOpened", (e: any) =>
      this.resizeGridContainer()
    )

    this.state.api?.addEventListener("firstDataRendered", (e: any) => {
      this.resizeGridContainer()
    })

    this.state.api.addEventListener(
      "gridSizeChanged",
      (e: GridSizeChangedEvent) => this.onGridSizeChanged(e)
    )
    this.state.api.addEventListener(
      "cellValueChanged",
      (e: CellValueChangedEvent) => this.cellValueChanged(e)
    )

    //Attach events
    this.attachStreamlitRerunToEvents(this.state.api)

    if (this.state.enterprise_features_enabled) {
      this.state.api?.forEachDetailGridInfo((i: DetailGridInfo) => {
        if (i.api !== undefined) {
          this.attachStreamlitRerunToEvents(i.api)
        }
      })
    }

    //If there is any event onGridReady in gridOptions, fire it
    let { onGridReady } = this.state.gridOptions
    onGridReady && onGridReady(event)
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
    let manualUpdate =  this.props.args.manual_update === true

    return (
      <div
        id="gridContainer"
        ref={this.gridContainerRef}
        style={this.defineContainerHeight()}
      >
        <GridToolBar
          showManualUpdateButton={manualUpdate}
          enabled={this.props.args.show_toolbar ?? true}
          showSearch={this.props.args.show_search ?? true}
          showDownloadButton={this.props.args.show_download_button ?? true}
          onQuickSearchChange={(value) => {
        this.state.api?.setGridOption("quickFilterText", value);
        this.state.api?.hideOverlay(); // Hide any overlay if present
          }}
          onDownloadClick={() => {
        this.state.api?.exportDataAsCsv();
          }}
          onManualUpdateClick={() => {
        console.log("Manual update triggered");
          }}
        />
        <AgGridReact
          onGridReady={(e: GridReadyEvent<any, any>) => this.onGridReady(e)}
          gridOptions={this.state.gridOptions}
        ></AgGridReact>
      </div>
    )
  }
}

export default withStreamlitConnection(AgGrid)