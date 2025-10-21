"""Minimal Topology Panel Loader - Expander Design (NO BUTTONS).

Ultra-clean architecture:
- Inherits Wayland-safe operations from base
- Delegates business logic to controller
- Just loads UI and wires expander signals

Author: Simão Eugénio
Date: 2025-10-20
"""

import sys

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

from shypn.ui.topology_panel_base import TopologyPanelBase
from shypn.ui.topology_panel_controller import TopologyPanelController


class TopologyPanelLoader(TopologyPanelBase):
    """Minimal loader for Topology Panel (Expander Design).
    
    Responsibilities (MINIMAL):
    - Load UI
    - Get widget references (expanders + labels)
    - Connect expander signals to controller
    - Delegate all logic to controller
    
    NOT responsible for:
    - Analysis logic (handled by controller)
    - Business logic (handled by analyzers)
    - Results caching (handled by controller)
    - Highlighting (handled by Switch Palette)
    """
    
    def __init__(self, model):
        """Initialize topology panel loader.
        
        Args:
            model: The ShypnModel instance
        """
        # Store model
        self.model = model
        
        # Controller (created after UI loads)
        self.controller = None
        
        # Widget references (12 analyzers, 3 widgets each)
        self.expanders = {}       # GtkExpander widgets
        self.report_labels = {}   # GtkLabel widgets (for reports)
        self.scrolled_windows = {} # GtkScrolledWindow widgets (for dynamic vexpand)
        
        # Initialize base
        super().__init__()
        
        # Load UI
        self.load()
    
    def _init_widgets(self):
        """Get widget references for all 12 analyzers.
        
        Called by base class after UI loads.
        """
        # Analyzer names
        analyzers = [
            # Structural (4)
            'p_invariants',
            't_invariants',
            'siphons',
            'traps',
            # Graph (3)
            'cycles',
            'paths',
            'hubs',
            # Behavioral (5)
            'reachability',
            'boundedness',
            'liveness',
            'deadlocks',
            'fairness',
        ]
        
        # Get references for each analyzer
        for analyzer in analyzers:
            # GtkExpander widget
            expander = self.builder.get_object(f'{analyzer}_expander')
            if expander:
                self.expanders[analyzer] = expander
            else:
                print(f"⚠ Warning: Could not find expander for {analyzer}", file=sys.stderr)
            
            # GtkScrolledWindow widget (for dynamic vexpand control)
            scrolled = self.builder.get_object(f'{analyzer}_scrolled')
            if scrolled:
                self.scrolled_windows[analyzer] = scrolled
            else:
                print(f"⚠ Warning: Could not find scrolled window for {analyzer}", file=sys.stderr)
            
            # Report label (inside expander)
            report_label = self.builder.get_object(f'{analyzer}_report_label')
            if report_label:
                self.report_labels[analyzer] = report_label
            else:
                print(f"⚠ Warning: Could not find report label for {analyzer}", file=sys.stderr)
    
    def _connect_signals(self):
        """Connect expander signals to controller methods.
        
        Called by base class after widgets are initialized.
        """
        # Create controller with expanders, scrolled windows, and labels
        self.controller = TopologyPanelController(
            model=self.model,
            expanders=self.expanders,
            scrolled_windows=self.scrolled_windows,
            report_labels=self.report_labels,
        )
        
        # Connect expander 'notify::expanded' signals
        # When user clicks expander arrow, this fires
        for analyzer, expander in self.expanders.items():
            expander.connect('notify::expanded', self.controller.on_expander_toggled, analyzer)
        
        # Apply CSS styling for vertical tabs appearance
        self._apply_css_styling()
    
    def _apply_css_styling(self):
        """Apply CSS styling to give expanders a vertical tabs appearance."""
        css = b"""
        /* Topology Panel - Vertical Tabs Styling */
        
        /* Add BOLD VISIBLE borders to all expanders */
        #p_invariants_expander,
        #t_invariants_expander,
        #siphons_expander,
        #traps_expander,
        #cycles_expander,
        #paths_expander,
        #hubs_expander,
        #reachability_expander,
        #boundedness_expander,
        #liveness_expander,
        #deadlocks_expander,
        #fairness_expander {
            border: 2px solid #4a5568;
            border-radius: 6px;
            margin: 4px;
            padding: 8px;
            background-color: #f7fafc;
        }
        
        /* Highlight expanded expander - BOLD and CLEAR */
        #p_invariants_expander:checked,
        #t_invariants_expander:checked,
        #siphons_expander:checked,
        #traps_expander:checked,
        #cycles_expander:checked,
        #paths_expander:checked,
        #hubs_expander:checked,
        #reachability_expander:checked,
        #boundedness_expander:checked,
        #liveness_expander:checked,
        #deadlocks_expander:checked,
        #fairness_expander:checked {
            background-color: #e6f7ff;
            border-color: #1890ff;
            border-width: 3px;
            box-shadow: 0 0 0 1px #69c0ff;
        }
        """
        
        try:
            css_provider = Gtk.CssProvider()
            css_provider.load_from_data(css)
            
            # Apply globally to the screen (not just individual widgets)
            screen = Gdk.Screen.get_default()
            if screen:
                Gtk.StyleContext.add_provider_for_screen(
                    screen,
                    css_provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
            else:
                # Fallback: apply to individual expanders if no screen
                for expander in self.expanders.values():
                    context = expander.get_style_context()
                    context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        except Exception as e:
            print(f"Warning: Could not apply topology panel CSS styling: {e}", file=sys.stderr)


__all__ = ['TopologyPanelLoader']
