import { AgGridReact } from "ag-grid-react"
import React, { useState, useRef, useEffect, useCallback, useMemo } from "react"
import ReactDOM from "react-dom/client"
import type { Root } from "react-dom/client"

import { ComponentArgs } from '@streamlit/component-v2-lib'

import {
  AllCommunityModule,
  CellValueChangedEvent,
  DetailGridInfo,
  GetRowIdParams,
  GridApi,
  GridReadyEvent,
  ModuleRegistry,
  ColumnState,
} from "ag-grid-community"

import { AgChartsEnterpriseModule } from "ag-charts-enterprise"
import { AllEnterpriseModule, LicenseManager } from "ag-grid-enterprise"

import debounce from 'lodash/debounce'
import isEqual from 'lodash/isEqual'
import omit from 'lodash/omit'

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

import { parseGridOptions, parseData } from "./utils/parsers"

type CSSDict = { [key: string]: { [key: string]: string } }

const reactRoots: WeakMap<ComponentArgs<any, AgGridData>["parentElement"], Root> = new WeakMap()

interface AgGridData {
  custom_css?: CSSDict
  pro_assets?: any[]
  enable_enterprise_modules?: any
  license_key?: string
  gridOptions?: any
  height?: number
  update_on?: any[]
  data_return_mode?: string
  debug?: boolean
  theme?: any
  data_hash?: string
  server_sync_strategy?: string
  columns_state?: any
  manual_update?: boolean
  show_toolbar?: boolean
  show_search?: boolean
  show_download_button?: boolean
  should_grid_return?: any
  custom_jscode_for_grid_return?: any
  [key: string]: any
}

interface AgGridProps {
  parentElement: HTMLElement | ShadowRoot
  setStateValue: (key: string, value: any) => void
  data?: AgGridData
  width?: number
  theme?: any
}

const AgGrid: React.FC<AgGridProps> = (props) => {

  // Register AG Grid modules
  const enableEnterpriseModules = props.data?.enable_enterprise_modules
  if (enableEnterpriseModules === "enterprise+AgCharts") {
    ModuleRegistry.registerModules([
      AllEnterpriseModule.with(AgChartsEnterpriseModule),
    ])
    if (props.data?.license_key) {
      LicenseManager.setLicenseKey(props.data.license_key)
    }
  } else if (
    enableEnterpriseModules === true ||
    enableEnterpriseModules === "enterpriseOnly"
  ) {
    ModuleRegistry.registerModules([AllEnterpriseModule])
    if (props.data?.license_key) {
      LicenseManager.setLicenseKey(props.data.license_key)
    }
  } else {
    ModuleRegistry.registerModules([AllCommunityModule])
  }


  // Refs (non-reactive values)
  const gridContainerRef = useRef<HTMLDivElement>(null)
  const renderedGridHeightPrevious = useRef(0)
  const themeParserRef = useRef<ThemeParser>(new ThemeParser())
  const shouldGridReturnRef = useRef<Function | undefined>(undefined)
  const collectGridReturnRef = useRef<Function | undefined>(undefined)
  const isGridAutoHeightOnRef = useRef(false)

  // State
  const [gridOptions, setGridOptions] = useState<any>(() => {
    const go = parseGridOptions(props.data || {})
    go.rowData = parseData(props.data || {})

    // Auto-generate getRowId if not provided and data has unique IDs
    if (!("getRowId" in go) && go.rowData?.[0]?.["::auto_unique_id::"]) {
      go.getRowId = (params: GetRowIdParams) => params.data["::auto_unique_id::"]
    }

    return go
  })

  const [editedRows, setEditedRows] = useState<Set<any>>(new Set())
  const [isMaximized, setIsMaximized] = useState(false)
  const [savedColumnState, setSavedColumnState] = useState<ColumnState[] | undefined>()
  const [dataHash, setDataHash] = useState(props.data?.data_hash)
  const [api, setApi] = useState<GridApi | undefined>()

  // Derived values
  const debug = props.data?.debug || false
  const enterprise_features_enabled = props.data?.enable_enterprise_modules || false
  const isRowDataEdited = editedRows.size > 0

  // One-time initialization
  useEffect(() => {
    if (debug) {
      console.log("***Received Props", props)
      console.log("*** Processed Initial State", {
        gridOptions,
        editedRows,
        isMaximized,
        savedColumnState,
        dataHash,
        api,
      })
    }

    // Handle custom CSS
    props.data?.custom_css && addCustomCSS(props.data.custom_css)

    // Handle pro assets
    props.data?.pro_assets?.forEach((asset: any) => injectProAssets(asset?.js, asset?.css))

    // Handle StreamlitAgGridPro extension
    const StreamlitAgGridPro = (window as any)?.StreamlitAgGridPro
    if (StreamlitAgGridPro) {
      StreamlitAgGridPro.returnGridValue = returnGridValue
      StreamlitAgGridPro.extenders?.forEach((extender: Function) => extender(gridOptions))
    }

    isGridAutoHeightOnRef.current = props.data?.gridOptions?.domLayout === "autoHeight"
    shouldGridReturnRef.current = props.data?.should_grid_return
      ? parseJsCodeFromPython(props.data.should_grid_return)
      : undefined
    collectGridReturnRef.current = props.data?.custom_jscode_for_grid_return
      ? parseJsCodeFromPython(props.data.custom_jscode_for_grid_return)
      : undefined
  }, []) // Only run once on mount

  // Handle prop updates
  useEffect(() => {
    if (!props.data) return

    debug && console.log("********** Props updated", props)

    // Update grid options if changed (excluding rowData)
    const prevGridOptions = omit(gridOptions, "rowData")
    const currGridOptions = omit(props.data.gridOptions, "rowData")
    if (!isEqual(prevGridOptions, currGridOptions)) {
      api?.updateGridOptions(parseGridOptions(props.data))
    }

    // Update theme if changed
    if (!isEqual(props.theme, themeParserRef.current) || !isEqual(props.data.theme, gridOptions?.theme)) {
      api?.updateGridOptions({
        theme: themeParserRef.current?.parse(props.data.theme, props.theme),
      })
    }

    // Handle data sync strategy
    const serverSyncStrategy = props.data.server_sync_strategy
    if (serverSyncStrategy === "client_wins" && !isRowDataEdited && props.data.data_hash !== dataHash) {
      api?.updateGridOptions({ rowData: parseData(props.data) || [] })
      setDataHash(props.data.data_hash)
    } else if (serverSyncStrategy === "server_wins") {
      api?.stopEditing(true)
      api?.updateGridOptions({ rowData: parseData(props.data) || [] })
    }

    // Update column state if changed
    if (!isEqual(gridOptions?.columnState, props.data.columns_state) && props.data.columns_state) {
      api?.applyColumnState({ state: props.data.columns_state, applyOrder: true })
    }
  }, [props.data, props.theme, api, dataHash, isRowDataEdited, gridOptions, debug])

  const resizeGridContainer = useCallback(() => {
    const renderedGridHeight = gridContainerRef.current?.clientHeight
    if (
      renderedGridHeight &&
      renderedGridHeight > 0 &&
      renderedGridHeight !== renderedGridHeightPrevious.current
    ) {
      renderedGridHeightPrevious.current = renderedGridHeight
      if (props.parentElement instanceof HTMLElement) {
        props.parentElement.style.height = `${renderedGridHeight}px`
      }
    }
  }, [props.parentElement])

  const returnGridValue = useCallback(async (eventData: any, streamlitRerunEventTriggerName: string) => {
    if (debug) {
      console.log(`Refreshing grid from ${streamlitRerunEventTriggerName}, mode: ${props.data?.data_return_mode}`)
    }

    const context: CollectorContext = {
      state: { gridOptions, isRowDataEdited, api, enterprise_features_enabled, debug, editedRows, isMaximized, savedColumnState, gridHeight: props.data?.height || 400 },
      props,
      eventData,
      streamlitRerunEventTriggerName,
    }

    const collectors = {
      AS_INPUT: new LegacyCollector(),
      FILTERED: new LegacyCollector(),
      FILTERED_AND_SORTED: new LegacyCollector(),
      MINIMAL: new LegacyCollector(),
      CUSTOM: new CustomCollector(collectGridReturnRef.current || (() => {})),
    }

    try {
      const collector = collectors[props.data?.data_return_mode as keyof typeof collectors || 'AS_INPUT']
      const result = await collector.processResponse(context)

      if (result.success) {
        debug && console.log(`Grid response processed by ${collector.getCollectorType()}:`, result.data)

        if (shouldGridReturnRef.current?.({ streamlitRerunEventTriggerName, eventData }) === false) {
          debug && console.log(`shouldGridReturn blocked return for event: ${streamlitRerunEventTriggerName}`)
          return
        }

        props.setStateValue("grid_response", result.data)
      } else {
        console.error(`Collector processing failed: ${result.error}`)
      }
    } catch (error) {
      console.error("Error in returnGridValue collector processing:", error)
    }
  }, [debug, props, gridOptions, isRowDataEdited, api, enterprise_features_enabled, editedRows, isMaximized, savedColumnState])

  const attachStreamlitRerunToEvents = useCallback((gridApi: GridApi) => {
    props.data?.update_on?.forEach((element: any) => {
      const [eventName, timeout] = Array.isArray(element) ? element : [element, 0]
      const handler = timeout > 0
        ? debounce((e: any) => returnGridValue(e, eventName), timeout, { leading: false, trailing: true, maxWait: timeout })
        : (e: any) => returnGridValue(e, eventName)

      gridApi.addEventListener(eventName, handler)
      debug && console.log(`Attached grid return event: ${eventName}${timeout ? ` (debounced ${timeout}ms)` : ''}`)
    })
  }, [props.data?.update_on, debug, returnGridValue])

  const toggleMaximize = useCallback(() => {
    setIsMaximized(prev => {
      if (!prev) {
        setSavedColumnState(api?.getColumnState())
        setTimeout(() => api?.sizeColumnsToFit(), 0)
      } else if (savedColumnState) {
        setTimeout(() => api?.applyColumnState({ state: savedColumnState, applyOrder: true }), 0)
      }
      return !prev
    })
  }, [api, savedColumnState])

  const onGridReady = useCallback((event: GridReadyEvent) => {
    setApi(event.api)

    // Attach resize listeners
    event.api.addEventListener("rowGroupOpened", resizeGridContainer)
    event.api.addEventListener("firstDataRendered", resizeGridContainer)
    event.api.addEventListener("gridSizeChanged", resizeGridContainer)

    // Handle client_wins strategy
    if (props.data?.server_sync_strategy === "client_wins") {
      event.api.addEventListener("cellValueChanged", (e: CellValueChangedEvent) => {
        console.warn("server_sync_strategy is 'client_wins' - Data edited on Grid. Ignoring server updates.")
        setEditedRows(prev => new Set(prev).add(e.node.id))
      })
    }

    // Attach custom events
    attachStreamlitRerunToEvents(event.api)

    // Attach events to detail grids (enterprise)
    enterprise_features_enabled && event.api.forEachDetailGridInfo((i: DetailGridInfo) =>
      i.api && attachStreamlitRerunToEvents(i.api)
    )

    // Call user's onGridReady if provided
    gridOptions.onGridReady?.(event)
  }, [props.data?.server_sync_strategy, enterprise_features_enabled, gridOptions, attachStreamlitRerunToEvents, resizeGridContainer])

  const defineContainerHeight = useMemo(() => {
    if (isMaximized) {
      return {
        width: '100vw',
        height: '100vh',
      }
    } else if (isGridAutoHeightOnRef.current) {
      return {
        width: props.width,
      }
    } else {
      return {
        width: props.width,
        height: props.data?.height || 400,
      }
    }
  }, [isMaximized, props.width, props.data?.height])

  const manualUpdate = props.data?.manual_update === true

  return (
    <div
      id="gridContainer"
      ref={gridContainerRef}
      className={isMaximized ? 'maximized' : ''}
      style={defineContainerHeight}
    >
      <GridToolBar
        gridContainerRef={gridContainerRef}
        showManualUpdateButton={manualUpdate}
        enabled={props.data?.show_toolbar ?? true}
        showSearch={props.data?.show_search ?? true}
        showDownloadButton={props.data?.show_download_button ?? true}
        isMaximized={isMaximized}
        onMaximizeToggle={toggleMaximize}
        onQuickSearchChange={(value) => {
          api?.setGridOption("quickFilterText", value)
          api?.hideOverlay()
        }}
        onDownloadClick={() => {
          api?.exportDataAsCsv()
        }}
        onManualUpdateClick={() => {
          if (debug) {
            console.log("Manual update triggered")
          }
        }}
      />
      <AgGridReact
        onGridReady={onGridReady}
        gridOptions={gridOptions}
      ></AgGridReact>
    </div>
  )
}

export default (componentArgs: ComponentArgs<any, AgGridData>) => {
  const { parentElement, ...restArgs } = componentArgs

  let reactRoot = reactRoots.get(parentElement)
  if (!reactRoot) {
    reactRoot = ReactDOM.createRoot(parentElement)
    reactRoots.set(parentElement, reactRoot)
  }

  reactRoot.render(
    <React.StrictMode>
      <AgGrid parentElement={parentElement} {...restArgs} />
    </React.StrictMode>
  )

  return () => {
    const root = reactRoots.get(parentElement)
    if (root) {
      root.unmount()
      reactRoots.delete(parentElement)
    }
  }
}
