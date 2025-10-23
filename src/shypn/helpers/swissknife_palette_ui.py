#!/usr/bin/env python3
"""SwissKnifePalette UI Builder - Widget Construction Module.

Responsible for creating the widget hierarchy and structure.
Separates UI construction from business logic and animation.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class SwissKnifePaletteUI:
    """UI builder for SwissKnifePalette widget structure."""
    
    def __init__(self, categories, tools):
        """Initialize UI builder.
        
        Args:
            categories: Dict of category configurations
            tools: Dict of tool instances
        """
        self.categories = categories
        self.tools = tools
        
        # UI components (created by build())
        self.main_container = None
        self.sub_palette_area = None
        self.category_buttons = {}
        self.sub_palettes = {}
        
    def build(self):
        """Build the complete widget hierarchy.
        
        Returns:
            Gtk.Box: Main container widget
        """
        # Main container (vertical: sub-palette area FIRST, then categories at bottom)
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main_container.get_style_context().add_class('swissknife-container')
        
        # Sub-palette area (stack of revealers) - FIRST (on top, toward canvas)
        self.sub_palette_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.sub_palette_area.set_margin_bottom(25)  # Space between sub-palettes and category buttons
        
        self.main_container.pack_start(self.sub_palette_area, False, False, 0)
        
        # Category buttons (horizontal) - LAST (at bottom, fixed)
        category_box = self._create_category_buttons()
        self.main_container.pack_end(category_box, False, False, 0)
        
        return self.main_container
    
    def _create_category_buttons(self):
        """Create category button bar.
        
        Returns:
            Gtk.Box: Container with category buttons
        """
        category_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        category_box.set_margin_start(8)
        category_box.set_margin_end(8)
        category_box.set_margin_top(4)
        category_box.set_margin_bottom(8)
        category_box.set_halign(Gtk.Align.CENTER)
        category_box.get_style_context().add_class('category-buttons')
        
        for cat_id, cat_info in self.categories.items():
            button = Gtk.Button(label=cat_info['label'])
            button.set_tooltip_text(cat_info['tooltip'])
            button.get_style_context().add_class('category-button')
            
            category_box.pack_start(button, False, False, 0)
            self.category_buttons[cat_id] = button
        
        return category_box
    
    def create_sub_palette(self, cat_id, cat_info):
        """Create a sub-palette with tools.
        
        Args:
            cat_id: Category ID
            cat_info: Category configuration
            
        Returns:
            dict: {'revealer': GtkRevealer, 'tools': [tool_ids], 'event_box': EventBox, 'tools_box': Box}
        """
        # Revealer for animation (SLIDE_UP = reveals upward from bottom)
        revealer = Gtk.Revealer()
        revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        revealer.set_transition_duration(600)  # 600ms animation
        revealer.set_reveal_child(False)  # Hidden by default
        
        # Event box for CSS
        event_box = Gtk.EventBox()
        event_box.get_style_context().add_class('sub-palette')
        event_box.get_style_context().add_class(f'sub-palette-{cat_id}')
        
        # Tool buttons container
        tools_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        tools_box.set_margin_start(8)
        tools_box.set_margin_end(8)
        tools_box.set_margin_top(4)
        tools_box.set_margin_bottom(8)
        tools_box.set_halign(Gtk.Align.CENTER)
        
        # Add tool buttons
        tool_ids = cat_info['tools']
        for tool_id in tool_ids:
            tool = self.tools.get(tool_id)
            if tool:
                button = tool.get_button()
                tools_box.pack_start(button, False, False, 0)
        
        event_box.add(tools_box)
        revealer.add(event_box)
        
        return {
            'revealer': revealer,
            'tools': tool_ids,
            'event_box': event_box,
            'tools_box': tools_box
        }
    
    def create_widget_palette_container(self, cat_id, widget_instance):
        """Create container for widget palette (e.g., SimulateToolsPalette).
        
        Args:
            cat_id: Category ID
            widget_instance: Widget palette loader instance
            
        Returns:
            dict: {'revealer': GtkRevealer, 'widget_palette': instance}
        """
        # Revealer for animation
        revealer = Gtk.Revealer()
        revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        revealer.set_transition_duration(600)
        revealer.set_reveal_child(False)
        
        # Get widget from instance
        widget_container = widget_instance.get_widget()
        
        if widget_container:
            revealer.add(widget_container)
        else:
            # Fallback to empty box
            revealer.add(Gtk.Box())
        
        return {
            'revealer': revealer,
            'widget_palette': widget_instance,
            'tools': []  # Widget palettes don't have direct tool buttons
        }
    
    def add_sub_palette_to_area(self, sub_palette):
        """Add sub-palette revealer to the sub-palette area.
        
        Args:
            sub_palette: Sub-palette dict with 'revealer' key
        """
        self.sub_palette_area.pack_start(sub_palette['revealer'], False, False, 0)
    
    def get_category_button(self, cat_id):
        """Get category button widget.
        
        Args:
            cat_id: Category ID
            
        Returns:
            Gtk.Button: Category button or None
        """
        return self.category_buttons.get(cat_id)
    
    def activate_category_button(self, cat_id):
        """Add active style to category button.
        
        Args:
            cat_id: Category ID
        """
        button = self.category_buttons.get(cat_id)
        if button:
            button.get_style_context().add_class('active')
    
    def deactivate_category_button(self, cat_id):
        """Remove active style from category button.
        
        Args:
            cat_id: Category ID
        """
        button = self.category_buttons.get(cat_id)
        if button:
            button.get_style_context().remove_class('active')
