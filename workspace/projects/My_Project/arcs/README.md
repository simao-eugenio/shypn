# Arc Transformation Test Battery

**Location:** `workspace/projects/My_Project/arcs/`  
**Date:** February 13, 2026  
**Purpose:** Comprehensive testing of arc type transformations, weights, thresholds, and visual properties

## Test Models

### 1. `01_arc_types_basic.shy` - Basic Arc Types
**Tests:** All 4 arc types side-by-side with default weight=1

**Layout:**
- **Row 1:** Normal arcs (black, both consume)
- **Row 2:** Test arcs (blue, catalyst does NOT consume)
- **Row 3:** Inhibitor arcs (black, both consume + threshold)
- **Row 4:** Signal flow arcs (gray, info transfer with consumption)

**Initial Tokens:**
- Substrate: 100.0
- Catalyst/Inhibitor/Signal: 10.0
- Product: 0.0

**Expected Behavior:**
1. **Normal arc reaction:** Both substrate and catalyst decrease by 1, product increases by 1
2. **Test arc reaction:** Only substrate decreases, catalyst stays at 10 (read-only)
3. **Inhibitor arc reaction:** Both decrease (same as normal in SHPN semantics)
4. **Signal flow arc reaction:** Both decrease (information with consumption)

**Visual Verification:**
- Normal arcs: **Black** (0.0, 0.0, 0.0)
- Test arcs: **Blue** (0.0, 0.0, 1.0)
- Inhibitor arcs: **Black** (0.0, 0.0, 0.0)
- Signal flow arcs: **Light Gray** (0.7, 0.7, 0.7)

---

### 2. `02_arc_weights.shy` - Arc Weights
**Tests:** Different weight values (1, 2, 5, 10)

**Layout:** 4 rows, each with increasing weights

**Purpose:**
- Verify arc transformation preserves weight values
- Test behavior with non-unit weights
- Ensure visual rendering scales properly with weight

**Test Procedure:**
1. Run simulation → verify token consumption equals weight
2. Transform catalyst arc to Test → verify weight preserved
3. Run simulation → catalyst should NOT consume (despite weight)
4. Transform to Inhibitor → verify weight preserved
5. Run simulation → both consume by weight amount

---

### 3. `03_transformation_test.shy` - Successive Transformations
**Tests:** Successive arc type transformations on same arc

**Layout:** Simple model with one transformable arc labeled "CATALYST - Transform this arc!"

**Test Sequence:**
1. **Initial:** Normal arc (black)
   - Fire transition → catalyst: 10 → 9 (consumed)
   
2. **Transform to Test:** Blue arc
   - Verify: Color changes to blue immediately
   - Fire transition → catalyst: 9 → 9 (NOT consumed)
   
3. **Transform to Inhibitor:** Black arc
   - Verify: Color changes to black immediately
   - Fire transition → catalyst: 9 → 8 (consumed)
   
4. **Transform back to Test:** Blue arc
   - Verify: Color changes to blue immediately
   - Fire transition → catalyst: 8 → 8 (NOT consumed)
   
5. **Transform to Normal:** Black arc
   - Verify: Color changes to black immediately
   - Fire transition → catalyst: 8 → 7 (consumed)

**Critical Checks:**
- ✅ Color changes immediately after transformation
- ✅ Behavior matches arc type (no mixing)
- ✅ No visual artifacts or color persistence issues
- ✅ Successive transformations work correctly

---

### 4. `04_threshold_expressions.shy` - Threshold Expressions
**Tests:** Inhibitor arcs with different threshold expressions

**Test Cases:**
1. **Fixed threshold = 5:** Inhibitor tokens = 7
   - Arc should be **satisfied** (7 >= 5)
   - Transition can fire
   
2. **Fixed threshold = 10:** Inhibitor tokens = 15
   - Arc should be **satisfied** (15 >= 10)
   - Transition can fire
   
3. **Dynamic threshold = tokens/2:** Inhibitor tokens = 20
   - Threshold evaluates to 20/2 = 10
   - Arc should be **satisfied** (20 >= 10)
   - Transition can fire

**Purpose:**
- Verify threshold expressions persist after transformation
- Test both static and dynamic threshold values
- Ensure threshold evaluation works correctly

**Test Procedure:**
1. Verify all 3 transitions can fire initially
2. Transform inhibitor arc to Normal → Test → back to Inhibitor
3. Verify threshold expression preserved
4. Fire transition, check threshold re-evaluated

---

### 5. `05_visual_properties.shy` - Visual Properties
**Tests:** Visual properties (colors) for all arc types

**Layout:** Star pattern with 4 arcs converging to center transition

**Arc Types Tested:**
1. **Normal arc:** Source from top-left → Black line
2. **Test arc:** Source from bottom-left → Blue line
3. **Inhibitor arc:** Source from top-right → Black line
4. **Signal flow arc:** Source from bottom-right (signal place) → Gray line

**Visual Checklist:**
- [ ] Normal arc rendered as solid black line
- [ ] Test arc rendered as solid blue line
- [ ] Inhibitor arc rendered as solid black line (circle at source)
- [ ] Signal flow arc rendered as solid gray line
- [ ] All labels visible and positioned correctly
- [ ] No overlapping or visual artifacts

**Transformation Test:**
Transform each arc through all types and verify:
1. Color updates immediately
2. Arc head style changes correctly (test arc circle, inhibitor circle)
3. Line thickness remains consistent
4. No rendering glitches or leftover artifacts

---

## Common Issues to Test For

### Issue 1: Color Persistence After Transformation ❌
**Symptom:** Arc keeps old color after transformation  
**Expected:** Color changes immediately to new type's color

**Test:**
1. Create normal arc (black)
2. Transform to test arc
3. **Check:** Arc becomes blue immediately
4. Transform to inhibitor
5. **Check:** Arc becomes black immediately

### Issue 2: Behavior Mixing ❌
**Symptom:** Test arc consumes tokens or normal arc doesn't consume  
**Expected:** Each arc type has distinct consumption behavior

**Test:**
1. Start with test arc → Fire → Catalyst stays same ✅
2. Transform to normal → Fire → Catalyst decreases ✅
3. Transform back to test → Fire → Catalyst stays same ✅
4. No mixing: behavior always matches current type

### Issue 3: Weight Loss After Transformation ❌
**Symptom:** Arc weight resets to 1 after transformation  
**Expected:** Weight value preserved across transformations

**Test:**
1. Create arc with weight=5
2. Transform between types multiple times
3. **Check:** Weight remains 5 after each transformation

### Issue 4: Threshold Expression Loss ❌
**Symptom:** Threshold expression cleared after transformation  
**Expected:** Threshold preserved when transforming to/from inhibitor

**Test:**
1. Create inhibitor arc with threshold="tokens/2"
2. Transform to normal → back to inhibitor
3. **Check:** Threshold still "tokens/2"

### Issue 5: Visual Artifacts ❌
**Symptom:** Multiple overlapping arcs, color flicker, rendering glitches  
**Expected:** Clean rendering, single arc, stable colors

**Test:**
1. Transform arc multiple times rapidly
2. **Check:** No duplicate arcs rendered
3. **Check:** Color stays stable (no flicker)
4. **Check:** Arc position/curve unchanged

---

## Testing Workflow

### Quick Test (5 minutes)
1. Open `03_transformation_test.shy`
2. Run 1 step → Check catalyst decreases (normal arc)
3. Transform catalyst arc to Test (context menu or dialog)
4. Run 1 step → Check catalyst stays same
5. Transform to Inhibitor
6. Run 1 step → Check catalyst decreases
7. **Pass:** All behaviors correct ✅

### Full Test (20 minutes)
1. Open each test model in sequence
2. Follow test procedure for each model
3. Document any issues found
4. Verify fixes by re-running tests

### Regression Test (after fixes)
1. **Re-run all 5 tests** to ensure fix didn't break anything
2. Pay special attention to edge cases:
   - Rapid successive transformations
   - Transform during simulation
   - Transform with high weights
   - Transform with complex threshold expressions

---

## Expected Results Summary

| Test Model | Visual Check | Behavior Check | Special Notes |
|------------|--------------|----------------|---------------|
| 01_arc_types_basic.shy | 4 different arc colors | 4 different consumption patterns | Baseline reference |
| 02_arc_weights.shy | Weights visible on arcs | Consumption × weight | Test all weights |
| 03_transformation_test.shy | Color changes immediately | Behavior matches type | **Primary test** |
| 04_threshold_expressions.shy | Inhibitor circles visible | Threshold evaluation works | Expression persistence |
| 05_visual_properties.shy | All 4 colors distinct | All 4 behaviors distinct | Visual regression test |

---

## Bug Reporting Template

If issues found during testing, report using this template:

```
**Model:** [Which test model]
**Arc:** [Arc ID or name]
**Transformation:** [e.g., Normal → Test]
**Issue:** [What went wrong]
**Expected:** [What should happen]
**Actual:** [What actually happened]
**Reproducible:** [Yes/No - steps to reproduce]
**Screenshots:** [If visual issue]
```

---

## Notes

- All models use **immediate transitions** for deterministic testing
- Initial token values chosen to allow multiple firings
- Arc labels help identify which arc to transform
- Signal places required for signal flow arc tests (blue hexagon shape)

---

## Maintenance

**Update frequency:** After any changes to:
- Arc transformation logic (`arc_transform.py`)
- Arc rendering (`arc_builder.py`, `arc.py`)
- Color schema (`color_schema_manager.py`)
- Simulation controller behavior cache
- Property dialog transformation handling

**Version:** 1.0 (2026-02-13)
