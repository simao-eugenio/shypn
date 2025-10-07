# Mode Palette Refactor Plan - Match Zoom Palette Style

**Date**: October 7, 2025  
**Objective**: Refactor mode palette to match zoom palette's visual style, structure, and characteristics

## Current State Analysis

### Zoom Palette Structure
```
GtkBox (zoom_control_container) - vertical, bottom-right
├── GtkRevealer (zoom_revealer) - slide-down animation, 200ms
│   └── GtkBox (revealer content) - vertical
│       ├── Buttons: 25%, 50%, 75%, 100%, 150%, 200%, 400%
│       ├── GtkSeparator
│       └── Button: Fit
└── GtkBox (zoom_control) - horizontal, main palette
    ├── Button: [-] Zoom Out
    ├── Button: [100%] Display (toggles revealer)
    └── Button: [+] Zoom In
```

**Key Characteristics**:
- **Container**: GtkBox, vertical orientation, spacing=18
- **Positioning**: halign=end, valign=end, margin-end=12, margin-bottom=12
- **Main Palette**: GtkBox horizontal with CSS class "zoom-palette"
- **Revealer**: Above main palette, slide-down transition, 200ms duration
- **CSS Styling**:
  - Gradient background: `#667eea → #764ba2` (purple gradient)
  - Border: 2px solid `#5568d3`
  - Border radius: 8px
  - Padding: 3px
  - Box shadow: Multiple layers (outer + inset glow)
- **Button Style**:
  - White gradient background: `#ffffff → #f0f0f5`
  - Border: 2px solid `#5568d3`
  - Border radius: 5px
  - Font: 18px, bold, color `#667eea`
  - Size: min-width/height = 28px (calculated as 1.3× font 'W' height)
  - Hover: Light blue background, glowing shadow
  - Active: Darker blue, inset shadow

### Current Mode Palette Structure
```
GtkBox (mode_palette_container) - horizontal, bottom-left
├── Button: [Edit] - 64×40px
└── Button: [Sim] - 64×40px
```

**Current Characteristics**:
- **Container**: GtkBox, horizontal, spacing=12
- **Positioning**: halign=start, valign=end, margin-left=24, margin-bottom=24
- **No revealer**: Just two buttons side by side
- **Minimal styling**: Basic button appearance
- **CSS Classes**: mode-palette, mode-button, edit-button, simulate-button

## Refactor Plan

### Phase 1: UI File Restructuring

**File**: `ui/palettes/mode/mode_palette.ui`

**Changes**:
1. **Match Zoom Container Structure**:
   ```xml
   <object class="GtkBox" id="mode_palette_container">
     <property name="orientation">horizontal</property>  <!-- Keep horizontal -->
     <property name="spacing">0</property>  <!-- No spacing, tight layout -->
     <property name="halign">start</property>  <!-- Bottom-left -->
     <property name="valign">end</property>
     <property name="margin-start">12</property>  <!-- Match zoom: 12px -->
     <property name="margin-bottom">12</property>  <!-- Match zoom: 12px -->
   ```

2. **Add Styled Inner Box** (like zoom_control):
   ```xml
   <child>
     <object class="GtkBox" id="mode_control">
       <property name="orientation">horizontal</property>
       <property name="spacing">0</property>
       <style>
         <class name="mode-palette"/>
       </style>
       
       <!-- Buttons go here -->
     </object>
   </child>
   ```

3. **Adjust Button Sizes**:
   - Change from 64×40px to match zoom buttons
   - Use dynamic sizing: min-width/height based on font metrics (like zoom)
   - Target: ~28px × 28px (compact square buttons)
   - Labels: "E" and "S" (single letter, like zoom +/-)

4. **Add CSS Classes**:
   - Keep: `mode-button`, `edit-button`, `simulate-button`
   - Match zoom structure for consistent styling

### Phase 2: Python Loader Refactoring

**File**: `src/ui/palettes/mode/mode_palette_loader.py`

**Changes**:

1. **Match Zoom Class Structure**:
   ```python
   class ModePaletteLoader(GObject.GObject):
       def __init__(self, ui_path=None):
           # Auto-detect UI path (like zoom)
           if ui_path is None:
               repo_root = Path(__file__).parent.parent.parent.parent
               ui_path = os.path.join(repo_root, 'ui', 'palettes', 'mode', 'mode_palette.ui')
           
           self.builder = Gtk.Builder()
           self.mode_palette_container = None  # Main container
           self.mode_control = None  # Inner styled box
           self.edit_button = None
           self.sim_button = None
           
           self.css_provider = None
           self.target_height = 28  # Calculated from font metrics
   ```

2. **Add Font Metrics Calculation** (from zoom):
   ```python
   def _calculate_target_size(self):
       """Calculate target button size as 1.3× the height of 'W' character."""
       temp_label = Gtk.Label(label="W")
       layout = temp_label.get_layout()
       if layout:
           ink_rect, logical_rect = layout.get_pixel_extents()
           w_height = logical_rect.height
           self.target_height = int(w_height * 1.3)
           if self.target_height < 24:
               self.target_height = 24
       else:
           self.target_height = 28
   ```

3. **Add load() Method**:
   ```python
   def load(self):
       """Load the mode palette UI and return the widget."""
       if not os.path.exists(self.ui_path):
           raise FileNotFoundError(f"Mode palette UI file not found: {self.ui_path}")
       
       self.builder.add_from_file(self.ui_path)
       self.mode_palette_container = self.builder.get_object('mode_palette_container')
       self.mode_control = self.builder.get_object('mode_control')
       self.edit_button = self.builder.get_object('edit_mode_button')
       self.sim_button = self.builder.get_object('sim_mode_button')
       
       if self.mode_palette_container is None:
           raise ValueError("Object 'mode_palette_container' not found")
       
       self._calculate_target_size()
       self._apply_styling()
       self._connect_signals()
       
       return self.mode_palette_container
   ```

### Phase 3: CSS Styling (Match Zoom Palette)

**File**: `src/ui/palettes/mode/mode_palette_loader.py` (in `_apply_styling()` method)

**New CSS** (adapted from zoom):
```python
def _apply_styling(self):
    """Apply custom CSS styling to match zoom palette."""
    css = f"""
    .mode-palette {{
        background: linear-gradient(to bottom, #667eea 0%, #764ba2 100%);
        border: 2px solid #5568d3;
        border-radius: 8px;
        padding: 3px;
        box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4),
                    0 2px 4px rgba(0, 0, 0, 0.3),
                    inset 0 1px 0 rgba(255, 255, 255, 0.2);
    }}
    
    .mode-button {{
        background: linear-gradient(to bottom, #ffffff 0%, #f0f0f5 100%);
        border: 2px solid #5568d3;
        border-radius: 5px;
        font-size: 18px;
        font-weight: bold;
        color: #667eea;
        min-width: {self.target_height}px;
        min-height: {self.target_height}px;
        padding: 0;
        margin: 0;
        transition: all 200ms ease;
    }}
    
    .mode-button:hover {{
        background: linear-gradient(to bottom, #e8f0ff 0%, #d5e5ff 100%);
        border-color: #667eea;
        color: #5568d3;
        box-shadow: 0 0 8px rgba(102, 126, 234, 0.5);
    }}
    
    .mode-button:active {{
        background: linear-gradient(to bottom, #d0e0ff 0%, #c0d5ff 100%);
        box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.2);
    }}
    
    /* Active mode highlighting */
    .mode-button.active-mode {{
        background: linear-gradient(to bottom, #3498db, #2980b9);
        border: 2px solid #2471a3;
        font-weight: bold;
        color: white;
        box-shadow: inset 0 1px 3px rgba(255, 255, 255, 0.3),
                    0 2px 4px rgba(0, 0, 0, 0.3);
    }}
    
    .mode-button:not(.active-mode) {{
        opacity: 0.9;
    }}
    
    .mode-button:not(.active-mode):hover {{
        opacity: 1.0;
    }}
    """
    
    self.css_provider = Gtk.CssProvider()
    self.css_provider.load_from_data(css.encode('utf-8'))
    
    from gi.repository import Gdk
    screen = Gdk.Screen.get_default()
    Gtk.StyleContext.add_provider_for_screen(
        screen,
        self.css_provider,
        Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
    )
```

### Phase 4: Integration Updates

**File**: `src/shypn/canvas/canvas_overlay_manager.py`

**Changes**:
1. Update `_setup_mode_palette()` to call `load()`:
   ```python
   def _setup_mode_palette(self):
       self.mode_palette = ModePaletteLoader()
       mode_widget = self.mode_palette.load()  # Call load() explicitly
       
       if mode_widget:
           self.overlay_widget.add_overlay(mode_widget)
           self.register_palette('mode', self.mode_palette)
           self.update_palette_visibility('edit')
   ```

2. **Optional**: Add factory function to mode_palette_loader.py:
   ```python
   def create_mode_palette(ui_path=None):
       """Factory function to create and load the mode palette."""
       palette = ModePaletteLoader(ui_path)
       palette.load()
       return palette
   ```

## Visual Comparison

### Before (Current):
```
┌─────────────────────┐
│  Edit  │    Sim     │  ← Plain buttons, 64×40px, spaced apart
└─────────────────────┘
```

### After (Zoom-styled):
```
╔═══════════╗
║ E │ S ║  ← Compact buttons in styled container
╚═══════════╝
- Purple gradient background (#667eea → #764ba2)
- White button gradients with purple border
- Active button: Blue highlight
- 28×28px buttons (dynamic sizing)
- 8px border radius
- Multi-layer shadows
- Positioned at bottom-left (12px margins)
```

## Benefits

1. **Visual Consistency**: Mode palette matches zoom palette aesthetics
2. **Professional Look**: Gradient backgrounds, shadows, hover effects
3. **Compact Design**: Smaller buttons (E/S) vs (Edit/Sim) saves space
4. **Better UX**: Clear visual feedback for active mode
5. **Code Consistency**: Same structure as zoom palette (easier maintenance)
6. **Dynamic Sizing**: Buttons scale with font size (accessibility)

## Implementation Order

1. ✅ **Phase 1**: Restructure UI file (`mode_palette.ui`)
   - Add mode_control inner box
   - Adjust margins to 12px
   - Change button sizes and labels

2. ✅ **Phase 2**: Refactor Python loader
   - Add load() method
   - Add font metrics calculation
   - Match zoom class structure

3. ✅ **Phase 3**: Apply CSS styling
   - Port zoom palette CSS
   - Add active-mode highlighting
   - Test hover/active states

4. ✅ **Phase 4**: Update integration
   - Modify canvas_overlay_manager setup
   - Test mode switching
   - Verify positioning

5. ✅ **Phase 5**: Testing & Polish
   - Test on different screen sizes
   - Verify active mode highlighting
   - Check button interactions
   - Ensure no regressions

## Files to Modify

1. `ui/palettes/mode/mode_palette.ui` - UI structure
2. `src/ui/palettes/mode/mode_palette_loader.py` - Loader class
3. `src/shypn/canvas/canvas_overlay_manager.py` - Integration
4. Test mode switching and visual appearance

## Expected Result

A compact, professionally-styled mode palette at bottom-left that:
- Matches zoom palette's visual design
- Has [E] and [S] buttons in a purple-gradient container
- Shows clear visual feedback for active mode
- Integrates seamlessly with existing overlay system
- Maintains all current functionality (mode switching, button states)

## Notes

- Keep existing signal structure (`mode-changed`)
- Maintain current mode logic (Edit/Sim switching)
- Active mode highlighting still uses CSS class approach
- Position stays at bottom-left (start alignment)
- No revealer needed (unlike zoom) - just the styled button container
