# 🚀 Quick Test Guide - Pathway Enhancements

## What I Just Added

I've added **three enhancement option checkboxes** to the KEGG Import panel:

- ☑️ **Layout Optimization** - Resolve overlapping elements
- ☑️ **Arc Routing** - Create curved arcs for parallel connections
- ☑️ **Metadata Enhancement** - Add compound/reaction names from KEGG

All are **enabled by default** to give you the best quality import.

---

## 🎯 How to Test Right Now

The app should be running now. Here's what to do:

### Step 1: Open KEGG Import Panel

1. Look for the **Pathway** menu at the top
2. Click: **Pathway** → **Import** → **KEGG Pathway**
3. A panel appears on the right side

### Step 2: Look for the New Checkboxes

Scroll down in the import panel options. You should now see:

```
┌─────────────────────────────────────────────┐
│ Options                                     │
├─────────────────────────────────────────────┤
│ ☑ Filter common cofactors (ATP, NAD+, etc.)│
│                                             │
│ Coordinate scale: [2.5]                     │
│                                             │
│ ☐ Include regulatory relations (future)    │
│                                             │
│ ─────────────────────────────────────────   │
│                                             │
│ Post-Processing Enhancements:               │
│                                             │
│ ☑ Layout Optimization - Resolve overlapping│
│   elements                                  │
│                                             │
│ ☑ Arc Routing - Create curved arcs for     │
│   parallel connections                      │
│                                             │
│ ☑ Metadata Enhancement - Add compound/     │
│   reaction names from KEGG                  │
└─────────────────────────────────────────────┘
```

### Step 3: Test with a Simple Pathway

**Pathway ID to test:** `hsa04668`

1. Enter `hsa04668` in the pathway ID field
2. Click **Fetch** (wait 2-5 seconds)
3. Preview appears showing pathway info
4. Click **Import**
5. New tab opens with the pathway

### Step 4: What You Should See

**With all enhancements enabled (default):**

✅ **Layout Optimization working:**
- No overlapping circles (places) or rectangles (transitions)
- Elements clearly separated
- You can click any element individually

✅ **Arc Routing working:**
- Look for elements with multiple connections
- Arcs should curve outward (not straight overlapping lines)
- Smooth Bézier curves visible

✅ **Metadata Enhancement working:**
- Labels show real names: "TNF", "TRADD", "TNFRSF1A" (not "Place 1", "Transition 1")
- Elements may have colors (if GTK theme shows them)

### Step 5: Compare With/Without Enhancements

**Test A: All Enhancements ON** (default)
- Leave all ☑ checked
- Import `hsa04668`
- Note the quality

**Test B: All Enhancements OFF**
- Uncheck all 3 enhancement boxes
- Import `hsa04668` again (or use a different pathway)
- Compare: You should see overlapping elements, straight arcs, generic labels

**Test C: Individual Processors**
- Try each enhancement individually to see its specific effect

---

## 📊 Expected Performance

| Pathway | Elements | Time | Result |
|---------|----------|------|--------|
| hsa04668 (TNF) | ~30 | <0.5s | ✅ Fast |
| hsa00010 (Glycolysis) | ~60 | <1.0s | ✅ Fast |
| hsa04010 (MAPK) | ~250 | <5.0s | ✅ Acceptable |

---

## 🐛 Troubleshooting

### "I don't see the new checkboxes"
- **Solution:** Restart the app. The UI file was updated.
- Kill the process: `pkill -f "python3 src/shypn.py"`
- Relaunch: `python3 src/shypn.py`

### "Import button stays disabled"
- **Cause:** Pathway fetch failed
- **Solution:** Check network, try again, or try different pathway ID

### "Import takes too long"
- **Cause:** First fetch downloads from KEGG (network delay)
- **Expected:** 2-10 seconds for large pathways on first fetch

### "Still see overlapping elements"
- **Check:** Is "Layout Optimization" checkbox checked?
- **Note:** Very dense pathways may still have some overlaps

### "Arcs are still straight"
- **Check:** Is "Arc Routing" checkbox checked?
- **Note:** Only parallel arcs (multiple arcs between same nodes) are curved

### "Labels still say 'Place 1'"
- **Check:** Is "Metadata Enhancement" checkbox checked?
- **Note:** Only elements with KEGG data get enhanced names

---

## 🎯 Quick Visual Tests

### Test Pathway IDs (Small to Large)

```bash
# Small pathway (~30 elements)
hsa04668  # TNF signaling - Good for seeing arc routing

# Medium pathway (~60 elements)  
hsa00010  # Glycolysis - Classic metabolic pathway

# Large pathway (~250 elements)
hsa04010  # MAPK signaling - Stress test
```

### What Makes a Good Visual Test

1. **Layout Test:** Look for no overlaps, good spacing
2. **Arc Test:** Find nodes with multiple connections (parallel arcs)
3. **Metadata Test:** Check if labels show biological names (ATP, Glucose, etc.)

---

## 📝 Next Steps

After testing in GUI:

1. ✅ **Works well?** 
   - Git commit the changes
   - Run automated tests to verify

2. ⚠️ **Issues?**
   - Check `/tmp/shypn_output.log` for errors
   - Let me know what's not working

3. 🚀 **Want more testing?**
   - Run: `python3 test_real_kegg_pathways.py`
   - This fetches real pathways and benchmarks performance

---

## 🎉 Success Criteria

You'll know it's working when:

1. ✅ See 3 new checkboxes in import panel
2. ✅ Import completes without errors
3. ✅ Visual quality is good:
   - No overlapping elements
   - Curved arcs where appropriate
   - Biological names on elements
4. ✅ Performance is acceptable (<5s for large pathways)

---

**Your app is running now!** 🚀

Go to: **Pathway** → **Import** → **KEGG Pathway**

Then try importing: `hsa04668`

Enjoy the enhanced pathway visualization! 🎨
