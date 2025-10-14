# Cross-Fetch Information Enrichment System - Comprehensive Plan

**Date**: January 10, 2025  
**Status**: 📋 Planning Phase  
**Purpose**: Multi-source pathway data aggregation and quality-based selection

---

## Executive Summary

The **Cross-Fetch System** is a specialized information enrichment pipeline that aggregates pathway data from multiple reliable sources (BioModels, KEGG, Reactome, WikiPathways, ChEBI, UniProt) to create the most complete and accurate representation possible. When the primary source lacks information, the system automatically queries complementary sources and intelligently selects the best data based on quality metrics.

### Core Principle

> "A Shypn pathway is a composition of several reliable sources of information, with quality-based voting to select the best data available."

---

## 1. System Architecture

### 1.1 Package Structure

```
src/shypn/crossfetch/
├── __init__.py                      # Package initialization
├── core/
│   ├── __init__.py
│   ├── enrichment_pipeline.py       # Main orchestrator
│   ├── quality_scorer.py            # Quality assessment engine
│   ├── data_aggregator.py           # Multi-source data merger
│   └── conflict_resolver.py         # Handles data conflicts
├── fetchers/                        # Specialized data fetchers
│   ├── __init__.py
│   ├── base_fetcher.py              # Abstract base class
│   ├── biomodels_fetcher.py         # BioModels Database
│   ├── kegg_fetcher.py              # KEGG API (enhanced)
│   ├── reactome_fetcher.py          # Reactome API
│   ├── wikipathways_fetcher.py      # WikiPathways API
│   ├── chebi_fetcher.py             # ChEBI for compounds
│   └── uniprot_fetcher.py           # UniProt for proteins
├── enrichers/                       # Data type enrichers
│   ├── __init__.py
│   ├── base_enricher.py             # Abstract base class
│   ├── concentration_enricher.py    # Initial concentrations
│   ├── coordinate_enricher.py       # Layout positions
│   ├── kinetic_enricher.py          # Rate parameters
│   ├── annotation_enricher.py       # Metadata & cross-refs
│   └── structure_enricher.py        # Chemical structures
├── models/
│   ├── __init__.py
│   ├── enrichment_result.py         # Result data structures
│   ├── quality_metrics.py           # Quality scoring models
│   └── source_metadata.py           # Source attribution
├── policies/
│   ├── __init__.py
│   ├── quality_policy.py            # Quality ranking rules
│   ├── priority_policy.py           # Source priority rules
│   └── voting_policy.py             # Multi-source voting
└── utils/
    ├── __init__.py
    ├── cache_manager.py             # API response caching
    ├── rate_limiter.py              # API rate limiting
    └── logger.py                    # Enrichment logging
```

---

## 2. Information Types to Enrich

### 2.1 Core Data Types

| Information Type | Primary Sources | Fallback Sources | Quality Metrics |
|------------------|----------------|------------------|-----------------|
| **Drawing Coordinates** | KEGG KGML, Reactome | WikiPathways, Layout algorithms | Coverage %, positioning consistency |
| **Initial Concentrations** | BioModels, SABIO-RK | Literature values, typical ranges | Experimental validation, confidence level |
| **Kinetic Parameters** | BioModels, SABIO-RK | BRENDA, manual curation | R² fit quality, experimental conditions |
| **Stoichiometry** | SBML, KEGG | Reactome, MetaCyc | Pathway consistency, mass balance |
| **Chemical Structures** | ChEBI, PubChem | KEGG Compound | Structure completeness, validation |
| **Protein Information** | UniProt, PDB | KEGG Genes | Annotation quality, evidence codes |
| **Cross-References** | Multiple databases | ID mapping services | Reference consistency |
| **Compartments** | Gene Ontology, SBML | Manual curation | GO evidence codes |

### 2.2 Enrichment Priority

1. **Critical** (blocks simulation):
   - Initial concentrations/markings
   - Kinetic parameters
   - Stoichiometry

2. **High** (affects accuracy):
   - Compartment assignments
   - Rate law types
   - Enzyme associations

3. **Medium** (improves usability):
   - Drawing coordinates
   - Names and descriptions
   - Cross-references

4. **Low** (nice to have):
   - Chemical structures
   - External links
   - Literature citations

---

## 3. Specialized Fetcher Classes

### 3.1 Base Fetcher Interface

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

@dataclass
class FetchResult:
    """Result from a data fetcher."""
    source: str                    # Source name (e.g., "KEGG")
    data: Optional[Dict[str, Any]] # Fetched data
    quality_score: float           # 0.0-1.0
    confidence: str                # "high", "medium", "low"
    timestamp: datetime
    metadata: Dict[str, Any]       # Source-specific metadata
    errors: List[str]              # Any errors encountered

class BaseFetcher(ABC):
    """Abstract base class for data fetchers."""
    
    def __init__(self, cache_manager: CacheManager, rate_limiter: RateLimiter):
        self.cache = cache_manager
        self.rate_limiter = rate_limiter
        self.logger = logging.getLogger(self.__class__.__name__)
    
    @abstractmethod
    def fetch(self, identifier: str, data_type: str) -> FetchResult:
        """Fetch data for an identifier.
        
        Args:
            identifier: Database ID or cross-reference
            data_type: Type of data ("concentration", "coordinates", etc.)
            
        Returns:
            FetchResult with data and quality score
        """
        pass
    
    @abstractmethod
    def supports(self, data_type: str) -> bool:
        """Check if fetcher supports a data type."""
        pass
    
    @abstractmethod
    def get_priority(self) -> int:
        """Return priority level (higher = preferred)."""
        pass
```

### 3.2 Fetcher Implementations

#### BioModels Fetcher
```python
class BioModelsFetcher(BaseFetcher):
    """Fetch from BioModels Database (EBI).
    
    Specializes in:
    - Curated SBML models
    - Initial concentrations
    - Kinetic parameters
    - Literature-validated data
    """
    
    BASE_URL = "https://www.ebi.ac.uk/biomodels"
    
    def fetch(self, identifier: str, data_type: str) -> FetchResult:
        # Implementation details
        pass
    
    def get_priority(self) -> int:
        return 10  # Highest - curated data
```

#### KEGG Fetcher (Enhanced)
```python
class KEGGFetcher(BaseFetcher):
    """Enhanced KEGG API fetcher.
    
    Specializes in:
    - Pathway coordinates (KGML)
    - Compound structures
    - Reaction stoichiometry
    - Cross-references
    """
    
    BASE_URL = "https://rest.kegg.jp"
    
    def fetch_coordinates(self, pathway_id: str, compound_id: str) -> FetchResult:
        """Fetch coordinates from KGML."""
        pass
    
    def fetch_compound_info(self, compound_id: str) -> FetchResult:
        """Fetch compound details."""
        pass
    
    def get_priority(self) -> int:
        return 8  # High - comprehensive but auto-generated
```

#### Reactome Fetcher
```python
class ReactomeFetcher(BaseFetcher):
    """Fetch from Reactome pathway database.
    
    Specializes in:
    - Pathway diagrams
    - Protein-protein interactions
    - Disease associations
    - Hierarchical pathways
    """
    
    BASE_URL = "https://reactome.org/ContentService"
    
    def get_priority(self) -> int:
        return 9  # Very high - expert-curated
```

#### ChEBI Fetcher
```python
class ChEBIFetcher(BaseFetcher):
    """Fetch from Chemical Entities of Biological Interest.
    
    Specializes in:
    - Chemical structures
    - Molecular formulas
    - Physical properties
    - Synonyms
    """
    
    BASE_URL = "https://www.ebi.ac.uk/chebi/webServices"
    
    def get_priority(self) -> int:
        return 9  # Very high for chemical data
```

---

## 4. Enrichment Pipeline

### 4.1 Pipeline Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 SBML Import (Primary Source)                │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Identify Missing Information                    │
│  • No coordinates? → Need layout enrichment                 │
│  • No concentrations? → Need concentration enrichment       │
│  • No kinetics? → Need kinetic enrichment                   │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           Query Multiple Sources in Parallel                 │
│  • BioModels API    • KEGG API    • Reactome API            │
│  • WikiPathways API • ChEBI API   • UniProt API             │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Quality Assessment & Scoring                    │
│  • Completeness score   • Confidence level                  │
│  • Source reliability   • Data consistency                  │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              Conflict Resolution & Voting                    │
│  • Weighted voting by quality                               │
│  • Priority-based selection                                 │
│  • Consensus algorithms                                     │
└───────────────────────────┬─────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│           Merge and Create Enriched Pathway                 │
│  • Combine best data from all sources                       │
│  • Log source attribution                                   │
│  • Track quality metrics                                    │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Enrichment Pipeline Class

```python
class EnrichmentPipeline:
    """Main orchestrator for multi-source enrichment."""
    
    def __init__(self):
        self.fetchers: List[BaseFetcher] = []
        self.enrichers: List[BaseEnricher] = []
        self.quality_scorer = QualityScorer()
        self.conflict_resolver = ConflictResolver()
        self.cache = CacheManager()
        self.logger = EnrichmentLogger()
    
    def register_fetcher(self, fetcher: BaseFetcher):
        """Register a data fetcher."""
        self.fetchers.append(fetcher)
        self.fetchers.sort(key=lambda f: f.get_priority(), reverse=True)
    
    def enrich_pathway(self, 
                       pathway_data: PathwayData,
                       enrichment_types: List[str] = None) -> EnrichedPathway:
        """Enrich pathway with multi-source data.
        
        Args:
            pathway_data: Primary pathway data (e.g., from SBML)
            enrichment_types: Types to enrich (None = all)
            
        Returns:
            EnrichedPathway with best data from all sources
        """
        # Step 1: Analyze what's missing
        missing = self._analyze_missing_data(pathway_data)
        self.logger.info(f"Missing data types: {missing}")
        
        # Step 2: Fetch from multiple sources
        fetch_results = {}
        for data_type in missing:
            fetch_results[data_type] = self._fetch_from_all_sources(
                pathway_data, data_type
            )
        
        # Step 3: Score quality
        scored_results = self._score_all_results(fetch_results)
        
        # Step 4: Resolve conflicts and select best
        best_data = self._resolve_and_select_best(scored_results)
        
        # Step 5: Merge into enriched pathway
        enriched = self._merge_enrichments(pathway_data, best_data)
        
        # Step 6: Log attribution
        self._log_enrichment_sources(enriched)
        
        return enriched
    
    def _fetch_from_all_sources(self, 
                                 pathway_data: PathwayData, 
                                 data_type: str) -> List[FetchResult]:
        """Query all relevant sources for a data type."""
        results = []
        
        for fetcher in self.fetchers:
            if not fetcher.supports(data_type):
                continue
            
            try:
                result = fetcher.fetch(
                    identifier=pathway_data.get_identifier(fetcher.source),
                    data_type=data_type
                )
                
                if result.data:
                    results.append(result)
                    self.logger.info(
                        f"✓ {fetcher.__class__.__name__}: "
                        f"quality={result.quality_score:.2f}"
                    )
            
            except Exception as e:
                self.logger.warning(f"✗ {fetcher.__class__.__name__}: {e}")
        
        return results
```

---

## 5. Quality Scoring System

### 5.1 Quality Metrics

```python
@dataclass
class QualityMetrics:
    """Quality assessment for fetched data."""
    
    # Completeness (0.0-1.0)
    completeness: float       # % of fields populated
    
    # Confidence level
    confidence: str           # "high", "medium", "low", "predicted"
    
    # Source reliability (0.0-1.0)
    source_reliability: float # Based on database reputation
    
    # Data consistency (0.0-1.0)
    consistency: float        # Internal consistency checks
    
    # Validation status
    experimental: bool        # Experimentally validated?
    curated: bool            # Manually curated?
    
    # Metadata
    evidence_codes: List[str] # GO evidence codes, etc.
    citations: List[str]      # PubMed IDs
    last_updated: datetime    # Data freshness
    
    def compute_overall_score(self) -> float:
        """Compute weighted overall quality score."""
        weights = {
            'completeness': 0.25,
            'source_reliability': 0.30,
            'consistency': 0.20,
            'validation': 0.25,
        }
        
        validation_score = (
            (0.6 if self.experimental else 0.0) +
            (0.4 if self.curated else 0.0)
        )
        
        score = (
            weights['completeness'] * self.completeness +
            weights['source_reliability'] * self.source_reliability +
            weights['consistency'] * self.consistency +
            weights['validation'] * validation_score
        )
        
        return score
```

### 5.2 Quality Scorer

```python
class QualityScorer:
    """Assesses quality of fetched data."""
    
    def __init__(self):
        self.source_reliability = {
            'BioModels': 1.0,      # Curated, peer-reviewed
            'Reactome': 0.95,      # Expert-curated
            'UniProt': 0.95,       # Expert-curated
            'ChEBI': 0.95,         # Expert-curated
            'KEGG': 0.85,          # Comprehensive, auto-generated
            'WikiPathways': 0.80,  # Community-curated
            'SABIO-RK': 0.90,      # Kinetic data specialist
            'PubChem': 0.75,       # Large, variable quality
            'Predicted': 0.30,     # Computational predictions
        }
    
    def score(self, fetch_result: FetchResult, data_type: str) -> QualityMetrics:
        """Score quality of a fetch result."""
        
        completeness = self._assess_completeness(fetch_result.data, data_type)
        consistency = self._check_consistency(fetch_result.data)
        
        return QualityMetrics(
            completeness=completeness,
            confidence=fetch_result.confidence,
            source_reliability=self.source_reliability.get(
                fetch_result.source, 0.5
            ),
            consistency=consistency,
            experimental=self._is_experimental(fetch_result),
            curated=self._is_curated(fetch_result),
            evidence_codes=fetch_result.metadata.get('evidence', []),
            citations=fetch_result.metadata.get('citations', []),
            last_updated=fetch_result.timestamp,
        )
```

---

## 6. Conflict Resolution & Voting

### 6.1 Voting Strategies

```python
class VotingPolicy:
    """Policies for selecting best data when multiple sources available."""
    
    @staticmethod
    def quality_weighted_vote(results: List[FetchResult]) -> FetchResult:
        """Select based on quality scores (default)."""
        return max(results, key=lambda r: r.quality_score)
    
    @staticmethod
    def source_priority_vote(results: List[FetchResult]) -> FetchResult:
        """Select based on source priority."""
        priority_order = ['BioModels', 'Reactome', 'UniProt', 'KEGG']
        
        for source in priority_order:
            for result in results:
                if result.source == source and result.quality_score > 0.5:
                    return result
        
        # Fallback to quality
        return VotingPolicy.quality_weighted_vote(results)
    
    @staticmethod
    def consensus_vote(results: List[FetchResult], 
                       threshold: float = 0.7) -> Optional[FetchResult]:
        """Select if multiple sources agree."""
        # Group by value
        from collections import defaultdict
        value_groups = defaultdict(list)
        
        for result in results:
            value_key = _hash_data(result.data)
            value_groups[value_key].append(result)
        
        # Find consensus (multiple high-quality sources agree)
        for group in value_groups.values():
            if len(group) >= 2:  # At least 2 sources
                avg_quality = sum(r.quality_score for r in group) / len(group)
                if avg_quality >= threshold:
                    return max(group, key=lambda r: r.quality_score)
        
        return None  # No consensus
    
    @staticmethod
    def merge_complementary(results: List[FetchResult]) -> FetchResult:
        """Merge non-conflicting data from multiple sources."""
        # Combine data where sources complement each other
        merged_data = {}
        
        for result in sorted(results, key=lambda r: r.quality_score, reverse=True):
            for key, value in result.data.items():
                if key not in merged_data:
                    merged_data[key] = value
        
        # Create merged result with highest quality source as primary
        best = max(results, key=lambda r: r.quality_score)
        return FetchResult(
            source=f"Merged({', '.join(r.source for r in results)})",
            data=merged_data,
            quality_score=sum(r.quality_score for r in results) / len(results),
            confidence="medium",
            timestamp=datetime.now(),
            metadata={'sources': [r.source for r in results]},
            errors=[]
        )
```

### 6.2 Conflict Resolver

```python
class ConflictResolver:
    """Resolves conflicts when multiple sources provide different data."""
    
    def __init__(self):
        self.voting_policy = VotingPolicy()
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def resolve(self, 
                results: List[FetchResult],
                strategy: str = "quality_weighted") -> FetchResult:
        """Resolve conflict between multiple fetch results.
        
        Args:
            results: List of fetch results for same data
            strategy: Resolution strategy
                - "quality_weighted": Select best quality
                - "source_priority": Use source priority
                - "consensus": Require multiple sources to agree
                - "merge": Merge complementary data
        
        Returns:
            Resolved FetchResult
        """
        if not results:
            raise ValueError("No results to resolve")
        
        if len(results) == 1:
            return results[0]
        
        self.logger.info(f"Resolving conflict: {len(results)} sources")
        
        # Apply strategy
        if strategy == "quality_weighted":
            resolved = self.voting_policy.quality_weighted_vote(results)
        elif strategy == "source_priority":
            resolved = self.voting_policy.source_priority_vote(results)
        elif strategy == "consensus":
            resolved = self.voting_policy.consensus_vote(results)
            if not resolved:
                # Fall back to quality if no consensus
                resolved = self.voting_policy.quality_weighted_vote(results)
        elif strategy == "merge":
            resolved = self.voting_policy.merge_complementary(results)
        else:
            raise ValueError(f"Unknown strategy: {strategy}")
        
        self.logger.info(f"Resolved: {resolved.source} (quality={resolved.quality_score:.2f})")
        return resolved
```

---

## 7. Enriched Pathway Model

### 7.1 Data Structures

```python
@dataclass
class SourceAttribution:
    """Track which source provided which data."""
    source_name: str
    data_type: str
    quality_score: float
    timestamp: datetime
    url: Optional[str] = None

@dataclass
class EnrichedSpecies(Species):
    """Species with enrichment metadata."""
    
    # Original Species fields inherited
    
    # Enrichment tracking
    sources: Dict[str, SourceAttribution] = field(default_factory=dict)
    quality_scores: Dict[str, float] = field(default_factory=dict)
    enrichment_log: List[str] = field(default_factory=list)
    
    def add_enrichment(self, field: str, value: Any, attribution: SourceAttribution):
        """Add enriched data with attribution."""
        setattr(self, field, value)
        self.sources[field] = attribution
        self.enrichment_log.append(
            f"{field} from {attribution.source_name} (quality={attribution.quality_score:.2f})"
        )

@dataclass
class EnrichedPathway(PathwayData):
    """Pathway with multi-source enrichment."""
    
    # Original PathwayData fields inherited
    
    # Enrichment metadata
    enrichment_summary: Dict[str, Any] = field(default_factory=dict)
    source_attributions: List[SourceAttribution] = field(default_factory=list)
    quality_report: Optional[Dict[str, float]] = None
    enrichment_timestamp: Optional[datetime] = None
    
    def get_enrichment_report(self) -> str:
        """Generate human-readable enrichment report."""
        report = ["="*60]
        report.append("PATHWAY ENRICHMENT REPORT")
        report.append("="*60)
        report.append(f"\nPathway: {self.metadata.get('name', 'Unknown')}")
        report.append(f"Enriched: {self.enrichment_timestamp}")
        report.append(f"\nSources used:")
        
        source_counts = {}
        for attr in self.source_attributions:
            source_counts[attr.source_name] = source_counts.get(attr.source_name, 0) + 1
        
        for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
            report.append(f"  • {source}: {count} fields")
        
        report.append(f"\nQuality Summary:")
        if self.quality_report:
            for data_type, score in self.quality_report.items():
                report.append(f"  • {data_type}: {score:.2%}")
        
        report.append("="*60)
        return "\n".join(report)
```

---

## 8. Implementation Phases

### Phase 1: Foundation (Weeks 1-2)

**Goal**: Core infrastructure

**Tasks**:
- [ ] Create `src/shypn/crossfetch/` package structure
- [ ] Implement `BaseFetcher` abstract class
- [ ] Implement `BaseEnricher` abstract class
- [ ] Create quality scoring framework
- [ ] Implement `CacheManager` for API responses
- [ ] Implement `RateLimiter` for API respect
- [ ] Create enrichment logging system

**Deliverables**:
- Package skeleton
- Base classes
- Utility infrastructure

### Phase 2: Coordinate Enrichment (Weeks 3-4)

**Goal**: Enhance existing coordinate resolution

**Tasks**:
- [ ] Refactor existing `KEGGFetcher` to new system
- [ ] Implement `ReactomeFetcher` for coordinates
- [ ] Implement `WikiPathwaysFetcher` for coordinates
- [ ] Create `CoordinateEnricher` class
- [ ] Implement quality voting for coordinates
- [ ] Integration tests

**Deliverables**:
- Working coordinate enrichment
- Multi-source coordinate selection
- Test coverage

### Phase 3: Concentration Enrichment (Weeks 5-6)

**Goal**: Fill missing initial concentrations

**Tasks**:
- [ ] Implement `BioModelsFetcher` for concentrations
- [ ] Query SABIO-RK kinetic database
- [ ] Create `ConcentrationEnricher` class
- [ ] Implement typical concentration ranges
- [ ] Quality assessment for concentrations
- [ ] Unit conversion handling

**Deliverables**:
- Concentration enrichment
- Unit conversion
- Range validation

### Phase 4: Kinetic Enrichment (Weeks 7-8)

**Goal**: Complete kinetic parameters

**Tasks**:
- [ ] Fetch kinetic laws from BioModels
- [ ] Query BRENDA enzyme database
- [ ] Create `KineticEnricher` class
- [ ] Implement parameter extraction
- [ ] Quality scoring for kinetic data
- [ ] Integration with existing rate functions

**Deliverables**:
- Kinetic parameter enrichment
- BRENDA integration
- Quality assessment

### Phase 5: Metadata Enrichment (Weeks 9-10)

**Goal**: Complete annotations

**Tasks**:
- [ ] Implement `ChEBIFetcher` for compounds
- [ ] Implement `UniProtFetcher` for proteins
- [ ] Create `AnnotationEnricher` class
- [ ] Cross-reference resolution
- [ ] Structure enrichment
- [ ] Literature citations

**Deliverables**:
- Complete metadata enrichment
- Cross-reference linking
- Structure information

### Phase 6: Integration & Polish (Weeks 11-12)

**Goal**: Complete pipeline integration

**Tasks**:
- [ ] Integrate with SBML import pipeline
- [ ] Create enrichment UI (progress dialog)
- [ ] Comprehensive testing
- [ ] Performance optimization
- [ ] Documentation
- [ ] User guide

**Deliverables**:
- Production-ready system
- UI integration
- Complete documentation

---

## 9. Quality Policies (To Be Developed)

### 9.1 Source Priority Rules

```python
# Coordinate enrichment priority
COORDINATE_PRIORITY = [
    'Reactome',      # Highest: Expert-curated diagrams
    'KEGG',          # High: Comprehensive, auto-generated
    'WikiPathways',  # Medium: Community-curated
    'LayoutAlgorithm' # Fallback: Automatic layout
]

# Concentration priority
CONCENTRATION_PRIORITY = [
    'BioModels',     # Highest: Curated, validated
    'SABIO-RK',      # High: Kinetic data specialist
    'Literature',    # Medium: Manual curation
    'TypicalRange'   # Fallback: Typical values
]

# Kinetic parameter priority
KINETIC_PRIORITY = [
    'BioModels',     # Highest: Validated models
    'SABIO-RK',      # High: Experimental kinetics
    'BRENDA',        # High: Enzyme database
    'Predicted'      # Fallback: Computational
]
```

### 9.2 Quality Thresholds

```python
# Minimum quality scores to accept data
QUALITY_THRESHOLDS = {
    'coordinates': 0.3,      # Accept low quality (better than random)
    'concentrations': 0.5,   # Require medium quality
    'kinetics': 0.6,         # Require good quality
    'annotations': 0.4,      # Accept medium-low quality
}

# Quality score weights
QUALITY_WEIGHTS = {
    'completeness': 0.25,
    'source_reliability': 0.30,
    'consistency': 0.20,
    'validation': 0.25,
}
```

### 9.3 Voting Strategies by Data Type

```python
VOTING_STRATEGIES = {
    'coordinates': 'quality_weighted',  # Best visual layout
    'concentrations': 'consensus',      # Multiple sources must agree
    'kinetics': 'source_priority',      # Trust expert databases
    'annotations': 'merge',             # Combine all sources
    'structures': 'consensus',          # Chemical structure must match
}
```

---

## 10. API Design Examples

### 10.1 Simple Usage

```python
from shypn.crossfetch import EnrichmentPipeline
from shypn.data.pathway import PathwayData

# Import SBML (primary source)
sbml_pathway = import_sbml("BIOMD0000000001.xml")

# Create enrichment pipeline
pipeline = EnrichmentPipeline()

# Auto-register standard fetchers
pipeline.register_standard_fetchers()

# Enrich pathway
enriched_pathway = pipeline.enrich_pathway(
    sbml_pathway,
    enrichment_types=['coordinates', 'concentrations', 'kinetics']
)

# Check results
print(enriched_pathway.get_enrichment_report())
```

### 10.2 Custom Configuration

```python
# Custom fetcher priorities
pipeline = EnrichmentPipeline()
pipeline.register_fetcher(BioModelsFetcher(priority=10))
pipeline.register_fetcher(KEGGFetcher(priority=8))
pipeline.register_fetcher(ReactomeFetcher(priority=9))

# Custom quality policy
pipeline.set_quality_policy(QualityPolicy(
    min_completeness=0.5,
    require_experimental=True
))

# Custom voting strategy
pipeline.set_voting_strategy('concentrations', 'consensus')

# Enrich with logging
with enrichment_logger('pathway_enrichment.log'):
    enriched = pipeline.enrich_pathway(sbml_pathway)
```

### 10.3 Manual Override

```python
# Enrich specific species only
enriched_species = pipeline.enrich_species(
    species_id="C00031",
    enrichment_types=['concentration', 'structure']
)

# Get all fetch results (not just best)
all_results = pipeline.fetch_all_sources(
    species_id="C00031",
    data_type="concentration"
)

# Manual selection
best_result = user_select_result(all_results)
pathway.apply_enrichment(species_id, best_result)
```

---

## 11. Logging & Attribution

### 11.1 Enrichment Log Format

```
[2025-01-10 14:23:15] ENRICHMENT START: BIOMD0000000001
[2025-01-10 14:23:15] Primary source: BioModels SBML
[2025-01-10 14:23:15] Missing data: coordinates (100%), concentrations (20%)

[2025-01-10 14:23:16] Fetching coordinates...
[2025-01-10 14:23:17]   ✓ KEGG: 85% coverage, quality=0.75
[2025-01-10 14:23:18]   ✓ Reactome: 60% coverage, quality=0.90
[2025-01-10 14:23:19]   ✗ WikiPathways: Not found
[2025-01-10 14:23:19] Selected: KEGG (better coverage)

[2025-01-10 14:23:20] Fetching concentrations...
[2025-01-10 14:23:22]   ✓ BioModels: 5 species, quality=0.95
[2025-01-10 14:23:23]   ✓ SABIO-RK: 3 species, quality=0.85
[2025-01-10 14:23:23] Merged: BioModels primary, SABIO-RK complementary

[2025-01-10 14:23:25] ENRICHMENT COMPLETE
[2025-01-10 14:23:25] Quality summary:
[2025-01-10 14:23:25]   • coordinates: 85% (KEGG)
[2025-01-10 14:23:25]   • concentrations: 95% (BioModels + SABIO-RK)
[2025-01-10 14:23:25] Overall pathway quality: 0.87
```

### 11.2 Source Attribution in Saved Files

```json
{
  "pathway": {
    "id": "BIOMD0000000001",
    "name": "Repressilator",
    "species": [
      {
        "id": "C00031",
        "name": "Glucose",
        "initial_concentration": 10.0,
        "x": 250.5,
        "y": 180.0,
        "enrichment": {
          "initial_concentration": {
            "source": "BioModels",
            "quality": 0.95,
            "url": "https://www.ebi.ac.uk/biomodels/...",
            "timestamp": "2025-01-10T14:23:22Z"
          },
          "coordinates": {
            "source": "KEGG",
            "quality": 0.75,
            "pathway_id": "hsa00010",
            "timestamp": "2025-01-10T14:23:17Z"
          }
        }
      }
    ]
  }
}
```

---

## 12. Testing Strategy

### 12.1 Unit Tests

- Test each fetcher independently
- Mock API responses
- Test quality scoring
- Test conflict resolution
- Test voting strategies

### 12.2 Integration Tests

- Test complete enrichment pipeline
- Test with real API calls (rate-limited)
- Test with known pathways (BIOMD0000000001, etc.)
- Verify quality of enrichments
- Check attribution accuracy

### 12.3 Performance Tests

- API response time monitoring
- Cache effectiveness
- Parallel fetch performance
- Memory usage with large pathways

---

## 13. Future Enhancements

### 13.1 Machine Learning Integration

- Learn optimal voting strategies from user feedback
- Predict missing data using trained models
- Quality score prediction

### 13.2 User Feedback Loop

- Allow users to rate enrichment quality
- Learn from manual corrections
- Improve source priorities over time

### 13.3 Additional Sources

- MetaCyc database
- Pathway Commons
- Systems Biology Ontology
- BiGG Models (metabolic networks)

### 13.4 Advanced Features

- Conflict visualization (show all options to user)
- Interactive enrichment (user selects sources)
- Batch enrichment (multiple pathways)
- Enrichment quality prediction

---

## 14. Success Metrics

### 14.1 Coverage Metrics

- **Coordinate Coverage**: >80% of species with positions
- **Concentration Coverage**: >50% of species with initial values
- **Kinetic Coverage**: >60% of reactions with parameters

### 14.2 Quality Metrics

- **Average Quality Score**: >0.75 for all enrichments
- **Source Diversity**: Data from 3+ sources per pathway
- **Conflict Resolution**: <5% conflicts requiring manual intervention

### 14.3 Performance Metrics

- **Enrichment Time**: <30 seconds for typical pathway
- **API Success Rate**: >95% for all fetchers
- **Cache Hit Rate**: >70% for repeated enrichments

---

## 15. References

### 15.1 Database APIs

- **BioModels**: https://www.ebi.ac.uk/biomodels/docs/
- **KEGG**: https://www.kegg.jp/kegg/rest/keggapi.html
- **Reactome**: https://reactome.org/dev/content-service
- **WikiPathways**: https://www.wikipathways.org/help/api
- **ChEBI**: https://www.ebi.ac.uk/chebi/webServices.do
- **UniProt**: https://www.uniprot.org/help/api
- **SABIO-RK**: http://sabio.h-its.org/webservice

### 15.2 Standards

- **SBML**: http://sbml.org/
- **MIRIAM**: http://www.ebi.ac.uk/miriam/
- **Identifiers.org**: https://identifiers.org/

---

## 16. Conclusion

The Cross-Fetch Information Enrichment System will transform Shypn's pathway import capabilities, creating the most complete and accurate pathway representations possible by intelligently aggregating data from multiple authoritative sources. The quality-based voting system ensures users always get the best available data, with full transparency through source attribution and quality metrics.

**Key Benefits**:
- ✅ More complete pathways (coordinates, concentrations, kinetics)
- ✅ Higher quality data (expert-curated sources preferred)
- ✅ Transparent attribution (know where every value came from)
- ✅ Intelligent conflict resolution (best data wins)
- ✅ Extensible architecture (easy to add new sources)

**Timeline**: 12 weeks for full implementation  
**Priority**: High - Directly improves user experience and simulation accuracy

---

**Document Status**: 📋 Planning Complete - Ready for Implementation  
**Next Step**: Phase 1 - Foundation infrastructure  
**Owner**: Development Team  
**Last Updated**: January 10, 2025
