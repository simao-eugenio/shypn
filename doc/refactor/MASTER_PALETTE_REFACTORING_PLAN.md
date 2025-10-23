# Master Palette Refactoring Plan

**Date**: October 20, 2025  
**Objective**: Create vertical master toolbar/palette on far left with category buttons  
**Branch**: feature/property-dialogs-and-simulation-palette  
**Backup**: legacy/shypn_backup_20251020_131029.tar.gz ✅

---

## 🎯 Objectives

### Primary Goal
Create a **vertical master palette** (toolbar) positioned at the **far left** of the main window, spanning **top to bottom**, containing large icon buttons (48x48px) that control the visibility of all panel categories.

### Panel Categories to Control
1. **Files** - File operations panel (currently "left panel")
2. **Pathways** - Pathway import/operations panel
3. **Analyses** - Dynamic analyses panel (currently "right panel")
4. **Topology** - NEW: Topology analysis panel (future)

---

## 📐 Current Architecture Analysis

### Current Structure (HeaderBar Buttons)

```
┌─────────────────────────────────────────────────────┐
│ [File Ops] Shypn [Analyses][Pathways] [_][□][×]   │ ← HeaderBar
├─────────────────────────────────────────────────────┤
│ ┌────────┬──────────────────────────┬────────────┐ │
│ │  Left  │                          │   Right    │ │
│ │  Dock  │    Canvas (Workspace)    │   Dock     │ │
│ │  Area  │                          │   Area     │ │
│ └────────┴──────────────────────────┴────────────┘ │
└─────────────────────────────────────────────────────┘
```

**Current Toggle Buttons** (in HeaderBar):
- `left_panel_toggle` - "File Ops" (left dock)
- `right_panel_toggle` - "Analyses" (right dock)
- `pathway_panel_toggle` - "Pathways" (right dock, mutually exclusive with Analyses)

**Current Issues**:
- Buttons in HeaderBar (horizontal, limited space)
- Small text labels only
- No visual hierarchy
- Difficult to add more panels (Topology coming)
- Not scalable

---

## 🎨 New Architecture (Master Palette)

### Target Structure

```
┌──┬──────────────────────────────────────────────────┐
│🗂│ Shypn                          [_][□][×]         │ ← HeaderBar (clean)
├──┼──────────────────────────────────────────────────┤
│📁│ ┌────────┬──────────────────────────┬──────────┐ │
│  │ │  Left  │                          │  Right   │ │
│🗺│ │  Dock  │    Canvas (Workspace)    │  Dock    │ │
│  │ │  Area  │                          │  Area    │ │
│📊│ └────────┴──────────────────────────┴──────────┘ │
│  │                                                   │
│🔬│                                                   │
│  │                                                   │
└──┴───────────────────────────────────────────────────┘
 ↑
Master Palette
(Vertical, 48px wide)
```

### Master Palette Features

**Position**: Far left, full height
**Width**: 48px (fixed)
**Orientation**: Vertical
**Button Size**: 48x48px
**Spacing**: 6px between buttons
**Background**: Slightly darker than main window
**Border**: 1px right border separator

**Buttons** (Top to Bottom):
1. **Files** 📁 - Toggle File operations panel
2. **Pathways** 🗺 - Toggle Pathway import panel
3. **Analyses** 📊 - Toggle Dynamic analyses panel
4. **Topology** 🔬 - Toggle Topology analysis panel (NEW)
5. *[Future expansion space]*

---

## 🏗️ Implementation Plan

### Phase 1: Create Master Palette Infrastructure (Day 1)

#### 1.1 Create OOP Module Structure

**New Directory Structure**:
```
src/shypn/panels/
├── __init__.py
├── master_palette.py          ← NEW: Main palette class
└── palette_button.py          ← NEW: Custom button class
```

**New UI Structure**:
```
ui/
├── master_palette.ui           ← NEW: Palette UI definition
└── master_palette_button.ui    ← NEW: Button template
```

#### 1.2 MasterPalette Class Design

**File**: `src/shypn/panels/master_palette.py`

```python
"""Master vertical palette for panel category controls."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
from pathlib import Path
from typing import Callable, Dict, Optional


class MasterPalette:
    """Vertical master palette with panel category buttons.
    
    Architecture:
    - Positioned at far left of main window
    - Contains large icon buttons (48x48px)
    - Controls visibility of panel categories
    - CSS-styled for visual hierarchy
    - Wayland-safe implementation
    
    Attributes:
        container: GtkBox (vertical) containing all buttons
        buttons: Dict of category name -> PaletteButton
        active_category: Currently active panel category
    """
    
    PALETTE_WIDTH = 48  # pixels
    BUTTON_SIZE = 48    # pixels
    BUTTON_SPACING = 6  # pixels
    
    def __init__(self, ui_path: Optional[Path] = None):
        """Initialize master palette.
        
        Args:
            ui_path: Optional path to master_palette.ui
        """
        self.container = None
        self.buttons: Dict[str, 'PaletteButton'] = {}
        self.active_category: Optional[str] = None
        self._callbacks: Dict[str, Callable] = {}
        
        self._load_ui(ui_path)
        self._apply_css()
    
    def _load_ui(self, ui_path: Optional[Path]):
        """Load palette UI from XML file."""
        if ui_path is None:
            ui_path = self._get_default_ui_path()
        
        builder = Gtk.Builder.new_from_file(str(ui_path))
        self.container = builder.get_object('palette_container')
        
        if self.container is None:
            raise ValueError("palette_container not found in UI file")
    
    def _get_default_ui_path(self) -> Path:
        """Get default UI file path."""
        # From src/shypn/panels/master_palette.py
        # to ui/master_palette.ui
        current = Path(__file__).resolve()
        repo_root = current.parent.parent.parent.parent
        return repo_root / 'ui' / 'master_palette.ui'
    
    def _apply_css(self):
        """Apply CSS styling to palette."""
        css_provider = Gtk.CssProvider()
        css = """
        #palette_container {
            background-color: #2e3440;
            border-right: 1px solid #4c566a;
            min-width: 48px;
            max-width: 48px;
        }
        
        .palette-button {
            background: transparent;
            border: none;
            border-radius: 8px;
            margin: 3px;
            min-width: 42px;
            min-height: 42px;
            padding: 0;
        }
        
        .palette-button:hover {
            background-color: rgba(136, 192, 208, 0.1);
        }
        
        .palette-button:active,
        .palette-button.active {
            background-color: #5e81ac;
            box-shadow: inset 0 0 4px rgba(0,0,0,0.3);
        }
        
        .palette-button image {
            color: #d8dee9;
        }
        
        .palette-button:active image,
        .palette-button.active image {
            color: #eceff4;
        }
        """
        css_provider.load_from_data(css.encode())
        
        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(
            screen,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def add_button(
        self,
        category: str,
        icon_name: str,
        tooltip: str,
        callback: Callable[[bool], None]
    ) -> 'PaletteButton':
        """Add a category button to palette.
        
        Args:
            category: Category identifier (e.g., 'files', 'pathways')
            icon_name: GTK icon name (e.g., 'folder-symbolic')
            tooltip: Tooltip text
            callback: Function to call when toggled (receives active state)
        
        Returns:
            The created PaletteButton instance
        """
        button = PaletteButton(category, icon_name, tooltip)
        button.connect_toggled(lambda active: self._on_button_toggled(category, active))
        
        self.buttons[category] = button
        self._callbacks[category] = callback
        
        self.container.pack_start(button.widget, False, False, self.BUTTON_SPACING)
        
        return button
    
    def _on_button_toggled(self, category: str, active: bool):
        """Handle button toggle event.
        
        Args:
            category: Category that was toggled
            active: New active state
        """
        # If activating, deactivate all other buttons (mutually exclusive)
        if active:
            for other_cat, other_btn in self.buttons.items():
                if other_cat != category:
                    other_btn.set_active(False, emit_signal=False)
            self.active_category = category
        else:
            if self.active_category == category:
                self.active_category = None
        
        # Call registered callback
        if category in self._callbacks:
            self._callbacks[category](active)
    
    def set_button_active(self, category: str, active: bool, emit_signal: bool = True):
        """Programmatically set button active state.
        
        Args:
            category: Category to modify
            active: New active state
            emit_signal: Whether to emit toggled signal
        """
        if category in self.buttons:
            self.buttons[category].set_active(active, emit_signal)
    
    def get_widget(self) -> Gtk.Box:
        """Get the palette container widget for packing."""
        return self.container
```

#### 1.3 PaletteButton Class Design

**File**: `src/shypn/panels/palette_button.py`

```python
"""Custom palette button for master palette."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from typing import Callable, Optional


class PaletteButton:
    """Large icon button for master palette.
    
    Features:
    - 48x48px size
    - Icon-only display
    - Toggle behavior
    - CSS styling support
    - Wayland-safe
    
    Attributes:
        category: Button category identifier
        widget: The GTK button widget
        icon_name: Icon name being displayed
        is_active: Current active state
    """
    
    def __init__(self, category: str, icon_name: str, tooltip: str):
        """Initialize palette button.
        
        Args:
            category: Category identifier
            icon_name: GTK symbolic icon name
            tooltip: Tooltip text
        """
        self.category = category
        self.icon_name = icon_name
        self.is_active = False
        self._toggled_callback: Optional[Callable] = None
        
        self.widget = Gtk.Button()
        self.widget.set_can_focus(False)
        self.widget.set_relief(Gtk.ReliefStyle.NONE)
        self.widget.set_tooltip_text(tooltip)
        
        # Add CSS class
        style_context = self.widget.get_style_context()
        style_context.add_class('palette-button')
        
        # Create icon
        self.icon = Gtk.Image.new_from_icon_name(icon_name, Gtk.IconSize.LARGE_TOOLBAR)
        self.icon.set_pixel_size(32)  # 32px icon in 48px button
        self.widget.add(self.icon)
        
        # Connect click handler
        self.widget.connect('clicked', self._on_clicked)
    
    def _on_clicked(self, button):
        """Handle button click."""
        self.is_active = not self.is_active
        self._update_style()
        
        if self._toggled_callback:
            self._toggled_callback(self.is_active)
    
    def _update_style(self):
        """Update button style based on active state."""
        style_context = self.widget.get_style_context()
        if self.is_active:
            style_context.add_class('active')
        else:
            style_context.remove_class('active')
    
    def connect_toggled(self, callback: Callable[[bool], None]):
        """Connect callback for toggle events.
        
        Args:
            callback: Function to call with new active state
        """
        self._toggled_callback = callback
    
    def set_active(self, active: bool, emit_signal: bool = True):
        """Set button active state programmatically.
        
        Args:
            active: New active state
            emit_signal: Whether to emit toggled signal
        """
        if self.is_active != active:
            self.is_active = active
            self._update_style()
            
            if emit_signal and self._toggled_callback:
                self._toggled_callback(active)
    
    def set_sensitive(self, sensitive: bool):
        """Enable/disable button.
        
        Args:
            sensitive: Whether button is clickable
        """
        self.widget.set_sensitive(sensitive)
```

#### 1.4 UI Definition Files

**File**: `ui/master_palette.ui`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!-- Master Palette - Vertical toolbar for panel category controls -->
<interface>
  <requires lib="gtk+" version="3.20"/>
  
  <object class="GtkBox" id="palette_container">
    <property name="name">palette_container</property>
    <property name="visible">True</property>
    <property name="orientation">vertical</property>
    <property name="spacing">0</property>
    <property name="valign">start</property>
    <property name="width-request">48</property>
    <property name="hexpand">False</property>
    <property name="vexpand">True</property>
    
    <!-- Buttons will be added programmatically -->
    
    <!-- Spacer to push buttons to top -->
    <child>
      <object class="GtkBox">
        <property name="visible">True</property>
        <property name="vexpand">True</property>
      </object>
      <packing>
        <property name="pack-type">end</property>
      </packing>
    </child>
  </object>
</interface>
```

---

### Phase 2: Integrate Palette into Main Window (Day 2)

#### 2.1 Modify main_window.ui

**Changes**:
1. Remove toggle buttons from HeaderBar
2. Add palette container at far left
3. Adjust paned layout

**Modified Structure**:
```xml
<child>
  <object class="GtkBox" id="root_container">
    <property name="orientation">horizontal</property>
    <property name="visible">True</property>
    
    <!-- NEW: Master Palette (far left) -->
    <child>
      <object class="GtkBox" id="master_palette_slot">
        <property name="visible">True</property>
        <property name="orientation">vertical</property>
        <property name="width-request">48</property>
        <!-- Palette will be inserted here programmatically -->
      </object>
      <packing>
        <property name="expand">False</property>
        <property name="fill">True</property>
      </packing>
    </child>
    
    <!-- Existing paned layout (left dock + workspace + right dock) -->
    <child>
      <object class="GtkPaned" id="left_paned">
        <!-- ... existing content ... -->
      </object>
      <packing>
        <property name="expand">True</property>
        <property name="fill">True</property>
      </packing>
    </child>
  </object>
</child>
```

#### 2.2 Modify src/shypn.py

**Key Changes**:

1. **Import Master Palette**:
```python
from shypn.panels.master_palette import MasterPalette
```

2. **Create and Insert Palette**:
```python
# Create master palette
master_palette = MasterPalette()

# Get palette slot from main window
palette_slot = main_builder.get_object('master_palette_slot')
if palette_slot:
    palette_slot.pack_start(master_palette.get_widget(), True, True, 0)
```

3. **Add Category Buttons**:
```python
# Add Files button
master_palette.add_button(
    category='files',
    icon_name='folder-symbolic',
    tooltip='File Operations',
    callback=on_files_category_toggled
)

# Add Pathways button
master_palette.add_button(
    category='pathways',
    icon_name='network-workgroup-symbolic',
    tooltip='Pathway Import',
    callback=on_pathways_category_toggled
)

# Add Analyses button
master_palette.add_button(
    category='analyses',
    icon_name='utilities-system-monitor-symbolic',
    tooltip='Dynamic Analyses',
    callback=on_analyses_category_toggled
)

# Add Topology button (NEW)
master_palette.add_button(
    category='topology',
    icon_name='applications-science-symbolic',
    tooltip='Topology Analysis',
    callback=on_topology_category_toggled
)
```

4. **Migrate Toggle Logic**:
Move existing toggle logic from HeaderBar buttons to palette button callbacks.

---

### Phase 3: Migrate Panel Toggle Logic (Day 3)

#### 3.1 Refactor Toggle Handlers

**Current Pattern** (in shypn.py):
```python
def on_left_toggle(button):
    if button.get_active():
        # Show left panel
        left_dock_area.show()
        left_paned.set_position(250)
    else:
        # Hide left panel
        left_dock_area.hide()
        left_paned.set_position(0)
```

**New Pattern** (with MasterPalette):
```python
def on_files_category_toggled(active: bool):
    """Handle Files category toggle from master palette."""
    if active:
        # Show left panel
        if left_panel_loader and left_dock_area:
            if not left_panel_loader.is_attached:
                left_panel_loader.dock(left_dock_area)
            left_dock_area.show()
            left_paned.set_position(250)
    else:
        # Hide left panel
        if left_dock_area:
            left_dock_area.hide()
            left_paned.set_position(0)
```

#### 3.2 Handle Mutual Exclusivity

Pathways and Analyses panels share the same dock area (right dock):

```python
def on_pathways_category_toggled(active: bool):
    """Handle Pathways category toggle."""
    if active:
        # Hide Analyses if active
        if right_panel_loader and right_panel_loader.is_attached:
            right_panel_loader.float()
            master_palette.set_button_active('analyses', False, emit_signal=False)
        
        # Show Pathways
        if pathway_panel_loader and right_dock_area:
            if not pathway_panel_loader.is_attached:
                pathway_panel_loader.dock(right_dock_area)
            right_dock_area.show()
            # Adjust paned for pathway width
            window_width = window.get_allocated_width()
            right_paned.set_position(window_width - 320)
    else:
        # Hide Pathways
        if right_dock_area:
            right_dock_area.hide()
            right_paned.set_position(10000)

def on_analyses_category_toggled(active: bool):
    """Handle Analyses category toggle."""
    if active:
        # Hide Pathways if active
        if pathway_panel_loader and pathway_panel_loader.is_attached:
            pathway_panel_loader.float()
            master_palette.set_button_active('pathways', False, emit_signal=False)
        
        # Show Analyses
        if right_panel_loader and right_dock_area:
            if not right_panel_loader.is_attached:
                right_panel_loader.dock(right_dock_area)
            right_dock_area.show()
            # Adjust paned for analyses width
            window_width = window.get_allocated_width()
            right_paned.set_position(window_width - 280)
    else:
        # Hide Analyses
        if right_dock_area:
            right_dock_area.hide()
            right_paned.set_position(10000)
```

#### 3.3 Sync Palette with Panel Float/Attach

When panels float/attach independently, sync palette buttons:

```python
# In panel float callback
def on_left_panel_floated():
    """Sync palette when left panel floats."""
    master_palette.set_button_active('files', False, emit_signal=False)

# In panel attach callback
def on_left_panel_attached():
    """Sync palette when left panel attaches."""
    master_palette.set_button_active('files', True, emit_signal=False)
```

---

### Phase 4: Clean Up Legacy Code (Day 4)

#### 4.1 Remove HeaderBar Toggle Buttons

**From main_window.ui**:
- Remove `left_panel_toggle`
- Remove `right_panel_toggle`
- Remove `pathway_panel_toggle`

**From shypn.py**:
- Remove `left_toggle = main_builder.get_object('left_panel_toggle')`
- Remove `right_toggle = main_builder.get_object('right_panel_toggle')`
- Remove `pathway_toggle = main_builder.get_object('pathway_panel_toggle')`
- Remove old toggle button signal connections

#### 4.2 Verify No Orphaned Widgets

**Check for references**:
```bash
grep -r "left_panel_toggle" src/ ui/
grep -r "right_panel_toggle" src/ ui/
grep -r "pathway_panel_toggle" src/ ui/
```

All should return no results after cleanup.

#### 4.3 Update Documentation

Update comments and docstrings:
- Remove references to HeaderBar toggle buttons
- Document new MasterPalette architecture
- Update architecture diagrams

---

## 🎨 Visual Design Specification

### Color Palette (Nord Theme)

```css
/* Master Palette Background */
background-color: #2e3440;  /* Nord Polar Night */
border-right: 1px solid #4c566a;  /* Nord Polar Night - lighter */

/* Button States */
button-default: transparent;
button-hover: rgba(136, 192, 208, 0.1);  /* Nord Frost - subtle */
button-active: #5e81ac;  /* Nord Frost - blue */

/* Icon Colors */
icon-default: #d8dee9;  /* Nord Snow Storm */
icon-active: #eceff4;  /* Nord Snow Storm - brightest */
```

### Icon Specifications

**Icon Set**: GTK Symbolic Icons
**Size**: 32x32px (in 48x48px button)
**Style**: Symbolic (monochrome, themed)

**Recommended Icons**:
- Files: `folder-symbolic` or `document-open-symbolic`
- Pathways: `network-workgroup-symbolic` or `emblem-shared-symbolic`
- Analyses: `utilities-system-monitor-symbolic` or `office-chart-line-symbolic`
- Topology: `applications-science-symbolic` or `view-grid-symbolic`

### Spacing & Sizing

```
Palette Width: 48px (fixed)
Button Size: 48x48px (outer)
Icon Size: 32x32px (inner)
Button Margin: 3px (all sides)
Button Spacing: 6px (between buttons)
Border Width: 1px (right edge)
Border Radius: 8px (rounded corners)
```

---

## 🧪 Testing Strategy

### Unit Tests

**File**: `tests/panels/test_master_palette.py`

```python
"""Tests for Master Palette."""

import pytest
from pathlib import Path
from shypn.panels.master_palette import MasterPalette
from shypn.panels.palette_button import PaletteButton


def test_palette_creation():
    """Test palette instance creation."""
    palette = MasterPalette()
    assert palette is not None
    assert palette.container is not None
    assert palette.PALETTE_WIDTH == 48


def test_add_button():
    """Test adding button to palette."""
    palette = MasterPalette()
    
    callback_called = []
    def callback(active):
        callback_called.append(active)
    
    button = palette.add_button(
        category='test',
        icon_name='folder-symbolic',
        tooltip='Test Button',
        callback=callback
    )
    
    assert button is not None
    assert 'test' in palette.buttons


def test_button_toggle():
    """Test button toggle behavior."""
    palette = MasterPalette()
    
    states = []
    def callback(active):
        states.append(active)
    
    palette.add_button('test', 'folder-symbolic', 'Test', callback)
    
    # Simulate toggle
    palette.set_button_active('test', True)
    assert states == [True]
    assert palette.active_category == 'test'
    
    palette.set_button_active('test', False)
    assert states == [True, False]
    assert palette.active_category is None


def test_mutual_exclusivity():
    """Test only one button active at a time."""
    palette = MasterPalette()
    
    palette.add_button('cat1', 'folder-symbolic', 'Cat 1', lambda x: None)
    palette.add_button('cat2', 'network-symbolic', 'Cat 2', lambda x: None)
    
    palette.set_button_active('cat1', True)
    assert palette.buttons['cat1'].is_active
    assert not palette.buttons['cat2'].is_active
    
    palette.set_button_active('cat2', True)
    assert not palette.buttons['cat1'].is_active
    assert palette.buttons['cat2'].is_active


def test_palette_button_creation():
    """Test PaletteButton instance creation."""
    button = PaletteButton('test', 'folder-symbolic', 'Test Tooltip')
    assert button.category == 'test'
    assert button.icon_name == 'folder-symbolic'
    assert not button.is_active


def test_palette_button_toggle():
    """Test palette button toggle."""
    button = PaletteButton('test', 'folder-symbolic', 'Test')
    
    states = []
    button.connect_toggled(lambda active: states.append(active))
    
    button.set_active(True)
    assert button.is_active
    assert states == [True]
    
    button.set_active(False)
    assert not button.is_active
    assert states == [True, False]
```

### Integration Tests

**File**: `tests/integration/test_palette_integration.py`

```python
"""Integration tests for palette with main window."""

import pytest
from unittest.mock import Mock, MagicMock
from shypn.panels.master_palette import MasterPalette


def test_palette_panel_coordination():
    """Test palette buttons coordinate with panel visibility."""
    # Mock setup
    palette = MasterPalette()
    mock_panel_loader = Mock()
    mock_dock_area = Mock()
    
    # Simulate button toggle
    def on_toggle(active):
        if active:
            mock_panel_loader.dock(mock_dock_area)
            mock_dock_area.show()
        else:
            mock_dock_area.hide()
    
    palette.add_button('test', 'folder-symbolic', 'Test', on_toggle)
    
    # Toggle on
    palette.set_button_active('test', True)
    mock_panel_loader.dock.assert_called_once()
    mock_dock_area.show.assert_called_once()
    
    # Toggle off
    palette.set_button_active('test', False)
    mock_dock_area.hide.assert_called_once()
```

### Visual Tests

**Manual Test Checklist**:
- [ ] Palette appears at far left
- [ ] Palette is 48px wide
- [ ] Buttons are 48x48px
- [ ] Icons are 32x32px and centered
- [ ] Hover effect works
- [ ] Active state shows blue background
- [ ] Only one button active at a time
- [ ] Tooltips appear on hover
- [ ] Panels show/hide on button click
- [ ] Panel float syncs with button
- [ ] Panel attach syncs with button
- [ ] Wayland: No crashes or warnings
- [ ] X11: Works correctly
- [ ] Theme changes respected

---

## 🛡️ Wayland Safety Guidelines

### Wayland-Safe Practices

1. **Widget Lifecycle**:
```python
# ✅ GOOD: Proper widget lifecycle
widget.realize()  # Before showing
widget.show_all()
# ... use widget ...
widget.hide()
widget.destroy()  # Clean destruction

# ❌ BAD: Direct manipulation without realize
widget.get_window().set_cursor(...)  # May be None on Wayland
```

2. **Event Handling**:
```python
# ✅ GOOD: Use signals
button.connect('clicked', on_clicked)

# ❌ BAD: Direct event loop manipulation
Gdk.EventExpose()  # Not available on Wayland
```

3. **Window Management**:
```python
# ✅ GOOD: Let GTK handle window placement
window.present()
window.set_transient_for(parent)

# ❌ BAD: Manual positioning
window.move(x, y)  # Ignored on Wayland
```

4. **CSS Styling**:
```python
# ✅ GOOD: CSS classes for styling
style_context.add_class('palette-button')

# ❌ BAD: Direct property modification
widget.modify_bg(Gtk.StateFlags.NORMAL, color)  # Deprecated
```

### Testing on Wayland

```bash
# Run on Wayland
WAYLAND_DISPLAY=wayland-0 python3 src/shypn.py

# Run on X11 (fallback)
GDK_BACKEND=x11 python3 src/shypn.py
```

---

## 📊 Migration Checklist

### Pre-Migration
- [x] Create backup (legacy/shypn_backup_20251020_131029.tar.gz)
- [x] Document current architecture
- [ ] Create test plan
- [ ] Identify all panel toggle references

### Phase 1: Infrastructure
- [ ] Create `src/shypn/panels/` directory
- [ ] Implement `MasterPalette` class
- [ ] Implement `PaletteButton` class
- [ ] Create `ui/master_palette.ui`
- [ ] Write unit tests
- [ ] Verify CSS styling works

### Phase 2: Integration
- [ ] Modify `ui/main/main_window.ui`
- [ ] Add palette slot to main window
- [ ] Modify `src/shypn.py` to create palette
- [ ] Add all category buttons
- [ ] Test palette appears correctly

### Phase 3: Migration
- [ ] Migrate Files toggle logic
- [ ] Migrate Pathways toggle logic
- [ ] Migrate Analyses toggle logic
- [ ] Add Topology toggle logic (placeholder)
- [ ] Implement panel float/attach sync
- [ ] Test all toggle combinations

### Phase 4: Cleanup
- [ ] Remove HeaderBar toggle buttons from UI
- [ ] Remove toggle button code from shypn.py
- [ ] Search for orphaned references
- [ ] Update all documentation
- [ ] Update architecture diagrams

### Testing
- [ ] Run unit tests
- [ ] Run integration tests
- [ ] Manual visual testing (Wayland)
- [ ] Manual visual testing (X11)
- [ ] Test all panel show/hide combinations
- [ ] Test float/attach synchronization
- [ ] Performance check (no lag on toggle)

### Documentation
- [ ] Update README.md
- [ ] Update architecture docs
- [ ] Create migration guide
- [ ] Document new palette API
- [ ] Add screenshots

---

## 📈 Success Criteria

### Functional Requirements
✅ Palette appears at far left of window
✅ Palette is 48px wide, full height
✅ Four category buttons (Files, Pathways, Analyses, Topology)
✅ Buttons are 48x48px with 32px icons
✅ Only one button active at a time (mutually exclusive)
✅ Panels show/hide on button toggle
✅ Panel float syncs button state
✅ Panel attach syncs button state
✅ No orphaned HeaderBar buttons
✅ No orphaned code references

### Non-Functional Requirements
✅ Wayland-safe (no crashes or warnings)
✅ X11 compatible
✅ CSS-styled (consistent theme)
✅ Smooth animations (hover, active states)
✅ Responsive (< 50ms toggle response)
✅ Clean OOP architecture
✅ Fully tested (unit + integration)
✅ Well documented

### User Experience
✅ Intuitive button layout
✅ Clear visual feedback (hover, active)
✅ Consistent with app design language
✅ Tooltips provide context
✅ Large touch-friendly buttons
✅ Scalable for future categories

---

## 🚀 Implementation Timeline

### Day 1: Infrastructure (6-8 hours)
- Create panel classes (MasterPalette, PaletteButton)
- Create UI files
- Write unit tests
- Verify CSS styling

### Day 2: Integration (6-8 hours)
- Modify main window UI
- Integrate palette into shypn.py
- Add all category buttons
- Test visual appearance

### Day 3: Migration (6-8 hours)
- Migrate toggle logic for all panels
- Implement float/attach sync
- Test all panel combinations
- Fix edge cases

### Day 4: Cleanup (4-6 hours)
- Remove legacy code
- Update documentation
- Final testing
- Commit and push

**Total Estimated Time**: 22-30 hours (~4 days)

---

## 📝 Notes & Considerations

### Design Decisions

**Why Vertical Toolbar?**
- More scalable (easy to add categories)
- Large touch-friendly buttons
- Common pattern in modern IDEs (VS Code, Atom)
- Doesn't compete with HeaderBar for space

**Why Mutually Exclusive Buttons?**
- Simpler user mental model
- Clearer visual focus
- Prevents panel overlap conflicts
- Matches current behavior

**Why 48x48px Buttons?**
- Touch-friendly (44px minimum, 48px comfortable)
- Room for 32px icons (good visibility)
- Standard in modern UIs

**Why CSS Styling?**
- Themeable
- Maintainable
- Wayland-safe
- Follows GTK best practices

### Potential Issues

**Issue 1: Panel Dock Areas**
- Files uses left dock
- Pathways/Analyses share right dock
- **Solution**: Keep existing dock architecture, palette just controls visibility

**Issue 2: Topology Panel Not Implemented**
- **Solution**: Add button now, disable until panel implemented, show "Coming Soon" tooltip

**Issue 3: Button Order**
- **Solution**: Top to bottom: Files, Pathways, Analyses, Topology (workflow order)

**Issue 4: Palette Width on Small Screens**
- **Solution**: 48px is minimal, consider collapsible palette in future

### Future Enhancements

- **Collapsible Palette**: Hide/show palette itself
- **Button Badges**: Show notification counts (e.g., "5 analyses ready")
- **Keyboard Shortcuts**: Ctrl+1/2/3/4 for categories
- **Drag to Reorder**: Custom button order
- **User Themes**: Multiple color schemes
- **Tooltips with Previews**: Show panel preview on hover

---

## 🎯 Next Steps

1. **Review This Plan**: Approve architecture and approach
2. **Create Backup**: ✅ Done (legacy/shypn_backup_20251020_131029.tar.gz)
3. **Start Phase 1**: Implement MasterPalette infrastructure
4. **Iterative Testing**: Test each phase before proceeding
5. **Commit Regularly**: Small commits with clear messages

---

**Status**: 🟢 Ready to Implement  
**Risk Level**: 🟡 Medium (significant refactoring, but well-planned)  
**Backup**: ✅ Complete  
**Dependencies**: None (self-contained refactoring)

**Last Updated**: October 20, 2025  
**Version**: 1.0 (Initial Plan)
