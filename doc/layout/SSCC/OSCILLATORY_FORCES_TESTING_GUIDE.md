# Quick Guide: Testing Oscillatory Forces on Canvas

## 🎯 How to Test

### Step-by-Step Instructions

**1. Load a Model**
   - Open Shypn
   - Load any Petri net (or create a simple one)
   - Example: Load BIOMD0000000001 from data/biomodels_test/

**2. Apply Standard Layout (Hub Repulsion)**
   ```
   → Right-click on canvas background
   → Select: "Layout: Solar System (SSCC)"
   → Wait for layout to complete
   → See message: "Physics: Hub Repulsion"
   ```

**3. Enable Oscillatory Forces**
   ```
   → Right-click on canvas background
   → Check: "☀️ Use Oscillatory Forces (Spring-like)"
   → See message: "Solar System Layout: Oscillatory Forces"
   ```

**4. Apply Layout Again**
   ```
   → Right-click on canvas background
   → Select: "Layout: Solar System (SSCC)"
   → Wait for layout to complete
   → See message: "Physics: Oscillatory Forces"
   ```

**5. Compare Results**
   - Which layout looks better?
   - Are hubs well-separated in both?
   - Any clustering or overlap?
   - Which feels more "natural"?

---

## 🎨 Visual Comparison

### Hub Repulsion (Standard) - Toggle OFF

**Characteristics:**
```
Hubs: ████    ████    ████
      Wide spacing (1300-2900 units)
      Strong repulsion
      "Explosive" pattern
```

**Best for:**
- Many hubs in network
- Need maximum separation
- Proven stable approach

### Oscillatory Forces (Spring-like) - Toggle ON

**Characteristics:**
```
Hubs: ███  ███  ███
      Natural spacing (700-1200 units)
      Equilibrium-based
      "Organic" pattern
```

**Best for:**
- Natural orbital appearance
- Mass-dependent spacing
- Experimental/research

---

## 🧪 Suggested Test Models

### 1. Simple Cycle (Quick Test)
**Create manually:**
```
P1 → T1 → P2 → T2 → P3 → T3 → P1
```
**Expected:** Small circular layout with both physics models

### 2. Hub Network (Core Test)
**Create manually:**
```
Hub Place (center) with 5-8 connections to transitions
```
**Expected:** Hub at center, satellites around it

### 3. Real Biomodel (Full Test)
**Load from file:**
```
data/biomodels_test/BIOMD0000000001.xml
```
**Expected:**
- Large SCC (cycle of 15 nodes)
- 2 hub nodes outside SCC
- Complex connection patterns

---

## 📊 What to Look For

### Hub Separation
- **Good:** Hubs clearly separated, not clustered
- **Bad:** Hubs overlap or cluster together

### Node Distribution
- **Good:** Balanced spacing, no dense clusters
- **Bad:** Some areas dense, others empty

### Arc Clarity
- **Good:** Can follow arcs easily
- **Bad:** Many crossing arcs, unclear connections

### Overall Aesthetics
- **Good:** Clean, organized, easy to understand
- **Bad:** Chaotic, messy, hard to read

---

## 💡 Tips

### Toggle Behavior
- Toggle state affects **next** layout application
- Check status message to confirm physics model
- Can switch back and forth any time

### Testing Strategy
1. **Start simple:** Test on small network first
2. **Increase complexity:** Try medium networks
3. **Real models:** Test on actual biomodels
4. **Compare:** Take screenshots to compare side-by-side

### Reporting Feedback
If you find issues or preferences:
- Note which network (simple/medium/biomodel)
- Which physics model (hub repulsion / oscillatory)
- What looks good or bad
- Screenshots helpful!

---

## 🔧 Troubleshooting

### Toggle Not Working?
- Check if checkbox is actually checked/unchecked
- Look at status message after toggling
- Status message should say "Oscillatory Forces" or "Hub Repulsion"

### Layout Looks Same in Both?
- Normal for very small networks (< 5 nodes)
- Difference more visible with:
  - Multiple hubs (3+)
  - Larger networks (10+ nodes)
  - Complex connection patterns

### Nodes Overlap?
- Try applying layout again (may need more iterations)
- Both physics models should prevent overlap
- Report if persistent overlap occurs

---

## ✅ Success Criteria

**Both physics models should:**
- ✓ Complete without errors
- ✓ Position all nodes
- ✓ Prevent hub clustering
- ✓ Create readable layout
- ✓ Finish in < 5 seconds

**You should see:**
- ✓ Clear difference between the two approaches
- ✓ Hubs well-separated in both
- ✓ Smooth, stable layouts
- ✓ No crashes or errors

---

## 🎉 Ready to Test!

**The toggle is working and ready for your feedback!**

Start with a simple network and work your way up to complex biomodels.

**Have fun exploring the two physics approaches!** ☀️🌌
