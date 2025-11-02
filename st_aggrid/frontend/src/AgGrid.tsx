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
  GridReadyEvent,
  GridSizeChangedEvent,
  ModuleRegistry,
} from "ag-grid-community"

import { AgChartsEnterpriseModule } from "ag-charts-enterprise"
import { AllEnterpriseModule, LicenseManager } from "ag-grid-enterprise"

import { debounce, isEqual, omit } from "lodash"
import { ThemeParser } from "./ThemeParser"
import { CustomCollector, LegacyCollector } from "./collectors"
import type { CollectorContext } from "./collectors"

import "@fontsource/source-sans-pro"
import "./AgGrid.css"

import GridToolBar from "./components/GridToolBar"

import {
  addCustomCSS,
  injectProAssets,
  parseJsCodeFromPython,
} from "./utils/gridUtils"

import { State } from "./types/AgGridTypes"
import { parseGridOptions, parseData } from "./utils/parsers"

class AgGrid extends React.Component<ComponentProps, State> {
  public state: State

  private gridContainerRef: React.RefObject<HTMLDivElement>
  private isGridAutoHeightOn: boolean
  private renderedGridHeightPrevious: number = 0
  private themeParser: ThemeParser | undefined = undefined
  private shouldGridReturn: Function | undefined = undefined
  private collectGridReturn: Function | undefined = undefined

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
    if (enableEnterpriseModules === "enterprise+AgCharts") {
      ModuleRegistry.registerModules([
        AllEnterpriseModule.with(AgChartsEnterpriseModule),
      ])
      if ("license_key" in props.args) {
        LicenseManager.setLicenseKey(props.args["license_key"])
      }
    } else if (
      enableEnterpriseModules === true ||
      enableEnterpriseModules === "enterpriseOnly"
    ) {
      ModuleRegistry.registerModules([AllEnterpriseModule])
      if ("license_key" in props.args) {
        LicenseManager.setLicenseKey(props.args["license_key"])
      }
    } else {
      ModuleRegistry.registerModules([AllCommunityModule])
    }

    const StreamlitAgGridPro = (window as any)?.StreamlitAgGridPro
    if (StreamlitAgGridPro) {
      StreamlitAgGridPro.returnGridValue = this.returnGridValue.bind(this)

      if (
        StreamlitAgGridPro.extenders &&
        Array.isArray(StreamlitAgGridPro.extenders)
      ) {
        StreamlitAgGridPro.extenders.forEach((extender: (go: any) => void) => {
          if (typeof extender === "function") {
            extender(go)
          }
        })
      }
    }

    this.isGridAutoHeightOn =
      this.props.args.gridOptions?.domLayout === "autoHeight"

    var go = parseGridOptions(props)
    go.rowData = parseData(props)

    if (!("getRowId" in go)) {
      if (
        Array.isArray(go.rowData) &&
        go.rowData.length > 0 &&
        go.rowData[0].hasOwnProperty("::auto_unique_id::")
      ) {
        go.getRowId = (params: GetRowIdParams) =>
          params.data["::auto_unique_id::"] as string
      }
    }

    this.shouldGridReturn = props.args.should_grid_return
      ? parseJsCodeFromPython(props.args.should_grid_return)
      : null
    this.collectGridReturn = props.args.custom_jscode_for_grid_return
      ? parseJsCodeFromPython(props.args.custom_jscode_for_grid_return)
      : null

    this.state = {
      gridHeight: this.props.args.height,
      gridOptions: go,
      isRowDataEdited: false,
      api: undefined,
      enterprise_features_enabled: props.args.enable_enterprise_modules,
      debug: props.args.debug || false,
      editedRows: new Set(),
    } as State

    if (this.state.debug) {
      console.log("***Received Props", props)
      console.log("*** Processed State", this.state)
    }
  }

  private attachStreamlitRerunToEvents(api: GridApi) {
    const updateEvents = this.props.args.update_on

    updateEvents.forEach((element: any) => {
      if (Array.isArray(element)) {
        // If element is a tuple (eventName, timeout), apply debounce for the timeout duration
        const [eventName, timeout] = element
        api.addEventListener(
          eventName,
          debounce(
            (e: any) => {
              this.returnGridValue(e, eventName)
            },
            timeout,
            {
              leading: false,
              trailing: true,
              maxWait: timeout,
            }
          )
        )
      } else {
        // Attach event listener for non-tuple events
        api.addEventListener(element, (e: any) => {
          this.returnGridValue(e, element)
        })
      }
      if (this.state.debug) {
        console.log(`Attached grid return event: ${element}`)
      }
    })
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

  private async returnGridValue(
    eventData: any,
    streamlitRerunEventTriggerName: string
  ) {
    if (this.state.debug) {
      console.log(`refreshing grid from ${streamlitRerunEventTriggerName}`)
      console.log("dataReturnMode is ", this.props.args.data_return_mode)
    }

    // Create collector context
    const context: CollectorContext = {
      state: this.state,
      props: this.props,
      eventData: eventData,
      streamlitRerunEventTriggerName: streamlitRerunEventTriggerName,
    }

    const collectorFactory = {
      AS_INPUT: new LegacyCollector(),
      FILTERED: new LegacyCollector(),
      FILTERED_AND_SORTED: new LegacyCollector(),
      MINIMAL: new LegacyCollector(),
      CUSTOM: new CustomCollector(this.collectGridReturn || (() => {})),
    }

    try {
      // Determine and create appropriate collector
      const collector =
        collectorFactory[
          this.props.args.data_return_mode as keyof typeof collectorFactory
        ]

      // Process response using collector
      const result = await collector.processResponse(context)

      if (result.success) {
        if (this.state.debug) {
          console.log(
            `Grid response processed by ${collector.getCollectorType()}:`,
            result.data
          )
        }
        // Check shouldGridReturn before sending value back to Python
        if (this.shouldGridReturn) {
          const shouldReturn = this.shouldGridReturn({ streamlitRerunEventTriggerName, eventData });
          if (!shouldReturn) {
            if (this.state.debug) {
              console.log(`shouldGridReturn blocked return for event: ${streamlitRerunEventTriggerName}`);
            }
            return; // Don't send value back
          }
        }
        Streamlit.setComponentValue(result.data)
      } else {
        console.error(`Collector processing failed: ${result.error}`)
        // Fallback to no return to avoid breaking the UI
      }
    } catch (error) {
      console.error("Error in returnGridValue collector processing:", error)
      // Fallback to no return to avoid breaking the UI
    }
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
    if (this.state.debug) {
      console.log("********** componentDidUpdate.prevProps")
      console.log(prevProps)
      console.log("********** componentDidUpdate.this")
      console.log(this)
    }

    //Check update on grid options. TODO: exclude `initial` options
    const prevGridOptions = omit(prevProps.args.gridOptions, "rowData")
    const currGridOptions = omit(this.props.args.gridOptions, "rowData")

    if (!isEqual(prevGridOptions, currGridOptions)) {
      let go = parseGridOptions(this.props)
      this.state.api?.updateGridOptions(go)
    }

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

    //Check if data changed and updates

    const serverSyncStragegy = this.props.args?.server_sync_strategy
    if (serverSyncStragegy === "client_wins") {
      if (!this.state.isRowDataEdited) {
        if (this.props.args.data_hash !== prevProps.args.data_hash) {
          const rowData = parseData(this.props) || []
          this.state.api?.updateGridOptions({ rowData })
        }
      }
    } else if (serverSyncStragegy === "server_wins") {
      const rowData = parseData(this.props) || []
      this.state.api?.stopEditing(true)
      this.state.api?.updateGridOptions({ rowData })
    }

    //check if columnStates changed
    if (!isEqual(prevProps.args.columns_state, this.props.args.columns_state)) {
      const columnsState = this.props.args.columns_state
      if (columnsState != null) {
        this.state.api?.applyColumnState({
          state: columnsState,
          applyOrder: true,
        })
      }
    }
  }

  private onGridReady(event: GridReadyEvent) {
    this.setState({ api: event.api })

    //Is it ugly? Yes. Does it work? Yes. Why? IDK
    // eslint-disable-next-line
    this.state.api = event.api

    // if (this.state.debug ) {
    //   this.state.api?.addGlobalListener((eventType, event) =>
    //     console.log("GlobalListener", eventType, event)
    //   )
    // }
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
    if (this.props.args.server_sync_strategy === "client_wins") {
      this.state.api.addEventListener(
        "cellValueChanged",
        (event: CellValueChangedEvent) => {
          console.warn(
            "server_sync_strategy is 'client_wins' and Data was edited on Grid. Ignoring further changes from Streamlit server."
          )

          let editedRows = new Set(this.state.editedRows).add(event.node.id)
          this.setState({ isRowDataEdited: true, editedRows: editedRows })
        }
      )
    }

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
    let manualUpdate = this.props.args.manual_update === true

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
            this.state.api?.setGridOption("quickFilterText", value)
            this.state.api?.hideOverlay() // Hide any overlay if present
          }}
          onDownloadClick={() => {
            this.state.api?.exportDataAsCsv()
          }}
          onManualUpdateClick={() => {
            if (this.state.debug) {
              console.log("Manual update triggered")
            }
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
