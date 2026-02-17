"""
Model identification metadata section.

Captures model file information, version, and provenance.
"""

from typing import Dict, Any, Optional
import hashlib
import json
from pathlib import Path
from datetime import datetime

from .base import MetadataSection


class ModelMetadata(MetadataSection):
    """Metadata about the model used in the sweep experiment."""
    
    def __init__(self):
        super().__init__("Model Identification")
        
    def collect(self, context: Dict[str, Any]) -> None:
        """
        Collect model metadata from context.
        
        Expected context keys:
            - model_path: Path to .shy file (None for experiment snapshots)
            - model: Loaded model dictionary
        """
        model_path = context.get('model_path')
        model = context.get('model')
        
        # Skip ModelMetadata for experiment snapshots (no source file)
        if not model_path:
            raise ValueError("ModelMetadata skipped: no source file (experiment snapshot)")
        
        if not model:
            raise ValueError("Context must contain 'model'")
        
        # Basic identification
        path = Path(model_path)
        self.add_field('Model_Name', path.stem)
        self.add_field('Model_Path', str(path.relative_to(Path.cwd()) if path.is_absolute() else path))
        
        # File hash for integrity checking
        model_hash = self._compute_model_hash(model_path)
        self.add_field('Model_Hash', f'sha256:{model_hash[:16]}', 'First 16 chars of SHA-256')
        
        # Modification time
        mtime = datetime.fromtimestamp(path.stat().st_mtime)
        self.add_field('Model_Modified', mtime)
        
        # Model type/formalism
        formalism = model.get('formalism', 'Signal_Hierarchical_Petri_Net')
        self.add_field('Formalism', formalism)
        
        # Version from model metadata
        version = model.get('metadata', {}).get('version', 'unknown')
        self.add_field('Version', version)
        
        # Model structure
        n_places = len(model.get('places', []))
        n_transitions = len(model.get('transitions', []))
        n_arcs = len(model.get('arcs', []))
        
        self.add_field('N_Places', n_places)
        self.add_field('N_Transitions', n_transitions)
        self.add_field('N_Arcs', n_arcs)
        
    def validate(self) -> tuple[bool, Optional[str]]:
        """Validate model metadata."""
        required = ['Model_Name', 'Model_Path', 'Model_Hash']
        
        for field in required:
            if field not in self._fields:
                return False, f"Missing required field: {field}"
        
        return True, None
    
    @staticmethod
    def _compute_model_hash(model_path: str) -> str:
        """Compute SHA-256 hash of model file."""
        sha256 = hashlib.sha256()
        
        with open(model_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        
        return sha256.hexdigest()
