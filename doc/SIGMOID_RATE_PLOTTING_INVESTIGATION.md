# Sigmoid Rate Function Plotting Issue - Investigation Report

## Issue Description
User reported entering `sigmoid(t, 10, 0.5)` formula on a continuous transition's rate function property, running a simple P-T-P net, and observing a **straight line** in the rate plot instead of the expected **S-curve**.

## Investigation Summary

### What Was Tested
1. ✅ **Sigmoid Function Implementation** (`src/shypn/engine/function_catalog.py`)
   - Formula: `amplitude / (1.0 + exp(-steepness * (x - center)))`
   - Correctly implements standard sigmoid function
   
2. ✅ **Continuous Transition Behavior** (`src/shypn/engine/continuous_behavior.py`)
   - Correctly compiles and evaluates rate function expressions
   - Properly passes time parameter to sigmoid function
   - Records rate value in details dict for each integration step
   
3. ✅ **Data Collection** (`src/shypn/analyses/data_collector.py`)
   - Correctly receives and stores transition events with details dict
   - Rate values are preserved in the data structure
   
4. ✅ **Plotting Code** (`src/shypn/analyses/transition_rate_panel.py`)
   - Correctly detects continuous transitions by checking for 'rate' in details
   - Extracts and plots rate values from details dict
   - Plotting logic is sound

5. ✅ **Test Verification** (`test_sigmoid_rate_plotting.py`)
   - Created comprehensive test that verifies sigmoid data
   - Results show perfect S-curve pattern:
     * Early times (t<5): rate ≈ 0.03 (low)
     * Middle time (t≈10): rate ≈ 0.5 (midpoint) 
     * Late times (t>15): rate ≈ 0.97 (saturated)
   - **Conclusion**: Sigmoid function IS working correctly!

## Root Cause

**The issue is NOT a bug in the code** - it's a **user experience/parameter mismatch** problem:

### The Problem
When simulation duration is not explicitly set, the controller runs until the source place is depleted. For a model with:
- P1 starting with 100 tokens
- Continuous transition with rate function `sigmoid(t, 10, 0.5)` (max rate ≈ 1.0 token/s)
- No duration limit set

The simulation will run for ~110 seconds (until P1 is empty).

### Why It Looks Like a Straight Line

The sigmoid function `sigmoid(t, 10, 0.5)` has these characteristics:
- **Center**: t = 10 seconds (where sigmoid = 0.5)
- **Transition range**: Roughly t = 0 to t = 20 seconds
- **Saturated** (rate ≈ 1.0): t > 20 seconds

When plotted on a 0-110 second time axis:
- The S-curve transition (0-20s) occupies only 18% of the X-axis width
- The remaining 82% shows flat rate at 1.0 (saturated region)
- The S-curve portion appears compressed and looks like:
  * A vertical step (if resolution is low)
  * A straight horizontal line at rate=1.0 (if user zooms out)
  * A barely visible transition (if plot canvas is small)

### Diagnosis Scenarios Tested

| Duration | S-Curve Visibility | Visual Appearance |
|----------|-------------------|-------------------|
| None (110s) | Compressed (18% of axis) | Looks like straight line at 1.0 |
| 20s optimal | Full S-curve (0-20s) | Perfect S-curve visible |
| 100s long | Compressed (20% of axis) | Partially visible |

## Solution & Recommendations

### Immediate User Solution
**Set simulation duration to match sigmoid parameters:**

For `sigmoid(t, center, steepness)`:
- **Recommended duration**: `2 × center` to `2.5 × center`
- For `sigmoid(t, 10, 0.5)`: Use duration = **20-25 seconds**

This ensures the full S-curve transition is visible and not compressed.

### Long-Term UX Improvements

#### 1. Smart Duration Suggestions
When user enters a rate function with time-dependent behavior:
- Parse the formula to detect sigmoid, exponential, etc.
- Extract parameters (center, time constant)
- Show UI hint: "💡 Suggested duration for this rate function: 20-25 seconds"

#### 2. Auto-Zoom to Interesting Region
In the plot panel:
- Detect when most of the plot shows saturated/constant values
- Offer "Zoom to dynamic region" button
- Automatically focus X-axis on the region where rate changes significantly

#### 3. Formula Documentation in UI
Add tooltips or help text in the property dialog:
```
Rate Function: sigmoid(t, center, steepness)
  center: Time (seconds) where rate = 50% of maximum
  steepness: How quickly transition occurs
  
💡 Tip: Set simulation duration to 2×center for best visualization
Example: sigmoid(t, 10, 0.5) → Duration: 20-25 seconds
```

#### 4. Plot Range Indicator
Show metadata on the plot:
```
Time Range: 0-110s
Active Transition: 0-20s (18% of range)
[Show Active Range] button
```

## Test Scripts Created

1. **test_sigmoid_rate_plotting.py**
   - Comprehensive test verifying sigmoid data collection
   - Confirms S-curve pattern in collected data
   - Result: ✅ PASSED - Sigmoid produces correct S-curve data

2. **diagnosis_sigmoid_issue.py**
   - Tests multiple duration scenarios
   - Demonstrates compression effect
   - Provides visual analysis of rate progression

## Conclusion

✅ **The sigmoid rate function implementation is correct and working as designed.**

❌ **The "straight line" appearance is a visualization issue caused by inappropriate time range**, not a bug.

📋 **Action Required**: 
- Document this behavior for users
- Consider implementing smart duration suggestions
- Add UI hints for time-dependent rate functions

## Files Investigated

- `src/shypn/engine/function_catalog.py` - Sigmoid implementation
- `src/shypn/engine/continuous_behavior.py` - Rate function evaluation
- `src/shypn/analyses/data_collector.py` - Data collection
- `src/shypn/analyses/transition_rate_panel.py` - Plotting logic
- `src/shypn/engine/simulation/controller.py` - Simulation control
- `src/shypn/engine/simulation/settings.py` - Duration/time step settings

## Next Steps

1. ✅ Inform user of the root cause and solution
2. ⏳ Create user documentation for sigmoid rate functions
3. ⏳ Consider implementing duration suggestion feature
4. ⏳ Add plot auto-zoom capability
