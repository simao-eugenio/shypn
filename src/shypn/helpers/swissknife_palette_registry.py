#!/usr/bin/env python3
"""SwissKnifePalette Sub-Palette Registry - Plugin Management.

Manages registration and lifecycle of sub-palettes (tool buttons and widget palettes).
Provides extensible architecture for adding new palette categories.
"""


class SubPaletteRegistry:
    """Registry for sub-palette instances and widget palettes."""
    
    def __init__(self, ui, categories, tools):
        """Initialize registry.
        
        Args:
            ui: SwissKnifePaletteUI instance
            categories: Dict of category configurations
            tools: Dict of tool instances
        """
        self.ui = ui
        self.categories = categories
        self.tools = tools
        
        # Registry storage
        self.sub_palettes = {}
        self.widget_palette_instances = {}
    
    def create_all_sub_palettes(self, model=None):
        """Create all sub-palettes based on category configuration.
        
        Args:
            model: Optional model instance for widget palettes
        """
        for cat_id, cat_info in self.categories.items():
            is_widget_palette = cat_info.get('widget_palette', False)
            
            if is_widget_palette:
                sub_palette = self._create_widget_palette(cat_id, cat_info, model)
            else:
                sub_palette = self._create_tool_button_palette(cat_id, cat_info)
            
            if sub_palette:
                self.sub_palettes[cat_id] = sub_palette
                self.ui.add_sub_palette_to_area(sub_palette)
    
    def _create_tool_button_palette(self, cat_id, cat_info):
        """Create standard tool button sub-palette.
        
        Args:
            cat_id: Category ID
            cat_info: Category configuration
            
        Returns:
            dict: Sub-palette structure
        """
        return self.ui.create_sub_palette(cat_id, cat_info)
    
    def _create_widget_palette(self, cat_id, cat_info, model):
        """Create widget palette (e.g., SimulateToolsPalette).
        
        Args:
            cat_id: Category ID
            cat_info: Category configuration
            model: Model instance
            
        Returns:
            dict: Sub-palette structure or None
        """
        if cat_id == 'simulate':
            try:
                from shypn.helpers.simulate_tools_palette_loader import SimulateToolsPaletteLoader
                
                widget_instance = SimulateToolsPaletteLoader(model=model)
                self.widget_palette_instances[cat_id] = widget_instance
                
                return self.ui.create_widget_palette_container(cat_id, widget_instance)
                
            except Exception as e:
                import traceback
                traceback.print_exc()
                return None
        
        return None
    
    def get_sub_palette(self, cat_id):
        """Get sub-palette structure.
        
        Args:
            cat_id: Category ID
            
        Returns:
            dict: Sub-palette structure or None
        """
        return self.sub_palettes.get(cat_id)
    
    def get_widget_palette_instance(self, cat_id):
        """Get widget palette loader instance.
        
        Args:
            cat_id: Category ID
            
        Returns:
            Widget palette instance or None
        """
        return self.widget_palette_instances.get(cat_id)
    
    def get_all_sub_palettes(self):
        """Get all sub-palette structures.
        
        Returns:
            dict: All sub-palettes
        """
        return self.sub_palettes
    
    def connect_simulation_signals(self, signal_handler):
        """Connect simulation palette signals to handler.
        
        Args:
            signal_handler: Object with signal handler methods
        """
        sim_palette = self.widget_palette_instances.get('simulate')
        if sim_palette:
            sim_palette.connect('step-executed', signal_handler._on_simulation_step)
            sim_palette.connect('reset-executed', signal_handler._on_simulation_reset)
            sim_palette.connect('settings-changed', signal_handler._on_simulation_settings_changed)
