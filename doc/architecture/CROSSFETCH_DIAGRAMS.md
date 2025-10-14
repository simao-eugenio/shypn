# Cross-Fetch System Architecture Diagrams

**Visual representations of the Cross-Fetch Information Enrichment System**

---

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SHYPN APPLICATION                             │
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │              PATHWAY IMPORT (Primary Source)                │   │
│  │  • SBML File                                                │   │
│  │  • BioModels ID                                             │   │
│  │  • User Input                                               │   │
│  └─────────────────────────┬──────────────────────────────────┘   │
│                            │                                        │
│                            ▼                                        │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │         CROSSFETCH ENRICHMENT SYSTEM                        │   │
│  │                                                             │   │
│  │  ┌─────────────────────────────────────────────────┐      │   │
│  │  │  1. Identify Missing Information                 │      │   │
│  │  │     • No coordinates → need layout               │      │   │
│  │  │     • No concentrations → need values            │      │   │
│  │  │     • No kinetics → need parameters              │      │   │
│  │  └───────────────────┬─────────────────────────────┘      │   │
│  │                      │                                      │   │
│  │                      ▼                                      │   │
│  │  ┌─────────────────────────────────────────────────┐      │   │
│  │  │  2. Query Multiple Sources (Parallel)           │      │   │
│  │  │                                                  │      │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐     │      │   │
│  │  │  │BioModels │  │  KEGG    │  │ Reactome │     │      │   │
│  │  │  └──────────┘  └──────────┘  └──────────┘     │      │   │
│  │  │  ┌──────────┐  ┌──────────┐  ┌──────────┐     │      │   │
│  │  │  │  ChEBI   │  │ UniProt  │  │WikiPaths │     │      │   │
│  │  │  └──────────┘  └──────────┘  └──────────┘     │      │   │
│  │  └───────────────────┬─────────────────────────────┘      │   │
│  │                      │                                      │   │
│  │                      ▼                                      │   │
│  │  ┌─────────────────────────────────────────────────┐      │   │
│  │  │  3. Quality Assessment & Scoring                │      │   │
│  │  │     • Completeness                               │      │   │
│  │  │     • Source reliability                         │      │   │
│  │  │     • Validation status                          │      │   │
│  │  │     • Internal consistency                       │      │   │
│  │  └───────────────────┬─────────────────────────────┘      │   │
│  │                      │                                      │   │
│  │                      ▼                                      │   │
│  │  ┌─────────────────────────────────────────────────┐      │   │
│  │  │  4. Conflict Resolution & Voting                │      │   │
│  │  │     • Weighted voting                            │      │   │
│  │  │     • Priority-based selection                   │      │   │
│  │  │     • Consensus algorithms                       │      │   │
│  │  └───────────────────┬─────────────────────────────┘      │   │
│  │                      │                                      │   │
│  │                      ▼                                      │   │
│  │  ┌─────────────────────────────────────────────────┐      │   │
│  │  │  5. Merge & Create Enriched Pathway             │      │   │
│  │  │     • Best data from all sources                 │      │   │
│  │  │     • Source attribution logged                  │      │   │
│  │  │     • Quality metrics tracked                    │      │   │
│  │  └─────────────────────────────────────────────────┘      │   │
│  └────────────────────────┬───────────────────────────────────┘   │
│                           │                                        │
│                           ▼                                        │
│  ┌────────────────────────────────────────────────────────────┐   │
│  │           ENRICHED PATHWAY (Complete & Attributed)          │   │
│  │  • Drawing Coordinates                                      │   │
│  │  • Initial Concentrations                                   │   │
│  │  • Kinetic Parameters                                       │   │
│  │  • Full Annotations                                         │   │
│  │  • Quality Metrics                                          │   │
│  └────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 2. Package Structure

```
src/shypn/crossfetch/
│
├── __init__.py                    # Package initialization
│
├── core/                          # 🎯 Core Orchestration
│   ├── __init__.py
│   ├── enrichment_pipeline.py    # Main coordinator
│   │   └─ EnrichmentPipeline     # Orchestrates entire process
│   ├── quality_scorer.py         # Quality assessment
│   │   └─ QualityScorer          # Scores fetched data
│   ├── data_aggregator.py        # Data merging
│   │   └─ DataAggregator         # Combines sources
│   └── conflict_resolver.py      # Voting & selection
│       └─ ConflictResolver       # Resolves conflicts
│
├── fetchers/                      # 🌐 Database Clients
│   ├── __init__.py
│   ├── base_fetcher.py           # Abstract base
│   │   └─ BaseFetcher            # Interface for all fetchers
│   ├── biomodels_fetcher.py      # BioModels Database
│   │   └─ BioModelsFetcher       # Priority: 10 (highest)
│   ├── kegg_fetcher.py           # KEGG API
│   │   └─ KEGGFetcher            # Priority: 8
│   ├── reactome_fetcher.py       # Reactome API
│   │   └─ ReactomeFetcher        # Priority: 9
│   ├── wikipathways_fetcher.py   # WikiPathways API
│   │   └─ WikiPathwaysFetcher    # Priority: 7
│   ├── chebi_fetcher.py          # ChEBI Compounds
│   │   └─ ChEBIFetcher           # Priority: 9
│   └── uniprot_fetcher.py        # UniProt Proteins
│       └─ UniProtFetcher         # Priority: 9
│
├── enrichers/                     # 🔬 Type-Specific Enrichment
│   ├── __init__.py
│   ├── base_enricher.py          # Abstract base
│   │   └─ BaseEnricher           # Interface for enrichers
│   ├── concentration_enricher.py # Initial values
│   │   └─ ConcentrationEnricher  # BioModels, SABIO-RK
│   ├── coordinate_enricher.py    # Layout positions
│   │   └─ CoordinateEnricher     # KEGG, Reactome, WikiPathways
│   ├── kinetic_enricher.py       # Rate parameters
│   │   └─ KineticEnricher        # BioModels, BRENDA, SABIO-RK
│   ├── annotation_enricher.py    # Metadata
│   │   └─ AnnotationEnricher     # UniProt, GO, Multiple
│   └── structure_enricher.py     # Chemical structures
│       └─ StructureEnricher      # ChEBI, KEGG Compound
│
├── models/                        # 📦 Data Structures
│   ├── __init__.py
│   ├── enrichment_result.py      # Result classes
│   │   ├─ FetchResult            # Result from fetcher
│   │   ├─ EnrichedSpecies        # Species with enrichment
│   │   └─ EnrichedPathway        # Pathway with enrichment
│   ├── quality_metrics.py        # Quality scoring
│   │   └─ QualityMetrics         # Quality assessment
│   └── source_metadata.py        # Attribution
│       └─ SourceAttribution      # Source tracking
│
├── policies/                      # ⚖️ Selection Rules
│   ├── __init__.py
│   ├── quality_policy.py         # Quality thresholds
│   │   └─ QualityPolicy          # Min quality rules
│   ├── priority_policy.py        # Source priorities
│   │   └─ PriorityPolicy         # Source ranking
│   └── voting_policy.py          # Conflict resolution
│       └─ VotingPolicy           # Selection strategies
│
└── utils/                         # 🛠️ Utilities
    ├── __init__.py
    ├── cache_manager.py          # API response caching
    │   └─ CacheManager           # LRU cache + persistence
    ├── rate_limiter.py           # API rate limiting
    │   └─ RateLimiter            # Respectful API usage
    └── logger.py                 # Enrichment logging
        └─ EnrichmentLogger       # Detailed logging
```

---

## 3. Data Flow Diagram

```
┌───────────────┐
│  SBML Import  │  Primary source (may be incomplete)
└───────┬───────┘
        │
        │ PathwayData
        ▼
┌────────────────────────────────┐
│  EnrichmentPipeline            │
│  .enrich_pathway(pathway_data) │
└───────┬────────────────────────┘
        │
        │ 1. Analyze
        ▼
┌────────────────────────────────┐
│  Identify Missing Data         │
│  • coordinates: 100% missing   │
│  • concentrations: 20% missing │
│  • kinetics: 50% missing       │
└───────┬────────────────────────┘
        │
        │ 2. Fetch (Parallel)
        ▼
┌─────────────────────────────────────────────────────┐
│  Query All Registered Fetchers                      │
│                                                     │
│  ┌─────────────┐  ┌─────────────┐  ┌────────────┐ │
│  │BioModels    │  │  KEGG       │  │ Reactome   │ │
│  │Fetcher      │  │  Fetcher    │  │ Fetcher    │ │
│  │             │  │             │  │            │ │
│  │ fetch()     │  │ fetch()     │  │ fetch()    │ │
│  │   ↓         │  │   ↓         │  │   ↓        │ │
│  │FetchResult  │  │FetchResult  │  │FetchResult │ │
│  │quality=0.95 │  │quality=0.75 │  │quality=0.90│ │
│  └─────────────┘  └─────────────┘  └────────────┘ │
└─────────────────────────────────────────────────────┘
        │
        │ List[FetchResult] per data type
        ▼
┌────────────────────────────────┐
│  QualityScorer                 │
│  .score(fetch_result)          │
│                                │
│  Compute:                      │
│  • Completeness: 0.85          │
│  • Reliability: 0.95           │
│  • Consistency: 0.78           │
│  • Validation: 0.90            │
│  ──────────────────            │
│  Overall: 0.87                 │
└───────┬────────────────────────┘
        │
        │ QualityMetrics per result
        ▼
┌────────────────────────────────┐
│  ConflictResolver              │
│  .resolve(results, strategy)   │
│                                │
│  Strategy: quality_weighted    │
│                                │
│  Results:                      │
│  1. BioModels: 0.95 ← WINNER  │
│  2. Reactome: 0.90            │
│  3. KEGG: 0.75                │
└───────┬────────────────────────┘
        │
        │ Best FetchResult selected
        ▼
┌────────────────────────────────┐
│  DataAggregator                │
│  .merge(pathway, enrichments)  │
│                                │
│  Merge best data into pathway  │
│  Add source attribution        │
│  Track quality metrics         │
└───────┬────────────────────────┘
        │
        │ EnrichedPathway
        ▼
┌────────────────────────────────┐
│  Enriched Pathway              │
│  • Complete data               │
│  • Source attribution          │
│  • Quality report              │
│                                │
│  species[0]:                   │
│    initial_conc: 10.0          │
│    source: BioModels           │
│    quality: 0.95               │
│    coordinates: (250, 180)     │
│    source: KEGG                │
│    quality: 0.75               │
└────────────────────────────────┘
```

---

## 4. Quality Scoring Flow

```
┌──────────────────────────┐
│     FetchResult          │
│  from any Fetcher        │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────────────────┐
│  QualityScorer.score()                │
│                                       │
│  1. Completeness Assessment           │
│     ┌──────────────────────┐         │
│     │ Count populated      │         │
│     │ fields vs total      │         │
│     │                      │         │
│     │ Example:             │         │
│     │ 17/20 fields = 0.85  │         │
│     └──────────────────────┘         │
│                                       │
│  2. Source Reliability Lookup         │
│     ┌──────────────────────┐         │
│     │ BioModels → 1.00     │         │
│     │ Reactome → 0.95      │         │
│     │ KEGG → 0.85          │         │
│     │ Predicted → 0.30     │         │
│     └──────────────────────┘         │
│                                       │
│  3. Consistency Check                 │
│     ┌──────────────────────┐         │
│     │ • Mass balance       │         │
│     │ • Unit consistency   │         │
│     │ • Range validation   │         │
│     │                      │         │
│     │ Pass: 0.90           │         │
│     └──────────────────────┘         │
│                                       │
│  4. Validation Status                 │
│     ┌──────────────────────┐         │
│     │ Experimental? Yes    │         │
│     │ Curated? Yes         │         │
│     │ Evidence codes: 3    │         │
│     │                      │         │
│     │ Score: 1.0           │         │
│     └──────────────────────┘         │
│                                       │
│  5. Weighted Average                  │
│     ┌──────────────────────┐         │
│     │ 0.25 × 0.85 = 0.2125 │         │
│     │ 0.30 × 1.00 = 0.3000 │         │
│     │ 0.20 × 0.90 = 0.1800 │         │
│     │ 0.25 × 1.00 = 0.2500 │         │
│     │ ────────────────────  │         │
│     │ Total:       0.9425  │         │
│     └──────────────────────┘         │
└────────┬─────────────────────────────┘
         │
         ▼
┌──────────────────────────┐
│   QualityMetrics         │
│   overall_score: 0.94    │
│   confidence: "high"     │
└──────────────────────────┘
```

---

## 5. Voting Strategy Decision Tree

```
Multiple FetchResults for same data
         │
         ▼
    ┌─────────────────────┐
    │  What data type?    │
    └──────┬──────────────┘
           │
    ┌──────┴──────────────────────────────────┐
    │                                          │
    ▼                                          ▼
┌───────────┐                          ┌─────────────┐
│Coordinates│                          │Concentrations│
└─────┬─────┘                          └──────┬──────┘
      │                                       │
      │ Strategy: quality_weighted            │ Strategy: consensus
      ▼                                       ▼
┌─────────────────┐                   ┌──────────────────┐
│ Select highest  │                   │ Require 2+ to    │
│ quality score   │                   │ agree            │
│                 │                   │                  │
│ KEGG: 0.85 ✓   │                   │ BioModels: 10.0 ─┐
│ Reactome: 0.75 │                   │ SABIO-RK: 10.0 ──┤→ Match!
│ WikiPaths: 0.60│                   │ Literature: 9.8  │
└─────────────────┘                   └──────────────────┘
                                              │
    ┌─────────────────────────────────────────┤
    │                                         │
    ▼                                         ▼
┌───────────┐                          ┌─────────────┐
│  Kinetics │                          │ Annotations │
└─────┬─────┘                          └──────┬──────┘
      │                                       │
      │ Strategy: source_priority             │ Strategy: merge
      ▼                                       ▼
┌─────────────────┐                   ┌──────────────────┐
│ Follow priority │                   │ Combine all non- │
│ order           │                   │ conflicting data │
│                 │                   │                  │
│ 1. BioModels ✓ │                   │ UniProt: name    │
│ 2. SABIO-RK    │                   │ ChEBI: formula   │
│ 3. BRENDA      │                   │ KEGG: pathway    │
│                 │                   │ → Merge all      │
└─────────────────┘                   └──────────────────┘
```

---

## 6. Fetcher Priority Hierarchy

```
                    PRIORITY PYRAMID
                    ================

                        🏆 10
                  ┌──────────────┐
                  │  BioModels   │  Curated, peer-reviewed
                  └──────────────┘
                      (Highest)

              🥇 9                    🥇 9
         ┌──────────────┐       ┌──────────────┐
         │   Reactome   │       │    ChEBI     │
         │   UniProt    │       │              │
         └──────────────┘       └──────────────┘
         Expert-curated         Chemical specialist

                    🥈 8
              ┌──────────────┐
              │     KEGG     │  Comprehensive
              └──────────────┘
              Auto-generated

                    🥉 7
              ┌──────────────┐
              │ WikiPathways │  Community
              └──────────────┘
              Variable quality

                    ⭐ 5
              ┌──────────────┐
              │   PubChem    │  Large scale
              └──────────────┘
              Variable quality

                    ⚠️ 3
              ┌──────────────┐
              │  Predicted   │  Computational
              └──────────────┘
              Low confidence
```

---

## 7. Cache & Rate Limiting

```
┌──────────────────────────────────────────────────────┐
│             API Request Flow                          │
└──────────────────────────────────────────────────────┘

    Application
        │
        │ fetch(identifier, data_type)
        ▼
┌────────────────────┐
│   BaseFetcher      │
└────────┬───────────┘
         │
         │ 1. Check cache
         ▼
┌────────────────────┐
│   CacheManager     │
│                    │
│   Key: "KEGG:     │
│         C00031:    │
│         coords"    │
│                    │
│   ┌─────────────┐ │
│   │ Hit? Return │ │─────→ Return cached data
│   └─────────────┘ │       (Fast path)
│         │          │
│         │ Miss     │
│         ▼          │
└─────────┬──────────┘
          │
          │ 2. Rate limit
          ▼
┌────────────────────┐
│   RateLimiter      │
│                    │
│   Last req: 0.3s   │
│   Min interval:    │
│   0.5s             │
│                    │
│   → Wait 0.2s      │
└─────────┬──────────┘
          │
          │ 3. Make request
          ▼
┌────────────────────┐
│   External API     │
│   (KEGG, etc.)     │
│                    │
│   Response ────────│───→ Parse result
└────────────────────┘
          │
          │ 4. Cache result
          ▼
┌────────────────────┐
│   CacheManager     │
│   .store(key, data)│
│                    │
│   TTL: 7 days      │
└────────────────────┘
          │
          │ 5. Return
          ▼
    FetchResult
```

---

## 8. Complete Enrichment Example

```
BIOMD0000000001 (Repressilator) Import
══════════════════════════════════════

Initial State (from SBML):
┌─────────────────────────────────┐
│ Species:                        │
│  • PX (protein X)               │
│    concentration: 0.0           │
│    coordinates: MISSING ✗       │
│  • PY (protein Y)               │
│    concentration: 0.0           │
│    coordinates: MISSING ✗       │
│  • PZ (protein Z)               │
│    concentration: MISSING ✗     │
│    coordinates: MISSING ✗       │
└─────────────────────────────────┘
         │
         │ EnrichmentPipeline.enrich_pathway()
         ▼
Step 1: Identify Missing
┌─────────────────────────────────┐
│ Missing:                        │
│  • Coordinates: 100% (3/3)      │
│  • Concentrations: 33% (1/3)    │
└─────────────────────────────────┘
         │
         ▼
Step 2: Fetch from Sources
┌─────────────────────────────────┐
│ Coordinates:                    │
│  KEGG:       None (not found)   │
│  Reactome:   None (not found)   │
│  Algorithm:  Generated ✓        │
│                                 │
│ Concentrations:                 │
│  BioModels:  PZ=0.0 ✓          │
│  SABIO-RK:   None               │
└─────────────────────────────────┘
         │
         ▼
Step 3: Score Quality
┌─────────────────────────────────┐
│ Coordinates:                    │
│  Algorithm: quality=0.40        │
│                                 │
│ Concentrations:                 │
│  BioModels: quality=0.95        │
└─────────────────────────────────┘
         │
         ▼
Step 4: Resolve & Select
┌─────────────────────────────────┐
│ Best:                           │
│  Coordinates → Algorithm        │
│  Concentrations → BioModels     │
└─────────────────────────────────┘
         │
         ▼
Step 5: Merge
┌─────────────────────────────────┐
│ Enriched Pathway:               │
│  • PX: conc=0.0, pos=(100,100) │
│    sources: {conc: SBML,        │
│               pos: Algorithm}   │
│  • PY: conc=0.0, pos=(200,100) │
│    sources: {conc: SBML,        │
│               pos: Algorithm}   │
│  • PZ: conc=0.0, pos=(150,200) │
│    sources: {conc: BioModels,   │
│               pos: Algorithm}   │
│                                 │
│ Overall Quality: 0.67           │
└─────────────────────────────────┘
```

---

## 9. Source Attribution Tracking

```
EnrichedSpecies Object:
┌──────────────────────────────────────────────────┐
│ id: "C00031"                                     │
│ name: "Glucose"                                  │
│ initial_concentration: 10.0                      │
│ x: 250.5                                         │
│ y: 180.0                                         │
│ formula: "C6H12O6"                               │
│                                                  │
│ sources:                                         │
│ ┌─────────────────────────────────────────────┐ │
│ │ 'initial_concentration':                    │ │
│ │   SourceAttribution(                        │ │
│ │     source_name='BioModels',                │ │
│ │     quality_score=0.95,                     │ │
│ │     url='https://www.ebi.ac.uk/...',       │ │
│ │     timestamp='2025-01-10T14:23:22Z'       │ │
│ │   )                                         │ │
│ │                                             │ │
│ │ 'coordinates':                              │ │
│ │   SourceAttribution(                        │ │
│ │     source_name='KEGG',                     │ │
│ │     quality_score=0.75,                     │ │
│ │     pathway_id='hsa00010',                  │ │
│ │     timestamp='2025-01-10T14:23:17Z'       │ │
│ │   )                                         │ │
│ │                                             │ │
│ │ 'formula':                                  │ │
│ │   SourceAttribution(                        │ │
│ │     source_name='ChEBI',                    │ │
│ │     quality_score=0.95,                     │ │
│ │     chebi_id='CHEBI:17234',                │ │
│ │     timestamp='2025-01-10T14:23:19Z'       │ │
│ │   )                                         │ │
│ └─────────────────────────────────────────────┘ │
│                                                  │
│ enrichment_log:                                  │
│   ["initial_concentration from BioModels...",   │
│    "coordinates from KEGG (quality=0.75)",      │
│    "formula from ChEBI (quality=0.95)"]         │
└──────────────────────────────────────────────────┘
```

---

**Visual Documentation Complete**

All diagrams use ASCII art for universal compatibility and version control friendliness.

**Last Updated**: January 10, 2025
