# Tabular Subnet Experimentation with Kinetic Parameters

## Overview

The Viability Panel provides a **micro-surgical analysis interface** for isolated subnets, allowing users to experiment with parameters in a structured tabular format and observe behavioral changes through automated simulation.

## Concept

Instead of modifying the full model, users can:
1. **Isolate a subnet** (e.g., transitions T5, T6 with their locality)
2. **Edit parameters** in table columns (markings, arc weights, kinetic constants)
3. **Run simulations** automatically on parameter changes
4. **Compare results** across multiple experiment configurations
5. **Diagnose viability** issues (deadlocks, boundedness violations)

## Table Organization

```
┌─────────────────────────┬──────────────┬──────────────┬──────────────┐
│ PARAMETER               │ Current      │ Experiment 1 │ Experiment 2 │
├─────────────────────────┼──────────────┼──────────────┼──────────────┤
│ PLACES (Markings)       │              │              │              │
│ ├─ P3 tokens            │ 5 ⚡         │ 10 ⚡        │ 3 ⚡         │
│ └─ P4 tokens            │ 2 ⚡         │ 2 ⚡         │ 0 ⚡         │
├─────────────────────────┼──────────────┼──────────────┼──────────────┤
│ ARCS (Weights)          │              │              │              │
│ ├─ P3→T5 weight         │ 1 ⚡         │ 2 ⚡         │ 1 ⚡         │
│ ├─ T5→P4 weight         │ 1 ⚡         │ 1 ⚡         │ 3 ⚡         │
│ ├─ P4→T6 weight         │ 1 ⚡         │ 1 ⚡         │ 1 ⚡         │
│ └─ T6→P3 weight         │ 1 ⚡         │ 2 ⚡         │ 1 ⚡         │
├─────────────────────────┼──────────────┼──────────────┼──────────────┤
│ TRANSITIONS (Kinetics)  │              │              │              │
│ ├─ T5 kcat (s⁻¹)        │ 100 ⚡       │ 150 ⚡       │ 50 ⚡        │
│ ├─ T5 Km (mM)           │ 0.5 ⚡       │ 0.3 ⚡       │ 1.0 ⚡       │
│ ├─ T5 Ki (mM)           │ - ⚡         │ 2.0 ⚡       │ - ⚡         │
│ ├─ T6 kcat (s⁻¹)        │ 80 ⚡        │ 80 ⚡        │ 120 ⚡       │
│ ├─ T6 Km (mM)           │ 0.8 ⚡       │ 0.8 ⚡       │ 0.4 ⚡       │
│ └─ T6 reversible        │ No ⚡        │ No ⚡        │ Yes ⚡       │
├─────────────────────────┼──────────────┼──────────────┼──────────────┤
│ RESULTS (Auto-compute)  │              │              │              │
│ ├─ Final P3             │ -            │ 0 tokens     │ 3 tokens     │
│ ├─ Final P4             │ -            │ 8 tokens     │ 0 tokens     │
│ ├─ T5 flux              │ -            │ 3.2 mM/s     │ 1.1 mM/s     │
│ ├─ T6 flux              │ -            │ 2.8 mM/s     │ 0.0 mM/s     │
│ ├─ Viability status     │ -            │ ✓ Stable     │ ✗ Deadlock   │
│ └─ Execution time       │ -            │ 0.12s        │ 0.08s        │
└─────────────────────────┴──────────────┴──────────────┴──────────────┘
```

**⚡ = Editable cell** (double-click to edit, Enter to commit, triggers auto-simulation)

## Panel Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ VIABILITY PANEL - Subnet Experimentation                         │
├──────────────────────────────────────────────────────────────────┤
│ Selected Localities:  [T5, T6]                          [Clear]  │
├──────────────────────────────────────────────────────────────────┤
│ ┌─ Simulation Controls ─────────────────────────────────────────┐│
│ │ Time limit: [100 ⚡] s   Max steps: [1000 ⚡]   Method: [ODE ▾]││
│ │ [▶ Run] [⏸ Pause] [⏹ Stop] [↻ Reset]   Status: ● Ready       ││
│ └──────────────────────────────────────────────────────────────┘│
├──────────────────────────────────────────────────────────────────┤
│ ┌─ Experiment Table (Editable) ──────────────────────────────────┐│
│ │ [+ Add Column] [- Remove] [📋 Copy] [💾 Save Experiments]      ││
│ │                                                                 ││
│ │ [Table with parameters + results as shown above]                ││
│ │                                                                 ││
│ └──────────────────────────────────────────────────────────────┘│
├──────────────────────────────────────────────────────────────────┤
│ ┌─ Diagnostics Log ──────────────────────────────────────────────┐│
│ │ [Auto-scroll ☑]                                                 ││
│ │ 13:45:02 - Experiment 1: Simulation started                     ││
│ │ 13:45:02 - T5 fired 3 times, consumed 6 tokens from P3         ││
│ │ 13:45:02 - Reached steady state at t=8.5s                       ││
│ │ 13:45:02 - ✓ Subnet viable, no deadlocks detected              ││
│ └──────────────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────────────┘
```

## Key Features

### 1. Editable Parameters (⚡ cells)
- **Places**: Initial token markings
- **Arcs**: Connection weights
- **Transitions**: Kinetic parameters (kcat, Km, Ki, reversibility)
- **Real-time updates**: Changes trigger automatic simulation

### 2. Simulation Controls
- **▶ Run**: Execute simulation with current parameters
- **⏸ Pause**: Temporarily halt execution
- **⏹ Stop**: Abort and reset to initial state
- **↻ Reset**: Restore original parameter values
- **Time limit**: Maximum simulation duration (seconds)
- **Max steps**: Maximum firing events
- **Method**: Solver selection (Gillespie, ODE, Hybrid)

### 3. Column Management
- **+ Add Column**: Create new experiment configuration
- **- Remove**: Delete selected experiment
- **📋 Copy**: Duplicate parameter set for variation
- **💾 Save**: Export experiments to CSV/JSON

### 4. Results Auto-computation
- **Token distribution**: Final marking state
- **Flux analysis**: Transition firing rates
- **Viability status**: Deadlock/boundedness detection
- **Performance metrics**: Execution time, convergence

### 5. Diagnostics Log
- **Real-time feedback**: Step-by-step simulation progress
- **Event tracking**: Transition firings, token movements
- **Issue detection**: Warnings about viability problems
- **Auto-scroll**: Follow execution live

## Architecture

### SubnetSimulator Class
Located in `viability_panel.py`, responsible for:
- **Subnet extraction**: Isolate selected transitions + localities
- **Parameter application**: Apply experiment column values
- **Simulation execution**: Run Gillespie/ODE solver
- **Results computation**: Calculate fluxes, detect issues
- **State management**: Track simulation progress

### Controller Methods
```python
def _on_run_simulation(self)
    """Start simulation with current parameters"""

def _on_pause_simulation(self)
    """Pause execution"""

def _on_stop_simulation(self)
    """Abort and reset"""

def _on_parameter_edited(self, renderer, path, new_text, column_index)
    """Cell edited, trigger auto-run"""

def _add_experiment_column(self)
    """Create new parameter set"""

def _remove_experiment_column(self, column_index)
    """Delete experiment configuration"""

def _export_experiments(self)
    """Save parameter sets + results to file"""

def _update_results_section(self, experiment_index, results)
    """Populate results rows after simulation"""
```

## Workflow Example

### Scenario: Testing T5/T6 Sensitivity to Substrate Concentration

1. **Select subnet**: Right-click T5 → "Add to Viability Analysis"
2. **Review current state**: "Current" column shows base parameters
3. **Create experiment 1**: 
   - Click "+ Add Column"
   - Edit P3 tokens: 10 (increased substrate)
   - Edit T5 Km: 0.3 (higher affinity)
4. **Run simulation**: Press "▶ Run"
5. **Observe results**:
   - T5 flux: 3.2 mM/s (vs 1.5 mM/s baseline)
   - Final P4: 8 tokens (vs 3 baseline)
   - Status: ✓ Stable
6. **Create experiment 2**:
   - Copy experiment 1
   - Edit P3 tokens: 3 (reduced substrate)
   - Edit T5 Km: 1.0 (lower affinity)
7. **Compare outcomes**:
   - T5 flux: 1.1 mM/s (starved)
   - Final P4: 0 tokens (depleted)
   - Status: ✗ Deadlock detected at t=12.3s
8. **Conclusion**: T5 requires Km < 0.5 mM with P3 ≥ 5 tokens for viability

## Benefits

### Micro-Surgical Precision
- **Isolated testing**: Modify subnet without affecting full model
- **Systematic comparison**: Side-by-side parameter variations
- **Hypothesis testing**: Validate kinetic assumptions

### Workflow Integration
- **Visual feedback**: Purple borders show selected subnet
- **Model consistency**: Changes don't persist to main model
- **Export results**: Document findings for reports

### Performance
- **Fast iterations**: Small subnet = quick simulations
- **Real-time feedback**: See results immediately
- **Parallel experiments**: Multiple columns run independently

## Implementation Status

- ✅ Subnet isolation (locality detection)
- ✅ Visual highlighting (purple borders)
- ✅ Parameter tables (arc weights, places)
- ⏳ **PENDING**: Experiment table with kinetic parameters
- ⏳ **PENDING**: SubnetSimulator integration
- ⏳ **PENDING**: Simulation controls (Run/Pause/Stop)
- ⏳ **PENDING**: Results auto-computation
- ⏳ **PENDING**: Diagnostics log
- ⏳ **PENDING**: Export functionality

## Future Enhancements

1. **Sensitivity analysis**: Auto-vary parameters, plot response curves
2. **Optimization**: Find parameter sets maximizing flux/minimizing deadlock risk
3. **Template library**: Save/load common experiment configurations
4. **Batch simulation**: Run multiple experiments in parallel
5. **3D visualization**: Plot flux vs two parameters (surface plots)
6. **Statistical analysis**: Mean/variance across repeated stochastic runs

---

**Date**: November 13, 2025  
**Version**: 1.0  
**Status**: Design specification
