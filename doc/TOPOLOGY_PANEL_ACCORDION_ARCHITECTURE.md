# Topology Panel - Accordion Architecture (Expandable Sections)

**Date:** October 20, 2025  
**Author:** Simão Eugénio  
**Status:** Design Phase

## Overview

Instead of separate detail pages, each analyzer has an **expandable section** with a **vertical (V) button** that reveals a detailed report **below** the summary, **on the same tab**.

---

## Visual Design

### COLLAPSED STATE (Default)
```
┌─────────────────────────────────────────────────────┐
│ Topology Analysis                          [Float]  │
├─────────────────────────────────────────────────────┤
│  Structural │ Graph & Network │ Behavioral          │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌─ P-Invariants (Conservation Laws) ─────────────┐ │
│  │                                                 │ │
│  │  Found 3 invariants                             │ │
│  │  • 5 places  • 3 places  • 7 places            │ │
│  │                                                 │ │
│  │  [Analyze] [Highlight] [V]                     │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─ T-Invariants (Reproducible Sequences) ────────┐ │
│  │                                                 │ │
│  │  Found 2 invariants                             │ │
│  │  • 4 transitions  • 6 transitions              │ │
│  │                                                 │ │
│  │  [Analyze] [Highlight] [V]                     │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─ Siphons (Deadlock Detection) ──────────────────┐ │
│  │                                                 │ │
│  │  Not analyzed                                   │ │
│  │                                                 │ │
│  │  [Analyze] [Highlight] [V]                     │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
└─────────────────────────────────────────────────────┘
```

### EXPANDED STATE (One analyzer expanded)
```
┌─────────────────────────────────────────────────────┐
│ Topology Analysis                          [Float]  │
├─────────────────────────────────────────────────────┤
│  Structural │ Graph & Network │ Behavioral          │
├─────────────────────────────────────────────────────┤
│                                                      │
│  ┌─ P-Invariants (Conservation Laws) ─────────────┐ │
│  │                                                 │ │
│  │  Found 3 invariants                             │ │
│  │  • 5 places  • 3 places  • 7 places            │ │
│  │                                                 │ │
│  │  [Analyze] [Highlight] [^]                     │ │
│  │                                                 │ │
│  │  ╔═══════════════════════════════════════════╗ │ │
│  │  ║ DETAILED REPORT                           ║ │ │
│  │  ╠═══════════════════════════════════════════╣ │ │
│  │  ║                                           ║ │ │
│  │  ║ P-Invariant #1: 5 places                  ║ │ │
│  │  ║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║ │ │
│  │  ║ Places:                                   ║ │ │
│  │  ║   • Glucose (weight: 1)                   ║ │ │
│  │  ║   • ATP (weight: 2)                       ║ │ │
│  │  ║   • Pyruvate (weight: 1)                  ║ │ │
│  │  ║   • NADH (weight: 3)                      ║ │ │
│  │  ║   • Lactate (weight: 1)                   ║ │ │
│  │  ║                                           ║ │ │
│  │  ║ Conservation equation:                    ║ │ │
│  │  ║   1×Glucose + 2×ATP + 1×Pyruvate +       ║ │ │
│  │  ║   3×NADH + 1×Lactate = constant          ║ │ │
│  │  ║                                           ║ │ │
│  │  ║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║ │ │
│  │  ║                                           ║ │ │
│  │  ║ P-Invariant #2: 3 places                  ║ │ │
│  │  ║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║ │ │
│  │  ║ Places:                                   ║ │ │
│  │  ║   • NAD+ (weight: 1)                      ║ │ │
│  │  ║   • NADH (weight: 1)                      ║ │ │
│  │  ║   • Water (weight: 2)                     ║ │ │
│  │  ║                                           ║ │ │
│  │  ║ [Export CSV] [Export PDF] [Highlight All]║ │ │
│  │  ╚═══════════════════════════════════════════╝ │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
│  ┌─ T-Invariants (Reproducible Sequences) ────────┐ │
│  │                                                 │ │
│  │  Found 2 invariants                             │ │
│  │  • 4 transitions  • 6 transitions              │ │
│  │  │                                                 │ │
│  │  [Analyze] [Highlight] [V]                     │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
└─────────────────────────────────────────────────────┘
```

---

## Architecture Comparison

### BEFORE (Current - Summary Only)
```
Each Analyzer Section:
┌─────────────────────────────────┐
│ Title                           │
│ Summary (2-3 lines)             │
│ [Analyze] [Highlight]           │
└─────────────────────────────────┘
```

### AFTER (Accordion - Expandable)
```
Each Analyzer Section:
┌─────────────────────────────────┐
│ Title                           │
│ Summary (2-3 lines)             │
│ [Analyze] [Highlight] [V/^]     │
│                                 │
│ ┌─────────────────────────────┐ │  ← Hidden by default
│ │ DETAILED REPORT (Scrolled)  │ │
│ │                             │ │
│ │ • Full results              │ │
│ │ • Element lists             │ │
│ │ • Statistics                │ │
│ │ • Export buttons            │ │
│ └─────────────────────────────┘ │
└─────────────────────────────────┘
```

---

## Component Structure

### GTK Widget Hierarchy
```
GtkFrame (analyzer_frame)
  └─ GtkBox (vertical)
       ├─ GtkLabel (title_label)
       ├─ GtkBox (summary_box)
       │    ├─ GtkLabel (result_label) ← Summary (2-3 lines)
       │    └─ GtkButtonBox
       │         ├─ GtkButton (analyze_btn)
       │         ├─ GtkButton (highlight_btn)
       │         └─ GtkToggleButton (expand_btn) [V/^] ← NEW!
       │
       └─ GtkRevealer (detail_revealer) ← NEW! Animated expand/collapse
            └─ GtkScrolledWindow
                 └─ GtkBox (vertical)
                      ├─ GtkLabel (detail_report_label) ← Full report with markup
                      └─ GtkButtonBox
                           ├─ GtkButton (export_csv_btn) ← Future
                           ├─ GtkButton (export_pdf_btn) ← Future
                           └─ GtkButton (highlight_all_btn) ← Future
```

### Key Widget: GtkRevealer
- **Purpose:** Smooth animated expand/collapse
- **Properties:**
  - `reveal-child`: False (default collapsed)
  - `transition-type`: slide-down
  - `transition-duration`: 300ms
- **Behavior:**
  - Click [V] → `reveal-child = True` → Slides down
  - Click [^] → `reveal-child = False` → Slides up

---

## User Interaction Flow

### 1. Initial State (All Collapsed)
```
User sees:
  ✓ All analyzer summaries visible
  ✓ All [V] buttons ready to expand
  ✓ Compact view - easy to scan
```

### 2. Click [V] on P-Invariants
```
Action:
  1. Toggle button changes: [V] → [^]
  2. GtkRevealer animates: reveal-child = True
  3. Detail report slides down smoothly
  4. Scrollbar appears if content > available height

Result:
  ✓ P-Invariants section now shows full report
  ✓ Other analyzers remain collapsed
  ✓ User can scroll within detail report
```

### 3. Click [V] on T-Invariants (P-Invariants still expanded)
```
Behavior Options:

OPTION A (Multiple Open):
  ✓ Both P-Invariants and T-Invariants expanded
  ✓ User can compare side-by-side (by scrolling)
  ✓ More flexible

OPTION B (Accordion - One at a time):
  ✓ P-Invariants auto-collapses
  ✓ T-Invariants expands
  ✓ Cleaner, less scrolling
  ✓ Similar to typical accordions

RECOMMENDATION: OPTION A (multiple open)
  - More useful for analysis
  - User controls what they want to see
```

### 4. Click [^] to Collapse
```
Action:
  1. Toggle button changes: [^] → [V]
  2. GtkRevealer animates: reveal-child = False
  3. Detail report slides up smoothly
  4. Section returns to compact summary

Result:
  ✓ Summary still visible
  ✓ More screen space for other analyzers
```

---

## Detailed Report Format (Per Analyzer)

### P-Invariants (Count-based)
```
╔═══════════════════════════════════════════╗
║ DETAILED REPORT: P-Invariants             ║
╠═══════════════════════════════════════════╣
║                                           ║
║ Total: 3 invariants found                 ║
║                                           ║
║ P-Invariant #1                            ║
║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║
║   Places (5):                             ║
║     • Glucose      (weight: 1)            ║
║     • ATP          (weight: 2)            ║
║     • Pyruvate     (weight: 1)            ║
║     • NADH         (weight: 3)            ║
║     • Lactate      (weight: 1)            ║
║                                           ║
║   Conservation Law:                       ║
║     1×M(Glucose) + 2×M(ATP) + ... = K₁    ║
║                                           ║
║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║
║                                           ║
║ P-Invariant #2                            ║
║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║
║   Places (3):                             ║
║     • NAD+         (weight: 1)            ║
║     • NADH         (weight: 1)            ║
║     • Water        (weight: 2)            ║
║                                           ║
║ [Highlight All] [Export CSV] [Export PDF] ║
╚═══════════════════════════════════════════╝
```

### Reachability (Boolean + Stats)
```
╔═══════════════════════════════════════════╗
║ DETAILED REPORT: Reachability             ║
╠═══════════════════════════════════════════╣
║                                           ║
║ Result: ✓ Network is reachable            ║
║                                           ║
║ State Space Exploration:                  ║
║   • Total states explored: 1,247          ║
║   • Reachable states: 1,247 (100%)        ║
║   • Unreachable states: 0                 ║
║   • Max depth: 23 transitions             ║
║   • Average depth: 12.4 transitions       ║
║                                           ║
║ Reachability Graph Properties:            ║
║   • Strongly connected: Yes               ║
║   • Diameter: 45                          ║
║   • Average path length: 15.7             ║
║                                           ║
║ Interpretation:                           ║
║   All states can be reached from the      ║
║   initial marking. The network has good   ║
║   connectivity and no dead ends.          ║
║                                           ║
║ [Visualize Graph] [Export DOT]            ║
╚═══════════════════════════════════════════╝
```

### Deadlocks (Boolean + List)
```
╔═══════════════════════════════════════════╗
║ DETAILED REPORT: Deadlocks                ║
╠═══════════════════════════════════════════╣
║                                           ║
║ Result: ✗ Deadlocks found (2 states)      ║
║                                           ║
║ Deadlock State #1                         ║
║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║
║   Marking:                                ║
║     • Place_1: 3 tokens                   ║
║     • Place_5: 1 token                    ║
║     • Place_9: 0 tokens                   ║
║     • (all other places: 0)               ║
║                                           ║
║   No enabled transitions                  ║
║   Path to deadlock: 7 transitions         ║
║   [Highlight] [Show Path]                 ║
║                                           ║
║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║
║                                           ║
║ Deadlock State #2                         ║
║ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ ║
║   Marking:                                ║
║     • Place_2: 2 tokens                   ║
║     • Place_7: 2 tokens                   ║
║     • (all other places: 0)               ║
║                                           ║
║   No enabled transitions                  ║
║   Path to deadlock: 5 transitions         ║
║   [Highlight] [Show Path]                 ║
║                                           ║
║ [Export All Deadlocks]                    ║
╚═══════════════════════════════════════════╝
```

---

## Implementation Layers

### 1. UI Layer (topology_panel.ui)
**Changes Needed:**
- Add `GtkRevealer` widget after each button box
- Add `GtkToggleButton` (expand_btn) to each analyzer
- Add detail report `GtkLabel` inside revealer
- Set proper IDs for all new widgets

### 2. Loader Layer (topology_panel_loader.py)
**Changes Needed:**
```python
# Collect new widget references
self.expand_buttons = {}    # 12 toggle buttons
self.detail_revealers = {}  # 12 revealers
self.detail_labels = {}     # 12 detail report labels

for analyzer_name in analyzer_names:
    self.expand_buttons[analyzer_name] = builder.get_object(f'{analyzer_name}_expand_btn')
    self.detail_revealers[analyzer_name] = builder.get_object(f'{analyzer_name}_detail_revealer')
    self.detail_labels[analyzer_name] = builder.get_object(f'{analyzer_name}_detail_label')
```

### 3. Controller Layer (topology_panel_controller.py)
**New Method:**
```python
def on_expand_clicked(self, toggle_button: Gtk.ToggleButton, analyzer_name: str):
    """Handle expand/collapse button toggle.
    
    Args:
        toggle_button: The toggle button that was clicked ([V] or [^])
        analyzer_name: Name of the analyzer to expand/collapse
    """
    is_expanded = toggle_button.get_active()
    revealer = self.detail_revealers.get(analyzer_name)
    
    if not revealer:
        return
    
    # Animate expand/collapse
    revealer.set_reveal_child(is_expanded)
    
    # If expanding and we have results, populate detail report
    if is_expanded and analyzer_name in self.results:
        self._populate_detail_report(analyzer_name)
```

**New Method:**
```python
def _populate_detail_report(self, analyzer_name: str):
    """Generate detailed report markup for an analyzer.
    
    Args:
        analyzer_name: Name of the analyzer
    """
    result = self.results.get(analyzer_name)
    if not result:
        return
    
    detail_label = self.detail_labels.get(analyzer_name)
    if not detail_label:
        return
    
    # Generate detailed markup based on analyzer type
    if analyzer_name == 'p_invariants':
        markup = self._format_p_invariants_detail(result)
    elif analyzer_name == 't_invariants':
        markup = self._format_t_invariants_detail(result)
    # ... (12 format methods, one per analyzer)
    
    detail_label.set_markup(markup)
```

### 4. Base Layer (topology_panel_base.py)
**No changes needed** - handles attach/detach/float only

---

## Advantages of Accordion Design

### ✅ Progressive Disclosure
- Start with compact overview (all summaries visible)
- Expand only what you need
- Reduces cognitive load

### ✅ Same-Tab Navigation
- No page switching
- No loss of context
- Easy comparison (expand multiple)

### ✅ Smooth Animation
- GtkRevealer provides native slide animation
- Professional feel
- Visual feedback

### ✅ Flexible
- User controls what's expanded
- Multiple sections can be open
- Easy to collapse all and start fresh

### ✅ Scalable
- Works with 12 analyzers
- Works with 100+ invariants (scrollable detail)
- No pagination needed

---

## Questions to Resolve

### 1. Multiple vs Single Expansion
**Should multiple analyzers be expandable at once?**
- **Option A:** Yes (recommended) - More flexible, can compare
- **Option B:** No (true accordion) - Auto-collapse others, cleaner

**Recommendation:** Option A (multiple open)

### 2. Auto-Expand After Analysis
**Should analyzer auto-expand after clicking Analyze?**
- **Option A:** Yes - Show results immediately
- **Option B:** No - Keep collapsed, user expands manually

**Recommendation:** Option A (auto-expand after analysis)

### 3. Export Buttons Location
**Where should export buttons go?**
- **Option A:** Inside detail report (per-analyzer exports)
- **Option B:** In header (export all results)
- **Option C:** Both

**Recommendation:** Option A (inside detail report) for Day 2/3

### 4. Detail Report Complexity
**How detailed should reports be?**
- **Minimal:** Just formatted lists
- **Moderate:** Lists + statistics + interpretation
- **Maximal:** Full analysis + visualizations + recommendations

**Recommendation:** Start **Moderate**, expand to **Maximal** in Day 3

---

## Implementation Phases

### Phase 1: Core Accordion (Day 2 - 4 hours)
1. Update UI with GtkRevealer widgets (12 revealers)
2. Add expand toggle buttons (12 buttons)
3. Update loader to collect new widgets
4. Implement `on_expand_clicked()` in controller
5. Test expand/collapse animation

### Phase 2: Detail Reports (Day 2 - 4 hours)
1. Implement `_format_*_detail()` methods (12 formatters)
2. Populate detail labels on expand
3. Add auto-expand after analysis
4. Test with real models

### Phase 3: Enhanced Details (Day 3 - 4 hours)
1. Add per-analyzer export buttons
2. Add individual highlighting from detail view
3. Add statistics and interpretation
4. Polish formatting and styling

---

## Next Steps

**Immediate:** 
1. Confirm accordion design with user ✓
2. Decide on multiple vs single expansion
3. Decide on auto-expand behavior

**Then:**
1. Update UI file with GtkRevealer widgets
2. Update loader with new widget references
3. Implement controller expand logic
4. Test with application launch

Would you like me to proceed with this accordion architecture?
