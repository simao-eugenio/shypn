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
            
        # Capture transition rates (column 2 = rate)
        for row in transitions_store:
            trans_id = row[0]
            rate = row[2]
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
            'notes': self.notes
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
