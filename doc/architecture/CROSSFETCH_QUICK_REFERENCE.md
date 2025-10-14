# Cross-Fetch System - Quick Reference

**Purpose**: Multi-source pathway enrichment with quality-based selection

---

## TL;DR

The **Cross-Fetch System** automatically fills missing pathway data by querying multiple reliable databases (BioModels, KEGG, Reactome, etc.) and intelligently selecting the best information based on quality metrics.

**Example**:
```python
# Import incomplete SBML
pathway = import_sbml("model.xml")  # Missing coordinates, some concentrations

# Enrich automatically
enriched = EnrichmentPipeline().enrich_pathway(pathway)

# Result: Complete pathway with:
# - Coordinates from KEGG (quality=0.75)
# - Concentrations from BioModels (quality=0.95)
# - All sources logged and attributed
```

---

## Architecture Overview

```
┌──────────────┐
│ SBML Import  │  Primary source (incomplete)
└──────┬───────┘
       │
       ▼
┌──────────────────────────────────────┐
│   Identify Missing Information       │
│   • No coordinates? Query KEGG       │
│   • No concentrations? Query BioM    │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│   Fetch from Multiple Sources        │
│   (parallel queries)                 │
│   ┌─────────┬─────────┬──────────┐  │
│   │ BioMod  │  KEGG   │ Reactome │  │
│   │ ChEBI   │ UniProt │  Others  │  │
│   └─────────┴─────────┴──────────┘  │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│   Quality Scoring                    │
│   • Completeness                     │
│   • Source reliability               │
│   • Validation status                │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│   Conflict Resolution & Voting       │
│   • Weighted by quality              │
│   • Consensus algorithms             │
│   • Source priority                  │
└──────┬───────────────────────────────┘
       │
       ▼
┌──────────────────────────────────────┐
│   Enriched Pathway                   │
│   • Complete data                    │
│   • Source attribution               │
│   • Quality metrics                  │
└──────────────────────────────────────┘
```

---

## Package Structure

```
src/shypn/crossfetch/
├── core/
│   ├── enrichment_pipeline.py    # Main orchestrator
│   ├── quality_scorer.py         # Quality assessment
│   ├── data_aggregator.py        # Multi-source merger
│   └── conflict_resolver.py      # Voting & selection
├── fetchers/
│   ├── base_fetcher.py           # Abstract base
│   ├── biomodels_fetcher.py      # BioModels DB
│   ├── kegg_fetcher.py           # KEGG API
│   ├── reactome_fetcher.py       # Reactome API
│   ├── chebi_fetcher.py          # ChEBI compounds
│   └── uniprot_fetcher.py        # UniProt proteins
├── enrichers/
│   ├── concentration_enricher.py # Initial values
│   ├── coordinate_enricher.py    # Layout positions
│   ├── kinetic_enricher.py       # Rate parameters
│   └── annotation_enricher.py    # Metadata
└── policies/
    ├── quality_policy.py         # Quality rules
    └── voting_policy.py          # Selection rules
```

---

## Data Types to Enrich

| Type | Primary Source | Fallback | Quality Threshold |
|------|---------------|----------|-------------------|
| **Coordinates** | KEGG, Reactome | WikiPathways | 0.3 (low OK) |
| **Concentrations** | BioModels | SABIO-RK | 0.5 (medium) |
| **Kinetics** | BioModels | BRENDA | 0.6 (high) |
| **Structures** | ChEBI | KEGG | 0.5 (medium) |
| **Annotations** | UniProt | Multiple | 0.4 (medium-low) |

---

## Quality Scoring

```python
Quality Score = (
    0.25 × Completeness +           # % fields populated
    0.30 × Source Reliability +     # Database reputation
    0.20 × Consistency +            # Internal checks
    0.25 × Validation Status        # Experimental?
)

Source Reliability:
  BioModels:    1.00  (curated, peer-reviewed)
  Reactome:     0.95  (expert-curated)
  KEGG:         0.85  (comprehensive, auto-gen)
  WikiPathways: 0.80  (community-curated)
  Predicted:    0.30  (computational)
```

---

## Voting Strategies

### Quality Weighted (Default)
```python
# Select highest quality score
best = max(results, key=lambda r: r.quality_score)
```

### Source Priority
```python
# Prefer specific sources
priority = ['BioModels', 'Reactome', 'KEGG', 'Others']
```

### Consensus
```python
# Require 2+ sources to agree
# High confidence when multiple sources match
```

### Merge Complementary
```python
# Combine non-conflicting data
# Use best source for each field
```

---

## Usage Examples

### Basic Enrichment

```python
from shypn.crossfetch import EnrichmentPipeline

# Create pipeline
pipeline = EnrichmentPipeline()
pipeline.register_standard_fetchers()

# Enrich pathway
enriched = pipeline.enrich_pathway(sbml_pathway)

# Check results
print(enriched.get_enrichment_report())
```

### Custom Configuration

```python
# Custom priorities
pipeline = EnrichmentPipeline()
pipeline.register_fetcher(BioModelsFetcher(priority=10))
pipeline.register_fetcher(KEGGFetcher(priority=8))

# Custom quality thresholds
pipeline.set_quality_policy(QualityPolicy(
    min_completeness=0.6,
    require_experimental=True
))

# Custom voting
pipeline.set_voting_strategy('concentrations', 'consensus')

# Enrich
enriched = pipeline.enrich_pathway(pathway)
```

### Selective Enrichment

```python
# Only enrich specific types
enriched = pipeline.enrich_pathway(
    pathway,
    enrichment_types=['coordinates', 'concentrations']
)

# Enrich single species
enriched_species = pipeline.enrich_species(
    species_id="C00031",
    enrichment_types=['concentration', 'structure']
)
```

---

## Implementation Phases

| Phase | Weeks | Goal | Deliverable |
|-------|-------|------|-------------|
| **1. Foundation** | 1-2 | Core infrastructure | Base classes, utilities |
| **2. Coordinates** | 3-4 | Layout enrichment | Multi-source coordinates |
| **3. Concentrations** | 5-6 | Initial values | BioModels + SABIO-RK |
| **4. Kinetics** | 7-8 | Rate parameters | BRENDA integration |
| **5. Metadata** | 9-10 | Annotations | ChEBI + UniProt |
| **6. Integration** | 11-12 | Complete system | Production-ready |

---

## Key Classes

### EnrichmentPipeline
```python
class EnrichmentPipeline:
    """Main orchestrator for enrichment."""
    
    def enrich_pathway(self, pathway, types=None) -> EnrichedPathway:
        """Enrich pathway with multi-source data."""
        
    def register_fetcher(self, fetcher: BaseFetcher):
        """Register a data fetcher."""
```

### BaseFetcher
```python
class BaseFetcher(ABC):
    """Abstract base for data fetchers."""
    
    @abstractmethod
    def fetch(self, identifier: str, data_type: str) -> FetchResult:
        """Fetch data for identifier."""
    
    @abstractmethod
    def get_priority(self) -> int:
        """Return priority (higher = preferred)."""
```

### QualityScorer
```python
class QualityScorer:
    """Assess quality of fetched data."""
    
    def score(self, result: FetchResult) -> QualityMetrics:
        """Score quality of fetch result."""
```

### ConflictResolver
```python
class ConflictResolver:
    """Resolve conflicts between sources."""
    
    def resolve(self, results: List[FetchResult], 
                strategy: str = "quality_weighted") -> FetchResult:
        """Select best result using voting strategy."""
```

---

## Source Attribution

Every enriched field tracks its source:

```python
enriched_species.sources = {
    'initial_concentration': SourceAttribution(
        source_name='BioModels',
        quality_score=0.95,
        url='https://...',
        timestamp='2025-01-10T14:23:22Z'
    ),
    'coordinates': SourceAttribution(
        source_name='KEGG',
        quality_score=0.75,
        timestamp='2025-01-10T14:23:17Z'
    )
}
```

Saved in JSON:
```json
{
  "id": "C00031",
  "initial_concentration": 10.0,
  "enrichment": {
    "initial_concentration": {
      "source": "BioModels",
      "quality": 0.95
    }
  }
}
```

---

## Database APIs

| Database | URL | Specialization |
|----------|-----|----------------|
| BioModels | ebi.ac.uk/biomodels | Curated models |
| KEGG | rest.kegg.jp | Pathways, compounds |
| Reactome | reactome.org/ContentService | Expert pathways |
| WikiPathways | wikipathways.org/api | Community pathways |
| ChEBI | ebi.ac.uk/chebi/webServices | Chemical entities |
| UniProt | uniprot.org/help/api | Protein data |
| SABIO-RK | sabio.h-its.org/webservice | Kinetic parameters |
| BRENDA | brenda-enzymes.org | Enzyme data |

---

## Success Metrics

**Coverage**:
- Coordinates: >80% of species
- Concentrations: >50% of species
- Kinetics: >60% of reactions

**Quality**:
- Average score: >0.75
- Source diversity: 3+ sources per pathway
- Conflicts: <5% manual intervention

**Performance**:
- Enrichment time: <30 seconds
- API success: >95%
- Cache hit rate: >70%

---

## Benefits

✅ **Complete Pathways**: Fill all missing data  
✅ **Best Quality**: Curated sources preferred  
✅ **Transparent**: Know where every value came from  
✅ **Intelligent**: Automatic conflict resolution  
✅ **Extensible**: Easy to add new sources  
✅ **Fast**: Parallel fetching + caching  

---

## Next Steps

1. **Phase 1**: Implement foundation (2 weeks)
2. **Phase 2**: Coordinate enrichment (2 weeks)
3. **Phase 3**: Concentration enrichment (2 weeks)

See `CROSSFETCH_SYSTEM_PLAN.md` for complete details.

---

**Status**: 📋 Planning Complete  
**Priority**: High  
**Timeline**: 12 weeks  
**Last Updated**: January 10, 2025
