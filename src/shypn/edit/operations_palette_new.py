#!/usr/bin/env python3
"""Operations Palette - Selection and edit operations (Select, Lasso, Undo, Redo).

Provides buttons for editing operations:
- Select (S): Selection mode
- Lasso (L): Lasso selection tool
- Undo (U): Undo last operation
- Redo (R): Redo previously undone operation

Architecture:
    Pure Python/OOP - no UI file dependency
    Extends BasePalette for common functionality
"""

from shypn.edit.base_palette import BasePalette
from gi.repository import GObject, Gtk


class OperationsPalette(BasePalette):
    """Palette for editing operations.
    
    Provides buttons for selection tools and undo/redo operations.
    Select is a toggle button (mode), others are action buttons.
    
    Signals:
        operation-triggered(str): Emitted when an operation is triggered
                                 Operation name: 'select', 'lasso', 'undo', 'redo'
    """
    
    __gsignals__ = {
        'operation-triggered': (GObject.SignalFlags.RUN_FIRST, None, (str,))
    }
    
    def __init__(self):
        """Initialize operations palette."""
        # Call parent with palette ID and horizontal orientation
        super().__init__(palette_id='operations', orientation=Gtk.Orientation.HORIZONTAL)
        
        self.selection_mode = False
        self._updating = False
    
    def _create_content(self):
        """Create palette-specific content (Select, Lasso, Undo, Redo buttons).
        
        Implementation of BasePalette abstract method.
        """
        # Create Select button (toggle)
        self.buttons['select'] = self._create_select_button()
        
        # Create Lasso button (action)
        self.buttons['lasso'] = self._create_action_button(
            'L',
            'Lasso Selection (Ctrl+L)\n\nSelect multiple objects by drawing a shape'
        )
        
        # Create Undo button (action)
        self.buttons['undo'] = self._create_action_button(
            'U',
            'Undo (Ctrl+Z)\n\nUndo the last operation',
            sensitive=False  # Disabled by default
        )
        
        # Create Redo button (action)
        self.buttons['redo'] = self._create_action_button(
            'R',
            'Redo (Ctrl+Shift+Z)\n\nRedo the previously undone operation',
            sensitive=False  # Disabled by default
        )
        
        # Add buttons to content box
        for button in self.buttons.values():
            self.content_box.pack_start(button, False, False, 0)
        
        print(f"[OperationsPalette] Created {len(self.buttons)} operation buttons")
    
    def _create_select_button(self) -> Gtk.ToggleButton:
        """Create the Select toggle button.
        
        Returns:
            GtkToggleButton: Configured select button
        """
        button = Gtk.ToggleButton(label='S')
        button.set_tooltip_text('Select Mode (Ctrl+S)\n\nActivate selection mode')
        button.set_size_request(40, 40)
        button.get_style_context().add_class('operation-button')
        button.get_style_context().add_class('select-button')
        button.set_visible(True)  # Ensure button is visible
        button.show()  # Explicitly show button
        return button
    
    def _create_action_button(self, label: str, tooltip: str, sensitive: bool = True) -> Gtk.Button:
        """Create an action button.
        
        Args:
            label: Button label text
            tooltip: Tooltip text
            sensitive: Whether button is enabled
            
        Returns:
            GtkButton: Configured button
        """
        button = Gtk.Button(label=label)
        button.set_tooltip_text(tooltip)
        button.set_size_request(40, 40)
        button.set_sensitive(sensitive)
        button.get_style_context().add_class('operation-button')
        button.set_visible(True)  # Ensure button is visible
        button.show()  # Explicitly show button
        return button
    
    def _connect_signals(self):
        """Connect button signals.
        
        Implementation of BasePalette abstract method.
        """
        # Select button (toggle)
        self.buttons['select'].connect('toggled', self._on_select_toggled)
        
        # Action buttons (clicked)
        self.buttons['lasso'].connect('clicked', self._on_lasso_clicked)
        self.buttons['undo'].connect('clicked', self._on_undo_clicked)
        self.buttons['redo'].connect('clicked', self._on_redo_clicked)
    
    def _on_select_toggled(self, button: Gtk.ToggleButton):
        """Handle select button toggle.
        
        Args:
            button: The select toggle button
        """
        if self._updating:
            return
        
        is_active = button.get_active()
        self.selection_mode = is_active
        
        if is_active:
            self.emit('operation-triggered', 'select')
            print(f"[OperationsPalette] Selection mode activated")
        else:
            self.emit('operation-triggered', 'select-off')
            print(f"[OperationsPalette] Selection mode deactivated")
    
    def _on_lasso_clicked(self, button: Gtk.Button):
        """Handle lasso button click.
        
        Args:
            button: The lasso button
        """
        self.emit('operation-triggered', 'lasso')
        print(f"[OperationsPalette] Lasso selection triggered")
    
    def _on_undo_clicked(self, button: Gtk.Button):
        """Handle undo button click.
        
        Args:
            button: The undo button
        """
        self.emit('operation-triggered', 'undo')
        print(f"[OperationsPalette] Undo triggered")
    
    def _on_redo_clicked(self, button: Gtk.Button):
        """Handle redo button click.
        
        Args:
            button: The redo button
        """
        self.emit('operation-triggered', 'redo')
        print(f"[OperationsPalette] Redo triggered")
    
    def _get_css(self) -> bytes:
        """Get operations palette CSS styling with dramatic floating effect.
        
        Implementation of BasePalette abstract method.
        
        Returns:
            bytes: CSS data for operations palette with floating shadows
        """
        return b"""
        /* ============================================
           Operations Palette - Floating Effect (Zoom Palette Style)
           Strong shadows and gradients like zoom palette
           ============================================ */
        
        .palette-operations {
            /* Purple gradient background (match edit/mode/zoom palettes) */
            background: linear-gradient(to bottom, #667eea 0%, #764ba2 100%);
            border: 2px solid #5568d3;
            border-radius: 8px;
            padding: 3px;
            /* STRONG shadow like zoom palette */
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4),
                        0 2px 4px rgba(0, 0, 0, 0.3),
                        inset 0 1px 0 rgba(255, 255, 255, 0.2);
        }
        
        .palette-operations:hover {
            /* Enhanced on hover */
            border-color: #5568d3;
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.45),
                        0 3px 6px rgba(0, 0, 0, 0.35),
                        0 0 12px rgba(102, 126, 234, 0.3),
                        inset 0 1px 0 rgba(255, 255, 255, 0.3);
        }
        
        .palette-operations .operation-button {
            /* White gradient like zoom buttons */
            background: linear-gradient(to bottom, #ffffff 0%, #f0f0f5 100%);
            border: 2px solid #999999;
            border-radius: 5px;
            color: #2e3436;
            font-weight: bold;
            font-size: 18px;
            min-width: 36px;
            min-height: 36px;
            padding: 0;
            margin: 0;
            transition: all 200ms ease;
        }
        
        .palette-operations .operation-button:hover {
            /* Light blue tint on hover like zoom */
            background: linear-gradient(to bottom, #e8f0ff 0%, #d5e5ff 100%);
            border-color: #3584e4;
            color: #1c71d8;
            box-shadow: 0 0 8px rgba(53, 132, 228, 0.5);
        }
        
        .palette-operations .operation-button:active {
            background: linear-gradient(to bottom, #d0e0ff 0%, #c0d5ff 100%);
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
        }
        
        .palette-operations .operation-button:disabled {
            opacity: 0.4;
            box-shadow: none;
        }
        
        .palette-operations .operation-button:disabled:hover {
            background: linear-gradient(to bottom, #ffffff 0%, #f0f0f5 100%);
            border-color: #999999;
            box-shadow: none;
        }
        
        /* Select button when active - GREEN gradient */
        .palette-operations .select-button:checked {
            background: linear-gradient(to bottom, #33d17a 0%, #26a269 100%);
            color: white;
            border-color: #1a7f4d;
            box-shadow: 0 0 12px rgba(51, 209, 122, 0.6),
                        inset 0 1px 0 rgba(255, 255, 255, 0.2);
        }
        
        .palette-operations .select-button:checked:hover {
            background: linear-gradient(to bottom, #43e18a 0%, #36b279 100%);
            box-shadow: 0 0 16px rgba(51, 209, 122, 0.7),
                        inset 0 1px 0 rgba(255, 255, 255, 0.3);
        }
        """
    
    # ==================== Public API ====================
    
    def is_selection_mode(self) -> bool:
        """Check if selection mode is active.
        
        Returns:
            bool: True if selection mode is active
        """
        return self.selection_mode
    
    def set_selection_mode(self, active: bool):
        """Programmatically set selection mode.
        
        Args:
            active: True to activate, False to deactivate
        """
        self._updating = True
        self.buttons['select'].set_active(active)
        self.selection_mode = active
        self._updating = False
    
    def set_undo_enabled(self, enabled: bool):
        """Enable/disable undo button.
        
        Args:
            enabled: True to enable, False to disable
        """
        print(f"[OperationsPalette] Setting undo button enabled={enabled}")
        self.set_button_sensitive('undo', enabled)
    
    def set_redo_enabled(self, enabled: bool):
        """Enable/disable redo button.
        
        Args:
            enabled: True to enable, False to disable
        """
        print(f"[OperationsPalette] Setting redo button enabled={enabled}")
        self.set_button_sensitive('redo', enabled)
    
    def update_undo_redo_state(self, can_undo: bool, can_redo: bool):
        """Update undo/redo button states.
        
        Args:
            can_undo: Whether undo is available
            can_redo: Whether redo is available
        """
        print(f"[OperationsPalette] update_undo_redo_state called: can_undo={can_undo}, can_redo={can_redo}")
        self.set_undo_enabled(can_undo)
        self.set_redo_enabled(can_redo)


# Register GObject type
GObject.type_register(OperationsPalette)
