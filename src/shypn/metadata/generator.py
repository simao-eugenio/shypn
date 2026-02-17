"""
Sweep header generator.

Orchestrates collection of all metadata sections and generates
complete CSV headers for parameter sweep experiments.
"""

from typing import Dict, Any, Optional, List, Type
from datetime import datetime
import json
from pathlib import Path

from .base import MetadataSection, MetadataHeader
from .model import ModelMetadata
from .sweep import SweepConfiguration
from .experiment import ExperimentMetadata
from .conservation import ConservationLaws, ValidationFlags
from .properties import DoseResponseMetrics, ParametrizationState
from .temporal import TemporalMetadata, ReferenceMetadata


class SweepHeaderGenerator:
    """
    Generates complete metadata headers for sweep experiment CSV files.
    
    This class orchestrates the collection of all metadata sections,
    validates them, and generates the final header text.
    """
    
    DEFAULT_SECTIONS: List[Type[MetadataSection]] = [
        ModelMetadata,
        SweepConfiguration,
        ExperimentMetadata,  # Experiment-specific details (NEW - prominent position)
        ParametrizationState,
        ConservationLaws,
        ValidationFlags,
        DoseResponseMetrics,
        TemporalMetadata,
        ReferenceMetadata
    ]
    
    def __init__(
        self,
        sections: Optional[List[Type[MetadataSection]]] = None
    ):
        """
        Initialize generator.
        
        Args:
            sections: List of MetadataSection classes to include.
                     If None, uses DEFAULT_SECTIONS.
        """
        self.section_classes = sections or self.DEFAULT_SECTIONS
        self.header = MetadataHeader()
        self.context: Dict[str, Any] = {}
        
    def set_context(self, context: Dict[str, Any]) -> None:
        """
        Set the context dictionary containing all required information.
        
        Args:
            context: Dictionary with model, simulation config, etc.
        """
        self.context = context
    
    def generate(
        self,
        context: Optional[Dict[str, Any]] = None
    ) -> MetadataHeader:
        """
        Generate complete metadata header.
        
        Args:
            context: Optional context dict (uses stored context if not provided)
            
        Returns:
            MetadataHeader instance
        """
        if context:
            self.context = context
        
        if not self.context:
            raise ValueError("Context must be set before generating header")
        
        # Create new header
        self.header = MetadataHeader()
        
        # Collect all sections
        for section_class in self.section_classes:
            section = section_class()
            
            try:
                section.collect(self.context)
                self.header.add_section(section)
            except Exception as e:
                # Skip section if collection fails (may be optional)
                # Suppress verbose warnings for expected skips (e.g., ModelMetadata for snapshots)
                if "skipped" not in str(e).lower():
                    print(f"Warning: Failed to collect {section_class.__name__}: {e}")
        
        return self.header
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate all collected metadata.
        
        Returns:
            (is_valid, error_messages) tuple
        """
        return self.header.validate_all()
    
    def to_header_text(self) -> str:
        """
        Convert metadata to CSV header comment text.
        
        Returns:
            Header text with '# ' prefix on each line
        """
        return self.header.to_header_text()
    
    def save_metadata_json(self, output_path: str) -> None:
        """
        Save metadata to JSON file for programmatic access.
        
        Args:
            output_path: Path to output JSON file
        """
        Path(output_path).write_text(self.header.to_json())
    
    @classmethod
    def create_sweep_header(
        cls,
        model_path: str,
        model: Optional[Dict[str, Any]] = None,
        sweep_config: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> str:
        """
        Convenience method to create header from common parameters.
        
        Args:
            model_path: Path to .shy model file
            model: Loaded model dictionary (loads from file if None)
            sweep_config: Sweep configuration dict
            **kwargs: Additional context fields
            
        Returns:
            Header text string
        """
        # Load model if not provided
        if model is None:
            with open(model_path, 'r') as f:
                model = json.load(f)
        
        # Build context
        context = {
            'model_path': model_path,
            'model': model,
            **(sweep_config or {}),
            **kwargs
        }
        
        # Generate header
        generator = cls()
        generator.set_context(context)
        generator.generate()
        
        # Validate
        is_valid, errors = generator.validate()
        if not is_valid:
            print("Warning: Header validation failed:")
            for error in errors:
                print(f"  - {error}")
        
        return generator.to_header_text()
    
    @classmethod
    def update_header_post_execution(
        cls,
        csv_path: str,
        final_state: Optional[Dict[str, Any]] = None,
        trajectory_data: Optional[Dict[str, Any]] = None,
        inferred_properties: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Update CSV header with post-execution information.
        
        This can be called after simulation completes to add:
        - Final state conservation laws
        - Validation flags from trajectory
        - Inferred dose-response properties
        
        Args:
            csv_path: Path to CSV file to update
            final_state: Final concentrations dict
            trajectory_data: Full trajectory data
            inferred_properties: Computed properties (homeostasis, Hill params)
        """
        # Read existing CSV
        csv_path = Path(csv_path)
        lines = csv_path.read_text().split('\n')
        
        # Find header end
        header_end = 0
        for i, line in enumerate(lines):
            if not line.startswith('#'):
                header_end = i
                break
        
        # Parse existing header (simplified - just extract context)
        # In production, would parse full header
        
        # Create context with updates
        context = {
            'final_state': final_state,
            'trajectory_data': trajectory_data,
            **(inferred_properties or {})
        }
        
        # Re-generate sections that need updating
        sections_to_update = [ConservationLaws, ValidationFlags, DoseResponseMetrics]
        
        # This is a simplified version - full implementation would:
        # 1. Parse existing header
        # 2. Update specific sections
        # 3. Re-write file with updated header
        
        pass  # TODO: Implement full update logic


class MinimalHeaderLoader:
    """
    Minimal loader for reading sweep CSV headers.
    
    Designed to be fast and lightweight for UI components.
    """
    
    @staticmethod
    def load_header(csv_path: str) -> MetadataHeader:
        """
        Load metadata header from CSV file.
        
        Args:
            csv_path: Path to CSV file
            
        Returns:
            MetadataHeader instance
        """
        header = MetadataHeader()
        
        with open(csv_path, 'r') as f:
            lines = []
            for line in f:
                if not line.startswith('#'):
                    break
                # Remove '# ' prefix
                lines.append(line[2:].strip())
        
        # Parse sections
        current_section = None
        
        for line in lines:
            if not line or line.startswith('='):
                continue
            
            if line.startswith('[') and line.endswith(']'):
                # New section
                section_name = line[1:-1]
                # Create appropriate section class
                current_section = MinimalHeaderLoader._create_section(section_name)
                if current_section:
                    header.add_section(current_section)
            
            elif current_section and ':' in line:
                # Field in current section
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.split('#')[0].strip()  # Remove comment
                
                MinimalHeaderLoader._parse_and_add_field(current_section, key, value)
        
        return header
    
    @staticmethod
    def _create_section(section_name: str) -> Optional[MetadataSection]:
        """Create appropriate section instance from name."""
        section_map = {
            'MODEL IDENTIFICATION': ModelMetadata,
            'SWEEP CONFIGURATION': SweepConfiguration,
            'EXPERIMENT DETAILS': ExperimentMetadata,
            'PARAMETRIZATION STATE': ParametrizationState,
            'CONSERVATION LAWS': ConservationLaws,
            'VALIDATION FLAGS': ValidationFlags,
            'INFERRED PROPERTIES': DoseResponseMetrics,
            'TEMPORAL METADATA': TemporalMetadata,
            'REFERENCES': ReferenceMetadata
        }
        
        section_class = section_map.get(section_name)
        return section_class() if section_class else None
    
    @staticmethod
    def _parse_and_add_field(
        section: MetadataSection,
        key: str,
        value_str: str
    ) -> None:
        """Parse field value and add to section."""
        # Try to parse as appropriate type
        value: Any = value_str
        
        # Boolean
        if value_str in ('YES', 'NO', 'TRUE', 'FALSE'):
            value = value_str in ('YES', 'TRUE')
        
        # Number
        elif value_str.replace('.', '').replace('-', '').isdigit():
            value = float(value_str) if '.' in value_str else int(value_str)
        
        # Datetime
        elif 'T' in value_str and value_str.endswith('Z'):
            try:
                value = datetime.fromisoformat(value_str[:-1])
            except:
                pass
        
        section.add_field(key, value)


# Alias for convenience
load_header = MinimalHeaderLoader.load_header
