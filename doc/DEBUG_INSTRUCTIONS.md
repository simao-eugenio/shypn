# Debug Instructions for Rate Function Property Changes

## How to Test

1. **Run the application:**
   ```bash
   cd /home/simao/projetos/shypn
   python3 src/shypn.py 2>&1 | tee /tmp/shypn_debug.log
   ```

2. **In the application:**
   - Create a transition with a rate function (e.g., `hill_equation(P1, vmax=10, kd=5, n=2)`)
   - Add the transition to the Dynamic Analyses → Transitions plot
   - Start the simulation
   - Let it run for a few seconds
   - **Open the transition properties dialog**
   - Change the rate function to something different (e.g., `michaelis_menten(P1, vmax=15, km=3)`)
   - Click OK

3. **Watch the console output for these debug messages:**

## Expected Debug Output

### When you click OK in properties dialog:
```
[PROPERTY CHANGE] Transition T_Test (ID:1) properties changed - setting needs_update=True
[PROPERTY CHANGE] New rate_function: michaelis_menten(P1, vmax=15, km=3)
```

### On next update loop iteration:
```
[UPDATE] data_changed=False, needs_update=True
[UPDATE] Calling update_plot(force_full_redraw=True)
```

### In update_plot:
```
[UPDATE_PLOT] force_full_redraw=True, selected_objects=1
[UPDATE_PLOT] current_ids=[1], cached_ids=[1]
[UPDATE_PLOT] Triggering _full_redraw() - ids_changed=False, force=True
```

### In transition_rate_panel.update_plot:
```
[TRANSITION_RATE_PANEL] update_plot called with force_full_redraw=True
[TRANSITION_RATE_PANEL] selected_objects: ['T_Test']
```

### In _apply_rate_function_adjustments:
```
[APPLY_ADJUSTMENTS] Called for 1 transitions
[APPLY_ADJUSTMENTS] Checking transition: T_Test (ID:1)
[APPLY_ADJUSTMENTS]   transition_type: continuous
[APPLY_ADJUSTMENTS]   rate_function from properties: michaelis_menten(P1, vmax=15, km=3)
[APPLY_ADJUSTMENTS]   Detected type: michaelis_menten, params: {'vmax': 15.0, 'km': 3.0}
```

## What to Look For

1. **Is the signal being emitted?**
   - Look for `[PROPERTY CHANGE]` messages
   - Check if `needs_update=True` is being set

2. **Is the update loop running?**
   - Look for `[UPDATE]` messages
   - Check if `needs_update=True` is detected

3. **Is update_plot being called with force_full_redraw?**
   - Look for `[UPDATE_PLOT] force_full_redraw=True`

4. **Is the transition_rate_panel receiving the call?**
   - Look for `[TRANSITION_RATE_PANEL] update_plot called`

5. **Is _apply_rate_function_adjustments reading the NEW rate function?**
   - Look for `[APPLY_ADJUSTMENTS] rate_function from properties:`
   - **This should show the NEW function, not the old one!**

## Possible Issues

### If you see the OLD function in [APPLY_ADJUSTMENTS]:
- The properties are cached somewhere
- The transition object is different

### If you DON'T see [PROPERTY CHANGE]:
- Signal is not being emitted by the properties dialog
- Signal handler not connected

### If you DON'T see [UPDATE]:
- Update loop not running
- needs_update flag not being checked

### If you see [UPDATE] but NO [UPDATE_PLOT]:
- Condition `if data_changed or self.needs_update:` is False
- needs_update is not True when checked

## Save the Output

After testing, save the relevant debug output and share it to identify the exact issue.

```bash
# Save just the debug messages:
grep -E '\[PROPERTY|UPDATE|APPLY' /tmp/shypn_debug.log > /tmp/debug_filtered.log
cat /tmp/debug_filtered.log
```
