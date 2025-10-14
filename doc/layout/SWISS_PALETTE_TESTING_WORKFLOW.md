# Swiss Palette Testing Workflow

**Quick Reference Guide for Testing Pure Force-Directed Layout**

---

## 🎯 Goal

Test force-directed physics parameters (k, iterations, threshold) using Swiss Palette on imported SBML pathways WITHOUT any preprocessing interference.

---

## 🔬 Two-Step Workflow

### Step 1: Parse → Pure Petri Net

**SBML Tab** → Choose file → **Parse**

**What happens:**
1. SBML file parsed to PathwayData (species, reactions, stoichiometry)
2. PathwayData converted directly to Petri net (places, transitions, arcs)
3. **NO layout processing** (no grid, no force-directed, no projection)
4. Petri net loaded to canvas with default positions (overlapping or linear)

**Status message:**
```
🔬 Pure Petri net loaded - Use Swiss Palette → Force-Directed to apply layout!
```

**Canvas state:**
- Objects exist but have no meaningful layout
- May be overlapping at origin (0,0)
- May be in a line (sequential positions)
- Ready for Swiss Palette transformation

---

### Step 2: Swiss Palette → Force-Directed

**View menu** → **Swiss Palette** → Layout dropdown → **Force-Directed** → **Apply**

**What happens:**
1. Swiss Palette reads current canvas object positions
2. Applies NetworkX spring_layout with **hardcoded parameters**:
   - k = adaptive (based on pathway size)
   - iterations = 100
   - threshold = 1e-6
   - edge weights = stoichiometry
   - scale = adaptive
3. Updates canvas with new force-directed positions
4. **This is the FIRST and ONLY layout applied**

**Result:**
- Pure physics-based layout (no projection interference)
- Connected nodes pulled together by springs
- Disconnected nodes pushed apart by anti-gravity
- Stoichiometry affects spring strength (2A → stronger pull)

---

## 🧪 Testing Protocol

### Test A: BIOMD0000000001 (Small Pathway, 12 nodes)

**Pathway:** Edelstein1996 - EPSP ACh event

1. **Fetch:** SBML tab → BioModels → BIOMD0000000001 → Fetch
2. **Parse:** Parse button → See "🔬 Pure Petri net loaded"
3. **Swiss Palette:** Force-Directed → Apply
4. **Observe:** Layout quality, node spacing, convergence

**Expected:**
- Tight clusters (small pathway)
- Fast convergence (< 1 second)
- Clear reaction flow visible

---

### Test B: BIOMD0000000061 (Medium Pathway, 25 nodes)

**Pathway:** Proctor2008 - p53/Mdm2 core regulation

1. **Fetch:** SBML tab → BioModels → BIOMD0000000061 → Fetch
2. **Parse:** Parse button → See "🔬 Pure Petri net loaded"
3. **Swiss Palette:** Force-Directed → Apply
4. **Observe:** Layout quality, node spacing, convergence

**Expected:**
- Moderate spacing
- Convergence in 1-2 seconds
- Some overlap possible (medium density)

---

### Test C: Parameter Variation (k values)

**Goal:** Test different k values to see spacing effects

| k Value | Spacing | Best For |
|---------|---------|----------|
| 0.5 | Very tight | Dense pathways (30+ nodes) |
| 1.0 | Default | Balanced (10-20 nodes) |
| 2.0 | Spacious | Small pathways (< 10 nodes) |
| 3.0 | Very loose | Presentation/readability |

**How to test:**
1. Import pathway (Fetch → Parse)
2. Open Swiss Palette
3. **Modify k parameter** in Swiss Palette UI (if available)
4. Apply and observe spacing changes
5. Document which k works best for pathway size

---

### Test D: Parameter Variation (iterations)

**Goal:** Test convergence speed vs quality

| Iterations | Speed | Quality | Notes |
|-----------|-------|---------|-------|
| 10 | Very fast | Poor | Not converged, rough layout |
| 50 | Fast | Moderate | NetworkX default |
| 100 | Medium | Good | **Current hardcoded value** |
| 200 | Slow | Excellent | Diminishing returns |
| 500 | Very slow | Excellent | Overkill for most cases |

**How to test:**
1. Import same pathway multiple times
2. Modify iterations in Swiss Palette (if available)
3. Time convergence with stopwatch
4. Compare visual quality
5. Find optimal iteration count per pathway size

---

### Test E: Edge Weight Verification

**Goal:** Verify stoichiometry affects spring strength

**Test case:** Find reaction with high stoichiometry
```
2A + B → C
```

**Expected behavior:**
- A should be pulled **twice as close** to reaction as B
- Edge weight for A→reaction = 2.0
- Edge weight for B→reaction = 1.0
- Spring force proportional to weight

**How to verify:**
1. Import pathway with varied stoichiometry
2. Apply force-directed
3. Measure distances (A to reaction vs B to reaction)
4. Check logs for edge weights

---

## 📊 Data Collection Template

Create a spreadsheet or markdown table:

| Pathway | Nodes | k | Iterations | Time (s) | Quality | Notes |
|---------|-------|---|-----------|----------|---------|-------|
| BIOMD0000000001 | 12 | 1.0 | 100 | 0.8 | Good | Tight clusters |
| BIOMD0000000001 | 12 | 2.0 | 100 | 0.9 | Excellent | Better spacing |
| BIOMD0000000061 | 25 | 1.0 | 100 | 1.5 | Moderate | Some overlap |
| BIOMD0000000061 | 25 | 1.5 | 150 | 2.1 | Good | Much better |

**Quality scale:** Poor / Moderate / Good / Excellent

---

## 🔍 What to Observe

### Visual Inspection

✅ **Node spacing** - Are nodes too close or too far?  
✅ **Overlap** - Are nodes overlapping (bad) or separate (good)?  
✅ **Clusters** - Are related nodes grouped together?  
✅ **Flow direction** - Can you follow reaction pathways visually?  
✅ **Edge crossing** - Minimal crossings = better layout  
✅ **Convergence** - Did layout stabilize or still moving?  

### Quantitative Metrics

- **Convergence time** - How long until stable? (stopwatch)
- **Final energy** - Lower = better layout (check logs)
- **Edge lengths** - Consistent or varied? (measure with ruler)
- **Node distances** - Stoichiometry effect visible? (measure)

---

## 🪵 Log Messages to Check

### Successful Force-Directed Application

```
INFO: 🔬 QUICK LOAD MODE - Pure Petri net conversion (NO layout processing)
INFO: Converted to pure Petri net: 25 places, 20 transitions
WARNING: ✓ Quick load complete - Swiss Palette will apply force-directed
INFO: Applying force-directed layout with k=1.2, iterations=100
INFO: Force-directed converged in 87 iterations (threshold=1e-6)
INFO: Final energy: 0.000234
```

### Edge Weight Information

```
DEBUG: Edge A->R1 weight=2.0 (stoichiometry)
DEBUG: Edge B->R1 weight=1.0 (stoichiometry)
DEBUG: Edge R1->C weight=1.0 (stoichiometry)
```

---

## ⚠️ Troubleshooting

### No objects on canvas after Parse

**Problem:** Parse button clicked but canvas empty  
**Causes:**
1. `ENABLE_QUICK_LOAD_AFTER_PARSE = False` (check line 65 in sbml_import_panel.py)
2. No model_canvas reference (check logs)
3. Converter not available (check logs)

**Solution:**
```python
# src/shypn/helpers/sbml_import_panel.py, line 65
ENABLE_QUICK_LOAD_AFTER_PARSE = True  # ← Must be True
```

---

### Swiss Palette not available

**Problem:** Swiss Palette button disabled  
**Causes:**
1. No objects on canvas (Parse didn't load)
2. Swiss Palette not implemented yet
3. Wrong view/menu

**Solution:**
- Check View menu → Swiss Palette
- Check toolbar for Layout button
- Ensure objects exist on canvas (zoom out)

---

### Force-directed not converging

**Problem:** Layout keeps moving, never stabilizes  
**Causes:**
1. Iterations too low (< 50)
2. Threshold too tight (< 1e-8)
3. Pathway too large (> 50 nodes)

**Solution:**
- Increase iterations (100 → 200)
- Relax threshold (1e-6 → 1e-4)
- Use projection for large pathways

---

### Objects overlapping at origin

**Problem:** All objects stacked at (0,0) after Parse  
**Causes:**
- PathwayConverter assigns default positions (0,0)
- This is EXPECTED behavior (no layout yet)

**Solution:**
- This is correct! Swiss Palette will separate them
- Apply force-directed to expand from origin
- Initial overlap doesn't affect final layout quality

---

## 📈 Expected Results

### Small Pathways (< 15 nodes)

- **k = 1.5-2.0** works best
- **iterations = 50-100** sufficient
- Converges quickly (< 1 second)
- Very clear structure
- Minimal overlap

---

### Medium Pathways (15-30 nodes)

- **k = 1.0-1.5** works best
- **iterations = 100-150** recommended
- Converges moderately (1-3 seconds)
- Good structure with minor overlap
- May benefit from manual adjustment

---

### Large Pathways (30+ nodes)

- **k = 0.5-1.0** works best (tight spacing)
- **iterations = 150-200** needed
- Converges slowly (3-5 seconds)
- Structure visible but complex
- **Consider projection post-processing** for these

---

## ✅ Success Criteria

Testing is successful when you can answer:

1. ✅ What k value works best for small/medium/large pathways?
2. ✅ What iteration count gives good quality without wasting time?
3. ✅ Does stoichiometry affect layout (edge weights working)?
4. ✅ How does convergence time scale with pathway size?
5. ✅ Do we need projection or is pure force-directed sufficient?

---

## 🎯 Next Steps After Testing

1. **Document findings** → Create `FORCE_DIRECTED_PARAMETER_EFFECTS.md`
2. **Define optimal ranges** → k_min, k_max per pathway size
3. **Create presets** → COMPACT, BALANCED, SPACIOUS configurations
4. **Implement config module** → `layout_config.py` with dataclasses
5. **Integrate into Import button** → Apply best parameters by default
6. **Remove quick load flag** → Testing mode no longer needed

---

**Document Version:** 1.0  
**Last Updated:** 2025-01-28  
**Status:** ✅ Ready for empirical testing
