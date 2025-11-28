# SHYpn Examples

This directory contains demonstration examples showcasing the key features of the Extended Biological Petri Net formalism and SHYpn simulation capabilities.

## Example Overview

### 1. Simple Hexokinase Reaction (`01_hexokinase_simple.py`)

**Difficulty**: ⭐ Beginner  
**Duration**: ~10 seconds  
**Key Concepts**:
- Basic Extended Bio-PN structure (places, transitions, arcs)
- Continuous transitions with Michaelis-Menten kinetics
- Test arcs (enzyme catalysis without consumption)
- Atomic formula tracking and mass balance validation
- ODE-based simulation

**Biological Context**: Hexokinase catalyzes the first step of glycolysis, phosphorylating glucose to glucose-6-phosphate using ATP.

**Usage**:
```bash
cd examples/
python 01_hexokinase_simple.py
```

**Expected Output**:
- Console: Model statistics, mass balance check, final concentrations
- Plots: `hexokinase_simulation.pdf` (substrates and products)

---

### 2. Glycolysis Pathway (`02_glycolysis_pathway.py`)

**Difficulty**: ⭐⭐ Intermediate  
**Duration**: ~15 seconds  
**Key Concepts**:
- Multi-step metabolic pathways
- Reversible reactions (phosphoglucose isomerase)
- Shared intermediates (weak independence)
- Competitive coupling (shared ATP pool)
- Hill equation for cooperative binding

**Biological Context**: First 3 steps of glycolysis demonstrating sequential metabolic processing with energy investment phase.

**Usage**:
```bash
python 02_glycolysis_pathway.py
```

**Expected Output**:
- Console: Weak independence analysis (transition pair classifications)
- Plots: `glycolysis_simulation.pdf` (glucose consumption, intermediates, products, ATP/ADP)

**Key Results**:
- Weak independence detected between PGI and PFK reactions
- Competitive coupling between hexokinase and PFK (shared ATP)
- Demonstrates parallelization potential in metabolic pathways

---

### 3. Lac Operon Regulation (`03_lac_operon_regulation.py`)

**Difficulty**: ⭐⭐⭐ Advanced  
**Duration**: ~30 seconds  
**Key Concepts**:
- Hybrid stochastic/continuous simulation
- Gene expression dynamics (transcription + translation)
- Inhibitor arcs (catabolite repression)
- Regulatory coupling mode
- Feedback control via glucose depletion

**Biological Context**: Classic bacterial gene regulation system where glucose inhibits lactose metabolism genes until glucose is depleted.

**Usage**:
```bash
python 03_lac_operon_regulation.py
```

**Expected Output**:
- Console: Regulatory structure, transition type breakdown, final state
- Plots: `lac_operon_simulation.pdf` (gene expression, glucose, lactose metabolism, system overview)

**Key Results**:
- Stochastic gene expression (discrete mRNA/protein bursts)
- Continuous enzyme activity (deterministic kinetics)
- Dynamic transcription control via glucose threshold
- Demonstrates hybrid simulation paradigm

---

### 4. PFK Allosteric Inhibition (`04_pfk_allosteric_inhibition.py`)

**Difficulty**: ⭐⭐⭐ Advanced  
**Duration**: ~25 seconds  
**Key Concepts**:
- Allosteric regulation with multiple effectors
- Dynamic threshold computation (function of AMP concentration)
- Hill equation with high cooperativity (n=4)
- Feedback inhibition (product citrate)
- Regulatory coupling mode under weak independence

**Biological Context**: Phosphofructokinase (PFK) is the rate-limiting enzyme of glycolysis, exquisitely sensitive to cellular energy status via ATP/AMP ratio.

**Usage**:
```bash
python 04_pfk_allosteric_inhibition.py
```

**Expected Output**:
- Console: Weak independence analysis, regulatory modes, comparative scenarios
- Plots: `pfk_allosteric_simulation.pdf` (low vs high energy state comparison)

**Key Results**:
- **Low energy (high AMP)**: PFK activated → high FBP production (glycolysis proceeds)
- **High energy (high ATP)**: PFK inhibited → low FBP production (glycolysis suppressed)
- Dynamic threshold: `T(AMP) = 5.0 - 0.5*[AMP]`
- Demonstrates weak independence under regulatory coupling

---

## Running All Examples

To execute all examples sequentially:

```bash
cd examples/
for example in 0*.py; do
    echo "=========================================="
    echo "Running: $example"
    echo "=========================================="
    python "$example"
    echo ""
done
```

Or use the provided batch script:

```bash
bash run_all_examples.sh
```

---

## Example Progression

The examples are designed to progressively introduce Extended Bio-PN concepts:

1. **Basic structure** → Hexokinase (single reaction, enzyme catalysis)
2. **Pathway dynamics** → Glycolysis (sequential reactions, weak independence)
3. **Regulatory control** → Lac operon (inhibitor arcs, hybrid simulation)
4. **Allosteric regulation** → PFK (dynamic thresholds, multiple effectors)

---

## Generated Files

Each example produces plots in PDF and PNG formats:
- `hexokinase_simulation.pdf` / `.png`
- `glycolysis_simulation.pdf` / `.png`
- `lac_operon_simulation.pdf` / `.png`
- `pfk_allosteric_simulation.pdf` / `.png`

All plots use publication-quality vector graphics (PDF) and high-resolution raster images (PNG, 150 DPI).

---

## Extending Examples

### Loading from SBML

To load models from BioModels or other SBML sources:

```python
from shypn.io.sbml_importer import SBMLImporter

importer = SBMLImporter()
net = importer.load_file("path/to/model.xml")
```

### KEGG Pathway Import

To fetch and simulate pathways from KEGG:

```python
from shypn.integration.kegg_fetcher import KEGGFetcher

fetcher = KEGGFetcher()
net = fetcher.fetch_pathway("hsa00010")  # Glycolysis pathway
```

### BRENDA Kinetic Parameters

To enrich models with kinetic parameters from BRENDA:

```python
from shypn.integration.brenda_enricher import BRENDAEnricher

enricher = BRENDAEnricher()
enricher.enrich_transition(transition, ec_number="2.7.1.1")
```

---

## Dependencies

All examples require:
- Python 3.10+
- SHYpn (core package)
- NumPy, SciPy (numerical computing)
- Matplotlib (visualization)

Optional:
- `python-libsbml` (for SBML import in custom extensions)

---

## Troubleshooting

### "Module shypn not found"

Ensure SHYpn is installed in editable mode:
```bash
cd /path/to/shypn
pip install -e .
```

### "GTK not available"

Examples run headless (no GUI required). If you want to use the GUI:
```bash
# Ubuntu/Debian
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0
```

### Slow simulation

For large models or long time horizons:
- Reduce `t_end` or increase `dt` for faster (less accurate) simulation
- Use `stochastic_method="tau_leaping"` for approximate stochastic simulation
- Enable parallel simulation: `simulator.enable_parallel(num_cores=4)`

---

## References

- **Thesis**: Chapter 4 (formalism), Chapter 5 (weak independence), Chapter 7 (validation examples)
- **Paper**: "Weak Independence and Coupled Parallelism in Biological Petri Nets" (2025)
  - Available in `doc/papers/weak_independence_biopn.pdf`
- **BioModels**: https://www.ebi.ac.uk/biomodels/
- **KEGG**: https://www.genome.jp/kegg/pathway.html
- **BRENDA**: https://www.brenda-enzymes.org/

---

## Contributing Examples

To contribute new examples:

1. Follow naming convention: `XX_descriptive_name.py` (where XX is sequential number)
2. Include comprehensive docstring with:
   - Biological context
   - Key features demonstrated
   - Expected output
   - References (thesis chapter, paper figure)
3. Generate publication-quality plots (PDF + PNG)
4. Add entry to this README
5. Test on clean Python environment

---

## License

All examples are released under MIT License (see LICENSE file in repository root).

For research use, please cite:

```bibtex
@inproceedings{simao2025weak,
  title={Weak Independence and Coupled Parallelism in Biological Petri Nets},
  author={Simão, Eugênio},
  booktitle={[Conference/Journal Name]},
  year={2025},
  note={Software: \url{https://github.com/simao-eugenio/shypn}}
}
```
