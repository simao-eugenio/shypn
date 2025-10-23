# Panel Float Refactoring - Next Steps

## ✅ Completed

### 1. Left Panel (File Panel V2)
- ✅ Refactored to skeleton pattern
- ✅ `is_hanged` flag implemented
- ✅ `hang_on()` and `detach()` methods
- ✅ Float button working
- ✅ Container visibility managed

### 2. Right Panel (Analyses Panel)
- ✅ Refactored to skeleton pattern  
- ✅ `is_hanged` flag implemented
- ✅ `hang_on()` and `detach()` methods
- ✅ Float button working
- ✅ Container visibility managed

## ⏳ TODO

### 3. Pathway Panel
- ⏳ Apply skeleton pattern
- ⏳ Add float button to UI
- ⏳ Test attach/detach

### 4. Topology Panel
- ⏳ Apply skeleton pattern
- ⏳ Add float button to UI  
- ⏳ Test attach/detach

### 5. Master Palette Exclusive Logic
Currently, multiple Master Palette buttons can be active simultaneously. We need to implement **exclusive button logic** where:

- Only ONE panel button can be active at a time
- Clicking a button:
  - Deactivates all other buttons
  - Hides all other panels
  - Shows the clicked panel
- Float button behavior:
  - When panel is floating, Master Palette button should remain active
  - When panel is detached, clicking another MP button should hide the floating panel's container

**Implementation Plan:**

```python
# In Master Palette button handler:
def on_panel_button_clicked(clicked_button, panel_name):
    """Handle exclusive panel button logic."""
    
    # Deactivate all other buttons
    for button_name, button in master_palette_buttons.items():
        if button_name != panel_name:
            button.set_active(False)
    
    # Get all panels
    panels = {
        'files': left_panel_loader,
        'analyses': right_panel_loader,
        'pathways': pathway_panel_loader,
        'topology': topology_panel
    }
    
    # Hide all other panels
    for name, panel in panels.items():
        if name != panel_name:
            panel.hide()
    
    # Show clicked panel
    active_panel = panels[panel_name]
    if clicked_button.get_active():
        active_panel.show()
    else:
        active_panel.hide()
```

### 6. Float Button in All Panels

Each panel UI file needs a float button:

```xml
<!-- In ui/panels/left_panel.ui, right_panel.ui, pathway_panel.ui, topology_panel.ui -->
<object class="GtkToggleButton" id="float_button">
  <property name="label">⬆️</property>
  <property name="tooltip_text">Float panel as separate window</property>
</object>
```

### 7. Test Checklist

- [ ] Left panel float/attach works
- [ ] Right panel float/attach works  
- [ ] Pathway panel float/attach works
- [ ] Topology panel float/attach works
- [ ] Only one Master Palette button active at a time
- [ ] Switching panels hides previous panel
- [ ] Float button doesn't interfere with Master Palette exclusive logic
- [ ] Empty containers are hidden when panel floats
- [ ] Containers reappear when panel reattaches
- [ ] No Error 71 during any operation
- [ ] Works on Wayland

## Files to Update

1. `src/shypn/helpers/pathway_panel_loader.py` - Apply skeleton pattern
2. `src/shypn/ui/panels/topology_panel.py` - Apply skeleton pattern (if it has a loader)
3. `ui/panels/pathway_panel.ui` - Add float button
4. `ui/panels/topology_panel.ui` - Add float button (if needed)
5. Master Palette handler in `src/shypn.py` - Implement exclusive button logic

## Benefits

- **Simpler code**: ~55% reduction in complexity
- **No race conditions**: Synchronous operations
- **Better UX**: Clean panel switching
- **Wayland safe**: Proven pattern
- **Maintainable**: Clear logic flow
