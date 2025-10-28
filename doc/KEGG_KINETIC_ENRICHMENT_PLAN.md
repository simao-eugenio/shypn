# Kinetic Model Enrichment System

**Date**: October 27, 2025  
**Status**: Planning Phase  
**Scope**: User-driven kinetic enrichment for all Petri net models (KEGG, SBML, manual, or any source)  
**Goal**: Allow users to enrich any model with kinetic functions based on locality analysis, biological knowledge, and experimental data, with enrichment metadata tracked at the project level

## Overview

Provide a comprehensive kinetic enrichment system that allows users to enhance **any Petri net model** (KEGG-imported, SBML-imported, manually drawn, or from any source) with biologically meaningful kinetic functions. The system:

- **User-Driven**: Users explicitly choose which models to enrich and what enrichment strategies to apply
- **Source-Agnostic**: Works with models from any source (KEGG, SBML, manual drawing, file imports)
- **Project-Level Metadata**: Enrichment configuration and history tracked at the project level
- **Flexible**: Multiple enrichment strategies available (automatic, semi-automatic, manual templates)
- **Reversible**: Users can clear enrichments and re-apply with different strategies

### Key Capabilities
- Locality analysis (input/output places, stoichiometry) for any model
- Kinetic data integration from multiple sources (KEGG, SBML, BRENDA, literature)
- Established biological kinetic models (Michaelis-Menten, mass action, Hill, exponential)
- Mathematical formulations (NumPy/SymPy)
- Project metadata tracking of enrichment decisions
- Batch enrichment with user review

## Current State (Baseline)

### Existing Capabilities
**Model Sources**:
- ✅ KEGG pathway import with topology extraction
- ✅ SBML model import with structure parsing
- ✅ Manual drawing with immediate/timed/stochastic transitions
- ✅ File import (.shy format)

**Current State**:
- ✅ Topology extraction (places, transitions, arcs, stoichiometry)
- ✅ Transition type assignment (immediate, timed, stochastic, continuous)
- ❌ No kinetic function pre-filling or enrichment
- ❌ No parameter estimation or suggestion
- ❌ Manual kinetic configuration required for all models
- ❌ No project-level enrichment metadata tracking

### Available Information Sources

1. **KEGG-Imported Models**:
   - Enzyme Commission (EC) numbers
   - Reaction equations with stoichiometry
   - Substrate and product identities
   - Reaction reversibility
   - KEGG compound IDs

2. **SBML-Imported Models**:
   - Rate laws (if present)
   - Kinetic parameters (if present)
   - Compartment information
   - Unit definitions
   - Annotation data

3. **Manually Created Models**:
   - User-defined topology
   - User-assigned transition types
   - Stoichiometry from arc weights

4. **External Databases** (enrichment sources):
   - KEGG ENZYME (EC-specific kinetics)
   - KEGG REACTION (reaction kinetics)
   - BRENDA (comprehensive enzyme data)
   - SABIO-RK (kinetic data repository)
   - Literature-curated databases

## Proposed Enhancement Architecture

### User-Driven Enrichment Workflow

**Core Principle**: Users explicitly choose when and how to enrich their models.

```
User opens any model (KEGG/SBML/Manual/File) →
    ↓
[Tools Menu] → "Enrich Model Kinetics..." →
    ↓
Enrichment Wizard Dialog opens:
    1. Select transitions to enrich (all/selected/by type)
    2. Choose enrichment strategy (automatic/semi-automatic/templates)
    3. Configure data sources (KEGG/BRENDA/SABIO-RK/manual)
    4. Preview proposed enrichments
    5. Accept/Reject/Modify individual enrichments
    6. Apply enrichments
    ↓
Enrichment metadata saved to project
```

**Key Features**:
- Works with any model source (not just KEGG)
- User has full control over enrichment process
- Can enrich entire model or selected transitions
- Can re-enrich with different strategies
- Can clear enrichments and start over
- All decisions tracked in project metadata

### Project-Level Enrichment Metadata

**New Project Structure**:
```json
{
  "project_name": "My Glycolysis Study",
  "models": [...],
  "enrichment_metadata": {
    "enrichment_history": [
      {
        "timestamp": "2025-10-27T14:30:00Z",
        "model_id": "glycolysis_kegg.shy",
        "strategy": "automatic_with_kegg",
        "transitions_enriched": ["T1", "T2", "T5", "T8"],
        "data_sources": ["KEGG_ENZYME", "BRENDA"],
        "user": "researcher@lab.edu",
        "notes": "Initial enrichment using KEGG EC numbers"
      },
      {
        "timestamp": "2025-10-28T09:15:00Z",
        "model_id": "glycolysis_kegg.shy",
        "strategy": "manual_refinement",
        "transitions_modified": ["T2", "T5"],
        "user": "researcher@lab.edu",
        "notes": "Updated Km values based on our experimental data"
      }
    ],
    "enrichment_config": {
      "preferred_strategy": "automatic_with_kegg",
      "preferred_sources": ["KEGG_ENZYME", "BRENDA"],
      "parameter_units": "SI",
      "confidence_threshold": "medium"
    },
    "custom_parameters": {
      "hexokinase_km": {
        "value": 0.15,
        "unit": "mM",
        "source": "lab_experiment_2025_10_15",
        "notes": "Measured in our lab with glucose"
      }
    }
  }
}
```

**Metadata Benefits**:
- Reproducibility: Know exactly how model was enriched
- Provenance: Track data sources and decisions
- Collaboration: Share enrichment strategies across team
- Version control: Keep history of enrichment changes
- Validation: Audit trail for publications

### Phase 1: Locality-Based Kinetic Inference

**Goal**: Use network topology to infer appropriate kinetic models for **any model source**

#### 1.1 Locality Analysis Engine
```python
class LocalityKineticAnalyzer:
    """Analyzes transition locality to determine kinetic model."""
    
    def analyze_transition(self, transition):
        """
        Returns:
            {
                'input_places': [P1, P2, ...],
                'output_places': [P3, P4, ...],
                'input_stoichiometry': {P1: 2, P2: 1, ...},
                'output_stoichiometry': {P3: 1, P4: 1, ...},
                'suggested_model': 'michaelis_menten' | 'mass_action' | 'hill' | 'exponential',
                'parameters': {...}
            }
        """
```

**Inference Rules**:
- **Single substrate → Single product**: Michaelis-Menten
- **Multiple substrates → Multiple products**: Mass action or Hill kinetics
- **Stochastic transitions**: Exponential distribution (Gillespie algorithm)
- **Inhibition present**: Competitive/Non-competitive inhibition models

#### 1.2 Stoichiometry-Aware Function Generation
```python
class StoichiometryFunction:
    """Generates rate functions respecting stoichiometry."""
    
    def generate_mass_action(self, inputs, stoich):
        """
        Example: 2A + B → C
        Rate = k * [A]^2 * [B]
        """
        
    def generate_michaelis_menten(self, substrate, enzyme, km, vmax):
        """
        Rate = (Vmax * [S]) / (Km + [S])
        """
```

### Phase 2: Multi-Source Kinetic Data Integration

**Goal**: Fetch and use kinetic parameters from multiple sources based on model origin and user preferences

#### 2.1 Multi-Source Kinetic Data Fetcher
```python
class KineticDataFetcher:
    """Fetches kinetic parameters from multiple sources."""
    
    def fetch_for_model_source(self, model_source, transition_data):
        """
        Fetches kinetic data based on model origin.
        
        Args:
            model_source: 'kegg' | 'sbml' | 'manual' | 'file'
            transition_data: Transition metadata (EC number, reaction ID, etc.)
            
        Returns:
            KineticData object with parameters and confidence
        """
        if model_source == 'kegg':
            return self.fetch_kegg_data(transition_data)
        elif model_source == 'sbml':
            return self.extract_sbml_kinetics(transition_data)
        elif model_source == 'manual':
            return self.suggest_from_locality(transition_data)
        else:
            return self.fetch_general_database(transition_data)
    
    def fetch_kegg_data(self, transition_data):
        """Fetch from KEGG ENZYME/REACTION databases using EC numbers."""
        
    def extract_sbml_kinetics(self, transition_data):
        """Extract existing kinetics from SBML rate laws."""
        
    def fetch_brenda_data(self, ec_number):
        """Fetch from BRENDA database (comprehensive enzyme data)."""
        
    def fetch_sabiork_data(self, reaction_id):
        """Fetch from SABIO-RK kinetic data repository."""
        
    def suggest_from_locality(self, transition_data):
        """Suggest parameters based on locality and literature defaults."""
```

**Data Sources by Model Origin**:

| Model Source | Primary Data Source | Secondary Sources | Fallback |
|--------------|-------------------|-------------------|----------|
| **KEGG Import** | KEGG ENZYME (EC) | BRENDA, SABIO-RK | Literature defaults |
| **SBML Import** | SBML rate laws | KEGG, BRENDA | Locality-based |
| **Manual Model** | User annotation | BRENDA, SABIO-RK | Template library |
| **File Import** | Embedded metadata | All databases | Locality-based |

#### 2.2 Parameter Estimation Fallbacks
When experimental data unavailable:
- **Literature-based defaults** (curated database)
- **Similarity-based estimation** (from similar EC numbers)
- **Order-of-magnitude estimates** (biologically plausible ranges)

### Phase 3: Kinetic Model Templates

**Goal**: Implement common biological kinetic models as pre-filled templates

#### 3.1 Template Library

##### Michaelis-Menten (Enzymatic Reactions)
```python
def michaelis_menten_rate(substrate_tokens, km, vmax):
    """
    Classic Michaelis-Menten kinetics.
    
    Formula: v = (Vmax * [S]) / (Km + [S])
    
    Args:
        substrate_tokens: Current substrate place marking
        km: Michaelis constant (affinity parameter)
        vmax: Maximum reaction velocity
    
    Returns:
        Reaction rate (tokens/time)
    """
    import numpy as np
    S = substrate_tokens
    return (vmax * S) / (km + S)
```

##### Mass Action Kinetics
```python
def mass_action_rate(input_tokens, stoichiometry, k):
    """
    Mass action law for elementary reactions.
    
    Formula: v = k * ∏([Xi]^ni)
    
    Args:
        input_tokens: Dict of {place_id: marking}
        stoichiometry: Dict of {place_id: coefficient}
        k: Rate constant
    
    Returns:
        Reaction rate
    """
    import numpy as np
    rate = k
    for place_id, coeff in stoichiometry.items():
        rate *= np.power(input_tokens[place_id], coeff)
    return rate
```

##### Hill Equation (Cooperative Binding)
```python
def hill_equation_rate(substrate_tokens, km, vmax, n):
    """
    Hill equation for cooperative binding.
    
    Formula: v = (Vmax * [S]^n) / (Km^n + [S]^n)
    
    Args:
        substrate_tokens: Current substrate marking
        km: Half-saturation constant
        vmax: Maximum velocity
        n: Hill coefficient (cooperativity)
    
    Returns:
        Reaction rate
    """
    import numpy as np
    S = substrate_tokens
    return (vmax * np.power(S, n)) / (np.power(km, n) + np.power(S, n))
```

##### Competitive Inhibition
```python
def competitive_inhibition_rate(substrate_tokens, inhibitor_tokens, km, vmax, ki):
    """
    Michaelis-Menten with competitive inhibition.
    
    Formula: v = (Vmax * [S]) / (Km * (1 + [I]/Ki) + [S])
    
    Args:
        substrate_tokens: Substrate place marking
        inhibitor_tokens: Inhibitor place marking
        km: Michaelis constant
        vmax: Maximum velocity
        ki: Inhibition constant
    
    Returns:
        Reaction rate
    """
    import numpy as np
    S = substrate_tokens
    I = inhibitor_tokens
    return (vmax * S) / (km * (1 + I/ki) + S)
```

##### Exponential Distribution (Stochastic)
```python
def stochastic_exponential_rate(propensity):
    """
    Gillespie algorithm exponential distribution.
    
    Formula: τ ~ Exp(a0), where a0 is total propensity
    
    Args:
        propensity: Reaction propensity (mass action * stochastic rate)
    
    Returns:
        Time to next firing (exponentially distributed)
    """
    import numpy as np
    return np.random.exponential(1.0 / propensity)
```

##### Threshold Functions
```python
def threshold_activation(input_tokens, threshold, max_rate):
    """
    Threshold-based activation (all-or-nothing).
    
    Formula: v = max_rate if [S] >= threshold else 0
    
    Args:
        input_tokens: Current input marking
        threshold: Activation threshold
        max_rate: Maximum rate above threshold
    
    Returns:
        Reaction rate
    """
    return max_rate if input_tokens >= threshold else 0.0
```

#### 3.2 Transition Type to Model Mapping

| Transition Type | Default Kinetic Model | Alternative Models |
|----------------|----------------------|-------------------|
| **Immediate** | Mass action | Threshold |
| **Timed** | Michaelis-Menten | Mass action, Hill |
| **Stochastic** | Exponential (Gillespie) | Mass action (discrete) |
| **Continuous** | Michaelis-Menten | Mass action, ODE |

### Phase 4: User-Driven Enrichment System

**Goal**: Provide user interface for selecting, reviewing, and applying enrichments to any model

#### 4.1 Enrichment Workflow
```
User Action: Tools → Enrich Model Kinetics
    ↓
Step 1: Selection Dialog
    - Select scope: [All transitions] [Selected only] [By type]
    - Model source detected: KEGG/SBML/Manual/File
    - Number of transitions: 24 found, 24 selected
    ↓
Step 2: Strategy Configuration
    - Enrichment strategy:
      ○ Automatic (use best available data)
      ○ Semi-automatic (require user confirmation)
      ● Template-based (choose from library)
    - Data sources priority:
      ☑ KEGG ENZYME (if available)
      ☑ BRENDA
      ☑ SABIO-RK
      ☑ Literature defaults
    - Model preferences:
      ○ Prefer Michaelis-Menten
      ○ Prefer mass action
      ● Auto-select by transition type
    ↓
Step 3: Analysis & Proposal
    - System analyzes each transition:
      * Locality (inputs/outputs)
      * Stoichiometry
      * Available data sources
      * Suggested kinetic model
    - Generates enrichment proposals
    ↓
Step 4: Review Interface
    - Table showing all transitions:
      | ID | Label | Current | Proposed Model | Confidence | Actions |
      |----|-------|---------|----------------|------------|---------|
      | T1 | HK    | None    | Michaelis-M.   | High ⭐⭐⭐   | ✓ ✗ ✏️ |
      | T2 | PFK   | None    | Mass action    | Medium ⭐⭐  | ✓ ✗ ✏️ |
    - User can:
      * Accept all / Accept selected
      * Reject individual proposals
      * Edit parameters before accepting
      * Change kinetic model type
    ↓
Step 5: Application
    - Apply accepted enrichments
    - Save enrichment metadata to project
    - Update model file with kinetic functions
    - Show summary report
    ↓
Step 6: Project Metadata Updated
    - Record enrichment history
    - Track data sources used
    - Store user decisions
    - Preserve for reproducibility
```

#### 4.2 Enrichment Dialog Components

**Main Enrichment Wizard** (`ui/dialogs/kinetic_enrichment_wizard.ui`):
```xml
<GtkDialog>
  <GtkNotebook> <!-- Multi-page wizard -->
    
    <!-- Page 1: Selection -->
    <GtkBox orientation="vertical">
      <GtkLabel>Select transitions to enrich</GtkLabel>
      <GtkRadioButton>All transitions</GtkRadioButton>
      <GtkRadioButton>Selected transitions only</GtkRadioButton>
      <GtkRadioButton>By transition type...</GtkRadioButton>
      <GtkLabel>Model source: KEGG Import (EC numbers available)</GtkLabel>
      <GtkLabel>Transitions found: 24</GtkLabel>
    </GtkBox>
    
    <!-- Page 2: Strategy -->
    <GtkBox orientation="vertical">
      <GtkLabel>Choose enrichment strategy</GtkLabel>
      <GtkComboBoxText>
        <item>Automatic (best available data)</item>
        <item>Semi-automatic (require confirmation)</item>
        <item>Template-based (library)</item>
        <item>Manual (user-defined)</item>
      </GtkComboBoxText>
      
      <GtkExpander label="Data Sources">
        <GtkCheckButton>KEGG ENZYME</GtkCheckButton>
        <GtkCheckButton>BRENDA</GtkCheckButton>
        <GtkCheckButton>SABIO-RK</GtkCheckButton>
        <GtkCheckButton>Literature defaults</GtkCheckButton>
      </GtkExpander>
      
      <GtkExpander label="Model Preferences">
        <GtkCheckButton>Prefer Michaelis-Menten for enzymatic</GtkCheckButton>
        <GtkCheckButton>Use mass action for multi-substrate</GtkCheckButton>
        <GtkCheckButton>Apply Hill equation for cooperativity</GtkCheckButton>
      </GtkExpander>
    </GtkBox>
    
    <!-- Page 3: Analysis (progress) -->
    <GtkBox orientation="vertical">
      <GtkLabel>Analyzing transitions...</GtkLabel>
      <GtkProgressBar/>
      <GtkLabel>Fetching kinetic data from KEGG ENZYME...</GtkLabel>
      <GtkTextView> <!-- Log output -->
        T1 (Hexokinase): Found EC 2.7.1.1 → Fetching parameters...
        T1: Km = 0.1 mM (KEGG), Vmax = estimated
        T2 (PFK): Found EC 2.7.1.11 → Fetching parameters...
        ...
      </GtkTextView>
    </GtkBox>
    
    <!-- Page 4: Review -->
    <GtkBox orientation="vertical">
      <GtkLabel>Review proposed enrichments</GtkLabel>
      <GtkTreeView> <!-- Enrichment proposals table -->
        <columns>
          <Accept:checkbox> <ID> <Label> <Current> <Proposed> <Confidence> <Actions>
        </columns>
      </GtkTreeView>
      
      <!-- Preview panel -->
      <GtkExpander label="Preview: T1 - Hexokinase">
        <GtkBox orientation="vertical">
          <GtkLabel>Kinetic Model: Michaelis-Menten</GtkLabel>
          <GtkLabel>Formula: v = (Vmax * [S]) / (Km + [S])</GtkLabel>
          <GtkGrid> <!-- Parameters -->
            <Label>Vmax:</Label> <GtkEntry>0.5</GtkEntry> <Label>mM/s</Label>
            <Label>Km:</Label>   <GtkEntry>0.1</GtkEntry> <Label>mM</Label>
          </GtkGrid>
          <GtkExpander label="Python Code">
            <GtkTextView>
              def rate_function(tokens):
                  import numpy as np
                  S = tokens['P_glucose']
                  Vmax = 0.5
                  Km = 0.1
                  return (Vmax * S) / (Km + S)
            </GtkTextView>
          </GtkExpander>
          <GtkLabel>Data Source: KEGG ENZYME (EC 2.7.1.1)</GtkLabel>
          <GtkLabel>Confidence: High ⭐⭐⭐</GtkLabel>
        </GtkBox>
      </GtkExpander>
      
      <GtkButtonBox>
        <GtkButton>Accept All</GtkButton>
        <GtkButton>Accept Selected</GtkButton>
        <GtkButton>Edit Selected</GtkButton>
      </GtkButtonBox>
    </GtkBox>
    
    <!-- Page 5: Summary -->
    <GtkBox orientation="vertical">
      <GtkLabel>Enrichment Complete!</GtkLabel>
      <GtkLabel>✓ 20 transitions enriched successfully</GtkLabel>
      <GtkLabel>✗ 4 transitions skipped (insufficient data)</GtkLabel>
      
      <GtkExpander label="Details">
        <GtkTextView>
          Applied Michaelis-Menten: 15 transitions
          Applied Mass Action: 3 transitions
          Applied Hill Equation: 2 transitions
          
          Data sources used:
          - KEGG ENZYME: 18 parameters
          - BRENDA: 5 parameters
          - Literature defaults: 7 parameters
          
          Enrichment metadata saved to project.
        </GtkTextView>
      </GtkExpander>
      
      <GtkCheckButton>Save enrichment configuration for future use</GtkCheckButton>
    </GtkBox>
    
  </GtkNotebook>
  
  <action-buttons>
    <GtkButton>Cancel</GtkButton>
    <GtkButton>Back</GtkButton>
    <GtkButton>Next</GtkButton>
    <GtkButton>Apply</GtkButton>
  </action-buttons>
</GtkDialog>
```

#### 4.3 Enrichment Engine with Project Metadata
```python
class KineticEnrichmentEngine:
    """Orchestrates user-driven kinetic enrichment for any model."""
    
    def enrich_model(self, model, user_config, project):
        """
        Main enrichment workflow with project metadata tracking.
        
        Args:
            model: The Petri net model to enrich (any source)
            user_config: User's enrichment preferences from wizard
            project: Project object for metadata storage
            
        Steps:
        1. Analyze selected transitions (locality, stoichiometry)
        2. Determine model source and available data
        3. Fetch kinetic data from user-selected sources
        4. Propose enrichments (model + parameters)
        5. Present to user for review
        6. Apply accepted enrichments
        7. Save metadata to project
        8. Update model file
        """
        
        # Detect model source
        model_source = self._detect_model_source(model)
        
        # Get transitions to enrich (based on user selection)
        transitions = self._get_selected_transitions(model, user_config)
        
        # Analyze each transition
        enrichment_proposals = []
        for transition in transitions:
            # Step 1: Locality analysis
            locality = self.analyze_locality(transition)
            
            # Step 2: Fetch kinetic data (multi-source)
            kinetic_data = self.fetch_kinetic_data(
                transition=transition,
                model_source=model_source,
                data_sources=user_config['data_sources']
            )
            
            # Step 3: Select kinetic model
            model_type = self.select_kinetic_model(
                transition_type=transition.transition_type,
                locality=locality,
                kinetic_data=kinetic_data,
                user_preferences=user_config['model_preferences']
            )
            
            # Step 4: Estimate parameters
            parameters = self.estimate_parameters(
                model_type=model_type,
                kinetic_data=kinetic_data,
                locality=locality
            )
            
            # Step 5: Generate function
            function_code = self.generate_function_code(
                model_type=model_type,
                parameters=parameters,
                locality=locality
            )
            
            # Create proposal
            proposal = EnrichmentProposal(
                transition=transition,
                model_type=model_type,
                parameters=parameters,
                function_code=function_code,
                confidence=kinetic_data.get('confidence', 'estimated'),
                data_source=kinetic_data.get('source', 'auto-generated')
            )
            enrichment_proposals.append(proposal)
        
        # Step 6: User review (via UI)
        accepted_proposals = self._user_review_interface(enrichment_proposals)
        
        # Step 7: Apply enrichments
        for proposal in accepted_proposals:
            self._apply_enrichment(proposal.transition, proposal)
        
        # Step 8: Save project metadata
        enrichment_record = {
            'timestamp': datetime.now().isoformat(),
            'model_id': model.id,
            'model_source': model_source,
            'strategy': user_config['strategy'],
            'transitions_enriched': [p.transition.id for p in accepted_proposals],
            'data_sources': user_config['data_sources'],
            'user': os.getenv('USER'),
            'notes': user_config.get('notes', '')
        }
        project.add_enrichment_record(enrichment_record)
        project.save()
        
        return {
            'enriched': len(accepted_proposals),
            'skipped': len(enrichment_proposals) - len(accepted_proposals),
            'metadata': enrichment_record
        }
```

### Phase 5: User Interface & Project Integration

**Goal**: Seamless integration with existing UI and project management system

#### 5.1 Main Menu Integration

**New Menu Items**:
```
Tools
  ├── Enrich Model Kinetics...     (Ctrl+K)
  ├── Clear All Enrichments
  ├── Re-enrich Selected
  ├── Export Enrichment Report
  └── Enrichment Settings...
```

#### 5.2 Enhanced Transition Property Dialog

**New Tab**: "Kinetics" (appears when transition has enrichment)
- **Kinetic Model Display**: Current model type and formula
- **Parameter Editor**: Edit enriched parameters
- **Confidence Indicator**: Visual badge (⭐⭐⭐ experimental, ⭐⭐ estimated, ⭐ template)
- **Data Source**: Show where parameters came from
- **Re-enrich Button**: Trigger re-enrichment for this transition
- **Clear Enrichment Button**: Remove kinetic function
- **History**: Show enrichment history for this transition

#### 5.3 Project Panel Enhancement

**New Section**: "Kinetic Enrichment"
- **Status**: Shows enrichment coverage (e.g., "18/24 transitions enriched")
- **Last Enriched**: Timestamp of last enrichment
- **Strategy Used**: Display enrichment strategy
- **Data Sources**: List of databases used
- **Quick Actions**:
  - Enrich Model
  - View Enrichment Report
  - Export Parameters

#### 5.4 Enrichment Report Panel

**New Panel**: "Enrichment Report" (dockable, similar to Analyses panel)
- **Summary Statistics**:
  - Total transitions: 24
  - Enriched: 20 (83%)
  - High confidence: 15 (⭐⭐⭐)
  - Medium confidence: 3 (⭐⭐)
  - Low confidence: 2 (⭐)
  - Unenriched: 4
  
- **Enrichment Breakdown**:
  - By model type: 15 Michaelis-Menten, 3 Mass Action, 2 Hill
  - By data source: 18 KEGG, 5 BRENDA, 2 Literature
  
- **Actions**:
  - Export to CSV/JSON
  - Generate publication table
  - View full history

#### 5.5 Batch Operations Toolbar

**New Toolbar** (context-sensitive when transitions selected):
```
[Enrich Selected] [Clear Selected] [Edit Parameters] [Export Report]
```

### Phase 6: Validation & Testing

#### 6.1 Validation Approaches

1. **Biological Plausibility**:
   - Parameter ranges within biological bounds
   - Rate constants reasonable for enzyme kinetics
   - Steady-state analysis

2. **Literature Comparison**:
   - Compare generated models with published pathway models
   - Validate against experimental time-series data

3. **Simulation Testing**:
   - Run simulations with pre-filled kinetics
   - Check for numerical stability
   - Verify conservation laws

#### 6.2 Test Cases
- **Test Pathway 1**: Glycolysis (well-studied, rich kinetic data)
- **Test Pathway 2**: MAPK cascade (signaling, cooperative binding)
- **Test Pathway 3**: Simple metabolic pathway (basic Michaelis-Menten)

## Implementation Roadmap

### Milestone 1: Foundation & Core Components (3-4 weeks)
- [ ] Implement LocalityKineticAnalyzer (any model source)
- [ ] Create kinetic model template library (6+ model types)
- [ ] Develop parameter estimation fallback system
- [ ] Implement EnrichmentMetadata and Project integration
- [ ] Unit tests for kinetic functions and metadata
- [ ] Design and implement enrichment data structures

### Milestone 2: Multi-Source Data Integration (3-4 weeks)
- [ ] Implement KineticDataFetcher (KEGG, BRENDA, SABIO-RK)
- [ ] SBML rate law extraction
- [ ] Parse KEGG ENZYME and REACTION databases
- [ ] Handle API rate limiting and caching
- [ ] Implement model source detection
- [ ] Integration tests with real data from all sources

### Milestone 3: User-Driven Enrichment Engine (2-3 weeks)
- [ ] Implement KineticEnrichmentEngine with user workflow
- [ ] Model selection heuristics
- [ ] Enrichment proposal generation
- [ ] Project metadata recording
- [ ] Enrichment history tracking
- [ ] End-to-end tests for all model sources

### Milestone 4: UI Integration (3-4 weeks)
- [ ] Create Enrichment Wizard dialog (5-page wizard)
- [ ] Enhance transition property dialog (kinetics tab)
- [ ] Create Enrichment Report panel (dockable)
- [ ] Add Tools menu items
- [ ] Implement batch operations toolbar
- [ ] Add project panel enrichment section
- [ ] User acceptance testing

### Milestone 5: Validation & Documentation (2-3 weeks)
- [ ] Test with KEGG-imported pathways (glycolysis, MAPK)
- [ ] Test with SBML models (BioModels)
- [ ] Test with manually created models
- [ ] Compare with literature models
- [ ] Performance benchmarking
- [ ] Write user documentation
- [ ] Create tutorial videos
- [ ] Prepare example enriched projects

### Milestone 6: Advanced Features (Optional, 2-3 weeks)
- [ ] Parameter sensitivity analysis tool
- [ ] Export enrichment reports (CSV, LaTeX, JSON)
- [ ] Import/export enrichment configurations
- [ ] Batch re-enrichment across multiple models
- [ ] Custom data source plugins
- [ ] Machine learning parameter estimation (future)

**Total Estimated Time**: 13-18 weeks (3.5-4.5 months)

## Technical Requirements

### Dependencies
```python
# New dependencies to add to requirements.txt
numpy>=1.21.0          # Numerical computations
sympy>=1.10           # Symbolic mathematics
requests>=2.26.0      # KEGG API calls
beautifulsoup4>=4.10  # HTML parsing (if needed)
lxml>=4.6.3           # XML parsing (KEGG data)
```

### Data Storage

**Enhanced Project Structure**:
```python
class Project:
    # Existing fields...
    
    # New enrichment fields
    enrichment_metadata: EnrichmentMetadata = None
    
class EnrichmentMetadata:
    """Tracks all enrichment activities for a project."""
    
    enrichment_history: List[EnrichmentRecord] = []
    enrichment_config: EnrichmentConfig = None
    custom_parameters: Dict[str, CustomParameter] = {}
    
class EnrichmentRecord:
    """Single enrichment event."""
    timestamp: str
    model_id: str
    model_source: str  # 'kegg', 'sbml', 'manual', 'file'
    strategy: str  # 'automatic', 'semi-automatic', 'template', 'manual'
    transitions_enriched: List[str]
    transitions_modified: List[str] = []  # For refinements
    data_sources: List[str]
    user: str
    notes: str = ""
    
class EnrichmentConfig:
    """User's enrichment preferences."""
    preferred_strategy: str = "automatic"
    preferred_sources: List[str] = ["KEGG_ENZYME", "BRENDA"]
    parameter_units: str = "SI"
    confidence_threshold: str = "medium"
    auto_apply: bool = False  # Apply without review
    
class CustomParameter:
    """User-defined parameter overrides."""
    value: float
    unit: str
    source: str  # e.g., "lab_experiment", "publication_doi"
    notes: str = ""
    timestamp: str
```

**New Fields in Transition Model**:
```python
class Transition:
    # Existing fields...
    
    # New kinetic enrichment fields
    rate_function: str = None  # Python code as string
    kinetic_model: str = None  # 'michaelis_menten', 'mass_action', 'hill', etc.
    kinetic_parameters: Dict[str, float] = None  # {param_name: value}
    kinetic_metadata: KineticMetadata = None
    enrichment_status: str = None  # 'enriched', 'unenriched', 'user_modified'
    
class KineticMetadata:
    """Metadata about transition kinetics."""
    confidence: str  # 'experimental', 'estimated', 'template', 'manual'
    data_source: str  # 'KEGG:E:2.7.1.1', 'BRENDA', 'user_defined'
    ec_number: str = None
    timestamp: str
    enriched_by: str  # username
    formula_latex: str = None  # For display/publication
    references: List[str] = []  # DOIs, URLs, etc.
```

### File Format Extensions

**Enhanced .shy format** (backward compatible):
```json
{
  "version": "2.0",
  "model_source": "kegg_import",
  "places": [...],
  "transitions": [
    {
      "id": "T1",
      "label": "Hexokinase",
      "type": "timed",
      "kinetic": {
        "model": "michaelis_menten",
        "function": "lambda tokens: (0.5 * tokens['P_glucose']) / (0.1 + tokens['P_glucose'])",
        "parameters": {
          "Vmax": {"value": 0.5, "unit": "mM/s"},
          "Km": {"value": 0.1, "unit": "mM"}
        },
        "metadata": {
          "confidence": "experimental",
          "data_source": "KEGG:E:2.7.1.1",
          "ec_number": "2.7.1.1",
          "timestamp": "2025-10-27T12:00:00Z",
          "enriched_by": "researcher@lab.edu",
          "formula_latex": "v = \\frac{V_{max}[S]}{K_m + [S]}",
          "references": ["doi:10.1234/enzyme.kinetics"]
        },
        "enrichment_status": "enriched"
      }
    }
  ],
  "arcs": [...],
  "enrichment_metadata": {
    "last_enrichment": "2025-10-27T12:00:00Z",
    "enrichment_strategy": "automatic_with_kegg",
    "coverage": {"total": 24, "enriched": 20, "percentage": 83.3}
  }
}
```

**Enhanced Project File** (.shypn-project):
```json
{
  "project_name": "Glycolysis Study",
  "version": "1.0",
  "models": ["glycolysis_kegg.shy", "glycolysis_refined.shy"],
  "enrichment_metadata": {
    "enrichment_history": [
      {
        "timestamp": "2025-10-27T14:30:00Z",
        "model_id": "glycolysis_kegg.shy",
        "model_source": "kegg_import",
        "strategy": "automatic_with_kegg",
        "transitions_enriched": ["T1", "T2", "T5", "T8"],
        "data_sources": ["KEGG_ENZYME", "BRENDA"],
        "user": "researcher@lab.edu",
        "notes": "Initial enrichment using KEGG EC numbers"
      },
      {
        "timestamp": "2025-10-28T09:15:00Z",
        "model_id": "glycolysis_kegg.shy",
        "model_source": "kegg_import",
        "strategy": "manual_refinement",
        "transitions_modified": ["T2", "T5"],
        "user": "researcher@lab.edu",
        "notes": "Updated Km values based on our experimental data"
      }
    ],
    "enrichment_config": {
      "preferred_strategy": "automatic_with_kegg",
      "preferred_sources": ["KEGG_ENZYME", "BRENDA", "SABIO-RK"],
      "parameter_units": "SI",
      "confidence_threshold": "medium",
      "auto_apply": false
    },
    "custom_parameters": {
      "hexokinase_km": {
        "value": 0.15,
        "unit": "mM",
        "source": "lab_experiment_2025_10_15",
        "notes": "Measured in our lab with glucose at 37°C, pH 7.4",
        "timestamp": "2025-10-15T16:30:00Z"
      }
    }
  }
}
```

## Benefits

### For Users
1. **Flexibility**: Enrich any model (KEGG, SBML, manual, file) with kinetics
2. **Control**: User decides when, how, and what to enrich
3. **Reduced Manual Work**: Automatic generation with user review/approval
4. **Scientific Accuracy**: Parameters based on experimental data when available
5. **Biological Realism**: Models respect stoichiometry and enzyme mechanisms
6. **Transparency**: Clear indication of data sources and confidence levels
7. **Project Management**: Enrichment history tracked for reproducibility
8. **Collaboration**: Share enrichment strategies across team via project metadata

### For Research
1. **Reproducibility**: Complete enrichment provenance in project metadata
2. **Comparability**: Standardized kinetic models across different studies
3. **Hypothesis Testing**: Easy parameter sensitivity analysis with tracked variations
4. **Publication Ready**: Models with documented parameter sources and confidence levels
5. **Data Integration**: Combine parameters from multiple sources (KEGG, BRENDA, experiments)
6. **Version Control**: Enrichment history enables tracking of model refinements

### For the Project
1. **Differentiation**: Unique user-driven enrichment not available in other Petri net tools
2. **Source Agnostic**: Works with any model, not just specific imports
3. **Systems Biology Focus**: Clear positioning in computational biology space
4. **Community Value**: Lower barrier to systems biology modeling
5. **Citation Potential**: Novel integration of multi-source kinetic data with Petri nets
6. **Extensibility**: Plugin architecture for additional data sources

## Challenges & Mitigations

### Challenge 1: Data Availability
**Issue**: Many reactions lack experimental kinetic parameters  
**Mitigation**: 
- Implement robust estimation fallbacks
- Use literature-curated default values
- Clearly indicate estimation confidence

### Challenge 2: Model Complexity
**Issue**: Some reactions require complex kinetic models  
**Mitigation**:
- Start with common models (Michaelis-Menten, mass action)
- Allow custom user-defined functions
- Provide model library that users can extend

### Challenge 3: Computational Cost
**Issue**: Fetching data for large pathways may be slow  
**Mitigation**:
- Implement local caching of KEGG data
- Background fetching with progress indicators
- Batch API requests when possible

### Challenge 4: Parameter Units
**Issue**: Kinetic parameters have different units across sources  
**Mitigation**:
- Standardize on SI units internally
- Implement unit conversion utilities
- Document unit assumptions clearly

## Future Extensions

### Extension 1: SBML Integration
Import kinetic parameters from SBML models that include rate laws

### Extension 2: Machine Learning Parameter Estimation
Train models to predict kinetic parameters from reaction structure

### Extension 3: Sensitivity Analysis Tools
Automatic parameter sensitivity and uncertainty quantification

### Extension 4: Time-Series Data Fitting
Fit kinetic parameters to experimental time-series data

### Extension 5: Multi-Compartment Kinetics
Handle compartment-specific parameters and transport kinetics

## References

### Kinetic Modeling
1. Cornish-Bowden, A. (2012). "Fundamentals of Enzyme Kinetics" (4th ed.)
2. Segel, I. H. (1993). "Enzyme Kinetics: Behavior and Analysis of Rapid Equilibrium and Steady-State Enzyme Systems"
3. Wilkinson, D. J. (2018). "Stochastic Modelling for Systems Biology" (3rd ed.)

### Databases
1. KEGG: https://www.kegg.jp/kegg/docs/relnote.html
2. BRENDA: https://www.brenda-enzymes.org/
3. SABIO-RK: http://sabiork.h-its.org/

### Methods
1. Gillespie, D. T. (1977). "Exact stochastic simulation of coupled chemical reactions"
2. Michaelis, L., & Menten, M. L. (1913). "Die Kinetik der Invertinwirkung"
3. Hill, A. V. (1910). "The possible effects of the aggregation of the molecules of haemoglobin"

## Related Documentation
- [KEGG Import Pipeline](KEGG_COMPLETE_IMPORT_FLOW.md)
- [Firing Policies](FIRING_POLICIES.md)
- [SBML Flow Analysis](SBML_COMPLETE_FLOW_ANALYSIS.md)
- [Pathway Enhancement Pipeline](PATHWAY_IMPORT_DESIGN_COMPLETE.md)

## Status Tracking

- [ ] **Phase 1**: Foundation - Not started
- [ ] **Phase 2**: KEGG Integration - Not started
- [ ] **Phase 3**: Pre-filling Engine - Not started
- [ ] **Phase 4**: UI Integration - Not started
- [ ] **Phase 5**: Validation - Not started

**Next Steps**:
1. Review plan with stakeholders
2. Create detailed Phase 1 implementation tickets
3. Set up development branch: `feature/kegg-kinetic-enrichment`
4. Begin LocalityKineticAnalyzer implementation
