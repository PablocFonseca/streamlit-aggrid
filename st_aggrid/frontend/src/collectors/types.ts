/**
 * Types for the collector system
 */

import { State } from "../types/AgGridTypes"

export interface CollectorContext {
  state: State
  props: any
  eventData: any
  streamlitRerunEventTriggerName: string
}

export interface CollectorResult {
  success: boolean
  data?: any
  error?: string
}