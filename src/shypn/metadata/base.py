"""
Base metadata classes for SHYPN sweep experiment headers.

This module provides the abstract base class for all metadata sections
that can be included in CSV file headers from parameter sweep experiments.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
import json


class MetadataSection(ABC):
    """Abstract base class for metadata sections in sweep CSV headers."""
    
    def __init__(self, section_name: str):
        self.section_name = section_name
        self._fields: Dict[str, Any] = {}
        self._field_order: List[str] = []
        self._comments: Dict[str, str] = {}
        
    @abstractmethod
    def collect(self, context: Dict[str, Any]) -> None:
        """
        Collect metadata from the given context.
        
        Args:
            context: Dictionary containing model, simulation config, etc.
        """
        pass
    
    @abstractmethod
    def validate(self) -> tuple[bool, Optional[str]]:
        """
        Validate the collected metadata.
        
        Returns:
            (is_valid, error_message) tuple
        """
        pass
    
    def add_field(self, key: str, value: Any, comment: Optional[str] = None) -> None:
        """Add a field to this metadata section."""
        self._fields[key] = value
        if key not in self._field_order:
            self._field_order.append(key)
        if comment:
            self._comments[key] = comment
    
    def get_field(self, key: str, default: Any = None) -> Any:
        """Get a field value."""
        return self._fields.get(key, default)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata section to dictionary."""
        # Convert datetime objects to ISO format strings for JSON serialization
        fields_copy = {}
        for key, value in self._fields.items():
            if isinstance(value, datetime):
                fields_copy[key] = value.isoformat()
            else:
                fields_copy[key] = value
        
        return {
            'section': self.section_name,
            'fields': fields_copy
        }
    
    def to_header_lines(self) -> List[str]:
        """
        Convert metadata section to CSV header comment lines.
        
        Returns:
            List of header lines (without leading '#')
        """
        lines = []
        lines.append("")
        lines.append(f"[{self.section_name.upper()}]")
        
        for key in self._field_order:
            value = self._fields[key]
            comment = self._comments.get(key, "")
            
            # Format value
            if isinstance(value, datetime):
                value_str = value.isoformat() + 'Z'
            elif isinstance(value, (int, float)):
                value_str = str(value)
            elif isinstance(value, bool):
                value_str = "YES" if value else "NO"
            else:
                value_str = str(value)
            
            # Build line
            if comment:
                line = f"{key}: {value_str}  # {comment}"
            else:
                line = f"{key}: {value_str}"
            
            lines.append(line)
        
        return lines
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MetadataSection':
        """Create metadata section from dictionary."""
        section_name = data.get('section', cls.__name__)
        instance = cls(section_name)
        
        for key, value in data.get('fields', {}).items():
            instance.add_field(key, value)
        
        return instance


class MetadataHeader:
    """Container for all metadata sections in a sweep CSV header."""
    
    VERSION = "1.0"
    
    def __init__(self):
        self.sections: List[MetadataSection] = []
        self.version = self.VERSION
        self.created_at = datetime.utcnow()
        
    def add_section(self, section: MetadataSection) -> None:
        """Add a metadata section."""
        self.sections.append(section)
    
    def get_section(self, section_type: type) -> Optional[MetadataSection]:
        """Get a specific metadata section by type."""
        for section in self.sections:
            if isinstance(section, section_type):
                return section
        return None
    
    def validate_all(self) -> tuple[bool, List[str]]:
        """
        Validate all metadata sections.
        
        Returns:
            (all_valid, error_messages) tuple
        """
        errors = []
        all_valid = True
        
        for section in self.sections:
            is_valid, error = section.validate()
            if not is_valid:
                all_valid = False
                if error:
                    errors.append(f"[{section.section_name}] {error}")
        
        return all_valid, errors
    
    def to_header_text(self) -> str:
        """
        Convert all metadata to CSV header text.
        
        Returns:
            Header text with '# ' prefix on each line
        """
        lines = []
        
        # Title banner
        lines.append("=" * 76)
        lines.append(f"SHYPN PARAMETER SWEEP DATA - HEADER PROTOCOL v{self.VERSION}")
        lines.append(f"Generated: {self.created_at.isoformat()}Z")
        lines.append("=" * 76)
        
        # Add all sections
        for section in self.sections:
            section_lines = section.to_header_lines()
            lines.extend(section_lines)
        
        # Data section marker
        lines.append("")
        lines.append("=" * 76)
        lines.append("DATA SECTION BEGINS")
        lines.append("=" * 76)
        
        # Add '# ' prefix to each line
        header_text = '\n'.join(f"# {line}" for line in lines)
        header_text += '\n'
        
        return header_text
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert header to dictionary."""
        return {
            'version': self.version,
            'created_at': self.created_at.isoformat(),
            'sections': [section.to_dict() for section in self.sections]
        }
    
    def to_json(self) -> str:
        """Convert header to JSON string."""
        return json.dumps(self.to_dict(), indent=2)


class EditableField:
    """
    Descriptor for editable metadata fields in UI.
    
    This allows metadata fields to be marked as user-editable
    and provides validation/constraints for UI components.
    """
    
    def __init__(
        self,
        field_type: type,
        default: Any = None,
        editable: bool = True,
        validator: Optional[callable] = None,
        choices: Optional[List[Any]] = None,
        min_value: Optional[float] = None,
        max_value: Optional[float] = None,
        description: Optional[str] = None
    ):
        self.field_type = field_type
        self.default = default
        self.editable = editable
        self.validator = validator
        self.choices = choices
        self.min_value = min_value
        self.max_value = max_value
        self.description = description
        self.value = default
        
    def validate_value(self, value: Any) -> tuple[bool, Optional[str]]:
        """Validate a value against constraints."""
        # Type check
        if not isinstance(value, self.field_type):
            return False, f"Expected {self.field_type.__name__}, got {type(value).__name__}"
        
        # Choice constraint
        if self.choices and value not in self.choices:
            return False, f"Value must be one of: {self.choices}"
        
        # Range constraint
        if self.min_value is not None and value < self.min_value:
            return False, f"Value must be >= {self.min_value}"
        
        if self.max_value is not None and value > self.max_value:
            return False, f"Value must be <= {self.max_value}"
        
        # Custom validator
        if self.validator:
            try:
                if not self.validator(value):
                    return False, "Custom validation failed"
            except Exception as e:
                return False, f"Validation error: {str(e)}"
        
        return True, None
