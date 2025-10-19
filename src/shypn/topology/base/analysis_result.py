"""Result data structure for topology analysis."""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class AnalysisResult:
    """Result of topology analysis.
    
    This class encapsulates the results of any topology analysis,
    including success status, data, summaries, and warnings/errors.
    
    Attributes:
        success: Whether the analysis succeeded
        data: Dictionary of analysis data (structure varies by analyzer)
        summary: Human-readable summary of results
        warnings: List of warning messages
        errors: List of error messages
        metadata: Additional metadata (e.g., computation time, parameters)
        
    Example:
        result = analyzer.analyze()
        if result.success:
            cycles = result.get('cycles', [])
            print(result.summary)
        else:
            print("Errors:", result.errors)
    """
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    summary: str = ""
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get data value by key.
        
        Args:
            key: Data key to retrieve
            default: Default value if key not found
            
        Returns:
            Data value or default
        """
        return self.data.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set data value.
        
        Args:
            key: Data key to set
            value: Value to store
        """
        self.data[key] = value
    
    def has_warnings(self) -> bool:
        """Check if result has warnings.
        
        Returns:
            True if warnings exist
        """
        return len(self.warnings) > 0
    
    def has_errors(self) -> bool:
        """Check if result has errors.
        
        Returns:
            True if errors exist
        """
        return len(self.errors) > 0
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message.
        
        Args:
            warning: Warning message to add
        """
        self.warnings.append(warning)
    
    def add_error(self, error: str) -> None:
        """Add an error message.
        
        Args:
            error: Error message to add
        """
        self.errors.append(error)
        self.success = False
    
    def __bool__(self) -> bool:
        """Allow boolean evaluation (True if successful)."""
        return self.success
    
    def __str__(self) -> str:
        """String representation."""
        status = "✓" if self.success else "✗"
        parts = [f"[{status}]"]
        
        if self.summary:
            parts.append(self.summary)
        
        if self.has_warnings():
            parts.append(f"⚠️  {len(self.warnings)} warning(s)")
        
        if self.has_errors():
            parts.append(f"❌ {len(self.errors)} error(s)")
        
        return " ".join(parts)
