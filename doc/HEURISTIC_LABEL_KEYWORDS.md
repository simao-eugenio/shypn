# Heuristic Parameters - Label Keyword Reference

## Overview

The Heuristic Parameters system uses **label keyword matching** to assign appropriate default kinetic parameters when EC numbers are not available. This document lists all supported keywords and their associated parameter values.

## Keyword Matching System

- **Case-insensitive**: All labels converted to lowercase before matching
- **Priority order**: First match wins (top to bottom)
  1. **EC Number** (if available)
  2. **KEGG gene symbols** (hk1, gapdh, pfkl, etc.)
  3. **Full enzyme names** (kinase, dehydrogenase, etc.)
  4. **Generic fallback**
- **Fallback**: Generic values if no keywords match

---

## KEGG Gene Symbol Patterns

KEGG models use abbreviated gene symbols rather than full enzyme names. These patterns are checked **first** to support KEGG pathways (e.g., hsa00010 Glycolysis).

### 1. Hexokinase / Glucokinase
**Patterns**: `hk*`, `gck*`  
**Parameters**: Vmax=50, Km=0.05, Kcat=5  
**Examples**: hk1, hk2, gck

### 2. Pyruvate Kinase
**Patterns**: `pk*`, `pklr`, `pkm`  
**Parameters**: Vmax=50, Km=0.05, Kcat=5  
**Examples**: pklr, pkm, pkm2

### 3. Phosphofructokinase
**Patterns**: `pfk*`  
**Parameters**: Vmax=50, Km=0.05, Kcat=5  
**Examples**: pfkl, pfkm, pfkp

### 4. Phosphoglycerate Kinase
**Patterns**: `pgk*`  
**Parameters**: Vmax=50, Km=0.05, Kcat=5  
**Examples**: pgk1, pgk2

### 5. Dehydrogenases (Gene Symbols)
**Patterns**: Contains `dh`, or `gapdh`, `ldh*`, `aldh*`, `adh*`, `pdh*`, `idh*`, `mdh*`  
**Parameters**: Vmax=150, Km=0.2, Kcat=15  
**Examples**: gapdh, ldhal6a, aldh2, adh1a, pdha1, idh1, mdh2

### 6. Aldolases (Gene Symbols)
**Patterns**: `aldo*`, `ald*`  
**Parameters**: Vmax=90, Km=0.2, Kcat=9  
**Examples**: aldoa, aldob, aldoc

### 7. Isomerases (Gene Symbols)
**Patterns**: `tpi*`, `gpi*`  
**Parameters**: Vmax=70, Km=0.12, Kcat=7  
**Examples**: tpi1, gpi1

### 8. Phosphoglycerate Mutase
**Patterns**: `pgam*`  
**Parameters**: Vmax=70, Km=0.12, Kcat=7  
**Examples**: pgam1, pgam4

### 9. Phosphoglucomutase
**Patterns**: `pgm*` (excluding pgam)  
**Parameters**: Vmax=70, Km=0.12, Kcat=7  
**Examples**: pgm1, pgm2

### 10. Enolases
**Patterns**: `eno*`  
**Parameters**: Vmax=90, Km=0.2, Kcat=9  
**Examples**: eno1, eno2

### 11. Fructose-Bisphosphatase
**Patterns**: `fbp*`  
**Parameters**: Vmax=100, Km=0.1, Kcat=10  
**Examples**: fbp1, fbp2

### 12. Reductases / Oxidases (Gene Symbols)
**Patterns**: `akr*`, `cox*`, `nox*`  
**Parameters**: Vmax=120, Km=0.15, Kcat=12  
**Examples**: akr1a1, cox1, nox4

### 13. Transferases (Gene Symbols)
**Patterns**: `dlat*`, `glut*`  
**Parameters**: Vmax=55, Km=0.08, Kcat=5.5  
**Examples**: dlat, glut1

---

## Enzyme Name Patterns (Full Names)

These patterns match full enzyme names and biological keywords. Checked **after** KEGG gene symbols.

### 1. Kinases / Phosphorylation
**Keywords**: `kinase`, `phosphorylation`  
**Parameters**: Vmax=50, Km=0.05, Kcat=5  
**Rationale**: Slower reaction, high substrate affinity  
**Examples**: 
- hexokinase
- phosphofructokinase
- protein phosphorylation

### 2. Phosphatases / Dephosphorylation
**Keywords**: `phosphatase`, `dephosphorylation`  
**Parameters**: Vmax=100, Km=0.1, Kcat=10  
**Rationale**: Medium speed, reverse of phosphorylation  
**Examples**:
- protein phosphatase
- alkaline phosphatase

### 3. Dehydrogenases
**Keywords**: `dehydrogenase`  
**Parameters**: Vmax=150, Km=0.2, Kcat=15  
**Rationale**: Fast oxidoreductases  
**Examples**:
- lactate dehydrogenase
- glucose-6-phosphate dehydrogenase
- alcohol dehydrogenase

### 4. Synthases / Synthesis
**Keywords**: `synthase`, `synthesis`, `synthetase`  
**Parameters**: Vmax=80, Km=0.3, Kcat=8  
**Rationale**: Medium-slow, complex product formation  
**Examples**:
- ATP synthase
- citrate synthase
- fatty acid synthesis

### 5. Proteases / Peptidases
**Keywords**: `protease`, `peptidase`  
**Parameters**: Vmax=200, Km=0.5, Kcat=20  
**Rationale**: Very fast, low substrate affinity  
**Examples**:
- trypsin protease
- chymotrypsin
- aminopeptidase

### 6. Glycosylases
**Keywords**: `glycosylase`, `glycosyl`  
**Parameters**: Vmax=120, Km=0.15, Kcat=12  
**Rationale**: Fast glycosidic bond cleavage  
**Examples**:
- DNA glycosylase
- glycosyltransferase

### 7. Reductases / Oxidases
**Keywords**: `reductase`, `oxidase`  
**Parameters**: Vmax=120, Km=0.15, Kcat=12  
**Rationale**: Fast oxidoreductases (EC 1)  
**Examples**:
- cytochrome c oxidase
- lactate oxidase
- nitrate reductase

### 8. Isomerases / Epimerases / Mutases
**Keywords**: `isomerase`, `epimerase`, `mutase`  
**Parameters**: Vmax=70, Km=0.12, Kcat=7  
**Rationale**: Medium speed structural rearrangement (EC 5)  
**Examples**:
- phosphoglucose isomerase
- triosephosphate isomerase
- UDP-glucose epimerase

### 9. Lyases / Decarboxylases / Aldolases
**Keywords**: `lyase`, `decarboxylase`, `aldolase`  
**Parameters**: Vmax=90, Km=0.2, Kcat=9  
**Rationale**: Medium speed bond cleavage (EC 4)  
**Examples**:
- fructose-bisphosphate aldolase
- pyruvate decarboxylase
- fumarase

### 10. Ligases / Carboxylases
**Keywords**: `ligase`, `carboxylase`  
**Parameters**: Vmax=45, Km=0.25, Kcat=4.5  
**Rationale**: Slower, ATP-dependent bond formation (EC 6)  
**Examples**:
- DNA ligase
- pyruvate carboxylase
- acetyl-CoA carboxylase

### 11. Transferases / Transaminases
**Keywords**: `transferase`, `transaminase`  
**Parameters**: Vmax=55, Km=0.08, Kcat=5.5  
**Rationale**: Medium speed group transfer (EC 2)  
**Examples**:
- aminotransferase
- methyltransferase
- acetyltransferase

### 12. Hydrolases / Lipases / Esterases
**Keywords**: `hydrolase`, `lipase`, `esterase`  
**Parameters**: Vmax=180, Km=0.4, Kcat=18  
**Rationale**: Fast hydrolytic cleavage (EC 3)  
**Examples**:
- lipase
- carbonic anhydrase
- acetylcholinesterase

### 13. Polymerases / Polymerization
**Keywords**: `polymerase`, `polymerization`  
**Parameters**: Vmax=30, Km=0.4, Kcat=3  
**Rationale**: Very slow, high substrate requirement  
**Examples**:
- DNA polymerase
- RNA polymerase
- actin polymerization

### 14. Binding / Association
**Keywords**: `binding`, `association`  
**Parameters**: Vmax=200, Km=0.05, Kcat=20  
**Rationale**: Very fast, high affinity interactions  
**Examples**:
- receptor binding
- protein-protein association
- ligand binding

### 15. Transport / Transporter / Channel
**Keywords**: `transport`, `transporter`, `channel`  
**Parameters**: Vmax=150, Km=0.1, Kcat=15  
**Rationale**: Fast membrane transport  
**Examples**:
- glucose transporter
- ion channel
- ABC transporter

### 16. Cleavage / Degradation
**Keywords**: `cleavage`, `degradation`  
**Parameters**: Vmax=100, Km=0.2, Kcat=10  
**Rationale**: Medium speed breakdown  
**Examples**:
- protein degradation
- RNA cleavage
- bond cleavage

### 17. Generic (Fallback)
**Keywords**: *None* (no match)  
**Parameters**: Vmax=100, Km=0.1, Kcat=10  
**Rationale**: Default enzymatic reaction  
**Examples**:
- simple reaction
- reaction 1
- unknown process

---

## Usage Examples

### ✅ Good Labels (Match Keywords)
```
hexokinase                    → kinase pattern      → Vmax=50
ATP synthase                  → synthase pattern    → Vmax=80
DNA polymerase                → polymerase pattern  → Vmax=30
glucose transporter           → transport pattern   → Vmax=150
lactate dehydrogenase         → dehydrogenase pattern → Vmax=150
```

### ⚠️ Generic Labels (No Match)
```
simple reaction               → generic fallback    → Vmax=100
reaction 1                    → generic fallback    → Vmax=100
process A                     → generic fallback    → Vmax=100
```

---

## Integration with Stoichiometry

After label-based defaults are applied, **stoichiometry refinement** adjusts values based on:

1. **Multi-substrate complexity**: 3+ substrates → Vmax × 0.7
2. **Arc weights**: High stoichiometry → Km × (weight/2)
3. **Locality (markings)**: High concentration → Vmax × 1.3
4. **Balance ratio**: Well-balanced → Confidence +10%

**Example Pipeline**:
```
Label: "hexokinase" → Vmax=50 (kinase pattern)
       ↓
Stoichiometry: 2 substrates, weight=2 → Km × 2
       ↓
Final: Vmax=50, Km=0.10, Confidence=0.75
```

---

## Best Practices

1. **Use descriptive biological labels**:
   - ✅ "glucose-6-phosphate dehydrogenase"
   - ❌ "reaction 1"

2. **Include enzyme class or function**:
   - ✅ "hexokinase" (contains "kinase")
   - ✅ "ATP synthesis" (contains "synthesis")

3. **For exact parameters, use BRENDA/SABIO-RK**:
   - Heuristics = reasonable defaults
   - BRENDA/SABIO = experimental data

4. **Expect generic fallback for non-biological labels**:
   - "simple reaction" → Vmax=100 (expected)
   - Let stoichiometry refine from there

---

## EC Number Priority

If an **EC number** is available, it takes priority over label matching:

```
EC 1.x.x.x → Oxidoreductases   → Vmax=100
EC 2.x.x.x → Transferases      → Vmax=50
EC 3.x.x.x → Hydrolases        → Vmax=200
EC 4.x.x.x → Lyases            → Vmax=80
EC 5.x.x.x → Isomerases        → Vmax=60
EC 6.x.x.x → Ligases           → Vmax=40
```

---

## Summary

- **17 keyword pattern groups** covering all major enzyme classes
- **Case-insensitive substring matching**
- **EC number takes priority** over label keywords
- **Generic fallback** for unrecognized labels (Vmax=100)
- **Stoichiometry refinement** applied after base values
- **Best used with biological labels** for specific values

---

*Last updated: 2025 - Heuristic Parameters v2.0*
