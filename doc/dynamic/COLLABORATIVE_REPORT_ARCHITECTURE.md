# Collaborative Report Panel Architecture

## Current Report Panel Structure Analysis

### Category Distribution & Data Responsibilities

```
┌─────────────────────────────────────────────────────────────────┐
│                        REPORT PANEL                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ 1. MODELS (model_structure_category.py)               │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │ STATIC MODEL INFORMATION                               │    │
│  │ • Model Overview (name, dates, file path)             │    │
│  │ • Petri Net Structure (places, transitions, arcs)     │    │
│  │ • Import Provenance (KEGG/SBML source)                │    │
│  │ • Species/Places Table (8 columns, IDs, names, mass)  │    │
│  │ • Reactions/Transitions Table (15 columns, kinetics)  │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ 2. DYNAMIC ANALYSES (parameters_category.py)          │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │ KINETIC PARAMETERS & SIMULATION                        │    │
│  │ • Kinetic Parameters (Km, Vmax, Kcat, Ki)            │    │
│  │ • Enrichments (BRENDA, SABIO-RK sources)              │    │
│  │ • Citations & References                               │    │
│  │ • Simulation Results (PLACEHOLDER - to implement)     │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ 3. TOPOLOGY ANALYSES (topology_analyses_category.py)  │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │ NETWORK STRUCTURE ANALYSIS                             │    │
│  │ • Topology Analysis (degree, components, cycles)       │    │
│  │ • Locality Analysis (regions, neighborhoods)           │    │
│  │ • Source-Sink Analysis (flow paths)                    │    │
│  │ • Structural Invariants (T-inv, P-inv)                │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
│  ┌────────────────────────────────────────────────────────┐    │
│  │ 4. PROVENANCE & LINEAGE (provenance_category.py)      │    │
│  ├────────────────────────────────────────────────────────┤    │
│  │ DATA SOURCE TRACKING                                   │    │
│  │ • Source Pathways (KEGG IDs, organisms, dates)        │    │
│  │ • Transformation Pipeline (import → enrich → edit)     │    │
│  │ • Change History (who, when, what)                     │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Cross-Referencing Map

### How Data Flows Between Categories

```
┌──────────────┐
│ KEGG/SBML    │
│ Import       │
└──────┬───────┘
       │
       ├─────────────────────────────────────────┐
       │                                         │
       v                                         v
┌──────────────────┐                    ┌────────────────┐
│ MODELS           │                    │ PROVENANCE     │
│ • Species List   │                    │ • Source ID    │
│ • Reactions List │                    │ • Organism     │
│ • EC Numbers     │                    │ • Import Date  │
│ • Stoichiometry  │                    │ • Citations    │
└────────┬─────────┘                    └────────┬───────┘
         │                                       │
         │      ┌─────────────────┐             │
         └─────>│ DYNAMIC ANALYSES│<────────────┘
                │ • Kinetics Params│
                │ • Enrichments    │
                │ • Citations      │
                └────────┬─────────┘
                         │
                         v
                ┌─────────────────┐
                │ SIMULATION RUN  │
                │ (Controller)    │
                └────────┬─────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
         v               v               v
┌─────────────┐  ┌──────────────┐  ┌────────────┐
│ DYNAMIC     │  │ TOPOLOGY     │  │ PROVENANCE │
│ ANALYSES    │  │ ANALYSES     │  │ (optional) │
│             │  │              │  │            │
│ • Time-     │  │ • Active     │  │ • Sim Run  │
│   series    │  │   paths      │  │   record   │
│ • Rates     │  │ • Bottlenecks│  │ • Settings │
│ • Fluxes    │  │ • Used arcs  │  │ • Duration │
└─────────────┘  └──────────────┘  └────────────┘
```

---

## Collaborative Data Sharing Strategy

### Principle: Each Category Owns Its Domain, Shares Read-Only Views

### 1. MODELS Category (Owner of Static Structure)

**What It Owns:**
- ✅ Place/Transition definitions (ID, name, label)
- ✅ Arc connectivity (structure)
- ✅ EC numbers (from KEGG/SBML)
- ✅ Stoichiometry
- ✅ Model metadata (name, dates, file path)

**What It Provides to Others:**
```python
# Read-only accessors
def get_species_list() -> List[Place]:
    """Returns list of all places with metadata"""
    
def get_reactions_list() -> List[Transition]:
    """Returns list of all transitions with metadata"""
    
def get_ec_number(transition_id: str) -> Optional[str]:
    """Returns EC number for a transition"""
```

**Who Uses It:**
- **DYNAMIC ANALYSES**: Reads species/reactions for kinetic parameter mapping
- **TOPOLOGY**: Reads structure for graph analysis
- **PROVENANCE**: Reads metadata for source tracking

---

### 2. DYNAMIC ANALYSES Category (Owner of Kinetics & Simulation)

**What It Owns:**
- ✅ Kinetic parameters (Km, Vmax, Kcat, Ki, k)
- ✅ Enrichment data (BRENDA, SABIO-RK)
- ✅ Parameter sources and citations
- ✅ **Simulation results** (time-series, rates, fluxes) ← **PRIMARY FOCUS**

**What It Provides to Others:**
```python
# Read-only accessors
def get_kinetic_parameters(transition_id: str) -> Dict:
    """Returns kinetic params for a transition"""
    
def get_simulation_results() -> SimulationResults:
    """Returns complete simulation data"""
    
def get_time_series(place_id: str) -> List[Tuple[float, int]]:
    """Returns time-series for a place"""
    
def get_active_reactions() -> List[str]:
    """Returns list of reactions that fired during simulation"""
```

**Who Uses It:**
- **TOPOLOGY**: Can highlight "active paths" based on simulation results
- **MODELS**: Can annotate species table with initial/final token counts
- **PROVENANCE**: Can record simulation run metadata

---

### 3. TOPOLOGY ANALYSES Category (Owner of Graph Metrics)

**What It Owns:**
- ✅ Degree distribution
- ✅ Connected components
- ✅ Cycles detection
- ✅ Locality regions
- ✅ Source-Sink paths
- ✅ Structural invariants

**What It Provides to Others:**
```python
# Read-only accessors
def get_critical_transitions() -> List[str]:
    """Returns high-degree transitions (hubs)"""
    
def get_source_sink_paths() -> List[List[str]]:
    """Returns flow paths through network"""
    
def get_bottlenecks() -> List[str]:
    """Returns transition IDs that are bottlenecks"""
```

**Who Uses It:**
- **DYNAMIC ANALYSES**: Can highlight bottlenecks in flux distribution chart
- **MODELS**: Can annotate reactions table with degree/criticality

---

### 4. PROVENANCE Category (Owner of History)

**What It Owns:**
- ✅ Import sources (KEGG ID, organism, date)
- ✅ Transformation history
- ✅ Edit logs
- ✅ Simulation run records (optional)

**What It Provides to Others:**
```python
# Read-only accessors
def get_import_metadata() -> Dict:
    """Returns source pathway info"""
    
def get_data_source(field: str) -> str:
    """Returns origin of a specific data field"""
    
def get_simulation_history() -> List[SimulationRun]:
    """Returns all simulation runs performed"""
```

**Who Uses It:**
- **MODELS**: Shows import provenance section
- **DYNAMIC ANALYSES**: Shows enrichment sources
- All categories can trace data lineage

---

## Focused Plan: Dynamic Analyses Category

### Core Responsibility
**Dynamic Analyses is the PRIMARY owner of simulation results.**

### What Dynamic Analyses Should Display

```
DYNAMIC ANALYSES
├── Summary
│   └── "X species, Y reactions, Z enriched params, 1 simulation run"
│
├── 📊 Simulation Data ⭐ PRIMARY FOCUS
│   ├── Run Metadata
│   │   ├── Duration: 60s
│   │   ├── Time Step: 0.006s (10000 steps)
│   │   ├── Time Scale: 2.0x
│   │   └── Completion: 100%
│   │
│   ├── Species Concentration Table
│   │   ├── Initial/Final/Min/Max/Avg
│   │   └── Change (Δ) and Rate (Δ/t)
│   │
│   └── Reaction Activity Table
│       ├── Firing Count/Rate/Flux
│       └── Contribution % and Status
│
├── 📈 Time Series Plots (FUTURE)
│   ├── Interactive plots (matplotlib)
│   ├── Multi-line: selected species
│   └── Export to PNG/SVG
│
├── 🧪 Kinetic Parameters
│   ├── Parameters Table (Km, Vmax, Kcat, Ki, k)
│   ├── Color-coded by source
│   └── Substrate specificity
│
└── 📚 Enrichment & Citations
    ├── BRENDA enrichment details
    ├── SABIO-RK data
    └── Literature references
```

---

## Collaborative Enhancements

### 1. Cross-Category Data Sharing (Read-Only)

**Scenario**: User runs simulation in Dynamic Analyses

**Automatic Updates:**
```
Dynamic Analyses                 Other Categories
└── Simulation Complete   ───>   MODELS
    │                            └── Species Table: Show Δ tokens
    │                                (optional annotation)
    │
    └──────────────────────────>  TOPOLOGY
                                  └── Highlight active paths
                                      (based on fired transitions)
```

**Implementation:**
```python
# In SimulationController
def on_simulation_complete(self):
    # 1. Notify Dynamic Analyses (primary)
    if self.dynamic_analyses_category:
        self.dynamic_analyses_category.refresh()
    
    # 2. Optional: Notify other categories
    if self.models_category:
        self.models_category.on_simulation_complete()
    
    if self.topology_category:
        self.topology_category.on_simulation_complete()
```

---

### 2. Shared Data Models (Common Interface)

**Create: `src/shypn/report/shared_data.py`**

```python
"""Shared data models for cross-category collaboration."""

class SharedSimulationResults:
    """Read-only view of simulation results.
    
    Available to all categories for annotation/highlighting.
    """
    
    def __init__(self, data_collector, controller):
        self._data_collector = data_collector
        self._controller = controller
        
    @property
    def duration(self) -> float:
        return self._controller.settings.duration
        
    @property
    def num_steps(self) -> int:
        return len(self._data_collector.time_points)
        
    def get_final_tokens(self, place_id: str) -> int:
        """Get final token count for a place."""
        series = self._data_collector.place_data.get(place_id, [])
        return series[-1] if series else 0
        
    def get_total_firings(self, transition_id: str) -> int:
        """Get total firing count for a transition."""
        series = self._data_collector.transition_data.get(transition_id, [])
        return series[-1] if series else 0
        
    def get_active_transitions(self) -> List[str]:
        """Get list of transitions that fired during simulation."""
        active = []
        for tid, series in self._data_collector.transition_data.items():
            if series and series[-1] > 0:
                active.append(tid)
        return active
```

**Usage in Other Categories:**

```python
# In MODELS category
def _populate_species_table(self):
    # ... existing code ...
    
    # Optional: Annotate with simulation results
    if self.shared_sim_results:
        final_tokens = self.shared_sim_results.get_final_tokens(place.id)
        # Add annotation column or highlight changed rows
        
# In TOPOLOGY category  
def _highlight_active_paths(self):
    # ... existing code ...
    
    # Optional: Highlight arcs involved in active transitions
    if self.shared_sim_results:
        active = self.shared_sim_results.get_active_transitions()
        # Highlight these transitions in topology view
```

---

### 3. Export Coordination

**Each Category Exports Its Domain:**

```python
# Report Panel coordinates exports
def export_full_report(self, format='html'):
    """Export complete report from all categories."""
    
    report = {
        'models': self.models_category.export_data(),
        'dynamic_analyses': self.dynamic_analyses_category.export_data(),
        'topology': self.topology_category.export_data(),
        'provenance': self.provenance_category.export_data()
    }
    
    if format == 'html':
        return self._format_html(report)
    elif format == 'json':
        return json.dumps(report, indent=2)
    elif format == 'csv':
        return self._export_csv_bundle(report)
```

**Each Category Provides:**
```python
class BaseReportCategory:
    def export_data(self) -> Dict:
        """Export category data as structured dict."""
        raise NotImplementedError
        
    def export_to_html(self) -> str:
        """Export category as HTML fragment."""
        raise NotImplementedError
        
    def export_to_csv(self) -> Dict[str, str]:
        """Export tables as CSV files (name → content)."""
        return {}
```

---

## Implementation Priority

### Phase 1: Dynamic Analyses Simulation Results (HIGH PRIORITY) ⭐
**Focus**: Implement simulation data collection and display
- ✅ Create DataCollector in engine
- ✅ Create analyzers (SpeciesAnalyzer, ReactionAnalyzer)
- ✅ Create simulation data tables in Dynamic Analyses
- ✅ Wire up to controller

**Why First**: 
- Most valuable for scientists (quantitative results)
- Self-contained (doesn't depend on other categories)
- User's primary interest

---

### Phase 2: Shared Data Interface (MEDIUM PRIORITY)
**Focus**: Create read-only data sharing between categories
- Create `shared_data.py` with common interfaces
- Allow MODELS to optionally annotate with simulation results
- Allow TOPOLOGY to highlight active paths

**Why Second**:
- Enhances user experience with cross-references
- Not critical for core functionality
- Can be added incrementally

---

### Phase 3: Export Coordination (MEDIUM PRIORITY)
**Focus**: Unified export from all categories
- Each category implements export_data()
- Report Panel coordinates multi-format export
- Single button exports entire report

**Why Third**:
- Nice-to-have for publication
- Can export individual categories for now
- Lower priority than getting data displayed

---

### Phase 4: Real-Time Cross-Updates (LOW PRIORITY)
**Focus**: Automatic refresh of other categories on simulation
- Dynamic Analyses refreshes automatically (already planned)
- Optional: MODELS shows token changes
- Optional: TOPOLOGY highlights active paths

**Why Last**:
- Enhancement, not core feature
- May be distracting if too automatic
- User can manually refresh if needed

---

## Architecture Principles

### 1. **Single Owner, Multiple Readers**
- Each category OWNS its data domain
- Other categories READ via accessors
- No direct modification across categories

### 2. **Loose Coupling**
- Categories don't import each other
- Share data via Report Panel coordinator
- Use interfaces/protocols, not concrete classes

### 3. **Progressive Enhancement**
- Core functionality works standalone
- Cross-category features are optional enhancements
- Graceful degradation if data unavailable

### 4. **User Control**
- Manual refresh button (existing)
- User chooses when to export
- Optional automatic updates (off by default)

---

## Summary: Focus on Dynamic Analyses First

### What We're Building (Priority Order)

**🎯 PHASE 1: Core Simulation Results (START HERE)**
```
DYNAMIC ANALYSES
└── 📊 Simulation Data
    ├── Run Metadata (duration, steps, time scale)
    ├── Species Concentration Table (8 columns)
    └── Reaction Activity Table (7 columns)
```

**🎯 PHASE 2: Time Series Visualization**
```
DYNAMIC ANALYSES
└── 📈 Time Series Plots
    ├── Interactive matplotlib plots
    └── Click place/transition to add/remove from plot
```

**🔗 PHASE 3: Cross-Category Sharing (Optional)**
```
Shared Data Interface
├── MODELS: Optional token change annotations
├── TOPOLOGY: Optional active path highlighting
└── PROVENANCE: Optional simulation run records
```

**📤 PHASE 4: Unified Export**
```
Report Panel
└── Export All Categories
    ├── HTML with all sections
    ├── JSON with structured data
    └── CSV bundle with all tables
```

---

## Implementation Guideline

### For Dynamic Analyses (Primary Focus):

1. **OWN the simulation results domain completely**
2. **Display comprehensive simulation data**
3. **Provide export functionality (CSV, JSON)**
4. **Eventually provide read-only accessors for others**

### For Other Categories (Supportive Role):

1. **MODELS**: Continues showing static structure
2. **TOPOLOGY**: Continues showing graph metrics
3. **PROVENANCE**: Continues showing data sources
4. **All**: Can OPTIONALLY read simulation results for annotations

### Collaboration Pattern:

```python
# Dynamic Analyses (owner)
class DynamicAnalysesCategory:
    def get_simulation_results(self) -> SharedSimulationResults:
        """Provide read-only view for other categories."""
        return SharedSimulationResults(self.data_collector, self.controller)

# Models (reader)
class ModelsCategory:
    def refresh(self):
        # ... existing code ...
        
        # Optional enhancement
        sim_results = self.report_panel.get_simulation_results()
        if sim_results:
            self._annotate_with_simulation_data(sim_results)
```

---

## Conclusion

**Primary Goal**: Build excellent simulation results display in Dynamic Analyses

**Secondary Goal**: Enable optional cross-category annotations

**Guiding Principle**: Each category excels at its domain, collaborates without coupling

**User Benefit**: Comprehensive, well-organized scientific report with optional cross-references

**Start Point**: Phase 1 - Core simulation data collection and display in Dynamic Analyses ✅
