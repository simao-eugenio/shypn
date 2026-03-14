"""
Base Extractor Class

Abstract base class for all SBML element extractors.
Provides common functionality for logging, error handling, and validation.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List
import logging

T = TypeVar('T')


class BaseExtractor(ABC, Generic[T]):
    """
    Abstract base class for SBML element extractors.
    
    Design Pattern: Template Method
    - Subclasses implement extract() for specific element types
    - Common logging, error handling in base class
    - Type-safe with generics
    
    Attributes:
        model: libsbml Model object
        logger: Logger instance for this extractor
        _errors: List of error messages encountered during extraction
        _warnings: List of warning messages encountered during extraction
    """
    
    def __init__(self, sbml_model, logger=None):
        """
        Initialize extractor with SBML model.
        
        Args:
            sbml_model: libsbml Model object
            logger: Optional logger instance (creates one if not provided)
        """
        self.model = sbml_model
        self.logger = logger or logging.getLogger(self.__class__.__name__)
        self._errors: List[str] = []
        self._warnings: List[str] = []
    
    @abstractmethod
    def extract(self) -> T:
        """
        Extract elements from SBML model.
        
        Must be implemented by subclasses.
        
        Returns:
            Extracted data (type depends on subclass)
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement extract()")
    
    def validate_extraction(self) -> bool:
        """
        Validate extracted data.
        
        Override in subclasses if custom validation is needed.
        
        Returns:
            True if extraction is valid (no errors), False otherwise
        """
        return len(self._errors) == 0
    
    def get_errors(self) -> List[str]:
        """
        Get list of errors encountered during extraction.
        
        Returns:
            Copy of error list
        """
        return self._errors.copy()
    
    def get_warnings(self) -> List[str]:
        """
        Get list of warnings encountered during extraction.
        
        Returns:
            Copy of warning list
        """
        return self._warnings.copy()
    
    def add_error(self, message: str) -> None:
        """
        Add an error message.
        
        Args:
            message: Error description
        """
        self._errors.append(message)
        self.logger.error(message)
    
    def add_warning(self, message: str) -> None:
        """
        Add a warning message.
        
        Args:
            message: Warning description
        """
        self._warnings.append(message)
        self.logger.warning(message)
    
    def clear_messages(self) -> None:
        """Clear all error and warning messages."""
        self._errors.clear()
        self._warnings.clear()
