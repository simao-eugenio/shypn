"""Main window controller with Master Palette integration."""

import sys
from gi.repository import Gtk, GLib, GObject
from shypn.ui.panels import (
    FilesPanelController,
    AnalysesPanelController,
    PathwaysPanelController,
    TopologyPanelController,
)


class MainWindowController(GObject.GObject):
    """Controller for main window with Master Palette and embedded panels.
    
    Architecture:
    - Single monolithic window (no floating)
    - Master Palette (54px) controls panel visibility
    - All panels embedded in LEFT side via GtkRevealer + GtkStack
    - Wayland-safe (no widget reparenting)
    
    Signals:
        window-ready: Emitted when window is fully initialized
        panel-changed: Emitted when active panel changes (str: panel_name)
    """
    
    __gsignals__ = {
        'window-ready': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'panel-changed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }
    
    def __init__(self, builder: Gtk.Builder, master_palette):
        """Initialize main window controller.
        
        Args:
            builder: Gtk.Builder with main_window.ui loaded
            master_palette: MasterPalette instance
        """
        super().__init__()
        self.builder = builder
        self.master_palette = master_palette
        
        # UI widgets (populated in _get_widgets)
        self.window = None
        self.panels_revealer = None
        self.panels_stack = None
        self.left_paned = None
        self.main_workspace = None
        
        # Panel controllers
        self.panels = {}
        self.active_panel = None
        
        # State
        self._initialized = False
    
    def initialize(self):
        """Initialize main window and panels.
        
        Steps:
        1. Get widget references from builder
        2. Insert Master Palette
        3. Create panel controllers
        4. Wire Master Palette signals
        5. Set initial state (all panels hidden)
        """
        print("[MAIN_WINDOW] Initializing...", file=sys.stderr)
        
        try:
            # Step 1: Get widget references
            self._get_widgets()
            
            # Step 2: Insert Master Palette
            self._insert_master_palette()
            
            # Step 3: Create panel controllers
            self._create_panel_controllers()
            
            # Step 4: Wire Master Palette signals
            self._wire_master_palette()
            
            # Step 5: Set initial state
            self._set_initial_state()
            
            self._initialized = True
            print("[MAIN_WINDOW] Initialized successfully", file=sys.stderr)
            self.emit('window-ready')
            
        except Exception as e:
            print(f"[MAIN_WINDOW] ERROR: Failed to initialize: {e}", file=sys.stderr)
            raise
    
    def _get_widgets(self):
        """Get widget references from builder."""
        print("[MAIN_WINDOW] Getting widget references...", file=sys.stderr)
        
        self.window = self.builder.get_object('main_window')
        if not self.window:
            raise ValueError("main_window not found in UI")
        
        self.panels_revealer = self.builder.get_object('panels_revealer')
        if not self.panels_revealer:
            raise ValueError("panels_revealer not found in UI")
        
        self.panels_stack = self.builder.get_object('panels_stack')
        if not self.panels_stack:
            raise ValueError("panels_stack not found in UI")
        
        self.left_paned = self.builder.get_object('left_paned')
        if not self.left_paned:
            raise ValueError("left_paned not found in UI")
        
        self.main_workspace = self.builder.get_object('main_workspace')
        if not self.main_workspace:
            raise ValueError("main_workspace not found in UI")
        
        print("[MAIN_WINDOW] Widget references obtained", file=sys.stderr)
    
    def _insert_master_palette(self):
        """Insert Master Palette widget into window."""
        print("[MAIN_WINDOW] Inserting Master Palette...", file=sys.stderr)
        
        # TEMPORARILY disable Master Palette insertion to debug Error 71
        # master_palette_slot = self.builder.get_object('master_palette_slot')
        # if not master_palette_slot:
        #     raise ValueError("master_palette_slot not found in UI")
        # 
        # master_palette_widget = self.master_palette.get_widget()
        # master_palette_slot.pack_start(master_palette_widget, True, True, 0)
        # master_palette_widget.show_all()
        print("[MAIN_WINDOW] Skipping Master Palette insertion (debugging Error 71)", file=sys.stderr)
        
        print("[MAIN_WINDOW] Master Palette inserted", file=sys.stderr)
    
    def _create_panel_controllers(self):
        """Create panel controller instances."""
        print("[MAIN_WINDOW] Creating panel controllers...", file=sys.stderr)
        
        # TEMPORARILY disable ALL panels to debug Error 71
        # self.panels['files'] = FilesPanelController(self.builder)
        # self.panels['analyses'] = AnalysesPanelController(self.builder)
        # self.panels['pathways'] = PathwaysPanelController(self.builder)
        # self.panels['topology'] = TopologyPanelController(self.builder)
        print("[MAIN_WINDOW] Skipping ALL panels (debugging Error 71)", file=sys.stderr)
        
        # Initialize each panel
        for panel_name, panel_ctrl in self.panels.items():
            panel_ctrl.connect('panel-ready', self._on_panel_ready, panel_name)
            panel_ctrl.connect('panel-error', self._on_panel_error, panel_name)
            panel_ctrl.initialize()
        
        print(f"[MAIN_WINDOW] Created {len(self.panels)} panel controllers", file=sys.stderr)
    
    def _wire_master_palette(self):
        """Wire Master Palette signals to panel toggle handlers."""
        print("[MAIN_WINDOW] Wiring Master Palette signals...", file=sys.stderr)
        
        # TEMPORARILY disable ALL signal wiring to debug Error 71
        # self.master_palette.connect('files', self._create_toggle_handler('files'))
        # self.master_palette.connect('analyses', self._create_toggle_handler('analyses'))
        # self.master_palette.connect('pathways', self._create_toggle_handler('pathways'))
        # self.master_palette.connect('topology', self._create_toggle_handler('topology'))
        print("[MAIN_WINDOW] Skipping signal wiring (debugging Error 71)", file=sys.stderr)
        
        print("[MAIN_WINDOW] Master Palette signals wired", file=sys.stderr)
    
    def _create_toggle_handler(self, panel_name: str):
        """Create toggle handler for a panel.
        
        Args:
            panel_name: Name of panel (e.g., 'files', 'analyses')
            
        Returns:
            Handler function
        """
        def on_toggle(is_active):
            """Handle panel toggle from Master Palette.
            
            Args:
                is_active: True if button toggled on, False if toggled off
            """
            if is_active:
                self._show_panel(panel_name)
            else:
                self._hide_panel(panel_name)
        
        return on_toggle
    
    def _show_panel(self, panel_name: str):
        """Show a panel with animation.
        
        Args:
            panel_name: Name of panel to show
        """
        if panel_name not in self.panels:
            print(f"[MAIN_WINDOW] WARNING: Unknown panel '{panel_name}'", file=sys.stderr)
            return
        
        panel = self.panels[panel_name]
        width = panel.get_preferred_width()
        
        print(f"[MAIN_WINDOW] Showing panel '{panel_name}' (width={width}px)", file=sys.stderr)
        
        # Switch stack to panel
        self.panels_stack.set_visible_child_name(panel_name)
        
        # Reveal with animation
        self.panels_revealer.set_reveal_child(True)
        
        # Adjust paned position
        GLib.idle_add(lambda: self.left_paned.set_position(width))
        
        # Activate panel
        panel.activate()
        
        # Update state
        self.active_panel = panel_name
        self.emit('panel-changed', panel_name)
    
    def _hide_panel(self, panel_name: str):
        """Hide a panel with animation.
        
        Args:
            panel_name: Name of panel to hide
        """
        if panel_name not in self.panels:
            return
        
        print(f"[MAIN_WINDOW] Hiding panel '{panel_name}'", file=sys.stderr)
        
        # Deactivate panel
        panel = self.panels[panel_name]
        panel.deactivate()
        
        # Hide with animation
        self.panels_revealer.set_reveal_child(False)
        
        # Collapse paned
        GLib.idle_add(lambda: self.left_paned.set_position(0))
        
        # Update state
        if self.active_panel == panel_name:
            self.active_panel = None
            self.emit('panel-changed', '')
    
    def _set_initial_state(self):
        """Set initial window state (all panels hidden)."""
        print("[MAIN_WINDOW] Setting initial state...", file=sys.stderr)
        
        # Hide revealer
        self.panels_revealer.set_reveal_child(False)
        
        # Collapse paned
        self.left_paned.set_position(0)
        
        print("[MAIN_WINDOW] Initial state set (all panels hidden)", file=sys.stderr)
    
    def show_default_panel(self):
        """Show default panel (Analyses) after window is mapped.
        
        Call this with GLib.idle_add() after window.show_all()
        """
        print("[MAIN_WINDOW] Showing default panel (analyses)...", file=sys.stderr)
        self.master_palette.set_active('analyses', True)
    
    def get_window(self) -> Gtk.ApplicationWindow:
        """Get main window widget.
        
        Returns:
            Main window
        """
        return self.window
    
    def get_workspace(self) -> Gtk.Box:
        """Get main workspace container (for canvas).
        
        Returns:
            Workspace container
        """
        return self.main_workspace
    
    def _on_panel_ready(self, panel, panel_name: str):
        """Handle panel-ready signal.
        
        Args:
            panel: Panel controller
            panel_name: Name of panel
        """
        print(f"[MAIN_WINDOW] Panel '{panel_name}' is ready", file=sys.stderr)
    
    def _on_panel_error(self, panel, error_msg: str, panel_name: str):
        """Handle panel-error signal.
        
        Args:
            panel: Panel controller
            error_msg: Error message
            panel_name: Name of panel
        """
        print(f"[MAIN_WINDOW] Panel '{panel_name}' error: {error_msg}", file=sys.stderr)
