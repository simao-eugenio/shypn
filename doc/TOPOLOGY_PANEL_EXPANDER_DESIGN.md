# Topology Panel - GtkExpander Design (Simplified)

**Date:** October 20, 2025  
**Status:** 🎯 ARCHITECTURE APPROVED  
**Design Philosophy:** Expand = Analyze (No buttons, scientific workflow)

---

## Core Principle

> **"Expanding the section triggers the analysis automatically"**

**NO BUTTONS.** Just clean expanders with reports.

---

## Visual Design

### All Collapsed (Initial State)
```
┌─────────────────────────────────────┐
│ Topology Analysis            [Float]│
├─────────────────────────────────────┤
│ Structural │ Graph & Network │ Behavioral │
├─────────────────────────────────────┤
│                                     │
│ > P-Invariants                      │
│ > T-Invariants                      │
│ > Siphons                           │
│ > Traps                             │
│                                     │
└─────────────────────────────────────┘
```

### First Expander Pre-Opened (Not Yet Analyzed)
```
┌─────────────────────────────────────┐
│ Topology Analysis            [Float]│
├─────────────────────────────────────┤
│ Structural │ Graph & Network │ Behavioral │
├─────────────────────────────────────┤
│                                     │
│ V P-Invariants                      │
│ ┌─────────────────────────────────┐ │
│ │                                 │ │
│ │  Not yet analyzed.              │ │
│ │  Collapse and expand again      │ │
│ │  to run analysis.               │ │
│ │                                 │ │
│ └─────────────────────────────────┘ │
│                                     │
│ > T-Invariants                      │
│ > Siphons                           │
│ > Traps                             │
│                                     │
└─────────────────────────────────────┘
```

### User Expands (Analysis Running)
```
┌─────────────────────────────────────┐
│ V P-Invariants                      │
│ ┌─────────────────────────────────┐ │
│ │                                 │ │
│ │  🔄 Analyzing P-Invariants...   │ │
│ │                                 │ │
│ │  This may take a few seconds    │ │
│ │  for large models.              │ │
│ │                                 │ │
│ └─────────────────────────────────┘ │
│                                     │
│ > T-Invariants                      │
```

### Analysis Complete (Full Report)
```
┌─────────────────────────────────────┐
│ V P-Invariants                      │
│ ┌─────────────────────────────────┐ │
│ │ P-Invariants Analysis Results   │ │
│ │                                 │ │
│ │ Found: 5 invariants             │ │
│ │                                 │ │
│ │ Invariant 1 (weight: 1.0):      │ │
│ │   • p1, p2, p3                  │ │
│ │                                 │ │
│ │ Invariant 2 (weight: 2.0):      │ │
│ │   • p4, p5, p6, p7              │ │
│ │                                 │ │
│ │ Invariant 3 (weight: 1.0):      │ │
│ │   • p8, p9                      │ │
│ │                                 │ │
│ │ ... (showing first 10)          │ │
│ │                                 │ │
│ │ ───────────────────────────────│ │
│ │ Analysis completed in 0.23s     │ │
│ └─────────────────────────────────┘ │
│                                     │
│ > T-Invariants                      │
```

### Re-Expand (Cached Results - Instant)
```
┌─────────────────────────────────────┐
│ V P-Invariants                      │
│ ┌─────────────────────────────────┐ │
│ │ P-Invariants Analysis Results   │ │
│ │ (Cached from previous run)      │ │
│ │                                 │ │
│ │ Found: 5 invariants             │ │
│ │ ...                             │ │
│ └─────────────────────────────────┘ │
```

### Error Case
```
┌─────────────────────────────────────┐
│ V P-Invariants                      │
│ ┌─────────────────────────────────┐ │
│ │ ⚠ Analysis Failed               │ │
│ │                                 │ │
│ │ Error: No Petri net loaded      │ │
│ │                                 │ │
│ │ Please load a model first.      │ │
│ └─────────────────────────────────┘ │
```

---

## Widget Structure

### Complete Hierarchy
```
GtkWindow (topology_window)
  └─ GtkBox (topology_content)
       ├─ GtkBox (header with float button)
       └─ GtkNotebook (3 tabs)
            ├─ Tab 1: Structural Analysis
            │    └─ GtkScrolledWindow
            │         └─ GtkBox (vertical container)
            │              ├─ GtkExpander (p_invariants_expander) ← expanded=True
            │              │    └─ GtkScrolledWindow (vexpand=True)
            │              │         └─ GtkLabel (p_invariants_report_label)
            │              ├─ GtkExpander (t_invariants_expander)
            │              │    └─ GtkScrolledWindow (vexpand=True)
            │              │         └─ GtkLabel (t_invariants_report_label)
            │              ├─ GtkExpander (siphons_expander)
            │              │    └─ GtkScrolledWindow (vexpand=True)
            │              │         └─ GtkLabel (siphons_report_label)
            │              └─ GtkExpander (traps_expander)
            │                   └─ GtkScrolledWindow (vexpand=True)
            │                        └─ GtkLabel (traps_report_label)
            │
            ├─ Tab 2: Graph & Network Analysis
            │    └─ [Same structure, 4 expanders]
            │
            └─ Tab 3: Behavioral Analysis
                 └─ [Same structure, 5 expanders]
```

### Key Properties

**GtkExpander:**
- `id`: `{analyzer}_expander`
- `expanded`: False (except p_invariants = True)
- `vexpand`: False (only expand when opened)
- Label: Bold text with analyzer name

**GtkScrolledWindow (inside expander):**
- `vexpand`: True (fill available space)
- `hexpand`: True
- `min-content-height`: 100
- `max-content-height`: -1 (no limit - expand to fill)
- `hscrollbar-policy`: automatic
- `vscrollbar-policy`: automatic

**GtkLabel (report):**
- `id`: `{analyzer}_report_label`
- `selectable`: True (copy results)
- `use-markup`: True (formatting)
- `wrap`: True
- `xalign`: 0 (left-align)
- `margin`: 12

---

## Signal Flow

### User Action: Click to Expand

```
1. User clicks > on "T-Invariants"
   │
   ├─→ GtkExpander.expanded changes to True
   │
   ├─→ 'notify::expanded' signal emitted
   │
   ├─→ controller.on_expander_toggled(expander, param, 't_invariants')
   │
   ├─→ Check: expander.get_expanded() == True? YES
   │   Check: analyzer already analyzed? NO
   │
   ├─→ Show spinner: "🔄 Analyzing T-Invariants..."
   │
   ├─→ Run analysis in background thread
   │   (UI remains responsive)
   │
   ├─→ Analysis completes
   │
   ├─→ Format results: _format_report('t_invariants', result)
   │
   └─→ Update label: report_label.set_markup(formatted_report)
```

### User Action: Collapse

```
1. User clicks V on "T-Invariants"
   │
   ├─→ GtkExpander.expanded changes to False
   │
   ├─→ 'notify::expanded' signal emitted
   │
   ├─→ controller.on_expander_toggled(expander, param, 't_invariants')
   │
   ├─→ Check: expander.get_expanded() == False
   │
   └─→ Do nothing (keep results cached for re-expand)
```

### User Action: Re-Expand (Already Analyzed)

```
1. User clicks > on "T-Invariants" (again)
   │
   ├─→ GtkExpander.expanded changes to True
   │
   ├─→ 'notify::expanded' signal emitted
   │
   ├─→ controller.on_expander_toggled(expander, param, 't_invariants')
   │
   ├─→ Check: expander.get_expanded() == True? YES
   │   Check: analyzer already analyzed? YES (cached)
   │
   └─→ Instantly show cached results (no spinner)
       report_label already has markup from previous run
```

---

## Controller Architecture

### Widget Collections
```python
class TopologyPanelController:
    def __init__(self, expanders, report_labels, ...):
        self.expanders = expanders        # {analyzer: GtkExpander}
        self.report_labels = report_labels # {analyzer: GtkLabel}
        self.results = {}                  # {analyzer: analysis_result}
        self.analyzing = set()             # Set of currently analyzing
```

### Key Methods

**1. on_expander_toggled()**
```python
def on_expander_toggled(self, expander: Gtk.Expander, 
                        param, analyzer_name: str):
    """Handle expander expand/collapse."""
    is_expanded = expander.get_expanded()
    
    if not is_expanded:
        # User collapsed - do nothing (keep cache)
        return
    
    # User expanded
    if analyzer_name in self.results:
        # Already analyzed - show cached results
        # (report_label already has markup, nothing to do)
        return
    
    # First time expanding - run analysis
    if analyzer_name not in self.analyzing:
        self._trigger_analysis(analyzer_name)
```

**2. _trigger_analysis()**
```python
def _trigger_analysis(self, analyzer_name: str):
    """Trigger analysis and show spinner."""
    self.analyzing.add(analyzer_name)
    
    # Show spinner
    label = self.report_labels[analyzer_name]
    label.set_markup(f"<b>🔄 Analyzing {self._get_display_name(analyzer_name)}...</b>\n\n"
                     f"This may take a few seconds for large models.")
    
    # Run analysis in background thread
    def analyze_thread():
        try:
            result = self._run_analysis(analyzer_name)
            GLib.idle_add(self._on_analysis_complete, analyzer_name, result)
        except Exception as e:
            GLib.idle_add(self._on_analysis_error, analyzer_name, str(e))
    
    threading.Thread(target=analyze_thread, daemon=True).start()
```

**3. _on_analysis_complete()**
```python
def _on_analysis_complete(self, analyzer_name: str, result):
    """Handle successful analysis completion."""
    self.analyzing.discard(analyzer_name)
    self.results[analyzer_name] = result
    
    # Format and display report
    report = self._format_report(analyzer_name, result)
    label = self.report_labels[analyzer_name]
    label.set_markup(report)
```

**4. _format_report()**
```python
def _format_report(self, analyzer_name: str, result) -> str:
    """Format analysis results as Pango markup."""
    if analyzer_name == 'p_invariants':
        return self._format_p_invariants_report(result)
    elif analyzer_name == 't_invariants':
        return self._format_t_invariants_report(result)
    # ... (12 formatters total)
```

---

## Initial State Handling

### Problem: First Expander Pre-Opened
The UI file has `p_invariants_expander.expanded = True`, but we DON'T want to auto-analyze on panel load.

### Solution: Track Initial State
```python
def __init__(self, ...):
    self.initial_state_handled = set()
    
def on_expander_toggled(self, expander, param, analyzer_name):
    is_expanded = expander.get_expanded()
    
    # Handle initial pre-expanded state
    if is_expanded and analyzer_name not in self.initial_state_handled:
        self.initial_state_handled.add(analyzer_name)
        # Show "not yet analyzed" message
        label = self.report_labels[analyzer_name]
        label.set_markup(
            "<b>Not yet analyzed.</b>\n\n"
            "Collapse and expand again to run analysis."
        )
        return
    
    # Normal expand/collapse logic...
```

---

## Advantages

### ✅ **Ultra-Clean UI**
- No button clutter
- Just expanders and reports
- Matches right_panel.ui pattern

### ✅ **Intuitive Workflow**
- "I want to see invariants" → Click to expand → See results
- One action does everything
- Scientific software pattern (like Jupyter notebooks)

### ✅ **Better Performance**
- Results cached - re-expanding is instant
- Background threads keep UI responsive
- Only analyze what user needs

### ✅ **Separation of Concerns**
- Topology Panel = Analyze topology
- Switch Palette = Highlight/select elements
- Each tool focused on one job

### ✅ **Vertical Expansion**
- ScrolledWindow with max-content-height=-1
- Reports expand to fill available space
- Long reports scroll internally

---

## Implementation Phases

### Phase 1: UI File Transformation (1 hour)
- Replace all 12 GtkFrame widgets with GtkExpander
- Remove all button boxes
- Add GtkScrolledWindow inside each expander (vexpand=True)
- Keep single GtkLabel for report (no separate summary/detail)
- Set p_invariants_expander.expanded = True

### Phase 2: Controller Refactor (1 hour)
- Remove button-related code
- Add expander signal handling
- Implement initial state logic
- Add spinner/progress messages
- Keep existing _format_*_detail() methods (rename to _format_*_report())

### Phase 3: Loader Update (30 minutes)
- Remove button collections
- Collect expanders and report_labels
- Connect 'notify::expanded' signals

### Phase 4: Testing (30 minutes)
- Test expand triggers analysis
- Test collapse keeps cache
- Test re-expand shows cached results
- Test first expander pre-opened behavior
- Test spinner during analysis
- Test error display

---

## Migration Notes

### What We Remove:
- ❌ All GtkButton widgets (analyze, highlight, expand)
- ❌ All GtkToggleButton widgets
- ❌ All GtkButtonBox containers
- ❌ All GtkRevealer widgets
- ❌ Separate summary/detail labels (use single report label)

### What We Keep:
- ✅ 3-tab notebook structure
- ✅ Base class (Wayland-safe attach/detach)
- ✅ Analysis classes (unchanged)
- ✅ Result formatting logic (just rename methods)
- ✅ Cache mechanism

### What We Add:
- ✅ 12 GtkExpander widgets
- ✅ 12 GtkScrolledWindow widgets (vexpand=True)
- ✅ Initial state tracking
- ✅ Background thread analysis
- ✅ Spinner/progress messages

---

## Code Reduction

**Before (Accordion with buttons):**
- UI: ~1,200 lines
- Controller: ~580 lines
- Loader: ~120 lines
- **Total: ~1,900 lines**

**After (Expander without buttons):**
- UI: ~800 lines (fewer widgets)
- Controller: ~500 lines (simpler logic)
- Loader: ~100 lines (fewer collections)
- **Total: ~1,400 lines**

**Reduction: ~500 lines** ✅

---

## User Questions Answered

### Q1: First Expander Behavior?
**Answer: A** - P-Invariants pre-expanded, shows "Collapse/expand to analyze"

### Q2: Re-Expand Behavior?
**Answer: A** - Show cached results (no re-analysis)

### Q3: Analysis Feedback?
**Answer: A (Spinner)** - Show "🔄 Analyzing..." with spinner in report area

### Q4: Error Handling?
**Answer: A** - Show error in report area, keep expanded

### Q5: Vertical Expansion?
**Answer: YES** - GtkScrolledWindow with max-content-height=-1 (unlimited)

---

## Ready to Implement! 🚀

**Status:** Architecture approved by user  
**Next Step:** Transform UI file with Python script  
**Estimated Time:** 3 hours total

---

**Author:** GitHub Copilot  
**Approved:** User (October 20, 2025)
