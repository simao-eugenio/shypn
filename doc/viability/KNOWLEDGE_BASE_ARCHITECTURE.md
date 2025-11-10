# Model Knowledge Base Architecture

**Purpose:** Unified data repository that aggregates knowledge from all Shypn panels and modules to enable intelligent inference by the Viability Panel.

**Date:** November 9, 2025  
**Status:** Design Phase

---

## Vision

The **ModelKnowledgeBase** transforms Shypn from separate analysis tools into an intelligent system that:

1. **Aggregates** multi-domain knowledge (topology, biology, biochemistry, dynamics)
2. **Synthesizes** cross-domain insights
3. **Enables** intelligent inference for model repair
4. **Persists** knowledge with the model for reuse

---

## Core Design Principles

### 1. **One Knowledge Base Per Model**
- Each model (drawing_area) has its own `ModelKnowledgeBase` instance
- Stored in `model_canvas_loader.knowledge_bases[drawing_area]`
- Lifetime: Created on model load, persisted on save, destroyed on close

### 2. **Incremental Population**
- Knowledge base starts empty
- Populated as user runs analyses
- Each panel/module contributes its domain knowledge
- Always reflects "what we know so far"

### 3. **Multi-Domain Structure**
- **Structural** (Petri Net graph)
- **Behavioral** (Topology analysis results)
- **Biological** (KEGG/SBML metadata)
- **Biochemical** (BRENDA kinetic parameters)
- **Dynamic** (Simulation results)

### 4. **Query-Oriented API**
- Easy to query: `kb.get_place_compound_id('P5')`
- Easy to update: `kb.update_topology(p_invariants=[...])`
- Easy to reason: `kb.infer_basal_marking('P5')`

---

## Schema Design

### ModelKnowledgeBase Class Structure

```python
class ModelKnowledgeBase:
    """Unified knowledge repository for a single Petri Net model.
    
    Aggregates knowledge from:
    - Topology Panel (structural/behavioral analysis)
    - Pathway Panel (biological context)
    - BRENDA (biochemical parameters)
    - Analyses Panel (dynamic behavior)
    - User annotations
    """
    
    def __init__(self, model):
        self.model = model  # ShypnModel reference
        
        # 1. STRUCTURAL KNOWLEDGE (Petri Net graph)
        self.places = {}         # place_id -> PlaceKnowledge
        self.transitions = {}    # transition_id -> TransitionKnowledge
        self.arcs = {}          # arc_id -> ArcKnowledge
        
        # 2. BEHAVIORAL KNOWLEDGE (Topology results)
        self.p_invariants = []   # List of P-invariant vectors
        self.t_invariants = []   # List of T-invariant vectors
        self.siphons = []        # List of minimal siphons
        self.traps = []          # List of minimal traps
        self.liveness_status = {} # transition_id -> LivenessLevel
        self.deadlock_states = [] # List of deadlock markings
        self.boundedness = {}    # place_id -> bound value
        
        # 3. BIOLOGICAL KNOWLEDGE (KEGG/SBML)
        self.pathway_info = None  # PathwayInfo (name, organism, etc.)
        self.compounds = {}      # compound_id -> CompoundInfo
        self.reactions = {}      # reaction_id -> ReactionInfo
        
        # 4. BIOCHEMICAL KNOWLEDGE (BRENDA)
        self.kinetic_parameters = {} # transition_id -> KineticParams
        self.enzyme_data = {}        # ec_number -> EnzymeData
        
        # 5. DYNAMIC KNOWLEDGE (Simulation)
        self.simulation_traces = []  # List of SimulationTrace
        self.steady_states = []      # List of steady-state markings
        
        # 6. ISSUE DATABASE
        self.issues = []         # List of Issue objects
        
        # 7. METADATA
        self.last_updated = {}   # domain -> timestamp
        self.confidence = {}     # knowledge_item -> confidence score
```

---

## Domain-Specific Knowledge Structures

### 1. Structural Knowledge

#### PlaceKnowledge
```python
@dataclass
class PlaceKnowledge:
    """Knowledge about a single place."""
    place_id: str
    label: str
    
    # Biological context
    compound_id: Optional[str] = None      # KEGG compound ID (e.g., "C00031")
    compound_name: Optional[str] = None    # e.g., "D-Glucose"
    
    # Current state
    current_marking: int = 0
    
    # Topology analysis results
    in_p_invariants: List[int] = field(default_factory=list)  # Which P-invariants include this
    in_siphons: List[int] = field(default_factory=list)       # Which siphons include this
    in_traps: List[int] = field(default_factory=list)         # Which traps include this
    is_bounded: bool = False
    bound_value: Optional[int] = None
    
    # Biochemical context
    basal_concentration: Optional[float] = None  # From BRENDA/literature (mM)
    concentration_range: Optional[Tuple[float, float]] = None  # (min, max) mM
    
    # Dynamic behavior
    token_history: List[int] = field(default_factory=list)  # From simulation
    avg_tokens: Optional[float] = None
    peak_tokens: Optional[int] = None
    
    # Constraints for repair
    must_have_tokens: bool = False  # Required for liveness
    suggested_initial_marking: Optional[int] = None
```

#### TransitionKnowledge
```python
@dataclass
class TransitionKnowledge:
    """Knowledge about a single transition."""
    transition_id: str
    label: str
    
    # Biological context
    reaction_id: Optional[str] = None      # KEGG reaction ID (e.g., "R00200")
    reaction_name: Optional[str] = None    # e.g., "Hexokinase"
    ec_number: Optional[str] = None        # e.g., "2.7.1.1"
    
    # Topology analysis results
    liveness_level: Optional[str] = None   # "L4-live", "L3-live", "L1-live", "dead"
    in_t_invariants: List[int] = field(default_factory=list)
    is_deadlock_causing: bool = False
    
    # Biochemical kinetics
    km_values: Dict[str, float] = field(default_factory=dict)  # substrate -> Km (mM)
    vmax: Optional[float] = None           # Maximum velocity
    kcat: Optional[float] = None           # Turnover number (1/sec)
    
    # Current state
    current_rate: Optional[float] = None   # tokens/sec
    is_enabled: bool = False
    
    # Dynamic behavior
    firing_count: int = 0                  # Times fired in simulation
    avg_firing_rate: Optional[float] = None
    
    # Constraints for repair
    must_be_live: bool = False
    suggested_firing_rate: Optional[float] = None
```

#### ArcKnowledge
```python
@dataclass
class ArcKnowledge:
    """Knowledge about a single arc."""
    arc_id: str
    source_id: str
    target_id: str
    arc_type: str  # "place_to_transition", "transition_to_place"
    
    # Current state
    current_weight: int = 1
    
    # Biological context
    stoichiometry: Optional[int] = None    # From KEGG/SBML reaction
    
    # Constraints for repair
    suggested_weight: Optional[int] = None
    biological_justification: Optional[str] = None
```

---

### 2. Behavioral Knowledge

#### P-Invariant
```python
@dataclass
class PInvariant:
    """A P-invariant (conservation law)."""
    vector: List[int]           # Coefficient for each place
    place_ids: List[str]        # Place IDs in order
    conserved_value: int        # Weighted sum of tokens
    
    # Semantic interpretation
    name: Optional[str] = None          # e.g., "ATP/ADP cycle"
    biological_meaning: Optional[str] = None
```

#### T-Invariant
```python
@dataclass
class TInvariant:
    """A T-invariant (firing sequence that returns to initial state)."""
    vector: List[int]           # Firing count for each transition
    transition_ids: List[str]   # Transition IDs in order
    
    # Semantic interpretation
    name: Optional[str] = None          # e.g., "Glycolysis cycle"
    biological_meaning: Optional[str] = None
```

#### Siphon/Trap
```python
@dataclass
class Siphon:
    """A minimal siphon (can become empty and stay empty)."""
    place_ids: List[str]
    is_minimal: bool = True
    is_properly_marked: bool = False  # Has tokens in current marking
    
    # Repair suggestion
    suggested_source: Optional[str] = None  # Place to add controlled source
    suggested_rate: Optional[float] = None
```

---

### 3. Biological Knowledge

#### PathwayInfo
```python
@dataclass
class PathwayInfo:
    """Biological pathway metadata from KEGG/SBML."""
    pathway_id: str            # e.g., "hsa00010"
    pathway_name: str          # e.g., "Glycolysis / Gluconeogenesis"
    organism: Optional[str] = None    # e.g., "Homo sapiens"
    source: str = "unknown"    # "kegg", "sbml", "user"
    
    # Context
    description: Optional[str] = None
    biological_function: Optional[str] = None
```

#### CompoundInfo
```python
@dataclass
class CompoundInfo:
    """Information about a metabolic compound."""
    compound_id: str           # KEGG ID (e.g., "C00031")
    name: str
    formula: Optional[str] = None
    
    # Biochemical properties
    molecular_weight: Optional[float] = None
    basal_concentration: Optional[float] = None  # mM
    concentration_range: Optional[Tuple[float, float]] = None
    
    # Context
    role: Optional[str] = None  # "substrate", "product", "cofactor"
```

#### ReactionInfo
```python
@dataclass
class ReactionInfo:
    """Information about a biochemical reaction."""
    reaction_id: str           # KEGG ID (e.g., "R00200")
    name: str
    ec_number: Optional[str] = None
    
    # Stoichiometry
    substrates: List[Tuple[str, int]] = field(default_factory=list)  # (compound_id, coefficient)
    products: List[Tuple[str, int]] = field(default_factory=list)
    
    # Context
    reversible: bool = False
    pathway_context: Optional[str] = None
```

---

### 4. Biochemical Knowledge

#### KineticParams
```python
@dataclass
class KineticParams:
    """Kinetic parameters for a transition/reaction."""
    transition_id: str
    ec_number: Optional[str] = None
    
    # Michaelis-Menten parameters
    km_values: Dict[str, float] = field(default_factory=dict)  # substrate -> Km (mM)
    vmax: Optional[float] = None           # Maximum velocity (mM/sec)
    kcat: Optional[float] = None           # Turnover number (1/sec)
    
    # Additional parameters
    ki_values: Dict[str, float] = field(default_factory=dict)  # inhibitor -> Ki
    optimal_ph: Optional[float] = None
    optimal_temp: Optional[float] = None  # Celsius
    
    # Data source
    source: str = "brenda"
    organism: Optional[str] = None
    confidence: float = 0.5  # 0.0 to 1.0
```

---

### 5. Dynamic Knowledge

#### SimulationTrace
```python
@dataclass
class SimulationTrace:
    """Results from a simulation run."""
    timestamp: datetime
    initial_marking: Dict[str, int]  # place_id -> tokens
    
    # Time series data
    time_points: List[float]         # seconds
    place_traces: Dict[str, List[int]]  # place_id -> token counts over time
    transition_firings: Dict[str, List[int]]  # transition_id -> firing times
    
    # Summary statistics
    final_marking: Dict[str, int]
    total_firings: Dict[str, int]    # transition_id -> count
    reached_steady_state: bool = False
```

---

### 6. Issue Database

#### Issue
```python
@dataclass
class Issue:
    """A problem detected by analysis."""
    issue_id: str              # Unique ID
    severity: str              # "critical", "warning", "info"
    category: str              # "liveness", "deadlock", "boundedness", "siphon"
    
    # Description
    title: str
    description: str
    
    # Context
    affected_elements: List[str]  # IDs of places/transitions involved
    detected_by: str           # "topology", "simulation", "brenda", etc.
    timestamp: datetime
    
    # Root cause analysis
    root_causes: List[str] = field(default_factory=list)
    constraints: List[str] = field(default_factory=list)  # Constraints for repair
    
    # Repair suggestions (to be filled by inference engine)
    suggestions: List['RepairSuggestion'] = field(default_factory=list)
```

#### RepairSuggestion
```python
@dataclass
class RepairSuggestion:
    """A suggested fix for an issue."""
    suggestion_id: str
    issue_id: str              # Which issue this fixes
    
    # Type of repair
    repair_type: str           # "add_marking", "add_arc", "modify_weight", "add_source", "modify_rate"
    
    # Specification
    target_element: str        # ID of element to modify
    parameter: str             # What to change (e.g., "initial_marking", "weight", "rate")
    suggested_value: Any       # New value
    
    # Justification (multi-domain reasoning)
    reasoning: List[str] = field(default_factory=list)  # Step-by-step explanation
    knowledge_sources: List[str] = field(default_factory=list)  # Which analyses contributed
    confidence: float = 0.5    # 0.0 to 1.0
    
    # Impact assessment
    fixes_issues: List[str] = field(default_factory=list)     # Issue IDs
    may_cause_issues: List[str] = field(default_factory=list) # Potential side effects
```

---

## Knowledge Base API

### Update Methods (Called by Panels)

```python
class ModelKnowledgeBase:
    
    # === TOPOLOGY PANEL ===
    def update_topology_structural(self, places, transitions, arcs):
        """Update structural knowledge from Petri Net graph."""
        pass
    
    def update_p_invariants(self, invariants: List[PInvariant]):
        """Update P-invariants from topology analysis."""
        pass
    
    def update_t_invariants(self, invariants: List[TInvariant]):
        """Update T-invariants from topology analysis."""
        pass
    
    def update_siphons_traps(self, siphons: List[Siphon], traps: List):
        """Update siphons and traps from topology analysis."""
        pass
    
    def update_liveness(self, liveness_results: Dict[str, str]):
        """Update liveness analysis results."""
        pass
    
    def update_deadlocks(self, deadlock_states: List):
        """Update deadlock analysis results."""
        pass
    
    def update_boundedness(self, boundedness: Dict[str, int]):
        """Update boundedness analysis results."""
        pass
    
    # === PATHWAY PANEL ===
    def update_pathway_metadata(self, pathway_info: PathwayInfo):
        """Update pathway context from KEGG/SBML import."""
        pass
    
    def update_compounds(self, compounds: Dict[str, CompoundInfo]):
        """Update compound information."""
        pass
    
    def update_reactions(self, reactions: Dict[str, ReactionInfo]):
        """Update reaction information."""
        pass
    
    def link_place_to_compound(self, place_id: str, compound_id: str):
        """Link a place to a KEGG compound."""
        pass
    
    def link_transition_to_reaction(self, transition_id: str, reaction_id: str):
        """Link a transition to a KEGG reaction."""
        pass
    
    # === BRENDA INTEGRATION ===
    def update_kinetic_parameters(self, transition_id: str, params: KineticParams):
        """Update kinetic parameters from BRENDA query."""
        pass
    
    def update_basal_concentrations(self, concentrations: Dict[str, float]):
        """Update basal metabolite concentrations."""
        pass
    
    # === ANALYSES PANEL ===
    def add_simulation_trace(self, trace: SimulationTrace):
        """Add simulation results."""
        pass
    
    def update_current_marking(self, marking: Dict[str, int]):
        """Update current model state."""
        pass
    
    # === ISSUE MANAGEMENT ===
    def add_issue(self, issue: Issue):
        """Register a detected issue."""
        pass
    
    def add_suggestion(self, issue_id: str, suggestion: RepairSuggestion):
        """Add a repair suggestion to an issue."""
        pass
```

### Query Methods (Called by Viability Panel)

```python
    # === STRUCTURAL QUERIES ===
    def get_place(self, place_id: str) -> Optional[PlaceKnowledge]:
        """Get complete knowledge about a place."""
        pass
    
    def get_transition(self, transition_id: str) -> Optional[TransitionKnowledge]:
        """Get complete knowledge about a transition."""
        pass
    
    def get_dead_transitions(self) -> List[str]:
        """Get all dead transitions."""
        pass
    
    def get_unbounded_places(self) -> List[str]:
        """Get all unbounded places."""
        pass
    
    # === BIOLOGICAL QUERIES ===
    def get_compound_for_place(self, place_id: str) -> Optional[CompoundInfo]:
        """Get biological compound info for a place."""
        pass
    
    def get_reaction_for_transition(self, transition_id: str) -> Optional[ReactionInfo]:
        """Get biological reaction info for a transition."""
        pass
    
    def get_basal_concentration(self, place_id: str) -> Optional[float]:
        """Get basal concentration for a place's compound."""
        pass
    
    # === BIOCHEMICAL QUERIES ===
    def get_kinetic_params(self, transition_id: str) -> Optional[KineticParams]:
        """Get kinetic parameters for a transition."""
        pass
    
    def get_km_value(self, transition_id: str, substrate_place_id: str) -> Optional[float]:
        """Get Km value for a specific substrate."""
        pass
    
    # === BEHAVIORAL QUERIES ===
    def get_conserved_places(self, place_id: str) -> List[str]:
        """Get places conserved with this place (same P-invariant)."""
        pass
    
    def get_cycle_transitions(self, transition_id: str) -> List[str]:
        """Get transitions in same T-invariant cycle."""
        pass
    
    def is_in_siphon(self, place_id: str) -> bool:
        """Check if place is in any siphon."""
        pass
    
    # === ISSUE QUERIES ===
    def get_all_issues(self) -> List[Issue]:
        """Get all detected issues."""
        pass
    
    def get_critical_issues(self) -> List[Issue]:
        """Get only critical issues."""
        pass
    
    def get_issues_for_element(self, element_id: str) -> List[Issue]:
        """Get all issues affecting an element."""
        pass
```

### Inference Methods (Called by Inference Engines)

```python
    # === INTELLIGENT INFERENCE ===
    def infer_initial_marking(self, place_id: str) -> Optional[int]:
        """Infer appropriate initial marking using all available knowledge.
        
        Considers:
        - Basal concentration (from biochemical data)
        - P-invariant conservation (from topology)
        - Avoid deadlock states (from behavioral analysis)
        - Pathway context (from biological data)
        """
        pass
    
    def infer_arc_weight(self, arc_id: str) -> Optional[int]:
        """Infer appropriate arc weight.
        
        Considers:
        - Stoichiometry from KEGG/SBML
        - T-invariant preservation
        - Kinetic ratios
        """
        pass
    
    def infer_firing_rate(self, transition_id: str) -> Optional[float]:
        """Infer appropriate firing rate.
        
        Considers:
        - Km/Vmax from BRENDA
        - Steady-state requirements from T-invariants
        - Biological time scales
        """
        pass
    
    def suggest_source_placement(self) -> List[Tuple[str, float]]:
        """Suggest where to add sources and at what rate.
        
        Returns: List of (place_id, rate) tuples
        
        Considers:
        - Structural siphons
        - Basal concentrations
        - Liveness requirements
        """
        pass
```

---

## Integration Points

### 1. Topology Panel Integration

**Location:** `src/shypn/ui/panels/topology/topology_panel.py`

**Hook points:**
```python
# After P-invariant analysis completes
def _on_p_invariants_complete(self, results):
    # ... existing code ...
    
    # NEW: Update knowledge base
    if self.model_canvas and hasattr(self.model_canvas, 'knowledge_base'):
        kb = self.model_canvas.knowledge_base
        invariants = self._parse_p_invariants(results)
        kb.update_p_invariants(invariants)

# After liveness analysis completes
def _on_liveness_complete(self, results):
    # ... existing code ...
    
    # NEW: Update knowledge base
    if self.model_canvas and hasattr(self.model_canvas, 'knowledge_base'):
        kb = self.model_canvas.knowledge_base
        liveness_status = self._parse_liveness(results)
        kb.update_liveness(liveness_status)

# Similar hooks for:
# - T-invariants
# - Siphons/Traps
# - Deadlocks
# - Boundedness
```

### 2. Pathway Panel Integration

**Location:** `src/shypn/ui/panels/pathway/pathway_panel.py`

**Hook points:**
```python
# After KEGG pathway import
def on_kegg_import_complete(self, pathway_data):
    # ... existing code ...
    
    # NEW: Update knowledge base
    if self.model_canvas and hasattr(self.model_canvas, 'knowledge_base'):
        kb = self.model_canvas.knowledge_base
        
        # Update pathway metadata
        pathway_info = PathwayInfo(...)
        kb.update_pathway_metadata(pathway_info)
        
        # Update compounds and reactions
        kb.update_compounds(pathway_data.compounds)
        kb.update_reactions(pathway_data.reactions)
        
        # Link places to compounds
        for place_id, compound_id in pathway_data.mappings.items():
            kb.link_place_to_compound(place_id, compound_id)
```

### 3. BRENDA Integration

**Location:** `src/shypn/brenda/` (various files)

**Hook points:**
```python
# After successful BRENDA query
def on_brenda_query_complete(self, ec_number, results):
    # ... existing code ...
    
    # NEW: Update knowledge base
    if self.model_canvas and hasattr(self.model_canvas, 'knowledge_base'):
        kb = self.model_canvas.knowledge_base
        
        # Update kinetic parameters for matching transitions
        for transition in self.get_transitions_with_ec(ec_number):
            params = KineticParams(
                transition_id=transition.id,
                ec_number=ec_number,
                km_values=results.km_values,
                vmax=results.vmax,
                kcat=results.kcat,
                source='brenda',
                organism=results.organism
            )
            kb.update_kinetic_parameters(transition.id, params)
```

### 4. Model Canvas Loader Integration

**Location:** `src/shypn/helpers/model_canvas_loader.py`

**Changes:**
```python
class ModelCanvasLoader:
    def __init__(self):
        # ... existing code ...
        
        # NEW: Knowledge bases per model
        self.knowledge_bases = {}  # drawing_area -> ModelKnowledgeBase
    
    def on_new_model_created(self, drawing_area):
        # ... existing code ...
        
        # NEW: Create knowledge base for new model
        model = self.get_model(drawing_area)
        kb = ModelKnowledgeBase(model)
        self.knowledge_bases[drawing_area] = kb
        
        # Make accessible to canvas manager
        manager = self.get_canvas_manager(drawing_area)
        if manager:
            manager.knowledge_base = kb
    
    def on_model_loaded(self, drawing_area, filepath):
        # ... existing code ...
        
        # NEW: Try to load persisted knowledge base
        kb_file = filepath + '.kb.json'
        if os.path.exists(kb_file):
            kb = ModelKnowledgeBase.load_from_file(kb_file)
            self.knowledge_bases[drawing_area] = kb
        else:
            # Create new knowledge base
            model = self.get_model(drawing_area)
            kb = ModelKnowledgeBase(model)
            self.knowledge_bases[drawing_area] = kb
    
    def on_model_saved(self, drawing_area, filepath):
        # ... existing code ...
        
        # NEW: Persist knowledge base
        if drawing_area in self.knowledge_bases:
            kb = self.knowledge_bases[drawing_area]
            kb_file = filepath + '.kb.json'
            kb.save_to_file(kb_file)
```

---

## Persistence Strategy

### File Format: JSON

**Knowledge base saved as:** `modelname.shypn.kb.json`

**Structure:**
```json
{
  "version": "1.0",
  "model_file": "glycolysis.shypn",
  "last_updated": "2025-11-09T21:45:00Z",
  
  "structural": {
    "places": {
      "P1": {
        "label": "Glucose",
        "compound_id": "C00031",
        "compound_name": "D-Glucose",
        "current_marking": 10,
        "basal_concentration": 5.0,
        "in_p_invariants": [0, 2],
        "suggested_initial_marking": 10
      }
    },
    "transitions": { ... },
    "arcs": { ... }
  },
  
  "behavioral": {
    "p_invariants": [ ... ],
    "t_invariants": [ ... ],
    "siphons": [ ... ],
    "liveness": { ... }
  },
  
  "biological": {
    "pathway": { ... },
    "compounds": { ... },
    "reactions": { ... }
  },
  
  "biochemical": {
    "kinetic_params": { ... }
  },
  
  "dynamic": {
    "simulation_traces": [ ... ]
  },
  
  "issues": [ ... ]
}
```

**Advantages:**
- Human-readable
- Easy to debug
- Can be version-controlled
- Easy to merge/diff

---

## Implementation Roadmap

### Phase 0: Foundation (Week 1)
1. Create `ModelKnowledgeBase` class with data structures
2. Implement serialization (save/load JSON)
3. Integrate with `model_canvas_loader` (create on model load)
4. Add basic query methods

### Phase 1: Topology Integration (Week 2)
1. Add update hooks to Topology Panel categories
2. Test P-invariant → knowledge base flow
3. Test liveness → knowledge base flow
4. Verify persistence works

### Phase 2: Biological Integration (Week 3)
1. Add update hooks to Pathway Panel
2. Test KEGG import → knowledge base flow
3. Test place/compound linking
4. Add biological queries

### Phase 3: BRENDA Integration (Week 4)
1. Add update hooks to BRENDA query module
2. Test kinetic parameter extraction
3. Add biochemical queries

### Phase 4: Inference Engine (Weeks 5-6)
1. Implement `infer_initial_marking()`
2. Implement `infer_arc_weight()`
3. Implement `infer_firing_rate()`
4. Implement `suggest_source_placement()`

### Phase 5: Viability Panel Integration (Week 7)
1. Connect ViabilityPanel to knowledge base
2. Display knowledge-backed suggestions
3. Show multi-domain reasoning
4. Test end-to-end flow

---

## Success Criteria

**Knowledge base is successful when:**

1. ✅ Every analysis automatically contributes knowledge
2. ✅ Viability Panel can query cross-domain information
3. ✅ Inference engines make biologically valid suggestions
4. ✅ Reasoning is transparent (shows which knowledge was used)
5. ✅ Knowledge persists with model (survives save/load)
6. ✅ Performance acceptable (<100ms query time)

---

## Example: Multi-Domain Inference

**Scenario:** Dead transition T5 (Hexokinase reaction)

**Knowledge Base Query Flow:**
```python
# 1. Get transition knowledge
t5 = kb.get_transition('T5')
# → label: "Hexokinase"
# → ec_number: "2.7.1.1"
# → liveness_level: "dead"

# 2. Get biological context
reaction = kb.get_reaction_for_transition('T5')
# → substrates: [("C00031", "D-Glucose"), ("C00002", "ATP")]
# → products: [("C00668", "G6P"), ("C00008", "ADP")]

# 3. Find input places
input_places = kb.get_input_places('T5')
# → ["P3", "P7"]  (Glucose, ATP)

# 4. Check if input places have tokens
p3_marking = kb.get_place('P3').current_marking
# → 0 (empty!)

# 5. Get basal concentration
basal = kb.get_basal_concentration('P3')
# → 5.0 mM (from BRENDA)

# 6. Check if in siphon
in_siphon = kb.is_in_siphon('P3')
# → True (structural problem)

# 7. INFERENCE: Suggest adding source to P3
suggestion = RepairSuggestion(
    repair_type="add_source",
    target_element="P3",
    suggested_value=0.05,  # tokens/sec
    reasoning=[
        "T5 (Hexokinase) is dead because P3 (D-Glucose) has no tokens",
        "P3 is in a structural siphon (can become permanently empty)",
        "Basal D-Glucose concentration is 5.0 mM (from BRENDA)",
        "Suggest controlled source at P3 with rate 0.05 tokens/sec",
        "This maintains basal glucose level for glycolysis pathway"
    ],
    knowledge_sources=["topology", "brenda", "kegg"],
    confidence=0.85
)
```

This is **intelligent, multi-domain reasoning** - not possible without unified knowledge base!

---

## Next Steps

1. **Review this architecture** - Does it capture all necessary knowledge?
2. **Implement ModelKnowledgeBase class** - Start with data structures
3. **Add first integration hook** - Test with Topology Panel
4. **Build inference engine** - Start with marking inference

Ready to proceed with implementation?

