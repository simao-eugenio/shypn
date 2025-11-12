# Testing the Refactored Viability Panel

**Date:** November 12, 2025  
**Status:** Ready for Testing

## Quick Test Checklist

### ✅ Prerequisites
- [x] Application starts without errors
- [x] Viability Panel visible in sidebar
- [x] Panel shows empty state message

### 🧪 Test 1: Basic Investigation (CRITICAL)

**Steps:**
1. Open a model with at least one transition
2. Right-click on any transition
3. Select **"Add to Viability Analysis"** from context menu
4. Observe the Viability Panel

**Expected Results:**
- ✅ Empty state message disappears
- ✅ Panel shows investigation results
- ✅ At least one suggestion appears (or message saying "No issues found")

**Actual Results:**
- [ ] Pass / [ ] Fail
- **Notes:** _______________________________________________

### 🧪 Test 2: Error Handling

**Steps:**
1. Follow Test 1 steps
2. Check terminal/console for errors

**Expected Results:**
- ✅ No Python exceptions or tracebacks
- ⚠️ May see warnings like "Locality analysis failed" (acceptable during initial testing)

**Actual Results:**
- [ ] Pass / [ ] Fail
- **Notes:** _______________________________________________

### 🧪 Test 3: Empty State Returns

**Steps:**
1. Complete Test 1 to show an investigation
2. Close the panel or clear it
3. Reopen panel

**Expected Results:**
- ✅ Empty state message returns
- ✅ No leftover investigation data visible

**Actual Results:**
- [ ] Pass / [ ] Fail
- **Notes:** _______________________________________________

## Known Limitations (Temporary)

### ⚠️ Analyzers Not Fully Integrated
The old analyzers expect different data structures than the new architecture provides. You may see:
- Empty suggestion lists
- Error messages like "Locality analysis failed"
- No suggestions even when issues exist

**This is expected** during the transition period. The fix system is ready, but the analyzers need to be updated to work with the new `Locality` and `Subnet` dataclasses.

### ⚠️ UI Views Not Fully Functional
The new UI views (`SubnetView`, `InvestigationView`) may:
- Not render correctly
- Show empty content
- Have missing Apply/Preview/Undo buttons

**This is also expected** as they depend on the analyzers providing properly structured suggestions.

## What SHOULD Work Now

✅ **Application Startup** - No import errors  
✅ **Panel Visibility** - Viability Panel appears in sidebar  
✅ **Context Menu** - "Add to Viability Analysis" option visible  
✅ **Basic Investigation Flow** - Panel receives transition and attempts analysis  
✅ **Error Resilience** - Failures are caught and don't crash the app  

## What Needs Work

❌ **Analyzer Integration** - Update analyzers to use new dataclasses  
❌ **Suggestion Generation** - Ensure suggestions are properly formatted  
❌ **UI Rendering** - Complete SubnetView and InvestigationView implementation  
❌ **Fix Application** - Wire Apply/Preview/Undo buttons to fix system  

## Debugging Tips

### Check Console Output
The new panel prints debug information:
```
Locality analysis failed: <error>
Dependency analysis failed: <error>
Boundary analysis failed: <error>
Conservation analysis failed: <error>
```

This helps identify which analyzers need updating.

### Verify Data Flow
Add print statements to track the flow:
```python
# In investigate_transition()
print(f"[VIABILITY] Investigating {transition_id}")
print(f"[VIABILITY] Locality: {locality}")
print(f"[VIABILITY] Suggestions: {len(all_suggestions)}")
```

### Check Investigation Object
After investigation runs:
```python
print(f"Investigation: {self.current_investigation}")
print(f"Subnet: {self.current_investigation.subnet}")
print(f"Suggestions: {self.current_investigation.suggestions}")
```

## Next Steps

### Phase 8: Analyzer Compatibility (Immediate Priority)

Update the 4 analyzers to work with new dataclasses:

1. **LocalityAnalyzer** - Accept `Locality` dataclass instead of old locality object
2. **DependencyAnalyzer** - Accept `Subnet` dataclass with `localities` attribute
3. **BoundaryAnalyzer** - Same as above
4. **ConservationAnalyzer** - Same as above

Each analyzer should return `List[Suggestion]` where `Suggestion` has:
```python
Suggestion(
    category='structural',  # or 'kinetic', 'biological', etc.
    action="Do something specific",
    impact="This will help because...",
    target_element_id='T1',
    details={'key': 'value'}
)
```

### Phase 9: UI View Implementation

Complete the UI views:
1. Ensure they can render with empty suggestions (graceful degradation)
2. Add proper callbacks for Apply/Preview/Undo
3. Test with mock data first, then real suggestions

### Phase 10: End-to-End Testing

Once analyzers and UI are working:
1. Test full workflow: Right-click → Suggestions appear → Apply works
2. Verify undo functionality
3. Test with various model types
4. Performance testing with large models

## Success Criteria

The refactor will be considered **complete** when:

✅ User can right-click transition → "Add to Viability Analysis"  
✅ Panel shows relevant suggestions (not empty)  
✅ Suggestions have working Apply/Preview/Undo buttons  
✅ Applied fixes actually modify the model  
✅ Undo successfully reverts changes  
✅ No errors or crashes during normal workflow  

---

**Current Status:** Phase 7 Complete (Integration), Phase 8 Needed (Analyzer Compatibility)  
**Estimated Work Remaining:** 2-3 phases (Analyzers, UI, Testing)
