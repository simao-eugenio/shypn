# Signal Hierarchy Enhancement Plan
**Date**: January 2, 2026  
**Status**: Implementation Ready

## Current State Assessment

### Signal Hierarchy Theory (Established)
✅ **4 Signal Types** - Well-defined taxonomy:
- **ENERGY** (Ψ_e): ATP, NADH, energy metabolites - Lowest layer orchestrators
- **SPATIAL** (Ψ_s): Compartments, membranes - Universal constraints  
- **QUORUM** (Ψ_q): AHL, autoinducers - Cell-cell communication
- **REGULATORY** (Ψ_r): Transcription factors, kinases - Decision variables

✅ **Signal Flow Arcs** - Information transfer mechanism:
- Light gray color (0.7, 0.7, 0.7)
- Consume tokens (unlike test arcs)
- Connect signal places to transitions
- Enable hierarchical preemption

✅ **Layer Detection** - Topology-based hierarchy inference:
- Topological sorting from signal flow graph
- Acyclicity validation
- Preemption relationship detection
- Layer assignment (Layer 0, 1, 2, ...)

✅ **Automated Classification**:
- `SignalClassifierManager` with 4 specialized classifiers
- Lexical, topology, and dynamics analysis
- Confidence scoring and conflict resolution

### Gaps Identified

#### 1. **KEGG Import - Limited Signal Detection**
❌ Currently only marks enzymes/proteins as signals
❌ No cofactor detection (ATP, NADH not marked as signals)
❌ No layer inference during import
❌ Test arcs used instead of signal flow arcs for regulation

#### 2. **Enrichment - No Layer-Aware Processing**
❌ Stoichiometry service doesn't infer layers
❌ Signal source/sink builder doesn't consider hierarchy
❌ No validation of layer consistency

#### 3. **Signal vs Test Arc Classification**
❌ Ambiguous criteria for choosing arc type
❌ Catalytic vs information flow not well distinguished
❌ No automatic conversion based on context

## Enhancement Strategy

### Phase 1: Enhanced KEGG Import (HIGH PRIORITY)

#### 1.1 Cofactor Signal Detection
**Location**: `src/shypn/importer/kegg/compound_mapper.py`

```python
ENERGY_COFACTORS = {
    'ATP', 'ADP', 'AMP', 'GTP', 'GDP',
    'NADH', 'NAD', 'NAD+', 'NADPH', 'NADP', 'NADP+',
    'CoA', 'Acetyl-CoA', 'FAD', 'FADH2',
    'Pi', 'PPi'
}

def detect_energy_signals(place: Place) -> bool:
    """Detect if place is an energy signal cofactor."""
    # Normalize name
    norm_name = normalize_compound_name(place.name)
    
    # Check against energy cofactor database
    if norm_name in ENERGY_COFACTORS:
        place.is_signal_place = True
        place.signal_type = SignalType.ENERGY
        return True
    
    return False
```

**Impact**:
- ✅ ATP, NADH automatically marked as signals
- ✅ Enables thermodynamic analysis
- ✅ Enables energy layer detection

#### 1.2 Automatic Signal Flow Arc Creation
**Location**: `src/shypn/importer/kegg/arc_builder.py`

**Current**: Creates regular Arc for all substrates/products  
**Enhanced**: Detect signal places and create SignalFlowArc

```python
def _create_input_arcs(self, place, transition, weight):
    """Create input arcs with signal flow detection."""
    # Check if source place is a signal
    if getattr(place, 'is_signal_place', False):
        # Create SignalFlowArc for information flow
        arc = SignalFlowArc(place, transition, arc_id, "", weight=weight)
        logger.info(f"Created signal flow arc: {place.name} → {transition.label}")
    else:
        # Regular arc for mass transfer
        arc = Arc(place, transition, arc_id, "", weight=weight)
    
    return arc
```

**Impact**:
- ✅ Automatic signal flow arc creation
- ✅ Correct light gray coloring
- ✅ Proper token consumption for signals

#### 1.3 Layer Inference During Import
**Location**: `src/shypn/importer/kegg/pathway_converter.py`

```python
def infer_signal_layers(document: DocumentModel) -> Dict[str, int]:
    """Infer signal place layers after import.
    
    Returns:
        Dict mapping place_id to layer number
    """
    # Get all signal places
    signal_places = [p for p in document.places if p.is_signal_place]
    
    # Layer assignment
    layers = {}
    
    # Layer 0: Energy signals (ATP, NADH)
    for place in signal_places:
        if place.signal_type == SignalType.ENERGY:
            layers[place.id] = 0
            place.metadata['hierarchy_layer'] = 0
    
    # Layer 1: Spatial signals (compartments)
    for place in signal_places:
        if place.signal_type == SignalType.SPATIAL:
            layers[place.id] = 1
            place.metadata['hierarchy_layer'] = 1
    
    # Layer 2: Quorum signals
    for place in signal_places:
        if place.signal_type == SignalType.QUORUM:
            layers[place.id] = 2
            place.metadata['hierarchy_layer'] = 2
    
    # Layer 3: Regulatory signals (transcription factors)
    for place in signal_places:
        if place.signal_type == SignalType.REGULATORY:
            layers[place.id] = 3
            place.metadata['hierarchy_layer'] = 3
    
    return layers
```

**Impact**:
- ✅ Automatic layer assignment
- ✅ Validates hierarchical structure
- ✅ Enables layer-specific analysis

### Phase 2: Enrichment Enhancements (MEDIUM PRIORITY)

#### 2.1 Layer-Aware Stoichiometry
**Location**: `src/shypn/services/enrichment/stoichiometry.py`

```python
def add_cofactors_with_hierarchy(self, document: DocumentModel):
    """Add cofactors and mark energy layer."""
    for transition in document.transitions:
        # Add ATP/NADH
        cofactors = self._detect_required_cofactors(transition)
        
        for cofactor in cofactors:
            place = self._get_or_create_place(cofactor)
            
            # Mark as energy signal
            place.is_signal_place = True
            place.signal_type = SignalType.ENERGY
            place.metadata['hierarchy_layer'] = 0
            
            # Create signal flow arc (not regular arc)
            arc = SignalFlowArc(place, transition, arc_id, "")
```

#### 2.2 Inhibitor Arc Detection from Rate Functions
**Location**: `src/shypn/services/enrichment/rate_inhibition_extractor.py`

```python
def detect_regulatory_signals(self, rate_function: str) -> List[str]:
    """Detect regulatory signals from inhibition patterns.
    
    Patterns:
    - 1/(1 + X/Ki) → X is inhibitory signal
    - (1 - X/Xmax) → X is suppressor signal
    - Ki/(Ki + X) → X is competitive inhibitor
    """
    inhibitors = []
    
    # Pattern 1: 1/(1 + X/Ki)
    matches = re.findall(r'1\s*/\s*\(1\s*\+\s*(\w+)\s*/\s*[\d.]+\)', rate_function)
    inhibitors.extend(matches)
    
    # Pattern 2: Ki/(Ki + X)
    matches = re.findall(r'[\w.]+\s*/\s*\([\w.]+\s*\+\s*(\w+)\)', rate_function)
    inhibitors.extend(matches)
    
    return inhibitors

def create_regulatory_arcs(self, inhibitors: List[str], transition: Transition):
    """Convert detected inhibitors to signal arcs."""
    for inhibitor_name in inhibitors:
        # Find or create signal place
        place = self._find_place_by_name(inhibitor_name)
        if not place:
            continue
        
        # Mark as regulatory signal
        place.is_signal_place = True
        place.signal_type = SignalType.REGULATORY
        
        # Create inhibitor arc (signal flow)
        arc = InhibitorArc(place, transition, arc_id, "", threshold=Ki)
```

### Phase 3: Signal vs Test Arc Classification (LOW PRIORITY)

#### 3.1 Decision Matrix

| Connection Type | Arc Type | Reasoning |
|----------------|----------|-----------|
| Signal Place → Transition | **SignalFlowArc** | Information flow with consumption |
| Enzyme Place → Reaction | **TestArc** | Catalytic, non-consuming |
| Metabolite → Transition | **Arc** | Mass transfer |
| Inhibitor → Transition | **InhibitorArc** | Negative regulation |

#### 3.2 Automatic Classification
**Location**: `src/shypn/core/controllers/document_controller.py`

```python
def infer_arc_type(self, source, target) -> str:
    """Infer correct arc type based on context."""
    # Check if source is signal place
    if isinstance(source, Place) and getattr(source, 'is_signal_place', False):
        # Signal place → transition = SignalFlowArc
        return 'signal_flow'
    
    # Check if source is enzyme/catalyst
    if isinstance(source, Place):
        metadata = getattr(source, 'metadata', {})
        if metadata.get('entry_type') in ['enzyme', 'gene', 'ortholog']:
            # Enzyme → reaction = TestArc
            return 'test'
    
    # Default: regular arc
    return 'normal'
```

## Implementation Priority

### Week 1 (Jan 2-8, 2026)
1. ✅ Enhanced cofactor detection in KEGG import
2. ✅ Automatic signal flow arc creation
3. ✅ Layer inference after import

### Week 2 (Jan 9-15, 2026)
4. ⏳ Enrichment layer-aware processing
5. ⏳ Rate function inhibitor extraction

### Week 3 (Jan 16-22, 2026)
6. ⏳ Signal vs test arc classification refinement
7. ⏳ Validation and testing

## Success Metrics

### Quantitative
- **Signal Detection Rate**: >95% of energy cofactors detected
- **Layer Assignment Accuracy**: 100% for energy, spatial, regulatory
- **Arc Type Accuracy**: >90% correct classification

### Qualitative
- ✅ KEGG models have complete signal hierarchy
- ✅ SignalHierarchyAnalyzer produces meaningful results
- ✅ Enrichment preserves hierarchical structure

## Testing Strategy

### Test Cases
1. **hsa00010** (Glycolysis): Verify ATP/NADH marked as energy signals
2. **hsa04010** (MAPK): Verify kinases marked as regulatory signals
3. **Lambda Phage**: Verify CI/Cro dimers correctly classified
4. **Enriched KEGG**: Verify added cofactors have correct layer

### Validation
```python
def validate_signal_hierarchy(document: DocumentModel):
    """Validate signal hierarchy structure."""
    analyzer = SignalHierarchyAnalyzer(document)
    result = analyzer.analyze()
    
    assert result.data['hierarchy']['is_hierarchical']
    assert result.data['hierarchy']['layer_count'] >= 2
    assert len(result.data['signal_places']) > 0
    assert len(result.data['signal_flow_arcs']) > 0
```

## Documentation Updates

1. **SIGNAL_HIERARCHY_THEORY.md**: Complete theory document
2. **KEGG_IMPORT.md**: Update with signal detection process
3. **ENRICHMENT.md**: Layer-aware enrichment documentation
4. **ARC_TYPE_GUIDE.md**: Decision matrix for arc type selection

## References

- `workspace/projects/Biochemical-Examples/22_Lambda_Phage_Switch/SIGNAL_HIERARCHY_REFACTORING.md`
- `src/shypn/topology/biological/signal_hierarchy.py`
- `src/shypn/analysis/signal_classification/`
- `doc/SIGNAL_CLASSIFICATION.md`
