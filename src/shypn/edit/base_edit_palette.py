#!/usr/bin/env python3
"""Base Edit Palette - Abstract base class for edit mode palettes."""

from abc import ABCMeta, abstractmethod
from gi.repository import GObject, Gtk, Gdk
import sys


# Custom metaclass that combines GObject and ABC
class GObjectABCMeta(type(GObject.GObject), ABCMeta):
    """Metaclass combining GObject and ABC."""
    pass


class BaseEditPalette(GObject.GObject, metaclass=GObjectABCMeta):
    """Abstract base class for edit mode palettes.
    
    Provides common functionality for palette state management,
    visibility control, and signal emission. Subclasses implement
    specific button handlers and tool activation logic.
    
    Signals:
        tool-changed(str): Emitted when active tool changes
    """
    
    __gsignals__ = {
        'tool-changed': (GObject.SignalFlags.RUN_FIRST, None, (str,))
    }
    
    def __init__(self):
        """Initialize the base palette."""
        super().__init__()
        
        # UI components (set by loader)
        self.revealer = None
        self.container = None
        self.buttons = {}
        
        # State
        self.edit_operations = None
        self._updating = False
        self._css_applied = False
    
    # ==================== Abstract Methods ====================
    
    @abstractmethod
    def setup_buttons(self, button_widgets):
        """Setup button references from UI.
        
        Args:
            button_widgets: Dict of button_id -> GtkButton widget
        """
        pass
    
    @abstractmethod
    def connect_signals(self):
        """Connect button signals to handlers.
        
        Subclasses must implement to wire their specific buttons.
        """
        pass
    
    # ==================== UI Management ====================
    
    def set_revealer(self, revealer):
        """Set the revealer widget.
        
        Args:
            revealer: GtkRevealer widget containing the palette
        """
        self.revealer = revealer
    
    def set_container(self, container):
        """Set the container widget.
        
        Args:
            container: GtkBox or other container holding buttons
        """
        self.container = container
    
    def show(self):
        """Show the palette with animation."""
        if self.revealer:
            self.revealer.set_reveal_child(True)
    
    def hide(self):
        """Hide the palette with animation."""
        if self.revealer:
            self.revealer.set_reveal_child(False)
    
    def is_visible(self):
        """Check if palette is visible.
        
        Returns:
            bool: True if palette is revealed
        """
        if self.revealer:
            return self.revealer.get_reveal_child()
        return False
    
    def toggle(self):
        """Toggle palette visibility."""
        if self.is_visible():
            self.hide()
        else:
            self.show()
    
    # ==================== State Management ====================
    
    def set_edit_operations(self, edit_operations):
        """Set edit operations manager.
        
        Args:
            edit_operations: EditOperations instance
        """
        self.edit_operations = edit_operations
    
    def get_edit_operations(self):
        """Get edit operations manager.
        
        Returns:
            EditOperations: The edit operations instance
        """
        return self.edit_operations
    
    # ==================== Styling ====================
    
    def apply_styling(self):
        """Apply CSS styling to palette.
        
        This should be called once after palette creation.
        Uses shared CSS for consistent appearance across palettes.
        """
        if self._css_applied:
            return
        
        css = """
        .transparent-palette {
            background-color: transparent;
            border: none;
        }
        
        .tool-button {
            background: linear-gradient(to bottom, #5dade2, #3498db);
            border: 2px solid #2e86c1;
            border-radius: 6px;
            font-size: 16px;
            font-weight: bold;
            color: white;
            min-width: 44px;
            min-height: 44px;
            padding: 4px;
            box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3),
                        0 1px 3px rgba(0, 0, 0, 0.2);
        }
        
        .tool-button:hover {
            background: linear-gradient(to bottom, #3498db, #2e86c1);
            box-shadow: 0 4px 8px rgba(93, 173, 226, 0.5),
                        0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .tool-button:checked {
            background: linear-gradient(to bottom, #2980b9, #21618c);
            border-color: #1b4f72;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .tool-button:checked:hover {
            background: linear-gradient(to bottom, #21618c, #1b4f72);
        }
        
        .tool-button:disabled {
            opacity: 0.4;
        }
        """
        
        try:
            css_provider = Gtk.CssProvider()
            css_provider.load_from_data(css.encode('utf-8'))
            
            screen = Gdk.Screen.get_default()
            Gtk.StyleContext.add_provider_for_screen(
                screen,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            
            self._css_applied = True
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"[BaseEditPalette] CSS styling failed: {e}")
    
    # ==================== Utility Methods ====================
    
    def get_button(self, button_name):
        """Get button widget by name.
        
        Args:
            button_name: Name of button (e.g., 'place', 'undo')
            
        Returns:
            GtkButton: Button widget or None if not found
        """
        return self.buttons.get(button_name)
    
    def emit_tool_changed(self, tool_name):
        """Emit tool-changed signal.
        
        Args:
            tool_name: Name of tool that was activated (or '' for none)
        """
        self.emit('tool-changed', tool_name)
