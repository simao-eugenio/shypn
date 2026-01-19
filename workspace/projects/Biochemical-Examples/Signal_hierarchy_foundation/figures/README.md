# Figures for Foundation Manuscript

## Figure 1: Signal Hierarchy Schematic
**File**: `decision_cascade.pdf`  
**Description**: Decision cascade showing UV → ATP → ComK/Spo0A hierarchy  
**Used in**: Introduction (Section 1)

## Figure 2: ATP Threshold Prediction ⭐ MAIN RESULT
**File**: `bacillus_atp_threshold.pdf`  
**Description**: 
- Sigmoid commitment probability curve
- **SHYPN prediction**: 2.38 mM ATP (purple dashed line)
- **Experimental data**: 2.21 ± 0.18 mM (red point with error bar)
- **Error**: 7% - demonstrates predictive capability
- Navy region: Competence pathway
- Firebrick region: Sporulation pathway

**Used in**: Validation (Section 5), Figure 2

**Alternate versions**:
- `bacillus_atp_threshold.png` - Raster format for quick preview

## Reproducibility
Figures generated from SHYPN simulation data using `generate_figure.py`:

```bash
python generate_figure.py  # Regenerates bacillus_atp_threshold.pdf
```

**Requirements**: matplotlib, numpy, scipy

## Figure Details

### Figure 2 Technical Specifications
- **Format**: PDF (vector graphics)
- **Size**: 10" × 6" (publication quality)
- **DPI**: 300 (for raster elements)
- **Font**: Arial/Helvetica family
- **Color scheme**: Navy (#1f4788), Firebrick (#b22222)
- **Data points**: 100 ATP concentrations (1.5-3.5 mM range)
- **Experimental error bars**: ±0.18 mM (1 standard deviation)

### Data Source
- **SHYPN simulation**: 1000 replicates, tau-leaping algorithm
- **Experimental reference**: Pettinari & Méndez (2015), Mirouze & Dubnau (2013)
- **Model**: B. subtilis sporulation decision network

## License
All figures are licensed under CC-BY 4.0, consistent with PLOS policy.
