# KEGG Kinetic Parameters - Test Results

**Date**: November 4, 2025  
**Question**: Does KEGG return kinetic parameters?  
**Answer**: ❌ **NO** - KEGG does NOT provide kinetic parameters

---

## Test Results Summary

### What KEGG Provides ✅

1. **Pathway Topology** - Which reactions connect which compounds
2. **Metabolite Information** - Compound IDs, names, chemical structures  
3. **Reaction Information** - EC numbers, stoichiometry, reversibility
4. **Gene/Enzyme Associations** - Which genes encode which enzymes
5. **Visualization Coordinates** - X/Y positions for pathway diagrams

### What KEGG Does NOT Provide ❌

1. **Vmax values** - Maximum reaction velocity
2. **Km values** - Michaelis constant (substrate affinity)
3. **Kcat values** - Turnover number (catalytic efficiency)
4. **Ki values** - Inhibition constants
5. **Rate functions** - Mathematical expressions for reaction rates
6. **Kinetic laws** - SBML-style kinetic equations

---

## Why KEGG Doesn't Provide Kinetics

**KEGG is a PATHWAY DATABASE, not a KINETICS DATABASE**

1. **Focus on Structure** - KEGG documents pathway topology (which reactions exist)
2. **Context-Dependent** - Kinetic parameters vary by:
   - Organism (human vs. E. coli)
   - Tissue type (liver vs. brain)
   - Cell conditions (pH, temperature, cofactor concentrations)
3. **Data Volume** - Each reaction would need thousands of parameter sets
4. **Specialization** - Better to use dedicated kinetics databases

---

## Test Evidence

### KGML Analysis
- Fetched KEGG pathway **hsa00010** (Glycolysis/Gluconeogenesis)
- KGML size: **46,581 characters**
- Searched for keywords: `vmax`, `Vmax`, `VMAX`, `km`, `Km`, `KM`, `kcat`, `Kcat`, `KCAT`, `ki`, `Ki`, `KI`, `kinetic`, `parameter`
- **Result**: Only false positives (e.g., "ki" in "hexokinase")

### KGML Structure
```xml
<?xml version="1.0"?>
<pathway name="path:hsa00010" org="hsa" number="00010" title="Glycolysis / Gluconeogenesis">
    <entry id="18" name="hsa:226 hsa:229 hsa:230" type="gene" reaction="rn:R01068">
        <graphics name="ALDOA, ALDA, GSD12, HEL-S-87p..." type="rectangle" x="427" y="411"/>
    </entry>
    <reaction id="61" name="rn:R01068" type="reversible">
        <substrate id="17" name="cpd:C00118"/>
        <product id="18" name="cpd:C05378"/>
    </reaction>
</pathway>
```

**Observations**:
- ✅ Contains `<entry>` (compounds/enzymes)
- ✅ Contains `<reaction>` (topology)
- ✅ Contains `<graphics>` (coordinates)
- ✅ Contains `<substrate>`/`<product>` (stoichiometry)
- ❌ NO `<kineticLaw>` elements
- ❌ NO parameter values (Vmax, Km, Kcat, Ki)

---

## Where to Get Real Kinetic Parameters

### 1. BRENDA Database ⭐ (Best for Enzymes)

**Usage in ShyPN**:
```
Right-click transition → "Enrich with BRENDA"
```

**What it provides**:
- Vmax, Km, Kcat, Ki from peer-reviewed literature
- Organism-specific data (Homo sapiens, E. coli, Saccharomyces cerevisiae, etc.)
- ~95,000 enzyme entries with kinetic data
- References to original publications

**Example**:
```
EC 2.7.1.1 (Hexokinase), Homo sapiens:
- Km(glucose): 0.15 mM
- Vmax: 2.5 µmol/min/mg protein
- Kcat: 450 s⁻¹
```

### 2. SABIO-RK Database ⭐ (Best for Reactions)

**Usage in ShyPN**:
```
Right-click transition → "Enrich with SABIO-RK"
```

**What it provides**:
- Kinetic laws from SBML models
- Parameter values with units
- Multiple parameter sets per reaction
- Links to original publications
- KEGG reaction ID mapping

**Example**:
```
EC 2.7.1.1, Homo sapiens:
- 292 kinetic parameters found
- 149 unique reactions
- KEGG R-IDs: R00299, R00300, R00301, ...
- Parameters: Vmax, Km, Kcat, Ki (all with units)
```

### 3. SBML Import (Pre-curated Models)

**Usage in ShyPN**:
```
File → Import → SBML
```

**What it provides**:
- Complete models with integrated kinetic laws
- BioModels database has ~1,000 curated models
- Parameters already embedded in `<kineticLaw>` elements
- Peer-reviewed and experimentally validated

---

## ShyPN Workflow for Kinetics

### Step 1: Import Pathway Structure (KEGG)
```
Pathways Panel → KEGG Import → Enter pathway ID (e.g., hsa00010)
```
**Result**: Petri net with transitions (NO kinetics)

### Step 2: Enrich with Kinetic Parameters

**Option A: BRENDA** (Enzyme-focused)
```
Right-click transition → Enrich with BRENDA → Search → Apply Selected
```

**Option B: SABIO-RK** (Reaction-focused)
```
Right-click transition → Enrich with SABIO-RK → Search → Apply Selected
```

### Step 3: Verify Parameters
```
Report Panel → Check "Kinetics" section
```

---

## Common Misconceptions

### ❌ Misconception 1
> "KEGG imported my pathway with kinetics"

**Reality**: Those are **HEURISTIC defaults** (vmax=10.0, km=0.5), not real data!  
Check transition metadata: `source = 'heuristic'`

### ❌ Misconception 2
> "I need to download KEGG kinetics database"

**Reality**: KEGG doesn't have a kinetics database. Use BRENDA or SABIO-RK instead.

### ❌ Misconception 3
> "SBML from KEGG includes kinetics"

**Reality**: KEGG's SBML export (KGML→SBML conversion) does NOT include kinetic laws.  
Only manually curated SBML models (like those on BioModels) have kinetics.

---

## Technical Details

### KEGG KGML Schema
```xml
<!DOCTYPE pathway SYSTEM "https://www.kegg.jp/kegg/xml/KGML_v0.7.2_.dtd">
```

**Elements in KGML**:
- `<pathway>` - Pathway metadata
- `<entry>` - Compounds, genes, enzymes
- `<reaction>` - Reaction topology
- `<substrate>` / `<product>` - Stoichiometry
- `<graphics>` - Visualization coordinates

**Elements NOT in KGML**:
- `<kineticLaw>` - ❌ Not in KGML schema
- `<parameter>` - ❌ Not in KGML schema
- `<listOfParameters>` - ❌ Not in KGML schema

### ShyPN Heuristic Assignment

When KEGG pathways are imported with "Enable kinetics enhancement":

```python
# Default heuristic values assigned by ShyPN
vmax = 10.0  # Arbitrary default
km = 0.5     # Arbitrary default
kinetic_type = 'mass_action'  # Or 'michaelis_menten' based on structure
```

These are **NOT real experimental values** - they are placeholders for simulation!

---

## Conclusion

✅ **KEGG is excellent for**:
- Pathway structure and topology
- Identifying which reactions exist
- Finding EC numbers for enzymes
- Visualizing metabolic pathways

❌ **KEGG is NOT suitable for**:
- Obtaining kinetic parameters
- Getting Vmax, Km, Kcat, Ki values
- Building quantitative kinetic models

🎯 **For real kinetic parameters, use**:
1. **BRENDA** - Best enzyme kinetics database
2. **SABIO-RK** - Best reaction kinetics database  
3. **BioModels** - Pre-curated SBML models with kinetics

---

## Related Documentation

- `SABIO_RK_DEDUPLICATION.md` - SABIO-RK result deduplication
- `SABIO_RK_ENHANCEMENTS.md` - SABIO-RK table refactoring
- `BRENDA_INTEGRATION_PLAN.md` - BRENDA enrichment workflow
- `test_kegg_kinetic_parameters.py` - Test script for this analysis

---

**Status**: ✅ Confirmed via KGML analysis (November 4, 2025)
