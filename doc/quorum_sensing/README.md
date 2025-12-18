# Quorum Sensing Documentation

This directory contains comprehensive documentation for the quorum sensing (signal place detection) feature in SHYpn.

## 🎯 Quick Links

- **[SUMMARY.md](SUMMARY.md)** - Quick summary (start here!)
- **[STATUS_REPORT.md](STATUS_REPORT.md)** - Detailed progress report (90% complete)
- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** - 7-phase roadmap
- **[THEORY.md](THEORY.md)** - Mathematical formalism

## 📦 What's Available Now (90% Complete)

### ✅ Core Functionality
- Signal place detection (automatic, no user input needed)
- 13-tuple Bio-PN formalism with Ψ component
- Integration with stochastic behavior engine
- Unit tests (9/9 passing)

### ✅ Example Models
1. **Example 19:** *V. fischeri* quorum sensing ([README](../../workspace/projects/Biochemical-Examples/19_Bacterial_Quorum_Sensing/README.md))
2. **Example 20:** Mammalian IL-2 paracrine signaling ([README](../../workspace/projects/Biochemical-Examples/20_Mammalian_Paracrine_Signaling/README.md))

### 🚧 Coming Soon (Phase 3)
- UI visualization (signal places as hexagons)
- Additional examples (plant, fungal)

## 📚 Documentation Structure

### Core Documentation
- **[SUMMARY.md](SUMMARY.md)** - Quick reference guide
- **[STATUS_REPORT.md](STATUS_REPORT.md)** - Comprehensive progress report
- **[IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)** - Complete implementation plan (85% → 100%)
- **[THEORY.md](THEORY.md)** - Mathematical formalism and 13-tuple extension
- **[FORMALISM.tex](FORMALISM.tex)** - Formal LaTeX paper on 13-tuple extension (academic)

### Examples
See `workspace/projects/Biochemical-Examples/` directory:
- `19_Bacterial_Quorum_Sensing/` - *V. fischeri* bioluminescence
- `20_Mammalian_Paracrine_Signaling/` - T cell IL-2 system

## 🔬 What is Quorum Sensing?

**Quorum sensing** is a cell density-dependent communication mechanism where cells produce, release, and detect signaling molecules called **autoinducers**. When the signal concentration reaches a threshold, it triggers coordinated behavior changes in the population.

### In SHYpn's Context

We generalize "quorum sensing" to mean **signal place detection** (Ψ component):
- Places referenced in rate formulas
- Without arc connections (input, output, or regulatory)
- Representing non-local chemical dependencies

This applies to:
- **Bacterial:** AHL quorum sensing
- **Mammalian:** Cytokine/growth factor signaling
- **Neural:** Neurotransmitter release
- **Fungal:** Density-dependent morphology
- **Plant:** Ethylene/volatile signaling

## 🧮 Mathematical Framework

### 13-Tuple Bio-PN Extension

```
BioPN = (P, T, F, W, M₀, K, Φ, Σ, Θ, Δ, τ, ρ, Ψ)
                                            ^^^
                                         NEW: Signal places
```

**Signal Place Definition:**
```
Ψ: T → 2^P

Ψ(t) = ReferencedPlaces(Φ(t)) \ (•t ∪ t• ∪ Σ(t))
```

Where:
- `Φ(t)` = Rate function of transition t
- `•t` = Input places (consumed)
- `t•` = Output places (produced)
- `Σ(t)` = Regulatory places (test/inhibitor arcs)
- `Ψ(t)` = **Signal places (sensed, non-local)**

## 🎯 Quick Start

### 1. Automatic Detection

Signal places are detected automatically when importing SBML or parsing rate formulas:

```python
from shypn.analysis.quorum_sensing import detect_and_annotate_signal_places

# Detect signal places in model
signal_map = detect_and_annotate_signal_places(model)

# Check results
for transition_id, signal_place_ids in signal_map.items():
    print(f"{transition_id} senses: {signal_place_ids}")
```

### 2. Check Transition Annotation

```python
transition = model.transitions['T5']

if transition.is_environment_aware:
    print(f"Signal dependencies: {transition.signal_places}")
    # Output: Signal dependencies: ['AHL', 'AI2']
```

### 3. Get Signal Network Topology

```python
from shypn.analysis.quorum_sensing import get_signal_network

network = get_signal_network(model)
# Returns: {'AHL': ['T5', 'T7'], 'AI2': ['T3']}
```

### 4. Classify QS Modules

```python
from shypn.analysis.quorum_sensing import classify_quorum_sensing_modules

modules = classify_quorum_sensing_modules(model)

for module in modules:
    print(f"Signal: {module['signal_place']}")
    print(f"Type: {module['module_type']}")  # autocrine/paracrine/external
    print(f"Producers: {module['producer_transitions']}")
    print(f"Sensors: {module['sensor_transitions']}")
```

## 🏗️ Implementation Status

| Component | Status | Priority |
|-----------|--------|----------|
| Core detection algorithm | ✅ Complete | - |
| Data structures (Transition) | ✅ Complete | - |
| Module classification | ✅ Complete | - |
| Stochastic integration | ⚠️ Missing method | 🔴 CRITICAL |
| Example models | ❌ Not started | 🔴 HIGH |
| Unit tests | ⏳ Partial | 🟡 MEDIUM |
| UI visualization | ❌ Not started | 🟡 MEDIUM |
| Documentation | ⏳ In progress | 🟡 MEDIUM |

**Current:** 85% complete  
**Target:** 100% production-ready

See [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for complete roadmap.

## 📖 Documentation Files

### For Users

1. **[USER_GUIDE.md](USER_GUIDE.md)**
   - What are signal places?
   - When to use them
   - Step-by-step modeling tutorial
   - Troubleshooting common issues

2. **[BACTERIAL_EXAMPLE.md](BACTERIAL_EXAMPLE.md)**
   - Complete *V. fischeri* model
   - Biological background
   - Model structure
   - Expected behavior
   - Validation against literature

3. **[MAMMALIAN_EXAMPLE.md](MAMMALIAN_EXAMPLE.md)**
   - T-cell IL-2 autocrine signaling
   - Demonstrates cross-kingdom applicability
   - Paracrine vs autocrine patterns

### For Developers

1. **[API_REFERENCE.md](API_REFERENCE.md)**
   - `QuorumSensingDetector` class
   - Public functions
   - Return types
   - Usage examples

2. **[DETECTION_ALGORITHM.md](DETECTION_ALGORITHM.md)**
   - Algorithm pseudocode
   - Implementation details
   - Performance considerations
   - Edge cases

3. **[TESTING_STRATEGY.md](TESTING_STRATEGY.md)**
   - Test coverage requirements
   - Unit test examples
   - Integration test scenarios
   - Validation methodology

### For Researchers

1. **[THEORY.md](THEORY.md)**
   - 13-tuple formalism
   - Mathematical proofs
   - Relationship to classical Bio-PNs
   - Biological justification
   - Literature references

2. **[CROSS_KINGDOM.md](CROSS_KINGDOM.md)**
   - Inter-organism signaling
   - Bacteria-fungus interactions
   - Multi-species models

## 🔗 Related Documentation

### Core SHYpn Docs
- [Main README](../../README.md) - Project overview
- [User Guide](../USER_GUIDE.md) - General usage
- [SBML Import](../SBML_IMPORT.md) - Model import

### Papers & Theory
- [Foundation Paper](../papers/foundation/) - 12-tuple Bio-PN
- [Bioinformatics Paper](../papers/bioinformatics/) - Weak independence
- [Tau-Leaping](../papers/tau-leaping/) - Stochastic simulation

### Examples
- [Biochemical Examples](../../workspace/projects/Biochemical-Examples/) - Model library
- Example 17: Lac Operon (similar regulatory patterns)
- Example 19: Bacterial QS (planned)
- Example 20: Mammalian Paracrine (planned)

## 🐛 Known Issues

1. **Missing Integration** (CRITICAL)
   - `StochasticBehavior._detect_signal_places()` not implemented
   - Called at line 83 but method missing
   - **Fix:** See Phase 1 in IMPLEMENTATION_PLAN.md

2. **No Example Models** (HIGH)
   - No demonstration of feature
   - Users cannot test functionality
   - **Fix:** Create Examples 19 & 20

3. **No Visual UI** (MEDIUM)
   - Signal dependencies not rendered
   - No topology panel display
   - **Fix:** See Phase 5 in IMPLEMENTATION_PLAN.md

## 🚀 Quick Links

- **Implementation:** [../IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md)
- **Source Code:** [../../src/shypn/analysis/quorum_sensing.py](../../src/shypn/analysis/quorum_sensing.py)
- **Tests:** [../../tests/test_quorum_sensing.py](../../tests/test_quorum_sensing.py) (to be created)
- **Examples:** [../../workspace/projects/Biochemical-Examples/19_*](../../workspace/projects/Biochemical-Examples/)

## 📝 Contributing

To contribute to quorum sensing documentation:

1. Read [THEORY.md](THEORY.md) for mathematical background
2. Review [API_REFERENCE.md](API_REFERENCE.md) for implementation
3. Check [IMPLEMENTATION_PLAN.md](IMPLEMENTATION_PLAN.md) for open tasks
4. Submit examples or improvements

## 📚 References

### Bacterial Quorum Sensing
- Miller & Bassler (2001). "Quorum sensing in bacteria." *Annu Rev Microbiol* 55:165-199
- Waters & Bassler (2005). "Quorum sensing: Cell-to-cell communication in bacteria." *Annu Rev Cell Dev Biol* 21:319-346
- Ng & Bassler (2009). "Bacterial quorum-sensing network architectures." *Annu Rev Genet* 43:197-222

### Eukaryotic Cell Signaling
- Keller & Surette (2006). "Communication in bacteria: an ecological and evolutionary perspective." *Nat Rev Microbiol* 4:249-258
- Albuquerque & Casadevall (2012). "Quorum sensing in fungi." *PLOS Pathog* 8:e1002783
- Hornby et al. (2001). "Quorum sensing in the dimorphic fungus *Candida albicans*." *Genes Dev* 15:2585-2597

### Petri Net Theory
- Heiner et al. (2008). "Petri nets for systems and synthetic biology." *LNCS* 5016:215-264
- Chaouiya (2007). "Petri net modelling of biological networks." *Brief Bioinform* 8:210-219
- Reddy et al. (1993). "Petri net representations in metabolic pathways." *ISMB* 1:328-336

---

**Documentation Version:** 1.0  
**Last Updated:** December 18, 2025  
**Status:** In progress (85% complete)  
**Maintainer:** Eugênio Simão
