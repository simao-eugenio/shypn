# Dual Editing Modes - Quick Comparison

**Two distinct editing contexts in SHYPN**

---

## 📊 Side-by-Side Comparison

```
┌─────────────────────────────────────┬─────────────────────────────────────┐
│   CREATE MODE (Interactive)         │   PATHWAY EDIT MODE (Imported)      │
├─────────────────────────────────────┼─────────────────────────────────────┤
│                                     │                                     │
│ Purpose: Build from scratch         │ Purpose: Refine imported pathways   │
│                                     │                                     │
│ Visual Style:                       │ Visual Style:                       │
│  • Uniform colors (defaults)        │  • Hierarchy colors (3 levels)      │
│  • No overlays                      │  • Visual guidance overlays         │
│  • Standard Petri net look          │  • Bounding boxes, arrows, labels   │
│                                     │                                     │
│ Operations:                         │ Operations:                         │
│  • Add place/transition             │  • Hide/show hierarchy levels       │
│  • Connect arcs                     │  • Abstract to source/sink          │
│  • Set properties                   │  • Expand abstractions              │
│  • Move, resize, delete             │  • Auto-layout pathway              │
│  • Undo/redo                        │  • Compute/re-compute hierarchy     │
│                                     │  • (Plus all create mode ops)       │
│                                     │                                     │
│ UI Controls:                        │ UI Controls:                        │
│  • Left palette (add objects)       │  • Right panel (edit pathway)       │
│  • Properties dialogs               │  • Visibility checkboxes            │
│  • Context menus                    │  • Visual mode radio buttons        │
│  • Transformation handles           │  • Overlay toggles                  │
│                                     │  • Action buttons                   │
│                                     │                                     │
│ Keyboard Shortcuts:                 │ Keyboard Shortcuts:                 │
│  • Ctrl+Z/Y (undo/redo)             │  • H (highlight mode)               │
│  • Del (delete)                     │  • G (ghost mode)                   │
│  • Ctrl+A (select all)              │  • M (heatmap mode)                 │
│  • Ctrl+C/V (copy/paste)            │  • F (focus mode)                   │
│                                     │  • 0/1/2 (show level)               │
│                                     │  • (Plus all create shortcuts)      │
│                                     │                                     │
│ Data Source:                        │ Data Source:                        │
│  • User-created                     │  • KEGG import                      │
│  • Loaded .shy files                │  • Manual hierarchy computation     │
│  • Empty canvas                     │  • Enriched with metadata           │
│                                     │                                     │
│ Metadata:                           │ Metadata:                           │
│  • Basic properties only            │  • hierarchy_level (0, 1, 2)        │
│  • User-defined labels              │  • centrality_score (float)         │
│  • Transition types                 │  • kegg_id (for imported)           │
│  • Guard/rate functions             │  • abstracted_pathway (for S/S)     │
│                                     │  • (Plus all basic metadata)        │
│                                     │                                     │
└─────────────────────────────────────┴─────────────────────────────────────┘
```

---

## 🎨 Visual Examples

### CREATE MODE - Clean, Uniform Appearance

```
Standard Petri Net:

  ┌────────┐
  │  [P1]  │ ← Default color (white/light gray)
  └───┬────┘
      │ ← Standard arc (black, 1px)
      ↓
  ┌────────┐
  │  (T1)  │ ← Default color (white/light gray)
  └───┬────┘
      │
      ↓
  ┌────────┐
  │  [P2]  │
  └────────┘

No overlay, no guidance, no hierarchy information.
Simple, clean, user is in full control.
```

### PATHWAY EDIT MODE - Hierarchy-Colored with Overlays

```
KEGG Pathway (Glycolysis):

  ┌─────────── Main Backbone (Level 0) ──────────┐ ← Overlay label
  │                                               │
  │  ┌────────┐                                   │ ← Bounding box
  │  │  [G6P] │ ← Dark blue (high importance)    │   (semi-transparent)
  │  └───┬────┘                                   │
  │      │ ← Thick arc (3px, dark gray)          │
  │      ↓                                        │
  │  ┌────────┐                                   │
  │  │  (PGI) │ ← Dark green (enzyme)            │
  │  └───┬────┘                                   │
  │      │                                        │
  └──────┼────────────────────────────────────────┘
         │
         ↓     ↙ Orange flow arrow (overlay)
  ┌─────────── Primary Branch (Level 1) ─────────┐
  │                                               │
  │  ┌────────┐                                   │
  │  │ [F6P]  │ ← Medium blue                    │
  │  └───┬────┘                                   │
  │      │ ← Medium arc (2px)                    │
  │      ↓                                        │
  │  ┌────────┐                                   │
  │  │ (PFK)  │ ← Medium green                   │
  │  └────────┘                                   │
  │                                               │
  └───────────────────────────────────────────────┘

[Secondary paths hidden - replaced with SOURCE/SINK]

[Minimap in corner] ← Small overview of full pathway
```

---

## 🔄 Mode Switching Behavior

### When to Use Each Mode

```
┌─────────────────────────────────────────────────────────┐
│  Decision Tree: Which Mode?                             │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  Are you working with an imported KEGG pathway?         │
│  ├─ YES → Use PATHWAY EDIT MODE                         │
│  │         • Get hierarchy colors automatically          │
│  │         • Use visual guidance overlays                │
│  │         • Hide/show levels as needed                  │
│  │                                                        │
│  └─ NO → Are you building from scratch?                 │
│      ├─ YES → Use CREATE MODE                            │
│      │         • Clean canvas, no distractions           │
│      │         • Full control over structure             │
│      │                                                    │
│      └─ Is it a manually created complex network?       │
│          ├─ YES → You can switch to PATHWAY EDIT MODE   │
│          │         • App will compute hierarchy          │
│          │         • Get colors and guidance             │
│          │                                                │
│          └─ NO → Stay in CREATE MODE                    │
│                   • Simple nets don't need hierarchy     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Automatic Mode Detection

The app can **suggest** the appropriate mode:

```python
def suggest_editing_mode(manager):
    """
    Suggest best editing mode based on document characteristics.
    """
    # Check if document has KEGG metadata
    has_kegg_import = any(
        'kegg_id' in obj.metadata
        for obj in manager.places + manager.transitions
    )
    
    if has_kegg_import:
        return 'pathway_edit', "This is an imported KEGG pathway"
    
    # Check if document has hierarchy metadata
    has_hierarchy = any(
        'hierarchy_level' in obj.metadata
        for obj in manager.places + manager.transitions
    )
    
    if has_hierarchy:
        return 'pathway_edit', "This document has pathway hierarchy"
    
    # Check complexity (many nodes → might benefit from hierarchy)
    node_count = len(manager.places) + len(manager.transitions)
    
    if node_count > 20:
        return 'pathway_edit', f"Large network ({node_count} nodes) might benefit from hierarchy visualization"
    
    # Default: create mode
    return 'create', "Simple network, create mode recommended"
```

---

## 🎯 Key Design Principles

### 1. **Mode Separation is Clear**
- Different toolbar button state
- Different panel shown (left palette vs. right edit panel)
- Different visual appearance (uniform vs. colored)
- Different status bar text

### 2. **Non-Destructive Switching**
- Switching modes doesn't modify the document
- Colors are temporary visual aids (not saved)
- Can switch back and forth freely
- Original data preserved

### 3. **Progressive Enhancement**
- CREATE mode: Simple, no frills
- PATHWAY EDIT mode: Enhanced visualization
- User chooses complexity level

### 4. **Context-Aware Defaults**
- Imported KEGG → Auto-switch to pathway edit mode
- New document → Start in create mode
- Loaded .shy file → Check for hierarchy metadata

---

## 🛠️ Implementation Strategy

### Phase 1: Foundation (START HERE) ✅
**Goal**: Get mode switching working

```
1. Create EditingModeManager class
2. Add mode toggle to toolbar
3. Implement basic switching logic
4. Test: modes don't interfere with each other
```

**Result**: User can toggle between modes, nothing breaks.

---

### Phase 2: Visual Differentiation
**Goal**: Make modes look different

```
1. Apply hierarchy colors in pathway edit mode
2. Reset to default colors in create mode
3. Test: colors update on mode switch
```

**Result**: Clear visual distinction between modes.

---

### Phase 3: Mode-Specific Features
**Goal**: Add pathway edit panel and overlays

```
1. Create pathway edit panel UI
2. Add overlay rendering
3. Implement visibility controls
4. Test: features only available in correct mode
```

**Result**: Each mode has its own features.

---

### Phase 4: Polish & Integration
**Goal**: Seamless user experience

```
1. Add keyboard shortcuts
2. Add mode suggestions
3. Add tooltips and help text
4. Test: user can discover and use both modes
```

**Result**: Production-ready dual mode system.

---

## 📚 Documentation Checklist

- [ ] User guide: "When to use each mode"
- [ ] Tutorial: "Switching between modes"
- [ ] Reference: "Pathway edit mode features"
- [ ] Video: "Importing and editing KEGG pathways"
- [ ] FAQ: "Why do I see colored nodes?"

---

## 🚀 Next Steps

**Immediate Actions**:
1. Review this plan
2. Decide if approach is correct
3. Prioritize phases

**Start Implementation**:
- Phase 1 (Foundation) - 2 days
- Can demo mode switching immediately
- Low risk, high value

**Future Enhancements**:
- Custom color schemes (user preferences)
- Save/load visual mode settings
- Export pathway with hierarchy colors
- 3D visualization mode (future)

---

**Questions?** Ask before starting implementation! 🎨
