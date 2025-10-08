# Pathway Editing - Quick Summary

**Research completed**: October 7, 2025

---

## 🎯 Three Main Goals Addressed

### 1. **Hierarchical Pathway Visualization**
**Show main backbone vs. secondary pathways**

- **Method**: Centrality analysis (betweenness, degree, closeness)
- **Result**: Classify nodes into 3 levels
  - Level 0: Main backbone (30% most important)
  - Level 1: Primary branches (40%)
  - Level 2: Secondary/leafs (30%)
- **Scientific basis**: Jeong et al. (2000) - Nature

### 2. **Source/Sink Abstraction**
**Hide secondary pathways, expose gradually**

- **Method**: Replace sub-pathways with source/sink transitions
- **UI Control**: Slider (0=full detail, 1=hide secondary, 2=main only)
- **Interaction**: Double-click source/sink to expand
- **Scientific basis**: Heiner et al. (2008) - Petri Nets for Biology

### 3. **Graph Auto-Layout**
**Self-organizing pathways after import/abstraction**

- **Algorithms**:
  - **Hierarchical** (Sugiyama) - for linear pathways
  - **Force-Directed** (Fruchterman-Reingold) - for complex networks
  - **Circular** - for cyclic pathways (TCA, Calvin)
  - **Orthogonal** - for circuit-like structures
- **Auto-detection**: Algorithm selection based on topology
- **Scientific basis**: Di Battista et al. (1998) - Graph Drawing

---

## 📊 Visual Examples

### Hierarchy Classification

```
Original KEGG Pathway (Glycolysis):
┌────────────────────────────────────────────┐
│ All 34 reactions shown                     │
│ Including: cofactors, side branches,       │
│            regulatory enzymes              │
└────────────────────────────────────────────┘
                    ↓
        Apply Centrality Analysis
                    ↓
┌────────────────────────────────────────────┐
│ Level 0 (Main): 10 reactions (backbone)    │
│ Level 1 (Primary): 14 reactions (branches) │
│ Level 2 (Secondary): 10 reactions (leafs)  │
└────────────────────────────────────────────┘
```

### Source/Sink Abstraction

```
Detail Level 0 (Full):
[Glucose-6P] → (G6PDH) → [6P-Gluconolactone]
                  ↓
           [NADP+] [NADPH]
              ↓       ↑
        (Cofactor recycling cycle...)
        
Detail Level 1 (Abstracted):
[Glucose-6P] → (G6PDH) → [6P-Gluconolactone]
                  ↑
         (SOURCE: "NADPH Cycle")
         
Detail Level 2 (Main only):
[Glucose-6P] → (G6PDH) → [6P-Gluconolactone]
```

### Graph Layouts

```
HIERARCHICAL (Sugiyama):
     Layer 0:    [A]    [B]
                  │      │
     Layer 1:    (T1)  (T2)
                  │ \  / │
     Layer 2:    [C] [D] [E]

FORCE-DIRECTED (Fruchterman-Reingold):
       [A]─────(T1)─────[C]
        │    /    \      │
        │  /        \    │
       [B]          [D]─[E]
       
CIRCULAR (for cycles):
           [A]
          /   \
       (T1)   (T4)
        |       |
       [B]     [D]
        |       |
       (T2)   (T3)
          \   /
           [C]
```

---

## 🔬 Scientific Foundation

### Key Papers (13 references)

1. **KEGG**: Kanehisa et al. (2000-2023) - Pathway database design
2. **Centrality**: Jeong et al. (2000) - Metabolic network organization
3. **Flux Analysis**: Schuster et al. (1999) - Elementary flux modes
4. **Petri Nets**: Heiner et al. (2008) - Biological modeling
5. **Pathway Layout**: Dogrusoz et al. (2009) - Compound graphs
6. **Hierarchical**: Sugiyama et al. (1981) - Layer assignment
7. **Force-Directed**: Fruchterman & Reingold (1991) - Physics-based
8. **Graph Drawing**: Di Battista et al. (1998) - Comprehensive reference

### Software Libraries

- **NetworkX** - Graph analysis, basic layouts
- **Graphviz** - Production-quality layouts (dot, neato, circo)
- **OGDF** - Advanced graph drawing framework

---

## 🚀 Implementation Plan

### Phase 1: Hierarchy (2-3 days) ⭐ **Start here**
- [x] Research complete
- [ ] Implement centrality calculations
- [ ] Create classification algorithm
- [ ] Add `hierarchy_level` metadata to objects
- [ ] Test with 5 pathways

### Phase 2: Abstraction (3-4 days)
- [ ] Extend source/sink with metadata
- [ ] Implement subgraph replacement
- [ ] Add detail level slider to UI
- [ ] Implement expand/collapse interaction

### Phase 3: Layout (4-5 days)
- [ ] Install NetworkX (already have)
- [ ] Implement 4 layout algorithms
- [ ] Create auto-detection logic
- [ ] Add "Re-layout" button to UI
- [ ] Create algorithm picker dialog

### Phase 4: Editing (3-4 days)
- [ ] Lock/unlock positions
- [ ] Align/distribute commands
- [ ] Straighten edges
- [ ] Manual refinement tools

### Phase 5: Documentation (2-3 days)
- [ ] User guide
- [ ] Algorithm guide
- [ ] Example pathways
- [ ] Integration testing

**Total: 14-19 days**

---

## 💡 Key Insights

### Why This Matters

1. **KEGG pathways are complex** - Glycolysis has 34 reactions, but only ~10 are "main" pathway
2. **Cofactors clutter** - ATP/NADH cycles obscure main flow
3. **Layout is essential** - KEGG coordinates don't translate well to Petri nets
4. **Abstraction enables exploration** - Start simple, drill down as needed

### Design Principles

1. **Progressive disclosure** - Show simple first, reveal complexity on demand
2. **Semantic abstraction** - Source/sink have biological meaning (external pathways)
3. **Automatic + manual** - Auto-layout for speed, manual editing for precision
4. **Preserve information** - Abstracted pathways stored in metadata, can be recovered

---

## 📚 Documentation Created

- **Main research**: `doc/KEGG/PATHWAY_EDITING_RESEARCH.md` (20+ pages)
- **This summary**: `doc/KEGG/PATHWAY_EDITING_SUMMARY.md`

---

## 🎯 Next Actions

**Immediate** (now):
1. Review research document
2. Decide which phases to implement
3. Prioritize based on user needs

**Short-term** (this week):
1. Start Phase 1 (hierarchy classification)
2. Test with real KEGG pathways
3. Validate approach with users

**Medium-term** (next 2-3 weeks):
1. Implement Phases 2-3 (abstraction + layout)
2. User testing and iteration
3. Documentation and examples

---

**Ready to start?** Phase 1 (hierarchy) is well-defined and can be implemented immediately.
