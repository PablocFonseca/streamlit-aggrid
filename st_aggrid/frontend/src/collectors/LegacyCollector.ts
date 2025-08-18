/**
 * Legacy collector that maintains backward compatibility
 * Contains the original getGridReturnValue logic moved from agGridReturnUtils.ts
 */

import { BaseCollector } from "./BaseCollector"
import { CollectorContext, CollectorResult } from "./types"
import { IRowNode } from "ag-grid-community"

export class LegacyCollector extends BaseCollector {
  


  private fetch_node_props(n: IRowNode | null): any {
    if (n == null) {
      return null
    }

    // Only calculate parentPath for non-group nodes (leaf nodes) to improve performance
    const parentPath = n.group ? "" : this.get_parent_path(n)

    const sanitizeData = (obj: any): any => {
      if (obj === null || obj === undefined) return obj
      
      const type = typeof obj
      if (type === 'bigint') return Number(obj)
      if (type === 'function' || type === 'symbol') return undefined
      if (type !== 'object') return obj
      
      if (Array.isArray(obj)) return obj.map(sanitizeData)
      
      const result: any = {}
      for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
          result[key] = sanitizeData(obj[key])
        }
      }
      return result
    }

    return {
      id: n.id,
      rowIndex: n.rowIndex,
      data: sanitizeData({...n.data}),
      group: n.group,
      isSelected: n.isSelected(),
      parentPath: parentPath,
    }
  }

  private get_parent_path(node: IRowNode | null): string {
    if (!node || !node.parent) {
      return ""
    }
    
    // Build path iteratively using row IDs instead of display values
    const pathParts: string[] = []
    let current: IRowNode | null = node.parent
    const visited = new Set<string>() // Use string IDs instead of object references
    let depth = 0
    const MAX_DEPTH = 10 // Safety limit to prevent infinite loops
    
    // Traverse up the parent chain, collecting row IDs
    while (current && depth < MAX_DEPTH) {
      const nodeId = current.id
      
      // Check for circular references using ID
      if (nodeId && visited.has(nodeId)) {
        console.warn(`Circular reference detected in group hierarchy at node: ${nodeId}`)
        break
      }
      
      if (nodeId) {
        visited.add(nodeId)
        pathParts.unshift(nodeId) // Add to beginning to maintain order
      }
      
      current = current.parent
      depth++
    }
    
    if (depth >= MAX_DEPTH) {
      console.warn(`Maximum group hierarchy depth (${MAX_DEPTH}) exceeded`)
    }
    
    return pathParts.join(".")
  }

  private filterSerializableEventData = (
    obj: any,
    maxDepth = 2,
    depth = 0
  ): any => {
    if (depth > maxDepth || obj === null || obj === undefined) {
      return undefined
    }

    // Return primitive types as-is (only these should be included)
    if (
      typeof obj === "string" ||
      typeof obj === "number" ||
      typeof obj === "boolean"
    ) {
      return obj
    }

    // Filter out functions, symbols, and other non-serializable types
    if (
      typeof obj === "function" ||
      typeof obj === "symbol" ||
      typeof obj === "bigint"
    ) {
      return undefined
    }

    // Handle arrays - filter out empty arrays
    if (Array.isArray(obj)) {
      const filteredArray = obj
        .map((item) =>
          this.filterSerializableEventData(item, maxDepth, depth + 1)
        )
        .filter((item) => item !== undefined && item !== null && item !== "")

      // Return undefined if array is empty after filtering
      return filteredArray.length > 0 ? filteredArray : undefined
    }

    // Handle objects - filter out empty objects
    if (typeof obj === "object") {
      const filtered: any = {}
      for (const key in obj) {
        if (obj.hasOwnProperty(key)) {
          const value = this.filterSerializableEventData(
            obj[key],
            maxDepth,
            depth + 1
          )
          if (value !== undefined && value !== null && value !== "") {
            filtered[key] = value
          }
        }
      }

      // Return undefined if object is empty after filtering
      return Object.keys(filtered).length > 0 ? filtered : undefined
    }

    return undefined
  }

  /**
   * Process response using the original getGridReturnValue logic
   */
  async processResponse(context: CollectorContext): Promise<CollectorResult> {
    const { state, props, eventData, streamlitRerunEventTriggerName } = context
    let api = state.api

    // Create functions for all data collection operations
    const collectNodes = (): any[] => {
      if (!api) return []

      const nodes: any[] = []
      api.forEachNode((n: any) => {
        nodes.push(this.fetch_node_props(n))
      })
      return nodes
    }

    const collectRowsAfterFilter = (): any[] => {
      const rows: any[] = []
      api?.forEachNodeAfterFilter((row: { group: any; id: any }) => {
        if (!row.group) {
          rows.push(row.id)
        }
      })
      return rows
    }

    const collectRowsAfterSortAndFilter = (): any[] => {
      const rows: any[] = []
      api?.forEachNodeAfterFilterAndSort((row: { group: any; id: any }) => {
        if (!row.group) {
          rows.push(row.id)
        }
      })
      return rows
    }

    const collectGridState = () => {
      return api?.getState()
    }

    const collectColumnsState = () => {
      return api?.getColumnState()
    }

    const collectSelectedItems = () => {
      const selectedRows = api?.getSelectedRows()

      return selectedRows
    }

    const processEventData = () => {
      const rawEventData = {
        ...eventData,
        streamlitRerunEventTriggerName: streamlitRerunEventTriggerName,
      }
      return this.filterSerializableEventData(rawEventData)
    }

    // Execute all collection operations synchronously
    const nodes = collectNodes()
    const rowsAfterFilter = collectRowsAfterFilter()
    const rowsAfterSortAndFilter = collectRowsAfterSortAndFilter()
    const gridState = collectGridState()
    const columnsState = collectColumnsState()
    const selectedItems = collectSelectedItems()
    const eventDataProcessed = processEventData()

    // Debug output removed - use browser dev tools if needed to inspect getRowId

    // Serialize the entire return value to ensure it can be sent via postMessage
    const returnValue = {
      originalDtypes: props.args.frame_dtypes,
      nodes: nodes,
      selectedItems: selectedItems,
      gridState: gridState,
      columnsState: columnsState,
      rowIdsAfterFilter: rowsAfterFilter,
      rowIdsAfterSortAndFilter: rowsAfterSortAndFilter,
      eventData: eventDataProcessed,
    }

    const result = returnValue // this.serializeForPostMessage(returnValue)
    return this.createSuccessResult(result)
  }

  /**
   * Get collector type
   */
  getCollectorType(): string {
    return "LegacyCollector"
  }
}
