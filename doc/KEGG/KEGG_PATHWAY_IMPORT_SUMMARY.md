# KEGG Pathway Import - Executive Summary

**Date**: October 7, 2025  
**Feature**: Import biochemical pathways from KEGG database as Petri nets  
**Status**: 📋 Analysis Complete - Ready for Implementation

## What This Feature Does

Allows users to import real-world biochemical pathways from the KEGG database and automatically convert them into Petri net models in shypn. This enables:

- **Systems biology modeling** using established pathway data
- **Educational use** with well-documented metabolic pathways
- **Research applications** with standardized pathway representations
- **Rapid model creation** without manual drawing

## How It Works

### User Workflow
1. User clicks **File → Import → KEGG Pathway**
2. Enters pathway ID (e.g., `hsa00010` for human glycolysis)
3. Selects import options (cofactors, initial marking, etc.)
4. Clicks **Import**
5. Pathway appears on canvas as Petri net

### Technical Workflow
1. **Fetch** KGML XML from KEGG API (`https://rest.kegg.jp/get/hsa00010/kgml`)
2. **Parse** XML to extract compounds, reactions, coordinates
3. **Convert** to Petri net:
   - Compounds → Places (e.g., "Glucose", "ATP")
   - Reactions → Transitions (e.g., "Hexokinase")
   - Substrate/Product → Arcs (with stoichiometry)
4. **Create** DocumentModel with all objects
5. **Display** on canvas

## Biochemical → Petri Net Mapping

| KEGG Element | Petri Net Element | Example |
|--------------|-------------------|---------|
| Compound (metabolite) | **Place** | Glucose, ATP, Pyruvate |
| Enzyme/Reaction | **Transition** | Hexokinase (EC:2.7.1.1) |
| Substrate | **Input Arc** | Glucose → [Hexokinase] |
| Product | **Output Arc** | [Hexokinase] → Glucose-6-P |
| Stoichiometry | **Arc Weight** | 2 ATP → [Reaction] |
| Reversible reaction | **Bidirectional** | A ⇌ B |

## Example: Glycolysis Import

**KEGG Pathway**: `hsa00010` (Glycolysis / Gluconeogenesis)

**Input**: KGML XML with:
- 66 compounds (Glucose, ATP, Pyruvate, etc.)
- 54 reactions (Hexokinase, Phosphofructokinase, etc.)
- Coordinates for layout

**Output**: Petri net with:
- ~66 Places (compounds)
- ~54 Transitions (enzymatic steps)
- ~200 Arcs (substrate/product relationships)
- Proper spatial layout based on KEGG coordinates

## Implementation Plan

### Phase 1: Core Infrastructure (2 days)
- API client to fetch KGML from KEGG
- XML parser to extract pathway data
- Data models for pathway elements

### Phase 2: Conversion Engine (2 days)
- Convert compounds to places
- Convert reactions to transitions
- Create arcs with stoichiometry
- Handle coordinate scaling

### Phase 3: Import Dialog UI (2 days)
- GTK dialog for pathway ID input
- Options panel (cofactors, marking, etc.)
- Academic use confirmation
- Error handling

### Phase 4: Advanced Features (2 days)
- Regulatory relations (activation/inhibition)
- Cofactor filtering
- Layout optimization
- Caching system

### Phase 5: Testing & Documentation (2 days)
- Test with multiple pathways
- User documentation
- Developer API docs

**Total Estimate**: 10 working days (2 weeks)

## Key Design Decisions

### ✅ Chosen Approaches

1. **Mapping Strategy**: Compounds→Places, Reactions→Transitions
   - Standard in systems biology literature
   - Intuitive for biologists

2. **Coordinate Handling**: Scale KEGG coordinates by 2.5x
   - Prevents overlap
   - Maintains relative positions

3. **Reversible Reactions**: Single transition with bidirectional arcs
   - Simpler than two transitions
   - More compact

4. **Technology**: `xml.etree.ElementTree` for parsing
   - Built-in to Python
   - Sufficient for KGML complexity

### ⚠️ Challenges to Address

1. **Graph Complexity**: Large pathways (100+ nodes) may be cluttered
   - **Solution**: Auto-layout optimization, filtering options

2. **Cofactors**: ATP/NAD+ appear in many reactions
   - **Solution**: Make cofactor inclusion optional

3. **Kinetic Information**: KEGG lacks rate constants
   - **Solution**: Preserve metadata for future enhancement

4. **API Limitations**: Academic use only, possible rate limits
   - **Solution**: Caching, usage warnings

## Dependencies

### New Requirements
```python
# May need to add to requirements.txt
requests>=2.31.0  # For HTTP requests to KEGG API
```

### Existing Dependencies (Already Available)
- `xml.etree.ElementTree` - XML parsing
- `GTK 3` - Dialog UI
- `dataclasses` - Data models

## File Structure

```
src/shypn/import/
├── __init__.py
├── kegg/
│   ├── __init__.py
│   ├── api_client.py          # Fetch KGML from KEGG
│   ├── kgml_parser.py         # Parse XML
│   ├── pathway_converter.py   # KGML → Petri net
│   ├── mapping_rules.py       # Mapping logic
│   └── models.py              # Data classes
└── dialogs/
    ├── __init__.py
    └── kegg_import_dialog.py  # Import UI

doc/
├── KEGG_PATHWAY_IMPORT_ANALYSIS.md  # ✅ Complete
├── KEGG_PATHWAY_IMPORT_PLAN.md      # ✅ Complete
└── KEGG_IMPORT_USER_GUIDE.md        # TODO
```

**New Code**: ~1500 lines

## Academic Use Compliance

⚠️ **Important Legal Notice**:

The KEGG API is provided for **academic use only**. Implementation MUST include:

1. **License Notice** in import dialog
2. **User Confirmation** of academic use
3. **Attribution** to KEGG in exported models
4. **Usage Guidelines** in documentation
5. **No Bulk Downloading** (respect API limits)

## Success Criteria

### Minimum Viable Product (MVP)
- ✅ Import human glycolysis pathway (hsa00010)
- ✅ Compounds correctly mapped to places
- ✅ Reactions correctly mapped to transitions
- ✅ Arcs have correct directionality
- ✅ UI dialog is functional
- ✅ Academic use warning displayed

### Complete Feature
- ⬜ Multiple pathway types (map, ko, ec, organism-specific)
- ⬜ Regulatory relations preserved
- ⬜ Cofactor filtering options
- ⬜ Coordinate optimization
- ⬜ Comprehensive documentation
- ⬜ Testing with 5+ pathways

## Example Pathways for Testing

| ID | Name | Type | Complexity | Notes |
|----|------|------|------------|-------|
| `hsa00010` | Glycolysis | Linear | Medium | Good first test |
| `hsa00020` | TCA Cycle | Circular | Medium | Tests cycles |
| `hsa00030` | Pentose Phosphate | Branching | Medium | Tests branching |
| `map00010` | Glycolysis (reference) | Linear | Medium | Organism-independent |
| `hsa04010` | MAPK Signaling | Network | High | Tests regulation |

## Benefits

### For Researchers
- Quick model creation from established data
- Standardized pathways for comparison
- Focus on analysis, not drawing

### For Educators
- Real-world examples for teaching
- Well-documented pathways
- Visual learning tool

### For shypn Project
- Expands use cases beyond toy models
- Connects to systems biology community
- Demonstrates practical applications

## Next Steps

**Immediate Action**: Begin Phase 1 implementation

1. Check if `requests` library is available
2. Create `src/shypn/import/kegg/` directory structure
3. Implement `api_client.py` with `fetch_kgml()` function
4. Test fetching glycolysis pathway
5. Examine KGML structure in detail

**Questions to Answer**:
- Do we need to add `requests` to requirements?
- What's the shypn coordinate system origin?
- Should initial marking be 0 or 1 for compounds?

---

**Documentation Files Created**:
1. ✅ `KEGG_PATHWAY_IMPORT_ANALYSIS.md` - Detailed technical analysis
2. ✅ `KEGG_PATHWAY_IMPORT_PLAN.md` - Implementation roadmap
3. ✅ `KEGG_PATHWAY_IMPORT_SUMMARY.md` - This executive summary (YOU ARE HERE)

**Ready to implement?** Let me know and we can start with Phase 1!
