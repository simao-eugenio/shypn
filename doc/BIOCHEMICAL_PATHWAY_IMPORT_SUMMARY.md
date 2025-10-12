# Biochemical Pathway Import - Executive Summary

**Date**: October 12, 2025  
**Status**: ✅ Research Complete - Ready for Implementation

---

## QUICK ANSWERS TO YOUR QUESTIONS

### 1. ✅ Is it possible to fetch data for biochemical pathways?

**YES!** Multiple options available:

- **SBML Files** (Recommended): Standard format, widely supported
- **Open Databases**: Reactome, BioModels (free access)
- **Commercial**: KEGG (requires license for commercial use)
- **Format**: XML-based, well-documented

### 2. ✅ What kind of data can be fetched?

**Complete pathway information**:

| Data Type | Available | Quality |
|-----------|-----------|---------|
| **Metabolites/Compounds** | ✅ Always | Excellent |
| **Reaction steps** | ✅ Always | Excellent |
| **Stoichiometry** (coefficients) | ✅ Always | Excellent |
| **Kinetic parameters** (rates, Km) | ⚠️ Sometimes | Variable |
| **Enzyme names** | ✅ Usually | Good |
| **Compartments** (cytosol, etc.) | ✅ Usually | Good |
| **Initial concentrations** | ⚠️ Sometimes | Variable |

### 3. ✅ Mapping to Petri Net Elements

**PERFECT MATCH!** Your intuition is correct:

```
BIOCHEMICAL              →    PETRI NET
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Metabolites/Compounds    →    Places (Tokens)
  ├─ Concentration       →      Token count
  └─ ChEBI/KEGG ID      →      Metadata

Reactions                →    Transitions
  ├─ Enzyme             →      Name/metadata
  ├─ Kinetics (Vmax, Km)→      Rate parameters
  └─ Rate constant (k)  →      Transition rate

Stoichiometry           →    Arc Weights
  ├─ Reactant ratio     →      Input arc weight
  └─ Product ratio      →      Output arc weight

Compartments            →    Visual grouping/colors
```

### 4. ✅ Can we put this in the import pipeline?

**YES!** Clean integration path:

**Current**: `File → Open → *.shy → Canvas`

**Enhanced**: `File → Open → *.shy | *.sbml → Parser → Canvas`

---

## RECOMMENDED APPROACH

### 🚀 Quick Start (2 weeks)

**Minimal Viable Import**:
1. Install: `python-libsbml`
2. Parse SBML: Extract species, reactions, stoichiometry
3. Convert: Species→Places, Reactions→Transitions
4. Display: Use existing canvas
5. Done! Users can import pathways

### 📊 Example: Glycolysis Import

**Input**: `glycolysis.sbml` (standard SBML file)

**Automatic conversion**:
- 10 metabolites → 10 Places (Glucose, ATP, Pyruvate, etc.)
- 10 reactions → 10 Transitions (Hexokinase, PFK, PK, etc.)
- Stoichiometry → Arc weights (1 glucose + 1 ATP → ...)
- Kinetics → Transition rates (if available)

**Result**: Full glycolysis pathway ready to simulate!

---

## IMPLEMENTATION PHASES

| Phase | Goal | Duration | Deliverable |
|-------|------|----------|-------------|
| **1. Foundation** | Parse SBML | 2 weeks | Read SBML files |
| **2. Conversion** | Map to Petri nets | 2 weeks | Generate DocumentModel |
| **3. Kinetics** | Import rates | 2 weeks | Full kinetic models |
| **4. UI** | File dialog | 2 weeks | User can open SBML |
| **5. Layout** | Auto-arrange | 2 weeks | Pretty visualization |
| **6. Database** | Fetch online | 2 weeks | Download from Reactome |

**Total**: 12 weeks for complete system  
**Quick Win**: 6 weeks for basic import (Phases 1-3)

---

## KEY BENEFITS

### For Users:
✅ **Access 1000+ curated pathways** from databases  
✅ **No manual modeling** - import ready-to-simulate models  
✅ **Standard format** - compatible with other tools  
✅ **Kinetic parameters included** - realistic simulations  
✅ **Publication-ready** - use validated pathway data  

### For Development:
✅ **Standard library** - python-libsbml is mature  
✅ **Clear mapping** - pathway concepts match Petri nets naturally  
✅ **Extensible** - start simple, add features incrementally  
✅ **Open data** - free databases available (Reactome, BioModels)  

---

## EXAMPLE PATHWAYS AVAILABLE

**Glycolysis** - 10 reactions, classic pathway  
**TCA Cycle** - 8 reactions, cellular respiration  
**Pentose Phosphate** - 13 reactions, NADPH production  
**Amino Acid Synthesis** - 50+ reactions  
**Signal Transduction** - MAPK, PKA cascades  
**Complete Metabolism** - 1000+ reactions  

**Source**: BioModels Database (900+ curated models)

---

## TECHNICAL REQUIREMENTS

### Dependencies (Minimal):
```bash
pip install python-libsbml>=5.19.0
```

### Optional (Enhanced features):
```bash
pip install requests networkx matplotlib
```

### New Modules (~5 files):
```
src/shypn/data/pathway/
├── sbml_parser.py          # Parse SBML files
├── pathway_converter.py    # Convert to Petri nets
├── pathway_data.py         # Data structures
├── kinetics_mapper.py      # Map rate laws
└── __init__.py
```

---

## RISKS & MITIGATIONS

| Risk | Impact | Mitigation |
|------|--------|------------|
| Complex rate laws | Medium | Start with simple mass action |
| Large pathways | Low | Implement zoom/pan, filtering |
| Missing kinetics | Low | Use defaults, allow manual input |
| KEGG licensing | Low | Use Reactome (fully open) |
| MathML parsing | Medium | Use libsbml built-in functions |

---

## NEXT STEPS

### Option A: Full Implementation (12 weeks)
→ Complete all 6 phases
→ Professional-grade pathway import
→ Database integration

### Option B: Quick Proof of Concept (2 weeks) ⭐ **RECOMMENDED**
→ Implement Phases 1-2 only
→ Basic SBML import working
→ Validate approach, get user feedback
→ Decide on full development

### Option C: Prototype Demo (3 days)
→ Hardcode one example pathway (glycolysis)
→ Show concept without parsing
→ Test user interest before investing time

---

## DECISION TIME

**Question**: Which approach do you prefer?

**A**: Full 12-week implementation  
**B**: 2-week proof of concept (recommended)  
**C**: 3-day prototype demo  
**D**: More research needed  

**My Recommendation**: **Option B** (2-week PoC)
- Low risk, quick validation
- Proves technical feasibility
- Gets user feedback early
- Can expand if successful

---

## CONCLUSION

✅ **Technically feasible** - SBML format is perfect for this  
✅ **Data available** - 1000+ pathways in open databases  
✅ **Natural mapping** - Petri nets are ideal for biochemical networks  
✅ **Quick start possible** - Basic import in 2 weeks  
✅ **High impact** - Opens up huge use case for your application  

**Bottom Line**: This is a **killer feature** that would make your Petri net tool invaluable for systems biology and bioinformatics users! 🚀

---

**Full details**: See `BIOCHEMICAL_PATHWAY_IMPORT_RESEARCH.md`
