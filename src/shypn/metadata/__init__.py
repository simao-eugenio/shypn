"""
SHYPN Metadata Module

Provides OOP framework for generating and parsing metadata headers
in CSV files from parameter sweep experiments.

Usage:
    from shypn.metadata import SweepHeaderGenerator
    
    # Generate header
    generator = SweepHeaderGenerator()
    context = {
        'model_path': 'model.shy',
        'model': model_dict,
        'sweep_parameter': 'P7.initial_marking',
        'sweep_range': (0, 5000),
        'sweep_step': 10,
        ...
    }
    generator.set_context(context)
    header = generator.generate()
    header_text = generator.to_header_text()
    
    # Load header
    from shypn.metadata import load_header
    header = load_header('experiment.csv')
"""

from .base import MetadataSection, MetadataHeader, EditableField
from .model import ModelMetadata
from .sweep import SweepConfiguration
from .experiment import ExperimentMetadata
from .conservation import ConservationLaws, ValidationFlags
from .properties import DoseResponseMetrics, ParametrizationState
from .temporal import TemporalMetadata, ReferenceMetadata
from .generator import SweepHeaderGenerator, MinimalHeaderLoader, load_header

__version__ = "1.0.0"

__all__ = [
    # Base classes
    'MetadataSection',
    'MetadataHeader',
    'EditableField',
    
    # Metadata sections
    'ModelMetadata',
    'SweepConfiguration',
    'ExperimentMetadata',
    'ConservationLaws',
    'ValidationFlags',
    'DoseResponseMetrics',
    'ParametrizationState',
    'TemporalMetadata',
    'ReferenceMetadata',
    
    # Generator and loader
    'SweepHeaderGenerator',
    'MinimalHeaderLoader',
    'load_header'
]
