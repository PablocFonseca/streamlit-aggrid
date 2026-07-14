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
  RowDragEndEvent,
  DateEditorModule,
  LargeTextEditorModule
} from "ag-grid-community"

import { AgChartsEnterpriseModule } from "ag-charts-enterprise"
import { AllEnterpriseModule, LicenseManager } from "ag-grid-enterprise"

import debounce from 'lodash/debounce'
import cloneDeep from 'lodash/cloneDeep'
import isEqual from 'lodash/isEqual'
import omit from 'lodash/omit'

import { ThemeParser, type StAggridThemeOptions } from "./ThemeParser"
import { CustomCollector, LegacyCollector, MinimalCollector } from "./collectors"
import type { CollectorContext } from "./collectors"

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
  theme?: StAggridThemeOptions
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
  "data" | "parentElement" | "setStateValue"
> & {
  componentRenderSequence: number
}

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

type RowReconciliationResult = {
  rowData?: any[]
  reusedRows: number
  fallbackReason?: string
}

const normalizeForSignature = (
  value: unknown,
  ancestors: WeakSet<object> = new WeakSet()
): unknown => {
  if (value === undefined) return ["__streamlit_aggrid_undefined__"]
  if (typeof value === "bigint") return ["__streamlit_aggrid_bigint__", String(value)]
  if (typeof value === "function") {
    return ["__streamlit_aggrid_function__", String(value)]
  }
  if (typeof value === "symbol") {
    return ["__streamlit_aggrid_symbol__", String(value)]
  }
  if (value === null || typeof value !== "object") return value
  if (value instanceof Date) return ["__streamlit_aggrid_date__", value.toISOString()]
  if (ancestors.has(value)) return ["__streamlit_aggrid_circular__"]

  ancestors.add(value)
  try {
    if (Array.isArray(value)) {
      return value.map((entry) => normalizeForSignature(entry, ancestors))
    }

    const normalized: Record<string, unknown> = {}
    for (const key of Object.keys(value).sort()) {
      normalized[key] = normalizeForSignature(
        (value as Record<string, unknown>)[key],
        ancestors
      )
    }
    return normalized
  } finally {
    ancestors.delete(value)
  }
}

const stableSignature = (value: unknown): string =>
  JSON.stringify(normalizeForSignature(value))

const asGridOptionsObject = (rawGridOptions: unknown): Record<string, any> => {
  if (typeof rawGridOptions === "string") {
    try {
      const parsed = JSON.parse(rawGridOptions)
      return parsed && typeof parsed === "object" ? parsed : {}
    } catch {
      return {}
    }
  }
  return rawGridOptions && typeof rawGridOptions === "object"
    ? rawGridOptions as Record<string, any>
    : {}
}

// AG Grid 36 rejects these options when they are passed through
// api.updateGridOptions(). Keep this list in sync with
// ag-grid-community/dist/types/src/gridOptionsInitial.d.ts while v36 is pinned.
const INITIAL_ONLY_GRID_OPTION_KEYS = new Set([
  "enableBrowserTooltips",
  "tooltipTrigger",
  "tooltipMouseTrack",
  "tooltipShowMode",
  "tooltipInteraction",
  "defaultColGroupDef",
  "suppressAutoSize",
  "skipHeaderOnAutoSize",
  "autoSizeStrategy",
  "components",
  "stopEditingWhenCellsLoseFocus",
  "undoRedoCellEditing",
  "undoRedoCellEditingLimit",
  "excelStyles",
  "cacheQuickFilter",
  "customChartThemes",
  "chartThemeOverrides",
  "chartToolPanelsDef",
  "loadingCellRendererSelector",
  "localeText",
  "keepDetailRows",
  "keepDetailRowsCount",
  "detailRowHeight",
  "detailRowAutoHeight",
  "tabIndex",
  "valueCache",
  "valueCacheNeverExpires",
  "enableCellExpressions",
  "suppressTouch",
  "suppressBrowserResizeObserver",
  "suppressPropertyNamesCheck",
  "debug",
  "dragAndDropImageComponent",
  "overlayComponent",
  "suppressOverlays",
  "loadingOverlayComponent",
  "suppressLoadingOverlay",
  "noRowsOverlayComponent",
  "paginateChildRows",
  "pivotPanelShow",
  "pivotSuppressAutoColumn",
  "suppressExpandablePivotGroups",
  "aggFuncs",
  "allowShowChangeAfterFilter",
  "ensureDomOrder",
  "enableRtl",
  "suppressColumnVirtualisation",
  "suppressMaxRenderedRowRestriction",
  "suppressRowVirtualisation",
  "rowDragText",
  "groupLockGroupColumns",
  "suppressGroupRowsSticky",
  "rowModelType",
  "cacheOverflowSize",
  "infiniteInitialRowCount",
  "serverSideInitialRowCount",
  "maxBlocksInCache",
  "maxConcurrentDatasourceRequests",
  "blockLoadDebounceMillis",
  "serverSideOnlyRefreshFilteredGroups",
  "serverSidePivotResultFieldSeparator",
  "viewportRowModelPageSize",
  "viewportRowModelBufferSize",
  "debounceVerticalScrollbar",
  "suppressAnimationFrame",
  "suppressPreventDefaultOnMouseWheel",
  "scrollbarWidth",
  "icons",
  "suppressRowTransform",
  "suppressContentVisibilityAuto",
  "gridId",
  "enableGroupEdit",
  "initialState",
  "processUnpinnedColumns",
  "createChartContainer",
  "getLocaleText",
  "getRowId",
  "reactiveCustomComponents",
  "renderingMode",
  "columnMenu",
  "suppressSetFilterByDefault",
  "getDataPath",
  "enableCellSpan",
  "enableFilterHandlers",
  "filterHandlers",
])

const runtimeGridOptions = (
  gridOptions: Record<string, any>
): Record<string, any> => {
  const runtimeOptions: Record<string, any> = {}
  for (const [key, value] of Object.entries(gridOptions)) {
    if (
      key !== "rowData" &&
      key !== "theme" &&
      !INITIAL_ONLY_GRID_OPTION_KEYS.has(key)
    ) {
      runtimeOptions[key] = value
    }
  }
  return runtimeOptions
}

const initialOnlyGridOptionSignatures = (
  gridOptions: Record<string, any>
): Record<string, string> => {
  const signatures: Record<string, string> = {}
  for (const key of INITIAL_ONLY_GRID_OPTION_KEYS) {
    signatures[key] = stableSignature(gridOptions[key])
  }
  return signatures
}

/**
 * Preserve the existing data object for rows whose stable ID and values did
 * not change. Passing that mixed old/new array back through AG Grid's immutable
 * row-data path lets the grid update only changed rows while still applying
 * server additions, removals, and order.
 *
 * Invalid or duplicate IDs reject the update. Passing the incoming array to AG
 * Grid in that case would still run the same invalid getRowId callback through
 * its immutable-data path and could corrupt the row model.
 */
const reconcileServerRows = (
  api: GridApi,
  incomingRows: any[],
): RowReconciliationResult => {
  if (incomingRows.length === 0) {
    return { rowData: [], reusedRows: 0 }
  }

  const getRowId = api.getGridOption("getRowId")
  if (typeof getRowId !== "function") {
    return {
      reusedRows: 0,
      fallbackReason: "getRowId is not a function",
    }
  }

  const existingRowsById = new Map<string, any>()
  let fallbackReason: string | undefined

  api.forEachNode((node) => {
    if (fallbackReason || node.data == null) return
    if (node.id == null) {
      fallbackReason = "an existing row has no ID"
      return
    }
    if (existingRowsById.has(node.id)) {
      fallbackReason = `existing row ID ${JSON.stringify(node.id)} is duplicated`
      return
    }
    existingRowsById.set(node.id, node.data)
  })

  if (fallbackReason) {
    return { reusedRows: 0, fallbackReason }
  }

  const incomingIds = new Set<string>()
  const reconciledRows: any[] = []
  let reusedRows = 0

  for (const data of incomingRows) {
    let rawId: unknown
    try {
      rawId = getRowId({
        api,
        context: api.getGridOption("context"),
        data,
        level: 0,
      } as GetRowIdParams)
    } catch (error) {
      return {
        reusedRows: 0,
        fallbackReason: `getRowId threw: ${String(error)}`,
      }
    }

    if (rawId == null) {
      return {
        reusedRows: 0,
        fallbackReason: "getRowId returned null or undefined",
      }
    }

    const rowId = String(rawId)
    if (incomingIds.has(rowId)) {
      return {
        reusedRows: 0,
        fallbackReason: `incoming row ID ${JSON.stringify(rowId)} is duplicated`,
      }
    }
    incomingIds.add(rowId)

    const existingData = existingRowsById.get(rowId)
    if (existingData !== undefined && isEqual(existingData, data)) {
      reconciledRows.push(existingData)
      reusedRows += 1
    } else {
      reconciledRows.push(data)
    }
  }

  return { rowData: reconciledRows, reusedRows }
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


const renderAgGrid: Component<stAggridStateShape, AgGridData> = (componentArgs) => {
  const { parentElement, ...restArgs } = componentArgs
  
  let reactRoot = reactRoots.get(parentElement)
  if (!reactRoot) {
    reactRoot = ReactDOM.createRoot(parentElement)
    reactRoots.set(parentElement, reactRoot)
  }

  const componentRenderSequence =
    (componentRenderSequences.get(parentElement) || 0) + 1
  componentRenderSequences.set(parentElement, componentRenderSequence)

  reactRoot.render(

      <AgGrid
        parentElement={parentElement}
        componentRenderSequence={componentRenderSequence}
        {...omit(restArgs, 'key')}
      />

  )

  return () => {
    const root = reactRoots.get(parentElement)
    if (root) {
      root.unmount()
      reactRoots.delete(parentElement)
      componentRenderSequences.delete(parentElement)
    }
  }
}

export default renderAgGrid


const AgGrid: React.FC<AgGridProps> = (props) => {

  const rawGridOptions = useMemo(
    () => asGridOptionsObject(props.data?.gridOptions),
    [props.data?.gridOptions]
  )
  const rawGridOptionsWithoutRowData = useMemo(
    () => omit(rawGridOptions, ["rowData"]),
    [rawGridOptions]
  )
  const gridOptionsInputSignature = stableSignature({
    allowUnsafeJsCode: props.data?.allow_unsafe_jscode === true,
    gridOptions: rawGridOptionsWithoutRowData,
  })
  const themeInputSignature = stableSignature(props.data?.theme)
  const columnsStateInputSignature = stableSignature(props.data?.columns_state)

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
  const dataHashRef = useRef(props.data?.data_hash)
  const latestComponentDataRef = useRef(props.data)
  const latestDebugRef = useRef(props.data?.debug === true)
  const isApplyingServerDataRef = useRef(false)
  const serverDataDirtyRef = useRef(false)
  const serverDataEditSequenceRef = useRef(0)
  const serverSyncStrategyRef = useRef(
    props.data?.server_sync_strategy || "client_wins"
  )
  const previousServerSyncStrategyRef = useRef(
    props.data?.server_sync_strategy || "client_wins"
  )
  const rowReconciliationWarningsRef = useRef<Set<string>>(new Set())
  const initialOnlyOptionWarningsRef = useRef<Set<string>>(new Set())
  const lastGridOptionsInputSignatureRef = useRef(gridOptionsInputSignature)
  const lastThemeInputSignatureRef = useRef(themeInputSignature)
  const lastColumnsStateInputSignatureRef = useRef<string | undefined>(undefined)
  const returnGridValueRef = useRef<
    (eventData: any, streamlitRerunEventTriggerName: string) => Promise<void>
  >(async () => undefined)


  // Initial grid options (stable reference, updates handled via AG Grid API)
  const gridOptionsRef = useRef<any>()
  const initialOnlyGridOptionSignaturesRef = useRef<Record<string, string>>()

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
      initialOnlyGridOptionSignaturesRef.current =
        initialOnlyGridOptionSignatures(go)
      go.rowData = parseData(props.data.data, rawGridOptions.rowData)

      // Auto-generate getRowId if not provided and data has unique IDs
      if (!("getRowId" in go) && go.rowData?.[0]?.["::auto_unique_id::"]) {
        go.getRowId = (params: GetRowIdParams) => params.data["::auto_unique_id::"]
      }

      gridOptionsRef.current = go
    }
  }

  const gridOptions = gridOptionsRef.current
  const appliedRuntimeGridOptionsRef = useRef<Record<string, any>>()
  if (!appliedRuntimeGridOptionsRef.current) {
    appliedRuntimeGridOptionsRef.current = runtimeGridOptions(gridOptions)
  }

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
  const [gridReadySequence, setGridReadySequence] = useState(0)
  const apiRef = useRef<GridApi | undefined>(undefined)

  latestComponentDataRef.current = props.data
  serverSyncStrategyRef.current =
    props.data?.server_sync_strategy || "client_wins"

  // Derived values
  const debug = props.data?.debug || false
  latestDebugRef.current = debug
  const enterprise_features_enabled = props.data?.enable_enterprise_modules || false
  const isRowDataEdited = editedRows.size > 0
  const proAssets = props.data?.pro_assets || []
  const proAssetsSignature = JSON.stringify(proAssets)
  const updateOnSignature = JSON.stringify(props.data?.update_on || [])
  const updateOn = useMemo(
    () => props.data?.update_on || [],
    [updateOnSignature]
  )

  const runAsServerApply = useCallback((operation: () => void) => {
    const wasApplyingServerData = isApplyingServerDataRef.current
    isApplyingServerDataRef.current = true
    try {
      operation()
    } finally {
      isApplyingServerDataRef.current = wasApplyingServerData
    }
  }, [])


  // Initialization diagnostics
  useEffect(() => {
    if (debug) {
      console.log("***Received Props", props)
      console.log("*** Processed Initial State", {
        gridOptions: gridOptionsRef.current,
        editedRows,
        isMaximized,
        savedColumnState,
        dataHash: dataHashRef.current,
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

  // Extension scripts live in the document and may register durable globals.
  // injectProScript content-deduplicates them so Components V2 remounts do not
  // execute the same extension more than once.
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

  // Effect 1: Update only semantically changed, runtime-mutable grid options.
  // Components V2 creates fresh object identities on each invocation; using
  // object identity here would rebuild columns during otherwise row-only runs.
  useEffect(() => {
    const api = apiRef.current
    const componentData = latestComponentDataRef.current
    if (!api || !componentData) return
    if (
      gridOptionsInputSignature ===
      lastGridOptionsInputSignatureRef.current
    ) return

    try {
      const newOptions = parseGridOptions(
        componentData.gridOptions,
        componentData.allow_unsafe_jscode,
        componentData.theme
      )
      const nextRuntimeOptions = runtimeGridOptions(newOptions)
      const previousRuntimeOptions = appliedRuntimeGridOptionsRef.current || {}
      const changedOptions: Record<string, any> = {}

      for (const key of new Set([
        ...Object.keys(previousRuntimeOptions),
        ...Object.keys(nextRuntimeOptions),
      ])) {
        const nextValue = Object.prototype.hasOwnProperty.call(
          nextRuntimeOptions,
          key
        ) ? nextRuntimeOptions[key] : undefined
        if (
          stableSignature(previousRuntimeOptions[key]) !==
          stableSignature(nextValue)
        ) {
          changedOptions[key] = nextValue
        }
      }

      const initialOptionSignatures =
        initialOnlyGridOptionSignaturesRef.current || {}
      const changedInitialOnlyOptions = Array.from(
        INITIAL_ONLY_GRID_OPTION_KEYS
      ).filter((key) =>
        stableSignature((newOptions as any)[key]) !==
        initialOptionSignatures[key]
      )
      const unwarnedInitialOnlyOptions = changedInitialOnlyOptions.filter(
        (key) => !initialOnlyOptionWarningsRef.current.has(key)
      )
      if (unwarnedInitialOnlyOptions.length > 0) {
        unwarnedInitialOnlyOptions.forEach((key) =>
          initialOnlyOptionWarningsRef.current.add(key)
        )
        console.warn(
          "These AG Grid options are initial-only and their runtime changes " +
          "were ignored. Change the Streamlit component key to remount the " +
          `grid: ${unwarnedInitialOnlyOptions.sort().join(", ")}`
        )
      }

      if (Object.keys(changedOptions).length > 0) {
        latestDebugRef.current && console.log(
          "********** GridOptions updated",
          Object.keys(changedOptions)
        )
        runAsServerApply(() => api.updateGridOptions(changedOptions))
      }

      appliedRuntimeGridOptionsRef.current = nextRuntimeOptions
      lastGridOptionsInputSignatureRef.current = gridOptionsInputSignature
    } catch (error) {
      console.error("Failed to update AG Grid options:", error)
    }
  }, [
    gridOptionsInputSignature,
    gridReadySequence,
    runAsServerApply,
  ])

  // Effect 2: Theme CSS variables update through the cascade. Rebuild the AG
  // Grid theme object only when the user-selected theme recipe actually changes.
  useEffect(() => {
    const api = apiRef.current
    const componentData = latestComponentDataRef.current
    if (!api || !componentData) return
    if (themeInputSignature === lastThemeInputSignatureRef.current) return

    try {
      latestDebugRef.current && console.log("********** Theme updated")
      api.updateGridOptions({
        theme: themeParserRef.current.parse(componentData.theme),
      })
      lastThemeInputSignatureRef.current = themeInputSignature
    } catch (error) {
      console.error("Failed to update AG Grid theme:", error)
    }
  }, [gridReadySequence, themeInputSignature])

  const applyAuthoritativeServerData = useCallback(
    (serverSyncStrategy: string): boolean => {
      const componentData = latestComponentDataRef.current
      const api = apiRef.current
      if (!componentData || !api) return false

      const currentRawGridOptions = asGridOptionsObject(componentData.gridOptions)
      const incomingRows =
        parseData(componentData.data, currentRawGridOptions.rowData) || []
      let rowData = incomingRows

      if (serverSyncStrategy === "server_wins_rows") {
        const reconciliation = reconcileServerRows(api, incomingRows)
        if (reconciliation.fallbackReason || !reconciliation.rowData) {
          const reason = reconciliation.fallbackReason || "unknown row-ID error"
          if (!rowReconciliationWarningsRef.current.has(reason)) {
            rowReconciliationWarningsRef.current.add(reason)
            console.warn(
              "server_wins_rows skipped an unsafe server row update and " +
              "preserved the existing grid rows:",
              reason
            )
          }
          return false
        }

        rowData = reconciliation.rowData
        latestDebugRef.current && console.log(
          `server_wins_rows reused ${reconciliation.reusedRows} of ${incomingRows.length} row objects`
        )
      }

      const authoritativeOptions: Record<string, any> = { rowData }
      for (const pinnedOption of ["pinnedTopRowData", "pinnedBottomRowData"]) {
        if (Object.prototype.hasOwnProperty.call(currentRawGridOptions, pinnedOption)) {
          authoritativeOptions[pinnedOption] = cloneDeep(
            currentRawGridOptions[pinnedOption]
          )
        }
      }

      try {
        runAsServerApply(() => {
          api.stopEditing(true)
          api.updateGridOptions(authoritativeOptions)
        })
      } catch (error) {
        console.error("Failed to apply authoritative server row data:", error)
        return false
      }

      dataHashRef.current = componentData.data_hash
      serverDataDirtyRef.current = false
      setEditedRows((current) => current.size > 0 ? new Set() : current)
      return true
    },
    [runAsServerApply]
  )

  // Effect 3: Handle data sync (rowData updates).
  useEffect(() => {
    const componentData = latestComponentDataRef.current
    const api = apiRef.current
    if (!componentData || !api) return

    const serverSyncStrategy =
      componentData.server_sync_strategy || "client_wins"
    const strategyChanged =
      previousServerSyncStrategyRef.current !== serverSyncStrategy
    previousServerSyncStrategyRef.current = serverSyncStrategy
    const newHash = componentData.data_hash

    latestDebugRef.current && console.log(
      `********** Data sync (${serverSyncStrategy})`,
      {
        dataHash: dataHashRef.current,
        newHash,
        isRowDataEdited,
        serverDataDirty: serverDataDirtyRef.current,
        strategyChanged,
      }
    )

    if (serverSyncStrategy === "client_wins") {
      serverDataDirtyRef.current = false
      if (!isRowDataEdited && newHash !== dataHashRef.current) {
        try {
          runAsServerApply(() => api.updateGridOptions({
            rowData:
              parseData(
                componentData.data,
                asGridOptionsObject(componentData.gridOptions).rowData
              ) || []
          }))
          dataHashRef.current = newHash
        } catch (error) {
          console.error("Failed to update client-wins row data:", error)
        }
      }
      return
    }

    const shouldApplyServerData =
      strategyChanged ||
      serverDataDirtyRef.current ||
      newHash !== dataHashRef.current
    if (!shouldApplyServerData) return

    applyAuthoritativeServerData(serverSyncStrategy)
  }, [
    applyAuthoritativeServerData,
    gridReadySequence,
    props.componentRenderSequence,
    runAsServerApply,
  ])

  // Effect 4: Handle column state changes only when its content changes.
  useEffect(() => {
    const api = apiRef.current
    const columnsState = latestComponentDataRef.current?.columns_state
    if (!api || !columnsState) return
    if (
      columnsStateInputSignature ===
      lastColumnsStateInputSignatureRef.current
    ) return

    latestDebugRef.current && console.log("********** Column state updated")
    api.applyColumnState({ state: columnsState, applyOrder: true })
    lastColumnsStateInputSignatureRef.current = columnsStateInputSignature
  }, [columnsStateInputSignature, gridReadySequence])

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

  const returnGridValue = useCallback(async (
    eventData: any,
    streamlitRerunEventTriggerName: string
  ) => {
    const serverDataEditSequence = serverDataEditSequenceRef.current
    let returnSequence: number | undefined
    let responseCommitted = false
    try {
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

      returnSequence = ++returnSequenceRef.current
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
          responseCommitted = true
        } else {
          console.error(`Collector processing failed: ${result.error}`)
        }
      } catch (error) {
        console.error("Error in returnGridValue collector processing:", error)
      }
    } finally {
      const serverSyncStrategy = serverSyncStrategyRef.current
      if (
        serverSyncStrategy !== "client_wins" &&
        responseCommitted &&
        returnSequence !== undefined &&
        returnSequence === returnSequenceRef.current &&
        serverDataDirtyRef.current &&
        serverDataEditSequence === serverDataEditSequenceRef.current
      ) {
        // Components V2 may memoize a byte-identical server payload and skip
        // invoking the component again after an edit. Restore the last server
        // snapshot only after the collector captured the edited value.
        applyAuthoritativeServerData(serverSyncStrategy)
      }
    }
  }, [
    applyAuthoritativeServerData,
    debug,
    editedRows,
    enterprise_features_enabled,
    isMaximized,
    isRowDataEdited,
    props,
    savedColumnState,
  ])

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

  const attachMutationTracking = useCallback(
    (gridApi: GridApi): Array<() => void> => {
      const markGridDataChanged = (rowId?: string) => {
        if (isApplyingServerDataRef.current) return

        if (serverSyncStrategyRef.current === "client_wins") {
          latestDebugRef.current && console.debug(
            "server_sync_strategy is 'client_wins' - Data edited on Grid. " +
            "Ignoring server updates."
          )
          setEditedRows((previous) =>
            new Set(previous).add(rowId ?? "__grid_data_mutation__")
          )
        } else {
          serverDataDirtyRef.current = true
          serverDataEditSequenceRef.current += 1
        }
      }

      const onCellValueChanged = (event: CellValueChangedEvent) => {
        markGridDataChanged(event.node.id)
      }
      const onRowDragEnd = (event: RowDragEndEvent) => {
        const rowsDrop = event.rowsDrop
        if (
          !rowsDrop?.rowDragManaged ||
          rowsDrop.allowed === false ||
          rowsDrop.moved === false
        ) return
        markGridDataChanged()
      }
      let rowDataUpdatedBeforeAsyncFlush = false
      const onRowDataUpdated = () => {
        if (isApplyingServerDataRef.current) return

        // A client-side async transaction synchronously emits rowDataUpdated
        // and then asyncTransactionsFlushed for the same batch. Count that as
        // one mutation so a return listener on rowDataUpdated does not become
        // stale before its collector promise resumes.
        rowDataUpdatedBeforeAsyncFlush = true
        queueMicrotask(() => {
          rowDataUpdatedBeforeAsyncFlush = false
        })
        markGridDataChanged()
      }
      const onAsyncTransactionsFlushed = () => {
        if (rowDataUpdatedBeforeAsyncFlush) {
          rowDataUpdatedBeforeAsyncFlush = false
          return
        }
        markGridDataChanged()
      }

      // Cell edits are not the only way browser-owned data can change. Managed
      // row dragging and client-side transactions must also make the next
      // Streamlit invocation reconcile against the authoritative snapshot.
      gridApi.addEventListener("cellValueChanged", onCellValueChanged)
      gridApi.addEventListener("rowDragEnd", onRowDragEnd)
      gridApi.addEventListener("rowDataUpdated", onRowDataUpdated)
      gridApi.addEventListener(
        "asyncTransactionsFlushed",
        onAsyncTransactionsFlushed
      )
      return [() => {
        gridApi.removeEventListener("cellValueChanged", onCellValueChanged)
        gridApi.removeEventListener("rowDragEnd", onRowDragEnd)
        gridApi.removeEventListener("rowDataUpdated", onRowDataUpdated)
        gridApi.removeEventListener(
          "asyncTransactionsFlushed",
          onAsyncTransactionsFlushed
        )
      }]
    },
    []
  )

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
      [
        ...attachMutationTracking(gridApi),
        ...attachStreamlitRerunToEvents(gridApi),
      ]
    )
  }, [attachMutationTracking, attachStreamlitRerunToEvents])

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
    }

    setGridReadySequence((sequence) => sequence + 1)
    // Call user's onGridReady if provided. The internal ready signal is set
    // first so an exception in user code cannot suppress pending prop updates.
    gridOptionsRef.current?.onGridReady?.(event)
  }, [bindConfiguredGridEvents, resizeGridContainer])

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

  const domLayout = rawGridOptions.domLayout
  const defineContainerHeight = useMemo(() => {
    if (isMaximized) {
      return {
        width: '100vw',
        height: '100vh',
      }
    } else if (domLayout === "autoHeight") {
      return {
        width: "100%",
      }
    } else {
      return {
        width: "100%",
        height: props.data?.height || 400,
      }
    }
  }, [domLayout, isMaximized, props.data?.height])

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
const componentRenderSequences: WeakMap<
  ComponentArgs<any, AgGridData>["parentElement"],
  number
> = new WeakMap()
