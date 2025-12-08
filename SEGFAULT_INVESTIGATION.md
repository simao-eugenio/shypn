# Segmentation Fault Investigation - December 8, 2025

## Critical Issues Identified

### 1. Segmentation Fault During Experiment Automation
- **When**: Occurs at 1-3% progress during batch experiment execution
- **Symptom**: `Segmentation fault (core dumped)` - application crashes completely
- **Exit Code**: 139 (indicates segfault)

### 2. GTK Widget Management Error
```
(shypn.py:223207): Gtk-CRITICAL **: 23:53:13.414: 
gtk_box_pack: assertion '_gtk_widget_get_parent (child) == NULL' failed
```
- Indicates widgets being packed while still having parents
- Suggests widget lifecycle/reparenting issues

### 3. Rate Function Error (User Error - Secondary)
```
❌ Rate Function Error - Simulation Stopped
   Transition: T1 (T1)
   Expression: sigmoid(P1, vmax=80, km=0.5)
   Error: sigmoid() got an unexpected keyword argument 'vmax'
```
- User is calling `sigmoid()` with wrong parameters
- Should use `michaelis_menten(P1, vmax=80, km=0.5)` instead
- OR `sigmoid(P1, center=40, steepness=0.1, amplitude=80)`

## Attempted Fixes Today

### Fix 1: Reduced Progress Update Frequency (Commit 639ec22)
- Changed from time-based throttling (200ms) to boundary-only updates
- Now only updates at 10%, 20%... 100% (11 updates total vs ~500)
- **Result**: Unknown - needs testing tomorrow

## What Needs Investigation Tomorrow

1. **Memory Corruption Source**
   - Segfault suggests memory corruption in C-level GTK code
   - May be related to threading + GTK interaction
   - Check if GLib.idle_add() is being called too frequently still

2. **Widget Lifecycle Issues**
   - GTK warning about widget parents
   - Check model_canvas_loader.py tab switching code (lines 658-690)
   - Check viability_panel_loader.py widget management

3. **Threading Safety**
   - Batch executor runs in background thread
   - Progress callbacks use GLib.idle_add() to update UI
   - May need additional protection or queuing mechanism

4. **High CPU Usage**
   - 72.8% CPU during simulation is expected
   - But verify it's not spinning/looping incorrectly

## Test Plan for Tomorrow

1. Restart application with fresh state
2. Fix rate expression: Change `sigmoid(P1, vmax=80, km=0.5)` to `michaelis_menten(P1, vmax=80, km=0.5)`
3. Run single experiment (not batch) first
4. Monitor for crashes at 1-3% progress
5. Check debug logs: `tail -f /tmp/shypn_debug.log`
6. If still crashes, consider:
   - Disabling progress callbacks entirely
   - Adding mutex locks around GTK updates
   - Using queue-based update mechanism instead of direct idle_add()

## Critical Files to Review

- `src/shypn/engine/simulation/replicate_runner.py` (lines 120-140)
- `src/shypn/ui/panels/viability/automation/batch_executor.py`
- `src/shypn/ui/panels/viability/automation/experiment_automation_category.py`
- `src/shypn/helpers/model_canvas_loader.py` (lines 658-690)
- `src/shypn/helpers/viability_panel_loader.py`

## Current State

- Application was running with 72.8% CPU (simulation active)
- Unknown if it completed or crashed again
- Commits made:
  - 7c8f016: Fix float concentration preservation
  - 639ec22: Emergency fix for progress updates

## Next Session Priority

**PRIORITY 1**: Determine if segfault is caused by:
- GTK threading issues (GLib.idle_add flood)
- Widget lifecycle problems (parent/child assertions)
- Memory corruption in simulation code
- Rate function errors triggering cleanup issues

**PRIORITY 2**: Implement robust error handling and crash recovery

---
**Note**: Application left in unknown state. Check if process is still running tomorrow before starting.
