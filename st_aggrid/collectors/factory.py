"""
Factory functions for creating and validating AgGrid collectors
"""

from typing import Optional
from .base import BaseCollector
from .legacy import LegacyCollector
from .custom import CustomCollector
from ..shared import DataReturnMode, JsCode


def validate_collector_params(collect_grid_return: Optional[JsCode], should_grid_return: Optional[JsCode]) -> None:
    """
    Validate collector parameters before creating collectors
    
    Parameters
    ----------
    collect_grid_return : JsCode or None
        User-provided JsCode for custom data collection
    should_grid_return : JsCode or None  
        User-provided JsCode for determining when to return
        
    Raises
    ------
    ValueError
        If parameters are invalid
    """
    if collect_grid_return is not None:
        if not isinstance(collect_grid_return, JsCode):
            raise ValueError(
                "collect_grid_return must be a JsCode object. "
                f"Got {type(collect_grid_return).__name__} instead."
            )
    
    if should_grid_return is not None:
        if not isinstance(should_grid_return, JsCode):
            raise ValueError(
                "should_grid_return must be a JsCode object. "
                f"Got {type(should_grid_return).__name__} instead."
            )


def determine_collector(
    collect_grid_return: Optional[JsCode] = None,
    should_grid_return: Optional[JsCode] = None,
    data_return_mode: DataReturnMode = DataReturnMode.AS_INPUT,
    try_to_convert_back_to_original_types: bool = True,
    conversion_errors: str = "coerce"
) -> BaseCollector:
    """
    Factory function to determine and create the appropriate collector
    
    Parameters
    ----------
    collect_grid_return : JsCode or None
        User-provided JsCode for custom data collection. 
        If provided, returns CustomCollector.
    should_grid_return : JsCode or None
        User-provided JsCode for determining when to return.
        Currently passed to frontend but doesn't affect collector choice.
    data_return_mode : DataReturnMode
        How to return data from the grid (for LegacyCollector)
    try_to_convert_back_to_original_types : bool
        Whether to attempt type conversion (for LegacyCollector)
    conversion_errors : str
        How to handle conversion errors (for LegacyCollector)
        
    Returns
    -------
    BaseCollector
        The appropriate collector instance
        
    Raises
    ------
    ValueError
        If collector parameters are invalid
    """
    # Validate parameters first
    validate_collector_params(collect_grid_return, should_grid_return)
    
    # If user provided custom collector JsCode, use CustomCollector
    if collect_grid_return is not None:
        return CustomCollector(collect_grid_return.js_code)
    
    # Otherwise, use LegacyCollector for backward compatibility
    else:
        return LegacyCollector(
            data_return_mode=data_return_mode,
            try_to_convert_back_to_original_types=try_to_convert_back_to_original_types,
            conversion_errors=conversion_errors
        )


def get_collector_info(collector: BaseCollector) -> dict:
    """
    Get information about a collector for debugging/logging
    
    Parameters
    ----------
    collector : BaseCollector
        The collector to get info about
        
    Returns
    -------
    dict
        Information about the collector
    """
    info = {
        "type": collector.__class__.__name__,
        "return_type": collector.get_return_type()
    }
    
    # Add specific info for different collector types
    if isinstance(collector, CustomCollector):
        info["js_code_length"] = len(collector.js_code)
        info["has_custom_logic"] = True
    elif isinstance(collector, LegacyCollector):
        info["data_return_mode"] = str(collector.data_return_mode)
        info["try_convert_types"] = collector.try_to_convert_back_to_original_types
        info["conversion_errors"] = collector.conversion_errors
        info["has_custom_logic"] = False
    
    return info