# Shypn Validation Plan - Control Pathway Models

**Date**: October 12, 2025  
**Objective**: Validate Shypn simulation accuracy against established control models  
**Status**: Planning Phase

---

## Plan Summary

### ✅ Control Models Exist!

**Answer to your question**: YES, widely accepted control pathway models with temporal data exist in scientific databases, specifically:

1. **BioModels Database** - 1000+ curated, peer-reviewed models
2. **Published validation data** - Experimental time-series
3. **SBML format** - Direct import to Shypn
4. **Academic acceptance** - Cited in major journals

---

## Recommended Validation Sequence

### Phase 1: Repressilator (SIMPLE) ⭐ START HERE
**Model**: BIOMD0000000012  
**System**: 3-gene synthetic oscillator  
**Time**: 2-4 hours to validate  
**Why**: Simplest, clearest result, easy to verify

**Expected Outcome**:
```
✓ 100-minute oscillation period
✓ 3 proteins oscillating out of phase
✓ Smooth sinusoidal curves
✓ Stable indefinite oscillations
```

### Phase 2: Glycolysis (PRACTICAL) 🔬
**Model**: BIOMD0000000064  
**System**: Yeast glucose metabolism  
**Time**: 1 day to validate  
**Why**: Real biochemistry, practical importance

**Expected Outcome**:
```
✓ ATP/ADP oscillations or steady state
✓ Glucose consumption rate
✓ NADH dynamics
✓ Metabolic flux conservation
```

### Phase 3: Calcium Signaling (COMPLEX) ⚡
**Model**: BIOMD0000000035  
**System**: Cellular Ca²⁺ oscillations  
**Time**: 1-2 days to validate  
**Why**: Fast dynamics, spike trains

**Expected Outcome**:
```
✓ Calcium spike frequency
✓ Amplitude modulation
✓ Fast time scale (seconds)
✓ Complex pattern generation
```

---

## Validation Workflow

### Step 1: Model Acquisition
```bash
# Download from BioModels
wget https://www.ebi.ac.uk/biomodels/model/download/BIOMD0000000012

# Or use BioModels API
curl -X GET "https://www.ebi.ac.uk/biomodels/BIOMD0000000012/files" -o repressilator.xml

# Save to: data/control_models/
```

### Step 2: Import to Shypn
```python
# GUI: File → Import → SBML → Select model
# Expected:
#   - Continuous transitions (default)
#   - Tree layout rendering
#   - All species and reactions loaded
```

### Step 3: Simulation Setup
```python
# Configure simulation settings:
settings = SimulationSettings()
settings.duration = 200.0  # minutes (for Repressilator)
settings.time_units = TimeUnits.MINUTES
settings.dt_auto = True
settings.time_scale = 1.0  # Start real-time

# Initial conditions from SBML (already loaded)
```

### Step 4: Run Simulation
```python
# Execute simulation
# Record data:
#   - Time points
#   - Species concentrations
#   - Transition rates
# Export to CSV
```

### Step 5: Data Comparison
```python
# Load reference data from BioModels
# Compare:
#   - Time series plots
#   - Period/frequency
#   - Amplitude ranges
#   - Phase relationships
# Calculate error metrics
```

### Step 6: Validation Report
```markdown
# Document:
#   - Visual comparison plots
#   - Quantitative metrics (RMSE, R²)
#   - Success/failure criteria
#   - Issues encountered
#   - Recommendations
```

---

## Success Criteria

### Quantitative Thresholds
| Metric | Acceptable | Good | Excellent |
|--------|-----------|------|-----------|
| Period Error | < 20% | < 10% | < 5% |
| Amplitude Error | < 25% | < 15% | < 10% |
| RMSE (normalized) | < 0.3 | < 0.2 | < 0.1 |
| R² Correlation | > 0.85 | > 0.90 | > 0.95 |
| Mass Conservation | ±1% | ±0.5% | ±0.1% |

### Qualitative Requirements
✓ Correct oscillation shape  
✓ Stable long-term behavior  
✓ No numerical artifacts  
✓ Proper phase relationships  
✓ Expected steady states  

---

## Tools & Scripts

### Validation Script Template
```python
#!/usr/bin/env python3
"""
Validate Shypn against BioModels control pathway
"""
import pandas as pd
import matplotlib.pyplot as plt
from scipy import stats

def load_shypn_results(csv_path):
    """Load Shypn simulation output"""
    return pd.read_csv(csv_path)

def load_reference_data(model_id):
    """Load BioModels reference data"""
    # From BioModels or published paper
    return pd.read_csv(f"data/reference/{model_id}.csv")

def calculate_metrics(shypn_data, reference_data):
    """Calculate validation metrics"""
    # Period comparison
    period_shypn = detect_period(shypn_data)
    period_ref = detect_period(reference_data)
    period_error = abs(period_shypn - period_ref) / period_ref
    
    # RMSE
    rmse = calculate_rmse(shypn_data, reference_data)
    
    # Correlation
    r2 = stats.pearsonr(shypn_data, reference_data)[0]**2
    
    return {
        'period_error': period_error,
        'rmse': rmse,
        'r2': r2
    }

def plot_comparison(shypn_data, reference_data, output_path):
    """Create comparison plots"""
    fig, axes = plt.subplots(2, 1, figsize=(12, 8))
    
    # Time series
    axes[0].plot(reference_data['time'], reference_data['concentration'], 
                 label='Reference', linewidth=2)
    axes[0].plot(shypn_data['time'], shypn_data['concentration'], 
                 label='Shypn', linestyle='--')
    axes[0].legend()
    axes[0].set_ylabel('Concentration')
    
    # Error plot
    error = shypn_data['concentration'] - reference_data['concentration']
    axes[1].plot(shypn_data['time'], error)
    axes[1].set_xlabel('Time')
    axes[1].set_ylabel('Error')
    
    plt.savefig(output_path)

if __name__ == "__main__":
    # Run validation
    shypn = load_shypn_results("output/repressilator_shypn.csv")
    reference = load_reference_data("BIOMD0000000012")
    
    metrics = calculate_metrics(shypn, reference)
    plot_comparison(shypn, reference, "results/comparison.png")
    
    print(f"Validation Metrics:")
    print(f"  Period Error: {metrics['period_error']:.2%}")
    print(f"  RMSE: {metrics['rmse']:.4f}")
    print(f"  R²: {metrics['r2']:.4f}")
```

---

## Timeline

### Week 1: Repressilator Validation
- **Day 1**: Download model, import to Shypn
- **Day 2**: Run simulation, export data
- **Day 3**: Compare with reference, calculate metrics
- **Day 4**: Create report, document results

### Week 2: Glycolysis Validation
- **Day 1-2**: Import and configure model
- **Day 3-4**: Run simulations (multiple conditions)
- **Day 5**: Data analysis and comparison
- **Day 6-7**: Report and documentation

### Week 3: Calcium Validation
- Similar timeline to Week 2

### Week 4: Documentation & Publication
- Compile all results
- Create comprehensive validation report
- Prepare for potential publication

---

## Resources Needed

### Data Files
- [ ] SBML models from BioModels (3-5 models)
- [ ] Reference time-series data (CSV format)
- [ ] Published parameter sets
- [ ] Experimental data (if available)

### Software
- [x] Shypn (current version)
- [ ] Python analysis scripts
- [ ] matplotlib for plotting
- [ ] pandas for data handling
- [ ] scipy for statistical analysis

### Documentation
- [ ] BioModels model descriptions
- [ ] Original papers (PDF)
- [ ] Experimental protocols
- [ ] Previous validation studies

---

## Risk Assessment

### Potential Issues
1. **Parameter Differences**: SBML may use different units
   - **Mitigation**: Carefully check unit conversions
   
2. **Initial Conditions**: May not match reference exactly
   - **Mitigation**: Use exact initial conditions from reference

3. **Numerical Precision**: Integration errors accumulate
   - **Mitigation**: Test different time steps (dt)

4. **Long Simulations**: May have stability issues
   - **Mitigation**: Check mass conservation, use adaptive dt

5. **Data Format**: Reference data may be in graphs only
   - **Mitigation**: Contact authors or use data extraction tools

---

## Expected Outcomes

### Best Case Scenario
✅ All models validate within acceptable thresholds  
✅ Shypn matches reference results closely  
✅ No major bugs discovered  
✅ Ready for scientific publication use

### Realistic Scenario
✅ Most models validate successfully  
⚠️ Some parameter tuning needed  
⚠️ Minor numerical issues identified and fixed  
✅ Overall confidence in Shypn accuracy

### Worst Case Scenario
❌ Significant discrepancies found  
❌ Bugs in simulation engine discovered  
🔧 Need major refactoring  
📚 Learning opportunity for improvements

---

## Documentation Structure

```
doc/control/
├── README.md (overview - already created)
├── VALIDATION_PLAN.md (this file)
│
├── models/
│   ├── BIOMD0000000012_repressilator.md
│   ├── BIOMD0000000064_glycolysis.md
│   └── BIOMD0000000035_calcium.md
│
├── results/
│   ├── repressilator_validation_report.md
│   ├── glycolysis_validation_report.md
│   └── calcium_validation_report.md
│
└── scripts/
    ├── validate_model.py
    ├── plot_results.py
    └── calculate_metrics.py
```

---

## Next Actions

### Immediate (Today)
1. ✅ Research control models (DONE)
2. ✅ Create validation plan (THIS FILE)
3. ⏳ Download Repressilator model
4. ⏳ Create data directories

### Short-term (This Week)
1. Import Repressilator to Shypn
2. Run first validation simulation
3. Create comparison plots
4. Document initial results

### Medium-term (This Month)
1. Complete 3 model validations
2. Create automated validation suite
3. Write comprehensive report
4. Prepare publication materials

---

## Conclusion

**Research Result**: ✅ **YES**, control pathway models with temporal data exist and are readily available!

**Best Models for Validation**:
1. **Repressilator** (BIOMD0000000012) - Simple, clear oscillations
2. **Glycolysis** (BIOMD0000000064) - Practical, well-studied
3. **Calcium** (BIOMD0000000035) - Complex dynamics

**Data Available**:
- SBML models (direct import)
- Reference time-series data
- Published validation results
- Experimental measurements

**Recommendation**: Start with **Repressilator** - simplest model with clearest validation criteria. Success here builds confidence for more complex models.

**Expected Timeline**: 2-4 weeks for comprehensive validation of 3 control models.

---

*Ready to begin validation! Next step: Download and import Repressilator model.* 🔬✅
