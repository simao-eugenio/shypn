# Topology Panel - Accordion Design (Simple Diagram)

**Concept:** Each analyzer has a **[V]** button that expands a detailed report **below** it on the same tab.

---

## Side-by-Side Comparison

```
┌──────────── COLLAPSED ────────────┐    ┌──────────── EXPANDED ──────────────┐
│                                   │    │                                    │
│  P-Invariants                     │    │  P-Invariants                      │
│  Found 3 invariants               │    │  Found 3 invariants                │
│  [Analyze] [Highlight] [V]        │    │  [Analyze] [Highlight] [^]         │
│                                   │    │                                    │
│                                   │    │  ┌──────────────────────────────┐  │
│                                   │    │  │ DETAILED REPORT              │  │
│                                   │    │  ├──────────────────────────────┤  │
│                                   │    │  │ P-Invariant #1: 5 places     │  │
│                                   │    │  │   • Glucose (weight: 1)      │  │
│                                   │    │  │   • ATP (weight: 2)          │  │
│                                   │    │  │   • Pyruvate (weight: 1)     │  │
│                                   │    │  │   • NADH (weight: 3)         │  │
│                                   │    │  │   • Lactate (weight: 1)      │  │
│                                   │    │  │                              │  │
│                                   │    │  │ P-Invariant #2: 3 places     │  │
│                                   │    │  │   • NAD+ (weight: 1)         │  │
│                                   │    │  │   • NADH (weight: 1)         │  │
│                                   │    │  │   • Water (weight: 2)        │  │
│                                   │    │  │                              │  │
│                                   │    │  │ P-Invariant #3: 7 places     │  │
│                                   │    │  │   • ... (more details)       │  │
│                                   │    │  └──────────────────────────────┘  │
├───────────────────────────────────┤    ├────────────────────────────────────┤
│  T-Invariants                     │    │  T-Invariants                      │
│  Found 2 invariants               │    │  Found 2 invariants                │
│  [Analyze] [Highlight] [V]        │    │  [Analyze] [Highlight] [V]         │
├───────────────────────────────────┤    ├────────────────────────────────────┤
│  Siphons                          │    │  Siphons                           │
│  Not analyzed                     │    │  Not analyzed                      │
│  [Analyze] [Highlight] [V]        │    │  [Analyze] [Highlight] [V]         │
└───────────────────────────────────┘    └────────────────────────────────────┘

       Click [V] ──────────────────────────────────────>
       <──────────────────────────────────── Click [^]
                      (Smooth slide animation)
```

---

## Key Features

### [V] Button (Collapsed State)
- **Icon:** Down arrow (`go-down-symbolic` or `pan-down-symbolic`)
- **Action:** Expands detail report below
- **Tooltip:** "Show detailed report"

### [^] Button (Expanded State)
- **Icon:** Up arrow (`go-up-symbolic` or `pan-up-symbolic`)
- **Action:** Collapses detail report
- **Tooltip:** "Hide detailed report"

### Smooth Animation
- Uses `GtkRevealer` widget
- Slide-down transition (300ms)
- Native GTK animation

### Multiple Expansion
- User can expand multiple analyzers simultaneously
- Easy to compare P-Invariants with T-Invariants
- Each expands/collapses independently

### Auto-Expand (Recommended)
- After clicking "Analyze", automatically expand detail
- Shows results immediately
- User can collapse if not interested

---

## Widget Structure (Per Analyzer)

```
GtkFrame (analyzer_frame)
  │
  └─ GtkBox (vertical)
       │
       ├─ GtkLabel (title) ──────────────── "P-Invariants (Conservation Laws)"
       │
       ├─ GtkBox (summary_box)
       │    ├─ GtkLabel ───────────────── "Found 3 invariants"
       │    └─ GtkButtonBox
       │         ├─ [Analyze]
       │         ├─ [Highlight]
       │         └─ [V] ← GtkToggleButton (NEW!)
       │
       └─ GtkRevealer (NEW!)
            │  reveal-child: False (initially)
            │  transition-type: slide-down
            │  transition-duration: 300ms
            │
            └─ GtkScrolledWindow
                 └─ GtkLabel (detail_report)
                      │ use-markup: True
                      │ selectable: True
                      │ wrap: True
                      │
                      └─ Contains formatted detailed report
```

---

## User Flow

### Step 1: Initial View
```
User opens Topology panel
  → Sees all 12 analyzers in compact form
  → All showing "Not analyzed"
  → All [V] buttons visible
```

### Step 2: Click Analyze on P-Invariants
```
User clicks [Analyze]
  → Analysis runs (same as before)
  → Summary updates: "Found 3 invariants"
  → [V] button auto-changes to [^]
  → Detail report slides down (300ms animation)
  → Shows full list of all 3 invariants with places and weights
```

### Step 3: View Details
```
User scrolls within detail report
  → Sees all invariants
  → Reads conservation equations
  → Reviews place weights
```

### Step 4: Collapse (Optional)
```
User clicks [^]
  → Detail report slides up (300ms animation)
  → Returns to compact summary view
  → [^] button changes back to [V]
```

### Step 5: Expand Another Analyzer
```
User clicks [Analyze] on T-Invariants
  → T-Invariants section expands
  → P-Invariants remains expanded (or collapsed if user closed it)
  → Both detail reports visible if both expanded
```

---

## Implementation Summary

### What Changes:

✅ **UI File** (`topology_panel.ui`)
- Add `GtkToggleButton` (expand_btn) after Highlight button
- Add `GtkRevealer` after button box
- Add `GtkScrolledWindow` + `GtkLabel` inside revealer
- 12 revealers (one per analyzer)

✅ **Loader** (`topology_panel_loader.py`)
- Collect 12 expand buttons
- Collect 12 revealers
- Collect 12 detail labels
- Pass to controller

✅ **Controller** (`topology_panel_controller.py`)
- Add `on_expand_clicked()` method
- Add `_populate_detail_report()` method
- Add 12 `_format_*_detail()` methods
- Auto-expand after successful analysis

✅ **No Changes to Base** (`topology_panel_base.py`)
- Attach/detach/float logic unchanged

---

## What We DON'T Change:

❌ Stack widget (not needed - no separate pages)
❌ Navigation between views (all on same tab)
❌ [>] / [<] buttons (using [V] / [^] instead)
❌ Detail pages (using expandable sections instead)

---

## Advantages Over Previous Design

| Aspect | Previous (Separate Pages) | New (Accordion) |
|--------|---------------------------|-----------------|
| **Navigation** | Click [>] → switch page → click [<] back | Click [V] → expand in place → click [^] collapse |
| **Context** | Lose view of other analyzers | Keep all analyzers visible |
| **Comparison** | Must switch between pages | Can expand multiple, compare side-by-side |
| **Complexity** | Stack + 12 pages + navigation | GtkRevealer (native GTK widget) |
| **Animation** | Page slide (Stack transition) | Smooth reveal (GtkRevealer) |
| **Simplicity** | More complex architecture | Simpler, more intuitive |

**Winner:** Accordion design ✅

---

## Next Steps

1. ✅ Confirm accordion design approved
2. Revert Stack changes from previous attempt
3. Update UI with GtkRevealer widgets
4. Update loader with new widget collection
5. Implement controller expand logic
6. Test with real models

**Ready to proceed?**
