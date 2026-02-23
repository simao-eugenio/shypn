#!/usr/bin/env python3
"""Experiment snapshot management for viability panel.

Manages multiple parameter configurations (snapshots) that can be
saved, loaded, and switched between. Each snapshot captures the
current state of parameter TreeViews (places, transitions, arcs).

Author: Simão Eugénio
Date: November 13, 2025
"""

import json
from datetime import datetime
from .automation.property_path_parser import parse_property_path


class ExperimentSnapshot:
    """Single parameter configuration snapshot.
    
    Captures/restores values from existing TreeViews without changing UI.
    Each snapshot represents one experiment configuration that can be
    saved, loaded, and compared with others.
    """
    
    def __init__(self, name="Experiment 1"):
        """Initialize experiment snapshot.
        
        Args:
            name: Human-readable name for this experiment
        """
        self.name = name
        self.place_markings = {}     # {place_id: marking}
        self.arc_weights = {}         # {arc_id: weight}
        self.transition_rates = {}    # {trans_id: rate}
        self.results = None           # SimulationResults after run
        self.timestamp = datetime.now().isoformat()
        self.notes = ""               # Optional user notes
        self.is_stale = False         # True if tables modified after capture
        self.swept_parameter = None   # {type: 'places'|'transitions'|'arcs', id: str, name: str} or None
        
        # New: Generic property overrides (property path → value)
        # Takes precedence over legacy dicts (place_markings, transition_rates, arc_weights)
        # Format: {"P1.initial_marking": 100.0, "T5.volume_threshold": 1.0, "A3.threshold": 50.0}
        self.property_overrides = {}  # {property_path: value}
        
    def capture_from_treeviews(self, places_store, transitions_store, arcs_store):
        """Read current parameter values from existing TreeViews.
        
        Args:
            places_store: Gtk.ListStore from Places tab
            transitions_store: Gtk.ListStore from Transitions tab
            arcs_store: Gtk.ListStore from Arcs tab
        """
        self.place_markings.clear()
        self.transition_rates.clear()
        self.arc_weights.clear()
        
        # Capture place markings (column 2 = marking)
        for row in places_store:
            place_id = row[0]
            marking = row[2]
            self.place_markings[place_id] = marking
            
        # Capture transition rates (column 2 = rate, column 3 = formula)
        # For kinetic formulas, use the formula string; otherwise use numeric rate
        for row in transitions_store:
            trans_id = row[0]
            rate = row[2]
            # TreeModelRow doesn't support len(), but we can safely access column 3
            try:
                formula = row[3]
            except (IndexError, KeyError):
                formula = ""
            
            # Prefer formula over rate if formula exists
            if formula and str(formula).strip():
                self.transition_rates[trans_id] = str(formula)
            else:
                self.transition_rates[trans_id] = rate
            
        # Capture arc weights (column 3 = weight)
        for row in arcs_store:
            arc_id = row[0]
            weight = row[3]
            self.arc_weights[arc_id] = weight
        
        self.timestamp = datetime.now().isoformat()
    
    def apply_to_treeviews(self, places_store, transitions_store, arcs_store):
        """Write snapshot values back to existing TreeViews.
        
        Args:
            places_store: Gtk.ListStore from Places tab
            transitions_store: Gtk.ListStore from Transitions tab
            arcs_store: Gtk.ListStore from Arcs tab
        """
        # Update place markings
        for row in places_store:
            place_id = row[0]
            if place_id in self.place_markings:
                row[2] = self.place_markings[place_id]
                
        # Update transition rates
        for row in transitions_store:
            trans_id = row[0]
            if trans_id in self.transition_rates:
                row[2] = self.transition_rates[trans_id]
                
        # Update arc weights
        for row in arcs_store:
            arc_id = row[0]
            if arc_id in self.arc_weights:
                row[3] = self.arc_weights[arc_id]
    
    def to_dict(self):
        """Serialize snapshot to dictionary for export.
        
        Returns:
            dict: Serializable snapshot data
        """
        return {
            'name': self.name,
            'place_markings': self.place_markings,
            'arc_weights': self.arc_weights,
            'transition_rates': self.transition_rates,
            'timestamp': self.timestamp,
            'notes': self.notes,
            'property_overrides': self.property_overrides  # New: generic property storage
        }
    
    @classmethod
    def from_dict(cls, data):
        """Deserialize snapshot from dictionary.
        
        Args:
            data: Dictionary from to_dict()
            
        Returns:
            ExperimentSnapshot: Restored snapshot
        """
        snapshot = cls(data['name'])
        snapshot.place_markings = data.get('place_markings', {})
        snapshot.arc_weights = data.get('arc_weights', {})
        snapshot.transition_rates = data.get('transition_rates', {})
        snapshot.timestamp = data.get('timestamp', datetime.now().isoformat())
        snapshot.notes = data.get('notes', '')
        snapshot.property_overrides = data.get('property_overrides', {})  # New: load property overrides
        return snapshot
    
    def __repr__(self):
        return f"ExperimentSnapshot(name='{self.name}', timestamp='{self.timestamp}')"


class ExperimentManager:
    """Manages multiple experiment snapshots.
    
    Provides add/remove/copy operations and import/export functionality.
    Works with existing ViabilityPanel TreeViews to save/restore parameter
    configurations without replacing the UI.
    """
    
    def __init__(self):
        """Initialize experiment manager."""
        self.snapshots = []           # List of ExperimentSnapshot
        self.active_index = 0         # Currently selected snapshot
        self.swept_parameters = {}    # {snapshot_index: {type, id, name, range}}
        
    def mark_baseline_stale(self):
        """Mark baseline snapshot as stale (needs resync from tables)."""
        if self.snapshots:
            # Mark all snapshots as stale since they depend on baseline
            for snapshot in self.snapshots:
                snapshot.is_stale = True
    
    def sync_baseline_from_tables(self, places_store, transitions_store, arcs_store):
        """Re-capture baseline snapshot from current table values.
        
        Args:
            places_store: Gtk.ListStore from Places tab
            transitions_store: Gtk.ListStore from Transitions tab
            arcs_store: Gtk.ListStore from Arcs tab
            
        Returns:
            bool: True if baseline was updated
        """
        if not self.snapshots:
            return False
        
        # Update baseline (first snapshot)
        baseline = self.snapshots[0]
        baseline.capture_from_treeviews(places_store, transitions_store, arcs_store)
        baseline.is_stale = False
        
        # Mark sweep snapshots as needing regeneration
        for i, snapshot in enumerate(self.snapshots[1:], start=1):
            snapshot.is_stale = True
        
        return True
    
    def get_swept_parameter_info(self, snapshot_index):
        """Get information about which parameter is being swept for a snapshot.
        
        Args:
            snapshot_index: Index of snapshot
            
        Returns:
            dict or None: {type, id, name, range} or None if not a sweep snapshot
        """
        return self.swept_parameters.get(snapshot_index)
        
    def add_snapshot(self, name=None):
        """Create new experiment snapshot.
        
        Args:
            name: Optional name (auto-generated if None)
            
        Returns:
            ExperimentSnapshot: Newly created snapshot
        """
        if name is None:
            name = f"Experiment {len(self.snapshots) + 1}"
        
        snapshot = ExperimentSnapshot(name)
        self.snapshots.append(snapshot)
        self.active_index = len(self.snapshots) - 1
        return snapshot
    
    def get_active_snapshot(self):
        """Get currently active snapshot.
        
        Returns:
            ExperimentSnapshot or None: Active snapshot or None if no snapshots
        """
        if not self.snapshots or self.active_index >= len(self.snapshots):
            return None
        return self.snapshots[self.active_index]
    
    def switch_to(self, index):
        """Switch active snapshot and return it.
        
        Args:
            index: Index of snapshot to activate
            
        Returns:
            ExperimentSnapshot or None: Activated snapshot or None if invalid index
        """
        if 0 <= index < len(self.snapshots):
            self.active_index = index
            return self.snapshots[index]
        return None
    
    def remove_snapshot(self, index):
        """Remove snapshot at index.
        
        Args:
            index: Index of snapshot to remove
            
        Returns:
            bool: True if removed, False if invalid index
        """
        if 0 <= index < len(self.snapshots):
            del self.snapshots[index]
            
            # Adjust active index if needed
            if self.active_index >= len(self.snapshots):
                self.active_index = max(0, len(self.snapshots) - 1)
            
            return True
        return False
    
    def copy_snapshot(self, source_index):
        """Duplicate snapshot for variation.
        
        Args:
            source_index: Index of snapshot to duplicate
            
        Returns:
            ExperimentSnapshot or None: Duplicated snapshot or None if invalid index
        """
        if 0 <= source_index < len(self.snapshots):
            source = self.snapshots[source_index]
            
            # Create copy
            copy_snapshot = ExperimentSnapshot(f"{source.name} (Copy)")
            copy_snapshot.place_markings = source.place_markings.copy()
            copy_snapshot.arc_weights = source.arc_weights.copy()
            copy_snapshot.transition_rates = source.transition_rates.copy()
            copy_snapshot.notes = source.notes
            
            # Add to list
            self.snapshots.append(copy_snapshot)
            self.active_index = len(self.snapshots) - 1
            
            return copy_snapshot
        return None
    
    def rename_snapshot(self, index, new_name):
        """Rename snapshot at index.
        
        Args:
            index: Index of snapshot to rename
            new_name: New name for snapshot
            
        Returns:
            bool: True if renamed, False if invalid index
        """
        if 0 <= index < len(self.snapshots):
            self.snapshots[index].name = new_name
            return True
        return False
    
    def get_snapshot_names(self):
        """Get list of all snapshot names.
        
        Returns:
            list: Snapshot names in order
        """
        return [s.name for s in self.snapshots]
    
    def _modify_rate_formula(self, original_rate, new_value):
        """Modify rate formula by replacing numeric coefficient with new value.
        
        Args:
            original_rate: Original rate (can be numeric or formula string)
            new_value: New coefficient value to use
            
        Returns:
            Modified rate (numeric if original was numeric, formula string if original was formula)
        """
        import re
        
        # If original is numeric (not a formula), just return the new value
        if not isinstance(original_rate, str) or not original_rate.strip():
            return new_value
        
        original_str = str(original_rate).strip()
        
        # Try to parse as simple number
        try:
            float(original_str)
            # It's just a number, replace with new value
            return new_value
        except ValueError:
            pass
        
        # It's a formula string - try to replace leading coefficient
        # Patterns to match:
        # "0.5*NAD" -> "4.5*NAD"
        # "0.5 * NAD" -> "4.5 * NAD"
        # "NAD*0.5" -> "NAD*4.5"
        # "(0.5)*NAD" -> "(4.5)*NAD"
        
        # Try to find coefficient at start: "0.5*..." or "0.5 *..."
        match = re.match(r'^([\d.]+)(\s*\*)', original_str)
        if match:
            old_coefficient = match.group(1)
            whitespace_and_operator = match.group(2)  # Captures " *" or "*"
            # Replace the full matched pattern (coefficient + whitespace + operator)
            old_pattern = old_coefficient + whitespace_and_operator
            new_pattern = str(new_value) + whitespace_and_operator
            modified = original_str.replace(old_pattern, new_pattern, 1)
            return modified
        
        # Try to find coefficient after multiplication: "...*0.5"
        match = re.search(r'\*\s*([\d.]+)$', original_str)
        if match:
            old_coefficient = match.group(1)
            modified = re.sub(r'\*\s*[\d.]+$', f'*{new_value}', original_str)
            return modified
        
        # If no coefficient found, prepend new coefficient: "NAD" -> "4.5*NAD"
        modified = f'{new_value}*({original_str})'
        return modified
    
    def generate_sweep_snapshots(self, parameter_type, parameter_id, parameter_name, values, base_snapshot=None):
        """Generate multiple snapshots from parameter sweep.
        
        Args:
            parameter_type: Type of parameter ('places', 'transitions', 'arcs')
            parameter_id: ID of parameter to vary (internal key for matching)
            parameter_name: Name of parameter (for display in labels)
            values: List of values to test
            base_snapshot: Base snapshot to vary (uses active if None)
        
        Returns:
            int: Number of snapshots created
        """
        if base_snapshot is None:
            base_snapshot = self.get_active_snapshot()
            if base_snapshot is None:
                # Create default snapshot if none exists
                base_snapshot = self.add_snapshot("Baseline")
        
        # Parse parameter_id to extract object_id (e.g., "P1.initial_marking" -> "P1")
        # This handles both explicit paths ("P1.initial_marking") and implicit ("P1")
        object_id, property_name = parse_property_path(parameter_id)
        
        # Validate parameter exists in base snapshot (use ID for lookup)
        if parameter_type == 'places':
            param_dict = base_snapshot.place_markings
        elif parameter_type == 'transitions':
            param_dict = base_snapshot.transition_rates
        elif parameter_type == 'arcs':
            param_dict = base_snapshot.arc_weights
        else:
            raise ValueError(f"Invalid parameter_type: {parameter_type}")
        
        # Check if object_id exists in baseline snapshot
        if object_id not in param_dict:
            raise ValueError(f"Parameter ID '{parameter_id}' (name: '{parameter_name}') not found in {parameter_type}")

        
        # Get baseline value to check if it's a formula
        baseline_value = param_dict[object_id]
        
        # Generate snapshots for each value
        created_count = 0
        start_index = len(self.snapshots)  # Track where sweep starts
        
        for value in values:
            # Create snapshot name using display name (user-friendly)
            name = f"{parameter_name}={value:.4g}"
            
            # Create new snapshot
            snapshot = ExperimentSnapshot(name)
            snapshot.place_markings = base_snapshot.place_markings.copy()
            snapshot.arc_weights = base_snapshot.arc_weights.copy()
            snapshot.transition_rates = base_snapshot.transition_rates.copy()
            snapshot.notes = f"Sweep: {parameter_name} (ID: {parameter_id}) = {value}"
            
            # Store swept parameter info
            snapshot.swept_parameter = {
                'type': parameter_type,
                'id': parameter_id,
                'name': parameter_name,
                'value': value
            }
            
            # Modify the swept parameter using object_id (internal key)
            # For transitions with formulas, preserve the formula structure
            if parameter_type == 'places':
                snapshot.place_markings[object_id] = value
            elif parameter_type == 'transitions':
                # Use formula modification helper for transitions
                snapshot.transition_rates[object_id] = self._modify_rate_formula(baseline_value, value)
            elif parameter_type == 'arcs':
                snapshot.arc_weights[object_id] = value
            
            # Add to snapshots
            self.snapshots.append(snapshot)
            
            # Store sweep info for quick lookup
            snapshot_index = len(self.snapshots) - 1
            self.swept_parameters[snapshot_index] = {
                'type': parameter_type,
                'id': parameter_id,
                'name': parameter_name,
                'range': values,
                'current_value': value
            }
            
            created_count += 1
        
        return created_count
    
    def export_to_json(self, filepath):
        """Save all snapshots to JSON file.
        
        Args:
            filepath: Path to JSON file to create
        """
        data = {
            'version': '1.0',
            'created': datetime.now().isoformat(),
            'snapshots': [s.to_dict() for s in self.snapshots],
            'active_index': self.active_index
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def import_from_json(self, filepath):
        """Load snapshots from JSON file.
        
        Args:
            filepath: Path to JSON file to load
            
        Returns:
            bool: True if loaded successfully, False on error
        """
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
            
            # Validate version (future-proofing)
            version = data.get('version', '1.0')
            if version != '1.0':
                print(f"Warning: Unknown version {version}, attempting to load anyway")
            
            # Load snapshots
            self.snapshots = [
                ExperimentSnapshot.from_dict(s) 
                for s in data.get('snapshots', [])
            ]
            
            # Restore active index
            self.active_index = data.get('active_index', 0)
            if self.active_index >= len(self.snapshots):
                self.active_index = 0
            
            return True
            
        except Exception as e:
            print(f"Error loading experiments from {filepath}: {e}")
            return False
    
    def clear(self):
        """Remove all snapshots."""
        self.snapshots.clear()
        self.active_index = 0
    
    def __len__(self):
        """Return number of snapshots."""
        return len(self.snapshots)
    
    def __repr__(self):
        return f"ExperimentManager({len(self.snapshots)} snapshots, active={self.active_index})"
