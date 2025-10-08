# KEGG Import Quick Reference

## One-Page Overview

### What It Does
Import real biochemical pathways from KEGG database → automatic Petri net conversion

### Mapping Rules
```
Compound (glucose, ATP)     →  Place
Enzyme/Reaction (hexokinase) →  Transition  
Substrate (input)            →  Input Arc
Product (output)             →  Output Arc
Stoichiometry (2 ATP)        →  Arc Weight = 2
```

### API Endpoints
```bash
# Fetch KGML
https://rest.kegg.jp/get/<pathway_id>/kgml

# Examples
https://rest.kegg.jp/get/hsa00010/kgml  # Human glycolysis
https://rest.kegg.jp/get/map00020/kgml  # Reference TCA cycle
```

### Pathway ID Format
```
<prefix><number>
  
Prefix types:
  map - Reference pathway
  hsa - Homo sapiens (human)
  mmu - Mus musculus (mouse)
  eco - E. coli
  
Examples:
  map00010 - Glycolysis (reference)
  hsa00010 - Glycolysis (human)
  hsa04010 - MAPK signaling
```

### Implementation Checklist

**Phase 1: Core** (2 days)
- [ ] Create `src/shypn/import/kegg/` directory
- [ ] Implement `api_client.py` (fetch KGML)
- [ ] Implement `kgml_parser.py` (parse XML)
- [ ] Test with glycolysis

**Phase 2: Conversion** (2 days)
- [ ] Implement `pathway_converter.py`
- [ ] Map compounds → places
- [ ] Map reactions → transitions
- [ ] Create arcs with stoichiometry
- [ ] Handle coordinates

**Phase 3: UI** (2 days)
- [ ] Create import dialog (GTK)
- [ ] Add File → Import menu item
- [ ] Add options panel
- [ ] Academic use warning

**Phase 4: Polish** (2 days)
- [ ] Regulatory relations
- [ ] Cofactor filtering
- [ ] Layout optimization
- [ ] Caching

**Phase 5: Testing** (2 days)
- [ ] Test 5+ pathways
- [ ] Documentation
- [ ] User guide

### Key Classes

```python
@dataclass
class KEGGEntry:
    id: str           # "18"
    name: str         # "hsa:226"
    type: str         # "gene", "compound"
    graphics: dict    # {x, y, width, height, name}

@dataclass
class KEGGReaction:
    id: str           # "23"
    name: str         # "rn:R01068"
    type: str         # "reversible"
    substrates: List  # [(entry_id, compound_id)]
    products: List

@dataclass
class KEGGPathway:
    id: str           # "00010"
    title: str        # "Glycolysis"
    entries: Dict
    reactions: List
```

### Conversion Flow

```
KEGG API
   ↓ (fetch_kgml)
KGML XML
   ↓ (parse)
KEGGPathway
   ↓ (convert)
DocumentModel
   ↓ (display)
Canvas
```

### Test Pathways

| ID | Name | Size | Notes |
|----|------|------|-------|
| hsa00010 | Glycolysis | Medium | Start here |
| hsa00020 | TCA Cycle | Medium | Circular |
| hsa00030 | Pentose Phosphate | Medium | Branching |
| hsa04010 | MAPK Signaling | Large | Complex |

### Common Issues & Solutions

**Issue**: Overlapping nodes
**Solution**: Multiply coordinates by 2.5-3.0

**Issue**: Too many cofactors (ATP everywhere)
**Solution**: Add "Include cofactors" checkbox

**Issue**: API rate limit
**Solution**: Cache downloaded KGML files

**Issue**: Reversible reactions
**Solution**: Single transition with bidirectional arcs

### Academic Use Requirements

✅ Include license notice  
✅ User confirmation dialog  
✅ Attribution in exports  
✅ Respect API limits  
✅ Document in user guide  

### Files to Create

```
src/shypn/import/kegg/
├── api_client.py       (150 lines)
├── kgml_parser.py      (300 lines)
├── pathway_converter.py (400 lines)
├── models.py           (100 lines)

src/shypn/import/dialogs/
└── kegg_import_dialog.py (350 lines)

Total: ~1300 lines
```

### Quick Start Command

```bash
# Create directory structure
mkdir -p src/shypn/import/kegg
mkdir -p src/shypn/import/dialogs

# Create __init__.py files
touch src/shypn/import/__init__.py
touch src/shypn/import/kegg/__init__.py
touch src/shypn/import/dialogs/__init__.py

# Start with API client
vim src/shypn/import/kegg/api_client.py
```

### Time Estimate
- **Minimum**: 6 days
- **Realistic**: 8 days  
- **Conservative**: 10 days

---

**Status**: 📋 Analysis complete, ready to code
**Next**: Implement api_client.py
