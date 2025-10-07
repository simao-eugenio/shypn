# Edit Palette Refactor Plan - Match Mode Palette Style

**Date**: October 7, 2025
**Objective**: Refactor [E] edit button to match mode palette's zoom-style appearance with expandable container

---

## Overview

Refactor the edit palette from a single floating [E] button to a professional styled container matching the mode palette design. The container will have space for 2 button positions with [E] centered, allowing for future expansion.

---

## Visual Comparison

### Current (Single Button)
```
┌────────┐
│   [E]  │  ← Flat green button, 36×36px
└────────┘
```

### Target (Zoom-Style Container) ✨
```
┌──────────────────────────────────┐
│ ╔═════════════╗                  │  ← Purple gradient container (like mode/zoom)
│ ║  [ ] [E]    ║                  │  ← 2 button positions, [E] centered
│ ╚═════════════╝                  │     (left position reserved for future)
└──────────────────────────────────┘
```

### Design Rationale
- **Container**: Purple gradient (#667eea → #764ba2) matching zoom/mode palettes
- **Button Layout**: Horizontal box with 2 positions (28×28px each)
  - Position 1 (left): Empty placeholder for future functionality
  - Position 2 (center): [E] toggle button
- **Spacing**: 3px padding inside container, 12px bottom margin
- **Positioning**: Bottom-center of canvas (CENTER alignment)

---

## Architecture Pattern

Following the successful mode palette refactor pattern:

```
edit_palette_container (GtkBox - outer)
  └─ edit_control (GtkBox - inner styled container)
       ├─ [placeholder] (28×28px invisible spacer)
       └─ edit_toggle_button [E] (28×28px)
```

This matches:
- **Mode Palette**: `mode_palette_container → mode_control → [E][S]`
- **Zoom Palette**: `zoom_container → zoom_control → [+][-][R]`

---

## Implementation Phases

### Phase 1: Restructure edit_palette.ui ✨
**File**: `ui/palettes/edit_palette.ui`

**Current Structure**:
```xml
<object class="GtkBox" id="edit_palette_container">
  <child>
    <object class="GtkToggleButton" id="edit_toggle_button">
      <property name="label">E</property>
      <property name="width-request">36</property>
      <property name="height-request">36</property>
      <style><class name="edit-button"/></style>
    </object>
  </child>
</object>
```

**Target Structure**:
```xml
<object class="GtkBox" id="edit_palette_container">
  <property name="halign">center</property>
  <property name="valign">end</property>
  <property name="margin_bottom">12</property>  <!-- 24 → 12 (match mode) -->
  
  <!-- NEW: Inner styled container -->
  <child>
    <object class="GtkBox" id="edit_control">
      <property name="visible">True</property>
      <property name="orientation">horizontal</property>
      <property name="spacing">3</property>
      <style>
        <class name="edit-palette"/>  <!-- Purple gradient container -->
      </style>
      
      <!-- Placeholder for future button (left position) -->
      <child>
        <object class="GtkBox" id="edit_placeholder">
          <property name="visible">True</property>
          <property name="width-request">28</property>
          <property name="height-request">28</property>
          <property name="opacity">0</property>  <!-- Invisible spacer -->
        </object>
      </child>
      
      <!-- [E] Toggle Button (center position) -->
      <child>
        <object class="GtkToggleButton" id="edit_toggle_button">
          <property name="visible">True</property>
          <property name="label">E</property>
          <property name="tooltip-text">Toggle Edit Tools (Place, Transition, Arc)</property>
          <property name="width-request">28</property>  <!-- 36 → 28 -->
          <property name="height-request">28</property>  <!-- 36 → 28 -->
          <style>
            <class name="edit-button"/>
          </style>
        </object>
      </child>
      
    </object>
  </child>
</object>
```

**Changes Summary**:
- ✨ Add inner `<object class="GtkBox" id="edit_control">` with horizontal orientation
- ✨ Add placeholder box (28×28px, opacity=0) for future expansion
- ✨ Change button size from 36×36px → 28×28px (match mode palette)
- ✨ Change bottom margin from 24px → 12px (match mode palette)
- ✨ Move `edit-palette` CSS class to inner box (for purple gradient)
- ✅ Preserve button ID: `edit_toggle_button`
- ✅ Preserve tooltip-text
- ✅ Preserve edit-button CSS class

---

### Phase 2: Refactor edit_palette_loader.py 🔧
**File**: `src/shypn/helpers/edit_palette_loader.py`

**Add New Infrastructure** (like mode palette):

```python
from pathlib import Path
from gi.repository import Pango

class EditPaletteLoader(GObject.GObject):
    """Zoom-style edit palette loader with styled container."""
    
    def __init__(self, ui_path=None):
        super().__init__()
        
        # Auto-detect UI path using Path
        if ui_path is None:
            self.ui_path = Path(__file__).parent.parent.parent.parent / 'ui' / 'palettes' / 'edit_palette.ui'
        else:
            self.ui_path = Path(ui_path)
        
        self.builder = Gtk.Builder()
        
        # Widget references
        self.edit_palette_container = None  # Outer container
        self.edit_control = None            # NEW: Inner styled box
        self.edit_placeholder = None        # NEW: Future expansion placeholder
        self.edit_toggle_button = None      # [E] button
        
        # Styling
        self.css_provider = None
        self.target_height = 24  # Dynamic font-based sizing
        
        # Palette control (existing - preserve)
        self.tools_palette = None
        self.operations_palette = None
        # ... other existing variables ...
    
    def load(self):
        """Load UI file, extract widgets, apply zoom-style styling."""
        # Validate file exists
        if not self.ui_path.exists():
            raise FileNotFoundError(f"Edit palette UI file not found: {self.ui_path}")
        
        # Load UI
        self.builder.add_from_file(str(self.ui_path))
        
        # Extract widgets
        self.edit_palette_container = self.builder.get_object('edit_palette_container')
        self.edit_control = self.builder.get_object('edit_control')  # NEW
        self.edit_placeholder = self.builder.get_object('edit_placeholder')  # NEW
        self.edit_toggle_button = self.builder.get_object('edit_toggle_button')
        
        if self.edit_palette_container is None:
            raise ValueError("Object 'edit_palette_container' not found")
        
        # Calculate dynamic sizing
        self._calculate_target_size()
        
        # Apply zoom-style CSS
        self._apply_css()
        
        # Connect signals (existing)
        self.edit_toggle_button.connect('toggled', self._on_edit_toggled)
        
        print(f"[EditPalette] Loaded and initialized with target size: {self.target_height}px")
        
        return self.edit_palette_container
    
    def _calculate_target_size(self):
        """Calculate dynamic button size based on font metrics (1.3× 'W' height)."""
        # Create temporary label to measure font
        temp_label = Gtk.Label(label="W")
        temp_label.show()
        
        # Get layout and measure
        layout = temp_label.get_layout()
        if layout:
            _, logical_rect = layout.get_pixel_extents()
            w_height = logical_rect.height
            self.target_height = max(int(w_height * 1.3), 24)  # Minimum 24px
        else:
            self.target_height = 24  # Fallback
        
        print(f"[EditPalette] Calculated target button size: {self.target_height}px")
    
    def _apply_css(self):
        """Apply zoom-style CSS with purple gradient container."""
        css = f"""
        /* Purple gradient container (match mode/zoom palettes) */
        .edit-palette {{
            background: linear-gradient(to bottom, #667eea 0%, #764ba2 100%);
            border: 2px solid #5568d3;
            border-radius: 8px;
            padding: 3px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4),
                        0 2px 4px rgba(0, 0, 0, 0.3),
                        inset 0 1px 0 rgba(255, 255, 255, 0.2);
        }}
        
        /* [E] Toggle Button - Green gradient (preserve green theme) */
        .edit-button {{
            background: linear-gradient(to bottom, #2ecc71 0%, #27ae60 100%);
            border: 2px solid #229954;
            border-radius: 5px;
            font-size: 18px;
            font-weight: bold;
            color: white;
            min-width: {self.target_height}px;
            min-height: {self.target_height}px;
            padding: 0;
            margin: 0;
            transition: all 200ms ease;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
        }}
        
        .edit-button:hover {{
            background: linear-gradient(to bottom, #27ae60 0%, #229954 100%);
            border-color: #1e8449;
            box-shadow: 0 0 8px rgba(46, 204, 113, 0.6);
        }}
        
        .edit-button:active {{
            background: linear-gradient(to bottom, #229954 0%, #1e8449 100%);
            box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.3);
        }}
        
        /* Checked state (tools visible) - darker green */
        .edit-button:checked {{
            background: linear-gradient(to bottom, #27ae60, #1e8449);
            border: 2px solid #186a3b;
            box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.3),
                        0 2px 4px rgba(0, 0, 0, 0.3);
        }}
        """
        
        self.css_provider = Gtk.CssProvider()
        self.css_provider.load_from_data(css.encode('utf-8'))
        
        # Apply to screen
        from gi.repository import Gdk
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen,
            self.css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    # Preserve ALL existing methods:
    # - _on_edit_toggled() ✅
    # - set_edit_palettes() ✅
    # - set_floating_buttons_manager() ✅
    # - set_combined_tools_palette_loader() ✅
    # - set_tools_palette_loader() ✅
    # - set_editing_operations_palette_loader() ✅
    # - get_widget() ✅
    # - is_tools_visible() ✅
    # - set_tools_visible() ✅
```

**Changes Summary**:
- ✨ Add `Path` import for auto-detection
- ✨ Add `load()` method with validation and widget extraction
- ✨ Add `_calculate_target_size()` for dynamic sizing
- ✨ Replace `_apply_styling()` with `_apply_css()` (zoom-style purple container)
- ✨ Add instance variables: `edit_control`, `edit_placeholder`, `target_height`
- ✅ Preserve ALL existing methods and signals
- ✅ Keep green button gradient (brand identity)
- ✅ Keep toggle button functionality

---

### Phase 3: Update Integration 🔌
**File**: `src/shypn/canvas/canvas_overlay_manager.py`

**Find and Update** `_setup_edit_palette()`:

```python
def _setup_edit_palette(self):
    """Create and add edit palette ([E] button for toggling tools)."""
    # Create palette loader instance
    self.edit_palette = create_edit_palette()
    
    # Load UI file and apply zoom-style styling
    # (No need to call load() explicitly - create_edit_palette() does it)
    
    edit_widget = self.edit_palette.get_widget()
    
    if edit_widget:
        self.overlay_widget.add_overlay(edit_widget)
        self.register_palette('edit', self.edit_palette)
        
        # NEW: Set edit palettes for control (OOP system)
        if self.tools_palette and self.operations_palette:
            self.edit_palette.set_edit_palettes(
                self.tools_palette, 
                self.operations_palette
            )
```

**Note**: `create_edit_palette()` already calls `load()` internally, so no changes needed!

---

### Phase 4: Testing & Verification ✅

**Functional Tests**:
1. ✅ Application starts with [E] button in styled purple container
2. ✅ Button is centered with space on left (placeholder visible as empty space)
3. ✅ Clicking [E] toggles tools/operations palettes visibility
4. ✅ Button changes to darker green when checked (tools visible)
5. ✅ Hover effects work (glow, color change)
6. ✅ No errors on startup or during interaction

**Visual Tests**:
1. ✅ Purple gradient container matches mode/zoom palettes
2. ✅ Button size is 28×28px (dynamic from font, minimum 24px)
3. ✅ Positioned at bottom-center with 12px margin
4. ✅ Container has 3px internal padding
5. ✅ Left placeholder creates visible space (center alignment)

**Regression Tests**:
1. ✅ Mode switching still hides edit palettes correctly
2. ✅ [E] button toggle state syncs with palette visibility
3. ✅ `tools-toggled` signal still emitted
4. ✅ All backwards compatibility methods still work

---

## CSS Styling Reference

### Container (.edit-palette)
```css
background: linear-gradient(to bottom, #667eea 0%, #764ba2 100%);
border: 2px solid #5568d3;
border-radius: 8px;
padding: 3px;
box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4),
            0 2px 4px rgba(0, 0, 0, 0.3),
            inset 0 1px 0 rgba(255, 255, 255, 0.2);
```

### Button (.edit-button)
- **Normal**: Green gradient (#2ecc71 → #27ae60)
- **Hover**: Darker green + glow (#27ae60 → #229954)
- **Active**: Even darker (#229954 → #1e8449)
- **Checked**: Dark green with inset shadow (#27ae60 → #1e8449)

### Button Size
- Dynamic: `1.3 × 'W' height` (Pango font metrics)
- Minimum: 24px
- Typical: 24-28px

---

## Design Decisions

### Why Purple Container + Green Button?
- **Container**: Purple (#667eea → #764ba2) maintains visual consistency with mode/zoom palettes
- **Button**: Green (#2ecc71 → #27ae60) preserves edit mode brand identity
- **Result**: Professional unified container style + recognizable green edit button

### Why 2 Button Positions?
- **Expandability**: Left position reserved for future edit mode functionality
  - Potential uses: Quick select mode, Grid snap toggle, Layer controls
- **Symmetry**: Matches mode palette's [E][S] two-button layout
- **Current**: Only [E] button visible, placeholder creates center alignment

### Why 28×28px Buttons?
- **Consistency**: Matches mode palette button size exactly
- **Touch-Friendly**: Large enough for finger interaction
- **Professional**: Not too small (cramped) or too large (childish)
- **Dynamic**: Actually calculated from font metrics (1.3× 'W' height)

---

## File Manifest

### Modified Files
1. **ui/palettes/edit_palette.ui**
   - Add inner `edit_control` styled container
   - Add `edit_placeholder` invisible spacer (28×28px)
   - Change button size from 36×36px → 28×28px
   - Change margin from 24px → 12px
   - Move `edit-palette` CSS class to inner box

2. **src/shypn/helpers/edit_palette_loader.py**
   - Add `load()` method (like mode palette)
   - Add `_calculate_target_size()` for dynamic sizing
   - Replace `_apply_styling()` with `_apply_css()` (purple container)
   - Add `Path` imports and auto-detection
   - Add `edit_control`, `edit_placeholder`, `target_height` variables
   - Preserve ALL existing methods and signals

3. **src/shypn/canvas/canvas_overlay_manager.py**
   - **NO CHANGES NEEDED** - `create_edit_palette()` already calls `load()`

### New Documentation
1. **doc/EDIT_PALETTE_REFACTOR_PLAN.md** (this file)
   - Comprehensive refactoring plan
   - Visual comparisons
   - Implementation phases
   - CSS specifications

2. **doc/EDIT_PALETTE_REFACTOR_COMPLETE.md** (after completion)
   - Testing results
   - Visual verification
   - Success metrics

---

## Success Criteria

| Metric | Target | How to Verify |
|--------|--------|---------------|
| Purple container visible | Yes | Visual inspection |
| [E] button centered with left space | Yes | Visual inspection |
| Button size matches mode palette | 28×28px | Visual comparison |
| Green button gradient preserved | Yes | Visual inspection |
| Toggle functionality works | 100% | Click [E], tools show/hide |
| Dynamic sizing calculated | Font-based | Check logs for "24px" |
| No errors on startup | 0 errors | Check terminal output |
| Backwards compatibility | 100% | All existing features work |

---

## Timeline Estimate

- **Phase 1** (UI restructure): ~15 minutes
- **Phase 2** (Python refactor): ~30 minutes
- **Phase 3** (Integration check): ~5 minutes (no changes needed)
- **Phase 4** (Testing): ~15 minutes
- **Documentation**: ~10 minutes

**Total**: ~75 minutes (1.25 hours)

---

## Related Palettes

This refactor aligns with:
- ✅ **Mode Palette** (`ui/palettes/mode/mode_palette.ui`) - Same container structure
- ✅ **Zoom Palette** (`ui/palettes/zoom/zoom_palette.ui`) - Same CSS styling pattern
- 🔄 **Simulate Palette** (`ui/palettes/simulate_palette.ui`) - Could use same refactor next

---

## Future Expansion Ideas

With the left placeholder position, future enhancements could include:

1. **Quick Select Mode [Q]**: Toggle between pointer and tool mode
2. **Grid Snap Toggle [G]**: Enable/disable grid snapping
3. **Layer Controls [L]**: Quick layer visibility toggle
4. **Undo/Redo Shortcuts**: Quick access to undo/redo
5. **Properties Inspector [P]**: Open properties panel

---

## Notes

- ⚠️ The green button color is intentionally preserved (brand identity for edit mode)
- ⚠️ Placeholder is invisible (`opacity=0`) but reserves space for future expansion
- ⚠️ All existing signal handlers and methods MUST be preserved (backwards compatibility)
- ⚠️ `create_edit_palette()` factory function already calls `load()`, so integration is seamless

---

## Approval Checklist

Before starting implementation:
- [ ] User approves visual design (purple container + green button)
- [ ] User approves 2-button layout (placeholder on left)
- [ ] User approves size changes (36→28px button, 24→12px margin)
- [ ] User confirms no breaking changes to existing functionality

---

**Ready to proceed with implementation?**
