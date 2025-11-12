# Testing Locality-Scoped Diagnosis - UPDATED

## Changes Made:

### 1. Fixed Selection Handler
- Now supports selecting **both transition rows AND place rows**
- Selecting a place row automatically selects its parent transition
- Debug: Shows "Selected transition row" or "Selected place row → parent transition"

### 2. Added Explicit Clearing
- `scan_with_locality()` now clears `issues_store` before scanning
- Ensures old data doesn't remain visible

### 3. Enhanced Debug Logging
All categories now show detailed flow:
```
[Category] ========== SCAN WITH LOCALITY ==========
[Category] Transition: T6
[Category] Input places: ['P5', 'P7']
[Category] Output places: ['P10']
[Category] → Clearing existing issues...
[Category] → Calling _scan_issues()...
[Category] ← _scan_issues() returned 15 issues
[Category] → Filtering issues to locality...
[Category] Filtered 15 → 3 issues
[Category] → Calling _display_issues(3)...
[Category] _display_issues called with 3 issues
[Category] Clearing issues_store...
[Category] Adding 3 rows to TreeView...
[Category] ✓ Added 3 rows to TreeView
[Category] ✓ _display_issues complete
[Category] ✓ Display complete
```

## Test Steps:

### 1. Load and Simulate
```bash
cd /home/simao/projetos/shypn && python src/shypn.py
```
- Open a model
- Run simulation until complete

### 2. Add Transition to Analysis
- Right-click on a transition (e.g., T6)
- Select "Add to Viability Analysis"
- **Verify**: Hierarchical display appears:
  ```
  🔄 T6: R03270
     ● ← Input: P5 (compound)
     ● → Output: P10 (compound)
  ```

### 3. Test Selection
**Test A: Click transition row (parent)**
- Click on "🔄 T6: R03270"
- Check console: `[DiagnosisCategory] Selected transition row: T6`
- **Verify**: RUN SELECTED button enabled

**Test B: Click place row (child)**
- Click on "● ← Input: P5"
- Check console: `[DiagnosisCategory] Selected place row → parent transition: T6`
- **Verify**: RUN SELECTED button enabled

### 4. Run Scoped Diagnosis
- Click "RUN SELECTED" button
- **Check console output for EACH category**:

```
[DiagnosisCategory] ========== NOTIFYING OTHER CATEGORIES ==========
[DiagnosisCategory] Locality: T6
[DiagnosisCategory] Parent panel: <ViabilityPanel>
[DiagnosisCategory] Categories: 4
[DiagnosisCategory] → Calling scan_with_locality on Structural
```

Then for EACH category (Structural, Biological, Kinetic):
```
[Structural] ========== SCAN WITH LOCALITY ==========
[Structural] Transition: T6
[Structural] Input places: ['P5', 'P7']
[Structural] Output places: ['P10']
[Structural] → Clearing existing issues...      ← IMPORTANT: Must see this!
[Structural] → Calling _scan_issues()...
[Structural] ← _scan_issues() returned 15 issues
[Structural] → Filtering issues to locality...
[Structural] All relevant IDs: {'T6', 'P5', 'P7', 'P10'}
[Structural] Issue 'Transition T12 is DEAD' element_id=T12 relevant=False
[Structural] Issue 'Transition T6 is DEAD' element_id=T6 relevant=True
[Structural] Filtered 15 → 3 issues
[Structural] → Calling _display_issues(3)...
[Structural] _display_issues called with 3 issues
[Structural] Clearing issues_store...            ← IMPORTANT: Must see this!
[Structural] Adding 3 rows to TreeView...
[Structural] ✓ Added 3 rows to TreeView
[Structural] ✓ Display complete
```

### 5. Verify Results

**Expected Behavior**:
- ✅ All categories CLEAR their tables first
- ✅ All categories show ONLY issues related to T6 + P5 + P7 + P10
- ✅ Issues for T12, P8, etc. should NOT appear
- ✅ If no issues for locality, table should be empty (not showing old data)

**UI Check**:
- Open each category (Structural, Biological, Kinetic)
- Count the rows in the tables
- Verify element IDs match {T6, P5, P7, P10}

### 6. Test Multiple Selections

Add another transition:
- Right-click T12 → "Add to Viability Analysis"
- List now shows:
  ```
  🔄 T6: R03270
     ● ← Input: P5
  🔄 T12: R01234
     ● ← Input: P8
  ```
- Click on T12 row
- Click "RUN SELECTED"
- **Verify**: Categories now show issues for T12's locality ONLY

## Debugging Issues

### Issue: Categories not clearing

**Symptom**: Old data remains visible after RUN SELECTED

**Check**:
1. Look for: `[Category] → Clearing existing issues...`
   - If MISSING: `scan_with_locality()` not being called
   
2. Look for: `[Category] Clearing issues_store...`
   - If MISSING: `_display_issues()` not being called

3. Look for: `[DiagnosisCategory] → Calling scan_with_locality on [Category]`
   - If MISSING: Parent panel not set or categories not in loop

**Solution**: Check if parent_panel is set (line 158 in viability_panel.py)

### Issue: No issues shown (but should be some)

**Check filtering logic**:
```
[Category] All relevant IDs: {'T6', 'P5', 'P7', 'P10'}
[Category] Issue 'Some issue' element_id=T6 relevant=True  ← Should see TRUE for relevant issues
[Category] Filtered 15 → 0 issues  ← If 0, filtering too aggressive
```

**Common cause**: Issues have no `element_id` attribute
- Look for: `Issue 'Title' has no element_id`
- Fix: Ensure _scan_issues() sets element_id on all Issue objects

### Issue: Selection not working

**Check selection handler**:
```
[DiagnosisCategory] Selected transition row: T6     ← Good!
```
or
```
[DiagnosisCategory] Selected place row → parent transition: T6  ← Good!
```

**If neither appears**: Selection handler not firing
- Check if ListBox row_selected signal is connected
- Check if rows have `is_transition_row` or `is_place_row` attributes

## Success Criteria

✅ **Test passes if:**
1. Console shows "Clearing existing issues" for each category
2. Console shows "Filtered X → Y issues" with correct Y
3. Categories display ONLY locality-scoped issues
4. Selecting different transitions updates all categories
5. No old data remains visible after running RUN SELECTED
