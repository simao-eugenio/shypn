#!/usr/bin/env python3
"""Unified Batch Results Saver - Standardized batch experiment persistence.

Provides consistent saving mechanism for batch experiments across:
- Swiss Palette simulation batch mode
- Viability Panel parameter sweep experiments

Features:
- Standardized folder structure: batch_{timestamp}/
- Rich metadata headers using SweepHeaderGenerator
- Individual replicate CSVs with time-series data
- Statistical summary JSON across replicates
- Configuration persistence for reproducibility

Architecture:
- Single source of truth for batch saving logic
- Reusable across different experiment types
- Backward compatible with existing saved batches

Author: Simão Eugénio
Date: February 15, 2026
"""

import os
import json
import csv
from datetime import datetime
from typing import Dict, Any, List, Optional, Set
from pathlib import Path


class BatchResultsSaver:
    """Standardized batch results saver for all experiment types.
    
    Handles:
    - Folder creation with timestamp
    - Configuration persistence (config.json)
    - Individual replicate CSVs with metadata headers
    - Statistical summary (summary.json)
    - Flexible metadata context
    
    Usage:
        # Swiss Palette batch mode
        saver = BatchResultsSaver(project_folder)
        saver.save_batch(
            results=batch_results,
            recorded_objects=recorded_ids,
            n_replicates=100,
            settings=simulation_settings,
            model=document_model
        )
        
        # Viability Panel experiments
        saver = BatchResultsSaver(project_folder, subfolder='experiments/results')
        saver.save_experiment(
            name='dose_response_EPO',
            result=experiment_result,
            metadata=metadata_context
        )
    """
    
    def __init__(
        self,
        base_path: str,
        subfolder: str = 'results',
        batch_prefix: str = 'batch'
    ):
        """Initialize batch results saver.
        
        Args:
            base_path: Base project folder path
            subfolder: Subfolder within base_path for results (e.g., 'results', 'experiments/results')
            batch_prefix: Prefix for batch folders (default: 'batch')
        """
        self.base_path = Path(base_path)
        self.subfolder = subfolder
        self.batch_prefix = batch_prefix
        self.batch_folder: Optional[Path] = None
        self.timestamp: Optional[str] = None
    
    def create_batch_folder(self, name_suffix: str = '') -> Path:
        """Create timestamped batch folder.
        
        Args:
            name_suffix: Optional suffix for batch name (e.g., experiment name)
        
        Returns:
            Path to created batch folder
        """
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if name_suffix:
            folder_name = f"{self.batch_prefix}_{name_suffix}_{self.timestamp}"
        else:
            folder_name = f"{self.batch_prefix}_{self.timestamp}"
        
        self.batch_folder = self.base_path / self.subfolder / folder_name
        self.batch_folder.mkdir(parents=True, exist_ok=True)
        
        return self.batch_folder
    
    def save_config(
        self,
        n_replicates: int,
        recorded_objects: List[str],
        settings: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Path:
        """Save batch configuration to config.json.
        
        Args:
            n_replicates: Number of replicates in batch
            recorded_objects: List of recorded object IDs
            settings: Simulation settings dict
            metadata: Optional additional metadata
        
        Returns:
            Path to saved config.json
        """
        if not self.batch_folder:
            raise RuntimeError("Batch folder not created. Call create_batch_folder() first.")
        
        config = {
            'timestamp': self.timestamp,
            'n_replicates': n_replicates,
            'recorded_objects': recorded_objects,
            'settings': settings
        }
        
        if metadata:
            config['metadata'] = metadata
        
        config_path = self.batch_folder / 'config.json'
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        return config_path
    
    def save_replicate_csv(
        self,
        replicate_id: int,
        time_points: List[float],
        place_data: Dict[str, List],
        transition_data: Dict[str, List],
        metadata_context: Optional[Dict[str, Any]] = None,
        use_metadata_header: bool = True
    ) -> Path:
        """Save individual replicate data to CSV with optional metadata header.
        
        Args:
            replicate_id: Replicate ID (0-indexed internally, 1-indexed in filename)
            time_points: List of time points
            place_data: Dict mapping place_id -> list of (time, tokens) tuples
            transition_data: Dict mapping transition_id -> list of (time, count) tuples
            metadata_context: Optional context for SweepHeaderGenerator
            use_metadata_header: Whether to include metadata header
        
        Returns:
            Path to saved CSV file
        """
        if not self.batch_folder:
            raise RuntimeError("Batch folder not created. Call create_batch_folder() first.")
        
        csv_path = self.batch_folder / f'run_{replicate_id + 1:03d}.csv'
        
        with open(csv_path, 'w', newline='') as f:
            # Write metadata header if requested
            if use_metadata_header and metadata_context:
                header_text = self._generate_metadata_header(
                    metadata_context,
                    replicate_id,
                    len(time_points)
                )
                f.write(header_text)
            
            writer = csv.writer(f)
            
            # Header row (column names)
            header = ['time'] + sorted(place_data.keys()) + sorted(transition_data.keys())
            writer.writerow(header)
            
            # Data rows
            for i, t in enumerate(time_points):
                row = [t]
                
                # Add place values - extract value from (time, tokens) tuples
                for obj_id in sorted(place_data.keys()):
                    if i < len(place_data[obj_id]):
                        _, tokens = place_data[obj_id][i]  # Extract tokens from tuple
                        row.append(tokens)
                    else:
                        row.append('')
                
                # Add transition values - extract value from (time, count) tuples
                for obj_id in sorted(transition_data.keys()):
                    if i < len(transition_data[obj_id]):
                        _, count = transition_data[obj_id][i]  # Extract count from tuple
                        row.append(count)
                    else:
                        row.append('')
                
                writer.writerow(row)
        
        return csv_path
    
    def save_summary(
        self,
        results: List[Dict[str, Any]],
        recorded_objects: Set[str],
        n_replicates: int
    ) -> Path:
        """Save statistical summary across replicates to summary.json.
        
        Args:
            results: List of result dicts from all replicates
            recorded_objects: Set of recorded object IDs
            n_replicates: Total number of replicates
        
        Returns:
            Path to saved summary.json
        """
        if not self.batch_folder:
            raise RuntimeError("Batch folder not created. Call create_batch_folder() first.")
        
        import numpy as np
        
        successful_results = [r for r in results if 'error' not in r]
        
        summary = {
            'timestamp': self.timestamp,
            'successful_replicates': len(successful_results),
            'total_replicates': n_replicates,
            'statistics': {}
        }
        
        # Calculate stats for each recorded object
        for obj_id in recorded_objects:
            obj_trajectories = []
            
            # Collect trajectories from all replicates
            for result in successful_results:
                if obj_id in result.get('place_data', {}):
                    # Extract just the values from (time, tokens) tuples
                    traj_tuples = result['place_data'][obj_id]
                    traj_values = [tokens for time, tokens in traj_tuples]
                    obj_trajectories.append(traj_values)
                elif obj_id in result.get('transition_data', {}):
                    # Extract just the values from (time, count) tuples
                    traj_tuples = result['transition_data'][obj_id]
                    traj_values = [count for time, count in traj_tuples]
                    obj_trajectories.append(traj_values)
            
            if obj_trajectories:
                # Filter out empty trajectories
                obj_trajectories = [traj for traj in obj_trajectories if len(traj) > 0]
                
                if obj_trajectories:  # Check again after filtering
                    # Convert to numpy array (pad to same length if needed)
                    max_len = max(len(traj) for traj in obj_trajectories)
                    padded = np.array([
                        traj + [traj[-1]] * (max_len - len(traj))
                        for traj in obj_trajectories
                    ])
                    
                    summary['statistics'][obj_id] = {
                        'mean': np.mean(padded, axis=0).tolist(),
                        'std': np.std(padded, axis=0).tolist(),
                        'min': np.min(padded, axis=0).tolist(),
                        'max': np.max(padded, axis=0).tolist(),
                        'final_mean': float(np.mean(padded[:, -1])),
                        'final_std': float(np.std(padded[:, -1]))
                    }
        
        summary_path = self.batch_folder / 'summary.json'
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2)
        
        return summary_path
    
    def _generate_metadata_header(
        self,
        context: Dict[str, Any],
        replicate_id: int,
        n_timepoints: int
    ) -> str:
        """Generate metadata header using SweepHeaderGenerator.
        
        Args:
            context: Context dict for metadata generation
            replicate_id: Current replicate ID
            n_timepoints: Number of time points in trajectory
        
        Returns:
            Header text with '# ' prefix
        """
        try:
            from shypn.metadata import SweepHeaderGenerator
            
            # Enhance context with replicate-specific info
            enhanced_context = dict(context)
            enhanced_context['current_replicate'] = replicate_id + 1
            enhanced_context['n_timepoints'] = n_timepoints
            
            generator = SweepHeaderGenerator()
            generator.set_context(enhanced_context)
            generator.generate()
            return generator.to_header_text()
        
        except Exception as e:
            # Fallback to minimal header if SweepHeaderGenerator fails
            print(f"Warning: Failed to generate metadata header: {e}")
            return self._generate_minimal_header(context, replicate_id)
    
    def _generate_minimal_header(
        self,
        context: Dict[str, Any],
        replicate_id: int
    ) -> str:
        """Generate minimal fallback header without SweepHeaderGenerator.
        
        Args:
            context: Context dict
            replicate_id: Current replicate ID
        
        Returns:
            Minimal header text
        """
        lines = [
            "=" * 76,
            "SHYPN BATCH EXPERIMENT DATA",
            f"Generated: {datetime.now().isoformat()}Z",
            "=" * 76,
            "",
            f"Replicate ID: {replicate_id + 1}",
            f"Timestamp: {self.timestamp}",
            "",
            "=" * 76,
            "DATA SECTION BEGINS",
            "=" * 76,
            ""
        ]
        return '\n'.join(f"# {line}" for line in lines) + '\n'
    
    def save_batch(
        self,
        results: List[Dict[str, Any]],
        recorded_objects: Set[str],
        n_replicates: int,
        settings: Dict[str, Any],
        model: Optional[Any] = None,
        name_suffix: str = '',
        metadata_context: Optional[Dict[str, Any]] = None
    ) -> Path:
        """Complete batch save operation (all-in-one method).
        
        Convenience method that handles:
        1. Folder creation
        2. Config save
        3. All replicate CSVs
        4. Summary statistics
        
        Args:
            results: List of result dicts from all replicates
            recorded_objects: Set of recorded object IDs
            n_replicates: Total number of replicates
            settings: Simulation settings dict
            model: Optional DocumentModel for metadata
            name_suffix: Optional suffix for batch folder name
            metadata_context: Optional additional metadata context
        
        Returns:
            Path to created batch folder
        """
        # Create batch folder
        batch_path = self.create_batch_folder(name_suffix)
        print(f"✓ Created batch folder: {batch_path}")
        
        # Save configuration
        self.save_config(n_replicates, list(recorded_objects), settings)
        print(f"✓ Saved config.json")
        
        # Build metadata context if model provided
        if metadata_context is None and model:
            metadata_context = self._build_metadata_context_from_model(
                model,
                settings,
                n_replicates,
                recorded_objects
            )
        
        # Save individual replicate CSVs
        csv_count = 0
        for result in results:
            if 'error' in result:
                continue  # Skip failed replicates
            
            replicate_id = result['replicate_id']
            time_points = result['time_points']
            place_data = result.get('place_data', {})
            transition_data = result.get('transition_data', {})
            
            self.save_replicate_csv(
                replicate_id,
                time_points,
                place_data,
                transition_data,
                metadata_context,
                use_metadata_header=True
            )
            csv_count += 1
        
        print(f"✓ Saved {csv_count} replicate CSVs")
        
        # Save summary statistics
        self.save_summary(results, recorded_objects, n_replicates)
        print(f"✓ Saved summary.json")
        
        return batch_path
    
    def _build_metadata_context_from_model(
        self,
        model: Any,
        settings: Dict[str, Any],
        n_replicates: int,
        recorded_objects: Set[str]
    ) -> Dict[str, Any]:
        """Build metadata context from DocumentModel.
        
        Args:
            model: DocumentModel instance
            settings: Simulation settings
            n_replicates: Number of replicates
            recorded_objects: Set of recorded object IDs
        
        Returns:
            Metadata context dict for SweepHeaderGenerator
        """
        # Convert DocumentModel to dict format for metadata generator
        if hasattr(model, 'to_dict'):
            model_dict = model.to_dict()
        else:
            model_dict = {
                'places': [p.to_dict() if hasattr(p, 'to_dict') else {} 
                          for p in getattr(model, 'places', [])],
                'transitions': [t.to_dict() if hasattr(t, 'to_dict') else {} 
                               for t in getattr(model, 'transitions', [])],
                'arcs': [a.to_dict() if hasattr(a, 'to_dict') else {} 
                        for a in getattr(model, 'arcs', [])],
                'formalism': getattr(model, 'formalism', 'Signal_Hierarchical_Petri_Net'),
                'metadata': {}
            }
        
        context = {
            'model_path': getattr(model, 'filepath', None),
            'model': model_dict,
            'n_replicates': n_replicates,
            'recorded_objects': list(recorded_objects),
            'simulation_config': settings,
            'phase': 'Batch_Mode'
        }
        
        return context
    
    def get_batch_path(self) -> Optional[Path]:
        """Get path to current batch folder.
        
        Returns:
            Path to batch folder, or None if not created yet
        """
        return self.batch_folder
    
    def get_timestamp(self) -> Optional[str]:
        """Get timestamp of current batch.
        
        Returns:
            Timestamp string, or None if batch not created yet
        """
        return self.timestamp


def save_swiss_palette_batch(
    results: List[Dict[str, Any]],
    recorded_objects: Set[str],
    n_replicates: int,
    simulation_settings: Any,
    model: Any,
    project_folder: Optional[str] = None
) -> str:
    """Convenience function for Swiss Palette batch save.
    
    Wrapper for backward compatibility with existing Swiss Palette code.
    
    Args:
        results: List of result dicts
        recorded_objects: Set of recorded object IDs
        n_replicates: Number of replicates
        simulation_settings: SimulationSettings object
        model: DocumentModel instance
        project_folder: Optional project folder (auto-detected if None)
    
    Returns:
        Path to created batch folder
    """
    # Auto-detect project folder if not provided
    if not project_folder:
        project_folder = _detect_project_folder(model, simulation_settings)
    
    # Convert settings object to dict
    settings_dict = {
        'duration': getattr(simulation_settings, 'duration', 0),
        'time_units': str(getattr(simulation_settings, 'time_units', 'SECONDS')),
        'dt_auto': getattr(simulation_settings, 'dt_auto', True),
        'use_tau_leaping': getattr(simulation_settings, 'use_tau_leaping', False),
        'tau_epsilon': getattr(simulation_settings, 'tau_epsilon', 0.03)
    }
    
    # Create saver and save batch
    saver = BatchResultsSaver(project_folder)
    batch_path = saver.save_batch(
        results=results,
        recorded_objects=recorded_objects,
        n_replicates=n_replicates,
        settings=settings_dict,
        model=model
    )
    
    return str(batch_path)


def _detect_project_folder(model: Any, simulation_settings: Any) -> str:
    """Detect project folder from model filepath.
    
    Args:
        model: DocumentModel instance
        simulation_settings: SimulationSettings instance from controller (session-specific)
    
    Returns:
        Project folder path
    """
    # Check simulation_settings for batch_output_folder (session-specific, not model-dependent)
    if simulation_settings and hasattr(simulation_settings, 'batch_output_folder'):
        if simulation_settings.batch_output_folder:
            return simulation_settings.batch_output_folder
    
    # Try to detect from model filepath
    if hasattr(model, 'filepath') and model.filepath:
        model_path = model.filepath
        path_parts = model_path.split(os.sep)
        
        # Look for 'projects' in path (workspace/projects/{project}/...)
        if 'projects' in path_parts:
            projects_idx = path_parts.index('projects')
            if projects_idx + 1 < len(path_parts):
                # Project folder is up to and including project name
                return os.sep.join(path_parts[:projects_idx + 2])
    
    # Final fallback: use workspace/results/
    current_dir = os.path.dirname(os.path.abspath(__file__))
    repo_root = os.path.normpath(os.path.join(current_dir, '..', '..'))
    return os.path.join(repo_root, 'workspace')
