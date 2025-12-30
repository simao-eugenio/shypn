# Multi-Compartment SBML Test Models

This directory contains test SBML models for validating the modular Bio-PN architecture.

## Test Models

### 1. Yeast Glycolysis (Cytoplasm/Mitochondria)
**Model**: Teusink et al. (2000) - Glycolysis in yeast
**Source**: BioModels Database - BIOMD0000000064
**Compartments**: cytoplasm, mitochondrion
**Expected**: Module detection, ATP/ADP signals between compartments

### 2. Eukaryotic Gene Expression (Nucleus/Cytoplasm)
**Model**: Transcription-Translation model
**Compartments**: nucleus, cytoplasm
**Expected**: mRNA as signal from nucleus to cytoplasm

### 3. Quorum Sensing (Multi-Cellular)
**Model**: Bacterial quorum sensing (Pseudomonas aeruginosa)
**Compartments**: cell1, cell2, extracellular
**Expected**: Signaling molecules (AHL) crossing cell boundaries

## Testing Checklist

For each model, verify:
- ✓ Compartments correctly mapped to modules
- ✓ Cross-compartment species identified as signal places
- ✓ Module visualization with colored boxes
- ✓ Signal place visualization with Ψ symbols
- ✓ Dashed arcs for cross-module connections
- ✓ Module collapse/expand functionality
- ✓ Simulation respects signal semantics (read-only, broadcast)
- ✓ Module analysis CLI generates correct metrics

