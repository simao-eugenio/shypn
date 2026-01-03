"""Base service class for BiGG database operations.

Provides common functionality for API communication, error handling,
and logging. All BiGG services should extend this class.
"""

from abc import ABC, abstractmethod
import logging
from typing import Optional


class BiGGServiceError(Exception):
    """Exception raised for BiGG service errors."""
    pass


class BaseBiGGService(ABC):
    """Abstract base class for BiGG database services.
    
    Provides common functionality for API communication, error handling,
    and logging. All BiGG services should extend this class.
    
    Attributes:
        base_url: Base URL for BiGG API
        logger: Logger instance for this service
    """
    
    def __init__(self, base_url: str = "http://bigg.ucsd.edu"):
        """Initialize service.
        
        Args:
            base_url: Base URL for BiGG API (default: http://bigg.ucsd.edu)
        """
        self.base_url = base_url
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def validate(self) -> bool:
        """Validate service configuration and connectivity.
        
        Returns:
            True if service is properly configured and accessible.
        """
        pass
    
    def _handle_http_error(self, error: Exception, context: str):
        """Centralized error handling for HTTP requests.
        
        Args:
            error: The exception that occurred
            context: Description of what operation failed
            
        Raises:
            BiGGServiceError: Always raised with context information
        """
        error_msg = f"Failed to {context}: {error}"
        self.logger.error(error_msg)
        raise BiGGServiceError(error_msg) from error
