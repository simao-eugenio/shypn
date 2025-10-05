# Continuous Transition Plotting - Debug Guide

## Issue Report
**Problem:** Continuous simulation is not plotting for selected places

## System Architecture (Verified ✓)

### 1. Data Collection Flow
```
SimulationController.step()
  ├─> Phase 1: Identify continuous transitions
  ├─> Phase 2: Execute discrete transitions  
  ├─> Phase 3: Execute continuous transitions
  │     ├─> behavior.integrate_step(dt, arcs)
  │     │     ├─> Consume tokens from input places
  │     │     ├─> Produce tokens to output places
  │     │     └─> Return details dict
  │     └─> data_collector.on_transition_fired(transition, time, details)
  ├─> time += dt
  └─> _notify_step_listeners()
        └─> data_collector.on_simulation_step(controller, time)
              └─> For each place: place_data[place.id].append((time, tokens))
```

### 2. Plotting Flow
```
PlaceRatePanel
  ├─> update_plot() (called every 100ms)
  │     └─> For each selected place:
  │           └─> _get_rate_data(place_id)
  │                 ├─> data_collector.get_place_data(place_id)
  │                 └─> rate_calculator.calculate_token_rate_series(data)
  └─> axes.plot(times, rates)
```

## Verified Components ✓

1. **ContinuousBehavior** (`src/shypn/engine/continuous_behavior.py`)
   - ✓ Implements `integrate_step()` correctly
   - ✓ Modifies place tokens via `place.set_tokens()`
   - ✓ Returns consumed/produced maps in details dict
   - ✓ Supports rate functions (constant, expression, callable)

2. **SimulationController** (`src/shypn/engine/simulation/controller.py`)
   - ✓ Identifies continuous transitions by `transition_type == 'continuous'`
   - ✓ Calls `behavior.integrate_step()` for each enabled continuous transition
   - ✓ Notifies data collector after integration
   - ✓ Updates place tokens before notifying step listeners

3. **SimulationDataCollector** (`src/shypn/analyses/data_collector.py`)
   - ✓ Records place tokens on each simulation step
   - ✓ Records transition firing events (including continuous)
   - ✓ Properly attached as step listener in `simulate_tools_palette_loader.py`

4. **RateCalculator** (`src/shypn/analyses/rate_calculator.py`)
   - ✓ Calculates token rate correctly: `Δtokens / Δtime`
   - ✓ Verified with debug script - produces expected rates

5. **PlaceRatePanel** (`src/shypn/analyses/place_rate_panel.py`)
   - ✓ Calls `_get_rate_data()` for each selected place
   - ✓ Plots rate data with matplotlib
   - ✓ Updates every 100ms via periodic callback

## Diagnostic Steps

### Step 1: Verify Continuous Transition Detection
**Added debug logging in controller.py:**
```python
DEBUG_CONTINUOUS = True  # Line ~420
```

**Expected output when simulation runs:**
```
[CONTINUOUS] Found N continuous transitions
[CONTINUOUS] T_name: can_flow=True, reason=enabled-continuous
[CONTINUOUS] ✓ T_name integrated at t=0.100
[CONTINUOUS]   consumed: {P1_id: amount}
[CONTINUOUS]   produced: {P2_id: amount}
[CONTINUOUS]   rate: value
[CONTINUOUS]   data_collector notified
```

**If you see:**
- `Found 0 continuous transitions` → **Problem: Transition type not set to 'continuous'**
- `can_flow=False` → **Problem: Input places have zero tokens**
- `NO data_collector attached!` → **Problem: Data collector not wired**

### Step 2: Verify Place Data Collection
**Enable debug logging in data_collector.py:**
```python
DEBUG_DATA_COLLECTOR = True  # Line ~75
```

**Expected output (first 5 steps):**
```
[DataCollector] Step 1: P1 = 99.0 tokens at t=0.100s
[DataCollector] Step 1: P2 = 1.0 tokens at t=0.100s
[DataCollector] Step 2: P1 = 98.0 tokens at t=0.200s
[DataCollector] Step 2: P2 = 2.0 tokens at t=0.200s
```

**If place tokens don't change:**
- Continuous transitions are not integrating
- Check Step 1 output first

### Step 3: Verify Places Are Selected for Plotting

**Check in UI:**
1. Open Place Rate Analysis panel (right panel)
2. Verify places appear in the objects list
3. Look for place names with format: `P_name (P<id>)`

**If places don't appear:**
- Use search functionality to add places
- Or use context menu: Right-click place → "Add to Analysis"

### Step 4: Verify Data Availability

**Add debug in place_rate_panel.py `_get_rate_data()`:**
```python
def _get_rate_data(self, place_id: Any) -> List[Tuple[float, float]]:
    raw_data = self.data_collector.get_place_data(place_id)
    print(f"[DEBUG] Place {place_id}: {len(raw_data)} data points")
    
    if len(raw_data) < 2:
        print(f"[DEBUG] Insufficient data for place {place_id}")
        return []
    ...
```

**Expected output:**
```
[DEBUG] Place 1: 50 data points
[DEBUG] Place 2: 50 data points
```

**If 0 data points:**
- Place is not being tracked by data collector
- Verify place exists in model
- Check if simulation has run (run/step buttons)

## Common Issues & Solutions

### Issue A: Transition Not Recognized as Continuous
**Symptom:** `Found 0 continuous transitions` in debug output

**Solution:**
1. Select the transition in the canvas
2. Open Properties dialog (double-click or right-click → Properties)
3. Verify "Transition Type" is set to "Continuous"
4. Save and try again

### Issue B: Continuous Transition Not Enabled
**Symptom:** `can_flow=False, reason=input-place-empty`

**Solution:**
- Continuous transitions require ALL input places to have **positive** tokens (> 0)
- Check initial marking of input places
- Unlike discrete transitions, continuous needs `tokens > 0`, not `tokens >= weight`

### Issue C: Zero Rate Function
**Symptom:** `rate: 0.000` in debug output, but expected non-zero

**Solution:**
1. Open transition properties
2. Check "Rate" field value
3. For constant rate: Enter number like `10.0`
4. For dynamic rate: Enter expression like `P1 * 2.0`
5. If no rate is set, defaults to `1.0`

### Issue D: Places Not Selected in Analysis Panel
**Symptom:** Empty plot with message "No places selected"

**Solution:**
1. In Place Rate Analysis panel (right side)
2. Use search box to find places by name
3. Or right-click place in canvas → "Add to Analysis"
4. Verify place appears in objects list

### Issue E: Data Collector Not Attached
**Symptom:** `NO data_collector attached!` in debug output

**Solution:**
- This indicates a wiring error in `simulate_tools_palette_loader.py`
- Should be automatically attached at line 129
- Try restarting the application

## Testing Procedure

### Simple Test Case
Create this minimal network to test continuous plotting:

```
P1 (tokens=100) ---> [T1:continuous, rate=10.0] ---> P2 (tokens=0)
```

**Expected behavior:**
1. Select both P1 and P2 for analysis
2. Click Run button
3. After 1 second:
   - P1 should show rate ≈ -10.0 tokens/s (consumption)
   - P2 should show rate ≈ +10.0 tokens/s (production)
   - P1 tokens ≈ 90
   - P2 tokens ≈ 10

### Complex Test Case
Test with multiple continuous transitions:

```
P1 (100) --[T1:rate=5]--> P2 (0) --[T2:rate=3]--> P3 (0)
```

**Expected rates:**
- P1: -5.0 tokens/s
- P2: +5.0 -3.0 = +2.0 tokens/s
- P3: +3.0 tokens/s

## Debug Checklist

- [ ] Continuous transitions have `transition_type = 'continuous'`
- [ ] Continuous transitions have non-zero `rate` property
- [ ] Input places have positive initial marking (tokens > 0)
- [ ] Places are selected in Place Rate Analysis panel
- [ ] Simulation is running (Run or Step button pressed)
- [ ] Debug output shows continuous transitions being detected
- [ ] Debug output shows integration happening
- [ ] Debug output shows data_collector being notified
- [ ] Place data contains multiple time points
- [ ] Plot updates every 100ms during simulation

## Additional Notes

### Rate Function Formats
Continuous transitions support multiple rate formats:

1. **Constant:** `10.0` → Always flows at 10 tokens/s
2. **Linear:** `5 * P1` → Flow proportional to P1 tokens
3. **Saturated:** `min(10, P1)` → Capped at 10 tokens/s
4. **Time-dependent:** `5 * (1 + 0.1*time)` → Rate increases over time

### Performance
- Data collector automatically downsamples after 8000 points
- Plot updates limited to 100ms intervals (10 FPS)
- No performance issues expected for typical simulations

### Known Limitations
- Continuous transitions use simplified RK4 integration
- Very fast rate changes may require smaller time steps
- Plot may show initial transient artifacts (first few points)

## Files Modified for Debugging

1. `src/shypn/engine/simulation/controller.py` - Added DEBUG_CONTINUOUS logging
2. `src/shypn/analyses/data_collector.py` - Added DEBUG_DATA_COLLECTOR logging

**To disable debug output:** Set `DEBUG_CONTINUOUS = False` and `DEBUG_DATA_COLLECTOR = False`
