/**
 * Lightweight collector used by DataReturnMode.MINIMAL.
 *
 * Unlike the legacy collector, this never walks the row model, filter model,
 * column state, or grid state. It returns only a compact, serializable summary
 * of the event that caused the Streamlit update.
 */

import { BaseCollector } from "./BaseCollector"
import { CollectorContext, CollectorResult } from "./types"

const HEAVY_EVENT_KEYS = new Set([
  "api",
  "columnApi",
  "context",
  "event",
  "eventPath",
  "eGui",
  "target",
])

const isPrimitive = (value: unknown): boolean =>
  value === null ||
  typeof value === "string" ||
  typeof value === "number" ||
  typeof value === "boolean"

const MAX_ROW_DATA_DEPTH = 20

const sanitizeRowData = (
  value: unknown,
  ancestors: WeakSet<object> = new WeakSet(),
  depth = 0
): unknown => {
  if (depth > MAX_ROW_DATA_DEPTH) return undefined
  if (isPrimitive(value)) return value
  if (typeof value === "bigint") return Number(value)
  if (value instanceof Date) return value.toISOString()

  if (!value || typeof value !== "object") return undefined
  if (ancestors.has(value)) return undefined

  ancestors.add(value)

  try {
    if (Array.isArray(value)) {
      return value
        .map((item) => sanitizeRowData(item, ancestors, depth + 1))
        .filter((item) => item !== undefined)
    }

    const result: Record<string, unknown> = {}
    for (const [key, child] of Object.entries(value)) {
      const sanitized = sanitizeRowData(child, ancestors, depth + 1)
      if (sanitized !== undefined) result[key] = sanitized
    }
    return result
  } finally {
    ancestors.delete(value)
  }
}

const collectEventData = (
  eventData: unknown,
  streamlitRerunEventTriggerName: string
): Record<string, unknown> => {
  const response: Record<string, unknown> = {
    streamlitRerunEventTriggerName,
  }

  if (!eventData || typeof eventData !== "object") return response
  const event = eventData as Record<string, unknown>

  for (const [key, value] of Object.entries(event)) {
    if (HEAVY_EVENT_KEYS.has(key)) continue

    if (isPrimitive(value)) {
      response[key] = value
    }
  }

  // Row data is the only potentially nested event value retained. This makes
  // cell edits useful without serializing every row in the grid.
  if ("data" in event) {
    const data = sanitizeRowData(event.data)
    if (data !== undefined) response.data = data
  }

  const node = event.node
  if (node && typeof node === "object") {
    const rowNode = node as {
      id?: unknown
      rowIndex?: unknown
      rowPinned?: unknown
      group?: unknown
    }
    const nodeFields = {
      id: rowNode.id,
      rowIndex: rowNode.rowIndex,
      rowPinned: rowNode.rowPinned,
      group: rowNode.group,
    }
    const nodeResponse: Record<string, unknown> = {}
    for (const [key, value] of Object.entries(nodeFields)) {
      const sanitized = sanitizeRowData(value)
      if (sanitized !== undefined) nodeResponse[key] = sanitized
    }
    response.node = nodeResponse
  }

  const column = event.column
  if (column && typeof column === "object") {
    const gridColumn = column as { getColId?: () => string; colId?: unknown }
    const colId = typeof gridColumn.getColId === "function"
      ? gridColumn.getColId()
      : sanitizeRowData(gridColumn.colId)
    if (colId !== undefined) response.column = { colId }
  }

  return response
}

export class MinimalCollector extends BaseCollector {
  async processResponse(context: CollectorContext): Promise<CollectorResult> {
    return this.createSuccessResult({
      eventData: collectEventData(
        context.eventData,
        context.streamlitRerunEventTriggerName
      ),
    })
  }

  getCollectorType(): string {
    return "MinimalCollector"
  }
}
