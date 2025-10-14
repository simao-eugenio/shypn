# Cross-Fetch Information Enrichment System - Summary

**Date**: January 10, 2025  
**Status**: 📋 **PLANNING COMPLETE - READY FOR IMPLEMENTATION**

---

## Overview

The **Cross-Fetch System** is a comprehensive multi-source pathway enrichment architecture that automatically aggregates data from multiple authoritative databases to create the most complete and accurate pathway representations possible.

### Core Concept

> **"A Shypn pathway is a composition of several reliable sources of information, with quality-based voting to select the best data ever and logged."**

When importing a pathway (e.g., from SBML), the system:
1. ✅ Identifies missing or incomplete information
2. ✅ Queries multiple authoritative sources in parallel
3. ✅ Scores quality of each source's data
4. ✅ Resolves conflicts using intelligent voting
5. ✅ Merges best data with full attribution
6. ✅ Logs all sources and quality metrics

---

## System Architecture

```
src/shypn/crossfetch/
├── core/                         # Orchestration & scoring
│   ├── enrichment_pipeline.py    # Main pipeline
│   ├── quality_scorer.py         # Quality assessment
│   ├── data_aggregator.py        # Multi-source merger
│   └── conflict_resolver.py      # Voting algorithms
├── fetchers/                     # Database clients
│   ├── biomodels_fetcher.py      # Curated models
│   ├── kegg_fetcher.py           # Pathways & compounds
│   ├── reactome_fetcher.py       # Expert pathways
│   ├── wikipathways_fetcher.py   # Community pathways
│   ├── chebi_fetcher.py          # Chemical entities
│   └── uniprot_fetcher.py        # Protein data
├── enrichers/                    # Type-specific enrichment
│   ├── concentration_enricher.py # Initial values
│   ├── coordinate_enricher.py    # Layout positions
│   ├── kinetic_enricher.py       # Rate parameters
│   └── annotation_enricher.py    # Metadata
├── models/                       # Data structures
│   ├── enrichment_result.py      # Results
│   ├── quality_metrics.py        # Quality scores
│   └── source_metadata.py        # Attribution
└── policies/                     # Selection rules
    ├── quality_policy.py         # Quality thresholds
    └── voting_policy.py          # Conflict resolution
```

---

## Information Types Enriched

| Type | Examples | Primary Sources | Quality Threshold |
|------|----------|----------------|-------------------|
| **Coordinates** | (x, y) positions | KEGG, Reactome, WikiPathways | 0.3 |
| **Concentrations** | Initial markings | BioModels, SABIO-RK | 0.5 |
| **Kinetics** | Vmax, Km, rate constants | BioModels, BRENDA, SABIO-RK | 0.6 |
| **Structures** | Chemical formulas | ChEBI, KEGG Compound | 0.5 |
| **Annotations** | Names, descriptions | UniProt, GO, Multiple | 0.4 |
| **Stoichiometry** | Reaction coefficients | SBML, KEGG, Reactome | 0.7 |
| **Compartments** | Cellular locations | GO, SBML | 0.5 |
| **Cross-refs** | Database IDs | MIRIAM, Identifiers.org | 0.4 |

---

## Quality Scoring System

### Score Calculation

```python
Quality Score = (
    0.25 × Completeness +           # % of fields populated
    0.30 × Source Reliability +     # Database reputation
    0.20 × Internal Consistency +   # Data validation
    0.25 × Validation Status        # Experimental proof
)
```

### Source Reliability Ratings

| Source | Reliability | Reasoning |
|--------|-------------|-----------|
| BioModels | 1.00 | Curated, peer-reviewed, validated |
| Reactome | 0.95 | Expert-curated by pathway specialists |
| UniProt | 0.95 | Expert-curated protein database |
| ChEBI | 0.95 | Expert-curated chemical database |
| SABIO-RK | 0.90 | Kinetic data specialist |
| KEGG | 0.85 | Comprehensive, mostly auto-generated |
| WikiPathways | 0.80 | Community-curated |
| PubChem | 0.75 | Large scale, variable quality |
| Predicted | 0.30 | Computational predictions |

---

## Voting & Conflict Resolution

### Strategies

1. **Quality Weighted** (default)
   - Selects source with highest quality score
   - Fast, reliable for most cases

2. **Source Priority**
   - Follows predefined source ranking
   - Used for critical data (kinetics, stoichiometry)

3. **Consensus**
   - Requires 2+ sources to agree
   - High confidence for concentrations

4. **Merge Complementary**
   - Combines non-conflicting data
   - Best for annotations and metadata

### Strategy Selection by Data Type

```python
VOTING_STRATEGIES = {
    'coordinates': 'quality_weighted',    # Best layout
    'concentrations': 'consensus',        # Must agree
    'kinetics': 'source_priority',        # Trust experts
    'annotations': 'merge',               # Combine all
}
```

---

## Implementation Plan

### Phase 1: Foundation (Weeks 1-2)
**Goal**: Core infrastructure

- [ ] Package structure
- [ ] Base classes (BaseFetcher, BaseEnricher)
- [ ] Quality scoring framework
- [ ] Cache manager
- [ ] Rate limiter
- [ ] Logging system

### Phase 2: Coordinate Enrichment (Weeks 3-4)
**Goal**: Multi-source layout resolution

- [ ] Refactor existing KEGG fetcher
- [ ] Implement Reactome fetcher
- [ ] Implement WikiPathways fetcher
- [ ] CoordinateEnricher class
- [ ] Quality voting
- [ ] Integration tests

### Phase 3: Concentration Enrichment (Weeks 5-6)
**Goal**: Initial value enrichment

- [ ] BioModels fetcher
- [ ] SABIO-RK integration
- [ ] ConcentrationEnricher class
- [ ] Unit conversion
- [ ] Typical ranges fallback

### Phase 4: Kinetic Enrichment (Weeks 7-8)
**Goal**: Rate parameter enrichment

- [ ] BRENDA integration
- [ ] KineticEnricher class
- [ ] Parameter extraction
- [ ] Quality assessment
- [ ] Integration with rate functions

### Phase 5: Metadata Enrichment (Weeks 9-10)
**Goal**: Complete annotations

- [ ] ChEBI fetcher
- [ ] UniProt fetcher
- [ ] AnnotationEnricher class
- [ ] Cross-reference resolution
- [ ] Structure enrichment

### Phase 6: Integration & Polish (Weeks 11-12)
**Goal**: Production-ready system

- [ ] SBML pipeline integration
- [ ] Progress UI
- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Documentation

**Total Timeline**: 12 weeks

---

## Usage Examples

### Basic Usage

```python
from shypn.crossfetch import EnrichmentPipeline

# Import SBML (primary source)
pathway = import_sbml("BIOMD0000000001.xml")

# Create and run enrichment
pipeline = EnrichmentPipeline()
pipeline.register_standard_fetchers()

enriched = pipeline.enrich_pathway(pathway)

# View results
print(enriched.get_enrichment_report())
```

**Output**:
```
============================================================
PATHWAY ENRICHMENT REPORT
============================================================

Pathway: Repressilator
Enriched: 2025-01-10 14:23:25

Sources used:
  • KEGG: 15 fields
  • BioModels: 12 fields
  • ChEBI: 8 fields
  • Reactome: 5 fields

Quality Summary:
  • coordinates: 85%
  • concentrations: 95%
  • kinetics: 78%
  • annotations: 92%

Overall Quality: 0.87
============================================================
```

### Custom Configuration

```python
# Custom priorities and policies
pipeline = EnrichmentPipeline()

pipeline.register_fetcher(BioModelsFetcher(priority=10))
pipeline.register_fetcher(KEGGFetcher(priority=8))

pipeline.set_quality_policy(QualityPolicy(
    min_completeness=0.6,
    require_experimental=True
))

pipeline.set_voting_strategy('concentrations', 'consensus')

enriched = pipeline.enrich_pathway(pathway)
```

---

## Source Attribution

Every enriched field includes full attribution:

```python
# Python object
species.sources = {
    'initial_concentration': SourceAttribution(
        source_name='BioModels',
        quality_score=0.95,
        url='https://www.ebi.ac.uk/biomodels/...',
        timestamp='2025-01-10T14:23:22Z'
    )
}

# Saved to JSON
{
  "id": "C00031",
  "initial_concentration": 10.0,
  "enrichment": {
    "initial_concentration": {
      "source": "BioModels",
      "quality": 0.95,
      "url": "https://...",
      "timestamp": "2025-01-10T14:23:22Z"
    }
  }
}
```

---

## Success Metrics

### Coverage Targets
- ✅ Coordinates: >80% of species with positions
- ✅ Concentrations: >50% of species with initial values
- ✅ Kinetics: >60% of reactions with parameters

### Quality Targets
- ✅ Average quality score: >0.75
- ✅ Source diversity: 3+ sources per pathway
- ✅ Manual conflicts: <5%

### Performance Targets
- ✅ Enrichment time: <30 seconds per pathway
- ✅ API success rate: >95%
- ✅ Cache hit rate: >70%

---

## Benefits

| Benefit | Description |
|---------|-------------|
| **Completeness** | Fill all missing data automatically |
| **Quality** | Expert-curated sources preferred |
| **Transparency** | Know exactly where every value came from |
| **Intelligence** | Automatic conflict resolution |
| **Extensibility** | Easy to add new sources |
| **Performance** | Parallel fetching + caching |
| **Reliability** | Fallback strategies always available |

---

## Documentation Files

1. **CROSSFETCH_SYSTEM_PLAN.md** (62 KB)
   - Complete technical specification
   - Detailed architecture
   - Implementation phases
   - API design

2. **CROSSFETCH_QUICK_REFERENCE.md** (11 KB)
   - Quick overview
   - Usage examples
   - Key concepts
   - Cheat sheet

3. **CROSSFETCH_SUMMARY.md** (This file, 8 KB)
   - Executive summary
   - High-level overview
   - Implementation plan
   - Success metrics

**Total Documentation**: 81 KB, comprehensive planning

---

## Related Work

### Existing Components

The system builds upon existing infrastructure:

- ✅ `src/shypn/data/pathway/sbml_layout_resolver.py` - KEGG coordinate fetching (will be refactored)
- ✅ `src/shypn/importer/kegg/` - KEGG API client (will be enhanced)
- ✅ `src/shypn/data/pathway/pathway_data.py` - Data structures (will be extended)

### Integration Points

- SBML import pipeline (`PathwayPostProcessor`, `PathwayConverter`)
- Property dialogs (display source attribution)
- Simulation engine (use enriched parameters)
- File persistence (save/load attribution)

---

## Next Steps

1. **Review & Approval** ✋ 
   - Review complete plan
   - Approve architecture
   - Confirm priorities

2. **Phase 1 Implementation** (Weeks 1-2)
   - Create package structure
   - Implement base classes
   - Build infrastructure

3. **Iterative Development**
   - Phase 2: Coordinates
   - Phase 3: Concentrations
   - Phase 4: Kinetics
   - Phase 5: Metadata
   - Phase 6: Integration

---

## Conclusion

The Cross-Fetch Information Enrichment System represents a significant advancement in pathway data quality and completeness. By intelligently aggregating information from multiple authoritative sources and applying quality-based selection, Shypn will provide users with the most accurate and complete pathway representations available.

**Key Achievements**:
- ✅ Comprehensive planning complete
- ✅ Architecture fully specified
- ✅ Implementation phases defined
- ✅ Success metrics established
- ✅ Documentation thorough

**Status**: 📋 **READY FOR IMPLEMENTATION**

---

**Timeline**: 12 weeks for full system  
**Priority**: High - Directly improves simulation accuracy  
**Risk**: Low - Builds on proven patterns  
**Impact**: High - Significantly enhances user experience  

**Last Updated**: January 10, 2025  
**Document Version**: 1.0  
**Status**: Planning Complete ✅
