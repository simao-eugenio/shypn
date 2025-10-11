# Arc Weight Display - Design Issue

**Date**: 2025-10-10  
**Status**: ⚠️ **TO BE RESOLVED**  
**Priority**: MEDIUM

---

## Problem Statement

Arc weight can be multiple types, but current implementation only handles simple numeric display:

### Current Implementation:
```python
# In arc.py render() method:
if self.weight > 1:
    cr.show_text(str(self.weight))
```

**This only works for**: Simple integers (2, 3, 4, etc.)

---

## Weight Types to Support

According to user requirements, arc weight can be:

### 1. **Numeric** (Current - Works)
- Simple integer: `2`, `3`, `5`
- Simple float: `2.5`, `3.14`
- **Display**: Just show the number

### 2. **Expression** (Not Implemented)
- Mathematical expression: `2*x`, `tokens/2`, `min(3, tokens)`
- **Question**: How to display on arc?
- **Options**:
  - Show full expression? (might be too long)
  - Show "f(x)" symbol?
  - Show evaluated result if possible?

### 3. **Threshold Function** (Not Implemented)
- Threshold formula: `threshold(place, operator, value)`
- Examples: `threshold(P1, '>=', 5)`, `threshold(P2, '<', 10)`
- **Question**: How to display?
- **Options**:
  - Show abbreviated notation: `P1≥5`?
  - Show "T" symbol with tooltip?
  - Show full formula (might be too long)?

---

## Current Behavior Issues

### Issue 1: Only shows if weight > 1
```python
if self.weight > 1:  # Only numeric comparison!
```
**Problem**: Expressions and functions are not numbers, so `> 1` comparison fails!

### Issue 2: Simple str() conversion
```python
cr.show_text(str(self.weight))
```
**Problem**: 
- For expression: Might show Python object representation
- For function: Might show `<function at 0x...>`
- Need smart formatting!

---

## Possible Solutions

### Solution 1: Type-Based Display

```python
def _get_weight_display_text(self):
    """Get display text for arc weight."""
    if isinstance(self.weight, (int, float)):
        # Simple numeric
        if self.weight > 1:
            return str(self.weight)
        return None  # Don't show weight=1
    
    elif isinstance(self.weight, str):
        # Expression as string
        if len(self.weight) < 10:
            return self.weight
        else:
            return self.weight[:8] + "..."  # Truncate long expressions
    
    elif callable(self.weight):
        # Threshold function
        return "f()"  # Or extract info from function
    
    else:
        return "?"  # Unknown type
```

### Solution 2: Always Show Label with Icon

Add visual indicator for type:
- `2` - Simple number
- `expr` - Expression (with fx icon)
- `T` - Threshold function (with special marker)

### Solution 3: Tooltip on Hover

- Show abbreviated version on arc
- Full formula/expression on hover/tooltip
- Requires hover detection on arcs

---

## Questions to Answer

### Q1: Display Format
**For expressions**: Show full text or abbreviate?
- Example: `2*tokens` vs `fx`
- Consider: Arc length, readability, zoom level

### Q2: Threshold Display
**For threshold functions**: What notation to use?
- Option A: Mathematical: `P1≥5`
- Option B: Symbolic: `T(P1)`
- Option C: Full text: `threshold(P1,>=,5)` (too long!)

### Q3: Weight = 1 with Expression
**If weight is expression that evaluates to 1**, should label appear?
- Current code: Only shows if weight > 1 (numeric comparison)
- Problem: Can't compare expression to 1
- Solution: Show all non-numeric weights regardless?

### Q4: Dynamic Evaluation
**Should we evaluate expressions at render time?**
- Example: `tokens/2` where tokens=6 → show "3"?
- Or show "tokens/2" (the expression itself)?
- Performance consideration if evaluating every frame

---

## Recommended Approach (Draft)

### Phase 1: Type Detection
```python
# Add weight_type property
@property
def weight_type(self):
    if isinstance(self.weight, (int, float)):
        return 'numeric'
    elif isinstance(self.weight, str):
        return 'expression'
    elif callable(self.weight):
        return 'threshold'
    else:
        return 'unknown'
```

### Phase 2: Smart Display
```python
def _render_weight_label(self, cr, mid_x, mid_y, zoom):
    """Render weight label with type-aware formatting."""
    display_text = None
    
    if self.weight_type == 'numeric':
        if self.weight > 1:
            display_text = str(self.weight)
    
    elif self.weight_type == 'expression':
        # Always show expressions
        display_text = self._format_expression(self.weight)
    
    elif self.weight_type == 'threshold':
        # Show abbreviated threshold notation
        display_text = self._format_threshold(self.weight)
    
    if display_text:
        # Render with appropriate styling
        cr.show_text(display_text)
```

### Phase 3: Helper Formatters
```python
def _format_expression(self, expr):
    """Format expression for display."""
    if len(expr) <= 12:
        return expr
    return expr[:10] + "..."

def _format_threshold(self, threshold_func):
    """Format threshold function for display."""
    # Extract parameters from function
    # Return abbreviated notation like "P1≥5"
    return "T"  # Placeholder
```

---

## Decision Needed

**User/Designer must decide**:

1. **Expression display**: Full text, abbreviated, or symbolic?
2. **Threshold display**: Notation format?
3. **Show all non-numeric weights**: Regardless of value?
4. **Maximum label length**: Truncate after how many characters?
5. **Tooltip support**: Implement hover for full formula?

---

## Current Status

- ✅ **Numeric weights**: Work correctly (show when > 1)
- ❌ **Expression weights**: Not properly displayed
- ❌ **Threshold weights**: Not properly displayed
- ⚠️ **Type detection**: Not implemented

---

## Priority

**MEDIUM** - Current system works for basic numeric weights (which covers most common cases), but needs enhancement for advanced features.

---

## Related Requirements

- **Requirement #7**: "All arcs with weight > 1 expose weight text over the arc"
- Note: This requirement assumes numeric weight only
- Need to extend requirement to cover expressions and thresholds

---

## Next Steps

1. Discuss with user/designer: What display format is preferred?
2. Implement type detection
3. Implement smart formatting
4. Add tooltip support (optional)
5. Update tests to cover all weight types

---

## Files to Modify

- `src/shypn/netobjs/arc.py` - Add weight type detection and smart formatting
- `src/shypn/netobjs/arc.py` - Update `render()` method to use new formatter
- Tests - Add test cases for expression and threshold weights

---

**Status**: Documented, awaiting design decision
