# Metadata Requirements for SHYpn Analysis

## Overview

SHYpn's analytical capabilities are significantly enhanced when biochemical models include standardized biological metadata. This document explains what metadata is required, why it's important, and how to include it in your models.

## Why Metadata Matters

### Without Metadata
- **Topology Analysis Only**: Limited to structural and graph-based analysis
- **No Biological Context**: Places and transitions are treated as abstract nodes
- **Limited Enrichment**: Cannot connect to external databases or pathway information
- **Behavioral Analysis Only**: Only mathematical properties are analyzed

### With Metadata
- **Biological Analysis Enabled**: Compound identification, enzyme classification, pathway linking
- **Database Integration**: Automatic enrichment from KEGG, ChEBI, BRENDA, and other sources
- **Regulatory Pattern Detection**: Identification of feedback loops, allosteric regulation
- **Enhanced Reporting**: Biological context in all analysis reports
- **Cross-Pathway Linking**: Connection to related pathways and biological processes

## Required Metadata Fields

### For Places (Metabolites/Compounds)

#### Essential Fields
```json
{
  "id": "P1",
  "name": "ATP",
  "metadata": {
    "kegg_id": "C00002",
    "chebi_id": "CHEBI:15422",
    "compound_name": "Adenosine triphosphate"
  }
}
```

**Field Descriptions:**
- **`kegg_id`** (string): KEGG Compound ID (format: `C#####`)
  - Primary identifier for metabolites in KEGG database
  - Example: `C00002` (ATP), `C00031` (Glucose), `C00092` (G6P)
  - Find at: https://www.genome.jp/kegg/compound/

- **`chebi_id`** (string): ChEBI ID (format: `CHEBI:#####`)
  - Chemical Entities of Biological Interest identifier
  - Example: `CHEBI:15422` (ATP), `CHEBI:17234` (D-Glucose)
  - Find at: https://www.ebi.ac.uk/chebi/

- **`compound_name`** (string): Full chemical name
  - Human-readable IUPAC or common name
  - Used for display and documentation

#### Optional but Recommended
```json
{
  "metadata": {
    "kegg_id": "C00002",
    "chebi_id": "CHEBI:15422",
    "compound_name": "Adenosine triphosphate",
    "molecular_formula": "C10H16N5O13P3",
    "molecular_weight": 507.181,
    "inchi": "InChI=1S/C10H16N5O13P3/...",
    "smiles": "C1=NC(=C2C(=N1)N(C=N2)...)...",
    "compartment": "cytosol"
  }
}
```

### For Transitions (Enzymes/Reactions)

#### Essential Fields
```json
{
  "id": "T1",
  "name": "Hexokinase",
  "metadata": {
    "ec_number": "2.7.1.1",
    "enzyme_name": "Hexokinase",
    "kegg_enzyme": "ec:2.7.1.1"
  }
}
```

**Field Descriptions:**
- **`ec_number`** (string): Enzyme Commission number (format: `#.#.#.#`)
  - Standard enzyme classification
  - Example: `2.7.1.1` (Hexokinase), `5.3.1.9` (PGI)
  - Find at: https://enzyme.expasy.org/

- **`enzyme_name`** (string): Common enzyme name
  - Human-readable enzyme designation
  - Matches standard nomenclature

- **`kegg_enzyme`** (string): KEGG Enzyme ID (format: `ec:#.#.#.#`)
  - Links to KEGG enzyme database
  - Enables automatic kinetic parameter lookup

#### Optional but Recommended
```json
{
  "metadata": {
    "ec_number": "2.7.1.1",
    "enzyme_name": "Hexokinase",
    "kegg_enzyme": "ec:2.7.1.1",
    "kegg_reaction": "R00299",
    "uniprot_id": "P00489",
    "direction": "forward",
    "cofactors": ["Mg2+"],
    "mechanism": "sequential"
  }
}
```

## Finding Metadata

### KEGG Compound IDs
1. Visit: https://www.genome.jp/kegg/compound/
2. Search by compound name (e.g., "ATP", "Glucose")
3. Copy the compound ID (format: C#####)
4. Example: Searching "ATP" → `C00002`

### ChEBI IDs
1. Visit: https://www.ebi.ac.uk/chebi/
2. Search by name, synonym, or formula
3. Copy the ChEBI accession number
4. Format as: `CHEBI:#####`
5. Example: Searching "ATP" → `CHEBI:15422`

### EC Numbers
1. Visit: https://enzyme.expasy.org/
2. Search by enzyme name or browse classification
3. Example: Hexokinase → `EC 2.7.1.1`
4. Classification: `2` (Transferases) `.7` (Phosphotransferases) `.1` (Alcohol acceptor) `.1` (Hexokinase)

### KEGG Enzyme/Reaction IDs
1. KEGG Enzyme: https://www.genome.jp/kegg/enzyme/
2. KEGG Reaction: https://www.genome.jp/kegg/reaction/
3. Linked from compound pages via reaction pathways

## Common Metabolites Quick Reference

### Energy Metabolism
| Metabolite | KEGG ID | ChEBI ID | Formula |
|------------|---------|----------|---------|
| ATP | C00002 | CHEBI:15422 | C₁₀H₁₆N₅O₁₃P₃ |
| ADP | C00008 | CHEBI:16761 | C₁₀H₁₅N₅O₁₀P₂ |
| AMP | C00020 | CHEBI:16027 | C₁₀H₁₄N₅O₇P |
| NAD+ | C00003 | CHEBI:15846 | C₂₁H₂₇N₇O₁₄P₂ |
| NADH | C00004 | CHEBI:16908 | C₂₁H₂₉N₇O₁₄P₂ |
| NADP+ | C00006 | CHEBI:18009 | C₂₁H₂₈N₇O₁₇P₃ |
| NADPH | C00005 | CHEBI:16474 | C₂₁H₃₀N₇O₁₇P₃ |
| Pi | C00009 | CHEBI:43474 | HO₄P |
| PPi | C00013 | CHEBI:29888 | H₄O₇P₂ |

### Glycolysis Intermediates
| Metabolite | KEGG ID | ChEBI ID | Common Name |
|------------|---------|----------|-------------|
| D-Glucose | C00031 | CHEBI:17234 | Glucose |
| G6P | C00092 | CHEBI:17665 | Glucose 6-phosphate |
| F6P | C00085 | CHEBI:16084 | Fructose 6-phosphate |
| F1,6BP | C00354 | CHEBI:16905 | Fructose 1,6-bisphosphate |
| DHAP | C00111 | CHEBI:16108 | Dihydroxyacetone phosphate |
| G3P | C00118 | CHEBI:17138 | Glyceraldehyde 3-phosphate |
| 1,3BPG | C00236 | CHEBI:16001 | 1,3-Bisphosphoglycerate |
| 3PG | C00197 | CHEBI:17794 | 3-Phosphoglycerate |
| 2PG | C00631 | CHEBI:17835 | 2-Phosphoglycerate |
| PEP | C00074 | CHEBI:18021 | Phosphoenolpyruvate |
| Pyruvate | C00022 | CHEBI:15361 | Pyruvic acid |

### Common Enzymes Quick Reference

#### Glycolysis Enzymes
| Enzyme | EC Number | KEGG Enzyme | KEGG Reaction |
|--------|-----------|-------------|---------------|
| Hexokinase | 2.7.1.1 | ec:2.7.1.1 | R00299 |
| Glucose-6-phosphate isomerase (PGI) | 5.3.1.9 | ec:5.3.1.9 | R00771 |
| Phosphofructokinase (PFK) | 2.7.1.11 | ec:2.7.1.11 | R00756 |
| Aldolase | 4.1.2.13 | ec:4.1.2.13 | R01068 |
| Triose-phosphate isomerase (TPI) | 5.3.1.1 | ec:5.3.1.1 | R01015 |
| GAPDH | 1.2.1.12 | ec:1.2.1.12 | R01061 |
| Phosphoglycerate kinase (PGK) | 2.7.2.3 | ec:2.7.2.3 | R01512 |
| Phosphoglycerate mutase (PGM) | 5.4.2.11 | ec:5.4.2.11 | R01518 |
| Enolase | 4.2.1.11 | ec:4.2.1.11 | R00658 |
| Pyruvate kinase (PK) | 2.7.1.40 | ec:2.7.1.40 | R00200 |

## Impact on SHYpn Analysis

### 1. Topology Panel
**Without Metadata:**
- Structural analysis (invariants, siphons, traps)
- Graph analysis (cycles, paths, hubs)
- Behavioral analysis (boundedness, liveness)

**With Metadata:**
- All of the above PLUS:
- Biological dependency analysis
- Regulatory pattern detection
- Pathway classification
- Enzyme-substrate relationship analysis

### 2. Enrichment Features
**Without Metadata:**
- Manual parameter entry only
- No database lookups
- Generic transition/place names

**With Metadata:**
- Automatic KEGG pathway enrichment
- BRENDA kinetic parameter lookup
- ChEBI compound information
- Cross-database linking

### 3. Report Generation
**Without Metadata:**
- Generic network statistics
- Abstract topology metrics

**With Metadata:**
- Biological context in all sections
- Enzyme classification summaries
- Pathway membership information
- Literature references (via database links)

### 4. Viability Analysis
**Without Metadata:**
- Mathematical steady-state analysis
- Flux analysis
- Escape detection

**With Metadata:**
- Biologically-relevant steady states
- Physiologically plausible parameter ranges
- Regulatory mechanism identification
- Metabolic control analysis

## Best Practices

### 1. Start with Core Metabolites
Begin by adding metadata to the most important compounds (ATP, ADP, NAD+, NADH, key pathway intermediates).

### 2. Use Consistent Identifiers
Always include both KEGG and ChEBI IDs when available. Some databases prefer one over the other.

### 3. Document Isoforms
If modeling tissue-specific or isoform-specific enzymes, note this in the metadata:
```json
{
  "ec_number": "2.7.1.1",
  "enzyme_name": "Hexokinase I",
  "isoform": "HK1",
  "tissue_specificity": "brain, muscle"
}
```

### 4. Include Compartment Information
For multi-compartment models:
```json
{
  "kegg_id": "C00002",
  "compound_name": "ATP",
  "compartment": "cytosol"
}
```

### 5. Version Your Models
When adding metadata to existing models, document the enrichment process:
```json
{
  "metadata": {
    "description": "ATP Hydrolysis - Enhanced with KEGG/ChEBI metadata",
    "enrichment_date": "2025-11-18",
    "enrichment_sources": ["KEGG", "ChEBI", "BRENDA"]
  }
}
```

## Example: Complete Model with Metadata

See the Foundation Examples for complete, fully-annotated models:
- `workspace/projects/Biochemical-Examples/01_ATP_Hydrolysis/model.shy`
- `workspace/projects/Biochemical-Examples/02_PGI_Equilibrium/model.shy`
- `workspace/projects/Biochemical-Examples/03_Hexokinase_MM/model.shy`

Each example demonstrates proper metadata structure and demonstrates the enhanced analysis capabilities.

## Automated Metadata Tools

### Within SHYpn
1. **KEGG Importer**: Automatically includes metadata when importing KEGG pathways
2. **SBML Parser**: Preserves annotations from SBML files
3. **Enrichment Tools**: Right-click → Enrich from KEGG/BRENDA

### External Resources
1. **UniChem** (https://www.ebi.ac.uk/unichem/): Cross-database identifier mapping
2. **PubChem** (https://pubchem.ncbi.nlm.nih.gov/): Additional compound information
3. **MetaNetX** (https://www.metanetx.org/): Reconciled metabolite identifiers

## Troubleshooting

### Q: Biological Analysis still shows no results
**A:** Check that:
1. Metadata is in the correct JSON format
2. IDs match the expected patterns (C##### for KEGG, CHEBI:##### for ChEBI)
3. You've run the Topology analyzers (they don't auto-run on model load)

### Q: Enrichment fails to find my compound
**A:** Try:
1. Verifying the KEGG/ChEBI ID is correct
2. Using compound synonyms or alternate names
3. Checking for stereochemistry (D-glucose vs L-glucose)
4. Looking for the protonated/deprotonated form

### Q: Multiple compounds share the same KEGG ID
**A:** This is normal for:
- Protonation states (use ChEBI for specific forms)
- Tautomers (specify in compound_name)
- Stereoisomers (add chirality information)

### Q: Should I add metadata to abstract transitions?
**A:** No. Only add enzyme metadata to transitions representing actual biochemical reactions. Abstract transitions (timers, switches, synchronization) should remain metadata-free.

## Summary

**Minimum Required for Biological Analysis:**
- Places: `kegg_id`, `chebi_id`, `compound_name`
- Transitions: `ec_number`, `enzyme_name`, `kegg_enzyme`

**Recommended for Full Analysis:**
- All minimum fields PLUS
- Reaction IDs (`kegg_reaction`)
- Compartment information
- Molecular formulas and weights
- Directional information for reversible reactions

By including this metadata, you unlock SHYpn's full analytical power and enable biological context throughout your modeling workflow.
