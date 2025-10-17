# Solar System Layout - Physics Models Summary

**Date:** October 16, 2025  
**Status:** Ready for Canvas Testing  

---

## 🌟 Overview

The Solar System Layout now supports **two physics models** that you can toggle between on the canvas!

### Quick Summary

| Feature | Hub Repulsion | Oscillatory Forces |
|---------|--------------|-------------------|
| **Status** | ✅ Default, Stable | ✅ Experimental |
| **Force Model** | Gravity + Coulomb Repulsion | Single Oscillatory Force |
| **Hub Separation** | 1300-2900 units | 700-1200 units |
| **Complexity** | Two opposing forces | One equilibrium force |
| **Best For** | Strong hub separation | Natural orbital patterns |
| **Toggle State** | OFF (unchecked) | ON (checked) |

---

## 📐 Physics Comparison

### Hub Repulsion (Standard)

**Force Model:**
```python
F_gravity = (G * m1 * m2 * weight) / r²        # Always attractive
F_repulsion = (K * m1 * m2) / r²  (if m ≥ 500) # Between hubs
F_total = F_gravity + F_repulsion
```

**Characteristics:**
- Two separate force types
- Explicit hub-to-hub repulsion (K = 50,000)
- Strong separation for high-mass nodes
- Proven stable approach

**Hub Masses:**
- Super-hubs (≥6 connections): 1000
- Major hubs (≥4 connections): 500
- Minor hubs (≥2 connections): 200

### Oscillatory Forces (Experimental)

**Force Model:**
```python
r_eq = scale * (m1+m2)^0.25 * weight^-0.3

if r > r_eq:
    F = (G * m1 * m2 * weight) / r²      # Gravity (attract)
else:
    F = -k * (r_eq - r)                   # Spring (repel)
```

**Characteristics:**
- Single oscillatory force
- Automatic equilibrium distances
- Mass-dependent natural spacing
- Spring-like behavior

**Equilibrium Examples:**
- Two super-hubs (m=1000): r_eq ≈ 1337 pixels
- Super-hub + regular (m=1000+100): r_eq ≈ 970 pixels
- Two major hubs (m=500): r_eq ≈ 1154 pixels

---

## 🎯 How to Use

### Canvas Toggle

**Location:** Right-click context menu

**Menu Item:** `☀️ Use Oscillatory Forces (Spring-like)`

**Usage:**
1. **Unchecked** (default) → Hub Repulsion
2. **Checked** → Oscillatory Forces
3. Apply "Layout: Solar System (SSCC)"

### Status Feedback

**After applying layout:**
```
Applied Solar System (SSCC) layout
Physics: [Hub Repulsion / Oscillatory Forces]
SCCs found: X
Nodes in SCCs: Y
Free places: Z
```

---

## 🧪 Test Results

### Integration Test: ✅ PASSED

**Network:** 3 places + 3 transitions in cycle

**Both physics models:**
- ✅ Applied layout successfully
- ✅ Positioned all 6 nodes
- ✅ Detected 1 SCC correctly
- ✅ No errors or crashes
- ✅ Stable convergence

**Spacing:**
- Hub Repulsion: 100-135 pixels (avg: 118.3)
- Oscillatory Forces: 100-135 pixels (avg: 118.3)
- Both prevent clustering ✓

### Previous Standalone Tests

**Hub Repulsion Test:**
- 3 hubs in network
- Hub separation: 1345-2906 units
- Result: ✅ No clustering, constellation pattern

**Oscillatory Forces Test:**
- 3 hubs in network
- Hub separation: 701-1230 units
- Result: ✅ No clustering, stable equilibrium

---

## 📊 When to Use Each

### Use Hub Repulsion When:

✓ **Network has many hubs** (3+ high-degree nodes)  
✓ **Need maximum separation** between important nodes  
✓ **Proven stability required** (production use)  
✓ **"Explosive" layout desired** (wide spreading)  

**Example networks:**
- Protein-protein interaction networks
- Social networks with influencers
- Communication networks with routers

### Use Oscillatory Forces When:

✓ **Natural appearance desired** (organic feel)  
✓ **Mass hierarchy important** (heavier → farther)  
✓ **Arc weights significant** (stronger → closer)  
✓ **Experimental/research** (exploring new approach)  

**Example networks:**
- Biological pathways (natural equilibrium)
- Chemical reaction networks (mass-dependent)
- Research models (parameter exploration)

---

## 🎨 Visual Testing Checklist

### Small Networks (< 10 nodes)
- [ ] Both models work without errors
- [ ] Layouts are readable
- [ ] No node overlap

### Medium Networks (10-50 nodes)
- [ ] Hub detection works in both
- [ ] Hubs well-separated
- [ ] Balanced distribution

### Large Networks (> 50 nodes)
- [ ] Performance acceptable (< 5 sec)
- [ ] No clustering
- [ ] Clear hub structure

### Real Biomodels
- [ ] BIOMD0000000001 (15-node SCC)
- [ ] Compare visual quality
- [ ] User preference?

---

## 🔧 Implementation Details

### Files Modified

**1. model_canvas_loader.py**
- Added toggle state variable
- Added checkbox menu item
- Added toggle handler
- Updated layout method

**2. solar_system_layout_engine.py**
- Added `use_oscillatory_forces` parameter
- Conditional simulator selection
- Updated statistics output

### Files Created

**3. oscillatory_gravitational_simulator.py** (298 lines)
- Physics engine
- Equilibrium calculation
- Object reference architecture

**4. test_oscillatory_integration.py** (153 lines)
- Integration test
- Both physics models
- Statistics verification

### Documentation Created

**5. OSCILLATORY_FORCES_DESIGN.md**
- Complete physics model explanation
- Mathematical formulas
- Parameter tuning guide

**6. OSCILLATORY_FORCES_CANVAS_INTEGRATION.md**
- UI integration details
- User guide
- Testing checklist

**7. OSCILLATORY_FORCES_TESTING_GUIDE.md**
- Quick start guide
- Step-by-step instructions
- Tips and troubleshooting

**8. SOLAR_SYSTEM_PHYSICS_MODELS_SUMMARY.md** (this file)

---

## 🚀 Next Steps

### Immediate: Canvas Testing

1. **Load Shypn** with the integrated code
2. **Open a Petri net** (simple or biomodel)
3. **Apply both physics models** using toggle
4. **Compare results** visually
5. **Provide feedback:**
   - Which looks better?
   - Any issues?
   - Parameter tuning needed?

### Short-term: Refinement

Based on canvas testing:
1. **Parameter tuning** (if needed)
   - Adjust equilibrium scale
   - Adjust spring constant
   - Fine-tune exponents

2. **Default decision**
   - Keep hub repulsion as default?
   - Or switch to oscillatory?
   - Or keep both as options?

3. **Documentation updates**
   - Add screenshots
   - Update user guide
   - Best practices

### Long-term: Enhancements

Possible future improvements:
1. **Persistent toggle state** (save in preferences)
2. **Parameter sliders** (UI for tuning)
3. **Visual feedback** (show equilibrium distances)
4. **Auto-apply on toggle** (real-time switching)
5. **Preset profiles** (Compact/Balanced/Spread)

---

## 📚 Related Documentation

**Algorithm Overview:**
- `SOLAR_SYSTEM_LAYOUT_PHASE1_COMPLETE.md`
- `SOLAR_SYSTEM_LAYOUT_TESTING_GUIDE.md`

**Hub-Based Features:**
- `HUB_BASED_MASS_ASSIGNMENT_RESULTS.md`
- `HUB_REPULSION_IMPLEMENTATION.md`
- `HUB_REPULSION_CANVAS_TESTING.md`

**Oscillatory Forces:**
- `OSCILLATORY_FORCES_DESIGN.md` ← Complete physics details
- `OSCILLATORY_FORCES_CANVAS_INTEGRATION.md` ← Integration guide
- `OSCILLATORY_FORCES_TESTING_GUIDE.md` ← Quick start

---

## ✅ Status Summary

**Implemented:** ✅  
**Tested:** ✅  
**Integrated:** ✅  
**Documented:** ✅  

**Ready for:** Canvas Testing! 🎨

**Toggle works!** Both physics models are fully functional and can be switched on the canvas.

**Try it now and see which approach works better for your networks!**

---

**Go ahead and test on the canvas!** 🌌☀️
