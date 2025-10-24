# BRENDA Integration with Heuristic System

**Date:** 2025-10-24  
**Purpose:** Define how BRENDA enrichment integrates with SHYpn's existing heuristic kinetics system

## Overview

SHYpn already has a **sophisticated heuristic system** for inferring kinetic parameters and transition types when data is incomplete. BRENDA enrichment must integrate seamlessly with this existing infrastructure.

## Existing Heuristic System

### Current Architecture

```
src/shypn/heuristic/
├── kinetics_assigner.py      - Main assignment coordinator
├── assignment_result.py      - Result metadata (source, confidence)
├── factory.py                - Estimator factory
├── michaelis_menten.py       - Enzymatic kinetics
├── mass_action.py            - Simple reactions
├── stochastic.py             - Stochastic processes
└── metadata.py               - Track assignment sources
```

### Tiered Assignment Strategy

The system uses **4 tiers** of data priority:

```
Tier 1: EXPLICIT DATA (Highest Priority)
  - From SBML <kineticLaw> elements
  - Source: AssignmentSource.EXPLICIT
  - Confidence: ConfidenceLevel.HIGH
  - Action: Use exactly as provided, NEVER override

Tier 2: DATABASE LOOKUP
  - From enzyme databases (BRENDA in future)
  - Requires EC number
  - Source: AssignmentSource.DATABASE
  - Confidence: ConfidenceLevel.HIGH
  - Action: Use if no explicit data exists

Tier 3: HEURISTIC ANALYSIS
  - From reaction structure inference
  - Source: AssignmentSource.HEURISTIC
  - Confidence: ConfidenceLevel.MEDIUM or LOW
  - Action: Use if no database match

Tier 4: DEFAULT FALLBACK
  - Safe defaults (continuous, rate=1.0)
  - Source: AssignmentSource.DEFAULT
  - Confidence: ConfidenceLevel.LOW
  - Action: Last resort
```

### Transition Type Inference Rules

```python
# Rule 1: Has EC number → Enzymatic (Michaelis-Menten)
if reaction.ec_numbers:
    type = 'continuous'
    kinetics = 'michaelis_menten'
    confidence = MEDIUM

# Rule 2: Has enzyme annotation → Michaelis-Menten
if reaction.enzyme:
    type = 'continuous'
    kinetics = 'michaelis_menten'
    confidence = MEDIUM

# Rule 3: Simple stoichiometry (1:1) → Mass action
if simple_reaction:
    type = 'stochastic'
    kinetics = 'mass_action'
    confidence = LOW

# Rule 4: Multiple substrates → Complex kinetics
if len(substrates) > 1:
    type = 'continuous'
    kinetics = 'michaelis_menten'
    confidence = LOW

# Rule 5: Default → Continuous
else:
    type = 'continuous'
    rate = 1.0
    confidence = LOW
```

### Core Principle

> **"Import as-is for curated models, enhance only when data is missing"**

This is enforced by `KineticsMetadata.should_enhance(transition)`:
- Returns `False` if transition has `USER` or `EXPLICIT` source
- Returns `True` if transition has `HEURISTIC`, `DEFAULT`, or no source

## BRENDA Integration Strategy

### BRENDA as Tier 2 Enhancement

BRENDA should fit into **Tier 2 (Database Lookup)**:

```
CURRENT Tier 2:
  - EnzymeKineticsAPI (local cache + fallback DB)
  - 10 glycolysis enzymes only
  - Offline-capable

ENHANCED Tier 2 (with BRENDA):
  - EnzymeKineticsAPI → checks cache first
  - BRENDA SOAP API → comprehensive enzyme DB
  - Fallback DB → offline safety net
  - Returns: Km, kcat, Ki, enzyme names, citations
```

### Decision Flow with BRENDA

```
START: Transition needs kinetics
  ↓
Check: Has explicit data (SBML <kineticLaw>)?
  YES → Use explicit, mark as EXPLICIT, STOP ✓
  NO → Continue
  ↓
Check: Has EC number?
  NO → Skip to Tier 3 (Heuristic)
  YES → Continue to database lookup
  ↓
TIER 2A: Check local cache
  HIT → Use cached data, mark as DATABASE, STOP ✓
  MISS → Continue
  ↓
TIER 2B: Query BRENDA API (NEW)
  SUCCESS → Use BRENDA data, mark as DATABASE, STOP ✓
  FAIL → Continue
  ↓
TIER 2C: Check fallback database
  HIT → Use fallback, mark as DATABASE, STOP ✓
  MISS → Continue
  ↓
TIER 3: Heuristic analysis (existing)
  → Infer from reaction structure
  → Mark as HEURISTIC
  → STOP ✓
```

### Data Source Priority for Each Model Type

**KEGG Pathways** (Pure Topology):
```
Priority:
1. BRENDA API (EC numbers available)
2. Fallback DB (offline)
3. Heuristic (structure inference)
4. Default (continuous, rate=1.0)

Characteristics:
- No explicit kinetics to preserve
- EC numbers usually available
- Safe to enrich aggressively
- BRENDA provides ALL the missing data
```

**SBML Models** (Curated):
```
Priority:
1. EXPLICIT data (SBML <kineticLaw>) ← NEVER OVERRIDE
2. BRENDA API (only if no explicit data)
3. Heuristic (only if no BRENDA match)
4. Default (last resort)

Characteristics:
- May have curated kinetics
- Must preserve existing data
- BRENDA complements gaps only
- User must confirm overrides
```

## BRENDA Enrichment Workflow

### Phase 1: Canvas Analysis

```python
def analyze_canvas(model_canvas):
    """Scan canvas and categorize transitions."""
    transitions_to_enrich = []
    
    for transition in model_canvas.get_all_transitions():
        # Get current metadata
        metadata = KineticsMetadata.get_metadata(transition)
        source = metadata.get('source', AssignmentSource.DEFAULT)
        
        # Categorize
        if source == AssignmentSource.EXPLICIT:
            # Has explicit SBML kinetics - DO NOT TOUCH
            category = 'explicit_skip'
            action = 'preserve'
            
        elif source == AssignmentSource.USER:
            # User configured manually - DO NOT OVERRIDE
            category = 'user_configured'
            action = 'preserve'
            
        elif source == AssignmentSource.DATABASE:
            # Already enriched from database
            category = 'already_enriched'
            action = 'update' if user_wants_update else 'preserve'
            
        elif source in (AssignmentSource.HEURISTIC, AssignmentSource.DEFAULT):
            # Heuristic or default - SAFE TO ENRICH
            category = 'needs_enrichment'
            action = 'enrich'
            ec_numbers = transition.metadata.get('ec_numbers', [])
            
            if ec_numbers:
                priority = 'high'  # Has EC number, direct BRENDA match
            else:
                priority = 'low'   # No EC, try name matching
        
        transitions_to_enrich.append({
            'transition': transition,
            'category': category,
            'action': action,
            'priority': priority,
            'current_source': source
        })
    
    return transitions_to_enrich
```

### Phase 2: BRENDA Query

```python
def query_brenda_for_transitions(transitions_to_enrich, brenda_connector):
    """Query BRENDA for kinetic data."""
    enrichment_proposals = []
    
    for item in transitions_to_enrich:
        if item['action'] != 'enrich':
            continue  # Skip preserved transitions
        
        transition = item['transition']
        ec_numbers = transition.metadata.get('ec_numbers', [])
        
        # Query BRENDA
        brenda_data = None
        if ec_numbers:
            # Direct EC number lookup
            for ec in ec_numbers:
                brenda_data = brenda_connector.query_ec_number(
                    ec,
                    organism=user_organism_filter
                )
                if brenda_data:
                    break
        else:
            # Fallback: try name matching
            brenda_data = brenda_connector.query_by_name(
                transition.name,
                organism=user_organism_filter
            )
        
        if brenda_data:
            # Create enrichment proposal
            proposal = {
                'transition': transition,
                'current_data': get_current_kinetics(transition),
                'brenda_data': brenda_data,
                'would_change': compare_data(current_data, brenda_data),
                'confidence': 'high' if ec_numbers else 'medium'
            }
            enrichment_proposals.append(proposal)
    
    return enrichment_proposals
```

### Phase 3: Enrichment Report

```python
def generate_enrichment_report(enrichment_proposals):
    """Generate user-friendly report for review."""
    report = {
        'total_transitions': len(all_transitions),
        'explicit_preserved': count(category='explicit_skip'),
        'user_preserved': count(category='user_configured'),
        'already_enriched': count(category='already_enriched'),
        'proposed_enrichments': [],
        'no_match_found': []
    }
    
    for proposal in enrichment_proposals:
        transition = proposal['transition']
        brenda = proposal['brenda_data']
        
        report['proposed_enrichments'].append({
            'transition_name': transition.name,
            'ec_number': brenda['ec_number'],
            'enzyme_name': brenda['recommended_name'],
            'current_type': transition.transition_type,
            'proposed_type': infer_type_from_brenda(brenda),
            'parameters': {
                'Km': brenda['km_values'][0] if brenda['km_values'] else None,
                'kcat': brenda['kcat_values'][0] if brenda['kcat_values'] else None,
                'Ki': brenda['ki_values'][0] if brenda['ki_values'] else None,
            },
            'citations': brenda['citations'][:3],  # First 3 references
            'confidence': proposal['confidence'],
            'would_override': bool(proposal['would_change'])
        })
    
    return report
```

### Phase 4: User Review Dialog

```
┌──────────────────────────────────────────────────────────┐
│ BRENDA Enrichment Report                                 │
├──────────────────────────────────────────────────────────┤
│ Canvas Analysis:                                         │
│   Total transitions: 45                                  │
│   ✓ Preserved (explicit SBML): 12                       │
│   ✓ Preserved (user configured): 3                      │
│   ℹ Already enriched: 8                                  │
│   ⚠ Proposed enrichments: 15                             │
│   ✗ No BRENDA match: 7                                   │
├──────────────────────────────────────────────────────────┤
│ Proposed Enrichments (select to apply):                 │
│                                                          │
│ ☑ R01 - Hexokinase                                      │
│    EC: 2.7.1.1                                          │
│    Add: Km=0.15 mM, kcat=150 s⁻¹                       │
│    Type: continuous (Michaelis-Menten)                  │
│    Citations: [PubMed:12345678, ...]                    │
│    Confidence: HIGH                                      │
│                                                          │
│ ☑ R02 - Phosphofructokinase                            │
│    EC: 2.7.1.11                                         │
│    Add: Km=0.08 mM, kcat=300 s⁻¹, Ki=0.05 mM          │
│    Type: continuous (Michaelis-Menten)                  │
│    Citations: [PubMed:23456789, ...]                    │
│    Confidence: HIGH                                      │
│                                                          │
│ ... (13 more)                                           │
│                                                          │
│ [Select All] [Deselect All] [Details...]               │
├──────────────────────────────────────────────────────────┤
│ ⚠ Warning: 2 enrichments would override existing data   │
│   (Override option is DISABLED for safety)              │
│                                                          │
│           [Cancel]  [Apply Selected (15)]               │
└──────────────────────────────────────────────────────────┘
```

### Phase 5: Apply Enrichments

```python
def apply_enrichments(selected_proposals, model_canvas):
    """Apply selected BRENDA enrichments to canvas."""
    results = {
        'success': [],
        'failed': [],
        'skipped': []
    }
    
    for proposal in selected_proposals:
        transition = proposal['transition']
        brenda_data = proposal['brenda_data']
        
        # Double-check: should we really enhance this?
        if not KineticsMetadata.should_enhance(transition):
            results['skipped'].append({
                'transition': transition.name,
                'reason': 'Protected by metadata'
            })
            continue
        
        try:
            # Apply BRENDA data using KineticsAssigner
            result = apply_brenda_to_transition(
                transition,
                brenda_data,
                force_override=False  # Respect existing data
            )
            
            if result.success:
                # Mark as DATABASE source (higher priority than HEURISTIC)
                KineticsMetadata.set_source(
                    transition,
                    AssignmentSource.DATABASE
                )
                KineticsMetadata.set_confidence(
                    transition,
                    ConfidenceLevel.HIGH
                )
                
                # Store BRENDA metadata
                if not hasattr(transition, 'metadata'):
                    transition.metadata = {}
                
                transition.metadata.update({
                    'brenda_ec': brenda_data['ec_number'],
                    'brenda_enzyme': brenda_data['recommended_name'],
                    'brenda_organism': brenda_data['organism'],
                    'brenda_citations': brenda_data['citations'],
                    'enriched_date': datetime.now().isoformat()
                })
                
                results['success'].append({
                    'transition': transition.name,
                    'ec_number': brenda_data['ec_number']
                })
            else:
                results['failed'].append({
                    'transition': transition.name,
                    'error': result.message
                })
                
        except Exception as e:
            results['failed'].append({
                'transition': transition.name,
                'error': str(e)
            })
    
    # Update canvas
    model_canvas.refresh()
    
    return results
```

## Integration with Existing Code

### Modify KineticsAssigner

Add BRENDA as Tier 2B option:

```python
# In kinetics_assigner.py

def _assign_from_database(self, transition, reaction, substrate_places, product_places):
    """Tier 2: Database lookup (now includes BRENDA)."""
    
    # Get EC numbers
    ec_numbers = self._extract_ec_numbers(transition, reaction)
    if not ec_numbers:
        return AssignmentResult.failed("No EC number available")
    
    # Try each EC number
    for ec in ec_numbers:
        # 2A: Local cache
        cached = self.database.get_from_cache(ec)
        if cached:
            return self._apply_database_result(transition, cached, ec)
        
        # 2B: BRENDA API (NEW)
        if self.brenda_enabled and not self.offline_mode:
            brenda_data = self.brenda_connector.query_ec_number(ec)
            if brenda_data:
                return self._apply_brenda_result(transition, brenda_data, ec)
        
        # 2C: Fallback database
        fallback = self.database.get_from_fallback(ec)
        if fallback:
            return self._apply_database_result(transition, fallback, ec)
    
    # No database match found
    return AssignmentResult.failed("No database match for EC numbers")

def _apply_brenda_result(self, transition, brenda_data, ec_number):
    """Apply BRENDA data to transition."""
    
    # Determine transition type from BRENDA data
    if brenda_data['km_values'] or brenda_data['kcat_values']:
        # Has Michaelis-Menten parameters
        transition.transition_type = "continuous"
        
        # Build rate function
        km = brenda_data['km_values'][0]['value'] if brenda_data['km_values'] else 0.1
        kcat = brenda_data['kcat_values'][0]['value'] if brenda_data['kcat_values'] else 1.0
        
        rate_function = self._build_mm_rate_function(
            kcat, km, substrate_places
        )
        
        if not hasattr(transition, 'properties'):
            transition.properties = {}
        transition.properties['rate_function'] = rate_function
        
        parameters = {'Km': km, 'kcat': kcat}
        
    else:
        # No kinetic parameters, use default continuous
        transition.transition_type = "continuous"
        transition.rate = 1.0
        parameters = {'rate': 1.0}
        rate_function = "1.0"
    
    # Create result
    result = AssignmentResult.from_database(
        parameters=parameters,
        rate_function=rate_function,
        ec_number=ec_number
    )
    
    # Store BRENDA metadata
    result.metadata['enzyme_name'] = brenda_data['recommended_name']
    result.metadata['organism'] = brenda_data['organism']
    result.metadata['citations'] = brenda_data['citations'][:3]
    
    KineticsMetadata.set_from_result(transition, result)
    
    return result
```

### Add BRENDA Connector to PathwayConverter

```python
# In pathway_converter.py

class PathwayConverter:
    def __init__(self, brenda_connector=None):
        self.brenda_connector = brenda_connector
        
        # Initialize kinetics assigner with BRENDA
        if brenda_connector:
            self.kinetics_assigner = KineticsAssigner(
                brenda_enabled=True,
                brenda_connector=brenda_connector
            )
        else:
            self.kinetics_assigner = KineticsAssigner(
                brenda_enabled=False
            )
```

## Configuration Options

### User Preferences

```python
# In workspace settings or preferences

brenda_config = {
    'enabled': True,
    'offline_mode': False,
    'auto_enrich_kegg': True,       # Auto-enrich KEGG pathways on import
    'auto_enrich_sbml': False,       # Require confirmation for SBML
    'override_existing': False,      # Never override by default
    'organism_filter': None,         # None = all organisms
    'preferred_organisms': [         # Priority list for multi-organism results
        'Homo sapiens',
        'Mus musculus',
        'Rattus norvegicus'
    ],
    'include_citations': True,
    'min_confidence': 'medium',      # Skip low-confidence matches
    'cache_results': True,
    'cache_duration_days': 30
}
```

### Import Options

In pathway panel, options expander:

```xml
<GtkCheckButton id="brenda_auto_enrich">
  Auto-enrich with BRENDA on import
  (Recommended for KEGG, not for SBML)
</GtkCheckButton>

<GtkCheckButton id="brenda_review_first">
  Show enrichment report before applying
  (Recommended for SBML models)
</GtkCheckButton>
```

## Implementation Timeline

### Phase 1: Infrastructure (Week 1)
- [ ] Modify `KineticsAssigner` to support BRENDA
- [ ] Add `_apply_brenda_result()` method
- [ ] Create `BRENDAConnector` class
- [ ] Implement SOAP client wrapper

### Phase 2: Canvas Analysis (Week 2)
- [ ] Implement `analyze_canvas()` function
- [ ] Implement `query_brenda_for_transitions()`
- [ ] Create enrichment proposal data structure
- [ ] Add metadata tracking

### Phase 3: User Interface (Week 2-3)
- [ ] Create enrichment report dialog
- [ ] Add checkbox list for selecting enrichments
- [ ] Implement "Details" view for each proposal
- [ ] Add warning dialogs for overrides

### Phase 4: Application (Week 3)
- [ ] Implement `apply_enrichments()` function
- [ ] Add rollback capability
- [ ] Create success/failure reporting
- [ ] Test with KEGG pathways

### Phase 5: Testing (Week 4)
- [ ] Test with pure KEGG pathways
- [ ] Test with curated SBML models
- [ ] Test with mixed data (partial kinetics)
- [ ] Verify explicit data preservation
- [ ] Verify heuristic fallback

## Success Criteria

### Functional Requirements

1. **Data Preservation** ✓
   - Explicit SBML kinetics NEVER overridden
   - User-configured data NEVER overridden
   - Source metadata always tracked

2. **Intelligent Enrichment** ✓
   - KEGG pathways enriched by default
   - SBML models require confirmation
   - Heuristic fallback when BRENDA unavailable

3. **User Control** ✓
   - Review enrichments before applying
   - Select/deselect individual enrichments
   - See what would change

4. **Integration** ✓
   - Works with existing KineticsAssigner
   - Uses same metadata system
   - Fits into Tier 2 (Database Lookup)

### Quality Metrics

- **Preserve explicit data:** 100% (MUST)
- **Match KEGG EC numbers:** >90%
- **Useful SBML enrichment:** >70%
- **User satisfaction:** Positive feedback on review UI

---

**Status:** Design Complete, Ready for Implementation  
**Next Steps:** Begin Phase 1 (Infrastructure development)
