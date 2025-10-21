# Topology Panel Architecture - With Page Navigation Refinement

**Date:** October 20, 2025  
**Refinement:** Add detailed report pages for each analyzer

## Current Architecture (Day 1 - Implemented)

```
┌─────────────────────────────────────────────────────────────┐
│ Topology Panel (400px width)                                │
├─────────────────────────────────────────────────────────────┤
│ Header: "Topology Analysis" [Float Button]                  │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Notebook (3 Tabs)                                       │ │
│ │ ┌─────────┬──────────────────┬────────────┐            │ │
│ │ │Structural│Graph & Network   │Behavioral  │            │ │
│ │ └─────────┴──────────────────┴────────────┘            │ │
│ │                                                         │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ Scrolled Window                                     │ │ │
│ │ │ ┌─────────────────────────────────────────────────┐ │ │ │
│ │ │ │ [P-Invariants (Conservation Laws)]              │ │ │ │
│ │ │ │ Result: Not analyzed                            │ │ │ │
│ │ │ │ [Analyze] [Highlight]                           │ │ │ │
│ │ │ ├─────────────────────────────────────────────────┤ │ │ │
│ │ │ │ [T-Invariants (Reproducible Sequences)]         │ │ │ │
│ │ │ │ Result: Not analyzed                            │ │ │ │
│ │ │ │ [Analyze] [Highlight]                           │ │ │ │
│ │ │ ├─────────────────────────────────────────────────┤ │ │ │
│ │ │ │ [Siphons (Deadlock Detection)]                  │ │ │ │
│ │ │ │ Result: Not analyzed                            │ │ │ │
│ │ │ │ [Analyze] [Highlight]                           │ │ │ │
│ │ │ ├─────────────────────────────────────────────────┤ │ │ │
│ │ │ │ [Traps (Token Accumulation)]                    │ │ │ │
│ │ │ │ Result: Not analyzed                            │ │ │ │
│ │ │ │ [Analyze] [Highlight]                           │ │ │ │
│ │ │ └─────────────────────────────────────────────────┘ │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Refined Architecture (Proposed - Day 2/3)

```
┌─────────────────────────────────────────────────────────────┐
│ Topology Panel (400px width) - SUMMARY VIEW                 │
├─────────────────────────────────────────────────────────────┤
│ Header: "Topology Analysis" [Float Button]                  │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Notebook (3 Tabs)                                       │ │
│ │ ┌─────────┬──────────────────┬────────────┐            │ │
│ │ │Structural│Graph & Network   │Behavioral  │            │ │
│ │ └─────────┴──────────────────┴────────────┘            │ │
│ │                                                         │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ Scrolled Window - ANALYZER CARDS                    │ │ │
│ │ │ ┌─────────────────────────────────────────────────┐ │ │ │
│ │ │ │ [P-Invariants (Conservation Laws)]      [>]     │ │ │ │
│ │ │ │ Found 3 P-invariant(s)                    ↑     │ │ │ │
│ │ │ │   • 2 places                              │     │ │ │ │
│ │ │ │   • 3 places                         Click = │ │ │ │
│ │ │ │   • 4 places                         Opens  │ │ │ │
│ │ │ │ [Analyze] [Highlight]                Detail  │ │ │ │
│ │ │ │                                       Page   │ │ │ │
│ │ │ ├─────────────────────────────────────────────────┤ │ │ │
│ │ │ │ [T-Invariants (Reproducible Sequences)] [>] │ │ │ │
│ │ │ │ Found 2 T-invariant(s)                          │ │ │ │
│ │ │ │   • 5 transitions                               │ │ │ │
│ │ │ │   • 3 transitions                               │ │ │ │
│ │ │ │ [Analyze] [Highlight]                           │ │ │ │
│ │ │ ├─────────────────────────────────────────────────┤ │ │ │
│ │ │ │ [Siphons (Deadlock Detection)]          [>] │ │ │ │
│ │ │ │ No siphons found (good - no deadlock...)        │ │ │ │
│ │ │ │ [Analyze] [Highlight]                           │ │ │ │
│ │ │ ├─────────────────────────────────────────────────┤ │ │ │
│ │ │ │ [Traps (Token Accumulation)]            [>] │ │ │ │
│ │ │ │ Found 1 trap(s)                                 │ │ │ │
│ │ │ │   • 3 places                                    │ │ │ │
│ │ │ │ [Analyze] [Highlight]                           │ │ │ │
│ │ │ └─────────────────────────────────────────────────┘ │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘

                           ↓ Click [>] Button
                           
┌─────────────────────────────────────────────────────────────┐
│ Topology Panel (400px width) - DETAIL VIEW                  │
├─────────────────────────────────────────────────────────────┤
│ Header: [<] P-Invariants - Detailed Report  [Float Button]  │
│         ↑                                                    │
│    Back to Summary                                           │
├─────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────┐ │
│ │ Scrolled Window - DETAILED REPORT                       │ │
│ │ ┌─────────────────────────────────────────────────────┐ │ │
│ │ │ P-Invariants Analysis Report                        │ │ │
│ │ │ ═══════════════════════════════════════════════════ │ │ │
│ │ │                                                     │ │ │
│ │ │ Summary:                                            │ │ │
│ │ │ • Total P-invariants found: 3                       │ │ │
│ │ │ • Analysis time: 0.023s                             │ │ │
│ │ │ • Status: ✓ Network is conservative                │ │ │
│ │ │                                                     │ │ │
│ │ │ ───────────────────────────────────────────────────  │ │ │
│ │ │ P-Invariant #1                                      │ │ │
│ │ │ ───────────────────────────────────────────────────  │ │ │
│ │ │ Places involved:                                    │ │ │
│ │ │   • P1 (ATP) - weight: 1                            │ │ │
│ │ │   • P3 (ADP) - weight: 1                            │ │ │
│ │ │                                                     │ │ │
│ │ │ Conservation law:                                   │ │ │
│ │ │   1·M(ATP) + 1·M(ADP) = constant                    │ │ │
│ │ │                                                     │ │ │
│ │ │ Interpretation:                                     │ │ │
│ │ │   ATP/ADP pool is conserved - no net               │ │ │
│ │ │   creation or destruction                           │ │ │
│ │ │                                                     │ │ │
│ │ │ Current value: 100 tokens                           │ │ │
│ │ │ [Highlight on Canvas]                               │ │ │
│ │ │                                                     │ │ │
│ │ │ ───────────────────────────────────────────────────  │ │ │
│ │ │ P-Invariant #2                                      │ │ │
│ │ │ ───────────────────────────────────────────────────  │ │ │
│ │ │ Places involved:                                    │ │ │
│ │ │   • P2 (NAD+) - weight: 1                           │ │ │
│ │ │   • P4 (NADH) - weight: 1                           │ │ │
│ │ │   • P5 (H+) - weight: 1                             │ │ │
│ │ │                                                     │ │ │
│ │ │ Conservation law:                                   │ │ │
│ │ │   1·M(NAD+) + 1·M(NADH) + 1·M(H+) = constant        │ │ │
│ │ │                                                     │ │ │
│ │ │ ... (continues)                                     │ │ │
│ │ └─────────────────────────────────────────────────────┘ │ │
│ └─────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

## Navigation Flow Diagram

```
                    ┌─────────────────────┐
                    │  TOPOLOGY PANEL     │
                    │  (Summary View)     │
                    └──────────┬──────────┘
                               │
         ┌─────────────────────┼─────────────────────┐
         │                     │                     │
         ▼                     ▼                     ▼
  ┌────────────┐      ┌────────────┐       ┌────────────┐
  │ Structural │      │  Graph &   │       │ Behavioral │
  │    Tab     │      │  Network   │       │    Tab     │
  │            │      │    Tab     │       │            │
  │ 4 Cards    │      │ 3 Cards    │       │ 5 Cards    │
  └────┬───────┘      └─────┬──────┘       └─────┬──────┘
       │                    │                    │
       │ Click [>]          │ Click [>]          │ Click [>]
       ▼                    ▼                    ▼
  ┌────────────┐      ┌────────────┐       ┌────────────┐
  │P-Invariants│      │  Cycles    │       │Reachability│
  │Detail Page │      │Detail Page │       │Detail Page │
  │            │      │            │       │            │
  │[<] Back    │      │[<] Back    │       │[<] Back    │
  └────────────┘      └────────────┘       └────────────┘
       │                    │                    │
       │ Click [<]          │ Click [<]          │ Click [<]
       └─────────────────────┴────────────────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │  Back to Summary    │
                    │  (Same tab active)  │
                    └─────────────────────┘
```

## UI Component Hierarchy

```
TopologyPanel
├── Header (with float button)
├── Stack (for view switching)
│   ├── summary_page (default)
│   │   └── Notebook (3 tabs)
│   │       ├── structural_tab
│   │       │   └── ScrolledWindow
│   │       │       └── Box (vertical)
│   │       │           ├── AnalyzerCard (P-Invariants) [>] button
│   │       │           ├── AnalyzerCard (T-Invariants) [>] button
│   │       │           ├── AnalyzerCard (Siphons) [>] button
│   │       │           └── AnalyzerCard (Traps) [>] button
│   │       ├── graph_network_tab
│   │       │   └── ScrolledWindow
│   │       │       └── Box (vertical)
│   │       │           ├── AnalyzerCard (Cycles) [>] button
│   │       │           ├── AnalyzerCard (Paths) [>] button
│   │       │           └── AnalyzerCard (Hubs) [>] button
│   │       └── behavioral_tab
│   │           └── ScrolledWindow
│   │               └── Box (vertical)
│   │                   ├── AnalyzerCard (Reachability) [>] button
│   │                   ├── AnalyzerCard (Boundedness) [>] button
│   │                   ├── AnalyzerCard (Liveness) [>] button
│   │                   ├── AnalyzerCard (Deadlocks) [>] button
│   │                   └── AnalyzerCard (Fairness) [>] button
│   └── detail_pages (12 pages)
│       ├── p_invariants_page ([<] button → summary)
│       ├── t_invariants_page ([<] button → summary)
│       ├── siphons_page ([<] button → summary)
│       ├── traps_page ([<] button → summary)
│       ├── cycles_page ([<] button → summary)
│       ├── paths_page ([<] button → summary)
│       ├── hubs_page ([<] button → summary)
│       ├── reachability_page ([<] button → summary)
│       ├── boundedness_page ([<] button → summary)
│       ├── liveness_page ([<] button → summary)
│       ├── deadlocks_page ([<] button → summary)
│       └── fairness_page ([<] button → summary)
└── Footer (status/export buttons)
```

## Analyzer Card Component

```
┌───────────────────────────────────────────────────────────┐
│ [Bold Title: "P-Invariants (Conservation Laws)"]    [>]  │
│ ────────────────────────────────────────────────────────  │
│ Quick Summary (1-3 lines):                               │
│ • Found 3 P-invariant(s)                                  │
│ • 2 places, 3 places, 4 places                            │
│ • Status: ✓ Network is conservative                      │
│ ────────────────────────────────────────────────────────  │
│ [Analyze Button] [Highlight Button]                       │
└───────────────────────────────────────────────────────────┘
         ↑                                  ↑
    Summary only                      Opens detail page
    (2-3 lines max)                   with full report
```

## Detail Page Component

```
┌───────────────────────────────────────────────────────────┐
│ [<] P-Invariants - Detailed Analysis Report              │
│  ↑                                                        │
│ Back to summary                                           │
├───────────────────────────────────────────────────────────┤
│ Scrolled Window (full report)                             │
│                                                           │
│ ╔═══════════════════════════════════════════════════════╗ │
│ ║ HEADER SECTION                                        ║ │
│ ╚═══════════════════════════════════════════════════════╝ │
│ • Analyzer name and description                           │
│ • Analysis timestamp                                      │
│ • Analysis time                                           │
│ • Overall status/summary                                  │
│                                                           │
│ ───────────────────────────────────────────────────────── │
│ RESULTS SECTION                                           │
│ ───────────────────────────────────────────────────────── │
│                                                           │
│ For each result item:                                     │
│   • Detailed information                                  │
│   • Mathematical representation                           │
│   • Biological interpretation                             │
│   • Related elements (places/transitions)                 │
│   • Individual highlight button                           │
│                                                           │
│ ───────────────────────────────────────────────────────── │
│ ACTIONS                                                   │
│ ───────────────────────────────────────────────────────── │
│ [Export to CSV] [Export to PDF] [Highlight All]           │
└───────────────────────────────────────────────────────────┘
```

## Data Flow

```
User Action Flow:
─────────────────

1. User clicks "Analyze" on summary card
   └─> Controller creates analyzer with current model
       └─> Analyzer runs analysis
           └─> Result stored in cache
               └─> Summary updated on card
                   └─> [>] button enabled

2. User clicks [>] button
   └─> Stack switches to detail page
       └─> Header updates with [<] back button
           └─> Detail page populated from cached result
               └─> Full report rendered

3. User clicks [<] back button
   └─> Stack switches to summary page
       └─> Returns to same tab that was active
           └─> Summary card still shows cached result

4. User clicks "Highlight" on detail page
   └─> Controller passes result to HighlightingManager
       └─> Canvas highlights relevant elements
```

## Implementation Layers

```
Layer 1: UI (XML)
─────────────────
ui/panels/topology_panel.ui
├── Stack widget (summary vs detail view switcher)
├── Summary page (3 tabs with analyzer cards)
└── Detail pages (12 pages, one per analyzer)

Layer 2: Base Class (Wayland-safe operations)
─────────────────────────────────────────────
src/shypn/ui/topology_panel_base.py
├── attach_to() - Wayland-safe docking
├── float() - Wayland-safe floating
├── Stack navigation methods
└── Widget lifecycle management

Layer 3: Controller (Business logic)
────────────────────────────────────
src/shypn/ui/topology_panel_controller.py
├── on_analyze_clicked() - Run analysis
├── on_detail_clicked() - Show detail page (NEW)
├── on_back_clicked() - Return to summary (NEW)
├── on_highlight_clicked() - Highlight on canvas
├── _format_summary() - Format card summary
└── _format_detail() - Format full report (NEW)

Layer 4: Loader (Minimal wrapper)
─────────────────────────────────
src/shypn/helpers/topology_panel_loader.py
├── Load UI
├── Get widget references
├── Create controller
└── Connect signals
```

## Summary

### Current (Day 1)
- ✅ Single view with 3 tabs
- ✅ Analyzer cards with summary (1-3 lines)
- ✅ Analyze and Highlight buttons

### Refinement (Day 2/3)
- 🔄 Add Stack widget for view switching
- 🔄 Add [>] button to each analyzer card
- 🔄 Add 12 detail pages (one per analyzer)
- 🔄 Add [<] back button in detail page header
- 🔄 Populate detail pages with full reports
- 🔄 Navigation between summary and detail views

### Benefits
- 📊 **Quick overview** in summary cards
- 📄 **Full details** in dedicated pages
- 🔍 **Better readability** (no scrolling through 12 long reports)
- 🎯 **Focused analysis** (one analyzer at a time)
- 💾 **Export options** per analyzer (CSV, PDF)
- 🎨 **Individual highlighting** from detail page

### Architecture Principle
**Two-level navigation:**
1. **Summary level** - See all 12 analyzers at once (cards)
2. **Detail level** - Deep dive into one analyzer (full report)

This follows the **progressive disclosure** UX pattern! 🎯
