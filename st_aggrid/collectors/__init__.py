"""
AgGrid Collectors - Response processing components

This module provides different collector strategies for processing AgGrid responses:
- LegacyCollector: Maintains backward compatibility with AgGridReturn (DataReturnMode: AS_INPUT, FILTERED, FILTERED_AND_SORTED)
- CustomCollector: Handles user-provided JsCode collectors (legacy compatibility)
- MinimalCollector: Lightweight collector for minimal responses (DataReturnMode: MINIMAL)
"""

from .base import BaseCollector
from .legacy import LegacyCollector
from .custom import CustomCollector, CustomResponse
from .minimal import MinimalCollector, MinimalResponse
from .factory import determine_collector, validate_collector_params

__all__ = [
    'BaseCollector',
    'LegacyCollector', 
    'CustomCollector',
    'CustomResponse',
    'MinimalCollector',
    'MinimalResponse',
    'determine_collector',
    'validate_collector_params'
]