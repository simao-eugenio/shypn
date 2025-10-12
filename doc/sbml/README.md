# SBML/Pathway Import Documentation

**Last Updated**: October 12, 2025  
**Status**: Design Complete ✅ | Implementation In Progress 🚧

This directory contains all documentation related to importing biochemical pathways from SBML (Systems Biology Markup Language) files into ShyPN as Petri nets.

---

## 📚 Documentation Index

### 1. Research & Design

| Document | Description | Lines | Status |
|----------|-------------|-------|--------|
| [**BIOCHEMICAL_PATHWAY_IMPORT_RESEARCH.md**](./BIOCHEMICAL_PATHWAY_IMPORT_RESEARCH.md) | Complete research on databases, formats, and mapping strategy | 925 | ✅ Complete |
| [**BIOCHEMICAL_PATHWAY_IMPORT_SUMMARY.md**](./BIOCHEMICAL_PATHWAY_IMPORT_SUMMARY.md) | Executive summary answering key feasibility questions | ~200 | ✅ Complete |

### 2. Architecture & Implementation

| Document | Description | Lines | Status |
|----------|-------------|-------|--------|
| [**BIOCHEMICAL_PATHWAY_IMPORT_REVISED.md**](./BIOCHEMICAL_PATHWAY_IMPORT_REVISED.md) | 6-phase pipeline architecture with refinements | 961 | ✅ Complete |
| [**PATHWAY_IMPORT_REVISION_SUMMARY.md**](./PATHWAY_IMPORT_REVISION_SUMMARY.md) | Quick reference for revised architecture | 390 | ✅ Complete |

### 3. Protection & Safety

| Document | Description | Lines | Status |
|----------|-------------|-------|--------|
| [**PATHWAY_IMPORT_PROTECTION_STRATEGY.md**](./PATHWAY_IMPORT_PROTECTION_STRATEGY.md) | Comprehensive protection strategy (5 layers) | 527 | ✅ Complete |
| [**PATHWAY_IMPORT_PROTECTION_QUICK_REF.md**](./PATHWAY_IMPORT_PROTECTION_QUICK_REF.md) | Quick reference card for recovery | 209 | ✅ Complete |

### 4. Installation & Setup

| Document | Description | Lines | Status |
|----------|-------------|-------|--------|
| [**PATHWAY_IMPORT_SYSTEM_WIDE_INSTALLATION.md**](./PATHWAY_IMPORT_SYSTEM_WIDE_INSTALLATION.md) | System-wide installation guide (no conda) | 441 | ✅ Complete |

**Total Documentation**: ~3,700 lines across 7 files

---

## 🎯 Quick Start Guide

### What is This Feature?

Import biochemical pathways (like glycolysis, Krebs cycle) from SBML files and automatically convert them to Petri nets:

- **Metabolites** → Places (with token counts)
- **Reactions** → Transitions (with rates)
- **Stoichiometry** → Arc weights
- **Kinetics** → Transition rates

### Where to Start?

1. **New to the project?** → Read [BIOCHEMICAL_PATHWAY_IMPORT_SUMMARY.md](./BIOCHEMICAL_PATHWAY_IMPORT_SUMMARY.md)
2. **Want technical details?** → Read [BIOCHEMICAL_PATHWAY_IMPORT_REVISED.md](./BIOCHEMICAL_PATHWAY_IMPORT_REVISED.md)
3. **Ready to implement?** → See implementation status below
4. **Installing dependencies?** → Read [PATHWAY_IMPORT_SYSTEM_WIDE_INSTALLATION.md](./PATHWAY_IMPORT_SYSTEM_WIDE_INSTALLATION.md)

---

## 🏗️ Architecture Overview

### 6-Phase Import Pipeline

```
┌─────────────┐
│ SBML File   │  User selects file (*.sbml)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Phase 1     │  Parse SBML → Raw PathwayData
│ PARSE       │  (species, reactions, kinetics)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Phase 2     │  Validate data integrity
│ VALIDATE    │  (check references, stoichiometry)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Phase 3     │  Enrich & optimize
│ POST-       │  (layout, colors, units)
│ PROCESS     │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Phase 4     │  Map to Petri net
│ CONVERT     │  (species→places, reactions→transitions)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Phase 5     │  Create objects automatically
│ INSTANTIATE │  (Place, Transition, Arc objects)
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ Canvas      │  ✅ Ready to simulate!
└─────────────┘
```

---

## 📦 Implementation Status

### ✅ Completed

- [x] Research (databases, formats, mapping)
- [x] Architecture design (6-phase pipeline)
- [x] Refinements (validation, post-processing, instantiation)
- [x] Protection strategy (5 redundancy layers)
- [x] Dependencies installed (libSBML 5.20.4, networkx 2.8.8)
- [x] Package structure (`src/shypn/data/pathway/`)
- [x] Data classes (Species, Reaction, PathwayData)

### 🚧 In Progress

- [ ] SBML Parser implementation
- [ ] Pathway Validator implementation
- [ ] Post-Processor implementation
- [ ] Pathway Converter implementation
- [ ] Canvas Instantiator implementation

### 📋 Planned

- [ ] UI integration (file dialog)
- [ ] Test suite
- [ ] Sample SBML files
- [ ] User documentation

---

## 🛠️ Technical Stack

### Dependencies

| Package | Version | Purpose | Status |
|---------|---------|---------|--------|
| GTK 3 | 3.24 | UI framework | ✅ System |
| python-libsbml | 5.20.4 | SBML parsing | ✅ Pip |
| networkx | 2.8.8 | Layout algorithms | ✅ System |
| Python | 3.12.3 | Runtime | ✅ System |

**Installation Method**: System-wide (no conda) to avoid GTK conflicts

### Project Structure

```
src/shypn/data/pathway/
├── __init__.py                    # Package initialization
├── pathway_data.py                # ✅ Data classes
├── sbml_parser.py                 # 🚧 SBML parsing
├── pathway_validator.py           # 🚧 Validation
├── pathway_postprocessor.py       # 🚧 Post-processing
├── pathway_converter.py           # 🚧 Conversion
├── kinetics_mapper.py             # 🚧 Kinetics
└── pathway_layout.py              # 🚧 Layout

src/shypn/helpers/
└── model_canvas_instantiator.py   # 🚧 Instantiation

tests/pathway/
└── (test files)                   # 📋 Planned
```

---

## 🗄️ Data Sources

### Supported Databases

| Database | Type | Access | Models |
|----------|------|--------|--------|
| **Reactome** | Open source | REST API | 2,500+ pathways |
| **BioModels** | Open source | Direct download | 900+ curated |
| **KEGG** | Commercial/Academic | REST API | 500+ pathways |
| **BioCyc** | Free/Subscription | API | 19,000+ pathways |

### Example Pathways

- Glycolysis (10 species, 10 reactions)
- Krebs cycle (20+ species, 15+ reactions)
- Glycogen metabolism
- Amino acid biosynthesis
- Signal transduction cascades

---

## 🎓 Key Concepts

### Mapping to Petri Nets

| SBML Element | Petri Net Element | Example |
|--------------|-------------------|---------|
| Species (metabolite) | Place | Glucose → Place with 500 tokens |
| Reaction | Transition | Hexokinase → Transition |
| Stoichiometry | Arc weight | 2 ATP consumed → Arc weight 2 |
| Kinetic law | Transition rate | Vmax=10, Km=0.5 → rate function |
| Compartment | Visual grouping | Cytosol → blue region |

### Example Transformation

**SBML Input** (glycolysis.sbml):
```xml
<species id="C00031" name="Glucose" initialAmount="5.0"/>
<reaction id="R00001" name="Hexokinase">
  <listOfReactants>
    <speciesReference species="C00031" stoichiometry="1"/>
  </listOfReactants>
  <kineticLaw>
    <math>Vmax * Glucose / (Km + Glucose)</math>
  </kineticLaw>
</reaction>
```

**Petri Net Output**:
- Place "Glucose" with 500 tokens (5.0 mM normalized)
- Transition "Hexokinase" with Michaelis-Menten rate
- Arc from Glucose to Hexokinase with weight 1

---

## 📖 Documentation Guide

### Reading Order (Recommended)

1. **Start Here**: [BIOCHEMICAL_PATHWAY_IMPORT_SUMMARY.md](./BIOCHEMICAL_PATHWAY_IMPORT_SUMMARY.md)
   - Quick overview
   - Answers key questions
   - Decision options

2. **Deep Dive**: [BIOCHEMICAL_PATHWAY_IMPORT_REVISED.md](./BIOCHEMICAL_PATHWAY_IMPORT_REVISED.md)
   - Complete 6-phase pipeline
   - Code examples
   - Implementation details

3. **Setup**: [PATHWAY_IMPORT_SYSTEM_WIDE_INSTALLATION.md](./PATHWAY_IMPORT_SYSTEM_WIDE_INSTALLATION.md)
   - Install dependencies
   - Verify setup
   - Troubleshooting

4. **Reference**: [BIOCHEMICAL_PATHWAY_IMPORT_RESEARCH.md](./BIOCHEMICAL_PATHWAY_IMPORT_RESEARCH.md)
   - Database analysis
   - Format specifications
   - Resources

---

## 🔒 Protection & Recovery

All design work is protected with **5 redundancy layers**:

1. ✅ Git tag: `pathway-import-design-v1.0`
2. ✅ Archive branch: `archive/pathway-import-design-2025-10-12`
3. ✅ External backup: `~/pathway-import-design-backup-20251012.tar.gz`
4. ✅ Feature branch: `feature/property-dialogs-and-simulation-palette`
5. ✅ Git history: Multiple commits

**Recovery Time**: < 1 minute using any method

See: [PATHWAY_IMPORT_PROTECTION_QUICK_REF.md](./PATHWAY_IMPORT_PROTECTION_QUICK_REF.md)

---

## 📊 Timeline

### Proof of Concept (2 weeks)
- **Week 1**: Parser + Validator (basic)
- **Week 2**: Converter + Instantiator (basic)
- **Deliverable**: Import simple SBML files

### Full Implementation (6-7 weeks)
- **Weeks 1-2**: Parser + Data classes
- **Weeks 3-4**: Validator + Post-processor
- **Weeks 5-6**: Converter + Instantiator + Kinetics
- **Week 7**: UI integration + Testing

---

## 🤝 Contributing

### Implementation Checklist

When implementing each phase:

1. Create the module file
2. Write docstrings
3. Add unit tests
4. Test with sample SBML file
5. Update this README
6. Commit with descriptive message

### Testing

Sample SBML files available from:
- BioModels: https://www.ebi.ac.uk/biomodels/
- BiGG Models: http://bigg.ucsd.edu/

---

## 📞 Support & References

### External Resources

- **SBML Specification**: http://sbml.org/
- **libSBML Documentation**: http://sbml.org/Software/libSBML
- **Reactome API**: https://reactome.org/dev/content-service
- **BioModels**: https://www.ebi.ac.uk/biomodels/

### Internal References

- Main project README: `../README.md`
- Architecture docs: `../doc/`
- Source code: `../../src/shypn/`

---

## 📝 Version History

| Version | Date | Changes |
|---------|------|---------|
| 0.1.0 | 2025-10-12 | Initial design and research complete |
| 0.2.0 | 2025-10-12 | Refined architecture (6-phase pipeline) |
| 0.3.0 | 2025-10-12 | Dependencies installed, package created |
| 1.0.0 | TBD | Full implementation complete |

---

## 📜 License

Same as main project (see root LICENSE file)

---

**Status**: Design complete ✅ | Implementation in progress 🚧 | Ready for development 🚀

