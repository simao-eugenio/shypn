# Quick Test Guide - Start Here! 🚀

**Current Test**: Test 1 - Basic Perimeter Connection

---

## Test 1: Perimeter-to-Perimeter Connection

### What to do:

1. **Open your Shypn application**

2. **Create a Place** (circle):
   - Click the Place tool in toolbar
   - Click on canvas at position ~(100, 100)
   - You should see a circle

3. **Create a Transition** (rectangle):
   - Click the Transition tool in toolbar
   - Click on canvas at position ~(300, 100) to the right
   - You should see a rectangle

4. **Create an Arc**:
   - Click the Arc tool in toolbar
   - Click on the Place (circle)
   - Click on the Transition (rectangle)
   - You should see an arrow connecting them

---

## What to Look For:

### ✅ CORRECT Behavior:
```
    Place (circle)          Transition (rectangle)
         ●━━━━━━━━━━━━━━━━━━━━━━━━━━►■
         
- Arc starts AT the right edge of circle (not center)
- Arc ends AT the left edge of rectangle (not center)
- NO GAP between arc and objects
- Arrow points to the right
```

### ❌ WRONG Behavior (if you see this, report it):
```
    Place                   Transition
         ●        ━━━━━━━━►    ■
              ^^^          ^^^
              GAPS!        GAPS!
              
- Arc starts INSIDE or OUTSIDE circle (gap visible)
- Arc ends away from rectangle edge (gap visible)
- Arc goes to/from centers instead of edges
```

---

## How to Report:

Just tell me one of these:

**Option 1** - Everything works:
> ✅ "Test 1 PASSED - Arc connects at object edges perfectly, no gaps"

**Option 2** - Small issue:
> ⚠️ "Test 1 - Works but I see [describe issue, e.g., 'small gap at circle edge']"

**Option 3** - Not working:
> ❌ "Test 1 FAILED - Arc [describe problem, e.g., 'connects to object centers, not edges']"

---

## After Test 1:

Once you report Test 1 results, I'll guide you through:
- ✅ Test 2: Right-click context menu
- ✅ Test 3: Transform to inhibitor arc
- ✅ Test 4: Weight label display
- And more...

---

**Ready?** Open the app and try Test 1! 🚀

Report back when you've created the arc and examined how it connects!
