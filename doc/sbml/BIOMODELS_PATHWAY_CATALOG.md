# BioModels Pathway Catalog for Testing

**Purpose**: Curated list of SBML models from BioModels Database for testing Shypn's pathway import and simulation capabilities.

**Organization**: Models are organized from simple to complex based on:
- Number of species (places)
- Number of reactions (transitions)
- Kinetic complexity
- Biological system type

**Source**: [BioModels Database](https://www.ebi.ac.uk/biomodels/)

---

## Simple Models (Ideal for Initial Testing)

### 1. BIOMD0000000001 - Edelstein1996 - EPSP ACh event
**Species**: 3  
**Reactions**: 3  
**Type**: Neurotransmission - Acetylcholine receptor  
**Description**: Simple model of excitatory postsynaptic potential (EPSP)  
**Good for**: Basic import testing, simple kinetics  
**Complexity**: ⭐ (Very Simple)

```
Download URL:
https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000001.4?filename=BIOMD0000000001_url.xml
```

---

### 2. BIOMD0000000002 - Kholodenko2000 - Ultrasensitivity and negative feedback bring oscillations
**Species**: 11  
**Reactions**: 19  
**Type**: Signal transduction - MAPK cascade  
**Description**: MAPK cascade with negative feedback producing oscillations  
**Good for**: Testing feedback loops, oscillatory behavior  
**Complexity**: ⭐⭐ (Simple)

```
Download URL:
https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000002.4?filename=BIOMD0000000002_url.xml
```

---

### 3. BIOMD0000000012 - Elowitz2000 - Repressilator
**Species**: 6  
**Reactions**: 12  
**Type**: Genetic regulatory network - Synthetic oscillator  
**Description**: Classic synthetic genetic oscillator with 3 repressors  
**Good for**: Testing oscillations, genetic networks, parameter sensitivity  
**Complexity**: ⭐⭐ (Simple)

**⭐ RECOMMENDED FOR FIRST TEST** - Well-documented, clear oscillatory dynamics

```
Download URL:
https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000012.2?filename=BIOMD0000000012_url.xml
```

**Expected Behavior**:
- Oscillating protein levels (period ~100-200 minutes)
- Clear phase relationships between repressors
- Good test for continuous Petri net dynamics

---

### 4. BIOMD0000000021 - Vilar2002 - Circadian oscillator
**Species**: 16  
**Reactions**: 16  
**Type**: Circadian rhythm - Gene regulatory network  
**Description**: Mammalian circadian clock model  
**Good for**: Testing circadian rhythms, gene regulation  
**Complexity**: ⭐⭐ (Simple-Medium)

```
Download URL:
https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000021.2?filename=BIOMD0000000021_url.xml
```

---

## Medium Complexity Models

### 5. BIOMD0000000010 - Kofahl2004 - MAPK cascade
**Species**: 19  
**Reactions**: 18  
**Type**: Signal transduction - MAPK pathway  
**Description**: Detailed MAPK cascade with scaffolding proteins  
**Good for**: Testing signal transduction, enzyme cascades  
**Complexity**: ⭐⭐⭐ (Medium)

```
Download URL:
https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000010.2?filename=BIOMD0000000010_url.xml
```

---

### 6. BIOMD0000000051 - Goldbeter1991 - Mitotic oscillator
**Species**: 4  
**Reactions**: 11  
**Type**: Cell cycle - Mitotic oscillations  
**Description**: Minimal cascade model for cell cycle oscillations  
**Good for**: Testing bistability, cell cycle dynamics  
**Complexity**: ⭐⭐⭐ (Medium)

```
Download URL:
https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000051.2?filename=BIOMD0000000051_url.xml
```

---

### 7. BIOMD0000000064 - Goldbeter1995 - Calcium oscillations
**Species**: 3  
**Reactions**: 8  
**Type**: Calcium signaling - Oscillations  
**Description**: Model for calcium oscillations based on calcium-induced calcium release  
**Good for**: Testing calcium dynamics, fast oscillations  
**Complexity**: ⭐⭐⭐ (Medium)

```
Download URL:
https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000064.2?filename=BIOMD0000000064_url.xml
```

---

### 8. BIOMD0000000206 - Teusink2000 - Glycolysis in yeast
**Species**: 23  
**Reactions**: 24  
**Type**: Metabolism - Glycolysis pathway  
**Description**: Detailed glycolysis model in Saccharomyces cerevisiae  
**Good for**: Testing metabolic pathways, enzyme kinetics  
**Complexity**: ⭐⭐⭐ (Medium)

**⭐ RECOMMENDED FOR METABOLIC TESTING**

```
Download URL:
https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000206.2?filename=BIOMD0000000206_url.xml
```

---

## Complex Models

### 9. BIOMD0000000019 - Schoeberl2002 - EGF-EGFR signaling
**Species**: 34  
**Reactions**: 47  
**Type**: Signal transduction - Growth factor signaling  
**Description**: EGF receptor activation and downstream signaling  
**Good for**: Testing complex signaling networks, receptor dynamics  
**Complexity**: ⭐⭐⭐⭐ (Complex)

```
Download URL:
https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000019.2?filename=BIOMD0000000019_url.xml
```

---

### 10. BIOMD0000000028 - Levchenko2000 - MAPK kinetics
**Species**: 23  
**Reactions**: 48  
**Type**: Signal transduction - MAPK cascade  
**Description**: Detailed MAPK signaling with multiple feedback loops  
**Good for**: Testing complex kinetics, multiple feedback loops  
**Complexity**: ⭐⭐⭐⭐ (Complex)

```
Download URL:
https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000028.2?filename=BIOMD0000000028_url.xml
```

---

### 11. BIOMD0000000033 - Novak2001 - Cell cycle
**Species**: 19  
**Reactions**: 25  
**Type**: Cell cycle - Eukaryotic division cycle  
**Description**: Comprehensive model of budding yeast cell cycle  
**Good for**: Testing cell cycle dynamics, checkpoint controls  
**Complexity**: ⭐⭐⭐⭐ (Complex)

```
Download URL:
https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000033.3?filename=BIOMD0000000033_url.xml
```

---

### 12. BIOMD0000000091 - Edelstein1996 - Calcium signaling
**Species**: 7  
**Reactions**: 20  
**Type**: Calcium signaling - Store-operated channels  
**Description**: Calcium dynamics with store-operated calcium entry  
**Good for**: Testing calcium homeostasis, compartmental models  
**Complexity**: ⭐⭐⭐⭐ (Complex)

```
Download URL:
https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000091.2?filename=BIOMD0000000091_url.xml
```

---

## Very Complex Models (Advanced Testing)

### 13. BIOMD0000000003 - Goldbeter1991 - Minimal model for mitotic oscillator
**Species**: 51  
**Reactions**: 75  
**Type**: Cell cycle - Full mitotic cycle  
**Description**: Comprehensive cell cycle model with checkpoints  
**Good for**: Stress testing, large network visualization  
**Complexity**: ⭐⭐⭐⭐⭐ (Very Complex)

```
Download URL:
https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000003.3?filename=BIOMD0000000003_url.xml
```

---

### 14. BIOMD0000000234 - Kholodenko1999 - EGFR signaling
**Species**: 58  
**Reactions**: 94  
**Type**: Signal transduction - Full EGFR pathway  
**Description**: Comprehensive EGF receptor signaling to MAPK  
**Good for**: Large network testing, performance benchmarking  
**Complexity**: ⭐⭐⭐⭐⭐ (Very Complex)

```
Download URL:
https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000234.2?filename=BIOMD0000000234_url.xml
```

---

### 15. BIOMD0000000237 - Markevich2004 - MAPK cascade with distributive mechanism
**Species**: 42  
**Reactions**: 77  
**Type**: Signal transduction - Distributive MAPK  
**Description**: MAPK cascade with distributive double phosphorylation  
**Good for**: Testing complex enzyme mechanisms, ultrasensitivity  
**Complexity**: ⭐⭐⭐⭐⭐ (Very Complex)

```
Download URL:
https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000237.2?filename=BIOMD0000000237_url.xml
```

---

## Specialized Models

### Stochastic/Small Molecule Numbers

#### BIOMD0000000061 - Tyson1991 - Cell cycle (Minimal)
**Species**: 2  
**Reactions**: 6  
**Type**: Cell cycle - Minimal model  
**Description**: Simplest cell cycle oscillator model  
**Good for**: Testing minimal oscillators, stochastic effects  
**Complexity**: ⭐ (Very Simple)

```
Download URL:
https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000061.2?filename=BIOMD0000000061_url.xml
```

---

### Metabolic Pathways

#### BIOMD0000000035 - Nakakuki2010 - Insulin signaling
**Species**: 31  
**Reactions**: 75  
**Type**: Metabolism - Insulin pathway  
**Description**: Insulin-induced AKT signaling pathway  
**Good for**: Testing metabolic signaling, insulin dynamics  
**Complexity**: ⭐⭐⭐⭐ (Complex)

```
Download URL:
https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000035.2?filename=BIOMD0000000035_url.xml
```

---

### Gene Regulatory Networks

#### BIOMD0000000026 - Gardner2000 - Genetic toggle switch
**Species**: 4  
**Reactions**: 6  
**Type**: Synthetic biology - Bistable switch  
**Description**: Classic genetic toggle switch showing bistability  
**Good for**: Testing bistability, synthetic biology designs  
**Complexity**: ⭐⭐ (Simple)

```
Download URL:
https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000026.2?filename=BIOMD0000000026_url.xml
```

---

## Testing Recommendations

### Phase 1: Basic Import Testing
Start with these to verify import functionality:
1. **BIOMD0000000001** - Very simple (3 species, 3 reactions)
2. **BIOMD0000000012** - Repressilator (6 species, 12 reactions)
3. **BIOMD0000000026** - Toggle switch (4 species, 6 reactions)

**Goal**: Verify SBML parsing, initial markings, basic visualization

---

### Phase 2: Dynamics Verification
Test different dynamical behaviors:
1. **BIOMD0000000012** - Repressilator (oscillations)
2. **BIOMD0000000026** - Toggle switch (bistability)
3. **BIOMD0000000051** - Mitotic oscillator (complex oscillations)
4. **BIOMD0000000064** - Calcium oscillations (fast dynamics)

**Goal**: Verify simulation accuracy, plot functionality, different time scales

---

### Phase 3: Locality Analysis
Test locality detection with different patterns:
1. **BIOMD0000000002** - MAPK cascade (normal localities: P→T→P)
2. **BIOMD0000000012** - Repressilator (multiple-source pattern: T→P←T)
3. **BIOMD0000000206** - Glycolysis (linear pathways)

**Goal**: Verify locality concept implementation, analyses tab functionality

---

### Phase 4: Complex Networks
Test scalability and performance:
1. **BIOMD0000000206** - Glycolysis (23 species, 24 reactions)
2. **BIOMD0000000019** - EGF signaling (34 species, 47 reactions)
3. **BIOMD0000000234** - Full EGFR pathway (58 species, 94 reactions)

**Goal**: Performance testing, layout quality, user experience with large models

---

## Model Categories

### By Biological System

**Metabolism**:
- BIOMD0000000206 - Glycolysis
- BIOMD0000000035 - Insulin signaling

**Signal Transduction**:
- BIOMD0000000002 - MAPK oscillations
- BIOMD0000000010 - MAPK cascade
- BIOMD0000000019 - EGF-EGFR signaling
- BIOMD0000000028 - MAPK kinetics
- BIOMD0000000234 - Full EGFR pathway
- BIOMD0000000237 - Distributive MAPK

**Cell Cycle**:
- BIOMD0000000033 - Novak model
- BIOMD0000000051 - Goldbeter mitotic oscillator
- BIOMD0000000061 - Minimal Tyson model

**Gene Regulation**:
- BIOMD0000000012 - Repressilator
- BIOMD0000000021 - Circadian clock
- BIOMD0000000026 - Toggle switch

**Calcium Signaling**:
- BIOMD0000000064 - Calcium oscillations
- BIOMD0000000091 - Store-operated calcium entry

**Neurotransmission**:
- BIOMD0000000001 - EPSP ACh event

---

### By Dynamic Behavior

**Oscillatory**:
- BIOMD0000000012 - Repressilator (genetic oscillations)
- BIOMD0000000002 - MAPK oscillations
- BIOMD0000000021 - Circadian rhythm
- BIOMD0000000051 - Mitotic oscillations
- BIOMD0000000064 - Calcium oscillations

**Bistable**:
- BIOMD0000000026 - Toggle switch
- BIOMD0000000051 - Mitotic oscillator (also bistable)

**Steady-State**:
- BIOMD0000000206 - Glycolysis (flux)
- BIOMD0000000019 - EGF signaling (adaptation)

**Transient Response**:
- BIOMD0000000001 - EPSP (pulse response)
- BIOMD0000000028 - MAPK activation

---

### By Network Topology

**Linear Cascades**:
- BIOMD0000000010 - MAPK cascade
- BIOMD0000000206 - Glycolysis

**Feedback Loops**:
- BIOMD0000000002 - Negative feedback
- BIOMD0000000012 - Repressilator (cyclic feedback)
- BIOMD0000000028 - Multiple feedback

**Mutual Inhibition**:
- BIOMD0000000026 - Toggle switch

**Complex Networks**:
- BIOMD0000000019 - EGF signaling
- BIOMD0000000234 - Full EGFR pathway

---

## Download Script

Use this bash script to download all recommended models:

```bash
#!/bin/bash
# Download BioModels for Shypn testing

MODELS_DIR="data/biomodels"
mkdir -p "$MODELS_DIR"

# Simple models
wget -O "$MODELS_DIR/BIOMD0000000001.xml" \
  "https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000001.4?filename=BIOMD0000000001_url.xml"

wget -O "$MODELS_DIR/BIOMD0000000012.xml" \
  "https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000012.2?filename=BIOMD0000000012_url.xml"

wget -O "$MODELS_DIR/BIOMD0000000026.xml" \
  "https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000026.2?filename=BIOMD0000000026_url.xml"

# Medium models
wget -O "$MODELS_DIR/BIOMD0000000002.xml" \
  "https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000002.4?filename=BIOMD0000000002_url.xml"

wget -O "$MODELS_DIR/BIOMD0000000064.xml" \
  "https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000064.2?filename=BIOMD0000000064_url.xml"

wget -O "$MODELS_DIR/BIOMD0000000206.xml" \
  "https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000206.2?filename=BIOMD0000000206_url.xml"

# Complex models
wget -O "$MODELS_DIR/BIOMD0000000019.xml" \
  "https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000019.2?filename=BIOMD0000000019_url.xml"

echo "Download complete! Models saved to $MODELS_DIR/"
```

Save as `scripts/download_biomodels.sh` and run:
```bash
chmod +x scripts/download_biomodels.sh
./scripts/download_biomodels.sh
```

---

## Python Import Script

Automated import and validation script:

```python
#!/usr/bin/env python3
"""
Test BioModels import in Shypn
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.data.pathway import SBMLParser, PathwayPostProcessor, PathwayConverter

BIOMODELS = [
    ("BIOMD0000000001", "data/biomodels/BIOMD0000000001.xml"),
    ("BIOMD0000000012", "data/biomodels/BIOMD0000000012.xml"),
    ("BIOMD0000000026", "data/biomodels/BIOMD0000000026.xml"),
    ("BIOMD0000000206", "data/biomodels/BIOMD0000000206.xml"),
]

def test_import(model_id, filepath):
    """Test import of single model."""
    print(f"\n{'='*70}")
    print(f"Testing: {model_id}")
    print(f"{'='*70}")
    
    if not os.path.exists(filepath):
        print(f"❌ File not found: {filepath}")
        return False
    
    try:
        # Parse SBML
        print("Parsing SBML...")
        parser = SBMLParser(filepath)
        pathway = parser.parse()
        print(f"✓ Parsed: {len(pathway.species)} species, {len(pathway.reactions)} reactions")
        
        # Post-process
        print("Post-processing...")
        postprocessor = PathwayPostProcessor(spacing=150.0, scale_factor=10.0)
        processed = postprocessor.process(pathway)
        print(f"✓ Processed: {len(processed.positions)} positions assigned")
        
        # Check initial markings
        total_tokens = sum(s.initial_tokens for s in processed.species)
        print(f"✓ Initial markings: {total_tokens} total tokens")
        
        # Convert to Petri net
        print("Converting to Petri net...")
        converter = PathwayConverter()
        document = converter.convert(processed)
        
        place_count, transition_count, arc_count = document.get_object_count()
        print(f"✓ Petri net: {place_count} places, {transition_count} transitions, {arc_count} arcs")
        
        # Verify initial markings applied
        place_tokens = sum(p.tokens for p in document.places)
        print(f"✓ Place tokens: {place_tokens} (matches initial_tokens: {place_tokens == total_tokens})")
        
        print(f"✅ {model_id} imported successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("BioModels Import Testing")
    print("="*70)
    
    results = []
    for model_id, filepath in BIOMODELS:
        success = test_import(model_id, filepath)
        results.append((model_id, success))
    
    # Summary
    print(f"\n{'='*70}")
    print("SUMMARY")
    print(f"{'='*70}")
    
    for model_id, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {model_id}")
    
    passed = sum(1 for _, s in results if s)
    total = len(results)
    print(f"\nTotal: {passed}/{total} passed")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())
```

Save as `tests/test_biomodels_import.py` and run:
```bash
python3 tests/test_biomodels_import.py
```

---

## Expected Results

### BIOMD0000000012 - Repressilator

**Initial Markings** (with scale_factor=10.0):
- PX (protein X): ~10 tokens
- PY (protein Y): ~10 tokens  
- PZ (protein Z): ~10 tokens
- mRNAX, mRNAY, mRNAZ: ~0-5 tokens each

**Simulation Behavior**:
- Oscillations with period ~100-200 simulation units
- Proteins oscillate out of phase (120° apart)
- Clear periodic behavior in plots

**Localities**:
- Multiple-source pattern: T→P←T (shared mRNA/protein places)
- All transitions should have valid localities
- Analyses tab should show all transitions

---

### BIOMD0000000206 - Glycolysis

**Initial Markings** (with scale_factor=10.0):
- Glucose: ~50-100 tokens (high concentration)
- ATP, ADP: ~20-30 tokens (medium)
- Intermediates: ~5-10 tokens (low)
- Products: ~0 tokens (empty)

**Simulation Behavior**:
- Steady-state flux through pathway
- Glucose consumed, products accumulate
- Clear metabolic flow

**Localities**:
- Linear cascade pattern: P→T→P→T→P
- Normal localities (inputs and outputs)
- Good test for sequential reactions

---

## References

- **BioModels Database**: https://www.ebi.ac.uk/biomodels/
- **SBML Specification**: http://sbml.org/
- **Model Documentation**: Each model page has detailed documentation, references, and parameter values

---

## Notes

1. **Scale Factor**: Default is 1.0 in UI. For most models, use 10.0 for better token counts.
2. **Simulation Time**: Different models need different time scales:
   - Repressilator: 200-300 time units
   - Calcium oscillations: 10-50 time units
   - Glycolysis: 100-500 time units
3. **Compartments**: Some models have multiple compartments (cytosol, nucleus, etc.)
4. **Units**: SBML concentrations typically in mM (millimolar)

---

**Last Updated**: October 12, 2025  
**Shypn Version**: Development (feature/property-dialogs-and-simulation-palette)  
**BioModels Database Version**: Current as of October 2025
