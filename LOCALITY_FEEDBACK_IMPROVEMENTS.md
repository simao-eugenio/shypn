# Locality Feedback Improvements

## Issue Resolved

**Problem:** When searching for a transition, there was no clear feedback about the locality being added, especially when simulation wasn't running.

**Solution:** Added comprehensive feedback in multiple places:
1. Search result message shows locality place count
2. Objects list shows locality information for each transition
3. Plot shows detailed waiting state with locality structure

## Changes Made

### 1. Enhanced Objects List Display

**File:** `src/shypn/analyses/transition_rate_panel.py`  
**Method:** `_update_objects_list()` (new override)

**Before:**
```
T1 [CON] (T1)
```

**After:**
```
T1 [CON] + locality (2→3)
         ↑           ↑ ↑
      type info   inputs outputs
```

Shows immediately that the transition has locality attached with input/output counts.

### 2. Added Waiting State Display

**Method:** `_show_waiting_state()` (new method)

**What It Shows:**
```
Objects ready for analysis:

• T1 [CON]
  with locality: 2 inputs → 3 outputs

▶ Start simulation to see plots
```

This appears in the plot area when:
- Transitions are selected
- Localities are detected
- Simulation hasn't started yet

### 3. Improved Plot Update Logic

**Method:** `update_plot()` (enhanced)

Now checks if data exists before plotting:
- No objects → Empty state message
- Objects but no data → Waiting state with locality info
- Objects with data → Full plots with localities

## User Experience Flow

### Complete Search-to-Plot Flow

```
Step 1: User searches "T1"
   ↓
Step 2: Search result shows:
   "✓ Added T1 with locality (5 places)"
   ↓
Step 3: Objects list updates:
   [Red] T1 [CON] + locality (2→3)  [✕]
   ↓
Step 4a: If simulation NOT running:
   Plot area shows:
   -----------------------------------
   Objects ready for analysis:
   
   • T1 [CON]
     with locality: 2 inputs → 3 outputs
   
   ▶ Start simulation to see plots
   -----------------------------------
   ↓
Step 4b: User starts simulation
   ↓
Step 5: Plot shows:
   T1 [CON] ──────────── (solid line)
   ↓ P1 (input) - - - - (dashed, lighter)
   ↓ P2 (input) - - - - (dashed, lighter)
   ↑ P3 (output) · · · · (dotted, darker)
   ↑ P4 (output) · · · · (dotted, darker)
   ↑ P5 (output) · · · · (dotted, darker)
```

## Visual Feedback at Each Stage

### 1. Search Result Label
```
✓ Added T1 with locality (5 places)
```
- Immediate confirmation
- Shows total place count
- Appears at bottom of search box

### 2. Objects List
```
┌─────────────────────────────────────┐
│ Selected Objects                     │
├─────────────────────────────────────┤
│ [■] T1 [CON] + locality (2→3)  [✕] │
│ [■] T2 [STO]                    [✕] │
└─────────────────────────────────────┘
```
- Color box shows plot color
- Type abbreviation [CON], [STO], etc.
- Locality info: (inputs→outputs)
- Remove button [✕]

### 3. Plot Area (No Data)
```
┌─────────────────────────────────────┐
│  Objects ready for analysis:        │
│                                      │
│  • T1 [CON]                         │
│    with locality: 2 inputs → 3      │
│    outputs                           │
│                                      │
│  ▶ Start simulation to see plots   │
└─────────────────────────────────────┘
```
- Lists all selected transitions
- Shows locality structure
- Clear call-to-action

### 4. Plot Area (With Data)
```
┌─────────────────────────────────────┐
│  Rate (tokens/s)                    │
│   │                                  │
│   │  T1 [CON] ───────────           │
│   │  ↓ P1 (in) - - - -              │
│   │  ↓ P2 (in) - - - -              │
│   │  ↑ P3 (out) · · · ·             │
│   │  ↑ P4 (out) · · · ·             │
│   │  ↑ P5 (out) · · · ·             │
│   └──────────────────────> Time (s) │
└─────────────────────────────────────┘
```
- Full locality visualization
- Color-coded by transition
- Legend shows all objects

## Benefits

### Clear Feedback
✅ User knows immediately if locality was detected  
✅ Can see locality structure before running simulation  
✅ No confusion about what will be plotted  

### Information Hierarchy
1. **Search result** - Quick confirmation
2. **Objects list** - Persistent status
3. **Plot area** - Detailed structure

### Better UX
- No silent failures
- Always know what's happening
- Clear next steps ("Start simulation")

## Technical Implementation

### Override Pattern
```python
class TransitionRatePanel(AnalysisPlotPanel):
    def _update_objects_list(self):
        """Override parent to add locality info"""
        # Custom implementation showing locality counts
        
    def _show_waiting_state(self):
        """New method for pre-simulation state"""
        # Shows selected objects with locality details
```

### Data Check
```python
# Check if simulation has started
has_any_data = False
for obj in self.selected_objects:
    if self._get_rate_data(obj.id):
        has_any_data = True
        break

if not has_any_data:
    self._show_waiting_state()  # Show locality info
    return
```

## Testing Scenarios

### Scenario A: Search with Locality
```
Action: Search "T1", model has P1,P2→T1→P3
Expected:
- Search: "✓ Added T1 with locality (3 places)"
- List: "T1 [CON] + locality (2→1)"
- Plot: Shows locality structure, "Start simulation"
```

### Scenario B: Search without Locality
```
Action: Search "T1", isolated transition
Expected:
- Search: "✓ Added T1 to analysis"
- List: "T1 [CON] (T1)"
- Plot: Shows "T1 [CON]", no locality info
```

### Scenario C: Multiple Transitions
```
Action: Add T1 with locality, T2 without
Expected:
- List shows both with appropriate info
- Plot waiting state lists both transitions
- T1 shows locality, T2 doesn't
```

### Scenario D: Start Simulation
```
Action: Have T1 with locality, start simulation
Expected:
- Plot transitions from waiting state to full visualization
- Shows T1 + P1, P2, P3 with appropriate line styles
```

## Files Modified

1. **src/shypn/analyses/transition_rate_panel.py**
   - Added `_update_objects_list()` override
   - Added `_show_waiting_state()` method
   - Enhanced `update_plot()` data checking

## Backwards Compatibility

✅ No breaking changes  
✅ Parent class methods still work  
✅ Overrides are clean extensions  
✅ Existing functionality preserved  

## Status

✅ **Implemented**  
✅ **Syntax validated**  
✅ **Ready for testing**  

---

**Result:** Users now have complete visibility into locality detection and structure at every stage of the workflow! 🎯
