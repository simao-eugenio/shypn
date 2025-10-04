# Mode Palette Implementation Plan

## Completed Tasks ✓

### 1. Mode Palette UI Creation ✓
- **File**: `ui/palettes/mode/mode_palette.ui`
- **Status**: Created and validated
- **Features**:
  - GtkBox container with horizontal orientation
  - Two buttons: Edit and Sim
  - Positioned at bottom center (halign=center, valign=end)
  - 24px margin from bottom
  - Custom CSS classes for styling
  - Tooltips for user guidance

### 2. Mode Palette Loader ✓
- **File**: `src/ui/palettes/mode/mode_palette_loader.py`
- **Status**: Created and syntax-validated
- **Features**:
  - Extends GObject.GObject for signal support
  - Emits 'mode-changed' signal with mode parameter
  - Manages button states (insensitive for active mode)
  - Methods: on_edit_clicked(), on_sim_clicked(), update_button_states()
  - Default mode: 'edit'
  - get_widget() returns the container for overlay integration

### 3. Package Structure ✓
- **File**: `src/ui/palettes/mode/__init__.py`
- **Status**: Created
- **Exports**: ModePaletteLoader

### 4. Integration with ModelCanvasLoader ✓
- **File**: `src/shypn/helpers/model_canvas_loader.py`
- **Status**: Updated and syntax-validated
- **Changes**:
  - Import ModePaletteLoader
  - Added mode_palettes dictionary for tracking
  - Create mode palette in _setup_canvas_manager()
  - Add mode palette as overlay at bottom center
  - Connect mode-changed signal
  - Initialize with edit mode (palettes visible)

### 5. Mode Change Handlers ✓
- **Methods Added**:
  - `_on_mode_changed()`: Signal handler for mode switches
  - `_update_palette_visibility()`: Shows/hides palettes per mode
- **Logic**:
  - Edit mode: Show edit palettes, hide sim palettes
  - Sim mode: Show sim palettes, hide edit palettes
  - Respects palette controllers (doesn't force-show tools)

### 6. Documentation ✓
- **File**: `doc/mode_palette_implementation.md`
- **Status**: Created
- **Content**: Architecture, flow, benefits, next steps

## Testing Checklist

### Basic Functionality
- [ ] Application starts without errors
- [ ] Mode palette appears at bottom center
- [ ] Edit button visible and sensitive by default
- [ ] Sim button visible and sensitive by default
- [ ] Edit palettes visible by default
- [ ] Simulation palettes hidden by default

### Mode Switching
- [ ] Clicking Edit button when in sim mode switches to edit mode
- [ ] Clicking Sim button when in edit mode switches to sim mode
- [ ] Active mode button becomes insensitive
- [ ] Inactive mode button becomes sensitive
- [ ] Edit palettes show in edit mode only
- [ ] Simulation palettes show in sim mode only
- [ ] No palette overlap occurs

### Signal Flow
- [ ] mode-changed signal emitted on button click
- [ ] _on_mode_changed() handler called correctly
- [ ] _update_palette_visibility() updates UI correctly
- [ ] Canvas manager state synced with mode (if needed)

### Edge Cases
- [ ] Rapid mode switching works correctly
- [ ] Multiple tabs maintain independent mode states
- [ ] Mode palette survives tab switching
- [ ] Mode persists across new document creation

## Known Limitations

1. **Mode State Persistence**: Mode state is not currently persisted across application sessions
2. **Keyboard Shortcuts**: No keyboard shortcuts for mode switching (e.g., Tab key)
3. **Visual Feedback**: No animations or transitions during mode switching
4. **CSS Styling**: Mode buttons use default GTK styling (no custom theme yet)

## Future Enhancements

### Priority 1: Essential
- [ ] Test in running application with user interaction
- [ ] Fix any runtime errors discovered during testing
- [ ] Add keyboard shortcut for mode switching (Tab or Ctrl+M)
- [ ] Persist mode state in view state file

### Priority 2: Polish
- [ ] Add CSS styling for mode buttons (active/inactive visual states)
- [ ] Add smooth transitions/animations during mode switch
- [ ] Add mode indicator to status bar or window title
- [ ] Add tooltips with keyboard shortcuts

### Priority 3: Advanced
- [ ] Per-tab mode state tracking
- [ ] Mode history for undo/redo
- [ ] Configurable mode button labels/icons
- [ ] Plugin architecture for adding custom modes

## Validation Steps

### 1. Static Analysis ✓
```bash
# Syntax check
python3 -m py_compile src/ui/palettes/mode/mode_palette_loader.py
python3 -m py_compile src/shypn/helpers/model_canvas_loader.py

# XML validation
xmllint --noout ui/palettes/mode/mode_palette.ui
```

### 2. Import Test
```bash
# Run test script
python3 tests/test_mode_palette.py
```

### 3. Runtime Test
```bash
# Start application
cd /home/simao/projetos/shypn
./shypn.sh
```

**Test Procedure**:
1. Open application
2. Verify mode palette at bottom center
3. Click Sim button → verify edit palettes hide, sim palettes show
4. Click Edit button → verify sim palettes hide, edit palettes show
5. Repeat several times to ensure stability
6. Create new tab → verify mode palette present
7. Switch tabs → verify mode states independent

## Integration Points

### Required Interfaces
- **GObject signals**: mode-changed(str mode)
- **GTK overlay system**: add_overlay() for floating widgets
- **Palette visibility**: show()/hide() methods
- **Widget references**: edit_palette, edit_tools_palette, simulate_palette, simulate_tools_palette

### Dependencies
- GTK 3.0
- GObject introspection
- Cairo (indirect, for canvas rendering)
- ModelCanvasManager (for palette integration)

### Signal Chain
```
User clicks button
  ↓
ModePaletteLoader.on_edit_clicked/on_sim_clicked
  ↓
emit('mode-changed', mode)
  ↓
ModelCanvasLoader._on_mode_changed
  ↓
ModelCanvasLoader._update_palette_visibility
  ↓
palette.get_widget().show()/hide()
  ↓
UI updates
```

## Rollback Plan

If issues arise, remove mode palette integration:

1. **Remove Import**:
   ```python
   # Remove from model_canvas_loader.py
   from ui.palettes.mode.mode_palette_loader import ModePaletteLoader
   ```

2. **Remove State**:
   ```python
   # Remove from __init__
   self.mode_palettes = {}
   ```

3. **Remove Integration**:
   - Remove mode palette creation in _setup_canvas_manager()
   - Remove mode-changed signal connection
   - Remove _on_mode_changed() method
   - Remove _update_palette_visibility() method
   - Remove initial palette visibility call

4. **Restore Default Behavior**:
   - Show all palettes by default
   - Remove mode-based visibility logic

## Code Review Checklist

- [x] Code follows Python PEP 8 style guidelines
- [x] All methods have docstrings
- [x] Signal names follow GTK conventions (lowercase, hyphenated)
- [x] Error handling for missing widgets
- [x] Proper use of GObject signal system
- [x] No hardcoded paths (uses builder for UI)
- [x] Consistent naming conventions
- [x] No duplicate code
- [x] Proper resource cleanup (if needed)

## Performance Considerations

- **Minimal Overhead**: Mode switching only shows/hides widgets, no data reconstruction
- **Signal Efficiency**: Single signal emission per mode switch
- **Memory Usage**: One mode palette instance per drawing area
- **Rendering**: No additional draw calls, uses existing overlay system

## Security Considerations

None. This is a UI-only feature with no:
- File system access (UI file loaded by GTK)
- Network operations
- External process execution
- User data storage (beyond in-memory mode state)

## Accessibility Considerations

- [ ] Add keyboard shortcuts for mode switching
- [ ] Ensure proper tab order for keyboard navigation
- [ ] Add ARIA labels for screen readers (if supported by GTK)
- [ ] Ensure sufficient color contrast for button states
- [ ] Add focus indicators for keyboard users

## Conclusion

The mode palette implementation is **complete and ready for testing**. All code has been syntax-validated and follows the established architecture. The next step is to run the application in a proper environment and test the user interaction flow.
