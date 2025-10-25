# Phase 5: UI Design Summary - Visual Reference

**Quick Reference for Implementation**

---

## The Pattern: Expander + TreeView

SHYpn uses **CategoryFrame expanders** with **TreeView widgets** inside:

```
┌─────────────────────────────────────────────────┐
│ ▼ CATEGORY TITLE             [Btn1] [Btn2]      │ ← CategoryFrame header
├─────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────┐ │
│ │ Column 1    │ Column 2  │ Column 3         │ │ ← TreeView headers
│ ├─────────────┼───────────┼──────────────────┤ │
│ │ Value 1     │ Value 2   │ Value 3          │ │
│ │ Value 4     │ Value 5   │ Value 6          │ │ ← TreeView rows
│ │ Value 7     │ Value 8   │ Value 9          │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
└─────────────────────────────────────────────────┘
```

---

## What We're Adding

### New Category 1: PATHWAYS

```
┌─────────────────────────────────────────────────────────────────────────┐
│ ▼ PATHWAYS                                          [↻ Refresh] [+ Import] │
├─────────────────────────────────────────────────────────────────────────┤
│ ┌─────────────────────────────────────────────────────────────────────┐ │
│ │   │ Name        │ Source │ Organism     │ Status       │ Enrich │ Date │ │
│ ├─┼─────────────┼────────┼──────────────┼──────────────┼────────┼──────┤ │
│ │🗺️│ Glycolysis   │ KEGG   │ H. sapiens   │ ✅ Converted  │   1    │ Oct25│ │
│ │🧬│ E.coli Gly.. │ SBML   │ E. coli      │ ✅ Converted  │   0    │ Oct24│ │
│ │🗺️│ TCA Cycle    │ KEGG   │ H. sapiens   │ ⚠️ Not conv.. │   0    │ Oct23│ │
│ └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
  Right-click row:
  ┌─────────────────────────┐
  │ View Source File        │
  │ Re-convert to Model     │
  ├─────────────────────────┤
  │ Add BRENDA Enrichment   │
  │ Add SABIO-RK Enrichment │
  ├─────────────────────────┤
  │ Export Metadata (JSON)  │
  │ Copy Pathway ID         │
  ├─────────────────────────┤
  │ Remove from Project     │
  └─────────────────────────┘
```

**What it shows:**
- All imported pathways (KEGG, SBML, BioModels)
- Which ones were converted to models
- How many enrichments each has
- When they were imported

### New Category 2: ENRICHMENTS

```
┌──────────────────────────────────────────────────────────────────────────┐
│ ▼ ENRICHMENTS                                   [↻ Refresh] [🗑️ Clear All] │
├──────────────────────────────────────────────────────────────────────────┤
│ ┌────────────────────────────────────────────────────────────────────┐   │
│ │   │ Date      │ Source    │ Pathway   │Trans│Parameters│Confidence│   │
│ ├─┼───────────┼───────────┼───────────┼─────┼──────────┼──────────┤   │
│ │⚡│Oct25 14:30│BRENDA API │Glycolysis │  8  │16(Km/Kc) │High ⭐    │   │
│ │⚡│Oct24 09:15│BRENDA Loc.│TCA Cycle  │  5  │10(Ki)    │Medium    │   │
│ │🔬│Oct23 16:45│SABIO-RK   │Glycolysis │  3  │6(Vmax)   │High ⭐    │   │
│ └────────────────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────────────────────────┘
  Right-click row:
  ┌───────────────────────┐
  │ View Details          │
  │ View BRENDA Data File │
  ├───────────────────────┤
  │ Re-apply Enrichment   │
  ├───────────────────────┤
  │ Export Metadata (JSON)│
  │ Copy Enrichment ID    │
  ├───────────────────────┤
  │ Remove Enrichment     │
  └───────────────────────┘
```

**What it shows:**
- All enrichments applied to any pathway
- When they were applied
- How many transitions were enriched
- What parameters were added
- Confidence level

### Enhanced Category: PROJECT INFORMATION

```
┌─────────────────────────────────────┐
│ ▶ PROJECT INFORMATION               │ ← Click to expand
├─────────────────────────────────────┤
│ Project:      MyProject             │
│ Path:         /workspace/proj...    │
│ Models:       3                     │
│ Pathways:     2  ← NEW              │
│ Enrichments:  1  ← NEW              │
│ Last Modified: Oct 25, 2025         │
└─────────────────────────────────────┘
```

**What changed:**
- Added "Pathways" count
- Added "Enrichments" count
- Updates automatically when data changes

---

## The Complete File Panel Layout

```
┌──────────────────────── EXPLORER ────────────────────────────────────┐
│                                                   [Float/Attach]      │
│                                                                       │
│ ▼ FILES                                    [+ File][+ Folder][⌂]     │
│ ├─ Path: /workspace/projects/MyProject/models                       │
│ └─ 📁 folder1/                                                       │
│    📁 folder2/                                                       │
│    📄 model1.shy                                                     │
│    📄 model2.shy                                                     │
│                                                                       │
│ ▼ PATHWAYS                                  [↻ Refresh][+ Import]   │
│ └─ Glycolysis    KEGG   H. sapiens  ✅ Converted   1   Oct25        │
│    E.coli Gly    SBML   E. coli     ✅ Converted   0   Oct24        │
│    TCA Cycle     KEGG   H. sapiens  ⚠️ Not conv.   0   Oct23        │
│                                                                       │
│ ▶ ENRICHMENTS                               [↻ Refresh][🗑️ Clear]   │
│                                                                       │
│ ▶ PROJECT INFORMATION                                                │
│                                                                       │
│ ▶ PROJECT ACTIONS                                                    │
│                                                                       │
└───────────────────────────────────────────────────────────────────────┘

Behavior:
• Only ONE category expanded at a time
• Click header → expands and collapses others
• TreeViews are scrollable
• Right-click rows for context menus
• Inline buttons in headers for quick actions
```

---

## Code Structure

```
Implementation Files:

src/shypn/helpers/
├── pathways_view_controller.py      ← NEW: PATHWAYS category logic
├── enrichments_view_controller.py   ← NEW: ENRICHMENTS category logic
├── project_info_controller.py       ← NEW: PROJECT INFO enhancements
└── file_panel_loader.py             ← MODIFY: Add new categories

Integration:
├── kegg_import_panel.py             ← ADD: Trigger refresh on import
├── sbml_import_panel.py             ← ADD: Trigger refresh on import
└── brenda_enrichment_controller.py  ← ADD: Trigger refresh on enrichment
```

---

## Implementation Checklist

### PATHWAYS Category

- [ ] Create `pathways_view_controller.py`
- [ ] Build TreeView with 8 columns
- [ ] Populate from `project.pathways.list_pathways()`
- [ ] Add icon column with source icons
- [ ] Format status with colors (green/amber)
- [ ] Build context menu with 8 actions
- [ ] Wire "View Source File" action
- [ ] Wire "Re-convert to Model" action
- [ ] Wire "Add Enrichment" action
- [ ] Wire "Export Metadata" action
- [ ] Wire "Remove from Project" action
- [ ] Add inline buttons (Refresh, Import)
- [ ] Connect to KEGG import panel
- [ ] Connect to SBML import panel
- [ ] Add to `file_panel_loader.py`

### ENRICHMENTS Category

- [ ] Create `enrichments_view_controller.py`
- [ ] Build TreeView with 9 columns
- [ ] Populate from pathway enrichments
- [ ] Add icon column with source icons
- [ ] Format confidence with stars
- [ ] Build context menu with 7 actions
- [ ] Wire "View Details" action
- [ ] Wire "View Data File" action
- [ ] Wire "Re-apply Enrichment" action
- [ ] Wire "Remove Enrichment" action
- [ ] Add inline buttons (Refresh, Clear All)
- [ ] Connect to BRENDA controller
- [ ] Add to `file_panel_loader.py`

### PROJECT INFORMATION Enhancement

- [ ] Create `project_info_controller.py`
- [ ] Build label grid
- [ ] Add "Pathways" count
- [ ] Add "Enrichments" count
- [ ] Wire auto-refresh on project changes
- [ ] Update `file_panel_loader.py`

### Integration & Testing

- [ ] Trigger refresh from KEGG import
- [ ] Trigger refresh from SBML import
- [ ] Trigger refresh from BRENDA enrichment
- [ ] File system observer integration
- [ ] Manual UI testing
- [ ] Integration testing
- [ ] Performance testing (large datasets)
- [ ] Documentation update

---

## Expected Outcome

**Before Phase 5:**
```
User imports pathway → Data saved to project
But: No way to see it except opening .project.shy file
```

**After Phase 5:**
```
User imports pathway → Data saved to project
AND: Immediately visible in PATHWAYS category
AND: Can right-click to re-convert, add enrichments, etc.
AND: PROJECT INFORMATION shows pathway count
```

**When enrichment applied:**
```
User enriches model → EnrichmentDocument created
AND: PATHWAYS view shows enrichment count
AND: ENRICHMENTS view shows new row with details
AND: Can view details, re-apply, or remove
AND: Full provenance tracking visible in UI
```

---

## Time Estimates

| Task | Days |
|------|------|
| PATHWAYS Category | 2-3 |
| ENRICHMENTS Category | 1-2 |
| PROJECT INFO Enhancement | 0.5 |
| Integration & Polish | 1 |
| **Total** | **4-6** |

---

**Summary:**
- ✅ Design follows established SHYpn patterns
- ✅ Uses familiar CategoryFrame + TreeView
- ✅ Context menus for all actions
- ✅ Inline buttons for quick operations
- ✅ Exclusive expansion behavior
- ✅ Full integration with import/enrichment workflows
- ✅ Clear visual feedback to users
- ✅ Complete provenance tracking visibility

**Ready to implement!** 🚀
