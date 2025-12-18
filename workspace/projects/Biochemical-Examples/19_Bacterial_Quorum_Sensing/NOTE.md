# Note: Example Format

This example (19_Bacterial_Quorum_Sensing) uses **Python simulation scripts** rather than `.shy` model files.

## Why Python Format?

This example demonstrates the **13-tuple Bio-PN formalism** with signal place detection (Ψ), which requires:
1. Programmatic model construction
2. Automatic signal place detection via `QuorumSensingDetector`
3. Direct access to simulation results for validation

## How to Use

### Option 1: Run Python Simulation (Recommended)
```bash
cd /home/simao/projetos/shypn/workspace/projects/Biochemical-Examples/19_Bacterial_Quorum_Sensing
PYTHONPATH=../../../../src:$PYTHONPATH python vfischeri_quorum_sensing.py
```

**Note:** This requires the shypn Python API to be available, which is currently under development.

### Option 2: Create .shy Model Manually
To use this example with the ShyPN GUI:
1. Open ShyPN application
2. Create a new Bio-Petri net model
3. Follow the model structure described in README.md:
   - 13 places (see "Places" section)
   - 10 transitions (see "Transitions" section)
   - Rate formulas as specified
4. The GUI should automatically detect signal places when you enter rate formulas

## Future Work

A `.shy` model file version of this example will be added once:
- The signal place detection is integrated into the GUI
- The model can be properly visualized with hexagonal signal places
- The 13-tuple formalism is fully supported in the file format

## Current Status

This example serves as:
- **Proof of concept** for signal place detection algorithm
- **Validation** of 13-tuple formalism
- **Documentation** of quorum sensing modeling approach
- **Reference implementation** for future GUI integration

## See Also

- [README.md](README.md) - Complete biological and mathematical documentation
- [vfischeri_quorum_sensing.py](vfischeri_quorum_sensing.py) - Python simulation script
- [parameters.json](parameters.json) - Model parameters
- [../../doc/quorum_sensing/](../../../../doc/quorum_sensing/) - Quorum sensing documentation

---

**Status:** Proof of concept / Reference implementation  
**Format:** Python script (awaiting GUI integration)  
**Phase:** Phase 2 of 7-phase implementation plan
