# Floating Palette Gesture Controls

## Overview

The Swiss Knife Palette uses intuitive gestures instead of separate control buttons. This provides a cleaner UI and more natural interaction.

## Gesture Guide

### 🖱️ Double-Click to Float/Attach

**Action**: Double-click on empty palette space  
**Result**: Toggle between floating and attached modes

```
┌─────────────────────────┐
│ [Edit] [Simulate] [Lay] │ ← Double-click here
│                         │    (empty space above buttons)
│    🖱️  Double Click     │
│                         │
└─────────────────────────┘

State Changes:
Attached → Floating: Palette detaches from bottom, can be moved
Floating → Attached: Palette snaps back to bottom-center
```

### 🤚 Click + Drag to Move (Floating Mode Only)

**Action**: Click and drag on empty palette space  
**Requirement**: Palette must be floating first (double-click to float)  
**Result**: Move palette to any screen position

```
┌─────────────────────────┐
│ [Edit] [Simulate] [Lay] │
│                         │
│    🤚 Click & Drag      │ ← Click here and move mouse
│      (when floating)    │
└─────────────────────────┘

Cursor Feedback:
- Default: Normal arrow cursor
- Hover over floating palette: 'grab' cursor (open hand ✋)
- While dragging: 'grabbing' cursor (closed fist ✊)
```

### 🎯 Tool Buttons Still Work Normally

**Important**: Buttons and tools work as expected. The gestures only activate on **empty space**.

```
┌─────────────────────────┐
│ [Edit] [Simulate] [Lay] │ ← Click = change category (normal)
│                         │
│  ┌───┐ ┌───┐ ┌───┐     │ ← Click tools = activate (normal)
│  │ P │ │ T │ │ A │     │
│  └───┘ └───┘ └───┘     │
│                         │ ← Empty space = gesture area
└─────────────────────────┘
```

## Detailed Workflow

### Starting State: Attached (Default)

```
                Canvas Area
┌────────────────────────────────────┐
│                                    │
│                                    │
│         Canvas Content             │
│                                    │
│                                    │
│    ┌───────────────────────┐      │
│    │ Swiss Knife Palette   │      │ ← Attached at bottom-center
│    │ [Edit] [Simul] [Lay]  │      │
│    └───────────────────────┘      │
└────────────────────────────────────┘

- Fixed position at bottom-center
- margin_bottom = 20px
- Cannot be dragged (attached)
- Cursor: Normal
```

### Step 1: Float the Palette

**Action**: Double-click on empty palette space

```
                Canvas Area
┌────────────────────────────────────┐
│                                    │
│                                    │
│  ┌───────────────────────┐        │ ← Now floating
│  │ Swiss Knife Palette   │        │   (position varies)
│  │ [Edit] [Simul] [Lay]  │        │
│  └───────────────────────┘        │
│                                    │
└────────────────────────────────────┘

- Position: Last known floating position
- Can now be dragged
- Cursor: 'grab' when hovering ✋
```

### Step 2: Drag to Reposition

**Action**: Click + drag on empty space

```
                Canvas Area
┌────────────────────────────────────┐
│                    ┌──────────┐    │
│                    │ Palette  │    │ ← Move anywhere
│                    │ [E][S][L]│    │
│                    └──────────┘    │
│         OR                         │
│  ┌──────────┐                      │
│  │ Palette  │                      │ ← Or here
│  │ [E][S][L]│                      │
│  └──────────┘                      │
└────────────────────────────────────┘

- Drag freely within canvas
- Position bounded to keep mostly visible
- Cursor: 'grabbing' while dragging ✊
```

### Step 3: Attach Back to Bottom

**Action**: Double-click again on empty space

```
                Canvas Area
┌────────────────────────────────────┐
│                                    │
│                                    │
│         Canvas Content             │
│                                    │
│                                    │
│    ┌───────────────────────┐      │
│    │ Swiss Knife Palette   │      │ ← Back to bottom-center
│    │ [Edit] [Simul] [Lay]  │      │
│    └───────────────────────┘      │
└────────────────────────────────────┘

- Returns to bottom-center position
- Cannot be dragged anymore
- Cursor: Normal
```

## Technical Details

### Event Detection

```python
# EventBox wraps main_container to capture events
drag_event_box = Gtk.EventBox()
drag_event_box.add(main_container)

# Events enabled
- BUTTON_PRESS_MASK    # Single/double click detection
- BUTTON_RELEASE_MASK  # End drag
- POINTER_MOTION_MASK  # Drag movement
```

### Double-Click Detection

```python
def _on_button_press(widget, event):
    if event.type == Gdk.EventType.DOUBLE_BUTTON_PRESS:
        # Toggle float/attach
        is_floating = not is_floating
        emit('float-toggled', is_floating)
```

### Drag Detection

```python
def _on_button_press(widget, event):
    if event.type == Gdk.EventType.BUTTON_PRESS and is_floating:
        # Start drag
        drag_active = True
        drag_start_x = event.x_root
        drag_start_y = event.y_root

def _on_drag_motion(widget, event):
    if drag_active:
        # Calculate delta and emit
        dx = event.x_root - drag_start_x
        dy = event.y_root - drag_start_y
        emit('position-changed', dx, dy)
```

### Event Propagation

Events propagate to child widgets (buttons/tools) when:
- Not a double-click
- Not actively dragging
- Return `False` from handler

This ensures buttons work normally while gestures are active.

## Visual Feedback

### Cursor States

| State | Cursor | Description |
|-------|--------|-------------|
| Attached | → (default) | Normal arrow, palette fixed |
| Floating (hover) | ✋ (grab) | Open hand, can drag |
| Dragging | ✊ (grabbing) | Closed fist, actively moving |
| Over buttons | → (default) | Normal arrow, buttons work |

### Position Bounds

Palette is kept mostly visible:
- Minimum visible: 50px from any edge
- Prevents accidental loss off-screen
- Dynamic bounds based on viewport size

```python
min_visible = 50
new_left = max(-palette_width + min_visible,
               min(viewport_width - min_visible,
                   current_left + dx))
```

## Comparison: Before vs After

### Before (Commit 4c517be)

```
┌─────────────────────────┐
│ ⋮⋮ ↖                    │ ← Separate controls overlay
├─────────────────────────┤   (50px extra height)
│ [Edit] [Simulate] [Lay] │
│                         │
│  ┌───┐ ┌───┐ ┌───┐     │
│  │ P │ │ T │ │ A │     │
│  └───┘ └───┘ └───┘     │
└─────────────────────────┘

Controls:
- Drag handle (⋮⋮): Click to drag
- Button (↖/📌): Click to toggle
- Always visible (visual clutter)
- Extra height required
```

### After (Commit 41f7dea)

```
┌─────────────────────────┐
│ [Edit] [Simulate] [Lay] │ ← Clean, no overlay
│                         │   
│  ┌───┐ ┌───┐ ┌───┐     │
│  │ P │ │ T │ │ A │     │
│  └───┘ └───┘ └───┘     │
└─────────────────────────┘

Gestures:
- Double-click empty space: Toggle
- Click + drag empty space: Move
- Cleaner visual design
- More intuitive interaction
- No extra height needed
```

## Usage Tips

1. **Double-click anywhere safe**: Any empty palette space works - above buttons, between tools, etc.

2. **Drag from any empty spot**: When floating, grab any empty area to move (not just one handle)

3. **Buttons always work**: Tool buttons and category buttons work normally - gestures don't interfere

4. **Visual feedback**: Watch the cursor change to know when palette is floating and draggable

5. **Quick toggle**: Double-click is fast for switching between modes

## Known Behaviors

### Expected Behaviors

- ✅ Palette starts attached at bottom-center
- ✅ First double-click floats palette at current position
- ✅ Drag only works when floating
- ✅ Second double-click returns to bottom-center
- ✅ Buttons work in both attached and floating modes
- ✅ Cursor changes provide clear feedback

### Edge Cases

- **Fast double-click on button**: Button action takes precedence (buttons capture events first)
- **Drag from button**: Won't drag (buttons handle their own clicks)
- **Resize window while floating**: Palette repositions to stay visible
- **Small viewport**: Palette may overlap canvas content (by design)

## Keyboard Shortcuts (Future)

Potential additions:
- `Ctrl+D`: Toggle float/attach
- `Arrow keys`: Nudge position when floating
- `Ctrl+Home`: Return to bottom-center
- `Ctrl+1/2/3/4`: Jump to preset corners

## Accessibility

- **Mouse-only**: Current implementation requires mouse for gestures
- **Future**: Add keyboard shortcuts for non-mouse users
- **Screen readers**: EventBox is transparent to assistive technology

## Related Documentation

- `FLOATING_PALETTE_CANVAS_TRANSFORMATIONS.md` - Canvas transformation awareness
- `SWISSKNIFE_PALETTE_REFACTORING_PHASE3.md` - Overall palette architecture
- Feature commits:
  - `41f7dea` - Gesture-based controls (this feature)
  - `4c517be` - Previous separate controls version
  - `a706cd5` - Canvas transformation documentation

## Status

- ✅ **Double-click to toggle**: Working
- ✅ **Click + drag to move**: Working
- ✅ **Cursor feedback**: Working
- ✅ **Button compatibility**: Working
- ⏰ **Keyboard shortcuts**: Not implemented
- ⏰ **Touch gestures**: Not implemented

Last updated: 2025-10-23
