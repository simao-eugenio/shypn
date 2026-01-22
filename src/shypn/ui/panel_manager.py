#!/usr/bin/env python3
"""PanelManager - Coordinates panel attachment/floating and exclusive toggling.

Extracted from shypn.py as part of OOP compliance refactoring (Phase 1, Week 1).
Manages panel visibility, exclusive mode toggling, and dock/float state coordination.

Author: Simão Eugénio
Date: January 22, 2026 (Refactored from shypn.py)
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib


class PanelManager:
    """Manager for panel coordination and exclusive toggling.
    
    Responsibilities:
    - Panel visibility toggling (exclusive mode - only one panel at a time)
    - Dock/float state management
    - Stack visibility coordination
    - Integration with MasterPalette toggle buttons
    - Per-document panel handling (Pathway, Analyses, Report)
    
    Architecture:
    - Global panels: Files, Topology, Viability (one instance)
    - Per-document panels: Pathway, Analyses, Report (instance per model)
    - Exclusive mode: Activating one panel deactivates others
    
    Attributes:
        main_window: MainWindow instance
        master_palette: MasterPalette instance
        left_paned: Left Gtk.Paned for panel stack
        left_dock_stack: Gtk.Stack for docked panels
        model_canvas_loader: ModelCanvasLoader for per-document panels
        
        Panel loaders:
        - left_panel_loader: Files panel (global)
        - topology_panel_loader: Topology panel (global)
        - viability_panel_loader: Viability panel (global)
    """
    
    def __init__(self, main_window):
        """Initialize panel manager.
        
        Args:
            main_window (MainWindow): Main window instance
        """
        self.main_window = main_window
        
        # UI components (set externally after initialization)
        self.master_palette = None
        self.left_paned = None
        self.left_dock_stack = None
        self.model_canvas_loader = None
        
        # Global panel loaders
        self.left_panel_loader = None  # Files panel
        self.topology_panel_loader = None
        self.viability_panel_loader = None
        
        # Panel names for exclusive mode
        self.all_panels = ['files', 'pathways', 'analyses', 'topology', 'viability', 'report']
    
    def set_master_palette(self, master_palette):
        """Set master palette and register toggle callbacks.
        
        Args:
            master_palette: MasterPalette instance
        """
        self.master_palette = master_palette
        
        # Register toggle callbacks
        master_palette.register_toggle_callback('files', self.on_files_toggle)
        master_palette.register_toggle_callback('pathways', self.on_pathways_toggle)
        master_palette.register_toggle_callback('analyses', self.on_analyses_toggle)
        master_palette.register_toggle_callback('topology', self.on_topology_toggle)
        master_palette.register_toggle_callback('viability', self.on_viability_toggle)
        master_palette.register_toggle_callback('report', self.on_report_toggle)
    
    def set_left_panel_loader(self, loader):
        """Set Files panel loader."""
        self.left_panel_loader = loader
    
    def set_topology_panel_loader(self, loader):
        """Set Topology panel loader."""
        self.topology_panel_loader = loader
    
    def set_viability_panel_loader(self, loader):
        """Set Viability panel loader."""
        self.viability_panel_loader = loader
    
    def set_ui_components(self, left_paned, left_dock_stack, model_canvas_loader):
        """Set UI components for panel coordination.
        
        Args:
            left_paned: Gtk.Paned for left panel stack
            left_dock_stack: Gtk.Stack for docked panels
            model_canvas_loader: ModelCanvasLoader for per-document panels
        """
        self.left_paned = left_paned
        self.left_dock_stack = left_dock_stack
        self.model_canvas_loader = model_canvas_loader
    
    def _deactivate_all_except(self, active_panel):
        """Deactivate all panels except the specified one (exclusive mode).
        
        Args:
            active_panel (str): Panel name to keep active
        """
        if not self.master_palette:
            return
        
        for panel_name in self.all_panels:
            if panel_name != active_panel:
                self.master_palette.set_active(panel_name, False)
    
    def _show_panel_in_stack(self, loader):
        """Show panel in dock stack.
        
        Args:
            loader: Panel loader instance with show_in_stack() method
        """
        if loader:
            loader.show_in_stack()
            
            # Expand left paned if panel is hanged
            if hasattr(loader, 'is_hanged') and loader.is_hanged and self.left_paned:
                try:
                    self.left_paned.set_position(250)
                except Exception:
                    pass
    
    def _hide_panel_in_stack(self, loader):
        """Hide panel in dock stack.
        
        Args:
            loader: Panel loader instance with hide_in_stack() method
        """
        if loader:
            loader.hide_in_stack()
            
            # Hide stack when last panel hidden
            if self.left_dock_stack:
                self.left_dock_stack.set_visible(False)
            if self.left_paned:
                try:
                    self.left_paned.set_position(0)
                except Exception:
                    pass
    
    def on_files_toggle(self, is_active):
        """Handle Files panel toggle (exclusive mode).
        
        Args:
            is_active (bool): True if panel activated, False if deactivated
        """
        if not self.left_panel_loader:
            return
        
        if is_active:
            self._deactivate_all_except('files')
            self._show_panel_in_stack(self.left_panel_loader)
        else:
            self._hide_panel_in_stack(self.left_panel_loader)
    
    def on_pathways_toggle(self, is_active):
        """Handle Pathways panel toggle (per-document, exclusive mode).
        
        Args:
            is_active (bool): True if panel activated, False if deactivated
        """
        # Get current document's pathway loader
        drawing_area = self.model_canvas_loader.get_current_document() if self.model_canvas_loader else None
        if not drawing_area:
            return
        
        overlay_manager = self.model_canvas_loader.overlay_managers.get(drawing_area) if self.model_canvas_loader else None
        if not overlay_manager or not hasattr(overlay_manager, 'pathway_panel_loader'):
            return
        
        pathway_loader = overlay_manager.pathway_panel_loader
        if not pathway_loader:
            return
        
        if is_active:
            self._deactivate_all_except('pathways')
            self._show_panel_in_stack(pathway_loader)
        else:
            self._hide_panel_in_stack(pathway_loader)
    
    def on_analyses_toggle(self, is_active):
        """Handle Analyses panel toggle (per-document, exclusive mode).
        
        Args:
            is_active (bool): True if panel activated, False if deactivated
        """
        # Get current document's analyses loader
        drawing_area = self.model_canvas_loader.get_current_document() if self.model_canvas_loader else None
        if not drawing_area:
            return
        
        overlay_manager = self.model_canvas_loader.overlay_managers.get(drawing_area) if self.model_canvas_loader else None
        if not overlay_manager or not hasattr(overlay_manager, 'analyses_panel_loader'):
            return
        
        analyses_loader = overlay_manager.analyses_panel_loader
        if not analyses_loader:
            return
        
        if is_active:
            self._deactivate_all_except('analyses')
            self._show_panel_in_stack(analyses_loader)
        else:
            self._hide_panel_in_stack(analyses_loader)
    
    def on_topology_toggle(self, is_active):
        """Handle Topology panel toggle (exclusive mode).
        
        Args:
            is_active (bool): True if panel activated, False if deactivated
        """
        if not self.topology_panel_loader:
            return
        
        if is_active:
            self._deactivate_all_except('topology')
            self._show_panel_in_stack(self.topology_panel_loader.panel_loader)
        else:
            self._hide_panel_in_stack(self.topology_panel_loader.panel_loader)
    
    def on_viability_toggle(self, is_active):
        """Handle Viability panel toggle (exclusive mode).
        
        Args:
            is_active (bool): True if panel activated, False if deactivated
        """
        if not self.viability_panel_loader:
            return
        
        if is_active:
            self._deactivate_all_except('viability')
            self._show_panel_in_stack(self.viability_panel_loader.panel_loader)
        else:
            self._hide_panel_in_stack(self.viability_panel_loader.panel_loader)
    
    def on_report_toggle(self, is_active):
        """Handle Report panel toggle (per-document, exclusive mode).
        
        Args:
            is_active (bool): True if panel activated, False if deactivated
        """
        # Get current document's report loader
        drawing_area = self.model_canvas_loader.get_current_document() if self.model_canvas_loader else None
        if not drawing_area:
            return
        
        overlay_manager = self.model_canvas_loader.overlay_managers.get(drawing_area) if self.model_canvas_loader else None
        if not overlay_manager or not hasattr(overlay_manager, 'report_panel_loader'):
            return
        
        report_loader = overlay_manager.report_panel_loader
        if not report_loader:
            return
        
        if is_active:
            self._deactivate_all_except('report')
            self._show_panel_in_stack(report_loader)
        else:
            self._hide_panel_in_stack(report_loader)
    
    def on_files_float(self):
        """Handle Files panel float request."""
        if self.left_panel_loader and hasattr(self.left_panel_loader, 'float'):
            self.left_panel_loader.float()
    
    def on_files_attach(self):
        """Handle Files panel attach request."""
        if self.left_panel_loader and hasattr(self.left_panel_loader, 'hang'):
            self.left_panel_loader.hang()
    
    def on_pathways_float(self):
        """Handle Pathways panel float request (per-document)."""
        drawing_area = self.model_canvas_loader.get_current_document() if self.model_canvas_loader else None
        if not drawing_area:
            return
        
        overlay_manager = self.model_canvas_loader.overlay_managers.get(drawing_area) if self.model_canvas_loader else None
        if overlay_manager and hasattr(overlay_manager, 'pathway_panel_loader'):
            pathway_loader = overlay_manager.pathway_panel_loader
            if pathway_loader and hasattr(pathway_loader, 'float'):
                pathway_loader.float()
    
    def on_pathways_attach(self):
        """Handle Pathways panel attach request (per-document)."""
        drawing_area = self.model_canvas_loader.get_current_document() if self.model_canvas_loader else None
        if not drawing_area:
            return
        
        overlay_manager = self.model_canvas_loader.overlay_managers.get(drawing_area) if self.model_canvas_loader else None
        if overlay_manager and hasattr(overlay_manager, 'pathway_panel_loader'):
            pathway_loader = overlay_manager.pathway_panel_loader
            if pathway_loader and hasattr(pathway_loader, 'hang'):
                pathway_loader.hang()
    
    def on_analyses_float(self):
        """Handle Analyses panel float request (per-document)."""
        drawing_area = self.model_canvas_loader.get_current_document() if self.model_canvas_loader else None
        if not drawing_area:
            return
        
        overlay_manager = self.model_canvas_loader.overlay_managers.get(drawing_area) if self.model_canvas_loader else None
        if overlay_manager and hasattr(overlay_manager, 'analyses_panel_loader'):
            analyses_loader = overlay_manager.analyses_panel_loader
            if analyses_loader and hasattr(analyses_loader, 'float'):
                analyses_loader.float()
    
    def on_analyses_attach(self):
        """Handle Analyses panel attach request (per-document)."""
        drawing_area = self.model_canvas_loader.get_current_document() if self.model_canvas_loader else None
        if not drawing_area:
            return
        
        overlay_manager = self.model_canvas_loader.overlay_managers.get(drawing_area) if self.model_canvas_loader else None
        if overlay_manager and hasattr(overlay_manager, 'analyses_panel_loader'):
            analyses_loader = overlay_manager.analyses_panel_loader
            if analyses_loader and hasattr(analyses_loader, 'hang'):
                analyses_loader.hang()
    
    def on_topology_float(self):
        """Handle Topology panel float request."""
        if self.topology_panel_loader and hasattr(self.topology_panel_loader, 'float'):
            self.topology_panel_loader.float()
    
    def on_topology_attach(self):
        """Handle Topology panel attach request."""
        if self.topology_panel_loader and hasattr(self.topology_panel_loader, 'hang'):
            self.topology_panel_loader.hang()
    
    def on_viability_float(self):
        """Handle Viability panel float request."""
        if self.viability_panel_loader and hasattr(self.viability_panel_loader, 'float'):
            self.viability_panel_loader.float()
    
    def on_viability_attach(self):
        """Handle Viability panel attach request."""
        if self.viability_panel_loader and hasattr(self.viability_panel_loader, 'hang'):
            self.viability_panel_loader.hang()
    
    def on_report_float(self):
        """Handle Report panel float request (per-document)."""
        drawing_area = self.model_canvas_loader.get_current_document() if self.model_canvas_loader else None
        if not drawing_area:
            return
        
        overlay_manager = self.model_canvas_loader.overlay_managers.get(drawing_area) if self.model_canvas_loader else None
        if overlay_manager and hasattr(overlay_manager, 'report_panel_loader'):
            report_loader = overlay_manager.report_panel_loader
            if report_loader and hasattr(report_loader, 'float'):
                report_loader.float()
    
    def on_report_attach(self):
        """Handle Report panel attach request (per-document)."""
        drawing_area = self.model_canvas_loader.get_current_document() if self.model_canvas_loader else None
        if not drawing_area:
            return
        
        overlay_manager = self.model_canvas_loader.overlay_managers.get(drawing_area) if self.model_canvas_loader else None
        if overlay_manager and hasattr(overlay_manager, 'report_panel_loader'):
            report_loader = overlay_manager.report_panel_loader
            if report_loader and hasattr(report_loader, 'hang'):
                report_loader.hang()
