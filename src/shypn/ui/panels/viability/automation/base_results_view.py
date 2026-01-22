#!/usr/bin/env python3
"""Base Results View - Abstract base class for result viewing components.

Provides common infrastructure for displaying and exporting experiment results.
Subclasses implement specific viewing modes (list, plot, table, etc.).

Author: Simão Eugénio
Date: January 22, 2026
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class BaseResultsView(Gtk.Box):
    """Abstract base class for result viewing components.
    
    Provides:
    - Common data storage (results dictionary)
    - Model reference for ID resolution
    - Callback registration (export, report)
    - Abstract methods for UI setup and result display
    
    Subclasses must implement:
    - setup_ui(): Build UI components
    - display_result(result_data): Display a single result
    - clear_results(): Clear all displayed results
    
    Attributes:
        results (dict): Experiment name -> results dictionary
        model: Optional model reference for ID->name resolution
        on_export_callback: Callback for export operations
        on_report_callback: Callback for report integration
    """
    
    def __init__(self, model=None):
        """Initialize base results view.
        
        Args:
            model: Optional model reference for resolving IDs to names
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        # Results data: experiment_name -> results_dict
        self.results = {}
        
        # Model reference for ID->name resolution
        self.model = model
        
        # Callbacks
        self.on_export_callback = None
        self.on_report_callback = None
        
        # Build UI (subclass implements)
        self.setup_ui()
    
    def setup_ui(self):
        """Build UI components.
        
        Subclasses must implement this to construct their specific UI.
        Should create all widgets and pack them into self (Gtk.Box).
        """
        raise NotImplementedError("Subclass must implement setup_ui()")
    
    def display_result(self, result_data):
        """Display a result.
        
        Subclasses must implement this to show result data in their view.
        
        Args:
            result_data (dict): Result dictionary with keys:
                - name (str): Experiment name
                - replicates (int): Number of replicates
                - elapsed_time (float): Execution time in seconds
                - status (str): 'success', 'error', etc.
                - data: Experiment-specific result data
        """
        raise NotImplementedError("Subclass must implement display_result()")
    
    def clear_results(self):
        """Clear all displayed results.
        
        Subclasses must implement this to remove all results from view.
        Should also clear self.results dictionary.
        """
        raise NotImplementedError("Subclass must implement clear_results()")
    
    def set_model(self, model):
        """Update model reference.
        
        Args:
            model: New model reference
        """
        self.model = model
    
    def add_result(self, name, result_data):
        """Add a result to the view.
        
        Stores result in dictionary and delegates display to subclass.
        
        Args:
            name (str): Experiment name (unique identifier)
            result_data (dict): Result data dictionary
        """
        self.results[name] = result_data
        self.display_result(result_data)
    
    def get_result(self, name):
        """Retrieve a result by name.
        
        Args:
            name (str): Experiment name
        
        Returns:
            dict: Result data or None if not found
        """
        return self.results.get(name)
    
    def get_all_results(self):
        """Get all results.
        
        Returns:
            dict: All results (name -> result_data)
        """
        return self.results.copy()
    
    def set_export_callback(self, callback):
        """Register export callback.
        
        Args:
            callback: Function(name, result_data, format_type) -> None
        """
        self.on_export_callback = callback
    
    def set_report_callback(self, callback):
        """Register report callback.
        
        Args:
            callback: Function(name, result_data) -> None
        """
        self.on_report_callback = callback
