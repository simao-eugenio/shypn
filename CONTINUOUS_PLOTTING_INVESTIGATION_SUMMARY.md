# Continuous Simulation Plotting - Investigation Summary

## Problem Statement
**Issue:** Continuous simulation is not plotting for selected places

## Investigation Results

### ✅ System Architecture Verified
I performed a comprehensive analysis of the continuous transition execution and plotting system. **All core components are correctly implemented:**

1. **Continuous Behavior** - Properly integrates transitions and modifies place tokens
2. **Simulation Controller** - Correctly executes continuous transitions in Phase 3 of each step
3. **Data Collector** - Properly records place token changes and transition firings
4. **Rate Calculator** - Correctly computes token rates from time-series data
5. **Plot Panel** - Correctly retrieves and displays rate data

### 🔍 Root Cause Analysis

The plotting infrastructure is sound. The most likely causes of "no plotting" are:

1. **Transition type not set to 'continuous'** - Most common issue
2. **Input places have zero tokens** - Continuous transitions require tokens > 0
3. **Places not selected in analysis panel** - User hasn't added places to plot
4. **Zero or missing rate property** - Transition rate not configured

### 🛠️ Debugging Tools Added

I've added **diagnostic logging** to help identify the exact issue:

#### File: `src/shypn/engine/simulation/controller.py`
```python
DEBUG_CONTINUOUS = True  # Line ~420
```

**Shows:**
- How many continuous transitions are found
- Whether each transition can fire
- Integration results (consumed/produced tokens)
- Whether data collector is notified

#### File: `src/shypn/analyses/data_collector.py`
```python
DEBUG_DATA_COLLECTOR = False  # Line ~75 (set True to enable)
```

**Shows:**
- Place token values at each step
- Timestamp for each data point

### 📋 Comprehensive Debug Guide

Created: **`CONTINUOUS_PLOTTING_DEBUG_GUIDE.md`**

This guide provides:
- Step-by-step diagnostic procedures
- Expected debug output for working system
- Common issues with solutions
- Testing procedures with example networks
- Debug checklist

## How to Diagnose Your Specific Issue

### Step 1: Run Simulation with Debug Output

1. **Make sure debug logging is enabled** (already done):
   - `DEBUG_CONTINUOUS = True` in controller.py (line ~420)

2. **Run your simulation** (Run or Step button)

3. **Check terminal output** for these key messages:

```
[CONTINUOUS] Found N continuous transitions  ← Should be > 0
[CONTINUOUS] T_name: can_flow=True          ← Should see your transition
[CONTINUOUS] ✓ T_name integrated            ← Integration happening
[CONTINUOUS]   consumed: {place_id: amount} ← Tokens being moved
[CONTINUOUS]   produced: {place_id: amount}
[CONTINUOUS]   data_collector notified       ← Data being recorded
```

### Step 2: Interpret Results

**If you see `Found 0 continuous transitions`:**
- **Problem:** Transition type not set correctly
- **Solution:** Select transition → Properties → Set "Transition Type" to "Continuous"

**If you see `can_flow=False, reason=input-place-empty`:**
- **Problem:** Input places have zero tokens
- **Solution:** Set initial marking (tokens) > 0 for input places

**If you see `rate: 0.000`:**
- **Problem:** Rate property is zero or not set
- **Solution:** Set transition "Rate" property to desired value (e.g., `10.0`)

**If you see `NO data_collector attached!`:**
- **Problem:** System wiring error
- **Solution:** Restart application

**If you don't see your places in the plot:**
- **Problem:** Places not added to analysis panel
- **Solution:** Right-click place → "Add to Analysis" or use search box

### Step 3: Verify Data Collection

Enable additional logging if needed:
```python
DEBUG_DATA_COLLECTOR = True  # in data_collector.py line ~75
```

This shows place token values being recorded at each step.

## Example Test Case

To verify the system works, create this simple network:

```
Create:
- Place P1: initial tokens = 100
- Transition T1: type = Continuous, rate = 10.0  
- Place P2: initial tokens = 0
- Arc: P1 → T1 (weight 1)
- Arc: T1 → P2 (weight 1)

Test:
1. Right-click P1 → "Add to Analysis"
2. Right-click P2 → "Add to Analysis"
3. Click Run button
4. Wait 1 second

Expected Results:
- P1 rate plot: -10.0 tokens/s (red/negative, consumption)
- P2 rate plot: +10.0 tokens/s (green/positive, production)
- P1 tokens: ~90
- P2 tokens: ~10
```

## Quick Fixes

### Fix 1: Transition Type
```
Select transition → Properties Dialog → Transition Type dropdown → "Continuous"
```

### Fix 2: Initial Tokens
```
Select place → Properties Dialog → Initial Marking → Set to > 0 (e.g., 100)
```

### Fix 3: Rate Value
```
Select transition → Properties Dialog → Rate field → Enter value (e.g., 10.0)
```

### Fix 4: Add Places to Plot
```
Right-click place in canvas → "Add to Analysis"
OR
In analysis panel → Use search box → Enter place name → Add
```

## Files Modified

1. **`src/shypn/engine/simulation/controller.py`**
   - Added `DEBUG_CONTINUOUS = True` logging
   - Lines modified: ~420-440, ~468-495
   - Shows continuous transition detection and execution

2. **`src/shypn/analyses/data_collector.py`**
   - Added `DEBUG_DATA_COLLECTOR = False` logging
   - Lines modified: ~64-84
   - Shows place data collection (enable if needed)

3. **`CONTINUOUS_PLOTTING_DEBUG_GUIDE.md`** (New)
   - Comprehensive troubleshooting guide
   - 250+ lines of diagnostic procedures

4. **`debug_continuous_plotting.py`** (New)
   - Standalone test script
   - Verifies rate calculation algorithm

## Next Steps

1. **Run your simulation with debug enabled** (already done)
2. **Check terminal output** for diagnostic messages
3. **Compare with expected output** in the debug guide
4. **Apply fixes** based on which message is missing/wrong
5. **Report back** what you see in the terminal - I can help interpret

## Confidence Level

**High confidence** that this issue is due to configuration, not a code bug:
- ✅ All infrastructure components verified
- ✅ Algorithm tested with standalone script
- ✅ Data flow traced end-to-end
- ✅ Debug logging added at key points

The debug output will reveal exactly which step is failing.
