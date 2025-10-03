# Context Menu - Final Fix: Event Sequence Claiming

## Root Cause Identified! 🎯

**The TreeView was intercepting right-clicks and selecting items, preventing the context menu from showing!**

### The Problem

When right-clicking anywhere in the file browser:
1. TreeView receives the click event
2. TreeView selects the first item in the row
3. Our context menu handler runs, but the event is already consumed
4. Menu code executes (`popup()` or `present()` called) but nothing appears
5. User only sees the selection highlight change

### The Solution

Two critical changes:

#### 1. Set Propagation Phase to CAPTURE
```python
gesture_click.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)
```

This makes our handler run **BEFORE** the TreeView's internal selection logic.

#### 2. Claim the Event Sequence
```python
sequence = gesture.get_current_sequence()
gesture.set_state(Gtk.EventSequenceState.CLAIMED)
```

This tells GTK: "We're handling this event, don't let other widgets process it!"

## Code Changes

### File: `src/shypn/ui/panels/file_explorer_panel.py`

#### In `_connect_signals()` method (~line 280):

**Before:**
```python
gesture_click = Gtk.GestureClick.new()
gesture_click.set_button(3)
gesture_click.connect("pressed", self._on_tree_view_right_click)
self.tree_view.add_controller(gesture_click)
```

**After:**
```python
gesture_click = Gtk.GestureClick.new()
gesture_click.set_button(3)
gesture_click.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)  # ← NEW!
gesture_click.connect("pressed", self._on_tree_view_right_click)
self.tree_view.add_controller(gesture_click)
```

#### In `_on_tree_view_right_click()` method (~line 545):

**Added at the beginning:**
```python
# Claim the sequence to prevent TreeView from processing this click
sequence = gesture.get_current_sequence()
gesture.set_state(Gtk.EventSequenceState.CLAIMED)
```

## GTK4 Event Propagation

### Event Phases (in order):
1. **CAPTURE** - Top-down from root to target
2. **TARGET** - At the target widget
3. **BUBBLE** - Bottom-up from target to root

### Default Behavior:
- Most widgets handle events in TARGET or BUBBLE phase
- TreeView selection happens in TARGET phase
- Our gesture was probably in BUBBLE phase (too late!)

### Our Fix:
- Set our gesture to CAPTURE phase
- We get the event FIRST
- We claim it
- TreeView never sees it
- Context menu shows! ✅

## Event Sequence States

```python
Gtk.EventSequenceState.NONE     # Event continues propagating
Gtk.EventSequenceState.CLAIMED  # This handler owns the event
Gtk.EventSequenceState.DENIED   # Reject the event
```

By setting `CLAIMED`, we tell GTK:
- "This right-click is for the context menu"
- "Don't let TreeView select items"
- "Don't propagate further"

## Testing

### Quick Test:
```bash
cd /home/simao/projetos/shypn
python3 src/shypn.py
```

### What to Check:
1. ✅ Right-click on file - Menu appears (no selection)
2. ✅ Right-click on folder - Menu appears (no selection)
3. ✅ Right-click on empty space - Menu appears
4. ✅ Left-click still selects items normally
5. ✅ Double-click still activates items

### Debug Output:
```
🖱️  Right-click detected at (x, y)
✓ Context menu exists
  → Clicked on item: filename.txt
  → Showing context menu...
  → popup() called
```

## Why This Matters

This is a common GTK4 pitfall:

### GTK3 (Old Way):
```python
def on_button_press(widget, event):
    if event.button == 3:  # Right-click
        menu.popup(...)
        return True  # Stop propagation
```

### GTK4 (New Way):
```python
gesture = Gtk.GestureClick.new()
gesture.set_button(3)
gesture.set_propagation_phase(Gtk.PropagationPhase.CAPTURE)  # Important!
gesture.connect("pressed", handler)

def handler(gesture, n, x, y):
    gesture.set_state(Gtk.EventSequenceState.CLAIMED)  # Important!
    menu.popup()
```

## Summary

| Issue | Symptom | Solution |
|-------|---------|----------|
| TreeView intercepts clicks | Selection changes, no menu | Set CAPTURE phase |
| Event propagates to TreeView | Menu code runs but nothing shows | Claim event sequence |
| Right-click selects first item | Unexpected selection highlight | Both fixes together |

## Files Modified

1. **src/shypn/ui/panels/file_explorer_panel.py**
   - Added `set_propagation_phase(Gtk.PropagationPhase.CAPTURE)` for both gestures
   - Added `gesture.set_state(Gtk.EventSequenceState.CLAIMED)` in handler

## References

- GTK4 Event Controllers: https://docs.gtk.org/gtk4/class.EventController.html
- Gesture Click: https://docs.gtk.org/gtk4/class.GestureClick.html
- Event Propagation: https://docs.gtk.org/gtk4/event-propagation.html

## Status

✅ Event propagation fixed
✅ Event sequence claimed
✅ Context menu should now appear
⏳ Awaiting user confirmation

---

**The context menu should now work! Right-click anywhere in the file browser to test it.** 🎉
