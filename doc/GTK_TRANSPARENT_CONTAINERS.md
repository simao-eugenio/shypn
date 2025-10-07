# GTK Transparent Containers Guide

## Overview
This guide explains how to make GTK containers (Box, Grid, Overlay, etc.) transparent.

---

## Method 1: CSS with `background-color: transparent`

### Complete Example

```python
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

class TransparentContainerExample(Gtk.Window):
    def __init__(self):
        super().__init__(title="Transparent Container Example")
        
        # Apply CSS
        css_provider = Gtk.CssProvider()
        css = """
        .transparent-box {
            background-color: transparent;
        }
        
        .semi-transparent-box {
            background-color: rgba(0, 0, 0, 0.5);  /* Black with 50% opacity */
        }
        
        .transparent-with-border {
            background-color: transparent;
            border: 2px solid rgba(255, 255, 255, 0.5);
            border-radius: 10px;
        }
        """
        css_provider.load_from_data(css.encode('utf-8'))
        
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        
        # Create transparent box
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.get_style_context().add_class('transparent-box')
        
        # Add some buttons inside
        for i in range(3):
            btn = Gtk.Button(label=f"Button {i+1}")
            box.pack_start(btn, False, False, 0)
        
        self.add(box)
        self.show_all()

# Run
win = TransparentContainerExample()
win.connect("destroy", Gtk.main_quit)
Gtk.main()
```

---

## Method 2: CSS with RGBA Colors

### Use Cases
- Semi-transparent backgrounds
- Frosted glass effect
- Overlay panels

```css
/* Fully transparent */
.container-transparent {
    background-color: transparent;
}

/* Semi-transparent black */
.container-dark-glass {
    background-color: rgba(0, 0, 0, 0.7);
}

/* Semi-transparent white */
.container-light-glass {
    background-color: rgba(255, 255, 255, 0.3);
}

/* Custom color with transparency */
.container-blue-tint {
    background-color: rgba(41, 128, 185, 0.4);  /* Blue with 40% opacity */
}
```

---

## Method 3: Programmatic Transparency (No CSS)

```python
import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

# Create container
box = Gtk.Box()

# Make background transparent
transparent_color = Gdk.RGBA()
transparent_color.red = 0
transparent_color.green = 0
transparent_color.blue = 0
transparent_color.alpha = 0  # 0 = fully transparent, 1 = fully opaque

box.override_background_color(Gtk.StateFlags.NORMAL, transparent_color)
```

### Shorter version:

```python
box.override_background_color(
    Gtk.StateFlags.NORMAL,
    Gdk.RGBA(0, 0, 0, 0)  # R, G, B, Alpha
)
```

---

## Method 4: Widget Opacity (Affects Everything Inside)

```python
# Make entire widget semi-transparent (including children)
box.set_opacity(0.8)  # 0.0 = invisible, 1.0 = fully visible

# Note: This affects ALL children widgets too!
```

**Warning**: `set_opacity()` makes the ENTIRE widget transparent, including all children. Use CSS `background-color: transparent` if you only want transparent background.

---

## Common Use Cases

### Use Case 1: Transparent Overlay Container

```python
# For floating toolbars/palettes over canvas
overlay = Gtk.Overlay()

# Transparent container for buttons
button_box = Gtk.Box(spacing=5)
button_box.get_style_context().add_class('transparent-container')

# CSS:
"""
.transparent-container {
    background-color: transparent;
}
"""
```

### Use Case 2: Semi-Transparent Popup Panel

```python
# For modal-like overlays
panel = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
panel.get_style_context().add_class('glass-panel')

# CSS:
"""
.glass-panel {
    background-color: rgba(44, 62, 80, 0.9);  /* Dark blue-grey, 90% opaque */
    border-radius: 10px;
    border: 1px solid rgba(255, 255, 255, 0.2);
    padding: 20px;
    box-shadow: 0 8px 16px rgba(0, 0, 0, 0.3);
}
"""
```

### Use Case 3: Invisible Container (Children Visible)

```python
# Container is invisible, but buttons inside are visible
container = Gtk.Box()
container.get_style_context().add_class('invisible-container')

button1 = Gtk.Button(label="Visible Button 1")
button2 = Gtk.Button(label="Visible Button 2")
container.pack_start(button1, False, False, 0)
container.pack_start(button2, False, False, 0)

# CSS:
"""
.invisible-container {
    background-color: transparent;
    border: none;
}
"""
```

---

## Advanced: Transparent Window (True Transparency)

To make the **window itself** transparent (showing desktop through it):

```python
class TransparentWindow(Gtk.Window):
    def __init__(self):
        super().__init__()
        
        # Enable transparency
        screen = self.get_screen()
        visual = screen.get_rgba_visual()
        if visual:
            self.set_visual(visual)
        
        # Set app-paintable to allow custom drawing
        self.set_app_paintable(True)
        
        # Make window background transparent
        self.connect('draw', self.on_draw)
    
    def on_draw(self, widget, cr):
        # Clear with transparent color
        cr.set_source_rgba(0, 0, 0, 0)  # Fully transparent
        cr.set_operator(cairo.OPERATOR_SOURCE)
        cr.paint()
        cr.set_operator(cairo.OPERATOR_OVER)
        return False
```

---

## Comparison Table

| Method | Affects Children | CSS Required | Best For |
|--------|-----------------|--------------|----------|
| CSS `transparent` | No | Yes | Container background only |
| CSS `rgba()` | No | Yes | Semi-transparent backgrounds |
| `override_background_color()` | No | No | Programmatic control |
| `set_opacity()` | **YES** | No | Entire widget transparency |
| Window transparency | No | No | Transparent windows |

---

## Troubleshooting

### Problem: Background still visible

**Solution 1**: Remove default styling
```css
.my-container {
    background-color: transparent;
    background-image: none;  /* Remove any background image */
    border: none;  /* Remove borders if needed */
}
```

**Solution 2**: Ensure CSS is applied
```python
# Verify CSS is loaded
if css_provider:
    print("CSS provider loaded")
    
# Verify class is added
classes = widget.get_style_context().list_classes()
print(f"Widget classes: {classes}")
```

### Problem: Children are also transparent

**Cause**: Using `set_opacity()` instead of CSS

**Solution**: Use CSS `background-color: transparent` instead:
```python
# Wrong (makes everything transparent):
widget.set_opacity(0.5)

# Right (only background transparent):
widget.get_style_context().add_class('transparent-bg')
# With CSS: .transparent-bg { background-color: transparent; }
```

### Problem: Transparency not working on overlay

**Solution**: Ensure overlay supports transparency
```python
overlay = Gtk.Overlay()
# The overlay itself should be transparent
overlay.get_style_context().add_class('transparent-overlay')

# CSS:
"""
.transparent-overlay {
    background-color: transparent;
}
"""
```

---

## Real-World Example: Floating Button Container

```python
class FloatingButtonContainer:
    def __init__(self):
        # Create transparent container for buttons
        self.container = Gtk.Box(spacing=10)
        self.container.set_halign(Gtk.Align.CENTER)
        self.container.set_valign(Gtk.Align.END)
        self.container.set_margin_bottom(20)
        
        # Make container transparent
        self.container.get_style_context().add_class('floating-container')
        
        # Add buttons (they remain opaque)
        for label in ['P', 'T', 'A', 'S']:
            btn = Gtk.Button(label=label)
            btn.set_size_request(44, 44)
            btn.get_style_context().add_class('floating-button')
            self.container.pack_start(btn, False, False, 0)
        
        self._setup_css()
    
    def _setup_css(self):
        css = """
        .floating-container {
            background-color: transparent;  /* Container is invisible */
        }
        
        .floating-button {
            background: linear-gradient(to bottom, #34495e, #2c3e50);
            border: 2px solid #1c2833;
            border-radius: 6px;
            /* Buttons remain fully opaque and visible */
        }
        """
        
        provider = Gtk.CssProvider()
        provider.load_from_data(css.encode('utf-8'))
        
        Gtk.StyleContext.add_provider_for_screen(
            Gdk.Screen.get_default(),
            provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
```

---

## Quick Reference

```python
# Fully transparent background
widget.get_style_context().add_class('transparent')
# CSS: .transparent { background-color: transparent; }

# Semi-transparent black overlay
widget.get_style_context().add_class('overlay')
# CSS: .overlay { background-color: rgba(0, 0, 0, 0.5); }

# Programmatic transparent background
widget.override_background_color(Gtk.StateFlags.NORMAL, Gdk.RGBA(0, 0, 0, 0))

# Make entire widget 50% transparent (including children)
widget.set_opacity(0.5)
```

---

## Summary

**Best Practice**: Use **CSS `background-color: transparent`** for most cases where you want containers to be invisible but children to remain fully visible.

**Key Principle**: 
- CSS `background-color` → affects only the container's background
- `set_opacity()` → affects the entire widget tree (container + all children)

Choose the right method based on your needs!
