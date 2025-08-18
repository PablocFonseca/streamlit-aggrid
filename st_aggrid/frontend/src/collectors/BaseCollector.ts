/**
 * Abstract base class for AgGrid response collectors
 */

import { CollectorContext, CollectorResult } from "./types"

export abstract class BaseCollector {
  /**
   * Process the grid response and return appropriate data structure
   */
  abstract processResponse(context: CollectorContext): Promise<CollectorResult>

  /**
   * Get the type/name of this collector
   */
  abstract getCollectorType(): string

  /**
   * Validate the collector context - override if needed
   */
  validateContext(context: CollectorContext): boolean {
    return (
      context.state?.api !== undefined &&
      context.props !== undefined &&
      context.streamlitRerunEventTriggerName !== undefined
    )
  }

  /**
   * Create a successful result
   */
  protected createSuccessResult(data: any): CollectorResult {
    return {
      success: true,
      data: data,
    }
  }

  /**
   * Create an error result
   */
  protected createErrorResult(error: string): CollectorResult {
    return {
      success: false,
      error: error,
    }
  }
}
