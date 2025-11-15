#!/usr/bin/env python3
"""Metadata storage utilities for .shypn files.

This module provides utilities for saving and loading metadata to/from
.shypn model files. Integrates with the existing file format while
maintaining backward compatibility.

Author: Simão Eugénio
Date: 2025-11-15
"""
import json
from typing import Optional, Dict, Any
from pathlib import Path

from .model_metadata import ModelMetadata


class MetadataStorage:
    """Utilities for metadata persistence in .shypn files.
    
    Handles saving and loading ModelMetadata to/from .shypn files.
    Maintains compatibility with existing file format by adding
    metadata as a separate section.
    """
    
    @staticmethod
    def save_to_shypn_file(filepath: str, metadata: ModelMetadata) -> bool:
        """Save metadata to .shypn file.
        
        Adds or updates the 'metadata' section in an existing .shypn file.
        If the file doesn't exist, only metadata is saved (model will be
        added separately by the normal save process).
        
        Args:
            filepath: Path to .shypn file
            metadata: ModelMetadata instance to save
            
        Returns:
            True if save succeeded
        """
        try:
            file_path = Path(filepath)
            
            # Load existing file content if it exists
            if file_path.exists():
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                # New file - create minimal structure
                data = {
                    'version': '1.0',
                    'model': {},
                }
            
            # Add/update metadata section
            data['metadata'] = metadata.to_dict()
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            print(f"Error saving metadata to {filepath}: {e}")
            return False
    
    @staticmethod
    def load_from_shypn_file(filepath: str) -> Optional[ModelMetadata]:
        """Load metadata from .shypn file.
        
        Reads the 'metadata' section from a .shypn file if it exists.
        Returns None if file doesn't exist or has no metadata section.
        
        Args:
            filepath: Path to .shypn file
            
        Returns:
            ModelMetadata instance or None
        """
        try:
            file_path = Path(filepath)
            
            # Check if file exists
            if not file_path.exists():
                return None
            
            # Load file
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if metadata section exists
            if 'metadata' not in data:
                return None
            
            # Deserialize metadata
            metadata = ModelMetadata()
            metadata.from_dict(data['metadata'])
            
            return metadata
            
        except Exception as e:
            print(f"Error loading metadata from {filepath}: {e}")
            return None
    
    @staticmethod
    def has_metadata(filepath: str) -> bool:
        """Check if .shypn file contains metadata.
        
        Args:
            filepath: Path to .shypn file
            
        Returns:
            True if file exists and contains metadata section
        """
        try:
            file_path = Path(filepath)
            
            if not file_path.exists():
                return False
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            return 'metadata' in data and bool(data['metadata'])
            
        except Exception:
            return False
    
    @staticmethod
    def extract_basic_info(filepath: str) -> Dict[str, str]:
        """Extract basic model info for quick display.
        
        Reads only essential fields without loading full metadata.
        Useful for file lists and previews.
        
        Args:
            filepath: Path to .shypn file
            
        Returns:
            Dictionary with basic info (name, id, description)
        """
        try:
            file_path = Path(filepath)
            
            if not file_path.exists():
                return {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'metadata' not in data:
                return {}
            
            metadata_dict = data['metadata']
            basic = metadata_dict.get('basic', {})
            
            return {
                'name': basic.get('model_name', ''),
                'id': basic.get('model_id', ''),
                'description': basic.get('description', ''),
                'version': basic.get('version', ''),
            }
            
        except Exception:
            return {}
    
    @staticmethod
    def update_modification_history(filepath: str, action: str, description: str, user: str = "") -> bool:
        """Add modification record to file's metadata.
        
        Convenience method to add a modification record without loading
        entire metadata object.
        
        Args:
            filepath: Path to .shypn file
            action: Modification action type
            description: Description of modification
            user: Username (optional)
            
        Returns:
            True if update succeeded
        """
        try:
            # Load existing metadata
            metadata = MetadataStorage.load_from_shypn_file(filepath)
            
            if not metadata:
                # Create new metadata if doesn't exist
                metadata = ModelMetadata()
            
            # Add modification record
            metadata.add_modification(action, description, user)
            
            # Save back
            return MetadataStorage.save_to_shypn_file(filepath, metadata)
            
        except Exception as e:
            print(f"Error updating modification history: {e}")
            return False
    
    @staticmethod
    def initialize_metadata_from_model(filepath: str, model) -> ModelMetadata:
        """Initialize metadata from existing model object.
        
        Creates basic metadata by extracting information from the
        model object (places, transitions, arcs counts, etc.).
        
        Args:
            filepath: Path where model will be saved
            model: Model object (with places, transitions, arcs)
            
        Returns:
            Initialized ModelMetadata instance
        """
        metadata = ModelMetadata()
        
        # Try to get model name/id from model object
        if hasattr(model, 'name'):
            metadata.model_name = model.name or ""
        if hasattr(model, 'id'):
            metadata.model_id = model.id or ""
        
        # Add basic description from model structure
        if hasattr(model, 'places') and hasattr(model, 'transitions'):
            num_places = len(model.places) if model.places else 0
            num_transitions = len(model.transitions) if model.transitions else 0
            num_arcs = len(model.arcs) if hasattr(model, 'arcs') and model.arcs else 0
            
            metadata.description = (
                f"Petri net model with {num_places} places, "
                f"{num_transitions} transitions, and {num_arcs} arcs."
            )
        
        # Add creation record
        metadata.add_modification("created", f"Model created from file: {Path(filepath).name}")
        
        return metadata
