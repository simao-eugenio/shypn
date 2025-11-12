# Viability Panel - Quick Reference

## For Users

### How to Investigate a Transition
1. Right-click on any transition in the model canvas
2. Select **"Add to Viability Analysis"** from context menu
3. Panel shows suggestions organized by analysis level

### Understanding Suggestions

#### Suggestion Levels
- **Locality Level**: Issues within the transition's immediate neighborhood
- **Dependency Level**: Issues between connected transitions
- **Boundary Level**: Missing sources/sinks at subnet borders
- **Conservation Level**: Stoichiometry and mass balance issues

#### Suggestion Categories
- **Structural**: Topology changes (add arcs, balance weights)
- **Kinetic**: Rate adjustments (increase/decrease/balance)
- **Biological**: Semantic mappings (KEGG compounds/reactions)
- **Flow**: Bottleneck fixes (rate balancing, flow optimization)
- **Boundary**: Sources/sinks (add input/output transitions)
- **Conservation**: Stoichiometry (fix mass imbalances)

### Applying Fixes

#### Apply Button
Immediately applies the fix to your model. Changes take effect instantly.

#### Preview Button
Shows what will change before applying:
- **Impact Level**: LOW → CRITICAL (number of affected elements)
- **Risk Level**: low/medium/high
- **Direct Changes**: Immediate modifications
- **Cascade Changes**: Downstream effects
- **Warnings**: High-impact or high-risk alerts

#### Undo Button
Reverts an applied fix, restoring the model to its previous state. Only available after applying.

### Best Practices
1. **Preview First**: Always check impact before applying
2. **Start with Structural**: Apply structural fixes before kinetic ones
3. **Undo if Needed**: Don't hesitate to revert and try different approach
4. **Investigate Connected**: Check neighboring transitions for related issues

## For Developers

### Architecture Overview
```
User Action → ViabilityPanel → DataPuller → SubnetBuilder → Analyzers → FixSystem → UI
```

### Main Entry Point
```python
# From canvas right-click menu
viability_panel.investigate_transition(transition_id)
```

### Key Components

#### 1. DataPuller (data/data_puller.py)
```python
from shypn.ui.panels.viability.data import DataPuller

puller = DataPuller(kb, simulation)
transition = puller.get_transition('T1')
input_arcs = puller.get_input_arcs('T1')
connected_places = puller.get_connected_places('T1')
```

#### 2. SubnetBuilder (investigation.py)
```python
from shypn.ui.panels.viability.investigation import SubnetBuilder

builder = SubnetBuilder()
subnet = builder.build_from_transition(
    transition_id='T1',
    data_puller=puller
)
# subnet.localities: List of Locality objects
# subnet.connectivity: Graph of connections
```

#### 3. Analyzers (analyzers/)
```python
from shypn.ui.panels.viability.analyzers import (
    LocalityAnalyzer, DependencyAnalyzer,
    BoundaryAnalyzer, ConservationAnalyzer
)

# Analyze single locality
locality_suggestions = LocalityAnalyzer().analyze(locality)

# Analyze entire subnet
dependency_suggestions = DependencyAnalyzer().analyze(subnet)
boundary_suggestions = BoundaryAnalyzer().analyze(subnet)
conservation_suggestions = ConservationAnalyzer().analyze(subnet)
```

#### 4. Fix Sequencer (fixes/fix_sequencer.py)
```python
from shypn.ui.panels.viability.fixes import FixSequencer

sequencer = FixSequencer()
fix_sequence = sequencer.sequence(all_suggestions)

# fix_sequence.batches: List of fix batches (can run in parallel)
# fix_sequence.dependencies: Dependency graph
# fix_sequence.conflicts: List of conflicting fixes
```

#### 5. Fix Applier (fixes/fix_applier.py)
```python
from shypn.ui.panels.viability.fixes import FixApplier

applier = FixApplier(kb)

# Apply fix
applied_fix = applier.apply(suggestion)

# Revert fix
applier.revert(applied_fix)

# Get history
history = applier.get_history()
```

#### 6. Fix Predictor (fixes/fix_predictor.py)
```python
from shypn.ui.panels.viability.fixes import FixPredictor

predictor = FixPredictor(kb)
prediction = predictor.predict(suggestion)

print(f"Impact: {prediction.impact_level}")  # LOW/MEDIUM/HIGH/CRITICAL
print(f"Risk: {prediction.risk_level}")      # low/medium/high
print(f"Direct changes: {len(prediction.direct_changes)}")
print(f"Cascade changes: {len(prediction.cascade_changes)}")
print(f"Warnings: {prediction.warnings}")
```

### Creating Custom Analyzers

```python
from shypn.ui.panels.viability.investigation import Suggestion

class MyCustomAnalyzer:
    """Custom analyzer template."""
    
    def analyze(self, subnet) -> list[Suggestion]:
        """Analyze subnet and return suggestions.
        
        Args:
            subnet: Subnet object with localities and connectivity
            
        Returns:
            List of Suggestion objects
        """
        suggestions = []
        
        for locality in subnet.localities:
            # Your analysis logic here
            if self._needs_fix(locality):
                suggestions.append(
                    Suggestion(
                        category='my_category',  # structural/kinetic/biological/etc.
                        action="Do something",
                        impact="Improves something",
                        target_element_id=locality.transition_id,
                        details={'custom': 'data'}
                    )
                )
        
        return suggestions
    
    def _needs_fix(self, locality):
        # Your detection logic
        return True
```

### Adding to Viability Panel
```python
# In viability_panel.py __init__
self.my_analyzer = MyCustomAnalyzer()

# In investigate_transition()
my_results = self.my_analyzer.analyze(subnet)
all_suggestions = (
    locality_results + 
    dependency_results + 
    boundary_results + 
    conservation_results +
    my_results  # Add your results
)
```

### Testing Your Analyzer

```python
import pytest
from shypn.ui.panels.viability.investigation import Subnet, Locality, Suggestion

def test_my_analyzer():
    # Create mock locality
    locality = Locality(
        transition_id='T1',
        input_places=['P1'],
        output_places=['P2'],
        input_arcs=['A1'],
        output_arcs=['A2']
    )
    
    # Create mock subnet
    subnet = Subnet(
        root_transition_id='T1',
        localities=[locality],
        connectivity={}
    )
    
    # Run analyzer
    analyzer = MyCustomAnalyzer()
    suggestions = analyzer.analyze(subnet)
    
    # Assert expectations
    assert len(suggestions) > 0
    assert suggestions[0].category == 'my_category'
    assert suggestions[0].action == "Do something"
```

### Common Patterns

#### Pull Data On-Demand
```python
# Good: Pull only what you need
transition = puller.get_transition(transition_id)
if transition:
    rate = puller.get_transition_rate(transition_id)

# Bad: Don't cache or store for later
# (Use DataCache for this)
```

#### Check Connectivity
```python
# Use subnet.connectivity to check reachability
downstream = subnet.connectivity.get(transition_id, set())
for connected_id in downstream:
    # Process connected transition
    pass
```

#### Create Actionable Suggestions
```python
# Good: Specific action with details
Suggestion(
    category='kinetic',
    action="Increase rate by 50%",
    impact="Speeds up bottleneck transition",
    target_element_id='T1',
    details={'multiplier': 1.5}
)

# Bad: Vague action
Suggestion(
    category='kinetic',
    action="Fix this",
    impact="Makes it better",
    target_element_id='T1'
)
```

#### Handle Errors Gracefully
```python
try:
    subnet = builder.build_from_transition(transition_id, puller)
except ValueError as e:
    # Handle disconnected or invalid subnet
    print(f"Cannot build subnet: {e}")
    return []
```

### UI Integration

#### Show Investigation View
```python
# Automatic in viability_panel.py
# Multi-level subnet → SubnetView
# Single locality → InvestigationView
```

#### Custom Callbacks
```python
def on_apply_custom(suggestion):
    """Custom apply handler."""
    print(f"Applying: {suggestion.action}")
    # Your custom logic
    
view = SubnetView(
    investigation=investigation,
    on_apply=on_apply_custom,
    on_preview=self._on_preview_fix,
    on_revert=self._on_revert_fix
)
```

### Performance Tips

#### Use Caching
```python
from shypn.ui.panels.viability.data import CachedDataPuller, DataCache

cache = DataCache(default_ttl=60.0)  # 60 second TTL
cached_puller = CachedDataPuller(puller, cache)

# Repeated calls use cache
t1 = cached_puller.get_transition('T1')  # Cache miss
t1 = cached_puller.get_transition('T1')  # Cache hit

# Check cache stats
stats = cached_puller.get_cache_stats()
print(f"Hit rate: {stats['hit_rate']:.2%}")
```

#### Invalidate After Changes
```python
# After modifying model
cached_puller.invalidate_model_changes()

# After running simulation
cached_puller.invalidate_simulation_state()
```

#### Limit Subnet Depth
```python
builder = SubnetBuilder(max_depth=5)  # Limit to 5 levels
subnet = builder.build_from_transition(transition_id, puller)
```

### Debugging

#### Enable Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Analyzers will log their decisions
analyzer = LocalityAnalyzer()
suggestions = analyzer.analyze(locality)
```

#### Inspect Fix Sequence
```python
fix_sequence = sequencer.sequence(suggestions)

# Get explanation
explanation = sequencer.explain_sequence(fix_sequence)
print(explanation)

# Check conflicts
if fix_sequence.conflicts:
    print(f"Conflicts detected: {fix_sequence.conflicts}")
```

#### Preview All Changes
```python
for suggestion in all_suggestions:
    prediction = predictor.predict(suggestion)
    print(f"\n{suggestion.action}")
    print(f"  Impact: {prediction.impact_level}")
    print(f"  Changes: {len(prediction.get_all_changes())}")
    if prediction.has_warnings():
        print(f"  ⚠ Warnings: {prediction.warnings}")
```

## Common Issues

### "No investigation active"
**Cause:** Panel hasn't been triggered yet  
**Solution:** Right-click transition and select "Investigate Viability"

### "Failed to build subnet"
**Cause:** Transition has no connections or is isolated  
**Solution:** Check that transition has at least one input or output arc

### "Cannot apply fix"
**Cause:** Model is locked or KB is unavailable  
**Solution:** Ensure model is editable and KB is loaded

### High impact warning
**Cause:** Fix affects many elements (>10)  
**Solution:** Review cascade effects in preview dialog before applying

### Conflicting fixes detected
**Cause:** Two suggestions try to modify same element in opposite ways  
**Solution:** Apply one, then re-investigate to get updated suggestions

## Resources

### Documentation
- `/doc/VIABILITY_REFACTOR_COMPLETE.md` - Complete implementation details
- `/doc/PHASE_*_COMPLETION.md` - Phase-by-phase documentation

### Source Code
- `/src/shypn/ui/panels/viability/viability_panel.py` - Main orchestrator
- `/src/shypn/ui/panels/viability/data/` - Data layer
- `/src/shypn/ui/panels/viability/investigation.py` - Subnet builder
- `/src/shypn/ui/panels/viability/analyzers/` - Analysis components
- `/src/shypn/ui/panels/viability/fixes/` - Fix system
- `/src/shypn/ui/panels/viability/widgets/` - UI components

### Tests
- `/tests/viability/test_subnet_builder.py` - Subnet tests
- `/tests/viability/test_*_analyzer.py` - Analyzer tests
- `/tests/viability/test_fix_*.py` - Fix system tests
- `/tests/viability/test_*_view.py` - UI tests

---

**Last Updated:** November 12, 2025  
**Version:** 1.0.0
