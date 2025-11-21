"""
Legacy collector that maintains backward compatibility with AgGridReturn
"""

from typing import Any, Dict
from .base import BaseCollector
from ..AgGridReturn import AgGridReturn
from ..shared import DataReturnMode


class LegacyCollector(BaseCollector):
    """
    Collector that encapsulates the original AgGrid response processing logic.
    Returns AgGridReturn objects to maintain backward compatibility.
    """
    
    def __init__(
        self,
        frame_dtypes=None,
        data_return_mode: DataReturnMode = DataReturnMode.AS_INPUT,
        try_to_convert_back_to_original_types: bool = True,
        conversion_errors: str = "coerce"
    ):
        """
        Initialize the legacy collector with original AgGrid parameters
        
        Parameters
        ----------
        data_return_mode : DataReturnMode
            How to return data from the grid
        try_to_convert_back_to_original_types : bool
            Whether to attempt type conversion
        conversion_errors : str
            How to handle conversion errors
        """
        self.data_return_mode = data_return_mode
        self.frame_dtypes = frame_dtypes
        self.try_to_convert_back_to_original_types=try_to_convert_back_to_original_types
        self.conversion_errors=conversion_errors
    
    def create_initial_response(self, original_data: Any, grid_options: Dict, **kwargs) -> AgGridReturn:
        """
        Create an initial AgGridReturn object that can be safely referenced by callbacks
        """
        # Create AgGridReturn object with original parameters
        response = AgGridReturn(
            originalData=original_data,
            data_return_mode=self.data_return_mode,
            frame_dtypes=self.frame_dtypes,
            conversion_errors='coerce' if self.try_to_convert_back_to_original_types else 'raise'
        )
        
        # Note: component value is not set yet - will be set by update_response
        return response
    
    def update_response(self, response: AgGridReturn, component_value: Any) -> AgGridReturn:
        """
        Update the AgGridReturn object with component data
        """
        if component_value:
            response._set_component_value(component_value)
        return response
    
    def process_response(self, component_value: Any, original_data: Any, grid_options: Dict) -> AgGridReturn:
        """
        Process response using the original AgGrid logic
        
        """
        # Create AgGridReturn object with original parameters
        response = AgGridReturn(
            originalData=original_data,
            data_return_mode=self.data_return_mode,
            try_to_convert_back_to_original_types=self.try_to_convert_back_to_original_types,
            conversion_errors=self.conversion_errors,
            frame_dtypes=self.frame_dtypes
        )
        
        # Set component value if present (original logic from AgGrid.py)
        if component_value:
            response._set_component_value(component_value)
            
        return response
    
    def get_return_type(self) -> str:
        """Return type description for legacy collector"""
        return "AgGridReturn"
    
    def validate_response(self, response: Any) -> bool:
        """Validate that response is an AgGridReturn object"""
        return isinstance(response, AgGridReturn)