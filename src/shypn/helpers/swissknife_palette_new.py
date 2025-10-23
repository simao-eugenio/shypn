#!/usr/bin/env python3
"""SwissKnifePalette - Refactored Modular Architecture.

Main coordinator class that integrates all modules:
- SwissKnifePaletteUI: Widget construction
- SwissKnifePaletteAnimator: Animation state machine
- SwissKnifePaletteController: Signal coordination
- SubPaletteRegistry: Plugin management
- ParameterPanelManager: Universal parameter panel lifecycle (Phase 3)

This refactored version maintains 100% compatibility with the old API
while providing clean separation of concerns.

PHASE 3: Universal Parameter Panel Architecture
================================================
Parameter panels now slide UP above sub-palettes, maintaining constant
114px main palette height (50px sub-palette + 64px buttons).
"""

from gi.repository import Gtk, Gdk, GObject

from shypn.helpers.swissknife_palette_ui import SwissKnifePaletteUI
from shypn.helpers.swissknife_palette_animator import SwissKnifePaletteAnimator
from shypn.helpers.swissknife_palette_controller import SwissKnifePaletteController
from shypn.helpers.swissknife_palette_registry import SubPaletteRegistry
from shypn.helpers.parameter_panel_manager import ParameterPanelManager


class SwissKnifePalette(GObject.GObject):
    """Unified multi-mode palette for Petri net operations (Refactored).
    
    Provides mode-aware interface with animated sub-palettes.
    Supports both simple tool buttons and complex widget palettes.
    
    Signals:
        category-selected(str): Category button clicked
        tool-activated(str): Tool button clicked  
        sub-palette-shown(str): Sub-palette revealed (after animation)
        sub-palette-hidden(str): Sub-palette hidden (after animation)
        mode-change-requested(str): Mode change requested (edit/simulate)
        simulation-step-executed(float): Simulation step completed (forwarded)
        simulation-reset-executed(): Simulation reset (forwarded)
        simulation-settings-changed(): Simulation settings changed (forwarded)
    """
    
    __gsignals__ = {
        'category-selected': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'tool-activated': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'sub-palette-shown': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'sub-palette-hidden': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'mode-change-requested': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        # Forward simulation palette signals
        'simulation-step-executed': (GObject.SignalFlags.RUN_FIRST, None, (float,)),
        'simulation-reset-executed': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'simulation-settings-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, mode='edit', model=None, tool_registry=None):
        """Initialize SwissKnifePalette.
        
        Args:
            mode: 'edit' or 'simulate' mode
            model: PetriNetModel instance for widget palettes (required for simulation)
            tool_registry: Optional tool registry for custom tools. If None, uses default.
        """
        super().__init__()
        
        self.mode = mode
        self.model = model
        self.tool_registry = tool_registry or self._create_default_tool_registry()
        
        # Get configuration from tool registry
        self.categories = self.tool_registry.get_categories(mode)
        self.tools = self.tool_registry.get_all_tools()
        
        # Create modular components
        self.ui = SwissKnifePaletteUI(self.categories, self.tools)
        self.registry = SubPaletteRegistry(self.ui, self.categories, self.tools)
        
        # Build UI first
        self.ui.build()
        
        # Create all sub-palettes
        self.registry.create_all_sub_palettes(model)
        
        # Create layout settings loader (for parameter panel)
        self._create_layout_settings_loader()
        
        # Create animator with sub-palettes
        self.animator = SwissKnifePaletteAnimator(self.registry.get_all_sub_palettes())
        
        # PHASE 3: Create parameter panel manager
        self.parameter_manager = ParameterPanelManager(
            self.ui.main_container,
            self.ui.sub_palette_area
        )
        
        # Register parameter panels from widget palettes
        self._register_parameter_panels()
        
        # Create controller with UI, animator, and parameter manager
        self.controller = SwissKnifePaletteController(
            self.ui, 
            self.animator, 
            mode,
            self.parameter_manager  # Pass parameter manager for auto-hide
        )
        
        # Connect controller signals to forward them
        self._connect_controller_signals()
        
        # Connect tool signals
        self.controller.connect_tool_signals(self.tools)
        
        # Connect simulation signals if available
        self.registry.connect_simulation_signals(self)
        
        # Apply CSS
        self._apply_css()
    
    def _create_default_tool_registry(self):
        """Create default tool registry.
        
        Returns:
            ToolRegistry: Default tool registry with standard tools
        """
        from shypn.ui.swissknife_tool_registry import ToolRegistry
        return ToolRegistry()
    
    def _create_layout_settings_loader(self):
        """Create layout settings loader for parameter panel.
        
        Creates an instance of LayoutSettingsLoader to provide parameter
        panel for layout algorithms.
        """
        try:
            from shypn.helpers.layout_settings_loader import LayoutSettingsLoader
            self.layout_settings_loader = LayoutSettingsLoader()
        except Exception as e:
            import traceback
            print(f'Warning: Failed to create layout settings loader: {e}')
            traceback.print_exc()
            self.layout_settings_loader = None
    
    def _register_parameter_panels(self):
        """Register parameter panels from widget palettes.
        
        PHASE 3: Extract parameter panel factories from widget palettes
        and register them with the parameter panel manager.
        """
        # Register simulate category parameter panel (settings)
        simulate_loader = self.registry.get_widget_palette_instance('simulate')
        if simulate_loader and hasattr(simulate_loader, 'create_settings_panel'):
            self.parameter_manager.register_parameter_panel(
                'simulate',
                simulate_loader.create_settings_panel
            )
        
        # Register layout category parameter panel (settings)
        if self.layout_settings_loader and hasattr(self.layout_settings_loader, 'create_settings_panel'):
            self.parameter_manager.register_parameter_panel(
                'layout',
                self.layout_settings_loader.create_settings_panel
            )
    
    def _connect_controller_signals(self):
        """Connect controller signals to forward them."""
        self.controller.connect('category-selected', self._forward_signal, 'category-selected')
        self.controller.connect('tool-activated', self._forward_signal, 'tool-activated')
        self.controller.connect('sub-palette-shown', self._forward_signal, 'sub-palette-shown')
        self.controller.connect('sub-palette-hidden', self._forward_signal, 'sub-palette-hidden')
        self.controller.connect('mode-change-requested', self._forward_signal, 'mode-change-requested')
    
    def _forward_signal(self, controller, *args):
        """Forward controller signal.
        
        Args:
            controller: Controller instance
            *args: Signal arguments (last arg is signal name)
        """
        signal_name = args[-1]
        signal_args = args[:-1]
        self.emit(signal_name, *signal_args)
    
    # Simulation signal handlers (for forwarding)
    
    def _on_simulation_step(self, sim_palette, time):
        """Forward simulation step signal.
        
        Args:
            sim_palette: Simulation palette instance
            time: Current simulation time
        """
        self.emit('simulation-step-executed', time)
    
    def _on_simulation_reset(self, sim_palette):
        """Forward simulation reset signal.
        
        Args:
            sim_palette: Simulation palette instance
        """
        self.emit('simulation-reset-executed')
    
    def _on_simulation_settings_changed(self, sim_palette):
        """Forward simulation settings changed signal.
        
        Args:
            sim_palette: Simulation palette instance
        """
        self.emit('simulation-settings-changed')
    
    def _on_settings_toggle_requested(self, sim_palette):
        """Handle settings toggle request from simulation palette.
        
        PHASE 3: Toggle parameter panel via ParameterPanelManager.
        
        Args:
            sim_palette: Simulation palette instance
        """
        self.parameter_manager.toggle_panel('simulate')
    
    def _apply_css(self):
        """Apply CSS styles to palette."""
        css = b"""
        /* SwissKnifePalette Styles */
        
        .swissknife-container {
            background-color: rgba(40, 50, 60, 0.95);
            border-radius: 8px;
            padding: 0px;
        }
        
        .category-buttons {
            background-color: transparent;
        }
        
        .category-button {
            min-width: 80px;
            min-height: 36px;
            padding: 8px 16px;
            font-weight: bold;
            background-image: none;
            background-color: rgba(60, 70, 80, 0.8);
            border: 1px solid rgba(100, 110, 120, 0.5);
            border-radius: 4px;
            color: #e0e0e0;
        }
        
        .category-button:hover {
            background-color: rgba(80, 90, 100, 0.9);
            border-color: rgba(120, 130, 140, 0.7);
        }
        
        .category-button.active {
            background-color: rgba(100, 110, 120, 1.0);
            border-color: rgba(140, 150, 160, 0.9);
            color: #ffffff;
        }
        
        .sub-palette {
            background-color: rgba(50, 60, 70, 0.9);
            border-radius: 6px;
            padding: 4px;
        }
        """
        
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css)
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    # Public API (maintains compatibility with old interface)
    
    def get_widget(self):
        """Get the main palette widget.
        
        Returns:
            Gtk.Box: Main container widget
        """
        return self.ui.main_container
    
    def set_mode(self, mode):
        """Set palette mode.
        
        Args:
            mode: 'edit' or 'simulate'
        """
        self.mode = mode
        self.controller.set_mode(mode)
    
    def hide_all_sub_palettes(self):
        """Hide all sub-palettes (for mode switching)."""
        self.controller.force_hide_all()
    
    def get_simulate_palette_loader(self):
        """Get SimulateToolsPaletteLoader instance.
        
        Returns:
            SimulateToolsPaletteLoader instance or None
        """
        return self.registry.get_widget_palette_instance('simulate')


__all__ = ['SwissKnifePalette']
