"""
AgGrid Collectors - Response processing components

This module provides different collector strategies for processing AgGrid responses:
- LegacyCollector: Maintains backward compatibility with AgGridReturn
- CustomCollector: Handles user-provided JsCode collectors
- Future collectors can be added for specific use cases
"""

from .base import BaseCollector
from .legacy import LegacyCollector
from .custom import CustomCollector, CustomResponse
from .factory import determine_collector, validate_collector_params

__all__ = [
    'BaseCollector',
    'LegacyCollector', 
    'CustomCollector',
    'CustomResponse',
    'determine_collector',
    'validate_collector_params'
]