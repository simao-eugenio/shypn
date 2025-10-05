# Auto-Tracking Diagnostics Feature

## Overview

The diagnostics panel now **automatically tracks and displays** the most recently fired transition during simulation. No manual selection needed!

## How It Works

### Auto-Tracking Algorithm

1. **Timer runs every 500ms** while panel is visible
2. **Scans all transitions** in the model
3. **Finds the most recently fired** transition
4. **Switches display** if a newer transition fired in the last 2 seconds
5. **Updates continuously** during simulation

### Smart Behavior

**During Simulation:**
- ✅ Automatically shows the "hottest" (most active) transition
- ✅ Switches when a different transition becomes more active
- ✅ Shows "(auto-tracking)" indicator in label
- ✅ No manual selection needed

**Before Simulation:**
- Shows "Auto-tracking: Waiting for transition activity..."
- Explains how to manually select a transition
- Enables immediately when simulation starts

**Manual Override:**
- Right-click transition → "Add to Analysis" locks to that transition
- Panel updates for selected transition until another is chosen
- Auto-tracking continues to find most active

## User Experience

### Scenario 1: Start Simulation
```
1. Open Diagnostics tab
2. See: "Auto-tracking: Waiting for transition activity..."
3. Click [R] to run simulation
4. Panel automatically shows first transition that fires
5. Continues showing most active transition
```

### Scenario 2: Multiple Transitions Firing
```
1. T1 fires frequently → Panel shows T1
2. T2 starts firing more → Panel switches to T2
3. T3 fires once → Panel briefly shows T3, then back to T2
4. Real-time view of what's happening NOW
```

### Scenario 3: Manual Selection
```
1. Right-click T5 → "Add to Analysis"
2. Panel locks to T5
3. Shows T5 diagnostics regardless of activity
4. Until you select a different transition
```

## Display Format

### Auto-Tracking Active
```
╔══════════════════════════════════════════════════════════╗
║ Diagnostics: T1                                          ║
║ Type: continuous                                         ║
╚══════════════════════════════════════════════════════════╝

ℹ Auto-tracking: Showing most recently fired transition

━━━ Locality Structure ━━━
P1, P2 → T1 → P3, P4

━━━ Runtime Diagnostics ━━━
  Simulation Time:  35.2s
  Enabled Now:      ✓ True
  Last Fired:       35.0s
  Throughput:       0.750 fires/sec
```

### Selection Label
```
Top of panel shows:
"Active: T1 (auto-tracking)"
```

## Implementation Details

### Key Methods

```python
def _on_update_timer():
    """Called every 500ms"""
    if self.current_transition:
        self._auto_update_active_transition()  # Check for newer activity
        self._update_display()
    else:
        self._auto_select_transition()  # Find any active transition

def _auto_update_active_transition():
    """Switch to most recently fired transition"""
    # Scan all transitions
    # Find one with most recent last_fired time
    # Switch if fired within last 2 seconds

def _auto_select_transition():
    """Select any transition with activity"""
    # Used when no transition selected yet
    # Picks first transition that has fired
```

### Activity Window

**2-second window** for considering a transition "active":
- If transition fired < 2 seconds ago → Active
- If transition fired > 2 seconds ago → Not active
- Prevents flickering between transitions
- Gives stable view of current activity

## Configuration

### Update Frequency
- **500ms** (2 times per second)
- Good balance between responsiveness and performance
- Can be changed in `_start_updates()` method

### Activity Window
- **2 seconds** threshold for "active"
- Prevents too-frequent switching
- Can be changed in `_auto_update_active_transition()` method

## Benefits

### 1. Zero Configuration
✅ Works automatically out of the box
✅ No need to pre-select transitions
✅ Just run simulation and watch

### 2. Real-Time Insight
✅ Always shows what's happening NOW
✅ Follows the "action" automatically
✅ Understand model behavior immediately

### 3. Intelligent Behavior
✅ Doesn't flicker rapidly between transitions
✅ Focuses on sustained activity
✅ Manual override available

### 4. Educational Value
✅ Great for understanding model dynamics
✅ See which transitions are most active
✅ Discover unexpected behavior patterns

## Use Cases

### Debugging
**Problem:** "Why isn't T5 firing?"
**Solution:** Watch diagnostics. If it never appears, it's never firing. Check enablement state when manually selected.

### Performance Analysis
**Problem:** "Which transition is the bottleneck?"
**Solution:** Watch which transition dominates the diagnostics panel. High activity = potential bottleneck.

### Model Validation
**Problem:** "Is the model behaving as expected?"
**Solution:** Watch the sequence of transitions that appear. Verify expected firing patterns.

### Learning
**Problem:** "I don't understand my model's behavior"
**Solution:** Watch diagnostics auto-track through different transitions. See the flow of execution.

## Comparison: Before vs After

### Before (Manual Selection Only)
```
1. User must know which transition to monitor
2. Must right-click to select
3. Static view of one transition
4. Miss activity in other transitions
```

### After (Auto-Tracking)
```
1. Panel automatically finds active transitions
2. Zero configuration needed
3. Dynamic view follows activity
4. Never miss important events
```

## Technical Notes

### Performance
- Scans all transitions every 500ms
- Efficient: Only queries last fired time
- No impact on simulation performance
- Timer stops when panel not visible

### Thread Safety
- All updates in GTK main thread
- Uses GLib.timeout_add for scheduling
- No threading issues

### Error Handling
- Silently fails if model unavailable
- Continues working if individual transition fails
- Robust against missing data

## Future Enhancements

### 1. Activity Histogram
Show bar chart of recent activity for all transitions.

### 2. Configurable Window
Let user adjust the 2-second activity window.

### 3. Freeze Mode
Button to "freeze" on current transition (disable auto-tracking).

### 4. History
Show list of recently tracked transitions.

### 5. Filters
Only auto-track certain types of transitions (e.g., only continuous).

## Summary

The auto-tracking feature makes the diagnostics panel **intelligent and proactive**:

✅ **Automatic** - No configuration needed
✅ **Smart** - Follows the action
✅ **Responsive** - Updates every 500ms
✅ **Stable** - 2-second activity window prevents flicker
✅ **Overrideable** - Manual selection still works

Just open the Diagnostics tab and run your simulation. The panel will automatically show you what's happening!
