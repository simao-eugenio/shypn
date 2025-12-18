#!/usr/bin/env python3
"""
Demo: Signal Place Hexagon Rendering

This script demonstrates the visual difference between regular places (circles)
and signal places (hexagons) in the quorum sensing feature.

Run this script to see the hexagon rendering in action.
"""

import cairo
import math

def draw_circle(cr, x, y, radius, color, label):
    """Draw a regular place (circle)."""
    cr.arc(x, y, radius, 0, 2 * math.pi)
    cr.set_source_rgb(*color)
    cr.set_line_width(3.0)
    cr.stroke()
    
    # Draw label
    cr.set_source_rgb(0, 0, 0)
    cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(16)
    x_bearing, y_bearing, width, height, x_advance, y_advance = cr.text_extents(label)
    cr.move_to(x - width / 2 - x_bearing, y + radius + 25)
    cr.show_text(label)

def draw_hexagon(cr, x, y, radius, color, label):
    """Draw a signal place (hexagon)."""
    # Draw hexagon path
    for i in range(6):
        angle = math.pi / 6 + i * math.pi / 3  # 30°, 90°, 150°, 210°, 270°, 330°
        px = x + radius * math.cos(angle)
        py = y + radius * math.sin(angle)
        if i == 0:
            cr.move_to(px, py)
        else:
            cr.line_to(px, py)
    cr.close_path()
    
    cr.set_source_rgb(*color)
    cr.set_line_width(3.0)
    cr.stroke()
    
    # Draw label
    cr.set_source_rgb(0, 0, 0)
    cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(16)
    x_bearing, y_bearing, width, height, x_advance, y_advance = cr.text_extents(label)
    cr.move_to(x - width / 2 - x_bearing, y + radius + 25)
    cr.show_text(label)

def main():
    """Generate comparison image."""
    # Create surface
    width, height = 800, 400
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    cr = cairo.Context(surface)
    
    # White background
    cr.set_source_rgb(1, 1, 1)
    cr.paint()
    
    # Title
    cr.set_source_rgb(0, 0, 0)
    cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_BOLD)
    cr.set_font_size(24)
    cr.move_to(200, 50)
    cr.show_text("Signal Place Visualization")
    
    # Subtitle
    cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(14)
    cr.move_to(220, 75)
    cr.show_text("Quorum Sensing Feature - Phase 3")
    
    # Regular places (circles)
    radius = 50
    y_pos = 200
    
    # Regular place 1
    draw_circle(cr, 150, y_pos, radius, (0.0, 0.0, 0.0), "Substrate")
    
    # Regular place 2
    draw_circle(cr, 300, y_pos, radius, (0.0, 0.0, 0.0), "Product")
    
    # Signal place 1
    draw_hexagon(cr, 500, y_pos, radius, (0.0, 0.4, 0.8), "AHL (Signal)")
    
    # Signal place 2
    draw_hexagon(cr, 650, y_pos, radius, (0.0, 0.4, 0.8), "IL-2 (Signal)")
    
    # Legend
    cr.set_source_rgb(0, 0, 0)
    cr.select_font_face("Sans", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(12)
    cr.move_to(50, 320)
    cr.show_text("Legend:")
    cr.move_to(50, 340)
    cr.show_text("• Circles (black) = Regular places (connected by arcs)")
    cr.move_to(50, 360)
    cr.show_text("• Hexagons (blue) = Signal places (referenced in rate formulas)")
    
    # Save
    surface.write_to_png("signal_place_demo.png")
    print("✅ Image saved: signal_place_demo.png")
    print("\nVisual distinction:")
    print("  Regular places:  ● (black circles)")
    print("  Signal places:   ⬢ (blue hexagons)")

if __name__ == "__main__":
    main()
