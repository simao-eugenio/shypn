#!/usr/bin/env python3
"""Base Palette - Abstract base class for floating palettes with overlay support.

Provides common functionality for all floating palettes:
- GtkRevealer for smooth show/hide animations
- GtkEventBox for CSS styling capabilities
- GtkBox for flexible content layout
- Position management (halign/valign)
- Automatic CSS application

Architecture:
    GtkRevealer (animation)
    └── GtkEventBox (CSS styling)
        └── GtkBox (content layout)
            └── [Palette-specific widgets]
"""

from abc import ABC, abstractmethod, ABCMeta
from gi.repository import GObject, Gtk, Gdk
import sys


# Custom metaclass combining GObject and ABC
class GObjectABCMeta(type(GObject.GObject), ABCMeta):
    """Metaclass that combines GObject and ABC for abstract base classes."""
    pass


class BasePalette(GObject.GObject, ABC, metaclass=GObjectABCMeta):
    """Abstract base class for floating palettes.
    
    Subclasses must implement:
        - _create_content(): Build palette-specific widgets
        - _connect_signals(): Wire up button/widget signals
        - _get_css(): Return CSS styling for the palette
    
    Attributes:
        palette_id (str): Unique identifier for this palette
        revealer (GtkRevealer): Container with show/hide animation
        event_box (GtkEventBox): Styled container for CSS
        content_box (GtkBox): Layout container for palette widgets
        buttons (dict): Dictionary of palette buttons/widgets
    """
    
    __gsignals__ = {
        'palette-shown': (GObject.SignalFlags.RUN_FIRST, None, ()),
        'palette-hidden': (GObject.SignalFlags.RUN_FIRST, None, ()),
    }
    
    def __init__(self, palette_id: str, orientation=Gtk.Orientation.HORIZONTAL):
        """Initialize base palette.
        
        Args:
            palette_id: Unique identifier (e.g., 'tools', 'operations')
            orientation: Content box orientation (horizontal/vertical)
        """
        super().__init__()
        
        self.palette_id = palette_id
        self.revealer = None
        self.event_box = None
        self.content_box = None
        self.buttons = {}
        self._is_visible = False  # Start hidden (edit mode toggles visibility)
        self._orientation = orientation
        
        # Create widget hierarchy
        self._create_structure()
        
        # Subclass implements content creation
        self._create_content()
        
        # Subclass implements signal connections
        self._connect_signals()
        
        # Apply CSS styling
        self._apply_css()
        
    
    def _create_structure(self):
        """Create the standard palette widget hierarchy.
        
        Creates:
            GtkRevealer → GtkEventBox → GtkBox
        """
        # Create revealer for smooth animations
        self.revealer = Gtk.Revealer()
        self.revealer.set_transition_type(Gtk.RevealerTransitionType.SLIDE_UP)
        self.revealer.set_transition_duration(250)  # ms
        self.revealer.set_reveal_child(False)  # HIDDEN by default (show only in edit mode)
        self.revealer.set_visible(True)  # Revealer widget itself must be visible
        
        # Create event box for CSS styling (better than Frame)
        self.event_box = Gtk.EventBox()
        self.event_box.get_style_context().add_class(f"palette-{self.palette_id}")
        self.event_box.get_style_context().add_class("floating-palette")
        self.event_box.set_visible(True)  # Event box must be visible
        
        # Create content box for widgets
        self.content_box = Gtk.Box(orientation=self._orientation, spacing=6)
        self.content_box.set_margin_start(8)
        self.content_box.set_margin_end(8)
        self.content_box.set_margin_top(8)
        self.content_box.set_margin_bottom(8)
        self.content_box.set_visible(True)  # Content box must be visible
        
        # Assemble hierarchy
        self.event_box.add(self.content_box)
        self.revealer.add(self.event_box)
        
        # Show all widgets (revealer controls visibility via reveal-child)
        self.content_box.show()  # Show content box explicitly
        self.event_box.show()     # Show event box explicitly  
        self.revealer.show()      # Show revealer explicitly
        
    
    @abstractmethod
    def _create_content(self):
        """Create palette-specific content.
        
        Subclasses must implement this to add their buttons/widgets
        to self.content_box and populate self.buttons dictionary.
        
        Example:
            self.buttons['my_button'] = Gtk.Button(label="Click Me")
            self.content_box.pack_start(self.buttons['my_button'], False, False, 0)
        """
        pass
    
    @abstractmethod
    def _connect_signals(self):
        """Connect palette-specific signals.
        
        Subclasses must implement this to wire up button click handlers
        and other signal connections.
        
        Example:
            self.buttons['my_button'].connect('clicked', self._on_button_clicked)
        """
        pass
    
    @abstractmethod
    def _get_css(self) -> bytes:
        """Get palette-specific CSS styling.
        
        Returns:
            bytes: CSS data to apply to this palette
            
        Example:
            return b'''
            .palette-mypalette button {
                min-width: 40px;
                min-height: 40px;
            }
            '''
        """
        pass
    
    def _apply_css(self):
        """Apply CSS styling to the palette.
        
        Applies both base palette styles and palette-specific styles
        from _get_css().
        """
        try:
            # Get palette-specific CSS
            palette_css = self._get_css()
            
            if palette_css:
                provider = Gtk.CssProvider()
                provider.load_from_data(palette_css)
                
                Gtk.StyleContext.add_provider_for_screen(
                    Gdk.Screen.get_default(),
                    provider,
                    Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
                )
                
        except Exception as e:
            pass
    
    # ==================== Public API ====================
    
    def get_widget(self) -> Gtk.Revealer:
        """Get the top-level widget for adding to overlay.
        
        Returns:
            GtkRevealer: The revealer widget to add to overlay
        """
        return self.revealer
    
    def set_position(self, halign: Gtk.Align, valign: Gtk.Align):
        """Set palette position on overlay.
        
        Args:
            halign: Horizontal alignment (START, CENTER, END, FILL)
            valign: Vertical alignment (START, CENTER, END, FILL)
        """
        if self.revealer:
            self.revealer.set_halign(halign)
            self.revealer.set_valign(valign)
    
    def show(self):
        """Show the palette with animation."""
        if self.revealer:
            if self._is_visible:
                return
                
            current_state = self.revealer.get_reveal_child()
            self.revealer.set_reveal_child(True)
            self._is_visible = True
            
            # Debug: Check allocation
            allocation = self.revealer.get_allocation()
            
            self.emit('palette-shown')
    
    def hide(self):
        """Hide the palette with animation."""
        if self.revealer and self._is_visible:
            self.revealer.set_reveal_child(False)
            self._is_visible = False
            self.emit('palette-hidden')
    
    def toggle(self):
        """Toggle palette visibility."""
        if self._is_visible:
            self.hide()
        else:
            self.show()
    
    def is_visible(self) -> bool:
        """Check if palette is currently visible.
        
        Returns:
            bool: True if palette is revealed
        """
        return self._is_visible
    
    def set_button_sensitive(self, button_id: str, sensitive: bool):
        """Set button sensitivity (enabled/disabled).
        
        Args:
            button_id: Button identifier from self.buttons
            sensitive: True to enable, False to disable
        """
        button = self.buttons.get(button_id)
        if button:
            button.set_sensitive(sensitive)
    
    def get_button(self, button_id: str) -> Gtk.Widget:
        """Get a button widget by ID.
        
        Args:
            button_id: Button identifier from self.buttons
            
        Returns:
            Gtk.Widget: The button widget, or None if not found
        """
        return self.buttons.get(button_id)


# Register GObject type
GObject.type_register(BasePalette)
