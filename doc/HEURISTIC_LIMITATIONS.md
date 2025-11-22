# Heuristic Parameter Estimation - Limitations and Scope

## Overview

Heuristic parameter estimation (like Michaelis-Menten kinetics) is **ONLY applicable to manual models**, not imported models.

## Why Heuristics Don't Work for Imports

### Problem: Naming Conventions

Heuristics rely on **well-formed biological names** to work correctly:
- Names represent actual biochemical entities (glucose, ATP, hexokinase)
- Parameter estimation uses names to look up biological data
- Names must be consistent and standardized

### KEGG Imports: Incomplete Naming

**What KEGG provides:**
- Topology (connectivity graph)
- Mixed naming (enzyme names, EC numbers, transition IDs, "UnknownEnzyme")
- NO kinetic parameters

**Why heuristics fail:**
```
Transition names: "HK", "PFK", "EC_2.7.1.1", "T1", "UnknownEnzyme"
Place names:      "ATP", "C00002", "Glucose-6-phosphate"
```

- Names are inconsistent (some biological, some codes, some IDs)
- Missing enzyme names ("UnknownEnzyme", "T1", "T2")
- Heuristics can't reliably estimate parameters from incomplete data

**Consequence:** KEGG models must be **manually enriched by user** with proper kinetics

### SBML Imports: Already Complete

**What SBML provides:**
- Complete kinetics from expert curators
- Validated parameters (Km, Vmax, rate laws)
- Simulation-ready models

**Why heuristics unnecessary:**
- Models already have kinetics
- If kinetics missing, it's intentional (user should add manually)
- Applying heuristics would overwrite curator expertise

**Consequence:** SBML models either have kinetics (use them) or intentionally lack them (mark for enrichment)

## Heuristic Scope

### ✅ MANUAL MODELS ONLY

Heuristics work when:
1. **User creates model manually** (not imported)
2. **Names are well-formed** (glucose, ATP, hexokinase)
3. **No kinetics provided** (user wants estimates)

Example manual model:
```
Places:     Glucose, ATP, G6P, ADP
Transition: Hexokinase
Reaction:   Glucose + ATP → G6P + ADP
Kinetics:   (not provided) → Apply Michaelis-Menten heuristic
Result:     Vmax=10 mM/s, Km=5 mM (estimated)
```

### ❌ IMPORTED MODELS

Heuristics **disabled** for:
1. **KEGG imports** (incomplete names, topology-only)
2. **SBML imports** (already have kinetics or intentionally missing)

## Implementation

### Detection Logic

```python
# Check if model is imported
is_imported = False
for species_id, _ in reaction.reactants + reaction.products:
    place = self.species_to_place.get(species_id)
    if place and hasattr(place, 'metadata') and place.metadata:
        data_source = place.metadata.get('data_source')
        if data_source in ('sbml_import', 'kegg_import'):
            is_imported = True
            break

if is_imported:
    # DO NOT apply heuristics
    # Mark for manual enrichment by user
    transition.properties['needs_enrichment'] = True
```

### Marking for Enrichment

When heuristics are disabled, transitions are marked:
```python
transition.properties['needs_enrichment'] = True
transition.properties['enrichment_reason'] = (
    "Imported model without kinetics - requires user enrichment "
    "(heuristics unreliable with import naming conventions)"
)
```

This allows UI to:
- Highlight transitions needing attention
- Guide user to add kinetics manually
- Explain why heuristics weren't applied

## User Workflow

### For KEGG Imports

1. Import KEGG pathway → Get topology + clues
2. System marks transitions as `needs_enrichment`
3. User reviews enzyme names (may be "UnknownEnzyme", "T1", etc.)
4. User **manually adds kinetics**:
   - Research enzyme parameters (Km, Vmax)
   - Define rate functions
   - Add proper biological names if missing
5. Model becomes simulation-ready

### For SBML Imports

1. Import SBML model → Get complete kinetics
2. Use curator-provided parameters
3. If kinetics missing (rare):
   - System marks as `needs_enrichment`
   - User adds kinetics manually (don't trust heuristics)

### For Manual Models

1. User creates model with proper names
2. User defines topology (places, transitions, arcs)
3. For transitions without kinetics:
   - System applies heuristics (Michaelis-Menten)
   - Estimates Vmax, Km from stoichiometry
4. User can refine estimates later

## Rationale

### Philosophy

**Import ≠ Complete Biology**
- KEGG: Topology + clues (requires work)
- SBML: Complete biology (trust curators)
- Manual: User-controlled (heuristics helpful)

**Names Matter**
- Heuristics need reliable biological identifiers
- Import naming is inconsistent (codes, abbreviations, IDs)
- Manual models have user-chosen, consistent names

**Safety First**
- Better to mark for enrichment than apply bad heuristics
- User can always add kinetics manually
- Heuristics on bad names → garbage parameters

## Technical Notes

### Data Source Tagging

All imports are tagged at creation:

**SBML Parser:**
```python
metadata['data_source'] = 'sbml_import'
```

**KEGG Compound Mapper:**
```python
place.metadata['data_source'] = 'kegg_import'
```

**KEGG Reaction Mapper:**
```python
transition.metadata['data_source'] = 'kegg_import'
```

### Conversion Flow

```
Import → Parse → Tag with data_source
     ↓
Convert to Petri Net → Check data_source
     ↓
Reaction without kinetics?
     ↓
If imported → Mark needs_enrichment (no heuristics)
If manual   → Apply heuristics (Michaelis-Menten)
```

## Summary

| Model Type | Kinetics Source | Heuristics | User Action |
|------------|----------------|------------|-------------|
| **KEGG Import** | None | ❌ Disabled | Manual enrichment required |
| **SBML Import** | Curators | ❌ Disabled | Use provided kinetics |
| **Manual Model** | User/Heuristics | ✅ Enabled | Optional refinement |

**Key Insight:** Heuristics are a tool for **manual model creation**, not a fix for **incomplete import data**.
