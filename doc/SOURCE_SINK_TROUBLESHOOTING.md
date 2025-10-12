# Source/Sink Troubleshooting Guide

## Problem: "Tokens are not moving in source/sink model"

The source/sink implementation IS working correctly in the engine (all tests pass ✅).  
If tokens aren't moving, the issue is likely in how you're using it.

---

## Quick Checklist

### 1. Did you mark the transition as Source or Sink?

**How to check:**
1. Double-click the transition to open properties dialog
2. Look at the "Basic Properties" tab
3. Check if "Source" or "Sink" checkbox is **CHECKED**

**Expected visual:**
- **Source transition**: Small arrow pointing INTO transition from LEFT (→|)
- **Sink transition**: Small arrow pointing OUT OF transition to RIGHT (|→)
- **Normal transition**: NO arrows

**If you don't see the arrow:**
- The transition is NOT marked as source/sink
- Re-check the checkbox and click OK

---

### 2. Is the transition actually enabled?

**For SOURCE transitions:**
- Should ALWAYS be enabled (doesn't need input tokens)
- If not firing, check:
  - Is the simulation running? (Play button pressed?)
  - Is "Step" mode working? (Try manual step button)

**For SINK transitions:**
- Still needs SUFFICIENT INPUT TOKENS to fire
- Check input places have enough tokens

**For NORMAL transitions:**
- Need sufficient input tokens
- Check arc weights vs. place tokens

---

### 3. Is the transition type set correctly?

Source/sink works with ALL transition types:
- ✅ Immediate (fires instantly)
- ✅ Timed (respects earliest/latest time)
- ✅ Stochastic (random delay)
- ✅ Continuous (integration over time)

**But:**
- **Timed**: Won't fire until earliest time has passed
- **Stochastic**: Won't fire until random delay expires
- **Continuous**: Requires continuous simulation mode

Try **Immediate** first for simplest testing.

---

### 4. Did you save and reload the model?

**Critical:** After setting source/sink checkboxes:
1. Click OK to close dialog
2. Save the file (Ctrl+S or File > Save)
3. If you reload, verify checkboxes are still checked

**Known issue:** If properties aren't persisting, there may be a serialization bug.

---

### 5. Is the simulation actually running?

**Check:**
- Simulation time advancing? (Look at time counter)
- Other transitions firing? (Try a normal transition first)
- Any error messages in console/log?

**Try:**
1. Reset simulation (Reset button)
2. Set initial marking (give places some tokens)
3. Step once manually (Step button)
4. Observe what happens

---

## Diagnostic Test: Create This Simple Model

### Test 1: Source Transition

```
Create:
  Place P1 (5 tokens) → Transition T1 → Place P2 (0 tokens)

Configure T1:
  - Type: Immediate
  - Check "Source" checkbox ✓
  - Click OK

Expected visual:
  - Arrow on LEFT of T1: →|T1|

Run simulation:
  1. Reset
  2. Step once

Expected result:
  - P1: still 5 tokens (NOT consumed)
  - P2: 5 tokens (produced)

If P1 changed: Source is NOT working
If P2 is still 0: Transition didn't fire
```

### Test 2: Sink Transition

```
Create:
  Place P3 (5 tokens) → Transition T2 → Place P4 (0 tokens)

Configure T2:
  - Type: Immediate
  - Check "Sink" checkbox ✓
  - Click OK

Expected visual:
  - Arrow on RIGHT of T2: |T2|→

Run simulation:
  1. Reset
  2. Step once

Expected result:
  - P3: 0 tokens (consumed)
  - P4: still 0 tokens (NOT produced)

If P4 changed: Sink is NOT working
If P3 is still 5: Transition didn't fire
```

---

## Common Issues

### Issue 1: "Transition not firing at all"

**Possible causes:**
1. **Timed transition**: Hasn't reached earliest time yet
   - **Fix**: Use Immediate type for testing
   
2. **Not enabled**: Insufficient input tokens (for sink/normal)
   - **Fix**: Check place tokens ≥ arc weights
   
3. **Simulation paused**: Not in running mode
   - **Fix**: Press Play or Step button

### Issue 2: "Source still consuming tokens"

**This means source is NOT properly set:**
1. Verify checkbox is checked in dialog
2. Verify arrow appears on LEFT of transition
3. Save and reload to confirm persistence
4. Check transition.is_source property in debug

**If checkbox is checked but still consuming:**
- This is a BUG - report it with your .shypn file

### Issue 3: "Sink still producing tokens"

**This means sink is NOT properly set:**
1. Verify checkbox is checked in dialog
2. Verify arrow appears on RIGHT of transition
3. Save and reload to confirm persistence
4. Check transition.is_sink property in debug

**If checkbox is checked but still producing:**
- This is a BUG - report it with your .shypn file

### Issue 4: "Visual arrows not appearing"

**Possible causes:**
1. Zoom level too low (arrows very small)
   - **Fix**: Zoom in
   
2. Rendering issue after zoom
   - **Fix**: Close and reopen file
   
3. Checkboxes not actually checked
   - **Fix**: Re-check and verify

---

## What to Report if Still Broken

If you've verified all the above and it's still not working:

**Please provide:**
1. Screenshot of the model
2. Screenshot of transition properties dialog (showing checkboxes)
3. Your .shypn file (so I can test it)
4. Exact steps you're taking
5. What you expect vs. what actually happens

**Helpful info:**
- Which transition type? (Immediate/Timed/Stochastic/Continuous)
- Are visual arrows appearing?
- Do checkboxes stay checked after save/reload?
- Any console errors or warnings?

---

## Engine Status

**Confirmed working (tests passed ✅):**
- ✅ Immediate source/sink
- ✅ Timed source/sink  
- ✅ Stochastic source/sink
- ✅ Continuous source/sink
- ✅ Property serialization
- ✅ Visual markers
- ✅ Backward compatibility

**The engine implementation is correct.** If it's not working for you, the issue is in:
- UI interaction (checkbox not actually setting property)
- File persistence (properties not being saved)
- Model setup (transition not connected properly)
- Simulation control (not running/stepping)

---

## Next Steps

1. **Try the diagnostic tests above** (simple source and sink)
2. **Take screenshots** of what you're seeing
3. **Check the transition properties** after saving/reloading
4. **Report back** with specific details if still broken

The implementation exists and works - we just need to figure out why your specific case isn't working!
