# Analyzer Quick Reference Guide

Quick guide for using the viability analyzers in code.

---

## Import Analyzers

```python
from shypn.ui.panels.viability.analysis.locality_analyzer import LocalityAnalyzer
from shypn.ui.panels.viability.analysis.dependency_analyzer import DependencyAnalyzer
from shypn.ui.panels.viability.analysis.boundary_analyzer import BoundaryAnalyzer
from shypn.ui.panels.viability.analysis.conservation_analyzer import ConservationAnalyzer
```

---

## Level 1: Locality Analysis

Analyze individual transition problems.

### Usage

```python
analyzer = LocalityAnalyzer()

# Prepare context
context = {
    'transition': transition_obj,      # Transition being analyzed
    'locality': locality_obj,          # Locality (inputs/outputs/arcs)
    'kb': knowledge_base,              # Knowledge base for compound/reaction info
    'sim_data': {                      # Optional: simulation results
        'firing_count': 42,
        'duration': 60.0,
        'rate': 0.7
    }
}

# Run analysis
issues = analyzer.analyze(context)

# Generate suggestions
suggestions = analyzer.generate_suggestions(issues, context)

# Display results
for issue in issues:
    print(f"{issue.severity}: {issue.message}")
    
for suggestion in suggestions:
    print(f"Suggestion: {suggestion.action}")
    print(f"Expected impact: {suggestion.impact}")
```

### Issue Categories

- **structural**: Missing arcs, source/sink, weight imbalance
- **biological**: Unmapped compounds, missing reaction mappings
- **kinetic**: Never fired, low rate, missing parameters

### Suggestion Types

- Balance arc weights
- Map compounds to KEGG
- Query BRENDA for rates
- Investigate transition enablement

---

## Level 2: Dependency Analysis

Analyze inter-locality flow dependencies.

### Usage

```python
analyzer = DependencyAnalyzer()

# Prepare context
context = {
    'dependencies': [dep1, dep2, dep3],  # List of Dependency objects
    'sim_data': {                         # Simulation data by transition/place
        'T1': {'rate': 10.0},
        'T2': {'rate': 2.0},
        'P1': {'tokens_over_time': [0, 10, 25, 45]}
    },
    'locality_issues': {                  # Optional: issues from Level 1
        'T1': [issue1, issue2]
    }
}

# Run analysis
issues = analyzer.analyze(context)
suggestions = analyzer.generate_suggestions(issues, context)
```

### Issue Types

- **flow**: Imbalanced production/consumption rates
- **bottleneck**: Slow transitions limiting subnet throughput
- **cascade**: Root cause problems affecting downstream

### Suggestion Types

- Adjust rates to balance flows
- Increase bottleneck rate
- Fix root cause to resolve cascades

---

## Level 3: Boundary Analysis

Analyze subnet boundary behavior.

### Usage

```python
analyzer = BoundaryAnalyzer()

# Prepare context
context = {
    'boundary_places': {
        'P1': {
            'type': 'input',              # 'input' or 'output'
            'initial_tokens': 100,
            'tokens_over_time': [100, 80, 60, 40]
        },
        'P2': {
            'type': 'output',
            'initial_tokens': 0,
            'tokens_over_time': [0, 10, 25, 45]
        }
    },
    'duration': 60.0                      # Simulation duration
}

# Run analysis
issues = analyzer.analyze(context)
suggestions = analyzer.generate_suggestions(issues, context)

# Create summary
summary = analyzer.create_boundary_analysis(context)
print(f"Inputs: {summary.inputs}")
print(f"Outputs: {summary.outputs}")
print(f"Net flow: {summary.net_flow}")
```

### Thresholds

- **Accumulation**: > 2x initial tokens (warning)
- **Depletion**: < 50% initial tokens (warning)
- **Critical Depletion**: < 10% initial tokens (error)

### Issue Types

- Accumulation at outputs
- Depletion at inputs
- Input/output imbalance

### Suggestion Types

- Add sink for accumulation
- Add source for depletion
- Balance subnet material flow

---

## Level 4: Conservation Analysis

Validate physical conservation laws.

### Usage

```python
analyzer = ConservationAnalyzer()

# Prepare context
context = {
    'p_invariants': [                     # P-invariant specifications
        {
            'places': ['P1', 'P2', 'P3'],
            'coefficients': [1, 1, 1],
            'expected_sum': 100,
            'tokens_over_time': {
                'P1': [30, 28, 25, 20],
                'P2': [40, 38, 35, 30],
                'P3': [30, 30, 30, 30]
            }
        }
    ],
    'reactions': [                        # Reaction specifications
        {
            'transition_id': 'T1',
            'reaction_id': 'R00001',
            'substrates': [
                {'compound_id': 'C00001', 'stoichiometry': 1, 'formula': 'H2O'}
            ],
            'products': [
                {'compound_id': 'C00002', 'stoichiometry': 1, 'formula': 'H2O'}
            ]
        }
    ],
    'places': {                           # Place token data
        'P1': {'compound_id': 'C00001', 'initial_tokens': 100, 'final_tokens': 80}
    },
    'duration': 60.0
}

# Run analysis
issues = analyzer.analyze(context)
suggestions = analyzer.generate_suggestions(issues, context)

# Create summary
summary = analyzer.create_conservation_analysis(context)
print(f"Violated invariants: {len(summary.invariants_violated)}")
print(f"Mass balance issues: {len(summary.mass_balance_issues)}")
```

### Issue Types

- **p_invariant**: Token conservation violated over time
- **mass_balance**: Stoichiometry doesn't conserve mass
- **leak**: Unexplained material appearance/disappearance

### Suggestion Types

- Add source/sink to preserve invariants
- Map reactions for validation
- Review stoichiometry and arc weights

---

## Common Patterns

### 1. Running All Analyzers

```python
def analyze_subnet(subnet, kb, sim_data):
    """Run all 4 levels of analysis."""
    all_issues = []
    all_suggestions = []
    
    # Level 1: Analyze each locality
    locality_analyzer = LocalityAnalyzer()
    for locality in subnet.localities:
        context = build_locality_context(locality, kb, sim_data)
        issues = locality_analyzer.analyze(context)
        suggestions = locality_analyzer.generate_suggestions(issues, context)
        all_issues.extend(issues)
        all_suggestions.extend(suggestions)
    
    # Level 2: Analyze dependencies
    dependency_analyzer = DependencyAnalyzer()
    context = build_dependency_context(subnet, sim_data)
    issues = dependency_analyzer.analyze(context)
    suggestions = dependency_analyzer.generate_suggestions(issues, context)
    all_issues.extend(issues)
    all_suggestions.extend(suggestions)
    
    # Level 3: Analyze boundaries
    boundary_analyzer = BoundaryAnalyzer()
    context = build_boundary_context(subnet, sim_data)
    issues = boundary_analyzer.analyze(context)
    suggestions = boundary_analyzer.generate_suggestions(issues, context)
    boundary_summary = boundary_analyzer.create_boundary_analysis(context)
    all_issues.extend(issues)
    all_suggestions.extend(suggestions)
    
    # Level 4: Analyze conservation
    conservation_analyzer = ConservationAnalyzer()
    context = build_conservation_context(subnet, kb, sim_data)
    issues = conservation_analyzer.analyze(context)
    suggestions = conservation_analyzer.generate_suggestions(issues, context)
    conservation_summary = conservation_analyzer.create_conservation_analysis(context)
    all_issues.extend(issues)
    all_suggestions.extend(suggestions)
    
    return {
        'issues': all_issues,
        'suggestions': all_suggestions,
        'boundary_summary': boundary_summary,
        'conservation_summary': conservation_summary
    }
```

### 2. Filtering Issues by Severity

```python
# Get only errors
errors = [issue for issue in issues if issue.severity == 'error']

# Get only warnings
warnings = [issue for issue in issues if issue.severity == 'warning']

# Sort by severity (error > warning > info)
severity_order = {'error': 0, 'warning': 1, 'info': 2}
sorted_issues = sorted(issues, key=lambda i: severity_order.get(i.severity, 3))
```

### 3. Grouping Suggestions by Category

```python
from collections import defaultdict

grouped = defaultdict(list)
for suggestion in suggestions:
    grouped[suggestion.category].append(suggestion)

# Display by category
for category, sug_list in grouped.items():
    print(f"\n{category.upper()} Fixes:")
    for sug in sug_list:
        print(f"  • {sug.action}")
```

### 4. Reusing Analyzers

```python
# Analyzers maintain state, so clear between uses
analyzer = LocalityAnalyzer()

for locality in localities:
    context = build_context(locality)
    issues = analyzer.analyze(context)
    # Process issues...
    analyzer.clear()  # Reset for next locality
```

---

## Context Building Helpers

Example helper functions for building contexts:

```python
def build_locality_context(locality, kb, sim_data):
    """Build context for locality analysis."""
    return {
        'transition': locality.transition,
        'locality': locality,
        'kb': kb,
        'sim_data': sim_data.get(locality.transition.id, {})
    }

def build_dependency_context(subnet, sim_data):
    """Build context for dependency analysis."""
    return {
        'dependencies': subnet.dependencies,
        'sim_data': sim_data,
        'locality_issues': {}  # Populated from Level 1
    }

def build_boundary_context(subnet, sim_data):
    """Build context for boundary analysis."""
    boundary_places = {}
    for place_id in subnet.boundary_places:
        boundary_places[place_id] = {
            'type': subnet.place_types[place_id],  # 'input' or 'output'
            'initial_tokens': sim_data['places'][place_id]['initial'],
            'tokens_over_time': sim_data['places'][place_id]['history']
        }
    return {
        'boundary_places': boundary_places,
        'duration': sim_data['duration']
    }

def build_conservation_context(subnet, kb, sim_data):
    """Build context for conservation analysis."""
    return {
        'p_invariants': extract_p_invariants(subnet, sim_data),
        'reactions': extract_reactions(subnet, kb),
        'places': extract_place_data(subnet, sim_data),
        'duration': sim_data['duration']
    }
```

---

## Error Handling

```python
def safe_analyze(analyzer, context):
    """Safely run analyzer with error handling."""
    try:
        issues = analyzer.analyze(context)
        suggestions = analyzer.generate_suggestions(issues, context)
        return issues, suggestions
    except KeyError as e:
        print(f"Missing required context key: {e}")
        return [], []
    except Exception as e:
        print(f"Analysis error: {e}")
        return [], []
```

---

## Display Helpers

```python
def format_issue(issue):
    """Format issue for display."""
    emoji = {'error': '🔴', 'warning': '🟡', 'info': '🟢'}
    return f"{emoji[issue.severity]} {issue.message}"

def format_suggestion(suggestion):
    """Format suggestion for display."""
    return f"💡 {suggestion.action}\n   → {suggestion.impact}"
```

---

## See Also

- **PHASE_3_COMPLETION.md** - Detailed architecture and design
- **VIABILITY_REFACTOR_PLAN.md** - Overall refactor plan
- **investigation.py** - Data class definitions (Issue, Suggestion)
- **subnet_builder.py** - Subnet extraction and validation
