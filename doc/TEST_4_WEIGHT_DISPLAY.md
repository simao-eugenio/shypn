# Test 4: Weight Text Display

**Current Test**: Verify weight label appears on arc when weight > 1

---

## ✅ Previous Tests: PASSED!

- ✅ Test 1: Perimeter connection with border accounting
- ✅ Test 2: Context menu working
- ✅ Test 3: Arc transformation with smart validation

---

## Test 4: Edit Arc Weight

### What to Do:

1. **Right-click** on any arc (normal or inhibitor)
2. Select **"Edit Weight..."**
3. A dialog should appear asking for the weight
4. **Change weight from 1 to 2**
5. Click **OK**
6. **Look at the arc** - what changed?

---

## What to Check:

### ✅ Weight = 1 (default):
- No weight label should appear on arc
- Arc looks normal

### ✅ Weight = 2 (after edit):
- Weight label **"2"** should appear
- Label positioned at **arc midpoint**
- Label should be **readable** (good color contrast)

---

## Visual Comparison:

**Weight = 1** (no label):
```
Place ━━━━━━━━━━━━━►■ Transition
```

**Weight = 2** (label appears):
```
Place ━━━━━━2━━━━━━►■ Transition
           ↑
      Label at midpoint
```

---

## How to Report:

**Option 1** - Works perfectly:
> ✅ "Weight label '2' appeared at arc midpoint, readable and well-positioned"

**Option 2** - Label issue:
> ⚠️ "Label appeared but [describe issue: position wrong, hard to read, etc.]"

**Option 3** - No label:
> ❌ "Changed weight to 2 but no label appeared"

**Option 4** - Dialog issue:
> ❌ "Edit Weight dialog didn't appear / had error"

---

## After This Test:

Next tests:
- Test 5: Interactive curve toggle (click handle)
- Test 6: Undo/redo transformation
- Test 7-8: Vertical/diagonal arcs
- Test 9-10: Parallel arcs

---

**Ready?** Edit the arc weight to 2 and let me know what you see! 🚀
