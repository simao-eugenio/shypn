# Test 2: Arc Context Menu

**Current Test**: Verify context-sensitive menu on arc right-click

---

## What to Do:

1. **Right-click** on the arc you just created (the one from Place to Transition)

---

## What to Check:

### ✅ Context Menu Should Show:

1. **"Transform Arc ►"** submenu
   - This should have a sub-menu arrow (►)
   - Hover or click to see submenu options

2. **"Edit Weight..."** option
   - Direct menu item for editing arc weight

3. **"Properties"** option
   - Opens arc properties dialog

4. **"Delete"** option
   - Removes the arc

---

## Expected Submenu (Transform Arc ►):

When you open "Transform Arc ►", you should see:

- **"Convert to Inhibitor Arc"** (if Place → Transition)
  - Only shown for valid inhibitor arc connections
  
OR

- **"Convert to Normal Arc"** (if already inhibitor)
  - Only shown if arc is already inhibitor type

---

## How to Report:

Just tell me:

**Option 1** - Everything present:
> ✅ "Context menu works - has Transform Arc submenu, Edit Weight, Properties, Delete"

**Option 2** - Missing items:
> ⚠️ "Context menu missing [list what's missing]"

**Option 3** - Menu doesn't appear:
> ❌ "No context menu on right-click"

---

## Next Tests After This:

- Test 3: Transform arc to inhibitor
- Test 4: Edit weight and see label
- Test 5: Interactive curve toggle
- And more...

---

**Ready?** Right-click the arc and tell me what you see! 🚀
