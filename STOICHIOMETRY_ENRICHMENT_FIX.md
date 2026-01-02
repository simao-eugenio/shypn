# Stoichiometry Enrichment Fix: Artificial Source/Sink Pattern

**Date**: 2026-01-02  
**Branch**: Thermodynamic-Constraints-Gibbs-Free-Energy  
**Issue**: Artificial source/sink transitions created for stoichiometrically-connected energy signals

## Problem Description

When enriching KEGG models with stoichiometry, the system was creating **artificial source/sink transitions** for energy signal places (NAD, CoA, ATP, etc.) even when those places were already properly connected to biochemical reactions via SignalFlowArcs.

### Suspicious Pattern (BEFORE FIX)

In eco00020.shy after enrichment:

```
Real biochemical connection (CORRECT):
  NAD (P78) --SignalFlowArc--> R02569 (T17) --SignalFlowArc--> NADH (P81)
  CoA (P79) --SignalFlowArc(w=2)--> R02569 (T17)

Artificial plumbing (WRONG):
  NAD_source (T32) --SignalFlowArc--> NAD (P78) --SignalFlowArc--> NAD_sink (T33)
  CoA_source (T34) --SignalFlowArc--> CoA (P79) --SignalFlowArc--> CoA_sink (T35)
  NADH_source (T36) --SignalFlowArc--> NADH (P81) --SignalFlowArc--> NADH_sink (T37)
```

**Issue**: 20 artificial source/sink transitions (T22-T41) were created for 10 energy signals, even though those signals were already properly connected to real metabolic reactions!

### Root Cause

The enrichment process has three phases:

1. **Phase 1** (Stoichiometry Enrichment): Adds missing cofactors (NAD, CoA, etc.) and connects them to reactions with SignalFlowArcs ✅ **WORKING CORRECTLY**
   
2. **Phase 2** (Hill Inhibition): Extracts inhibition terms ✅ **WORKING CORRECTLY**
   
3. **Phase 3** (Signal Source/Sink Builder): Adds source/sink transitions for ALL signal places with SignalFlowArcs ❌ **TOO AGGRESSIVE**

The SignalSourceSinkBuilder was originally designed for **catalytic signal places** (connected via TestArcs) that act as read-only regulators. It unconditionally added source/sink for all signal places with SignalFlowArcs, not distinguishing between:

- **Catalytic signals**: Need source/sink (no stoichiometric balance)
- **Stoichiometric signals**: Already balanced by biochemical reactions

## Solution

Modified `SignalSourceSinkBuilder` to check if signal places are connected to **real biochemical reactions** before adding source/sink transitions.

### Code Changes

**File**: `src/shypn/services/enrichment/signal_source_sink_builder.py`

#### Change 1: Added connectivity check in `build_signal_network()`

```python
# NEW: Check if place is already connected to biochemical reactions
if self._is_connected_to_reactions(document, place):
    self.logger.debug(
        f"Skipping {place.label or place.name}: Already connected to biochemical reactions"
    )
    continue
```

#### Change 2: Added helper method `_is_connected_to_reactions()`

Checks if a signal place has SignalFlowArcs to/from transitions that:
- Have KEGG reaction IDs (metadata)
- Have EC numbers (enzyme classification)
- Are from KEGG import (source metadata)
- Are NOT marked as source/sink

```python
def _is_connected_to_reactions(self, document, place: Place) -> bool:
    """Check if signal place is connected to biochemical reactions."""
    from shypn.netobjs.signal_flow_arc import SignalFlowArc
    
    for arc in document.arcs:
        if not isinstance(arc, SignalFlowArc):
            continue
        
        if arc.source == place:
            target_transition = arc.target
            if isinstance(target_transition, Transition):
                if self._is_biochemical_reaction(target_transition):
                    return True
        
        elif arc.target == place:
            source_transition = arc.source
            if isinstance(source_transition, Transition):
                if self._is_biochemical_reaction(source_transition):
                    return True
    
    return False
```

#### Change 3: Added helper method `_is_biochemical_reaction()`

Distinguishes real reactions from artificial transitions:

```python
def _is_biochemical_reaction(self, transition: Transition) -> bool:
    """Check if transition represents a real biochemical reaction."""
    
    # Skip artificial source/sink transitions
    if getattr(transition, 'is_source', False) or getattr(transition, 'is_sink', False):
        return False
    
    # Check metadata for KEGG origin
    if hasattr(transition, 'metadata') and transition.metadata:
        metadata = transition.metadata
        
        # KEGG import markers
        if metadata.get('source') == 'KEGG':
            return True
        if metadata.get('data_source') == 'kegg_import':
            return True
        
        # KEGG reaction ID
        if 'kegg_reaction_id' in metadata or 'kegg_reaction_name' in metadata:
            return True
        
        # EC number (enzyme classification)
        if 'ec_numbers' in metadata and metadata['ec_numbers']:
            return True
    
    # Check label for KEGG reaction pattern (R00001, rn:R00001)
    if hasattr(transition, 'label') and transition.label:
        label = transition.label
        if 'R' in label and any(c.isdigit() for c in label):
            return True
    
    return False
```

## Expected Behavior (AFTER FIX)

When enriching a KEGG model:

1. **Energy cofactors properly connected to reactions**: NO source/sink created
   - Example: NAD → R02569 → NADH (already balanced by reaction stoichiometry)

2. **Energy cofactors NOT connected** (isolated): Source/sink created
   - Example: ATP added but no reactions use it → ATP_source → ATP → ATP_sink

3. **Catalytic enzyme places** (TestArcs only): Source/sink created if needed
   - Example: Enzyme regulation via TestArcs (non-consuming)

## Testing Instructions

### Manual Test (Recommended)

1. **Delete existing enriched model**:
   ```bash
   rm workspace/projects/My_Project/models/eco00020.shy
   ```

2. **Launch shypn GUI**:
   ```bash
   source .venv/bin/activate
   python src/shypn.py
   ```

3. **Import eco00020**:
   - File → Import → KEGG Pathway
   - Enter: `eco00020`
   - Wait for import

4. **Enrich stoichiometry**:
   - Tools → Enrich → Stoichiometry Enrichment
   - Wait for completion

5. **Verify no artificial source/sink**:
   - Open Node Inspector (click on NAD place)
   - Check connected transitions
   - Should see: R02569, R00361, etc. (real reactions)
   - Should NOT see: NAD_source, NAD_sink

6. **Check other energy signals**:
   - Repeat for: CoA, NADH, ATP, ADP, NADPH, NADP
   - All should connect to real reactions without source/sink

### Expected Results

**Before fix** (eco00020.shy had):
- 85 places
- 41 transitions (including 20 source/sink)
- 145 arcs

**After fix** (eco00020.shy should have):
- ~75 places (fewer if some cofactors unused)
- ~21 transitions (real reactions only, NO source/sink)
- ~125 arcs (fewer source/sink arcs)

### Verification Queries

```python
# Count source/sink transitions
source_sinks = [t for t in transitions if '_source' in t.label or '_sink' in t.label]
print(f"Source/sink transitions: {len(source_sinks)}")  # Should be 0 or very few

# Check NAD connections
nad = next(p for p in places if p.name == 'NAD')
for arc in arcs:
    if arc.source == nad or arc.target == nad:
        print(f"NAD connected to: {arc.target.label if arc.source == nad else arc.source.label}")
        # Should see: R02569, R00361, etc. (NOT NAD_source/sink)
```

## Benefits

1. **Cleaner topology**: No artificial transitions cluttering the network
2. **Correct semantics**: Energy signals balanced by stoichiometry, not artificial sources
3. **Better visualization**: Easier to understand metabolic flow
4. **Proper simulation**: No artificial token generation/consumption
5. **Thermodynamic integrity**: Signal places represent actual metabolite pools

## Compatibility

- ✅ Existing models enriched before fix: Still work (just have extra source/sink)
- ✅ New enrichments: Clean topology without artificial transitions
- ✅ TestArc catalysis: Still gets source/sink when needed
- ✅ Isolated signals: Still get source/sink (expected behavior)

## Related Files

- `src/shypn/services/enrichment/signal_source_sink_builder.py` (modified)
- `src/shypn/services/enrichment/stoichiometry.py` (uses builder)
- `dev/test_source_sink_fix.py` (test script - WIP)

## References

- Issue reported: 2026-01-02
- Analysis: eco00020.shy places P78-P85 (NAD, CoA, NADH region)
- Signal Hierarchy Theory: `doc/signal_hierarchy/SIGNAL_HIERARCHY_THEORY.md`
