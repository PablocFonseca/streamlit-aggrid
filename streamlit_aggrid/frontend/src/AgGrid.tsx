import { AgGridReact } from "ag-grid-react"
import React, { useState, useRef, useEffect, useCallback, useMemo } from "react"
import ReactDOM from "react-dom/client"
import type { Root } from "react-dom/client"

import { Component, ComponentArgs } from '@streamlit/component-v2-lib'

import {
  AllCommunityModule,
  CellValueChangedEvent,
  DetailGridInfo,
  GetRowIdParams,
  GridApi,
  GridReadyEvent,
  ModuleRegistry,
  ColumnState,
  GridState,
  DateEditorModule,
  LargeTextEditorModule
} from "ag-grid-community"

import { AgChartsEnterpriseModule } from "ag-charts-enterprise"
import { AllEnterpriseModule, LicenseManager } from "ag-grid-enterprise"

import debounce from 'lodash/debounce'
import omit from 'lodash/omit'

import { ThemeParser } from "./ThemeParser"
import { CustomCollector, LegacyCollector, MinimalCollector } from "./collectors"
import type { CollectorContext } from "./collectors"

import "@fontsource/source-sans-pro"
import "./AgGrid.css"

import GridToolBar from "./components/GridToolBar"

import {
  getCSS,
  injectProScript,
  parseJsCodeFromPython,
} from "./utils/gridUtils"

import { parseGridOptions, parseData } from "./utils/parsers"

type CSSDict = { [key: string]: { [key: string]: string } }

type stAggridStateShape = {
  gridState: GridState,
  grid_response: any
}

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

type AgGridProps = Pick<
  ComponentArgs<stAggridStateShape, AgGridData>,
  "setStateValue"
> &
  AgGridData;

type ProReturnHandler = (
  eventData: any,
  streamlitRerunEventTriggerName: string
) => Promise<void>

type ProReturnRegistration = {
  handler: ProReturnHandler
  ownsApi: (api: GridApi) => boolean
}

type ProReturnRegistry = {
  originalHandler: any
  dispatcher: (...args: any[]) => any
  registrations: Map<symbol, ProReturnRegistration>
}

const proReturnRegistries = new WeakMap<object, ProReturnRegistry>()

/**
 * StreamlitAgGridPro exposes one historical global return hook. Keep that API,
 * but dispatch events carrying an AG Grid API to the component that owns it.
 * Calls without an API preserve the old last-registered-grid behaviour.
 */
const registerProReturnHandler = (
  target: Record<string, any>,
  owner: symbol,
  registration: ProReturnRegistration
): (() => void) => {
  let registry = proReturnRegistries.get(target)

  if (!registry) {
    const registrations = new Map<symbol, ProReturnRegistration>()
    const originalHandler = target.returnGridValue
    const dispatcher = (...args: any[]) => {
      const activeRegistry = proReturnRegistries.get(target)
      if (!activeRegistry) {
        return typeof originalHandler === "function"
          ? originalHandler.apply(target, args)
          : undefined
      }

      const entries = Array.from(activeRegistry.registrations.values())
      const eventApi = args[0]?.api
      let matched: ProReturnRegistration | undefined
      if (eventApi) {
        for (let index = entries.length - 1; index >= 0; index--) {
          if (entries[index].ownsApi(eventApi)) {
            matched = entries[index]
            break
          }
        }
      }
      const active = matched || entries[entries.length - 1]

      if (active) return active.handler(args[0], args[1])
      return typeof activeRegistry.originalHandler === "function"
        ? activeRegistry.originalHandler.apply(target, args)
        : undefined
    }

    registry = { originalHandler, dispatcher, registrations }
    proReturnRegistries.set(target, registry)
  }

  registry.registrations.set(owner, registration)
  target.returnGridValue = registry.dispatcher

  return () => {
    const activeRegistry = proReturnRegistries.get(target)
    if (!activeRegistry) return

    activeRegistry.registrations.delete(owner)
    if (activeRegistry.registrations.size > 0) return

    if (target.returnGridValue === activeRegistry.dispatcher) {
      target.returnGridValue = activeRegistry.originalHandler
    }
    proReturnRegistries.delete(target)
  }
}


export default (componentArgs: ComponentArgs<stAggridStateShape, AgGridData>) : Component<stAggridStateShape, AgGridProps> => {
  const { parentElement, ...restArgs } = componentArgs
  
  let reactRoot = reactRoots.get(parentElement)
  if (!reactRoot) {
    reactRoot = ReactDOM.createRoot(parentElement)
    reactRoots.set(parentElement, reactRoot)
  }

  reactRoot.render(

      <AgGrid parentElement={parentElement} {...omit(restArgs, 'key')}/>

  )

  return () => {
    const root = reactRoots.get(parentElement)
    if (root) {
      root.unmount()
      reactRoots.delete(parentElement)
    }
  }
}


const AgGrid: React.FC<AgGridProps> = (props) => {

  // Refs (non-reactive values)
  const gridContainerRef = useRef<HTMLDivElement>(null)
  const renderedGridHeightPrevious = useRef(0)
  const themeParserRef = useRef<ThemeParser>(new ThemeParser())
  const shouldGridReturnRef = useRef<Function | undefined>(
    props.data?.should_grid_return
      ? parseJsCodeFromPython(props.data.should_grid_return)
      : undefined
  )
  const collectGridReturnRef = useRef<Function | undefined>(
    props.data?.custom_jscode_for_grid_return
      ? parseJsCodeFromPython(props.data.custom_jscode_for_grid_return)
      : undefined
  )
  const modulesRegisteredRef = useRef(false)
  const isMountedRef = useRef(true)
  const returnSequenceRef = useRef(0)
  const eventListenerCleanupsRef = useRef<Map<GridApi, Array<() => void>>>(new Map())
  const gridLifecycleCleanupRef = useRef<(() => void) | undefined>(undefined)
  const proReturnOwnerRef = useRef(Symbol("streamlit-aggrid-instance"))
  const returnGridValueRef = useRef<
    (eventData: any, streamlitRerunEventTriggerName: string) => Promise<void>
  >(async () => undefined)


  // Initial grid options (stable reference, updates handled via AG Grid API)
  const gridOptionsRef = useRef<any>()

  if (!gridOptionsRef.current) {
    // Initialize once on first render
    if (!props.data) {
      gridOptionsRef.current = {}
    } else {
      const go = parseGridOptions(
        props.data.gridOptions,
        props.data.allow_unsafe_jscode,
        props.data.theme
      )
      go.rowData = parseData(props.data.data, props.data.gridOptions?.rowData)

      // Auto-generate getRowId if not provided and data has unique IDs
      if (!("getRowId" in go) && go.rowData?.[0]?.["::auto_unique_id::"]) {
        go.getRowId = (params: GetRowIdParams) => params.data["::auto_unique_id::"]
      }

      gridOptionsRef.current = go
    }
  }

  const gridOptions = gridOptionsRef.current

  // Register AG Grid modules (must run before render)
  if (!modulesRegisteredRef.current) {
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
      ModuleRegistry.registerModules([AllCommunityModule, DateEditorModule, LargeTextEditorModule])
    }

    modulesRegisteredRef.current = true
  }

  // State

  const [editedRows, setEditedRows] = useState<Set<any>>(new Set())
  const [isMaximized, setIsMaximized] = useState(false)
  const [savedColumnState, setSavedColumnState] = useState<ColumnState[] | undefined>()
  const [dataHash, setDataHash] = useState(props.data?.data_hash)
  const apiRef = useRef<GridApi | undefined>(undefined)

  // Derived values
  const debug = props.data?.debug || false
  const enterprise_features_enabled = props.data?.enable_enterprise_modules || false
  const isRowDataEdited = editedRows.size > 0
  const proAssets = props.data?.pro_assets || []
  const proAssetsSignature = JSON.stringify(proAssets)
  const updateOnSignature = JSON.stringify(props.data?.update_on || [])
  const updateOn = useMemo(
    () => props.data?.update_on || [],
    [updateOnSignature]
  )


  // Initialization diagnostics
  useEffect(() => {
    if (debug) {
      console.log("***Received Props", props)
      console.log("*** Processed Initial State", {
        gridOptions: gridOptionsRef.current,
        editedRows,
        isMaximized,
        savedColumnState,
        dataHash,
      })
    }
  }, [debug])

  // Keep user-provided JavaScript hooks current across Streamlit rerenders.
  useEffect(() => {
    shouldGridReturnRef.current = props.data?.should_grid_return
      ? parseJsCodeFromPython(props.data.should_grid_return)
      : undefined
    collectGridReturnRef.current = props.data?.custom_jscode_for_grid_return
      ? parseJsCodeFromPython(props.data.custom_jscode_for_grid_return)
      : undefined
  }, [
    props.data?.should_grid_return,
    props.data?.custom_jscode_for_grid_return,
  ])

  // Extension scripts must live in the document, but their DOM nodes should
  // not accumulate as Components V2 mounts and unmounts component instances.
  useEffect(() => {
    const cleanups = proAssets.map((asset: any) => injectProScript(asset?.js))

    const StreamlitAgGridPro = (window as any)?.StreamlitAgGridPro
    StreamlitAgGridPro?.extenders?.forEach((extender: Function) =>
      extender(gridOptionsRef.current)
    )

    return () => cleanups.forEach((cleanup: () => void) => cleanup())
  }, [proAssetsSignature])

  // Prevent Streamlit keyboard shortcuts from interfering with grid
  // Block specific Streamlit shortcuts while allowing AG Grid to handle its own keys
  useEffect(() => {
    const container = gridContainerRef.current
    if (!container) return

    // Streamlit keyboard shortcuts that we need to block
    const streamlitShortcuts = new Set(['r', 'c'])

    const stopStreamlitShortcuts = (e: KeyboardEvent) => {
      // Only block single-key shortcuts without modifiers (Ctrl/Cmd/Alt)
      if (!e.ctrlKey && !e.metaKey && !e.altKey && streamlitShortcuts.has(e.key.toLowerCase())) {
        e.stopPropagation()
      }
    }

    container.addEventListener('keydown', stopStreamlitShortcuts, true)

    return () => {
      container.removeEventListener('keydown', stopStreamlitShortcuts, true)
    }
  }, []) 

  // Effect 1: Handle gridOptions changes (excluding rowData and theme)
  useEffect(() => {
    if (!props.data?.gridOptions || !apiRef.current) return

    debug && console.log("********** GridOptions updated")

    const newOptions = parseGridOptions(
      props.data.gridOptions,
      props.data.allow_unsafe_jscode,
      props.data.theme
    )

    // Remove rowData and theme as they're handled in separate effects
    const optionsToUpdate = omit(newOptions, ["rowData", "theme"])

    apiRef.current.updateGridOptions(optionsToUpdate)
  }, [props.data?.gridOptions])

  // Effect 2: Handle theme changes
  useEffect(() => {
    if (!apiRef.current) return

    debug && console.log("********** Theme updated")

    apiRef.current.updateGridOptions({
      theme: themeParserRef.current?.parse(props.data?.theme, props.theme),
    })
  }, [props.data?.theme])

  // Effect 3: Handle data sync (rowData updates)
  useEffect(() => {
    if (!props.data || !apiRef.current) return

    const serverSyncStrategy = props.data.server_sync_strategy

    debug && console.log(`********** Data sync (${serverSyncStrategy})`, {
      dataHash,
      newHash: props.data.data_hash,
      isRowDataEdited
    })

    if (serverSyncStrategy === "client_wins") {
      if (!isRowDataEdited && props.data.data_hash !== dataHash) {
        apiRef.current.updateGridOptions({
          rowData: parseData(props.data.data, props.data.gridOptions?.rowData) || []
        })
        setDataHash(props.data.data_hash)
      }
    } else if (serverSyncStrategy === "server_wins") {
      apiRef.current.stopEditing(true)
      apiRef.current.updateGridOptions({
        rowData: parseData(props.data.data, props.data.gridOptions?.rowData) || []
      })
    }
  }, [props.data?.data_hash, props.data?.server_sync_strategy, props.data?.data, props.data?.gridOptions?.rowData, isRowDataEdited, dataHash, debug])

  // Effect 4: Handle column state changes
  useEffect(() => {
    if (!apiRef.current || !props.data?.columns_state) return

    debug && console.log("********** Column state updated")

    apiRef.current.applyColumnState({
      state: props.data.columns_state,
      applyOrder: true
    })
  }, [props.data?.columns_state, debug])

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

    try {
      // Avoid expensive full-grid collection for intermediate events that the
      // user has explicitly chosen not to return.
      if (shouldGridReturnRef.current?.({ streamlitRerunEventTriggerName, eventData }) === false) {
        debug && console.log(`shouldGridReturn blocked return for event: ${streamlitRerunEventTriggerName}`)
        return
      }
    } catch (error) {
      console.error("Error evaluating should_grid_return:", error)
      return
    }

    const returnSequence = ++returnSequenceRef.current
    const context: CollectorContext = {
      state: { gridOptions: gridOptionsRef.current, isRowDataEdited, api: apiRef.current, enterprise_features_enabled, debug, editedRows, isMaximized, savedColumnState, gridHeight: props.data?.height || 400 },
      props: {data: props.data},
      eventData,
      streamlitRerunEventTriggerName,
    }

    const customCollectorFunction = collectGridReturnRef.current
    const legacyCollector = new LegacyCollector()
    const collectors = {
      AS_INPUT: legacyCollector,
      FILTERED: legacyCollector,
      FILTERED_AND_SORTED: legacyCollector,
      MINIMAL: new MinimalCollector(),
      CUSTOM: customCollectorFunction
        ? new CustomCollector(customCollectorFunction)
        : undefined,
    }
    const returnMode = (props.data?.data_return_mode || "AS_INPUT") as keyof typeof collectors
    if (returnMode === "CUSTOM" && !collectors.CUSTOM) {
      console.error(
        "CUSTOM data_return_mode requires custom_jscode_for_grid_return. Grid response was not sent."
      )
      return
    }

    try {
      const collector = collectors[returnMode] || collectors.AS_INPUT
      const result = await collector.processResponse(context)

      if (result.success) {
        debug && console.log(`Grid response processed by ${collector.getCollectorType()}:`, result.data)

        // An asynchronous custom collector may finish after a newer event. Do
        // not let the stale response overwrite the latest grid state.
        if (!isMountedRef.current || returnSequence !== returnSequenceRef.current) {
          debug && console.log(`Discarded stale grid response for event: ${streamlitRerunEventTriggerName}`)
          return
        }

        props.setStateValue("grid_response", result.data)
      } else {
        console.error(`Collector processing failed: ${result.error}`)
      }
    } catch (error) {
      console.error("Error in returnGridValue collector processing:", error)
    }
  }, [debug, props, isRowDataEdited, enterprise_features_enabled, editedRows, isMaximized, savedColumnState])

  returnGridValueRef.current = returnGridValue

  const detachConfiguredGridEvents = useCallback((gridApi: GridApi) => {
    const cleanups = eventListenerCleanupsRef.current.get(gridApi)
    cleanups?.forEach((cleanup) => cleanup())
    eventListenerCleanupsRef.current.delete(gridApi)
  }, [])

  const clearConfiguredGridEvents = useCallback(() => {
    eventListenerCleanupsRef.current.forEach((cleanups) =>
      cleanups.forEach((cleanup) => cleanup())
    )
    eventListenerCleanupsRef.current.clear()
  }, [])

  const attachStreamlitRerunToEvents = useCallback((gridApi: GridApi): Array<() => void> => {
    const cleanups: Array<() => void> = []

    updateOn.forEach((element: any) => {
      const [eventName, timeout] = Array.isArray(element) ? element : [element, 0]
      if (typeof eventName !== "string" || eventName.length === 0) return

      const debounceTimeout = Number(timeout)
      const invoke = (event: any) => {
        void returnGridValueRef.current(event, eventName)
      }
      const handler = Number.isFinite(debounceTimeout) && debounceTimeout > 0
        ? debounce(invoke, debounceTimeout, {
            leading: false,
            trailing: true,
            maxWait: debounceTimeout,
          })
        : invoke

      // update_on is intentionally extensible, including enterprise events
      // not present in the community GridApi event type union.
      gridApi.addEventListener(eventName as any, handler as any)
      cleanups.push(() => {
        gridApi.removeEventListener(eventName as any, handler as any)
        const cancel = (handler as { cancel?: () => void }).cancel
        if (typeof cancel === "function") {
          cancel()
        }
      })
      debug && console.log(`Attached grid return event: ${eventName}${debounceTimeout > 0 ? ` (debounced ${debounceTimeout}ms)` : ''}`)
    })

    return cleanups
  }, [updateOn, debug])

  const attachConfiguredGridEvents = useCallback((gridApi: GridApi) => {
    if (eventListenerCleanupsRef.current.has(gridApi)) return
    eventListenerCleanupsRef.current.set(
      gridApi,
      attachStreamlitRerunToEvents(gridApi)
    )
  }, [attachStreamlitRerunToEvents])

  const syncDetailGridEvents = useCallback((masterGridApi: GridApi) => {
    const liveApis = new Set<GridApi>([masterGridApi])

    if (enterprise_features_enabled) {
      masterGridApi.forEachDetailGridInfo((info: DetailGridInfo) => {
        if (!info.api) return
        liveApis.add(info.api)
        attachConfiguredGridEvents(info.api)
      })
    }

    for (const configuredApi of eventListenerCleanupsRef.current.keys()) {
      if (!liveApis.has(configuredApi)) detachConfiguredGridEvents(configuredApi)
    }
  }, [
    attachConfiguredGridEvents,
    detachConfiguredGridEvents,
    enterprise_features_enabled,
  ])

  const syncDetailGridEventsRef = useRef(syncDetailGridEvents)
  syncDetailGridEventsRef.current = syncDetailGridEvents

  const bindConfiguredGridEvents = useCallback((gridApi: GridApi) => {
    clearConfiguredGridEvents()
    attachConfiguredGridEvents(gridApi)
    syncDetailGridEvents(gridApi)
  }, [
    attachConfiguredGridEvents,
    clearConfiguredGridEvents,
    syncDetailGridEvents,
  ])

  useEffect(() => {
    if (apiRef.current) bindConfiguredGridEvents(apiRef.current)
    return clearConfiguredGridEvents
  }, [bindConfiguredGridEvents, clearConfiguredGridEvents])

  const proReturnHandler = useCallback<ProReturnHandler>(
    (eventData, streamlitRerunEventTriggerName) =>
      returnGridValueRef.current(eventData, streamlitRerunEventTriggerName),
    []
  )

  // StreamlitAgGridPro historically calls one global hook. The registry keeps
  // that public hook while routing API-bearing events to the owning grid.
  useEffect(() => {
    const StreamlitAgGridPro = (window as any)?.StreamlitAgGridPro
    if (!StreamlitAgGridPro) return

    return registerProReturnHandler(
      StreamlitAgGridPro,
      proReturnOwnerRef.current,
      {
        handler: proReturnHandler,
        ownsApi: (api) =>
          apiRef.current === api || eventListenerCleanupsRef.current.has(api),
      }
    )
  }, [proAssetsSignature, proReturnHandler])

  const toggleMaximize = useCallback(() => {
    setIsMaximized(prev => {
      if (!prev) {
        setSavedColumnState(apiRef.current?.getColumnState())
        setTimeout(() => apiRef.current?.sizeColumnsToFit(), 0)
      } else if (savedColumnState) {
        setTimeout(() => apiRef.current?.applyColumnState({ state: savedColumnState, applyOrder: true }), 0)
      }
      return !prev
    })
  }, [savedColumnState])

  const onGridReady = useCallback((event: GridReadyEvent) => {
    apiRef.current = event.api
    gridLifecycleCleanupRef.current?.()

    // Attach resize listeners
    event.api.addEventListener("rowGroupOpened", resizeGridContainer)
    event.api.addEventListener("firstDataRendered", resizeGridContainer)
    event.api.addEventListener("gridSizeChanged", resizeGridContainer)

    let detailSyncTimeout: number | undefined
    let detailSyncFrame: number | undefined
    const runDetailGridSync = () => {
      if (!event.api.isDestroyed()) {
        syncDetailGridEventsRef.current(event.api)
      }
    }
    const scheduleDetailGridSync = () => {
      if (detailSyncTimeout !== undefined) window.clearTimeout(detailSyncTimeout)
      if (detailSyncFrame !== undefined) window.cancelAnimationFrame(detailSyncFrame)
      detailSyncTimeout = window.setTimeout(runDetailGridSync, 0)
      detailSyncFrame = window.requestAnimationFrame(runDetailGridSync)
    }

    // Detail grids register with the master just after expansion/rendering.
    // Scan after those lifecycle events so newly created and removed detail
    // APIs receive the same configured Streamlit listeners as the master.
    event.api.addEventListener("rowGroupOpened", scheduleDetailGridSync)
    event.api.addEventListener("modelUpdated", scheduleDetailGridSync)
    event.api.addEventListener("firstDataRendered", scheduleDetailGridSync)

    // Handle client_wins strategy
    let onClientValueChanged: ((event: CellValueChangedEvent) => void) | undefined
    if (props.data?.server_sync_strategy === "client_wins") {
      onClientValueChanged = (e: CellValueChangedEvent) => {
        console.warn("server_sync_strategy is 'client_wins' - Data edited on Grid. Ignoring server updates.")
        setEditedRows(prev => new Set(prev).add(e.node.id))
      }
      event.api.addEventListener("cellValueChanged", onClientValueChanged)
    }

    bindConfiguredGridEvents(event.api)
    scheduleDetailGridSync()

    gridLifecycleCleanupRef.current = () => {
      event.api.removeEventListener("rowGroupOpened", resizeGridContainer)
      event.api.removeEventListener("firstDataRendered", resizeGridContainer)
      event.api.removeEventListener("gridSizeChanged", resizeGridContainer)
      event.api.removeEventListener("rowGroupOpened", scheduleDetailGridSync)
      event.api.removeEventListener("modelUpdated", scheduleDetailGridSync)
      event.api.removeEventListener("firstDataRendered", scheduleDetailGridSync)
      if (detailSyncTimeout !== undefined) window.clearTimeout(detailSyncTimeout)
      if (detailSyncFrame !== undefined) window.cancelAnimationFrame(detailSyncFrame)
      if (onClientValueChanged) {
        event.api.removeEventListener("cellValueChanged", onClientValueChanged)
      }
    }

    // Call user's onGridReady if provided
    gridOptionsRef.current?.onGridReady?.(event)
  }, [props.data?.server_sync_strategy, bindConfiguredGridEvents, resizeGridContainer])

  useEffect(() => {
    isMountedRef.current = true
    return () => {
      isMountedRef.current = false
      returnSequenceRef.current += 1
      clearConfiguredGridEvents()
      gridLifecycleCleanupRef.current?.()
      gridLifecycleCleanupRef.current = undefined
      apiRef.current = undefined
    }
  }, [clearConfiguredGridEvents])

  const defineContainerHeight = useMemo(() => {
    if (isMaximized) {
      return {
        width: '100vw',
        height: '100vh',
      }
    } else if (props.data?.gridOptions?.domLayout === "autoHeight") {
      return {
        width: props.width,
      }
    } else {
      return {
        width: props.width,
        height: props.data?.height || 400,
      }
    }
  }, [isMaximized, props.width, props.data?.height, props.data?.gridOptions?.domLayout])

  const manualUpdate = props.data?.manual_update === true
  const showToolbar = props.data?.show_toolbar === true
  const customCss = props.data?.custom_css
    ? getCSS(props.data.custom_css)
    : ""
  const proCss = proAssets
    .map((asset: any) => asset?.css)
    .filter((css: unknown): css is string => typeof css === "string")
    .join("\n")
  const componentCss = [customCss, proCss].filter(Boolean).join("\n")

  return (
    <div
      id="gridContainer"
      ref={gridContainerRef}
      className={isMaximized ? 'maximized' : ''}
      style={defineContainerHeight}
    >
      {componentCss && (
        <style data-streamlit-aggrid-custom-css>{componentCss}</style>
      )}
      <GridToolBar
        showManualUpdateButton={manualUpdate}
        enabled={showToolbar || manualUpdate}
        showFullscreenButton={showToolbar}
        showSearch={showToolbar && (props.data?.show_search ?? true)}
        showDownloadButton={showToolbar && (props.data?.show_download_button ?? true)}
        isMaximized={isMaximized}
        onMaximizeToggle={toggleMaximize}
        onQuickSearchChange={(value) => {
          apiRef.current?.setGridOption("quickFilterText", value)
          apiRef.current?.hideOverlay()
        }}
        onDownloadClick={() => {
          apiRef.current?.exportDataAsCsv()
        }}
        onManualUpdateClick={() => {
          debug && console.log("Manual update triggered")
          returnGridValue({ api: apiRef.current }, "manualUpdate")
        }}
      />
      <AgGridReact
        onGridReady={onGridReady}
        gridOptions={gridOptions}
      ></AgGridReact>
    </div>
  )
}

const reactRoots: WeakMap<ComponentArgs<any, AgGridData>["parentElement"], Root> = new WeakMap()
