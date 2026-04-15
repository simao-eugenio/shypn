# Figures Directory

## Published Figures

Figures used in the arXiv manuscript (9 pages, 3 figures).

### Figure Files

1. **thermodynamic_landscape.pdf**
   - Type: Energy landscape visualization
   - Content: Thermodynamic constraints driving pathway selection
   - Format: PDF (publication quality)

2. **bacillus_basin_of_attraction.pdf**
   - Type: Basin of attraction analysis
   - Content: State space analysis showing attractor regions
   - Format: PDF (publication quality)

3. **bacillus_sporulation_stress.pdf**
   - Type: Stress response dynamics
   - Content: Time series showing ATP depletion and spore formation
   - Format: PDF (publication quality)

## Generation Scripts

All figures can be regenerated using scripts in `../scripts/`:

```bash
cd ../scripts/

# Generate energy landscape
python generate_thermodynamic_landscape.py

# Generate basin of attraction
python plot_basin_attraction.py

# Visualize thermodynamic constraints
python plot_thermodynamic_landscape.py

# Plot decision cascade
python plot_decision_cascade.py
```

## Archive Directory

Development and intermediate figures from parameter exploration and model tuning.

- PNG versions of publication figures
- Exploratory plots
- Parameter sweep visualizations
- Diagnostic figures

## Figure Specifications

**Format:** PDF (vector graphics preferred)
**Resolution:** 300 DPI minimum for raster elements
**Color:** RGB for digital, CMYK for print if needed
**Fonts:** Embedded, typically Arial or Helvetica
**Size:** Standard column width (3.5") or full width (7")

## Notes

- Original figures preserved in this directory
- Archive contains development versions
- All figures reproducible from raw data in `../data/`
