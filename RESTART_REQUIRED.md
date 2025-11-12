# ✅ AUTOMATIC STOCHASTIC NOISE NOW ENABLED

## What Changed

When you import pathways (KEGG or SBML) and apply "Heuristic Parameters", the rate functions now **automatically include wiener() noise by default**.

## Before (Old Behavior)
```
michaelis_menten(P17, vmax=70.0, km=0.1)
```

## After (New Behavior - Default)
```
(michaelis_menten(P17, vmax=70.0, km=0.1)) * (1 + 0.1 * wiener(time))
```

## ⚠️ IMPORTANT: You Must Restart Shypn!

The changes won't take effect until you restart the application because:
- Python modules are cached in memory
- Your running instance still has the old code loaded
- New imports will use the updated PathwayConverter

**Steps to see the new behavior:**
1. Close Shypn completely
2. Restart Shypn
3. Import a fresh pathway (e.g., hsa00010)
4. Apply heuristic parameters
5. Check transition properties → you should now see wiener() in the rate functions!

## Testing Checklist

After restarting, verify:

1. **Import KEGG pathway** (e.g., hsa00010)
   - ✅ Should see: "Stochastic noise enabled: ±10% (prevents steady state traps)" in logs

2. **Apply Heuristic Parameters**
   - ✅ Button should work as before

3. **Check Transition Properties**
   - Open any transition that got heuristic rates
   - Look at "Rate Function" field
   - ✅ Should contain: `(michaelis_menten(...)) * (1 + 0.1 * wiener(time))`

4. **Run Simulation**
   - Continuous transitions should fluctuate instead of freezing
   - ✅ No steady state traps!

## Configuration Options

The behavior is controlled in `PathwayConverter.__init__()`:

```python
# Default (noise enabled):
converter = PathwayConverter()  
# → Adds ±10% noise to all heuristic rates

# Custom amplitude:
converter = PathwayConverter(
    add_stochastic_noise=True,
    noise_amplitude=0.15  # ±15% for low concentrations
)

# Disable noise (old behavior):
converter = PathwayConverter(
    add_stochastic_noise=False
)
```

## Why This Matters

**Problem solved**: Models with continuous transitions getting stuck in steady states

**Before**: 
- Continuous cycle reaches equilibrium (P1=0.9, P2=0.1)
- Stays there forever
- Simulation appears "frozen"

**After**:
- Tokens fluctuate around equilibrium
- Biologically realistic molecular noise
- Never freezes in exact steady state

## Files Modified

1. `src/shypn/heuristic/base.py`
   - Added `add_stochastic_noise()` utility function
   - Updated `KineticEstimator` base class

2. `src/shypn/heuristic/factory.py`
   - Updated `EstimatorFactory.create()` with noise parameters

3. `src/shypn/heuristic/michaelis_menten.py`
   - Updated `__init__()` to accept noise parameters

4. `src/shypn/heuristic/mass_action.py`
   - Updated `__init__()` to accept noise parameters

5. `src/shypn/heuristic/stochastic.py`
   - Updated `__init__()` to accept noise parameters

6. `src/shypn/data/pathway/pathway_converter.py`
   - Added noise configuration to `PathwayConverter.__init__()`
   - Pass parameters to `ReactionConverter`
   - Apply noise in `_setup_heuristic_kinetics()`

7. `src/shypn/engine/function_catalog.py`
   - Added `wiener()` and 5 other stochastic functions

## Verification Command

After restarting, you can also test manually:

```bash
cd /home/simao/projetos/shypn
python test_pathway_converter_noise.py
```

Expected output:
```
✓ Stochastic noise IS present (wiener function found)
  This prevents steady state traps!
```

## Troubleshooting

**Q: I restarted but still seeing old rate functions?**

A: The pathway you imported before the changes still has the old rates. You need to:
1. Delete the old model
2. Import a fresh copy after restart
3. Apply heuristic parameters again

**Q: Can I update existing models?**

A: Yes! Use the viability engine's steady state escape suggestions:
- Detects steady state traps
- Suggests adding wiener() noise
- Can apply automatically

**Q: How do I disable this for a specific import?**

A: You'd need to modify the UI code to add a checkbox. Currently it's always enabled by default because it's the recommended behavior for biological systems.

## Next Steps

If you want to make this configurable in the UI:

1. Add checkbox in import dialog: "☑ Add stochastic noise (prevents steady states)"
2. Add slider for amplitude: 5% - 20%
3. Pass values to PathwayConverter constructor

Let me know if you need help implementing that!

---

**Summary**: After restarting Shypn, all newly imported pathways will automatically have stochastic noise in their heuristic rate functions. This prevents steady state traps and makes models more biologically realistic! 🎉
