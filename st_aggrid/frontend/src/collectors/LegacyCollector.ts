/**
 * Legacy collector that maintains backward compatibility
 * Contains the original getGridReturnValue logic moved from agGridReturnUtils.ts
 */

import { BaseCollector } from './BaseCollector'
import { CollectorContext, CollectorResult } from './types'
import { IRowNode } from "ag-grid-community"
import { eventDataWhiteList } from "../constants"

export class LegacyCollector extends BaseCollector {

  private fetch_node_props(n: IRowNode | null, visitedNodes = new Set<string>()): any {
    if (n == null) {
      return null
    }
    
    // Prevent infinite recursion by tracking visited nodes
    if (n.id && visitedNodes.has(n.id)) {
      return { id: n.id }
    }
    if (n.id) {
      visitedNodes.add(n.id)
    }
    
    return {
      id: n.id,
      rowIndex: n.rowIndex,
      data: n.data,
      group: n.group,
      isSelected: n.isSelected(),
      parent: n.parent ? this.fetch_node_props(n.parent, visitedNodes) : null,
    }
  }

  // Helper function to serialize objects safely for postMessage
  private serializeForPostMessage(obj: any, visited = new WeakSet()): any {
    if (obj === null || obj === undefined) {
      return obj
    }

    // Handle primitives
    if (typeof obj !== "object") {
      return obj
    }

    // Handle circular references
    if (visited.has(obj)) {
      return "[Circular]"
    }
    visited.add(obj)

    // Handle arrays
    if (Array.isArray(obj)) {
      return obj.map(item => this.serializeForPostMessage(item, visited))
    }

    // Handle AG Grid Row objects and other non-serializable objects
    if (obj.constructor && obj.constructor.name === "Row") {
      // Extract only the data from Row objects
      return obj.data || null
    }

    // Handle dates
    if (obj instanceof Date) {
      return obj.toISOString()
    }

    // Handle functions
    if (typeof obj === "function") {
      return "[Function]"
    }

    // Handle regular objects
    const serialized: any = {}
    for (const key in obj) {
      if (obj.hasOwnProperty(key)) {
        try {
          serialized[key] = this.serializeForPostMessage(obj[key], visited)
        } catch (error) {
          serialized[key] = "[Unserializable]"
        }
      }
    }
    return serialized
  }

  /**
   * Process response using the original getGridReturnValue logic
   */
  async processResponse(context: CollectorContext): Promise<CollectorResult> {
    try {
      // Validate context
      if (!this.validateContext(context)) {
        return this.createErrorResult('Invalid collector context for LegacyCollector')
      }

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
        // Serialize each selected row to avoid DataCloneError
        return selectedRows ? this.serializeForPostMessage(selectedRows) : []
      }

      const processEventData = () => {
        const cleanEventKeys = (obj: any, root = "", level = 0, visited = new WeakSet()): any => {
          // Handle circular references
          if (typeof obj === "object" && obj !== null) {
            if (visited.has(obj)) {
              return "[Circular]"
            }
            visited.add(obj)
          }

          if (Array.isArray(obj)) {
            return obj.map((v) => cleanEventKeys(v, root, level + 1, visited))
          } else if (typeof obj === "object" && obj !== null) {
            const cleanedObj: any = {}
            Object.keys(obj).forEach(function (key) {
              if (level > 3) return
              if (key === "data") return
              let fullKey = [root, key].filter((v) => v !== "").join(".")

              if (eventDataWhiteList.includes(fullKey)) {
                cleanedObj[key] = cleanEventKeys(obj[key], fullKey, level + 1, visited)
              }
            })
            return cleanedObj
          }
          return obj
        }

        // Process event data safely
        let cleanEventData = cleanEventKeys(eventData)
        cleanEventData["streamlitRerunEventTriggerName"] = streamlitRerunEventTriggerName
        return cleanEventData
      }

      // Execute all collection operations synchronously
      const nodes = collectNodes()
      const rowsAfterFilter = collectRowsAfterFilter()
      const rowsAfterSortAndFilter = collectRowsAfterSortAndFilter()
      const gridState = collectGridState()
      const columnsState = collectColumnsState()
      const selectedItems = collectSelectedItems()
      const eventDataProcessed = processEventData()

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

      const result = this.serializeForPostMessage(returnValue)
      return this.createSuccessResult(result)

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error in LegacyCollector'
      return this.createErrorResult(`LegacyCollector processing failed: ${errorMessage}`)
    }
  }

  /**
   * Get collector type
   */
  getCollectorType(): string {
    return 'LegacyCollector'
  }
}