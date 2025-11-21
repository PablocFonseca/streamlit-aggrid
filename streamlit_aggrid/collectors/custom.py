"""
Custom collector for handling user-provided JsCode responses
"""

from typing import Any, Dict
from .base import BaseCollector


class CustomResponse:
    """
    Wrapper for custom collector responses that provides safe access methods.
    
    This prevents KeyError issues when user code tries to access response properties
    that don't exist in custom responses (like grid_response['nodes']['data']).
    """
    
    def __init__(self, data: Any):
        """
        Initialize custom response wrapper
        
        Parameters
        ----------
        data : Any
            The raw data returned by the custom collector JsCode
        """
        self._data = data
        self._is_dict_like = hasattr(data, '__getitem__') and hasattr(data, 'keys')
    
    def __getitem__(self, key):
        """
        Dictionary-style access with better error messages
        
        Parameters
        ----------
        key : Any
            The key to access
            
        Returns
        -------
        Any
            The value at the key
            
        Raises
        ------
        TypeError
            If the custom response doesn't support key access
        KeyError
            If the key doesn't exist in the response
        """
        if not self._is_dict_like:
            raise TypeError(
                f"Custom collector response does not support key access. "
                f"Response type: {type(self._data).__name__}, "
                f"Response value: {self._data}"
            )
        
        try:
            return self._data[key]
        except KeyError as e:
            raise KeyError(
                f"Key '{key}' not found in custom collector response. "
                f"Available keys: {list(self._data.keys()) if hasattr(self._data, 'keys') else 'N/A'}"
            ) from e
    
    def get(self, key, default=None):
        """
        Safe access method that returns default if key doesn't exist
        
        Parameters
        ----------
        key : Any
            The key to access
        default : Any, optional
            Default value to return if key doesn't exist
            
        Returns
        -------
        Any
            The value at the key or the default value
        """
        try:
            return self[key]
        except (KeyError, TypeError):
            return default
    
    def __repr__(self):
        """String representation for debugging"""
        return f"CustomResponse({self._data!r})"
    
    def __str__(self):
        """String representation"""
        return str(self._data)
    
    @property
    def raw_data(self):
        """Access to the underlying raw data"""
        return self._data
    
    def is_dict_like(self):
        """Check if the response supports dictionary-like access"""
        return self._is_dict_like
    
    def keys(self):
        """Get keys if response is dict-like"""
        if self._is_dict_like and hasattr(self._data, 'keys'):
            return self._data.keys()
        return []


class CustomCollector(BaseCollector):
    """
    Collector for handling user-provided JsCode that returns custom data structures.
    
    This collector returns the raw response data without AgGridReturn processing,
    wrapped in a CustomResponse object for safe access.
    """
    
    def __init__(self, js_code: str):
        """
        Initialize custom collector with user JsCode
        
        Parameters
        ----------
        js_code : str
            The JavaScript code that processes the grid response
        """
        self.js_code = js_code
    
    def create_initial_response(self, original_data: Any, grid_options: Dict, **kwargs) -> CustomResponse:
        """
        Create an initial CustomResponse object that can be safely referenced by callbacks
        """
        # Create CustomResponse with None as initial data
        # This provides safe access methods from the start
        return CustomResponse(None)
    
    def update_response(self, response: CustomResponse, component_value: Any) -> CustomResponse:
        """
        Update the CustomResponse object with actual component data
        """
        # For custom collectors, we replace the data entirely
        # since the component_value contains the processed custom data
        return CustomResponse(component_value)
    
    def process_response(self, component_value: Any, original_data: Any, grid_options: Dict) -> CustomResponse:
        """
        Process response by returning the raw component value wrapped in CustomResponse
        
        For custom collectors, we don't apply AgGridReturn processing since the user's
        JsCode has already processed the data into their desired format.
        
        Parameters
        ----------
        component_value : Any
            The raw response from the custom collector JsCode
        original_data : Any
            The original data (not used for custom collectors)
        grid_options : Dict
            The grid options (not used for custom collectors)
            
        Returns
        -------
        CustomResponse
            Wrapped response with safe access methods
        """
        return CustomResponse(component_value)
    
    def get_return_type(self) -> str:
        """Return type description for custom collector"""
        return "CustomResponse"
    
    def validate_response(self, response: Any) -> bool:
        """Validate that response is a CustomResponse object"""
        return isinstance(response, CustomResponse)