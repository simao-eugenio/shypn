#!/usr/bin/env python3
"""Palette Manager - Central coordinator for floating palettes on canvas overlay.

Responsibilities:
- Register palettes with unique IDs
- Attach palettes to canvas overlay
- Coordinate positioning to avoid conflicts
- Manage palette visibility
- Apply global CSS styles

Architecture:
    Canvas Overlay (GtkOverlay)
    ├── Drawing Area (main canvas)
    └── Palette Manager
        ├── Tools Palette (bottom-center)
        ├── Operations Palette (bottom-left)
        ├── Simulation Palette (top-right) [future]
        └── Properties Palette (right) [future]
"""

from gi.repository import Gtk, Gdk
from typing import Dict, Tuple, Optional
import sys


class PaletteManager:
    """Central manager for all floating palettes on canvas overlay.
    
    Manages palette lifecycle:
    1. Register palettes with unique IDs
    2. Attach to overlay with position
    3. Show/hide individual or all palettes
    4. Coordinate positioning to avoid overlap
    
    Attributes:
        overlay (GtkOverlay): The canvas overlay widget
        palettes (dict): Registered palettes {palette_id: BasePalette}
    """
    
    def __init__(self, overlay: Gtk.Overlay, reference_widget=None):
        """Initialize palette manager.
        
        Args:
            overlay: GtkOverlay widget to attach palettes to
            reference_widget: Optional widget to use as positioning reference (e.g., [E] button)
        """
        self.overlay = overlay
        self.palettes: Dict[str, 'BasePalette'] = {}
        self.reference_widget = reference_widget  # For relative positioning
        
        # Apply global palette CSS
        self._apply_global_css()
        
        print(f"[PaletteManager] Initialized with overlay: {overlay}, reference: {reference_widget}")
    
    def calculate_relative_position(self, offset_x: int, palette_width: int):
        """Calculate positioning to place palette relative to reference widget.
        
        Args:
            offset_x: Horizontal offset from reference widget center (negative = left, positive = right)
            palette_width: Width of the palette to position
            
        Returns:
            tuple: (halign, margin_start, margin_end) for positioning
        """
        if self.reference_widget is None:
            # Fallback: center alignment with offset as margin
            if offset_x < 0:
                return (Gtk.Align.CENTER, 0, abs(offset_x))
            else:
                return (Gtk.Align.CENTER, offset_x, 0)
        
        # Get reference widget allocation (only valid after widget is realized)
        ref_alloc = self.reference_widget.get_allocation()
        ref_center_x = ref_alloc.x + ref_alloc.width / 2
        
        print(f"[PaletteManager] Reference widget at: x={ref_alloc.x}, w={ref_alloc.width}, center={ref_center_x}")
        
        # Calculate palette position:
        # palette_center = ref_center_x + offset_x
        # With CENTER alignment, we shift using margins
        if offset_x < 0:
            # Palette to the left of reference
            margin_end = abs(offset_x) + (palette_width / 2)
            return (Gtk.Align.CENTER, 0, int(margin_end))
        else:
            # Palette to the right of reference
            margin_start = offset_x - (palette_width / 2)
            return (Gtk.Align.CENTER, int(margin_start), 0)
    
    def register_palette(self, 
                        palette: 'BasePalette', 
                        position: Tuple[Gtk.Align, Gtk.Align]) -> bool:
        """Register and attach palette to overlay.
        
        Args:
            palette: BasePalette instance to register
            position: (halign, valign) tuple for positioning
                     e.g., (Gtk.Align.CENTER, Gtk.Align.END)
        
        Returns:
            bool: True if successful, False if palette_id already exists
        """
        palette_id = palette.palette_id
        
        # Check for duplicate ID
        if palette_id in self.palettes:
            print(f"[PaletteManager] Error: Palette '{palette_id}' already registered", 
                  file=sys.stderr)
            return False
        
        # Set position
        halign, valign = position
        palette.set_position(halign, valign)
        
        # Attach to overlay
        revealer = palette.get_widget()
        self.overlay.add_overlay(revealer)
        
        # Store reference
        self.palettes[palette_id] = palette
        
        print(f"[PaletteManager] Registered palette: {palette_id} at position {position}")
        return True
    
    def unregister_palette(self, palette_id: str) -> bool:
        """Unregister and remove palette from overlay.
        
        Args:
            palette_id: ID of palette to remove
            
        Returns:
            bool: True if successful, False if not found
        """
        palette = self.palettes.get(palette_id)
        if not palette:
            print(f"[PaletteManager] Warning: Palette '{palette_id}' not found", 
                  file=sys.stderr)
            return False
        
        # Hide first
        palette.hide()
        
        # Remove from overlay
        revealer = palette.get_widget()
        self.overlay.remove(revealer)
        
        # Remove from registry
        del self.palettes[palette_id]
        
        print(f"[PaletteManager] Unregistered palette: {palette_id}")
        return True
    
    def get_palette(self, palette_id: str) -> Optional['BasePalette']:
        """Get palette by ID.
        
        Args:
            palette_id: ID of palette to retrieve
            
        Returns:
            BasePalette: The palette instance, or None if not found
        """
        return self.palettes.get(palette_id)
    
    def show_palette(self, palette_id: str) -> bool:
        """Show specific palette.
        
        Args:
            palette_id: ID of palette to show
            
        Returns:
            bool: True if successful, False if not found
        """
        palette = self.palettes.get(palette_id)
        if palette:
            palette.show()
            return True
        
        print(f"[PaletteManager] Warning: Cannot show palette '{palette_id}' - not found", 
              file=sys.stderr)
        return False
    
    def hide_palette(self, palette_id: str) -> bool:
        """Hide specific palette.
        
        Args:
            palette_id: ID of palette to hide
            
        Returns:
            bool: True if successful, False if not found
        """
        palette = self.palettes.get(palette_id)
        if palette:
            palette.hide()
            return True
        
        print(f"[PaletteManager] Warning: Cannot hide palette '{palette_id}' - not found", 
              file=sys.stderr)
        return False
    
    def toggle_palette(self, palette_id: str) -> bool:
        """Toggle specific palette visibility.
        
        Args:
            palette_id: ID of palette to toggle
            
        Returns:
            bool: True if successful, False if not found
        """
        palette = self.palettes.get(palette_id)
        if palette:
            palette.toggle()
            return True
        
        print(f"[PaletteManager] Warning: Cannot toggle palette '{palette_id}' - not found", 
              file=sys.stderr)
        return False
    
    def show_all(self):
        """Show all registered palettes."""
        for palette_id, palette in self.palettes.items():
            palette.show()
        print(f"[PaletteManager] Showing all {len(self.palettes)} palettes")
    
    def hide_all(self):
        """Hide all registered palettes."""
        for palette_id, palette in self.palettes.items():
            palette.hide()
        print(f"[PaletteManager] Hiding all {len(self.palettes)} palettes")
    
    def is_palette_visible(self, palette_id: str) -> bool:
        """Check if specific palette is visible.
        
        Args:
            palette_id: ID of palette to check
            
        Returns:
            bool: True if visible, False if hidden or not found
        """
        palette = self.palettes.get(palette_id)
        if palette:
            return palette.is_visible()
        return False
    
    def is_any_visible(self) -> bool:
        """Check if any palette is currently visible.
        
        Returns:
            bool: True if at least one palette is visible, False otherwise
        """
        return any(palette.is_visible() for palette in self.palettes.values())
    
    def get_palette_count(self) -> int:
        """Get number of registered palettes.
        
        Returns:
            int: Number of palettes
        """
        return len(self.palettes)
    
    def list_palettes(self) -> list:
        """Get list of all registered palette IDs.
        
        Returns:
            list: List of palette ID strings
        """
        return list(self.palettes.keys())
    
    def _apply_global_css(self):
        """Apply global CSS styles for all floating palettes with smooth animations.
        
        This provides base styling that all palettes inherit.
        Individual palettes can override via their own CSS.
        """
        try:
            css = b"""
            /* ============================================
               Floating Palettes - Global Base (Zoom Style)
               Strong shadows like zoom palette
               ============================================ */
            
            .floating-palette {
                /* White gradient background like zoom */
                background: linear-gradient(to bottom, #f5f5f5 0%, #d8d8d8 100%);
                border: 2px solid #999999;
                border-radius: 8px;
                padding: 3px;
                
                /* STRONG shadow like zoom palette */
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4),
                            0 2px 4px rgba(0, 0, 0, 0.3),
                            inset 0 1px 0 rgba(255, 255, 255, 0.2);
                
                transition: all 200ms ease;
            }
            
            .floating-palette:backdrop {
                background: linear-gradient(to bottom, #e0e0e0 0%, #c8c8c8 100%);
                border-color: #888888;
                box-shadow: 0 2px 4px rgba(0, 0, 0, 0.3),
                            0 1px 2px rgba(0, 0, 0, 0.2);
            }
            
            /* Global button base styles */
            .floating-palette button {
                transition: all 200ms ease;
            }
            
            /* Smooth reveal animation */
            revealer {
                transition: all 200ms ease;
            }
            """
            
            provider = Gtk.CssProvider()
            provider.load_from_data(css)
            
            Gtk.StyleContext.add_provider_for_screen(
                Gdk.Screen.get_default(),
                provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            
            print("[PaletteManager] Global palette CSS applied with floating effects")
        except Exception as e:
            print(f"[PaletteManager] Warning: Global CSS styling failed: {e}", 
                  file=sys.stderr)
