#!/usr/bin/env python3
"""SwissKnifePalette Animator - Animation State Machine.

Handles revealer animations and state transitions for sub-palettes.
Prevents animation conflicts and manages timing.
"""

from gi.repository import GLib


class SwissKnifePaletteAnimator:
    """Animation state machine for sub-palette reveal/hide transitions."""
    
    def __init__(self, sub_palettes):
        """Initialize animator.
        
        Args:
            sub_palettes: Dict of sub-palette structures
        """
        self.sub_palettes = sub_palettes
        self.animation_in_progress = False
        self.active_category = None
        
        # Callbacks for animation events
        self.on_show_complete = None
        self.on_hide_complete = None
        self.on_switch_complete = None
    
    def is_animating(self):
        """Check if animation is in progress.
        
        Returns:
            bool: True if animating
        """
        return self.animation_in_progress
    
    def get_active_category(self):
        """Get currently active category.
        
        Returns:
            str: Active category ID or None
        """
        return self.active_category
    
    def show_sub_palette(self, cat_id):
        """Show sub-palette with animation.
        
        Args:
            cat_id: Category ID
        """
        sub_palette = self.sub_palettes.get(cat_id)
        if not sub_palette:
            return
        
        self.animation_in_progress = True
        revealer = sub_palette['revealer']
        revealer.set_reveal_child(True)
        
        # Schedule completion callback
        GLib.timeout_add(revealer.get_transition_duration(), 
                        self._on_show_complete, cat_id)
    
    def hide_sub_palette(self, cat_id):
        """Hide sub-palette with animation.
        
        Args:
            cat_id: Category ID
        """
        sub_palette = self.sub_palettes.get(cat_id)
        if not sub_palette:
            return
        
        self.animation_in_progress = True
        revealer = sub_palette['revealer']
        revealer.set_reveal_child(False)
        
        # Schedule completion callback
        GLib.timeout_add(revealer.get_transition_duration(),
                        self._on_hide_complete, cat_id)
    
    def switch_sub_palette(self, from_cat, to_cat):
        """Switch from one sub-palette to another with animation.
        
        Args:
            from_cat: Source category ID
            to_cat: Target category ID
        """
        # Hide current, then show new
        from_palette = self.sub_palettes.get(from_cat)
        if not from_palette:
            return
        
        self.animation_in_progress = True
        revealer = from_palette['revealer']
        revealer.set_reveal_child(False)
        
        # Schedule show after hide completes
        GLib.timeout_add(revealer.get_transition_duration(),
                        self._on_switch_hide_complete, from_cat, to_cat)
    
    def _on_show_complete(self, cat_id):
        """Handle show animation completion.
        
        Args:
            cat_id: Category ID
            
        Returns:
            bool: False to stop timer
        """
        self.animation_in_progress = False
        self.active_category = cat_id
        
        if self.on_show_complete:
            self.on_show_complete(cat_id)
        
        return False  # Stop timer
    
    def _on_hide_complete(self, cat_id):
        """Handle hide animation completion.
        
        Args:
            cat_id: Category ID
            
        Returns:
            bool: False to stop timer
        """
        self.animation_in_progress = False
        self.active_category = None
        
        if self.on_hide_complete:
            self.on_hide_complete(cat_id)
        
        return False
    
    def _on_switch_hide_complete(self, from_cat, to_cat):
        """Handle switch hide phase completion, start show phase.
        
        Args:
            from_cat: Source category
            to_cat: Target category
            
        Returns:
            bool: False to stop timer
        """
        # Now show the new sub-palette
        to_palette = self.sub_palettes.get(to_cat)
        if to_palette:
            revealer = to_palette['revealer']
            revealer.set_reveal_child(True)
            
            # Schedule final completion
            GLib.timeout_add(revealer.get_transition_duration(),
                           self._on_switch_show_complete, from_cat, to_cat)
        else:
            self.animation_in_progress = False
        
        return False
    
    def _on_switch_show_complete(self, from_cat, to_cat):
        """Handle switch show phase completion.
        
        Args:
            from_cat: Source category
            to_cat: Target category
            
        Returns:
            bool: False to stop timer
        """
        self.animation_in_progress = False
        self.active_category = to_cat
        
        if self.on_switch_complete:
            self.on_switch_complete(from_cat, to_cat)
        
        return False
    
    def force_hide_all(self):
        """Force hide all sub-palettes without animation (for mode switch)."""
        for sub_palette in self.sub_palettes.values():
            revealer = sub_palette['revealer']
            revealer.set_reveal_child(False)
        
        self.animation_in_progress = False
        self.active_category = None
