# Thesis Figure Export System

Automated export of SHYpn Petri Net models as publication-quality figures for the thesis.

## Features

- **Multiple formats**: PNG (raster), PDF (vector), SVG (editable), TikZ (LaTeX-native)
- **High quality**: 300 DPI PNG, vector formats for perfect scaling
- **Batch export**: Process all example models at once
- **LaTeX integration**: Direct TikZ code generation for native LaTeX figures
- **Automatic bounds**: Smart cropping with configurable margins

## Installation

Ensure pycairo is installed:

```bash
pip install pycairo
```

## Usage

### Export Single Model

```bash
# Export to all formats (PNG, PDF, SVG, TikZ)
python scripts/export_thesis_figures.py --model examples/01_atp_synthesis.shy --output doc/thesis/latex/gfx/

# Export specific format only
python scripts/export_thesis_figures.py --model examples/09_glycolysis.shy --format pdf --output doc/thesis/latex/gfx/
```

### Export All Example Models

```bash
# Batch export all 16 validation examples
python scripts/export_thesis_figures.py --all --output doc/thesis/latex/gfx/
```

### Custom DPI/Size

```bash
# High-resolution PNG for print
python scripts/export_thesis_figures.py --model examples/13_cellular_respiration.shy --format png --dpi 600 --output doc/thesis/latex/gfx/

# Fixed dimensions
python scripts/export_thesis_figures.py --model examples/08_energy_sensing.shy --width 800 --height 600 --output doc/thesis/latex/gfx/
```

## Output Formats

### PNG (Raster)
- **Use case**: Quick previews, presentations
- **Quality**: 300 DPI by default (configurable)
- **File size**: Moderate (depends on model complexity)
- **LaTeX inclusion**: `\includegraphics{gfx/model.png}`

### PDF (Vector)
- **Use case**: LaTeX figures, print-ready documents
- **Quality**: Infinite scaling (vector format)
- **File size**: Small for simple models
- **LaTeX inclusion**: `\includegraphics{gfx/model.pdf}`

### SVG (Editable Vector)
- **Use case**: Post-editing in Inkscape/Illustrator
- **Quality**: Infinite scaling
- **File size**: Small
- **Editing**: Open in Inkscape for annotations, colors, layout

### TikZ (LaTeX Native)
- **Use case**: Native LaTeX figures with perfect font matching
- **Quality**: LaTeX-rendered (perfect typography)
- **File size**: Minimal (just coordinates and commands)
- **LaTeX inclusion**: `\input{gfx/model.tex}`

**TikZ Example Output:**

```latex
\begin{tikzpicture}[
  place/.style={circle, draw=black, thick, minimum size=60pt},
  transition/.style={rectangle, draw=black, thick, fill=black, minimum width=10pt, minimum height=40pt},
  arc/.style={->, thick},
  test/.style={->, thick, dashed},
  inhibitor/.style={-o, thick}
]
  % Places
  \node[place] (P1) at (1.39cm, -2.78cm) {ATP, label=center:10};
  \node[place] (P2) at (4.17cm, -2.78cm) {ADP};
  
  % Transitions
  \node[transition] (T1) at (2.78cm, -2.78cm) {};
  \node[above=2pt of T1] {Hydrolysis};
  
  % Arcs
  \draw[arc] (P1) -- (T1);
  \draw[arc] (T1) -- (P2);
\end{tikzpicture}
```

## Integration with Thesis LaTeX

### Method 1: Include PDF/PNG

```latex
\begin{figure}[h]
\centering
\includegraphics[width=0.8\textwidth]{gfx/01_atp_synthesis.pdf}
\caption{ATP synthesis Petri net model}
\label{fig:atp-synthesis}
\end{figure}
```

### Method 2: Include TikZ (Native)

```latex
\begin{figure}[h]
\centering
\input{gfx/01_atp_synthesis.tex}
\caption{ATP synthesis Petri net model}
\label{fig:atp-synthesis}
\end{figure}
```

**Advantages of TikZ:**
- Perfect font matching with thesis body text
- Can be styled with TikZ commands in main document
- Can overlay additional annotations
- Smaller file size

## Recommended Workflow

1. **Create/refine models in SHYpn GUI**
   - Design Petri net structure
   - Apply layout algorithms (Force-directed, Hierarchical)
   - Save as `.shy` files in `examples/` or `workspace/projects/`

2. **Export for thesis**
   ```bash
   python scripts/export_thesis_figures.py --all --output doc/thesis/latex/gfx/
   ```

3. **Include in LaTeX chapters**
   - For simple figures: Use PDF (best quality/size ratio)
   - For editable figures: Export SVG, edit in Inkscape, re-export as PDF
   - For perfect LaTeX integration: Use TikZ

4. **Rebuild thesis**
   ```bash
   cd doc/thesis/latex
   pdflatex thesis.tex
   ```

## Example Models to Export

### Part III: Validation (Chapter 7)
- `01_atp_synthesis.shy` - Basic catalysis
- `02_reversible_reaction.shy` - Bidirectional arcs
- `03_hexokinase.shy` - Enzyme kinetics
- `04_competitive_inhibition.shy` - Inhibitor arcs
- `05_allosteric_regulation.shy` - Test arcs
- `06_gene_expression.shy` - Stochastic transitions
- `07_calcium_signaling.shy` - Burst transitions
- `08_energy_sensing.shy` - All four innovations

### Part V: Evaluation (Chapters 12-13)
- `09_glycolysis.shy` - 10 transitions, 3 regulatory checkpoints
- `10_tca_cycle.shy` - 8 transitions, cyclic topology
- `13_cellular_respiration.shy` - 32 transitions, integrated system

### Part VI: Synthesis (Chapters 14-15)
- `14_mapk_cascade.shy` - Signaling cascade
- `15_lac_operon.shy` - Gene regulation + metabolism
- `16_cell_cycle.shy` - Timed transitions

## Customization

Edit `scripts/export_thesis_figures.py` to customize:

- **Margins**: `ThesisFigureExporter(margin=100.0)` for more whitespace
- **DPI**: `ThesisFigureExporter(dpi=600)` for ultra-high-res PNG
- **Colors**: Modify rendering in `Place.render()` / `Transition.render()`
- **TikZ styles**: Edit the generated `.tex` files manually or modify `export_tikz()` method

## Troubleshooting

### "pycairo not installed"
```bash
# Ubuntu/Debian
sudo apt install python3-cairo

# Or via pip
pip install pycairo
```

### "No .shy files found"
Ensure you have example models in `examples/` directory. Create them in SHYpn GUI or import from KEGG/SBML.

### PDF/SVG not generated
Check Cairo installation:
```bash
python -c "import cairo; print(cairo.version)"
```

### TikZ not compiling in LaTeX
Ensure you have TikZ package:
```latex
\usepackage{tikz}
\usetikzlibrary{positioning, arrows}
```

## Advanced: Batch Processing

Create a shell script to export specific models with custom settings:

```bash
#!/bin/bash
# scripts/export_key_figures.sh

SCRIPT="python scripts/export_thesis_figures.py"
OUTPUT="doc/thesis/latex/gfx"

# High-quality figures for Chapter 7 (Validation)
for model in 01 02 03 04 05 06 07 08; do
    $SCRIPT --model examples/${model}_*.shy --format pdf --dpi 600 --output $OUTPUT
done

# TikZ figures for Chapter 12 (Case Studies)
for model in 09 10 13; do
    $SCRIPT --model examples/${model}_*.shy --format tikz --output $OUTPUT
done

echo "✅ Key figures exported!"
```

## Future Enhancements

- [ ] **Automated layout**: Apply force-directed layout before export
- [ ] **Style templates**: Predefined color schemes (grayscale, colorblind-friendly)
- [ ] **Annotations**: Add captions, arrows, highlights in exported figures
- [ ] **Comparison views**: Side-by-side before/after for perturbation studies
- [ ] **Animation export**: GIF/MP4 for simulation trajectories
- [ ] **GraphML export**: For Cytoscape visualization integration

## References

- **Cairo documentation**: https://pycairo.readthedocs.io/
- **TikZ manual**: https://tikz.dev/
- **LaTeX graphics**: https://en.wikibooks.org/wiki/LaTeX/Importing_Graphics
