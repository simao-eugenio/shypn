# Compound Mapping Quick Reference

## Overview

The compound mapping system automatically links Petri net places to biochemical compound identifiers (KEGG, ChEBI) for thermodynamic validation.

---

## Basic Usage

### Automatic Mapping

```python
from shypn.data.canvas.document_model import DocumentModel
from shypn.thermodynamics.mappers import CompoundMapperService

# Load or create document
document = DocumentModel()

# Auto-map compounds
service = CompoundMapperService()
mappings, confidences = service.map_all_places(document)

# View results
for place in document.places:
    compound_id = mappings.get(place.id, "NOT MAPPED")
    confidence = confidences.get(place.id, 0.0)
    print(f"{place.label} → {compound_id} (confidence: {confidence:.0%})")
```

### Manual Override

```python
# Update a mapping
service.update_mapping(document, "P001", "C00002")  # ATP

# Remove a mapping
service.remove_mapping(document, "P001")
```

### Check Unmapped Places

```python
unmapped = service.get_unmapped_places(document)
print(f"{len(unmapped)} places need manual mapping")
```

---

## Supported Compound IDs

### KEGG Format
- Pattern: `C#####` (5 digits)
- Example: `C00002` (ATP)
- Database: KEGG COMPOUND

### ChEBI Format
- Pattern: `CHEBI:#####`
- Example: `CHEBI:15422` (ATP)
- Database: Chemical Entities of Biological Interest

---

## Mapping Strategies

### 1. SBML Annotations (Highest Priority)
- **Confidence:** 1.0 (100%)
- **Source:** `document.metadata['sbml_species']`
- **Trigger:** SBML file import
- **Format:**
  ```python
  document.metadata = {
      "sbml_species": {
          "M_atp_c": {
              "name": "ATP",
              "kegg_id": "C00002",
              "chebi_id": "CHEBI:15422"
          }
      }
  }
  ```

### 2. Label Direct Extraction
- **Confidence:** 0.95 (95%)
- **Patterns:**
  - `ATP (C00002)` → `C00002`
  - `Glucose [C00031]` → `C00031`
  - `CHEBI:15422` → `CHEBI:15422`

### 3. Label Fuzzy Matching
- **Confidence:** 0.60 (60%)
- **Database:** 80+ common compounds
- **Examples:**
  - `ATP` → `C00002`
  - `Glucose` → `C00031`
  - `NADH` → `C00004`
  - `Pyruvate` → `C00022`

---

## Confidence Levels

| Score | Category | Description |
|-------|----------|-------------|
| 1.0   | Exact    | SBML annotation |
| 0.9-0.99 | High  | Direct ID extraction |
| 0.5-0.89 | Medium | Fuzzy name match |
| 0.0-0.49 | Low   | Uncertain match |
| 0.0   | None    | No mapping found |

---

## Common Compounds

### Energy Carriers
- ATP → `C00002`
- ADP → `C00008`
- AMP → `C00020`
- GTP → `C00044`
- GDP → `C00035`

### Redox Carriers
- NADH → `C00004`
- NAD+ → `C00003`
- NADPH → `C00005`
- NADP+ → `C00006`
- FAD → `C00016`
- FADH2 → `C01352`

### Central Carbon
- Glucose → `C00031`
- Glucose-6-phosphate → `C00092`
- Fructose-6-phosphate → `C00085`
- Pyruvate → `C00022`
- Acetyl-CoA → `C00024`
- Citrate → `C00158`

### Amino Acids
- Glycine → `C00037`
- Alanine → `C00041`
- Serine → `C00065`
- Glutamate → `C00025`
- Glutamine → `C00064`

### Small Molecules
- Water → `C00001`
- Phosphate → `C00009`
- CO2 → `C00011`
- Ammonia → `C00014`
- Oxygen → `C00007`

*Full list: 80+ compounds in `label_matcher.py`*

---

## Statistics Summary

```python
summary = service.get_mapping_summary(mappings, confidences)

print(f"Total mapped: {summary['total_mapped']}")
print(f"High confidence: {summary['high_confidence']}")
print(f"Medium confidence: {summary['medium_confidence']}")
print(f"Average confidence: {summary['average_confidence']:.1%}")
```

---

## Persistence

Mappings are automatically saved with the document:

```python
# Save document
document.save_to_file("model.shy")

# Load document
document2 = DocumentModel.load_from_file("model.shy")

# Mappings restored
assert document2.compound_mappings == document.compound_mappings
```

**File format:**
```json
{
  "version": "2.0",
  "compound_mappings": {
    "P001": "C00002",
    "P002": "C00031"
  },
  ...
}
```

---

## Extending the System

### Add Custom Mapper

```python
from shypn.thermodynamics.mappers import CompoundMapperBase

class CustomMapper(CompoundMapperBase):
    def map_places(self, places):
        mappings = {}
        for place in places:
            # Your custom logic
            if "custom_pattern" in place.label:
                mappings[place.id] = "C99999"
        return mappings
    
    def get_confidence(self, place_id):
        return 0.75  # Your confidence level

# Use custom mapper
service = CompoundMapperService(
    custom_mappers=[CustomMapper(), LabelBasedMapper()]
)
```

---

## Troubleshooting

### No Mappings Found

**Symptoms:** All places return "NOT MAPPED"

**Solutions:**
1. Check place labels contain compound names
2. Add compound IDs to labels: `ATP (C00002)`
3. Use manual override: `service.update_mapping(...)`

### Low Confidence Scores

**Symptoms:** Confidence < 0.5

**Solutions:**
1. Use more specific labels
2. Add KEGG/ChEBI IDs to labels
3. Import from SBML with annotations
4. Manually verify and override

### Invalid Compound ID

**Symptoms:** `ValueError: Invalid compound ID format`

**Solutions:**
1. Use KEGG format: `C00002` (5 digits)
2. Use ChEBI format: `CHEBI:15422`
3. Check typos: `C0002` → `C00002`

---

## API Reference

### CompoundMapperService

**Methods:**
- `map_all_places(document)` → (mappings, confidences)
- `update_mapping(document, place_id, compound_id, confidence=1.0)`
- `remove_mapping(document, place_id)`
- `get_unmapped_places(document)` → List[Place]
- `get_mapping_summary(mappings, confidences)` → dict

### DocumentModel

**Attributes:**
- `compound_mappings: Dict[str, str]` - Place ID → Compound ID

**Methods:**
- `to_dict()` - Serializes compound_mappings
- `from_dict(data)` - Restores compound_mappings

---

## Examples

### Example 1: SBML Import Workflow

```python
# After SBML import
document = load_sbml("model.xml")

# Auto-map from SBML annotations
service = CompoundMapperService()
mappings, confidences = service.map_all_places(document)

# All SBML species should have confidence 1.0
sbml_mapped = [p for p, c in confidences.items() if c == 1.0]
print(f"{len(sbml_mapped)} places mapped from SBML")
```

### Example 2: Mixed Workflow

```python
# Create model manually
document = DocumentModel()
document.create_place(100, 100, label="ATP (C00002)")  # Direct ID
document.create_place(200, 100, label="Glucose")        # Fuzzy match
document.create_place(300, 100, label="Compound X")     # Unmapped

# Auto-map
service = CompoundMapperService()
mappings, confidences = service.map_all_places(document)

# Manual override for unmapped
unmapped = service.get_unmapped_places(document)
for place in unmapped:
    compound_id = input(f"Compound ID for {place.label}: ")
    service.update_mapping(document, place.id, compound_id)
```

### Example 3: Quality Report

```python
mappings, confidences = service.map_all_places(document)
summary = service.get_mapping_summary(mappings, confidences)

# Generate report
print("=== Compound Mapping Report ===")
print(f"Total places: {len(document.places)}")
print(f"Mapped: {summary['total_mapped']}")
print(f"Unmapped: {len(document.places) - summary['total_mapped']}")
print(f"\nConfidence Distribution:")
print(f"  High (≥0.9): {summary['high_confidence']}")
print(f"  Medium (0.5-0.9): {summary['medium_confidence']}")
print(f"  Low (<0.5): {summary['low_confidence']}")
print(f"  Average: {summary['average_confidence']:.1%}")
```

---

**See Also:**
- [THERMODYNAMICS_REFACTOR_PLAN.md](THERMODYNAMICS_REFACTOR_PLAN.md) - Complete refactoring plan
- [THERMODYNAMICS_PHASE1_COMPLETE.md](THERMODYNAMICS_PHASE1_COMPLETE.md) - Implementation details
- `src/shypn/thermodynamics/mappers/` - Source code
- `scripts/test_compound_mapper.py` - Test examples
