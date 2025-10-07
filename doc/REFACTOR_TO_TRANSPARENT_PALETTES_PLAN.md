# Refactor Plan: From Floating Buttons to Transparent Palettes

## Executive Summary

**Current State**: 7 individual floating buttons positioned with margins (complex to maintain)

**Target State**: 2 organized transparent palettes with clean separation of concerns

**Rationale**: 
- Better code organization and maintainability
- Easier to add/remove buttons within each palette
- Natural grouping (Tools vs Operations)
- Simpler positioning logic (revealer containers vs individual margins)
- Transparent containers eliminate visual clutter

---

## Architecture Comparison

### Current Architecture (Floating Buttons)
```
FloatingButtonsManager
├── 7 individual buttons (P, T, A, S, L, U, R)
├── Each with custom margin positioning
├── All added individually to overlay
└── Single show/hide for all buttons

Problems:
- Complex margin calculations for positioning
- Hard to reorganize button layout
- Single monolithic manager class
- Difficult to add/remove buttons
```

### Target Architecture (Transparent Palettes)
```
EditPaletteLoader [E]
├── ToolsPalette (Revealer)
│   ├── Transparent Box Container
│   └── Buttons: [P][T][A]
│
└── OperationsPalette (Revealer)
    ├── Transparent Box Container
    └── Buttons: [S][L][U][R]

Advantages:
+ Clear separation: Tools vs Operations
+ Easy positioning with revealer placement
+ Transparent containers = invisible background
+ Simple box layout for buttons
+ Easy to extend each palette independently
```

---

## Detailed Plan

### Phase 1: Create UI Files ⏱️ ~30 minutes

#### 1.1 Create Tools Palette UI
**File**: `ui/palettes/edit_tools_palette.ui`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <requires lib="gtk+" version="3.20"/>
  
  <object class="GtkRevealer" id="tools_revealer">
    <property name="visible">True</property>
    <property name="can_focus">False</property>
    <property name="halign">center</property>
    <property name="valign">end</property>
    <property name="margin_bottom">78</property>
    <property name="margin_end">200</property>
    <property name="transition_type">slide-up</property>
    <property name="transition_duration">200</property>
    <property name="reveal_child">False</property>
    
    <child>
      <object class="GtkBox" id="tools_box">
        <property name="visible">True</property>
        <property name="orientation">horizontal</property>
        <property name="spacing">10</property>
        <style>
          <class name="transparent-palette"/>
        </style>
        
        <!-- [P] Place Button -->
        <child>
          <object class="GtkToggleButton" id="btn_place">
            <property name="label">P</property>
            <property name="visible">True</property>
            <property name="width_request">44</property>
            <property name="height_request">44</property>
            <property name="tooltip_text">Place Tool (Ctrl+P)</property>
            <style>
              <class name="tool-button"/>
            </style>
          </object>
        </child>
        
        <!-- [T] Transition Button -->
        <child>
          <object class="GtkToggleButton" id="btn_transition">
            <property name="label">T</property>
            <property name="visible">True</property>
            <property name="width_request">44</property>
            <property name="height_request">44</property>
            <property name="tooltip_text">Transition Tool (Ctrl+T)</property>
            <style>
              <class name="tool-button"/>
            </style>
          </object>
        </child>
        
        <!-- [A] Arc Button -->
        <child>
          <object class="GtkToggleButton" id="btn_arc">
            <property name="label">A</property>
            <property name="visible">True</property>
            <property name="width_request">44</property>
            <property name="height_request">44</property>
            <property name="tooltip_text">Arc Tool (Ctrl+A)</property>
            <style>
              <class name="tool-button"/>
            </style>
          </object>
        </child>
        
      </object>
    </child>
  </object>
</interface>
```

**Position**: Left of center, above [E] button

---

#### 1.2 Create Operations Palette UI
**File**: `ui/palettes/edit_operations_palette.ui`

```xml
<?xml version="1.0" encoding="UTF-8"?>
<interface>
  <requires lib="gtk+" version="3.20"/>
  
  <object class="GtkRevealer" id="operations_revealer">
    <property name="visible">True</property>
    <property name="can_focus">False</property>
    <property name="halign">center</property>
    <property name="valign">end</property>
    <property name="margin_bottom">78</property>
    <property name="margin_start">200</property>
    <property name="transition_type">slide-up</property>
    <property name="transition_duration">200</property>
    <property name="reveal_child">False</property>
    
    <child>
      <object class="GtkBox" id="operations_box">
        <property name="visible">True</property>
        <property name="orientation">horizontal</property>
        <property name="spacing">10</property>
        <style>
          <class name="transparent-palette"/>
        </style>
        
        <!-- [S] Select Button -->
        <child>
          <object class="GtkToggleButton" id="btn_select">
            <property name="label">S</property>
            <property name="visible">True</property>
            <property name="width_request">44</property>
            <property name="height_request">44</property>
            <property name="tooltip_text">Select Tool (Ctrl+S)</property>
            <style>
              <class name="tool-button"/>
            </style>
          </object>
        </child>
        
        <!-- [L] Lasso Button -->
        <child>
          <object class="GtkButton" id="btn_lasso">
            <property name="label">L</property>
            <property name="visible">True</property>
            <property name="width_request">44</property>
            <property name="height_request">44</property>
            <property name="tooltip_text">Lasso Selection (Ctrl+L)</property>
            <style>
              <class name="tool-button"/>
            </style>
          </object>
        </child>
        
        <!-- [U] Undo Button -->
        <child>
          <object class="GtkButton" id="btn_undo">
            <property name="label">U</property>
            <property name="visible">True</property>
            <property name="width_request">44</property>
            <property name="height_request">44</property>
            <property name="tooltip_text">Undo (Ctrl+Z)</property>
            <property name="sensitive">False</property>
            <style>
              <class name="tool-button"/>
            </style>
          </object>
        </child>
        
        <!-- [R] Redo Button -->
        <child>
          <object class="GtkButton" id="btn_redo">
            <property name="label">R</property>
            <property name="visible">True</property>
            <property name="width_request">44</property>
            <property name="height_request">44</property>
            <property name="tooltip_text">Redo (Ctrl+Shift+Z)</property>
            <property name="sensitive">False</property>
            <style>
              <class name="tool-button"/>
            </style>
          </object>
        </child>
        
      </object>
    </child>
  </object>
</interface>
```

**Position**: Right of center, above [E] button

---

### Phase 2: Create Loader Classes ⏱️ ~45 minutes

#### 2.1 Tools Palette Loader
**File**: `src/shypn/helpers/edit_tools_palette_loader.py`

```python
#!/usr/bin/env python3
"""Edit Tools Palette Loader - Loads palette with Place, Transition, Arc tools."""

import sys
import os

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Gdk, GObject
except Exception as e:
    print(f'ERROR: GTK3 not available: {e}', file=sys.stderr)
    sys.exit(1)


class EditToolsPalette:
    """Container for edit tools palette widgets."""
    
    def __init__(self, revealer, buttons):
        """Initialize palette.
        
        Args:
            revealer: GtkRevealer widget
            buttons: Dict of button_name -> GtkButton widget
        """
        self.revealer = revealer
        self.buttons = buttons


class EditToolsPaletteLoader(GObject.GObject):
    """Loader for edit tools palette UI."""
    
    __gsignals__ = {
        'tool-changed': (GObject.SignalFlags.RUN_FIRST, None, (str,))
    }
    
    def __init__(self):
        """Initialize the loader."""
        super().__init__()
        self.builder = None
        self.palette = None
        self.edit_operations = None
        self._updating = False
        self.current_tool = None
    
    def load_ui(self):
        """Load the UI from Glade file."""
        ui_file = 'ui/palettes/edit_tools_palette.ui'
        
        if not os.path.exists(ui_file):
            print(f'ERROR: UI file not found: {ui_file}', file=sys.stderr)
            sys.exit(1)
        
        self.builder = Gtk.Builder()
        self.builder.add_from_file(ui_file)
        
        # Get widgets
        revealer = self.builder.get_object('tools_revealer')
        
        buttons = {
            'place': self.builder.get_object('btn_place'),
            'transition': self.builder.get_object('btn_transition'),
            'arc': self.builder.get_object('btn_arc')
        }
        
        # Create palette object
        self.palette = EditToolsPalette(revealer, buttons)
        
        # Connect signals
        self._connect_signals()
        
        # Apply CSS styling
        self._apply_styling()
        
        return self.palette
    
    def _connect_signals(self):
        """Connect button signals."""
        for tool_name, button in self.palette.buttons.items():
            button.connect('toggled', lambda b, t=tool_name: self._on_tool_toggled(t, b))
    
    def _on_tool_toggled(self, tool_name, button):
        """Handle tool button toggle."""
        if self._updating:
            return
        
        is_active = button.get_active()
        
        if is_active:
            # Deactivate other tools
            self._updating = True
            for name, btn in self.palette.buttons.items():
                if name != tool_name:
                    btn.set_active(False)
            self._updating = False
            
            # Activate tool
            self.current_tool = tool_name
            if self.edit_operations and self.edit_operations.canvas_manager:
                self.edit_operations.canvas_manager.set_tool(tool_name)
            
            self.emit('tool-changed', tool_name)
            print(f"[ToolsPalette] Tool activated: {tool_name}")
        else:
            # Deactivate tool
            self.current_tool = None
            if self.edit_operations and self.edit_operations.canvas_manager:
                self.edit_operations.canvas_manager.clear_tool()
            
            self.emit('tool-changed', '')
            print(f"[ToolsPalette] Tool deactivated")
    
    def _apply_styling(self):
        """Apply CSS styling."""
        css = """
        .transparent-palette {
            background-color: transparent;
        }
        
        .tool-button {
            background: linear-gradient(to bottom, #34495e, #2c3e50);
            border: 2px solid #1c2833;
            border-radius: 6px;
            font-size: 16px;
            font-weight: bold;
            color: white;
            padding: 4px;
            box-shadow: 0 3px 6px rgba(0, 0, 0, 0.3);
        }
        
        .tool-button:hover {
            background: linear-gradient(to bottom, #2c3e50, #1c2833);
        }
        
        .tool-button:checked {
            background: linear-gradient(to bottom, #2980b9, #21618c);
            border-color: #1b4f72;
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        """
        
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css.encode('utf-8'))
        
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def get_palette(self):
        """Get the palette object."""
        return self.palette
    
    def set_edit_operations(self, edit_operations):
        """Set edit operations instance."""
        self.edit_operations = edit_operations
    
    def show(self):
        """Show the palette."""
        if self.palette:
            self.palette.revealer.set_reveal_child(True)
    
    def hide(self):
        """Hide the palette."""
        if self.palette:
            self.palette.revealer.set_reveal_child(False)
    
    def is_visible(self):
        """Check if palette is visible."""
        if self.palette:
            return self.palette.revealer.get_reveal_child()
        return False


def create_edit_tools_palette():
    """Convenience function to create edit tools palette.
    
    Returns:
        EditToolsPaletteLoader: Configured loader instance
    """
    loader = EditToolsPaletteLoader()
    loader.load_ui()
    return loader
```

---

#### 2.2 Operations Palette Loader
**File**: `src/shypn/helpers/edit_operations_palette_loader.py`

```python
#!/usr/bin/env python3
"""Edit Operations Palette Loader - Loads palette with Select, Lasso, Undo, Redo."""

import sys
import os

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Gdk, GObject
except Exception as e:
    print(f'ERROR: GTK3 not available: {e}', file=sys.stderr)
    sys.exit(1)


class EditOperationsPalette:
    """Container for edit operations palette widgets."""
    
    def __init__(self, revealer, buttons):
        """Initialize palette.
        
        Args:
            revealer: GtkRevealer widget
            buttons: Dict of button_name -> GtkButton widget
        """
        self.revealer = revealer
        self.buttons = buttons


class EditOperationsPaletteLoader(GObject.GObject):
    """Loader for edit operations palette UI."""
    
    __gsignals__ = {
        'tool-changed': (GObject.SignalFlags.RUN_FIRST, None, (str,))
    }
    
    def __init__(self):
        """Initialize the loader."""
        super().__init__()
        self.builder = None
        self.palette = None
        self.edit_operations = None
        self._updating = False
        self.select_active = False
    
    def load_ui(self):
        """Load the UI from Glade file."""
        ui_file = 'ui/palettes/edit_operations_palette.ui'
        
        if not os.path.exists(ui_file):
            print(f'ERROR: UI file not found: {ui_file}', file=sys.stderr)
            sys.exit(1)
        
        self.builder = Gtk.Builder()
        self.builder.add_from_file(ui_file)
        
        # Get widgets
        revealer = self.builder.get_object('operations_revealer')
        
        buttons = {
            'select': self.builder.get_object('btn_select'),
            'lasso': self.builder.get_object('btn_lasso'),
            'undo': self.builder.get_object('btn_undo'),
            'redo': self.builder.get_object('btn_redo')
        }
        
        # Create palette object
        self.palette = EditOperationsPalette(revealer, buttons)
        
        # Connect signals
        self._connect_signals()
        
        # Apply CSS styling (shared with tools palette)
        self._apply_styling()
        
        return self.palette
    
    def _connect_signals(self):
        """Connect button signals."""
        self.palette.buttons['select'].connect('toggled', self._on_select_toggled)
        self.palette.buttons['lasso'].connect('clicked', self._on_lasso_clicked)
        self.palette.buttons['undo'].connect('clicked', self._on_undo_clicked)
        self.palette.buttons['redo'].connect('clicked', self._on_redo_clicked)
    
    def _on_select_toggled(self, button):
        """Handle select button toggle."""
        is_active = button.get_active()
        self.select_active = is_active
        
        if is_active:
            if self.edit_operations:
                self.edit_operations.activate_select_mode()
                if self.edit_operations.canvas_manager:
                    self.edit_operations.canvas_manager.clear_tool()
            
            self.emit('tool-changed', 'select')
            print(f"[OperationsPalette] Select mode activated")
        else:
            self.emit('tool-changed', '')
            print(f"[OperationsPalette] Select mode deactivated")
    
    def _on_lasso_clicked(self, button):
        """Handle lasso button click."""
        if self.edit_operations:
            self.edit_operations.activate_lasso_mode()
            print("[OperationsPalette] Lasso mode activated")
    
    def _on_undo_clicked(self, button):
        """Handle undo button click."""
        if self.edit_operations:
            self.edit_operations.undo()
            print("[OperationsPalette] Undo triggered")
    
    def _on_redo_clicked(self, button):
        """Handle redo button click."""
        if self.edit_operations:
            self.edit_operations.redo()
            print("[OperationsPalette] Redo triggered")
    
    def _apply_styling(self):
        """Apply CSS styling (same as tools palette)."""
        # CSS already applied by tools palette loader
        pass
    
    def get_palette(self):
        """Get the palette object."""
        return self.palette
    
    def set_edit_operations(self, edit_operations):
        """Set edit operations instance."""
        self.edit_operations = edit_operations
        
        # Set state change callback
        if edit_operations:
            edit_operations.set_state_change_callback(self._on_state_changed)
            self._update_button_states()
    
    def _on_state_changed(self, undo_available, redo_available, has_selection):
        """Handle state changes from EditOperations."""
        self._update_button_states()
    
    def _update_button_states(self):
        """Update button sensitivity based on context."""
        if not self.edit_operations:
            return
        
        # Update undo/redo states
        undo_avail = self.edit_operations.can_undo()
        redo_avail = self.edit_operations.can_redo()
        
        self.palette.buttons['undo'].set_sensitive(undo_avail)
        self.palette.buttons['redo'].set_sensitive(redo_avail)
    
    def show(self):
        """Show the palette."""
        if self.palette:
            self.palette.revealer.set_reveal_child(True)
    
    def hide(self):
        """Hide the palette."""
        if self.palette:
            self.palette.revealer.set_reveal_child(False)
    
    def is_visible(self):
        """Check if palette is visible."""
        if self.palette:
            return self.palette.revealer.get_reveal_child()
        return False


def create_edit_operations_palette():
    """Convenience function to create edit operations palette.
    
    Returns:
        EditOperationsPaletteLoader: Configured loader instance
    """
    loader = EditOperationsPaletteLoader()
    loader.load_ui()
    return loader
```

---

### Phase 3: Update Canvas Overlay Manager ⏱️ ~20 minutes

**File**: `src/shypn/canvas/canvas_overlay_manager.py`

**Changes**:
1. Replace `floating_buttons_manager` with two palettes
2. Update `_setup_floating_buttons()` → `_setup_edit_palettes()`
3. Add both palette revealers to overlay
4. Update visibility control

```python
# In __init__:
self.edit_tools_palette = None
self.edit_operations_palette = None

# Replace _setup_floating_buttons with:
def _setup_edit_palettes(self):
    """Setup edit tools and operations palettes."""
    from shypn.helpers.edit_tools_palette_loader import create_edit_tools_palette
    from shypn.helpers.edit_operations_palette_loader import create_edit_operations_palette
    
    # Create EditOperations instance
    edit_operations = EditOperations(self.canvas_manager)
    
    # Create tools palette (left side)
    self.edit_tools_palette = create_edit_tools_palette()
    self.edit_tools_palette.set_edit_operations(edit_operations)
    
    # Create operations palette (right side)
    self.edit_operations_palette = create_edit_operations_palette()
    self.edit_operations_palette.set_edit_operations(edit_operations)
    
    # Add palettes to overlay
    tools_revealer = self.edit_tools_palette.get_palette().revealer
    operations_revealer = self.edit_operations_palette.get_palette().revealer
    
    self.overlay_widget.add_overlay(tools_revealer)
    self.overlay_widget.add_overlay(operations_revealer)
    
    # Register palettes
    self.register_palette('edit_tools', self.edit_tools_palette)
    self.register_palette('edit_operations', self.edit_operations_palette)
```

---

### Phase 4: Update Edit Palette Loader ⏱️ ~15 minutes

**File**: `src/shypn/helpers/edit_palette_loader.py`

**Changes**:
1. Wire to both palettes instead of floating_buttons_manager
2. Update toggle to show/hide both palettes

```python
# In __init__:
self.edit_tools_palette = None
self.edit_operations_palette = None

# New method:
def set_edit_palettes(self, tools_palette, operations_palette):
    """Set references to both edit palettes."""
    self.edit_tools_palette = tools_palette
    self.edit_operations_palette = operations_palette

# Update _on_edit_toggled:
def _on_edit_toggled(self, toggle_button):
    """Handle Edit button toggle."""
    is_active = toggle_button.get_active()
    
    if self.edit_tools_palette and self.edit_operations_palette:
        if is_active:
            self.edit_tools_palette.show()
            self.edit_operations_palette.show()
        else:
            self.edit_tools_palette.hide()
            self.edit_operations_palette.hide()
```

---

### Phase 5: Testing & Cleanup ⏱️ ~30 minutes

#### 5.1 Testing Checklist
- [ ] Press [E] - both palettes appear (left and right)
- [ ] Press [E] again - both palettes hide
- [ ] Click [P] - place tool activates
- [ ] Click [T] - transition tool activates (P deactivates)
- [ ] Click [A] - arc tool activates
- [ ] Click [S] - select mode activates
- [ ] Click [L] - lasso mode activates
- [ ] Click [U] - undo triggers (when available)
- [ ] Click [R] - redo triggers (when available)
- [ ] Containers are transparent (invisible background)
- [ ] Buttons have proper styling and hover effects

#### 5.2 Cleanup Tasks
- [ ] Remove `src/shypn/helpers/floating_buttons_manager.py`
- [ ] Update imports in canvas_overlay_manager.py
- [ ] Update documentation files
- [ ] Archive old implementation for reference
- [ ] Commit changes with clear message

---

## Visual Layout

```
                    CANVAS AREA
          ┌─────────────────────────────┐
          │                             │
          │                             │
          │                             │
          │                             │
          │                             │
          │   [P] [T] [A]    [S][L][U][R]  ← Transparent palettes
          │   Tools Palette  Operations    │
          │        ↓              ↓         │
          └─────────[E]───────────────────┘
                    ↑
              Edit Toggle Button
```

**Key**: 
- `[P][T][A]` = Tools Palette (left of center)
- `[S][L][U][R]` = Operations Palette (right of center)
- `[E]` = Toggle button (controls both)
- Both palettes have transparent containers
- Slide-up animation on reveal/hide

---

## Migration Path

### Step-by-Step Execution

1. **Create UI files** (Phase 1)
   - Start with tools palette UI
   - Test loading in isolation
   - Create operations palette UI
   - Test loading in isolation

2. **Create loaders** (Phase 2)
   - Implement tools palette loader
   - Test button clicks and tool activation
   - Implement operations palette loader
   - Test all button functionality

3. **Integration** (Phase 3 + 4)
   - Update canvas overlay manager
   - Update edit palette loader
   - Test [E] button toggle

4. **Cleanup** (Phase 5)
   - Run full test suite
   - Remove old code
   - Update documentation

---

## Risk Assessment

### Low Risk
- ✅ UI file creation (standard GTK pattern)
- ✅ CSS transparency (well documented)
- ✅ Loader classes (existing pattern to follow)

### Medium Risk
- ⚠️ Signal wiring (need to test tool activation)
- ⚠️ State synchronization (undo/redo button states)

### Mitigation
- Test each palette independently before integration
- Keep old code until new implementation fully tested
- Can run both systems in parallel during transition

---

## Benefits of This Approach

1. **Maintainability** ⭐
   - UI defined in Glade (visual editing possible)
   - Clean separation of concerns
   - Easy to add/remove buttons from each palette

2. **Organization** ⭐
   - Natural grouping: Tools vs Operations
   - Clear code structure
   - Two small, focused classes instead of one large one

3. **Flexibility** ⭐
   - Easy to reposition palettes (just change UI margins)
   - Can show/hide palettes independently if needed
   - Can extend each palette separately

4. **User Experience**
   - Transparent containers = clean visual appearance
   - Smooth slide-up animations
   - Logical button grouping

---

## Timeline Estimate

| Phase | Task | Time | Dependencies |
|-------|------|------|--------------|
| 1 | Create UI files | 30 min | None |
| 2.1 | Tools palette loader | 25 min | Phase 1 complete |
| 2.2 | Operations palette loader | 20 min | Phase 1 complete |
| 3 | Update overlay manager | 20 min | Phase 2 complete |
| 4 | Update edit palette loader | 15 min | Phase 3 complete |
| 5 | Testing & cleanup | 30 min | All phases complete |
| **Total** | | **~2.5 hours** | |

---

## Rollback Plan

If issues arise:
1. Keep `floating_buttons_manager.py` as backup
2. Can switch back by uncommenting old code in overlay manager
3. Git revert if needed
4. No data loss risk (UI-only changes)

---

## Conclusion

This refactor trades implementation complexity for maintainability. While we've invested time in the floating buttons approach, the transparent palette architecture is:

- **Easier to understand** (standard revealer pattern)
- **Easier to modify** (UI files + focused loaders)
- **Easier to extend** (add buttons to appropriate palette)
- **Cleaner visually** (transparent containers)

**Recommendation**: Proceed with refactor. The 2.5 hour investment will pay off in reduced maintenance burden and improved code quality.

---

## Next Steps

1. ✅ Review and approve this plan
2. Create Phase 1 (UI files)
3. Test UI files load correctly
4. Create Phase 2 (loaders)
5. Test loaders in isolation
6. Integrate (Phases 3 & 4)
7. Final testing and cleanup

**Ready to proceed?** Let me know and I'll start with Phase 1!
