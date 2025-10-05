# Real-Time Diagnostics Panel - Implementation Complete

## Date: October 5, 2025

## Summary

Successfully implemented **real-time diagnostics panel** in the right panel, solving the problem of not being able to access diagnostics during simulation. The new panel provides live runtime metrics that update automatically every 500ms while simulation is running.

---

## Problem Solved

**Original Issue:**
- During simulation, you cannot open the transition properties dialog
- Runtime diagnostics were only accessible in the static properties dialog
- No way to monitor metrics in real-time during simulation

**Solution:**
- Added a third **"Diagnostics"** tab to the right panel notebook
- Updates automatically every 500ms during simulation
- Shows real-time metrics for selected transitions
- Always accessible, even while simulation is running

---

## Implementation Details

### 1. UI Structure (right_panel.ui)

Added new Diagnostics tab to the notebook:

```xml
<!-- Diagnostics Page -->
<child>
  <object class="GtkBox" id="diagnostics_page">
    <!-- Selection Info Label -->
    <child>
      <object class="GtkLabel" id="diagnostics_selection_label">
        <property name="label">Select a transition to view diagnostics</property>
      </object>
    </child>
    
    <!-- Scrolled Window with Diagnostics Content -->
    <child>
      <object class="GtkScrolledWindow" id="diagnostics_scrolled">
        <child>
          <object class="GtkBox" id="diagnostics_content_container">
            <!-- DiagnosticsPanel attaches here -->
          </object>
        </child>
      </object>
    </child>
  </object>
</child>
<child type="tab">
  <object class="GtkLabel">
    <property name="label">Diagnostics</property>
  </object>
</child>
```

**Notebook Tabs:**
1. **Transitions** - Real-time transition rate plots
2. **Places** - Real-time place token plots  
3. **Diagnostics** - Real-time runtime diagnostics ← **NEW**

### 2. DiagnosticsPanel Class

**File:** `src/shypn/analyses/diagnostics_panel.py`

**Key Features:**
- Automatic updates every 500ms during simulation
- Combines structural and runtime analysis
- Clean, formatted text display
- Monospace font for alignment

**Methods:**
```python
class DiagnosticsPanel:
    def __init__(model, data_collector)
    def setup(container, selection_label, placeholder_label)
    def set_transition(transition)          # Set which transition to monitor
    def set_model(model)                    # Update model reference
    def set_data_collector(data_collector)  # Update data collector
    
    # Internal
    def _update_display()                   # Refresh diagnostics
    def _show_diagnostics()                 # Format and display
    def _start_updates()                    # Start 500ms timer
    def _stop_updates()                     # Stop timer
    def _on_update_timer()                  # Timer callback
```

**Display Format:**
```
╔══════════════════════════════════════════════════════════╗
║ Diagnostics: T1                                          ║
╚══════════════════════════════════════════════════════════╝

━━━ Locality Structure ━━━
P1, P2 → T1 → P3, P4

━━━ Static Analysis ━━━
  Places:           4 (2 in, 2 out)
  Arcs:             4
  Arc Weight:       8.0
  
  Input Tokens:     10
  Output Tokens:    5
  Token Balance:    +5
  
  Can Fire (static): ✓ Yes

━━━ Runtime Diagnostics ━━━
  Simulation Time:  35.2s
  
  Enabled Now:      ✓ True
  Reason:           All preconditions satisfied
  
  Last Fired:       34.8s
  Time Since:       0.4s ago
  Recent Events:    8
  Throughput:       0.750 fires/sec

━━━ Recent Events (last 5) ━━━
  1. t= 30.20s  transition
  2. t= 31.50s  transition
  3. t= 32.80s  transition
  4. t= 33.90s  transition
  5. t= 34.80s  transition
```

### 3. Integration with Right Panel Loader

**File:** `src/shypn/helpers/right_panel_loader.py`

**Changes:**
1. Added `self.diagnostics_panel` attribute
2. Setup diagnostics panel in `_setup_plotting_panels()`
3. Updated `set_model()` to propagate model to diagnostics panel
4. Updated `set_data_collector()` to propagate collector to diagnostics panel
5. Pass diagnostics panel to ContextMenuHandler

**Code:**
```python
# Setup diagnostics panel
diagnostics_container = self.builder.get_object('diagnostics_content_container')
diagnostics_selection_label = self.builder.get_object('diagnostics_selection_label')
diagnostics_placeholder = self.builder.get_object('diagnostics_placeholder')

if diagnostics_container:
    self.diagnostics_panel = DiagnosticsPanel(self.model, self.data_collector)
    self.diagnostics_panel.setup(
        diagnostics_container,
        selection_label=diagnostics_selection_label,
        placeholder_label=diagnostics_placeholder
    )
```

### 4. Integration with Context Menu Handler

**File:** `src/shypn/analyses/context_menu_handler.py`

**Changes:**
1. Added `diagnostics_panel` parameter to `__init__()`
2. When a transition is added to analysis, also update diagnostics panel
3. Diagnostics panel now shows metrics for the most recently selected transition

**Code:**
```python
def _on_add_to_analysis_clicked(self, obj, panel):
    panel.add_object(obj)
    
    # If it's a transition, also update the diagnostics panel
    if isinstance(obj, Transition) and self.diagnostics_panel:
        self.diagnostics_panel.set_transition(obj)
        print(f"[ContextMenuHandler] Updated diagnostics panel with transition {obj.name}")
```

---

## Usage

### 1. During Simulation

**Steps:**
1. Run simulation (click [R] in simulate palette)
2. Right-click a transition and select "Add to Analysis"
3. Click on the **"Diagnostics"** tab in the right panel
4. See real-time metrics updating every 500ms

**What You See:**
- Current simulation time
- Enablement state (can fire now?)
- Last fired time and time since
- Recent events count
- Throughput (fires per second)
- Recent events list (last 5)

### 2. Before Simulation

**Steps:**
1. Select a transition (right-click → Add to Analysis)
2. Go to Diagnostics tab
3. See structural analysis and static metrics

**What You See:**
- Locality structure (P-T-P pattern)
- Token counts and balance
- Static firing capability
- "No firing events recorded" (simulation not run yet)

### 3. After Simulation

**Steps:**
1. Stop simulation
2. Diagnostics tab still shows last known state
3. Metrics frozen at final simulation state

---

## Files Modified

### New Files
1. **src/shypn/analyses/diagnostics_panel.py** - DiagnosticsPanel class (380+ lines)
2. **REAL_TIME_DIAGNOSTICS_PANEL.md** - This documentation

### Modified Files
1. **ui/panels/right_panel.ui** - Added Diagnostics tab
2. **src/shypn/helpers/right_panel_loader.py** - Integrated diagnostics panel
3. **src/shypn/analyses/context_menu_handler.py** - Update diagnostics on transition selection

---

## Benefits

### Real-Time Monitoring
✅ See metrics while simulation is running
✅ Updates every 500ms automatically
✅ No need to pause simulation

### Accessibility
✅ Always visible in right panel
✅ Doesn't block simulation controls
✅ Easy to switch between plots and diagnostics

### Complete Information
✅ Combines structural and runtime analysis
✅ Shows both static and dynamic metrics
✅ Includes recent event history

### Performance
✅ Efficient 500ms updates
✅ Stops updating when no transition selected
✅ Minimal overhead

---

## Data Flow

```
Simulation Running
  ↓
SimulationDataCollector (records events)
  ↓
DiagnosticsPanel (every 500ms)
  ↓
LocalityRuntimeAnalyzer (gets metrics)
  ↓
Format and Display
  ↓
GTK TextView (user sees updates)
```

**Update Cycle:**
1. GLib timer fires every 500ms
2. DiagnosticsPanel calls `_update_display()`
3. `_update_display()` calls `runtime_analyzer.get_transition_diagnostics()`
4. Runtime analyzer queries data collector
5. Format results and update TextView
6. User sees updated metrics immediately

---

## Testing Checklist

### ✅ Implementation Complete
- [x] DiagnosticsPanel class created
- [x] UI tab added to right_panel.ui
- [x] Integration with right_panel_loader
- [x] Integration with context_menu_handler
- [x] All files syntax validated

### 🔄 User Testing Required
- [ ] Open application
- [ ] Toggle right panel visible
- [ ] See 3 tabs: Transitions, Places, **Diagnostics**
- [ ] Click on Diagnostics tab
- [ ] See "Select a transition to view diagnostics"
- [ ] Right-click a transition → Add to Analysis
- [ ] See diagnostics appear
- [ ] Run simulation
- [ ] See metrics update in real-time (every 500ms)
- [ ] Check simulation time incrementing
- [ ] Check throughput calculations
- [ ] Check recent events list
- [ ] Stop simulation
- [ ] See metrics frozen at final state

---

## Architecture

### Panel Hierarchy

```
RightPanelLoader
├─ PlaceRatePanel (plot panel)
├─ TransitionRatePanel (plot panel)
└─ DiagnosticsPanel (NEW - text panel)
    ├─ LocalityDetector (structure)
    ├─ LocalityAnalyzer (static analysis)
    └─ LocalityRuntimeAnalyzer (runtime metrics)
        └─ SimulationDataCollector (data source)
```

### Update Mechanism

```
GLib.timeout_add(500ms)
  ↓
_on_update_timer()
  ↓
_update_display()
  ↓
runtime_analyzer.get_transition_diagnostics()
  ↓
data_collector.get_transition_data()
  ↓
Format and display
```

---

## Comparison: Dialog vs Panel

### Static Properties Dialog
- ❌ Cannot open during simulation
- ✅ Detailed property editing
- ❌ Static snapshot only
- ❌ Must pause to view

### Real-Time Diagnostics Panel (NEW)
- ✅ Always accessible during simulation
- ✅ Updates every 500ms automatically
- ✅ Real-time metrics
- ✅ No need to pause
- ✅ Side-by-side with plots
- ✅ Easy to monitor multiple transitions

---

## Future Enhancements (Optional)

### 1. Multi-Transition View
Show diagnostics for multiple transitions simultaneously in a table format.

### 2. Custom Update Interval
Allow user to adjust update frequency (100ms to 2000ms).

### 3. Export Diagnostics
Save current diagnostics to file (text or CSV).

### 4. Historical View
Show diagnostics evolution over time with mini-graphs.

### 5. Alerts
Highlight transitions that meet certain conditions (e.g., throughput drops).

---

## Conclusion

✅ **Real-time diagnostics panel implementation complete!**

The new Diagnostics tab in the right panel provides:
- **Real-time monitoring** during simulation (500ms updates)
- **Complete information** (locality + runtime metrics)
- **Always accessible** (no need to pause simulation)
- **Easy to use** (right-click → Add to Analysis → Diagnostics tab)

This solves the original problem of not being able to view diagnostics during simulation and provides a much better user experience than the static properties dialog.

---

## Quick Start

1. **Start application**
2. **Toggle right panel visible** (if not already)
3. **Right-click a transition** → "Add to Analysis"
4. **Click "Diagnostics" tab** in right panel
5. **Run simulation** and watch metrics update in real-time!

That's it! The diagnostics panel will now show live updates every 500ms while your simulation runs.
