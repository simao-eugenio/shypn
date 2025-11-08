# Scientist Data Requirements for Dynamic Analysis

## Overview
This document outlines the meaningful information scientists need to record and analyze when conducting simulation experiments on the SHYpn platform. The data is categorized into metadata, time-series observations, derived analyses, and comparative studies.

---

## 1. EXPERIMENT METADATA (Setup Information)

Essential parameters that define the simulation experiment:

- **Model Name/ID**: Which pathway/network was simulated
- **Simulation Duration**: Total model time (e.g., 60s)
- **Time Scale**: Playback speed used (e.g., 2.0x)
- **Time Step (dt)**: Granularity of simulation (e.g., 0.006s with 10000 steps target)
- **Initial Conditions**: Starting token counts in each place
- **Kinetic Parameters**: Rate constants (k), Km, Vmax for each transition
- **Model Type**: Stochastic, Continuous, or Hybrid
- **Random Seed**: For stochastic reproducibility

---

## 2. TIME-SERIES DATA (Dynamic Observations)

### 2.1 Place-Centered (Concentration/Token Evolution)

**Species Concentration vs Time**
- Format: `[time, tokens]` pairs for each place
- Example: Glucose-6-P concentration over 60 seconds
- Applications:
  - Substrate consumption curves
  - Product accumulation kinetics
  - Intermediate metabolite dynamics

**Mass Conservation Analysis**
- Total mass: Sum of all tokens over time (should be constant in closed systems)
- Mass balance verification

**Steady State Detection**
- Identify when concentrations stabilize (d[X]/dt ≈ 0)
- Time to reach steady state
- Steady state concentrations

### 2.2 Transition-Centered (Reaction Activity)

**Firing Count**
- Total number of times each transition fired during simulation
- Indicates overall reaction activity

**Firing Rate**
- Firings per unit time (activity level)
- Formula: `firing_count / duration`

**Flux Through Reaction**
- Tokens processed per unit time
- For continuous: Instantaneous rate
- For stochastic: Average rate from firing events

**Event Timing** (Stochastic)
- Exact firing times for discrete transitions
- Inter-event intervals
- Event distribution analysis

**Continuous Flow** (Continuous)
- Instantaneous rate at each time step
- Rate evolution over time

---

## 3. DERIVED ANALYSES (Calculated Insights)

### 3.1 Kinetic Analysis

**Rate Calculations**
- **Substrate Consumption Rate**: -d[S]/dt (negative slope)
- **Product Formation Rate**: +d[P]/dt (positive slope)
- **Net Rate**: For reversible reactions

**Performance Metrics**
- **Reaction Velocity**: Current rate vs theoretical maximum (v/Vmax)
- **Saturation Level**: [S]/(Km + [S]) for Michaelis-Menten kinetics
- **Catalytic Efficiency**: kcat/Km for enzymatic reactions

**Bottleneck Identification**
- Which reactions are rate-limiting
- Where flux is constrained
- Potential optimization targets

### 3.2 Network Behavior

**Pathway Flux Distribution**
- Which branches carry most flow
- Flux partitioning at branch points
- Dominant pathways vs minor routes

**Accumulation Points**
- Where tokens build up
- Potential regulatory sites
- Buffer capacities

**Depletion Points**
- Where tokens get exhausted
- Starvation conditions
- Supply bottlenecks

**Network Efficiency**
- Overall pathway throughput
- Conversion efficiency (product/substrate ratio)
- Energy coupling efficiency

---

## 4. COMPARATIVE DATA (Multiple Runs)

### 4.1 Parameter Sensitivity

**Kinetic Parameter Variations**
- How changing Km affects flux
- Effect of Vmax on throughput
- Rate constant sensitivity

**Stoichiometry Impact**
- Effect of changing substrate ratios
- Product inhibition analysis

### 4.2 Perturbation Response

**Inhibition Studies**
- Competitive inhibitor effects
- Non-competitive inhibitor effects
- Partial vs complete inhibition

**Environmental Conditions**
- Temperature effects (if modeled)
- pH effects (if modeled)
- Cofactor availability

### 4.3 Condition Comparison

**Physiological States**
- Aerobic vs anaerobic metabolism
- Fed vs fasted state
- Normal vs disease conditions

**Genetic Variations**
- Wild-type vs mutant
- Overexpression effects
- Knockout analysis

---

## 5. PRIORITY FOR REPORT PANEL - DYNAMIC ANALYSES CATEGORY

### 5.1 Essential Tables

#### **Species Concentration Table** (Place-centered)
```
Columns:
- Place Name (with color indicator)
- Initial Tokens
- Final Tokens
- Minimum
- Maximum
- Average
- Total Change (Δ)
- Change Rate (Δ/duration)
```

**Use Cases:**
- Identify which species accumulated or depleted
- Find concentration ranges
- Detect steady states (small Δ)

---

#### **Reaction Activity Table** (Transition-centered)
```
Columns:
- Transition Name
- Type (Stochastic/Continuous)
- Firing Count
- Average Rate (firings/time)
- Total Flux (tokens processed)
- Contribution (% of total network flux)
- Status (Active/Inactive/Bottleneck)
```

**Use Cases:**
- Identify active vs dormant reactions
- Find bottleneck reactions (low flux)
- Compare reaction contributions

---

### 5.2 Essential Visualizations

#### **Time Series Plot** (⭐ Most Important!)

**Configuration:**
- **X-axis**: Time (model time in seconds)
- **Y-axis**: Concentration (token count)
- **Multiple lines**: One per selected place (color-coded)
- **Interactive**: Click place in canvas or table to add/remove from plot
- **Legend**: Automatically generated with place names

**Features:**
- Zoom and pan
- Cursor crosshair with value display
- Export to PNG/SVG
- Data export to CSV

**Scientific Value:**
- Visualize substrate consumption kinetics
- Observe product formation curves
- Detect steady states
- Identify oscillations or instabilities

---

#### **Flux Distribution Chart**

**Type**: Horizontal bar chart

**Configuration:**
- **Y-axis**: Transition names
- **X-axis**: Total flux (tokens processed) or % contribution
- **Color coding**: By transition type or activity level
- **Sorting**: By flux (descending)

**Scientific Value:**
- Identify dominant pathways
- Find bottlenecks (short bars)
- Compare branch point distributions

---

#### **Phase Plot** (Advanced)

**Configuration:**
- **X-axis**: Concentration of species A
- **Y-axis**: Concentration of species B
- **Trajectory**: Path through phase space over time

**Scientific Value:**
- Visualize system dynamics
- Identify limit cycles (oscillations)
- Detect attractors (steady states)

---

### 5.3 Export Capabilities

**Data Export Formats:**
- **CSV**: Raw time-series data
  - Columns: Time, Place1, Place2, ..., PlaceN
  - One row per time step
  
- **JSON**: Complete experiment data
  - Metadata
  - Time-series arrays
  - Derived metrics

**Report Export:**
- **PDF**: Complete analysis report with tables and plots
- **HTML**: Interactive report for web viewing

---

## 6. IMPLEMENTATION ROADMAP

### Phase 1: Data Collection Infrastructure
1. Create `DataCollector` class to record time-series during simulation
2. Store data in efficient format (numpy arrays or pandas DataFrame)
3. Hook into simulation engine to capture state at each step

### Phase 2: Analysis Module
1. Implement rate calculations (d[X]/dt)
2. Implement steady-state detection
3. Calculate flux distributions
4. Identify bottlenecks

### Phase 3: Visualization
1. Time-series plot with matplotlib/plotly
2. Flux distribution bar chart
3. Interactive plot controls (zoom, pan, select)

### Phase 4: Report Panel Integration
1. Add "DYNAMIC ANALYSES" category to Report Panel
2. Implement Species Concentration table
3. Implement Reaction Activity table
4. Embed plots in expandable sections

### Phase 5: Export and Persistence
1. CSV export for time-series data
2. JSON export for complete experiment
3. PDF report generation
4. Save/load analysis sessions

---

## 7. KEY INSIGHTS

### Most Valuable Data
1. **Time-series plots**: Visual understanding of dynamics
2. **Final vs initial states**: Overall conversion metrics
3. **Bottleneck identification**: Optimization targets

### Scientist Workflow
1. **Setup**: Define model, set parameters, set initial conditions
2. **Run**: Execute simulation with appropriate duration and dt
3. **Observe**: Watch animation and real-time plots
4. **Analyze**: Review tables and charts in Report Panel
5. **Compare**: Run variations and compare results
6. **Export**: Save data and generate reports for publication

### Critical Requirements
- **Reproducibility**: Record all parameters for exact replication
- **Accuracy**: Fine enough time step (dt) to capture dynamics
- **Clarity**: Clear labeling and units for all data
- **Flexibility**: Allow custom analysis and export

---

## 8. FUTURE ENHANCEMENTS

### Advanced Analysis
- **Sensitivity analysis**: Automated parameter sweeps
- **Optimization**: Find parameters that maximize/minimize objectives
- **Statistical analysis**: Mean, variance, confidence intervals for stochastic runs
- **Spectral analysis**: Frequency analysis for oscillating systems

### Machine Learning Integration
- **Pattern recognition**: Identify characteristic dynamics
- **Anomaly detection**: Flag unusual simulation behavior
- **Parameter estimation**: Fit model to experimental data

### Collaboration Features
- **Shared experiments**: Cloud storage for experiment data
- **Annotations**: Add notes and observations to plots
- **Versioning**: Track experiment history

---

## References

This document is based on standard practices in:
- Systems biology simulation (COPASI, Cell Designer)
- Chemical kinetics analysis (Kintecus, CHEMKIN)
- Biochemical pathway analysis (KEGG, BioCyc)
- Petri net simulation (CPN Tools, PIPE)

**Last Updated**: November 7, 2025
**Status**: Planning Document for Dynamic Analyses Implementation
