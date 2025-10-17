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
        # Mode change signal - emitted when Edit or Simulate category is clicked
        'mode-change-requested': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        # Forward simulation palette signals
        'simulation-step-executed': (GObject.SignalFlags.RUN_FIRST, None, (float,)),
        'simulation-reset-executed': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'simulation-settings-changed': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, mode='edit', model=None):
        """Initialize placeholder palette.
        
        Args:
            mode: 'edit' or 'simulate'
            model: Optional PetriNetModel for widget palettes (e.g., simulation)
        """
        super().__init__()
        
        self.mode = mode
        self.model = model  # Store model for widget palettes
        self.categories = get_categories_for_mode(mode)
        self.tools = create_tools_for_mode(mode)
        
        self.category_buttons = {}
        self.sub_palettes = {}
        self.active_category = None
        self.active_sub_palette = None
        
        self.animation_in_progress = False
        
        # Widget palette instances (for complex palettes like Simulate)
        self.widget_palette_instances = {}
        
        # Create widget structure
        self._create_structure()
        
        # Apply CSS
        self._apply_css()
    
    def _create_structure(self):
        """Create palette widget hierarchy."""
        # Main container (vertical: sub-palette area FIRST, then categories at bottom)
        self.main_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.main_container.get_style_context().add_class('swissknife-container')
        self.main_container.get_style_context().add_class('placeholder-palette')
        
        # Sub-palette area (stack of revealers) - FIRST (on top, toward canvas)
        self.sub_palette_area = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.sub_palette_area.set_margin_bottom(25)  # Add space between sub-palettes and main row
        
        # Create sub-palettes for each category
        for cat_id, cat_info in self.categories.items():
            sub_palette = self._create_sub_palette(cat_id, cat_info)
            self.sub_palettes[cat_id] = sub_palette
            self.sub_palette_area.pack_start(sub_palette['revealer'], False, False, 0)
        
        self.main_container.pack_start(self.sub_palette_area, False, False, 0)
        
        # Category buttons (horizontal) - LAST (at bottom, fixed)
        category_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        category_box.set_margin_start(8)
        category_box.set_margin_end(8)
        category_box.set_margin_top(4)
        category_box.set_margin_bottom(8)
        category_box.set_halign(Gtk.Align.CENTER)  # Center the category buttons
        category_box.get_style_context().add_class('category-buttons')
        
        # Create category buttons
        for cat_id, cat_info in self.categories.items():
            button = Gtk.Button(label=cat_info['label'])
            button.set_tooltip_text(cat_info['tooltip'])
            button.get_style_context().add_class('category-button')
            button.connect('clicked', self._on_category_clicked, cat_id)
            
            category_box.pack_start(button, False, False, 0)
            self.category_buttons[cat_id] = button
        
        self.main_container.pack_end(category_box, False, False, 0)
    
    def _create_sub_palette(self, cat_id, cat_info):
        """Create a sub-palette with tools or widget palette.
        
        Args:
            cat_id: Category ID
            cat_info: Category configuration
            
        Returns:
            dict: {'revealer': GtkRevealer, 'tools': [tool_ids], 'widget_palette': loader_instance or None}
        """
        # Revealer for animation (SLIDE_UP = reveals upward from bottom)
        revealer = Gtk.Revealer()
        revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        revealer.set_transition_duration(600)  # 600ms - slower animation
        revealer.set_reveal_child(False)  # Hidden by default
        
        # Check if this is a widget palette (e.g., Simulate)
        is_widget_palette = cat_info.get('widget_palette', False)
        widget_palette_instance = None
        
        if is_widget_palette and cat_id == 'simulate':
            # Create real SimulateToolsPaletteLoader
            try:
                from shypn.helpers.simulate_tools_palette_loader import SimulateToolsPaletteLoader
                
                widget_palette_instance = SimulateToolsPaletteLoader(model=self.model)
                self.widget_palette_instances[cat_id] = widget_palette_instance
                
                # Connect simulation palette signals and forward them
                widget_palette_instance.connect('step-executed', self._on_simulation_step)
                widget_palette_instance.connect('reset-executed', self._on_simulation_reset)
                widget_palette_instance.connect('settings-changed', self._on_simulation_settings_changed)
                
                # Get the widget (GtkGrid with all controls)
                # Note: SimulateToolsPaletteLoader.get_widget() returns a GtkRevealer
                # We need to get the container inside it
                loader_revealer = widget_palette_instance.get_widget()
                
                # Extract the container from the loader's revealer
                # (we use our own revealer for animation)
                container = widget_palette_instance.simulate_tools_container
                
                if container:
                    # Remove from loader's revealer and add to ours
                    loader_revealer.remove(container)
                    revealer.add(container)
                    
                    print(f"[PlaceholderPalette] Created widget palette for {cat_id}")
                else:
                    print(f"[PlaceholderPalette] ERROR: No container in SimulateToolsPaletteLoader")
                    # Fallback to empty box
                    revealer.add(Gtk.Box())
                    
            except Exception as e:
                print(f"[PlaceholderPalette] ERROR: Failed to create widget palette for {cat_id}: {e}")
                import traceback
                traceback.print_exc()
                # Fallback to empty box
                revealer.add(Gtk.Box())
        else:
            # Standard tool buttons sub-palette
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
            tools_box.set_halign(Gtk.Align.CENTER)  # Center the buttons horizontally
            
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
            'tools': cat_info['tools'],
            'widget_palette': widget_palette_instance
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
        
        # Emit mode change signal for Edit and Simulate categories
        # BUT only if we're switching TO a different mode than current
        # In Edit mode: both edit and simulate categories are visible, no mode switch needed
        # This signal is for when we want to switch between Edit and Simulate MODES
        mode_for_category = {
            'edit': 'edit',
            'simulate': 'edit',  # Simulate category is part of Edit mode
            'layout': 'edit'     # Layout category is part of Edit mode
        }
        
        requested_mode = mode_for_category.get(cat_id)
        if requested_mode and requested_mode != self.mode:
            print(f"[PlaceholderPalette] Requesting mode change to: {requested_mode}")
            self.emit('mode-change-requested', requested_mode)
        
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
        print(f"[ANIMATION] Showing sub-palette: {cat_id} (slide UP from bottom, 600ms)")
        
        revealer = sub_palette['revealer']
        revealer.set_reveal_child(True)
        
        # Wait for animation to complete
        GLib.timeout_add(600, self._on_show_complete, cat_id)
    
    def _hide_sub_palette(self, cat_id):
        """Hide sub-palette with animation.
        
        Args:
            cat_id: Category ID
        """
        sub_palette = self.sub_palettes.get(cat_id)
        if not sub_palette:
            return
        
        self.animation_in_progress = True
        print(f"[ANIMATION] Hiding sub-palette: {cat_id} (slide DOWN to hide, 600ms)")
        
        revealer = sub_palette['revealer']
        revealer.set_reveal_child(False)
        
        # Wait for animation to complete
        GLib.timeout_add(600, self._on_hide_complete, cat_id)
    
    def _switch_sub_palette(self, from_cat, to_cat):
        """Switch between sub-palettes with animation.
        
        Args:
            from_cat: Category to hide
            to_cat: Category to show
        """
        self.animation_in_progress = True
        print(f"[ANIMATION] Switching: {from_cat} → {to_cat} (hide 600ms, show 600ms)")
        
        # Hide current
        from_palette = self.sub_palettes.get(from_cat)
        if from_palette:
            from_palette['revealer'].set_reveal_child(False)
        
        # Wait for hide animation, then show new
        GLib.timeout_add(600, self._on_switch_hide_complete, from_cat, to_cat)
    
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
        GLib.timeout_add(600, self._on_show_complete, to_cat)
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
    
    def _on_simulation_step(self, sim_palette, time):
        """Handle simulation step signal from SimulateToolsPaletteLoader.
        
        Args:
            sim_palette: SimulateToolsPaletteLoader instance
            time: Current simulation time
        """
        print(f"[SIMULATION] Step executed at time: {time:.3f}")
        self.emit('simulation-step-executed', time)
    
    def _on_simulation_reset(self, sim_palette):
        """Handle simulation reset signal from SimulateToolsPaletteLoader.
        
        Args:
            sim_palette: SimulateToolsPaletteLoader instance
        """
        print(f"[SIMULATION] Reset executed")
        self.emit('simulation-reset-executed')
    
    def _on_simulation_settings_changed(self, sim_palette):
        """Handle simulation settings changed signal from SimulateToolsPaletteLoader.
        
        Args:
            sim_palette: SimulateToolsPaletteLoader instance
        """
        print(f"[SIMULATION] Settings changed")
        self.emit('simulation-settings-changed')
    
    def get_widget(self):
        """Get main container widget."""
        return self.main_container
    
    def _apply_css(self):
        """Apply CSS styling."""
        css = b"""
        /* SwissKnifePalette Test Bed CSS */
        
        /* Main Palette Container - Blue theme */
        .swissknife-container {
            background: linear-gradient(to bottom, 
                rgba(52, 73, 94, 0.92) 0%, 
                rgba(44, 62, 80, 0.92) 100%);
            border: 2px solid rgba(30, 40, 50, 0.9);
            border-radius: 8px;
            padding: 3px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4),
                        0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        /* Category Buttons Container - Darker background */
        .category-buttons {
            padding: 4px;
            background: rgba(0, 0, 0, 0.15);
            border-radius: 6px;
        }
        
        /* Category Buttons - Light gray */
        .category-button {
            min-width: 80px;
            min-height: 36px;
            transition: all 200ms ease;
            background: linear-gradient(to bottom, 
                rgba(236, 240, 241, 1) 0%, 
                rgba(189, 195, 199, 1) 100%);
            border: 1px solid rgba(127, 140, 141, 0.8);
            border-radius: 4px;
            margin: 2px;
        }
        
        .category-button:hover {
            background: linear-gradient(to bottom, 
                rgba(255, 255, 255, 1) 0%, 
                rgba(220, 225, 230, 1) 100%);
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        /* Active Category Button - Green */
        .category-button.active {
            background: linear-gradient(to bottom, #6ab04c 0%, #4a9034 100%);
            color: white;
            border-color: #3a7024;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        /* Sub-Palette Container - Light blue/white theme */
        .sub-palette {
            margin: 4px 8px 8px 8px;
            padding: 8px;
            background: linear-gradient(to bottom,
                rgba(236, 240, 241, 0.95) 0%,
                rgba(220, 225, 230, 0.95) 100%);
            border-radius: 6px;
            border: 2px solid rgba(149, 165, 166, 0.8);
            box-shadow: 0 3px 8px rgba(0, 0, 0, 0.3);
        }
        
        /* Edit Sub-Palette - Dark blue-gray gradient */
        .sub-palette-edit {
            background: linear-gradient(to bottom,
                rgba(52, 73, 94, 0.92) 0%,
                rgba(44, 62, 80, 0.92) 100%);
            border: 2px solid rgba(30, 40, 50, 0.9);
            box-shadow: 0 3px 8px rgba(0, 0, 0, 0.4);
        }
        
        /* Layout Sub-Palette - Dark blue-gray gradient */
        .sub-palette-layout {
            background: linear-gradient(to bottom,
                rgba(52, 73, 94, 0.92) 0%,
                rgba(44, 62, 80, 0.92) 100%);
            border: 2px solid rgba(30, 40, 50, 0.9);
            box-shadow: 0 3px 8px rgba(0, 0, 0, 0.4);
        }
        
        /* Tool Buttons - Keep minimal styling */
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
        
        /* Edit Sub-Palette Tool Buttons - Dark Blue accent */
        .sub-palette-edit .tool-button {
            background: linear-gradient(to bottom, 
                rgba(255, 255, 255, 1) 0%, 
                rgba(214, 234, 248, 1) 100%);
            border: 2px solid rgba(52, 152, 219, 0.6);
        }
        
        .sub-palette-edit .tool-button:hover {
            background: linear-gradient(to bottom, 
                rgba(255, 255, 255, 1) 0%, 
                rgba(187, 222, 251, 1) 100%);
            border-color: rgba(41, 128, 185, 0.9);
            box-shadow: 0 2px 4px rgba(52, 152, 219, 0.4);
        }
        
        .tool-button.placeholder-tool {
            border-left: 3px solid #3498db;
        }
        
        /* Edit buttons - Dark Blue left border */
        .sub-palette-edit .tool-button.placeholder-tool {
            border-left: 4px solid rgba(41, 128, 185, 1);
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
