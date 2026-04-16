# Data Directory

## Simulation Data

Simulation results and analysis data from Bacillus subtilis sporulation models.

### Data Organization

- **Manuscript:** Final datasets used for published figures and analysis
- **Archive:** Experimental data, parameter sweeps, preliminary results

## Data Files

Typical data files include:

- Time series data (CSV format)
  - Columns: time, ATP, GTP, ADP, GDP, Spore, etc.
  - Normal condition simulations
  - Stress condition simulations
  
- Basin of attraction data
  - Initial condition sweeps
  - Attractor classification
  
- Thermodynamic landscape data
  - Free energy calculations
  - Energy barrier measurements

## Data Format

**Primary Format:** CSV (comma-separated values)

```csv
time,ATP,GTP,ADP,GDP,Spore,Vegetative
0.0,5000.0,5000.0,100.0,100.0,0.0,100.0
1.0,4998.2,5001.3,101.8,98.7,0.5,99.5
...
```

**Metadata:** JSON files with simulation parameters

```json
{
  "model": "bacillus_sporulation_stress.shy",
  "duration": 180,
  "initial_ATP": 300,
  "timestamp": "2026-01-07T10:30:00"
}
```

## Data Generation

Data can be regenerated using the models in `../models/manuscript/`:

```python
from shypn import load_model, simulate
import pandas as pd

# Load model
model = load_model('../models/manuscript/bacillus_sporulation_stress.shy')

# Simulate
results = simulate(model, duration=180)

# Save data
df = pd.DataFrame(results)
df.to_csv('stress_timeseries.csv', index=False)
```

## Archive Directory

Contains experimental and development data:
- Parameter exploration results
- Failed experiments / troubleshooting data
- Intermediate analysis outputs
- Raw data before processing

## Data Availability

All data supporting the published manuscript is available in this repository under MIT license. Data can be freely used with appropriate citation.

## Notes

- All simulations performed with SHYPN v1.0
- Random seeds documented in metadata files for reproducibility
- Data validated against experimental literature when available
