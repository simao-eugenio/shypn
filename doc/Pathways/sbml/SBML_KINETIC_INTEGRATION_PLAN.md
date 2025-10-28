# SBML Kinetic Integration Plan

**Date**: October 28, 2025  
**Status**: Planning Phase  
**Related**: KEGG_KINETIC_ENRICHMENT_PLAN.md

## Executive Summary

SBML files contain **reliable kinetic data** (formulas, parameters, rate types) that should be treated as **primary source truth**, not "enrichment". This plan integrates SBML kinetics into the data model with full metadata tracking for project reports.

**Key Principle**: SBML kinetic laws are **source data**, not enrichment. They have highest confidence and should never be overwritten.

---

## Current State Analysis

### What SBML Already Provides ✅

From `src/shypn/data/pathway/sbml_parser.py`:

1. **Kinetic Laws** (per reaction):
   - `formula`: Mathematical expression (e.g., `"Vmax * S / (Km + S)"`)
   - `rate_type`: Auto-detected (`michaelis_menten`, `mass_action`, `custom`)
   - `parameters`: Dictionary (e.g., `{"Vmax": 10.0, "Km": 0.5}`)

2. **Species Data**:
   - Initial concentrations/amounts
   - Compartment volumes
   - Database IDs (ChEBI, KEGG)

3. **Global Parameters**:
   - Model-wide constants
   - Shared parameter values

4. **Metadata**:
   - Source file, model ID, SBML version
   - Model notes/description

### What's Missing ❌

1. **No transition-level metadata storage** for kinetic source tracking
2. **No confidence indicators** (SBML should be "definitive" confidence)
3. **No project report integration** for kinetic metadata
4. **No UI visibility** of kinetic source (SBML vs enriched vs manual)
5. **Advanced models not supported**: Hill equation, inhibition, threshold functions

---

## Conceptual Framework

### Data Source Hierarchy (by Confidence)

```
┌─────────────────────────────────────────────────┐
│ 1. SBML Explicit Kinetics    [DEFINITIVE]      │ ← Source data (never overwrite)
│    - From SBML file kinetic laws               │
│    - Confidence: 100%                           │
│    - Metadata: formula, parameters, SBML level │
├─────────────────────────────────────────────────┤
│ 2. Manual User Entry          [HIGH]           │ ← User-provided
│    - Entered via UI dialogs                     │
│    - Confidence: 95%                            │
│    - Metadata: user, timestamp, rationale       │
├─────────────────────────────────────────────────┤
│ 3. Database Lookup (EC)       [MEDIUM-HIGH]    │ ← Enrichment
│    - BRENDA, KEGG via EC number                │
│    - Confidence: 70-80%                         │
│    - Metadata: EC, database, species, organism  │
├─────────────────────────────────────────────────┤
│ 4. Heuristic Analysis         [MEDIUM]         │ ← Enrichment
│    - Structure-based inference                  │
│    - Confidence: 50-60%                         │
│    - Metadata: method, assumptions, locality    │
├─────────────────────────────────────────────────┤
│ 5. Default/Placeholder        [LOW]            │ ← Fallback
│    - Generic mass action                        │
│    - Confidence: 30%                            │
│    - Metadata: needs_review flag                │
└─────────────────────────────────────────────────┘
```

### Terminology Clarification

- **Source Data**: SBML kinetics, manual entry (trustworthy, don't overwrite)
- **Enrichment**: Database lookup, heuristics (augment missing data)
- **Integration**: Combining source data + enrichment + metadata

---

## Data Model Design

### 1. Transition Kinetic Metadata Schema

Extend `src/shypn/data/document/transition.py`:

```python
@dataclass
class TransitionKineticMetadata:
    """
    Tracks kinetic data source and confidence for transitions.
    
    Used for:
    - Preventing accidental overwrite of reliable data
    - Project report generation
    - UI confidence indicators
    - Audit trail
    """
    
    # Source tracking
    source: str  # "sbml", "manual", "database_lookup", "heuristic", "default"
    source_file: Optional[str] = None  # SBML filename or database name
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    # Confidence
    confidence: str = "low"  # "definitive", "high", "medium", "low"
    confidence_score: float = 0.3  # 0.0-1.0
    
    # Kinetic details
    rate_type: Optional[str] = None  # "michaelis_menten", "mass_action", "hill", "inhibition"
    formula: Optional[str] = None  # Mathematical expression
    parameters: Dict[str, float] = field(default_factory=dict)  # {"Vmax": 10.0, "Km": 0.5}
    
    # SBML-specific (if applicable)
    sbml_level: Optional[int] = None
    sbml_version: Optional[int] = None
    sbml_reaction_id: Optional[str] = None
    
    # Enrichment-specific (if applicable)
    ec_number: Optional[str] = None  # e.g., "2.7.1.1"
    organism: Optional[str] = None  # e.g., "Homo sapiens"
    database: Optional[str] = None  # "brenda", "kegg", "sabio-rk"
    
    # Manual entry (if applicable)
    entered_by: Optional[str] = None  # Username
    rationale: Optional[str] = None  # Why this kinetic was chosen
    
    # Quality flags
    needs_review: bool = False
    manually_edited: bool = False  # True if user modified after initial assignment
    locked: bool = False  # Prevent enrichment from overwriting
    
    # Locality analysis (for heuristics)
    locality_context: Optional[Dict[str, Any]] = None  # Neighborhood info
```

### 2. Project Metadata Schema

Extend `src/shypn/data/document/project_metadata.py`:

```python
@dataclass
class ProjectKineticReport:
    """
    Summary of kinetic data sources in project.
    
    Used for:
    - Project-level reports
    - Quality assessment
    - Completeness tracking
    """
    
    # Statistics
    total_transitions: int = 0
    
    # By source
    sbml_kinetics: int = 0  # From SBML files
    manual_kinetics: int = 0  # User-entered
    database_kinetics: int = 0  # From EC databases
    heuristic_kinetics: int = 0  # Inferred
    default_kinetics: int = 0  # Placeholders
    
    # By confidence
    definitive_confidence: int = 0  # SBML
    high_confidence: int = 0  # Manual, well-characterized enzymes
    medium_confidence: int = 0  # Database with caveats
    low_confidence: int = 0  # Heuristics, defaults
    
    # By kinetic model type
    mass_action: int = 0
    michaelis_menten: int = 0
    hill_equation: int = 0
    competitive_inhibition: int = 0
    custom_formulas: int = 0
    
    # Quality flags
    needs_review: int = 0  # Transitions flagged for review
    incomplete: int = 0  # Missing kinetic data
    
    # Detailed breakdown
    transition_details: Dict[str, TransitionKineticMetadata] = field(default_factory=dict)
    
    # Report generation
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def get_completeness_score(self) -> float:
        """Calculate % of transitions with reliable kinetics (SBML + manual)."""
        if self.total_transitions == 0:
            return 0.0
        reliable = self.sbml_kinetics + self.manual_kinetics
        return (reliable / self.total_transitions) * 100
    
    def get_average_confidence(self) -> float:
        """Calculate weighted average confidence score."""
        if not self.transition_details:
            return 0.0
        scores = [meta.confidence_score for meta in self.transition_details.values()]
        return sum(scores) / len(scores)
```

---

## Implementation Phases

### Phase 1: SBML Kinetic Integration (2 weeks)

**Goal**: Properly capture and preserve SBML kinetic data

#### Tasks:

1. **Extend Transition Model** (2 days)
   - Add `kinetic_metadata: TransitionKineticMetadata` field to `Transition` class
   - Add serialization/deserialization for metadata
   - Update `.shypn` file format (backward compatible)

2. **Update SBML Import Pipeline** (3 days)
   - Modify `sbml_parser.py` to preserve kinetic laws in `Reaction` objects
   - Update `DocumentConverter` to transfer kinetics to `Transition.kinetic_metadata`
   - Set confidence to "definitive" for SBML kinetics
   - Store SBML-specific metadata (level, version, reaction ID)

3. **Add Confidence Scoring** (2 days)
   - Implement `calculate_confidence_score()` function
   - SBML → 1.0 (definitive)
   - Manual → 0.95 (high)
   - Database → 0.7-0.8 (medium-high)
   - Heuristic → 0.5-0.6 (medium)
   - Default → 0.3 (low)

4. **Update Kinetics Assigner** (3 days)
   - Modify `KineticsAssigner.assign()` to check `transition.kinetic_metadata.source`
   - **NEVER overwrite SBML or manual kinetics** unless `locked=False`
   - Update to populate full metadata structure
   - Add `force=False` parameter for manual override

**Files to Modify**:
- `src/shypn/data/document/transition.py`
- `src/shypn/data/pathway/sbml_parser.py`
- `src/shypn/importer/sbml_converter.py`
- `src/shypn/heuristic/kinetics_assigner.py`

**Success Criteria**:
- SBML kinetics preserved with full metadata
- Confidence scores assigned correctly
- No accidental overwriting of source data

---

### Phase 2: Project Report Integration (1.5 weeks)

**Goal**: Generate kinetic metadata reports for projects

#### Tasks:

1. **Create Report Generator** (3 days)
   - New file: `src/shypn/analysis/kinetic_report_generator.py`
   - Scan all transitions in document
   - Aggregate statistics by source, confidence, type
   - Generate `ProjectKineticReport` object

2. **Add Report Export** (2 days)
   - Export to JSON (machine-readable)
   - Export to Markdown (human-readable report)
   - Export to HTML (with confidence visualizations)

3. **Integrate with Project Save** (2 days)
   - Auto-generate report on project save
   - Store in `.shypn` file metadata
   - Update on every edit that changes kinetics

**Files to Create**:
- `src/shypn/analysis/kinetic_report_generator.py`
- `src/shypn/analysis/report_exporters.py`

**Files to Modify**:
- `src/shypn/data/document/project_metadata.py`
- `src/shypn/helpers/file_operations.py` (save/load)

**Success Criteria**:
- Reports generated automatically
- Statistics accurate and complete
- Multiple export formats available

---

### Phase 3: UI Visualization (2 weeks)

**Goal**: Show kinetic source and confidence in UI

#### Tasks:

1. **Transition Property Dialog** (3 days)
   - Add "Kinetic Source" info panel
   - Show: source, confidence badge, timestamp
   - Display formula and parameters (read-only for SBML)
   - Add "Lock" checkbox to prevent enrichment

2. **Confidence Indicators** (2 days)
   - Color-coded badges:
     * 🟢 Green: Definitive (SBML)
     * 🔵 Blue: High (manual)
     * 🟡 Yellow: Medium (database)
     * 🟠 Orange: Low (heuristic)
     * 🔴 Red: Needs review (default/incomplete)
   - Show in transition dialog
   - Show in canvas tooltips

3. **Kinetic Report Viewer** (3 days)
   - New menu: `Tools → Kinetic Report...`
   - Display `ProjectKineticReport` statistics
   - Pie charts for source distribution
   - Bar charts for confidence levels
   - List transitions needing review

4. **Canvas Visual Cues** (2 days)
   - Small badge on transitions showing confidence
   - Color tint on transitions (optional setting)
   - Filter/highlight by source or confidence

**Files to Modify**:
- `ui/dialogs/transition_prop_dialog.ui`
- `src/shypn/helpers/transition_prop_dialog_loader.py`
- `src/shypn/canvas/transition_renderer.py`

**Files to Create**:
- `ui/dialogs/kinetic_report_dialog.ui`
- `src/shypn/helpers/kinetic_report_dialog.py`

**Success Criteria**:
- Users can see kinetic source at a glance
- Confidence badges clear and intuitive
- Report dialog provides actionable insights

---

### Phase 4: Advanced Kinetic Models (2 weeks)

**Goal**: Support Hill equation, inhibition, threshold models from SBML

#### Tasks:

1. **Extend Formula Parser** (3 days)
   - Detect Hill equation patterns: `Vmax * S^n / (Km^n + S^n)`
   - Detect competitive inhibition: `Vmax * S / (Km * (1 + I/Ki) + S)`
   - Detect non-competitive inhibition: `Vmax * S / ((Km + S) * (1 + I/Ki))`
   - Detect threshold functions: `if S > threshold then rate else 0`

2. **Update Rate Type Detection** (2 days)
   - Modify `ReactionExtractor._detect_rate_type()` in `sbml_parser.py`
   - Add detection for: `hill_equation`, `competitive_inhibition`, `noncompetitive_inhibition`, `threshold`
   - Extract Hill coefficient `n`, inhibitor constant `Ki`

3. **Parameter Extraction** (2 days)
   - Extract Hill coefficient, inhibitor constants
   - Handle multiple inhibitors
   - Detect allosteric modulation parameters

4. **UI Support** (3 days)
   - Update transition dialog to show advanced parameters
   - Add UI for Hill coefficient, inhibitor species
   - Display formula with proper mathematical notation

**Files to Modify**:
- `src/shypn/data/pathway/sbml_parser.py`
- `src/shypn/heuristic/kinetics_assigner.py`
- `ui/dialogs/transition_prop_dialog.ui`

**Success Criteria**:
- Advanced SBML kinetics correctly parsed
- Parameters extracted and stored
- UI displays advanced models clearly

---

### Phase 5: Enrichment Service Integration (2 weeks)

**Goal**: Unified enrichment that respects SBML source data

#### Tasks:

1. **Create Kinetic Integration Service** (4 days)
   - New file: `src/shypn/services/kinetic_integration_service.py`
   - Unified API for all kinetic sources
   - Respects source hierarchy (never overwrites SBML)
   - Supports selective enrichment

2. **User-Driven Enrichment Dialog** (4 days)
   - New dialog: `Tools → Enrich Kinetics...`
   - Show all transitions with current source
   - Allow user to select which to enrich
   - Preview enrichment results before applying
   - Batch operations support

3. **Integrate with KEGG Import** (2 days)
   - Use `KineticIntegrationService` instead of direct `KineticsAssigner`
   - Preserve existing SBML kinetics from crossfetch
   - Only enrich transitions without kinetics

**Files to Create**:
- `src/shypn/services/kinetic_integration_service.py`
- `ui/dialogs/enrich_kinetics_dialog.ui`
- `src/shypn/helpers/enrich_kinetics_dialog.py`

**Files to Modify**:
- `src/shypn/importer/kegg/pathway_converter.py`
- `src/shypn/crossfetch/sbml_enricher.py`

**Success Criteria**:
- Enrichment never overwrites reliable data
- User has full control over enrichment
- Preview before applying changes

---

## File Format Updates

### .shypn File Structure

Add `kinetic_metadata` to transition serialization:

```xml
<transition id="T1" type="stochastic">
    <name>Hexokinase</name>
    <rate>10.5</rate>
    <!-- NEW: Kinetic metadata -->
    <kinetic_metadata>
        <source>sbml</source>
        <source_file>glycolysis.sbml</source_file>
        <confidence>definitive</confidence>
        <confidence_score>1.0</confidence_score>
        <rate_type>michaelis_menten</rate_type>
        <formula>Vmax * Glucose / (Km + Glucose)</formula>
        <parameters>
            <parameter name="Vmax" value="10.0"/>
            <parameter name="Km" value="0.5"/>
        </parameters>
        <sbml_level>3</sbml_level>
        <sbml_version>2</sbml_version>
        <sbml_reaction_id>R_HK</sbml_reaction_id>
        <timestamp>2025-10-28T10:30:00</timestamp>
        <locked>true</locked>
    </kinetic_metadata>
</transition>
```

### Backward Compatibility

- Old `.shypn` files without metadata → Load successfully
- Default metadata created on load: `source="default", confidence="low"`
- User prompted to enrich on first open

---

## Testing Strategy

### Unit Tests

1. **SBML Parser Tests** (`tests/test_sbml_parser_kinetics.py`)
   - Test kinetic law extraction
   - Test rate type detection
   - Test parameter parsing
   - Test advanced model detection

2. **Metadata Tests** (`tests/test_kinetic_metadata.py`)
   - Test metadata creation
   - Test confidence scoring
   - Test serialization/deserialization
   - Test locking mechanism

3. **Report Generator Tests** (`tests/test_kinetic_report.py`)
   - Test statistics aggregation
   - Test completeness calculation
   - Test export formats

### Integration Tests

1. **SBML Import Integration** (`tests/test_sbml_import_kinetics.py`)
   - Import SBML with kinetics → Verify metadata preserved
   - Import SBML without kinetics → Verify enrichment possible
   - Import + enrich → Verify SBML not overwritten

2. **Round-trip Tests**
   - Save project with metadata → Load → Verify metadata intact
   - Edit kinetics manually → Save → Verify manual source recorded

### Acceptance Tests

1. **User Workflows**
   - Import BioModels SBML → Verify kinetics auto-integrated
   - Import KEGG pathway → Enrich selectively → Verify mixed sources
   - Generate report → Verify statistics accurate
   - Lock SBML kinetics → Attempt enrich → Verify protected

---

## Timeline Summary

| Phase | Duration | Focus |
|-------|----------|-------|
| Phase 1: SBML Integration | 2 weeks | Data model + import pipeline |
| Phase 2: Project Reports | 1.5 weeks | Report generation + export |
| Phase 3: UI Visualization | 2 weeks | Dialogs + badges + report viewer |
| Phase 4: Advanced Models | 2 weeks | Hill, inhibition, threshold |
| Phase 5: Enrichment Service | 2 weeks | Unified integration API |
| **Total** | **9.5 weeks** | **Complete integration** |

---

## Success Metrics

### Technical Metrics
- ✅ 100% SBML kinetics preserved on import
- ✅ No accidental overwriting of source data
- ✅ Metadata stored for all transitions
- ✅ Reports generated successfully

### User Experience Metrics
- ✅ Users can identify kinetic source at a glance
- ✅ Confidence badges intuitive and helpful
- ✅ Enrichment process clear and controllable
- ✅ Reports provide actionable insights

### Quality Metrics
- ✅ Average confidence score > 0.7 for enriched projects
- ✅ Completeness score > 80% for SBML imports
- ✅ < 10% transitions need manual review

---

## Migration Plan

### For Existing Projects

1. **On First Load** (post-update):
   - Scan all transitions
   - Create default metadata (`source="unknown", confidence="low"`)
   - Flag all for review
   - Prompt user: "Generate kinetic report for this project?"

2. **User Options**:
   - Accept current kinetics → Mark as `source="manual", confidence="high"`
   - Run enrichment → Apply database/heuristic assignment
   - Review individually → Mark reliable transitions as `locked=true`

3. **No Data Loss**:
   - Existing formulas and parameters preserved
   - Only metadata added (backward compatible)

---

## Future Enhancements

### Post-Release Features

1. **Machine Learning Confidence**
   - Train model on validated kinetics
   - Predict confidence based on reaction similarity
   - Active learning from user corrections

2. **Multi-Source Reconciliation**
   - Compare SBML vs KEGG vs BRENDA parameters
   - Highlight discrepancies
   - Suggest consensus values

3. **Temporal Tracking**
   - Version history for kinetic changes
   - Track database updates
   - Re-enrichment scheduling

4. **Collaborative Curation**
   - Share kinetic metadata across team
   - Peer review for low-confidence kinetics
   - Community parameter database

---

## Conclusion

This plan treats **SBML kinetics as source data** (not enrichment) with full metadata tracking. Key benefits:

1. **Reliability**: SBML kinetics never accidentally overwritten
2. **Transparency**: Users know where each kinetic came from
3. **Quality**: Confidence scores guide manual review
4. **Reporting**: Project-level statistics for publications
5. **Integration**: Unified system for all kinetic sources

Implementation is **9.5 weeks** of focused work, building on the existing 80% complete enrichment infrastructure.

**Next Step**: Review this plan and decide on Phase 1 implementation priority.
