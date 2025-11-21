/**
 * AgGrid Frontend Collectors - Response processing components
 * 
 * This module provides different collector strategies for processing AgGrid responses:
 * - LegacyCollector: Maintains backward compatibility with existing getGridReturnValue
 * - CustomCollector: Handles user-provided JavaScript functions
 * - Future collectors can be added for specific use cases
 */

export { BaseCollector } from './BaseCollector'
export { LegacyCollector } from './LegacyCollector'
export { CustomCollector } from './CustomCollector'
export { determineCollector, validateCollectorConfig, CollectorType } from './CollectorFactory'
export type { CollectorContext, CollectorResult } from './types'