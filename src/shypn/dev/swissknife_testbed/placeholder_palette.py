#!/usr/bin/env python3
"""Placeholder SwissKnifePalette for testing.

Simplified version of SwissKnifePalette for testing animations,
signals, and CSS without full implementation.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GObject, GLib
import time

from placeholder_tools import (
    create_tools_for_mode,
    get_categories_for_mode
)


class PlaceholderPalette(GObject.GObject):
    """Placeholder SwissKnifePalette for testing.
    
    Tests:
    - Sub-palette animations (slide up/down)
    - Category button behavior
    - Tool button signals
    - CSS styling
    
    Signals:
        category-selected(str): Category button clicked
        tool-activated(str): Tool button clicked
        sub-palette-shown(str): Sub-palette revealed (after animation)
        sub-palette-hidden(str): Sub-palette hidden (after animation)
    """
    
    __gsignals__ = {
        'category-selected': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'tool-activated': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'sub-palette-shown': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'sub-palette-hidden': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }
    
    def __init__(self, mode='edit'):
        """Initialize placeholder palette.
        
        Args:
            mode: 'edit' or 'simulate'
        """
        super().__init__()
        
        self.mode = mode
        self.categories = get_categories_for_mode(mode)
        self.tools = create_tools_for_mode(mode)
        
        self.category_buttons = {}
        self.sub_palettes = {}
        self.active_category = None
        self.active_sub_palette = None
        
        self.animation_in_progress = False
        
        # Create widget structure
        self._create_structure()
        
        # Apply CSS
        self._apply_css()
    
    def _create_structure(self):
        """Create palette widget hierarchy."""
        # Main container (vertical: categories + sub-palette area)
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main_container.get_style_context().add_class('swissknife-container')
        self.main_container.get_style_context().add_class('placeholder-palette')
        
        # Category buttons (horizontal)
        category_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        category_box.set_margin_start(8)
        category_box.set_margin_end(8)
        category_box.set_margin_top(8)
        category_box.set_margin_bottom(4)
        category_box.get_style_context().add_class('category-buttons')
        
        # Create category buttons
        for cat_id, cat_info in self.categories.items():
            button = Gtk.Button(label=cat_info['label'])
            button.set_tooltip_text(cat_info['tooltip'])
            button.get_style_context().add_class('category-button')
            button.connect('clicked', self._on_category_clicked, cat_id)
            
            category_box.pack_start(button, False, False, 0)
            self.category_buttons[cat_id] = button
        
        self.main_container.pack_start(category_box, False, False, 0)
        
        # Sub-palette area (stack of revealers)
        self.sub_palette_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        
        # Create sub-palettes for each category
        for cat_id, cat_info in self.categories.items():
            sub_palette = self._create_sub_palette(cat_id, cat_info)
            self.sub_palettes[cat_id] = sub_palette
            self.sub_palette_area.pack_start(sub_palette['revealer'], False, False, 0)
        
        self.main_container.pack_start(self.sub_palette_area, False, False, 0)
    
    def _create_sub_palette(self, cat_id, cat_info):
        """Create a sub-palette with tools.
        
        Args:
            cat_id: Category ID
            cat_info: Category configuration
            
        Returns:
            dict: {'revealer': GtkRevealer, 'tools': [tool_ids]}
        """
        # Revealer for animation (SLIDE_UP = reveals upward from bottom)
        revealer = Gtk.Revealer()
        revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        revealer.set_transition_duration(200)  # 200ms
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
        
        # Add tool buttons
        tool_ids = cat_info['tools']
        for tool_id in tool_ids:
            tool = self.tools.get(tool_id)
            if tool:
                button = tool.get_button()
                tools_box.pack_start(button, False, False, 0)
                
                # Connect tool signal
                tool.connect('activated', self._on_tool_activated)
        
        event_box.add(tools_box)
        revealer.add(event_box)
        
        return {
            'revealer': revealer,
            'tools': tool_ids
        }
    
    def _on_category_clicked(self, button, cat_id):
        """Handle category button click.
        
        Args:
            button: Category button
            cat_id: Category ID
        """
        if self.animation_in_progress:
            print("[PlaceholderPalette] Animation in progress, ignoring click")
            return
        
        print(f"[PlaceholderPalette] Category clicked: {cat_id}")
        self.emit('category-selected', cat_id)
        
        # Toggle if clicking active category
        if self.active_category == cat_id:
            print(f"[PlaceholderPalette] Toggling off active category: {cat_id}")
            self._hide_sub_palette(cat_id)
            self._deactivate_category_button(cat_id)
            self.active_category = None
        else:
            # Switch to new category
            if self.active_category:
                print(f"[PlaceholderPalette] Switching from {self.active_category} to {cat_id}")
                self._switch_sub_palette(self.active_category, cat_id)
            else:
                print(f"[PlaceholderPalette] Showing sub-palette: {cat_id}")
                self._show_sub_palette(cat_id)
            
            # Update active category
            if self.active_category:
                self._deactivate_category_button(self.active_category)
            self.active_category = cat_id
            self._activate_category_button(cat_id)
    
    def _show_sub_palette(self, cat_id):
        """Show sub-palette with animation.
        
        Args:
            cat_id: Category ID
        """
        sub_palette = self.sub_palettes.get(cat_id)
        if not sub_palette:
            return
        
        self.animation_in_progress = True
        print(f"[ANIMATION] Showing sub-palette: {cat_id} (slide UP from bottom, 200ms)")
        
        revealer = sub_palette['revealer']
        revealer.set_reveal_child(True)
        
        # Wait for animation to complete
        GLib.timeout_add(200, self._on_show_complete, cat_id)
    
    def _hide_sub_palette(self, cat_id):
        """Hide sub-palette with animation.
        
        Args:
            cat_id: Category ID
        """
        sub_palette = self.sub_palettes.get(cat_id)
        if not sub_palette:
            return
        
        self.animation_in_progress = True
        print(f"[ANIMATION] Hiding sub-palette: {cat_id} (slide DOWN to hide, 200ms)")
        
        revealer = sub_palette['revealer']
        revealer.set_reveal_child(False)
        
        # Wait for animation to complete
        GLib.timeout_add(200, self._on_hide_complete, cat_id)
    
    def _switch_sub_palette(self, from_cat, to_cat):
        """Switch between sub-palettes with animation.
        
        Args:
            from_cat: Category to hide
            to_cat: Category to show
        """
        self.animation_in_progress = True
        print(f"[ANIMATION] Switching: {from_cat} → {to_cat} (hide 200ms, show 200ms)")
        
        # Hide current
        from_palette = self.sub_palettes.get(from_cat)
        if from_palette:
            from_palette['revealer'].set_reveal_child(False)
        
        # Wait for hide animation, then show new
        GLib.timeout_add(200, self._on_switch_hide_complete, from_cat, to_cat)
    
    def _on_show_complete(self, cat_id):
        """Called after show animation completes.
        
        Args:
            cat_id: Category ID
        """
        print(f"[ANIMATION] Show animation complete: {cat_id}")
        self.active_sub_palette = cat_id
        self.animation_in_progress = False
        self.emit('sub-palette-shown', cat_id)
        return False  # Don't repeat
    
    def _on_hide_complete(self, cat_id):
        """Called after hide animation completes.
        
        Args:
            cat_id: Category ID
        """
        print(f"[ANIMATION] Hide animation complete: {cat_id}")
        self.active_sub_palette = None
        self.animation_in_progress = False
        self.emit('sub-palette-hidden', cat_id)
        return False  # Don't repeat
    
    def _on_switch_hide_complete(self, from_cat, to_cat):
        """Called after hide animation in switch sequence.
        
        Args:
            from_cat: Hidden category
            to_cat: Category to show next
        """
        print(f"[ANIMATION] Hide complete: {from_cat}, now showing: {to_cat}")
        self.emit('sub-palette-hidden', from_cat)
        
        # Now show new sub-palette
        to_palette = self.sub_palettes.get(to_cat)
        if to_palette:
            to_palette['revealer'].set_reveal_child(True)
        
        # Wait for show animation
        GLib.timeout_add(200, self._on_show_complete, to_cat)
        return False  # Don't repeat
    
    def _activate_category_button(self, cat_id):
        """Highlight category button.
        
        Args:
            cat_id: Category ID
        """
        button = self.category_buttons.get(cat_id)
        if button:
            button.get_style_context().add_class('active')
    
    def _deactivate_category_button(self, cat_id):
        """Un-highlight category button.
        
        Args:
            cat_id: Category ID
        """
        button = self.category_buttons.get(cat_id)
        if button:
            button.get_style_context().remove_class('active')
    
    def _on_tool_activated(self, tool, tool_id):
        """Handle tool activation signal.
        
        Args:
            tool: PlaceholderTool instance
            tool_id: Tool ID
        """
        print(f"[PlaceholderPalette] Tool activated: {tool_id}")
        self.emit('tool-activated', tool_id)
    
    def get_widget(self):
        """Get main container widget."""
        return self.main_container
    
    def _apply_css(self):
        """Apply CSS styling."""
        css = b"""
        /* SwissKnifePalette Test Bed CSS */
        
        .swissknife-container {
            background: linear-gradient(to bottom, #f5f5f5 0%, #d8d8d8 100%);
            border: 2px solid #999999;
            border-radius: 8px;
            padding: 3px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4),
                        0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .category-buttons {
            padding: 4px;
        }
        
        .category-button {
            min-width: 80px;
            min-height: 36px;
            transition: all 200ms ease;
            background: linear-gradient(to bottom, #ffffff 0%, #e0e0e0 100%);
            border: 1px solid #999;
            border-radius: 4px;
            margin: 2px;
        }
        
        .category-button:hover {
            background: linear-gradient(to bottom, #ffffff 0%, #f0f0f0 100%);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        .category-button.active {
            background: linear-gradient(to bottom, #6ab04c 0%, #4a9034 100%);
            color: white;
            border-color: #3a7024;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .sub-palette {
            margin: 4px 8px 8px 8px;
            padding: 8px;
            background: rgba(255, 255, 255, 0.8);
            border-radius: 4px;
            border: 1px solid #ccc;
        }
        
        .tool-button {
            min-width: 50px;
            min-height: 40px;
            margin: 2px;
            transition: all 200ms ease;
            background: linear-gradient(to bottom, #ffffff 0%, #e8e8e8 100%);
            border: 1px solid #999;
            border-radius: 4px;
        }
        
        .tool-button:hover {
            background: linear-gradient(to bottom, #ffffff 0%, #f5f5f5 100%);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        .tool-button.placeholder-tool {
            border-left: 3px solid #3498db;
        }
        """
        
        try:
            provider = Gtk.CssProvider()
            provider.load_from_data(css)
            
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
        except Exception as e:
            print(f"[PlaceholderPalette] CSS error: {e}")
