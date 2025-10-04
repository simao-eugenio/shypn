# Simulation Palette Visual Layout

## Final Positioning

### Side-by-Side Button Layout (Bottom Center)
```
                    Canvas Area
                         
                         
                         
    ┌─────────────────────────────────────────────┐
    │                                             │
    │                                             │
    │          Drawing Area                       │
    │                                             │
    │                                             │
    │                                             │
    │            ┌────┐              ┌────┐       │
    │            │ E  │              │ S  │       │ ← 24px from bottom
    │            │    │              │    │       │
    │            └────┘              └────┘       │
    │               ↑                   ↑         │
    │               │                   └─ Red (#e74c3c)
    │               │                     140px offset
    │               │                     (3 button widths gap)
    │               └──────────────────── Green (#2ecc71)
    │                                      center align
    └─────────────────────────────────────────────┘
    
    Button Details:
    - Size: 36x36 pixels each
    - Gap: 140 pixels between buttons (space for ~3 buttons)
    - Edit [E] at center (margin_start=0)
    - Simulate [S] at center+140px (margin_start=140)
```

### Tools Revealed (Vertical Stack)
```
    ┌─────────────────────────────────────┐
    │                                     │
    │          Drawing Area               │
    │                                     │
    │   ┌────┬────┬────┐  ┌────┬────┬────┐│
    │   │ S  │ P  │ T  │  │ R  │ S  │ T  ││ ← Edit tools / Simulate tools
    │   └────┴────┴────┘  └────┴────┴────┘│   (78px from bottom)
    │         ┌────┐         ┌────┐       │
    │         │ E  │         │ S  │       │ ← Toggle buttons
    │         └────┘         └────┘       │   (24px from bottom)
    └─────────────────────────────────────┘
    
    Tools Details:
    - Tool buttons: 40x40 pixels each
    - 2px spacing between tools
    - Slide-up animation: 200ms
    - Edit tools: [S]elect, [P]lace, [T]ransition, [A]rc
    - Simulate tools: [R]un, [S]top, rese[T]
```

## Measurements

### Horizontal Positioning
```
Center line
    │
    ├─────────┐
    │   [E]   │ ← Edit palette
    └─────────┘
    
    ├────────────────────┐
    │ 0px    │   [E]     │ margin_start = 0
    └────────────────────┘
           center
    
    ├──────────────────────────────────────────────────────────┐
    │ 0px    │ 8px│ 36px│ 8px│ 36px│ 8px│ 36px│ 8px│   [S]     │
    └──────────────────────────────────────────────────────────┘
           center  gap   btn   gap   btn   gap   btn   gap
           
           |<────────── 140px total offset ──────────>|
                           
Calculation:
- Gap before: 8px
- Button space 1: 36px
- Gap: 8px
- Button space 2: 36px
- Gap: 8px
- Button space 3: 36px
- Gap after: 8px
- Total: 8 + 36 + 8 + 36 + 8 + 36 + 8 = 140px
```

### Vertical Positioning
```
    ┌────────────┐
    │   Tools    │ ← margin_bottom = 78px
    │            │   (54px above button + 24px button bottom)
    └────────────┘
         │
         │ 54px gap (allows button visibility)
         │
         ▼
    ┌────────────┐
    │   Button   │ ← margin_bottom = 24px
    └────────────┘
         │
         │ 24px gap
         │
         ▼
    ─────────────── Window bottom edge
```

## Color Specifications

### Edit Palette [E] - Green Theme
```
Normal:     #2ecc71 → #27ae60 (gradient top → bottom)
Border:     #229954 (solid 2px)
Hover:      #27ae60 → #229954 (darker gradient)
Active:     #229954 → #1e8449 (darkest)
Shadow:     rgba(0,0,0,0.3) + glow rgba(46,204,113,0.4)
```

### Simulate Palette [S] - Red Theme
```
Normal:     #e74c3c → #c0392b (gradient top → bottom)
Border:     #a93226 (solid 2px)
Hover:      #c0392b → #a93226 (darker gradient)
Active:     #a93226 → #922b21 (darkest)
Shadow:     rgba(0,0,0,0.3) + glow rgba(231,76,60,0.4)
```

### Tool Buttons - White Theme
```css
.sim-tool-button {
    background: #ffffff;
    border: 1px solid rgba(0,0,0,0.08);
    border-radius: 6px;
    box-shadow: 0 1px 2px rgba(0,0,0,0.10);
}

.sim-tool-button:hover {
    background: #f5f5f5;
}

.sim-tool-button:checked {
    background: rgba(255,255,255,0.65);
    border-color: rgba(0,0,0,0.35);
    box-shadow: 0 0 0 2px rgba(0,0,0,0.22) inset;
}
```

## Responsive Behavior

### Window Resize
- Palettes maintain bottom-center position
- Horizontal offset (44px) remains constant
- Tools revealer adapts to available space
- Overlay system prevents canvas content overlap

### Toggle States
1. **Both closed**: Only [E] and [S] buttons visible
2. **Edit open**: [E] pressed, tools revealed above, [S] unpressed
3. **Simulate open**: [S] pressed, tools revealed above, [E] unpressed
4. **Mode switch**: Clicking opposite button closes current, opens new

### Animation
- Revealer uses `slide-up` transition
- Duration: 200ms (smooth but responsive)
- Both palettes animate independently
- No overlap during transitions

## Implementation Notes

### GTK Overlay System
```python
# Main window contains GtkOverlay
overlay_widget = GtkOverlay()
overlay_widget.add(canvas_drawing_area)  # Base layer

# Add palettes as independent overlays
overlay_widget.add_overlay(edit_tools_widget)      # Layer 1
overlay_widget.add_overlay(edit_widget)            # Layer 2
overlay_widget.add_overlay(simulate_tools_widget)  # Layer 3
overlay_widget.add_overlay(simulate_widget)        # Layer 4
```

Each overlay widget uses CSS properties to self-position:
- `halign=center` - Horizontal alignment
- `valign=end` - Vertical alignment (bottom)
- `margin_bottom` - Distance from bottom edge
- `margin_start` - Horizontal offset from alignment point

### Z-Order
1. Canvas (base)
2. Edit tools revealer (layer 1)
3. Edit button (layer 2) ← Appears above edit tools when collapsed
4. Simulate tools revealer (layer 3)
5. Simulate button (layer 4) ← Appears above simulate tools when collapsed

This ensures toggle buttons always remain clickable even when tools are revealed.

## CSS Class Hierarchy

```
.edit-button              (Edit toggle button [E])
.edit-tools-palette       (Container for edit tools)
  .edit-tool-button         (Individual tool buttons S/P/T/A)

.simulate-button          (Simulate toggle button [S])
.simulate-tools-palette   (Container for simulate tools)
  .sim-tool-button          (Individual tool buttons R/S/T)
    .run-button              (Run [R] specific styling)
    .stop-button             (Stop [S] specific styling)
    .reset-button            (Reset [T] specific styling)
```

## Accessibility

### Tooltips
- [E]: "Toggle Edit Tools (Place, Transition, Arc)"
- [S]: "Toggle Simulation Tools (Run, Stop, Reset)"
- [R]: "Run Simulation - Start executing the Petri net"
- [S] (Stop): "Stop Simulation - Pause execution"
- [T]: "Reset Simulation - Reset to initial marking"

### Keyboard Navigation
- Tab: Cycle through visible buttons
- Space/Enter: Activate focused button
- Escape: Close open palette (to be implemented)

### State Indicators
- Disabled state: `opacity: 0.45` + `sensitive: False`
- Active state: Darker gradient + inset shadow
- Hover state: Brighter gradient + enhanced shadow glow

## Testing Checklist

✅ **Visual Tests**:
- [ ] Buttons appear side-by-side (not overlapping)
- [ ] 8px gap visible between [E] and [S]
- [ ] [E] is green, [S] is red
- [ ] Both buttons same size (36x36px)
- [ ] Tools slide up smoothly (200ms)
- [ ] Tool buttons are 40x40px
- [ ] Stop button starts disabled

✅ **Interaction Tests**:
- [ ] Click [E] → Edit tools appear
- [ ] Click [S] → Simulate tools appear
- [ ] Click [E] while [S] open → Edit opens, Simulate closes
- [ ] Hover states show glow effect
- [ ] Tooltips appear on hover

✅ **Integration Tests**:
- [ ] No console errors on palette load
- [ ] Palettes appear on all canvas tabs
- [ ] Window resize maintains position
- [ ] Z-order correct (buttons above tools when collapsed)
