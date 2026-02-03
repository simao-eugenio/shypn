# Batch Execution Error Fix

## Problem
User reports: Generated 100 experiments, clicked "Run All", all show 100% instantly with "error" status.

## Root Cause Analysis

### 1. Missing Method Parameter
- Stage 3 added `method` selector (Gillespie/ODE/Hybrid) to sweep builder
- Config generation includes `method` field
- **BUT**: `method` is not passed to `batch_executor.run_batch()`
- **AND**: `run_batch()` doesn't accept or use `method` parameter
- **AND**: `ReplicateRunner.run_replicates()` doesn't have `method` parameter

### 2. Instant 100% Progress
The instant 100% with errors means:
- Experiments start (progress set to "running" at 0%)
- Exception is thrown immediately
- Progress callback never called during execution
- Exception handler sets status to "failed" with error message
- But queue shows 100% because that's set when marking as failed

### 3. Error Not Visible
- Errors are captured with `traceback.print_exc()`
- Error messages truncated to 100 chars in progress callback
- User sees "error" status but not the actual error message
- Need to check terminal output or add error display in results browser

## Solution

### Immediate Fix (Show Error Messages)
1. Display error message in results browser status column
2. Add tooltip or expandable error details
3. Check Simulation Log expander for traceback output

### Proper Fix (Add Method Support)
1. Add `method` parameter to `run_batch()` signature
2. Pass `method` to `_run_single_experiment()`
3. Add `method` to `ReplicateRunner.run_replicates()` if needed
4. Or: Store method in ExperimentSnapshot during generation
5. Or: Use method from sweep builder config during execution

## Workaround
Check the terminal/console where shypn.py was launched for the actual error traceback.
The batch executor prints full tracebacks with `traceback.print_exc()`.
