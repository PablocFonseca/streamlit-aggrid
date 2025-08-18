"""
Base collector abstract class for AgGrid response processing
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class BaseCollector(ABC):
    """Abstract base class for AgGrid response collectors"""
    
    @abstractmethod
    def create_initial_response(self, original_data: Any, grid_options: Dict, **kwargs) -> Any:
        """
        Create an initial response object that can be safely referenced by callbacks
        before component execution completes.
        
        Parameters
        ----------
        original_data : Any  
            The original data passed to AgGrid
        grid_options : Dict
            The grid options used for AgGrid
        **kwargs : dict
            Additional collector-specific parameters
            
        Returns
        -------
        Any
            Initial response object in the appropriate format for this collector
        """
        pass
    
    @abstractmethod
    def update_response(self, response: Any, component_value: Any) -> Any:
        """
        Update the initial response object with actual data from the component
        
        Parameters
        ----------
        response : Any
            The initial response object created by create_initial_response
        component_value : Any
            The raw response from the AgGrid component
            
        Returns
        -------
        Any
            Updated response object with component data
        """
        pass
    
    @abstractmethod
    def process_response(self, component_value: Any, original_data: Any, grid_options: Dict) -> Any:
        """
        Process the component response and return appropriate data structure
        
        NOTE: This method is now primarily used as a fallback. The preferred approach
        is to use create_initial_response() + update_response() for better callback support.
        
        Parameters
        ----------
        component_value : Any
            The raw response from the AgGrid component
        original_data : Any  
            The original data passed to AgGrid
        grid_options : Dict
            The grid options used for AgGrid
            
        Returns
        -------
        Any
            Processed response in the appropriate format for this collector
        """
        pass
    
    @abstractmethod
    def get_return_type(self) -> str:
        """
        Return the type of data this collector returns
        
        Returns
        -------
        str
            String description of the return type
        """
        pass
    
    def validate_response(self, response: Any) -> bool:
        """
        Validate the response data - override if needed
        
        Parameters
        ----------
        response : Any
            The response to validate
            
        Returns
        -------
        bool
            True if response is valid, False otherwise
        """
        return response is not None