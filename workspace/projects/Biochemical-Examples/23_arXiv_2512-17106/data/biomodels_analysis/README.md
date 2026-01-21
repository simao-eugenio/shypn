# BioModels Dependency Classification Data

This directory contains results from analyzing 100 BioModels database models.

## Data Not Included

The actual BioModels SBML files are **not included** in this repository because:
- They are externally maintained by EBI BioModels Database
- Total size exceeds 100+ MB
- They can be downloaded from: https://www.ebi.ac.uk/biomodels/

## Reproduced Results

To reproduce the analysis in Table 3 of the paper:

1. Download models from BioModels:
   - BIOMD0000000001 through BIOMD0000000100
   - BIOMD0000000200 through BIOMD0000000299
   - BIOMD0000000300 through BIOMD0000000399  
   - BIOMD0000000400 through BIOMD0000000499

2. Run the classification script:
   ```bash
   python ../scripts/classify_all_dependencies.py \
       --sbml-dir /path/to/biomodels \
       --output classification_results.csv
   ```

3. Results: 93 models successfully analyzed (7 had import errors)
   - Total pairs: 102,960
   - Weakly independent: 96.93%
   - Competitive (conflicts): 3.07%

## Paper Results

The published results (Table 3) showed:
- **1,775 species** across 100 models
- **2,234 reactions** across 100 models
- **93.06%** strongly independent (no shared places)
- **3.48%** convergent coupling (shared outputs)
- **0.38%** regulatory coupling (shared catalysts)
- **3.07%** competitive (true conflicts)

**Key finding:** 96.93% of transition pairs can execute in parallel.
