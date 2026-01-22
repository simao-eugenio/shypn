#!/usr/bin/env python3
"""SHYPN Main Loader - Refactored Version (Proof of Concept).

This is the THIN LOADER demonstrating OOP compliance refactoring.
Reduces from 1,395 lines → ~150 lines by extracting MainWindow and PanelManager.

To test this version:
    python3 src/shypn_refactored.py

Author: Simão Eugénio
Date: January 22, 2026 (Refactored from shypn.py)
"""

import os
import sys
import logging
import warnings

# Configure logging
logging.basicConfig(level=logging.CRITICAL)
logging.getLogger('shypn').setLevel(logging.CRITICAL)

# Suppress warnings
warnings.filterwarnings('ignore', message='Unable to import Axes3D')
warnings.filterwarnings('ignore', message="'parseString' deprecated")

REPO_ROOT = os.path.normpath(os.path.join(os.path.dirname(__file__), '..'))
UI_PATH = os.path.join(REPO_ROOT, 'ui', 'main', 'main_window.ui')

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')

# Import cairo for foreign struct converters (conda compatibility)
try:
    gi.require_version('cairo', '1.0')
    from gi.repository import cairo as _gi_cairo  # noqa: F401
except (ImportError, ValueError):
    pass

from gi.repository import Gtk, Gdk, GLib, Gio

# Initialize Gdk early
Gdk.init(sys.argv)

# Wayland Error 71 suppression
if 'G_MESSAGES_DEBUG' not in os.environ:
    os.environ['G_MESSAGES_DEBUG'] = ''

# Import new OOP classes
from shypn.ui.main_window import MainWindow
from shypn.ui.panel_manager import PanelManager

# Import panel loaders
USE_FILE_PANEL = os.environ.get('SHYPN_USE_FILE_PANEL', '1') == '1'
if USE_FILE_PANEL:
    from shypn.helpers.file_panel_loader import create_left_panel
else:
    from shypn.helpers.left_panel_loader import create_left_panel

from shypn.helpers.topology_panel_loader import TopologyPanelLoader
from shypn.helpers.viability_panel_loader import ViabilityPanelLoader
from shypn.helpers.model_canvas_loader import create_model_canvas
from shypn.file import create_persistency_manager
from shypn.ui import MasterPalette


def main(argv=None):
    """Main entry point with refactored OOP architecture."""
    if argv is None:
        argv = sys.argv
    
    # Validate UI file
    if not os.path.exists(UI_PATH):
        logging.getLogger(__name__).error('Main UI file not found: %s', UI_PATH)
        sys.exit(2)
    
    # Create application
    app = Gtk.Application(
        application_id='org.shypn.dockdemo',
        flags=Gio.ApplicationFlags.HANDLES_OPEN
    )
    
    # File to open from command line
    file_to_open = None
    if len(argv) > 1:
        file_to_open = os.path.abspath(argv[1])
    
    def on_activate(a):
        """Application activation handler (REFACTORED - much shorter)."""
        
        # Create main window (handles geometry, Wayland, menu)
        window = MainWindow(a, UI_PATH, file_to_open)
        
        # Create panel manager (handles toggle/float/attach)
        panel_manager = PanelManager(window)
        window.panel_manager = panel_manager
        
        # Get UI components from builder
        builder = window.builder
        left_paned = builder.get_object('left_paned')
        left_dock_stack = builder.get_object('left_dock_stack')
        canvas_notebook = builder.get_object('canvas_notebook')
        main_box = builder.get_object('main_box')
        
        # Create persistency manager
        persistency_manager = create_persistency_manager()
        
        # Create model canvas loader
        model_canvas_loader = create_model_canvas(
            canvas_notebook,
            persistency_manager,
            window
        )
        
        # Create master palette
        master_palette = MasterPalette()
        master_palette_widget = master_palette.get_widget()
        
        # Add master palette to main box
        if main_box and master_palette_widget:
            main_box.pack_start(master_palette_widget, False, False, 0)
            main_box.reorder_child(master_palette_widget, 0)
        
        # Create global panels
        left_panel_loader = create_left_panel(
            left_dock_stack,
            persistency_manager,
            model_canvas_loader
        )
        
        topology_panel_loader = TopologyPanelLoader(
            left_dock_stack,
            model_canvas_loader
        )
        
        viability_panel_loader = ViabilityPanelLoader(
            left_dock_stack,
            model_canvas_loader
        )
        
        # Configure panel manager
        panel_manager.set_master_palette(master_palette)
        panel_manager.set_left_panel_loader(left_panel_loader)
        panel_manager.set_topology_panel_loader(topology_panel_loader)
        panel_manager.set_viability_panel_loader(viability_panel_loader)
        panel_manager.set_ui_components(left_paned, left_dock_stack, model_canvas_loader)
        
        # Wire window close event
        window.connect('delete-event', window.on_delete_event)
        
        # Show window
        window.show_all()
        
        # Apply maximized state after show (Wayland Error 71 prevention)
        window.apply_maximize_state()
    
    app.connect('activate', on_activate)
    return app.run(argv)


if __name__ == '__main__':
    sys.exit(main())
