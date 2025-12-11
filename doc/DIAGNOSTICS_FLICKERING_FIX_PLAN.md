# Diagnostics Panel Flickering Fix - Implementation Plan

## Problem Analysis

The diagnostics panel in Dynamic Analysis category currently updates every 500ms by:
1. Regenerating entire text content
2. Calling `buffer.set_text()` which replaces all text
3. This causes visual flickering as GTK redraws the entire TextView

**Current Implementation:**
- Update interval: 500ms (2 times per second)
- Method: `_update_display()` → `_show_diagnostics()` → `_update_text_preserve_scroll()`
- Issue: Full text replacement causes flickering

## Root Causes of Flickering

1. **Complete Buffer Replacement**: `buffer.set_text(text)` replaces all content, even unchanged parts
2. **Layout Recalculation**: GTK must recalculate entire TextView layout on every update
3. **Scroll Adjustment**: Manual scroll position restoration can cause visual jumps
4. **High Frequency Updates**: 500ms is fast enough to notice flickering

## Solution Strategy

### Approach 1: Differential Text Updates (RECOMMENDED)
Update only the parts of the text that actually changed.

**Implementation:**
1. Split diagnostics into sections (header, structure, static analysis, runtime)
2. Track previous values for each section
3. Only update sections that changed
4. Use `TextBuffer` marks and iterators for targeted updates

**Benefits:**
- Minimal visual disruption
- Preserves scroll position naturally
- No flickering for unchanged sections
- More efficient (less CPU for layout)

**Code Changes:**
```python
class DiagnosticsPanel:
    def __init__(self):
        self._cached_sections = {
            'header': '',
            'structure': '',
            'static': '',
            'runtime': ''
        }
        self._section_marks = {}  # TextMarks for section boundaries
    
    def _update_display_differential(self):
        """Update only changed sections."""
        new_sections = self._generate_sections()
        
        for section_name, new_content in new_sections.items():
            if new_content != self._cached_sections[section_name]:
                self._update_section(section_name, new_content)
                self._cached_sections[section_name] = new_content
```

### Approach 2: Double Buffering with Fade Transition
Use two TextViews and fade between them.

**Implementation:**
1. Maintain two TextView widgets in a Stack
2. Update inactive TextView while visible one is displayed
3. Fade transition between views when content changes

**Benefits:**
- Smooth visual transition
- No perceived flickering

**Drawbacks:**
- More complex implementation
- Higher memory usage
- May still have brief visual artifacts

### Approach 3: Reduce Update Frequency with Smart Detection
Only update when data actually changes.

**Implementation:**
1. Hash or compare runtime metrics before updating
2. Skip updates if data unchanged
3. Increase update interval to 1000ms
4. Use event-driven updates for critical changes

**Benefits:**
- Simple to implement
- Reduces unnecessary updates

**Code Changes:**
```python
def _on_update_timer(self):
    if self.current_transition:
        new_data = self._get_current_diagnostics_data()
        
        # Only update if data changed
        if new_data != self._last_displayed_data:
            self._update_display()
            self._last_displayed_data = new_data
    
    return True
```

### Approach 4: Combine Multiple Strategies (BEST)
Use differential updates + change detection + adjusted timing.

**Implementation:**
1. Split display into static (rarely changes) and dynamic (updates often) sections
2. Update static sections only when structure changes
3. Update dynamic sections (runtime metrics) every 500ms but only if values changed
4. Use differential text buffer updates for smooth rendering
5. Implement smart scroll behavior (stick to bottom if scrolled down)

## Recommended Implementation Plan

### Phase 1: Data Change Detection (Quick Win)
**Effort:** 30 minutes  
**Impact:** Reduces updates by ~50-80%

1. Add `_last_diagnostics_hash` attribute
2. Hash runtime metrics before updating
3. Skip `buffer.set_text()` if unchanged

```python
def _on_update_timer(self):
    if self.current_transition:
        new_hash = self._compute_diagnostics_hash()
        
        if new_hash != self._last_diagnostics_hash:
            self._update_display()
            self._last_diagnostics_hash = new_hash
    
    return True

def _compute_diagnostics_hash(self):
    """Compute hash of current diagnostic data."""
    if not self.runtime_analyzer:
        return None
    
    diag = self.runtime_analyzer.get_transition_diagnostics(
        self.current_transition.id
    )
    
    # Hash relevant fields
    return hash((
        diag.get('total_events', 0),
        diag.get('last_event_time', 0),
        diag.get('throughput', 0),
        tuple(e.get('time', 0) for e in diag.get('recent_events', [])[-5:])
    ))
```

### Phase 2: Differential Section Updates (Medium Effort)
**Effort:** 2-3 hours  
**Impact:** Eliminates flickering completely

1. Split `_show_diagnostics()` into section generators
2. Track previous section content
3. Update only changed sections using TextBuffer API
4. Add TextMarks for section boundaries

```python
def _initialize_text_sections(self):
    """Initialize text buffer with section marks."""
    buffer = self.textview.get_buffer()
    
    # Create marks for section boundaries
    iter_start = buffer.get_start_iter()
    self._section_marks['header_start'] = buffer.create_mark(None, iter_start, True)
    self._section_marks['structure_start'] = buffer.create_mark(None, iter_start, True)
    self._section_marks['static_start'] = buffer.create_mark(None, iter_start, True)
    self._section_marks['runtime_start'] = buffer.create_mark(None, iter_start, True)
    self._section_marks['end'] = buffer.create_mark(None, iter_start, False)

def _update_section(self, section_name, new_content):
    """Update specific section without touching others."""
    buffer = self.textview.get_buffer()
    
    # Get section boundaries
    start_mark = self._section_marks[f'{section_name}_start']
    
    # Find next section or end
    section_order = ['header', 'structure', 'static', 'runtime']
    current_idx = section_order.index(section_name)
    
    if current_idx < len(section_order) - 1:
        end_mark = self._section_marks[f'{section_order[current_idx + 1]}_start']
    else:
        end_mark = self._section_marks['end']
    
    # Get iterators
    start_iter = buffer.get_iter_at_mark(start_mark)
    end_iter = buffer.get_iter_at_mark(end_mark)
    
    # Delete old content
    buffer.delete(start_iter, end_iter)
    
    # Insert new content
    start_iter = buffer.get_iter_at_mark(start_mark)
    buffer.insert(start_iter, new_content)
    
    # Move next section mark
    if current_idx < len(section_order) - 1:
        next_mark = self._section_marks[f'{section_order[current_idx + 1]}_start']
        new_iter = buffer.get_iter_at_mark(start_mark)
        new_iter.forward_chars(len(new_content))
        buffer.move_mark(next_mark, new_iter)
```

### Phase 3: Optimize Update Frequency (Fine-tuning)
**Effort:** 30 minutes  
**Impact:** Balances responsiveness and performance

1. Adjust timer interval based on simulation speed
2. Separate static (structure) from dynamic (metrics) updates
3. Update structure only on transition change
4. Update metrics every 500ms but skip if no change

```python
def set_transition(self, transition):
    """Set transition and update static sections immediately."""
    self.current_transition = transition
    
    # Update static sections immediately (structure, static analysis)
    self._update_static_sections()
    
    # Start dynamic updates timer
    self._start_updates()

def _on_update_timer(self):
    """Update only dynamic sections."""
    if self.current_transition:
        # Only update runtime metrics section
        self._update_dynamic_sections()
    
    return True
```

## Implementation Priority

### Immediate (Do First):
✅ **Phase 1: Change Detection** - Quick win, significant improvement

### High Priority:
✅ **Phase 2: Differential Updates** - Eliminates flickering completely

### Optional (If Needed):
⚪ **Phase 3: Frequency Optimization** - Fine-tuning for performance

## Testing Plan

1. **Manual Testing:**
   - Run simulation with diagnostics panel visible
   - Verify no visible flickering
   - Check scroll position preservation
   - Test with fast and slow simulations

2. **Performance Testing:**
   - Measure CPU usage before/after
   - Check memory usage with differential updates
   - Verify update latency < 100ms

3. **Edge Cases:**
   - Transition with no events
   - Very high event rate (>100/sec)
   - Auto-tracking mode switching
   - Panel resize during updates

## Success Criteria

- ✅ No visible flickering during real-time updates
- ✅ Scroll position preserved correctly
- ✅ Updates reflect latest data within 500ms
- ✅ CPU usage < 5% during updates
- ✅ Smooth user experience (60fps rendering)

## Alternative: If Flickering Persists

**Last Resort Options:**

1. **Use HTML rendering via WebKit:**
   - Embed WebKit view instead of TextView
   - Update via JavaScript DOM manipulation
   - CSS transitions for smooth updates

2. **Use Cairo drawing:**
   - Custom widget with Cairo rendering
   - Direct text drawing with caching
   - More control over rendering pipeline

3. **Reduce to event-driven updates:**
   - Only update on firing events
   - No periodic timer
   - May miss some state changes

## Estimated Total Effort

- Phase 1: **30 minutes**
- Phase 2: **2-3 hours**  
- Phase 3: **30 minutes**
- Testing: **1 hour**

**Total: ~4-5 hours** for complete flickering elimination

## Files to Modify

1. `src/shypn/analyses/diagnostics_panel.py` - Main implementation
2. `src/shypn/ui/panels/dynamic_analyses/diagnostics_category.py` - Category wrapper (minimal changes)

## Backward Compatibility

All changes are internal to the diagnostics panel implementation. No API changes required. Existing code that uses `set_transition()` and `_update_display()` will continue to work.
