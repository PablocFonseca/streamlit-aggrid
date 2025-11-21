/**
 * Custom collector for handling user-provided JavaScript functions
 */

import { BaseCollector } from './BaseCollector'
import { CollectorContext, CollectorResult } from './types'

export class CustomCollector extends BaseCollector {
  private customFunction: Function

  constructor(customFunction: Function) {
    super()
    this.customFunction = customFunction
  }

  /**
   * Process response using the user-provided custom function
   */
  async processResponse(context: CollectorContext): Promise<CollectorResult> {
    try {
      // Validate context
      if (!this.validateContext(context)) {
        return this.createErrorResult('Invalid collector context for CustomCollector')
      }

      // Validate custom function
      if (typeof this.customFunction !== 'function') {
        return this.createErrorResult('Custom collector function is not a valid function')
      }

      // Execute the custom function with the same parameters as the original
      const customResult = this.customFunction({
        streamlitRerunEventTriggerName: context.streamlitRerunEventTriggerName,
        eventData: context.eventData
      })

      // Handle both synchronous and asynchronous custom functions
      const result = await Promise.resolve(customResult)

      return this.createSuccessResult(result)
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Unknown error in CustomCollector'
      return this.createErrorResult(`CustomCollector processing failed: ${errorMessage}`)
    }
  }

  /**
   * Get collector type
   */
  getCollectorType(): string {
    return 'CustomCollector'
  }

  /**
   * Enhanced validation for custom collector
   */
  validateContext(context: CollectorContext): boolean {
    const baseValid = super.validateContext(context)
    
    if (!baseValid) {
      return false
    }

    // Custom collectors need the eventData to have api access
    if (!context.eventData?.api && !context.state?.api) {
      console.warn('CustomCollector: No API access available in eventData or state')
    }

    return true
  }

  /**
   * Get information about the custom function for debugging
   */
  getFunctionInfo(): { name: string; length: number; source: string } {
    return {
      name: this.customFunction.name || 'anonymous',
      length: this.customFunction.length,
      source: this.customFunction.toString().substring(0, 100) + '...'
    }
  }
}