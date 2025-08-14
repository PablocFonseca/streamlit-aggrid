"""
Factory functions for creating and validating AgGrid collectors
"""

from typing import Optional
from .base import BaseCollector
from .legacy import LegacyCollector
from .custom import CustomCollector
from .minimal import MinimalCollector
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
    Factory function to determine and create the appropriate collector based on DataReturnMode
    
    Parameters
    ----------
    collect_grid_return : JsCode or None
        DEPRECATED: User-provided JsCode for custom data collection.
        Now only used if data_return_mode is not MINIMAL and collect_grid_return is provided.
    should_grid_return : JsCode or None
        User-provided JsCode for determining when to return.
        Currently passed to frontend but doesn't affect collector choice.
    data_return_mode : DataReturnMode
        Determines which collector to use:
        - AS_INPUT, FILTERED, FILTERED_AND_SORTED: LegacyCollector
        - MINIMAL: MinimalCollector
    try_to_convert_back_to_original_types : bool
        Whether to attempt type conversion (for LegacyCollector)
    conversion_errors : str
        How to handle conversion errors (for LegacyCollector)
        
    Returns
    -------
    BaseCollector
        The appropriate collector instance based on data_return_mode
        
    Raises
    ------
    ValueError
        If collector parameters are invalid
    """
    # Validate parameters first
    validate_collector_params(collect_grid_return, should_grid_return)
    
    # Determine collector based exclusively on DataReturnMode
    if data_return_mode == DataReturnMode.MINIMAL:
        # For MINIMAL mode, use MinimalCollector
        return MinimalCollector()
    
    # For the first 3 modes (AS_INPUT, FILTERED, FILTERED_AND_SORTED), use LegacyCollector
    elif data_return_mode in (DataReturnMode.AS_INPUT, DataReturnMode.FILTERED, DataReturnMode.FILTERED_AND_SORTED):
        # Legacy support: if collect_grid_return is provided with legacy modes, use CustomCollector
        if collect_grid_return is not None:
            return CustomCollector(collect_grid_return.js_code)
        
        # Otherwise use LegacyCollector for the first 3 modes
        return LegacyCollector(
            data_return_mode=data_return_mode,
            try_to_convert_back_to_original_types=try_to_convert_back_to_original_types,
            conversion_errors=conversion_errors
        )
    
    else:
        raise ValueError(f"Unsupported DataReturnMode: {data_return_mode}")


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
    elif isinstance(collector, MinimalCollector):
        info["data_return_mode"] = "MINIMAL"
        info["lightweight"] = True
        info["has_custom_logic"] = False
    
    return info