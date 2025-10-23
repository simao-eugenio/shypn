#!/usr/bin/env python3
"""SwissKnifePalette Controller - Signal Coordination and Business Logic.

Coordinates between UI, Animator, and external signals.
Handles user interactions and delegates to appropriate modules.
"""

from gi.repository import GObject


class SwissKnifePaletteController(GObject.GObject):
    """Controller for SwissKnifePalette signal coordination.
    
    Signals:
        category-selected(str): Category button clicked
        tool-activated(str): Tool button clicked  
        sub-palette-shown(str): Sub-palette revealed (after animation)
        sub-palette-hidden(str): Sub-palette hidden (after animation)
        mode-change-requested(str): Mode change requested (edit/simulate)
    """
    
    __gsignals__ = {
        'category-selected': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'tool-activated': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'sub-palette-shown': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'sub-palette-hidden': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'mode-change-requested': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
    }
    
    def __init__(self, ui, animator, mode):
        """Initialize controller.
        
        Args:
            ui: SwissKnifePaletteUI instance
            animator: SwissKnifePaletteAnimator instance
            mode: Current mode ('edit' or 'simulate')
        """
        super().__init__()
        
        self.ui = ui
        self.animator = animator
        self.mode = mode
        
        # Connect animator callbacks
        self.animator.on_show_complete = self._on_animation_show_complete
        self.animator.on_hide_complete = self._on_animation_hide_complete
        self.animator.on_switch_complete = self._on_animation_switch_complete
        
        # Connect category button signals
        self._connect_category_buttons()
    
    def _connect_category_buttons(self):
        """Connect category button click signals."""
        for cat_id, button in self.ui.category_buttons.items():
            button.connect('clicked', self._on_category_clicked, cat_id)
    
    def _on_category_clicked(self, button, cat_id):
        """Handle category button click.
        
        Args:
            button: Category button
            cat_id: Category ID
        """
        if self.animator.is_animating():
            return
        
        self.emit('category-selected', cat_id)
        
        # Emit mode change signal if needed
        self._check_mode_change(cat_id)
        
        # Handle toggle or switch
        active_category = self.animator.get_active_category()
        
        if active_category == cat_id:
            # Toggle off
            self._hide_category(cat_id)
        elif active_category:
            # Switch to different category
            self._switch_category(active_category, cat_id)
        else:
            # Show new category
            self._show_category(cat_id)
    
    def _check_mode_change(self, cat_id):
        """Check if category switch requires mode change.
        
        Args:
            cat_id: Category ID
        """
        # Map categories to modes
        mode_for_category = {
            'edit': 'edit',
            'simulate': 'edit',  # Simulate category is part of Edit mode
            'layout': 'edit'     # Layout category is part of Edit mode
        }
        
        requested_mode = mode_for_category.get(cat_id)
        if requested_mode and requested_mode != self.mode:
            self.emit('mode-change-requested', requested_mode)
    
    def _show_category(self, cat_id):
        """Show category sub-palette.
        
        Args:
            cat_id: Category ID
        """
        self.ui.activate_category_button(cat_id)
        self.animator.show_sub_palette(cat_id)
    
    def _hide_category(self, cat_id):
        """Hide category sub-palette.
        
        Args:
            cat_id: Category ID
        """
        self.animator.hide_sub_palette(cat_id)
        self.ui.deactivate_category_button(cat_id)
    
    def _switch_category(self, from_cat, to_cat):
        """Switch between categories.
        
        Args:
            from_cat: Source category ID
            to_cat: Target category ID
        """
        self.ui.deactivate_category_button(from_cat)
        self.ui.activate_category_button(to_cat)
        self.animator.switch_sub_palette(from_cat, to_cat)
    
    def _on_animation_show_complete(self, cat_id):
        """Handle show animation completion.
        
        Args:
            cat_id: Category ID
        """
        self.emit('sub-palette-shown', cat_id)
    
    def _on_animation_hide_complete(self, cat_id):
        """Handle hide animation completion.
        
        Args:
            cat_id: Category ID
        """
        self.emit('sub-palette-hidden', cat_id)
    
    def _on_animation_switch_complete(self, from_cat, to_cat):
        """Handle switch animation completion.
        
        Args:
            from_cat: Source category
            to_cat: Target category
        """
        self.emit('sub-palette-shown', to_cat)
    
    def connect_tool_signals(self, tools):
        """Connect tool activation signals.
        
        Args:
            tools: Dict of tool instances
        """
        for tool in tools.values():
            tool.connect('activated', self._on_tool_activated)
    
    def _on_tool_activated(self, tool, tool_id):
        """Handle tool activation.
        
        Args:
            tool: Tool instance
            tool_id: Tool ID
        """
        self.emit('tool-activated', tool_id)
    
    def set_mode(self, mode):
        """Set current mode.
        
        Args:
            mode: Mode string ('edit' or 'simulate')
        """
        self.mode = mode
    
    def force_hide_all(self):
        """Force hide all sub-palettes (for mode switch)."""
        active_cat = self.animator.get_active_category()
        if active_cat:
            self.ui.deactivate_category_button(active_cat)
        
        self.animator.force_hide_all()
