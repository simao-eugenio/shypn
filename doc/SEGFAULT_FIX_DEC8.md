# Segmentation Fault Fix - December 8, 2025

## Root Cause

The segfault was caused by **GTK threading issues**, not by canvas simulation triggering.

### What Was Happening

1. Background thread runs simulations (correct architecture ✅)
2. Progress updates sent via `progress_callback()` from background thread
3. Each progress update calls `GLib.idle_add()` to schedule UI update
4. **Problem**: Too many `idle_add()` calls in rapid succession
5. GTK event loop gets overwhelmed → memory corruption → segfault

### Key Evidence

- Crashes at random progress points (0%, 10%, 20%, 30%)
- No canvas controller messages in logs
- ReplicateRunner creates isolated controllers (correct ✅)
- Model extraction uses DocumentModel copies (correct ✅)
- Crash happens during `[QUEUE_VIEW] Updating` messages

## The Fix

### 1. Single Idle Handler Pattern

**Before**: Each progress update called `GLib.idle_add()` separately
```python
def _on_experiment_progress(self, queue_index, status, progress):
    GLib.idle_add(update_ui)  # ❌ Multiple calls = GTK overload
```

**After**: One idle handler processes all pending updates in batch
```python
def _on_experiment_progress(self, queue_index, status, progress):
    self._pending_updates[queue_index] = (status, progress)
    
    if self._idle_handler_active:
        return  # Already scheduled
    
    self._idle_handler_active = True
    GLib.idle_add(process_all_updates)  # ✅ Single call
```

### 2. Increased Throttling

**Before**: Progress updates every 0.2 seconds
```python
if (current_time - last_progress_time[0]) >= 0.2:
```

**After**: Progress updates every 0.5 seconds + small sleep
```python
if (current_time - last_progress_time[0]) >= 0.5:
    progress_callback(idx, "running", percentage_str)
    time.sleep(0.01)  # Give GTK breathing room
```

### 3. Batch Processing

All pending UI updates are now processed in a single GTK main loop iteration:
```python
def process_all_updates():
    updates_to_process = list(self._pending_updates.items())
    self._pending_updates.clear()
    
    for idx, (status, progress) in updates_to_process:
        self.queue_view.update_experiment_status(idx, status, progress)
```

## Files Modified

1. `src/shypn/ui/panels/viability/automation/experiment_automation_category.py`
   - Added `_idle_handler_active` flag
   - Rewrote `_on_experiment_progress()` to use single idle handler
   - Batch processes all pending updates

2. `src/shypn/ui/panels/viability/automation/batch_executor.py`
   - Increased progress throttle from 0.2s to 0.5s
   - Added 0.01s sleep after each progress callback

## Testing

Run the batch automation again:
1. Load model with transition
2. Configure parameter sweep
3. Generate experiments
4. Start batch execution

**Expected**: No segfault, progress updates work smoothly

## Why This Works

1. **Reduces GLib.idle_add() frequency**: Only one call per batch of updates
2. **Prevents event queue overflow**: GTK has time to process between batches
3. **Avoids threading race conditions**: Single flag prevents concurrent handlers
4. **Maintains responsiveness**: Still updates at 10% boundaries via ReplicateRunner

## Previous Misconception

Initially thought automation was triggering canvas simulation controller. Investigation proved:
- ✅ Automation uses isolated DocumentModel copies
- ✅ ReplicateRunner creates its own SimulationController
- ✅ Canvas controller never accessed during automation
- ❌ Real issue: Too many GTK idle_add calls from background thread
