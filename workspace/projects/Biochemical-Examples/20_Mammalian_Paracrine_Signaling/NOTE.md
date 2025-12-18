# Note: Example Format

This example (20_Mammalian_Paracrine_Signaling) uses **Python simulation scripts** rather than `.shy` model files.

## Why Python Format?

This example demonstrates the **13-tuple Bio-PN formalism** with signal place detection (Ψ) for mammalian cell communication, which requires:
1. Programmatic model construction
2. Automatic signal place detection via `QuorumSensingDetector`
3. Direct access to simulation results for validation
4. Complex parameter sets from clinical data

## How to Use

### Option 1: Run Python Simulation (Recommended)
```bash
cd /home/simao/projetos/shypn/workspace/projects/Biochemical-Examples/20_Mammalian_Paracrine_Signaling
PYTHONPATH=../../../../src:$PYTHONPATH python mammalian_paracrine_signaling.py
```

**Note:** This requires the shypn Python API to be available, which is currently under development.

### Option 2: Create .shy Model Manually
To use this example with the ShyPN GUI:
1. Open ShyPN application
2. Create a new Bio-Petri net model
3. Follow the model structure described in README.md:
   - 15 places (see "Places" section)
   - 12 transitions (see "Transitions" section)
   - Rate formulas as specified
4. The GUI should automatically detect signal places when you enter rate formulas

## Clinical Relevance

This model can be adapted for:
- **Cancer immunotherapy** (high-dose IL-2 for melanoma)
- **Autoimmune disease** (low-dose IL-2 for Type 1 diabetes, SLE)
- **Transplantation** (IL-2 modulation in graft tolerance)

See README.md for dosing parameters and clinical references.

## Future Work

A `.shy` model file version of this example will be added once:
- The signal place detection is integrated into the GUI
- The model can be properly visualized with hexagonal signal places
- The 13-tuple formalism is fully supported in the file format
- Clinical parameter sets can be easily loaded

## Current Status

This example serves as:
- **Proof of concept** for signal place detection in mammalian systems
- **Validation** of 13-tuple formalism across kingdoms (bacteria → mammals)
- **Clinical reference** for IL-2 immunotherapy modeling
- **Reference implementation** for future GUI integration

## See Also

- [README.md](README.md) - Complete biological and mathematical documentation
- [mammalian_paracrine_signaling.py](mammalian_paracrine_signaling.py) - Python simulation script
- [parameters.json](parameters.json) - Model parameters with clinical references
- [../../doc/quorum_sensing/](../../../../doc/quorum_sensing/) - Quorum sensing documentation

---

**Status:** Proof of concept / Reference implementation  
**Format:** Python script (awaiting GUI integration)  
**Phase:** Phase 2 of 7-phase implementation plan  
**Clinical Application:** IL-2 immunotherapy
