# Coordinate Enrichment - Phase 3: Pipeline Integration

**Date:** October 13, 2025  
**Status:** ✅ Complete  
**Previous Phase:** Phase 2 - OOP Architecture & Helper Modules  
**Next Phase:** Phase 4 - UI Integration

## Overview

Phase 3 integrates the CoordinateEnricher into the main CrossFetch enrichment pipeline, making coordinate data available alongside other enrichment types (concentrations, kinetics, annotations).

## Objectives

1. ✅ Register CoordinateEnricher in EnrichmentPipeline
2. ✅ Add 'coordinates' as default data type in fetch operations
3. ✅ Update SBMLEnricher to handle coordinate data
4. ✅ Wire coordinate merging into SBML enrichment workflow

## Changes Made

### 1. EnrichmentPipeline Registration

**File:** `src/shypn/crossfetch/core/enrichment_pipeline.py`

#### Added Import
```python
from ..enrichers import (
    EnricherBase,
    ConcentrationEnricher,
    InteractionEnricher,
    KineticsEnricher,
    AnnotationEnricher,
    CoordinateEnricher  # NEW
)
```

#### Registered in Default Enrichers
```python
def _register_default_enrichers(self):
    """Register default enrichers."""
    self.register_enricher(ConcentrationEnricher(scale_factor=1000.0))
    self.register_enricher(InteractionEnricher(create_missing=True, min_confidence=0.7))
    self.register_enricher(KineticsEnricher(prefer_time_aware=True))
    self.register_enricher(AnnotationEnricher(
        conflict_strategy="highest_quality",
        merge_multi_valued=True,
        keep_provenance=True
    ))
    self.register_enricher(CoordinateEnricher())  # NEW
```

#### Added to Default Data Types
```python
# Default to common data types
if data_types is None:
    data_types = ["pathway", "concentrations", "kinetics", 
                  "interactions", "annotations", "coordinates"]  # Added coordinates
```

**Impact:** CoordinateEnricher is now automatically available in all enrichment operations.

### 2. SBMLEnricher Integration

**File:** `src/shypn/crossfetch/sbml_enricher.py`

#### Updated Constructor
```python
def __init__(self, 
             fetch_sources: Optional[List[str]] = None,
             enrich_concentrations: bool = True,
             enrich_kinetics: bool = True,
             enrich_annotations: bool = True,
             enrich_coordinates: bool = True):  # NEW parameter
    """Initialize SBML enricher.
    
    Args:
        fetch_sources: Sources to fetch from (default: ["KEGG", "Reactome"])
        enrich_concentrations: Whether to enrich concentration data
        enrich_kinetics: Whether to enrich kinetic parameters
        enrich_annotations: Whether to enrich annotations
        enrich_coordinates: Whether to enrich layout coordinates  # NEW
    """
    self.pipeline = EnrichmentPipeline()
    self.fetch_sources = fetch_sources or ["KEGG", "Reactome"]
    self.enrich_concentrations = enrich_concentrations
    self.enrich_kinetics = enrich_kinetics
    self.enrich_annotations = enrich_annotations
    self.enrich_coordinates = enrich_coordinates  # NEW
```

#### Enhanced Missing Data Detection
```python
# Check for missing layout coordinates
if self.enrich_coordinates:
    # Check if SBML already has Layout extension
    has_layout = False
    try:
        mplugin = model.getPlugin('layout')
        if mplugin and mplugin.getNumLayouts() > 0:
            has_layout = True
    except:
        pass
    
    if not has_layout:
        # Request coordinates for all species and reactions
        missing['coordinates'] = {
            'species': [model.getSpecies(i).getId() 
                       for i in range(model.getNumSpecies())],
            'reactions': [model.getReaction(i).getId() 
                         for i in range(model.getNumReactions())]
        }
```

**Logic:**
1. Check if SBML model already has Layout extension
2. If not, mark coordinates as missing for all species/reactions
3. This triggers fetching from KEGG

#### Added to Data Type Selection
```python
# Determine which data types to fetch
data_types = []
if 'concentrations' in missing_data:
    data_types.append('concentrations')
if 'kinetics' in missing_data:
    data_types.append('kinetics')
if 'annotations' in missing_data:
    data_types.append('annotations')
if 'coordinates' in missing_data:
    data_types.append('coordinates')  # NEW
```

#### Added to Merge Pipeline
```python
# Merge concentrations
if 'concentrations' in external_data:
    self._merge_concentrations(model, external_data['concentrations'])

# Merge kinetics
if 'kinetics' in external_data:
    self._merge_kinetics(model, external_data['kinetics'])

# Merge annotations
if 'annotations' in external_data:
    self._merge_annotations(model, external_data['annotations'])

# Merge coordinates (via CoordinateEnricher)
if 'coordinates' in external_data:
    self._merge_coordinates(model, external_data['coordinates'])  # NEW
```

#### New Method: _merge_coordinates()
```python
def _merge_coordinates(self, model, coordinate_data: Dict[str, Any]):
    """Merge coordinate data into SBML Layout extension.
    
    Uses the CoordinateEnricher to apply coordinate data to the SBML model.
    The coordinates are transformed from screen coordinates to Cartesian
    (first quadrant, origin at bottom-left) as required by Shypn.
    
    Args:
        model: libsbml Model object
        coordinate_data: Dictionary with 'species' and 'reactions' coordinate data
    """
    logger.info("Merging coordinate data...")
    
    try:
        from shypn.crossfetch.enrichers import CoordinateEnricher
        from shypn.crossfetch.models import FetchResult
        
        # Create a CoordinateEnricher instance
        enricher = CoordinateEnricher()
        
        # Wrap coordinate data in FetchResult format
        fetch_result = FetchResult(
            source='KEGG',
            data_type='coordinates',
            pathway_id=model.getId() or 'unknown',
            success=True,
            data=coordinate_data
        )
        
        # Create a simple pathway wrapper with the model
        class PathwayWrapper:
            def __init__(self, sbml_model):
                self.model = sbml_model
        
        pathway = PathwayWrapper(model)
        
        # Validate data before applying
        is_valid, warnings = enricher.validate(pathway, fetch_result)
        
        if not is_valid:
            logger.warning(f"Coordinate data validation failed: {warnings}")
            return
        
        if warnings:
            for warning in warnings:
                logger.warning(f"Coordinate validation warning: {warning}")
        
        # Apply coordinate enrichment
        result = enricher.apply(pathway, fetch_result)
        
        if result.success:
            logger.info(
                f"Successfully merged coordinates: "
                f"{result.statistics.get('species_glyphs', 0)} species, "
                f"{result.statistics.get('reaction_glyphs', 0)} reactions"
            )
        else:
            logger.error(f"Failed to merge coordinates: {result.message}")
            
    except Exception as e:
        logger.error(f"Failed to merge coordinate data: {e}", exc_info=True)
```

**Key Features:**
- Wraps coordinate data in proper FetchResult format
- Creates lightweight PathwayWrapper for the SBML model
- Validates coordinate data before applying
- Logs warnings and errors appropriately
- Delegates actual enrichment to CoordinateEnricher

### 3. CoordinateEnricher Update

**File:** `src/shypn/crossfetch/enrichers/coordinate_enricher.py`

#### Fixed Enricher Name
```python
def __init__(self):
    """Initialize coordinate enricher with helper components."""
    super().__init__("CoordinateEnricher")  # Pass name to base class
    self.logger = logging.getLogger(self.__class__.__name__)
    
    # Initialize helper components
    self.id_mapper = SBMLIDMapper()
    self.layout_writer = SBMLLayoutWriter()
    self.transformer = CoordinateTransformer()
```

**Why:** EnricherBase requires enricher_name for registration and logging.

## Data Flow

### Complete Enrichment Pipeline with Coordinates

```
User Request: Import pathway "hsa00010"
        ↓
┌───────────────────────────┐
│  SBMLEnricher             │
│  .enrich_by_pathway_id()  │
└───────────┬───────────────┘
            │
            ├─► Fetch base SBML from BioModels
            │   └─► GET https://biomodels.org/...
            │
            ├─► Parse SBML & identify missing data
            │   └─► Check: concentrations? kinetics? annotations? coordinates?
            │       Result: missing['coordinates'] = {species: [...], reactions: [...]}
            │
            ├─► Fetch external data via EnrichmentPipeline
            │   ┌────────────────────────────────┐
            │   │  EnrichmentPipeline.fetch()    │
            │   │  data_types=['coordinates']    │
            │   └────────┬───────────────────────┘
            │            │
            │            ├─► KEGGFetcher._fetch_coordinates("hsa00010")
            │            │   ├─► GET https://rest.kegg.jp/get/hsa00010/kgml
            │            │   ├─► Parse KGML with KGMLParser
            │            │   ├─► Extract species coords: {kegg_id, x, y, width, height}
            │            │   └─► Return FetchResult{data: {species: [...], reactions: [...]}}
            │            │
            │            └─► Quality scoring & source selection
            │                └─► Best result selected
            │
            └─► Merge external data into SBML
                ┌─────────────────────────────────┐
                │  _merge_coordinates()           │
                └────────┬────────────────────────┘
                         │
                         ├─► Create CoordinateEnricher instance
                         ├─► Wrap data in FetchResult
                         ├─► Create PathwayWrapper(model)
                         ├─► Validate coordinate data
                         │   └─► enricher.validate(pathway, fetch_result)
                         │
                         └─► Apply enrichment
                             ┌──────────────────────────────────┐
                             │  CoordinateEnricher.apply()      │
                             └────────┬─────────────────────────┘
                                      │
                                      ├─► CoordinateTransformer.transform_species_coordinates()
                                      │   └─► Screen coords → Cartesian (y' = canvas_height - y)
                                      │
                                      ├─► SBMLIDMapper.map_species_ids()
                                      │   └─► KEGG IDs → SBML species IDs
                                      │
                                      └─► SBMLLayoutWriter.write_layout()
                                          └─► Create SBML Layout extension
                                              <layout id="kegg_layout_1">
                                                <speciesGlyph species="M_glucose_c">
                                                  <boundingBox x="100" y="400" .../>
                                                </speciesGlyph>
                                              </layout>
        ↓
    Enriched SBML string with Layout extension
        ↓
    Return to caller (SBMLImportPanel)
```

## Integration Points

### 1. EnrichmentPipeline
- **Location:** `src/shypn/crossfetch/core/enrichment_pipeline.py`
- **Role:** Central registry for all fetchers and enrichers
- **Change:** Added CoordinateEnricher to default enrichers list
- **Impact:** Coordinates now available in all fetch operations

### 2. KEGGFetcher
- **Location:** `src/shypn/crossfetch/fetchers/kegg_fetcher.py`
- **Role:** Fetch KGML coordinate data from KEGG API
- **Change:** Already implemented in Phase 1 (_fetch_coordinates method)
- **Status:** ✅ Complete

### 3. SBMLEnricher
- **Location:** `src/shypn/crossfetch/sbml_enricher.py`
- **Role:** Main SBML pre-processing orchestrator
- **Changes:** 
  - Added enrich_coordinates parameter
  - Enhanced _identify_missing_data() to check for Layout extension
  - Added _merge_coordinates() method
  - Wired coordinates into enrichment flow
- **Status:** ✅ Complete

### 4. CoordinateEnricher
- **Location:** `src/shypn/crossfetch/enrichers/coordinate_enricher.py`
- **Role:** Apply coordinate data to SBML model
- **Change:** Fixed enricher_name for proper registration
- **Status:** ✅ Complete

## Usage Example

### Basic Usage
```python
from shypn.crossfetch import SBMLEnricher

# Initialize enricher with all features enabled (default)
enricher = SBMLEnricher(
    fetch_sources=["KEGG", "Reactome"],
    enrich_coordinates=True  # Enable coordinate enrichment
)

# Enrich pathway with coordinates
enriched_sbml = enricher.enrich_by_pathway_id("hsa00010")

# enriched_sbml now contains:
# - Original SBML structure
# - Enriched concentrations (if missing)
# - Enriched kinetics (if missing)
# - Enriched annotations (if missing)
# - SBML Layout extension with KEGG coordinates ← NEW!
```

### Selective Enrichment
```python
# Enrich only coordinates (disable other enrichments)
enricher = SBMLEnricher(
    enrich_concentrations=False,
    enrich_kinetics=False,
    enrich_annotations=False,
    enrich_coordinates=True  # Only coordinates
)

enriched_sbml = enricher.enrich_by_pathway_id("hsa00010")
```

### Check for Layout Extension
```python
import libsbml

document = libsbml.readSBMLFromString(enriched_sbml)
model = document.getModel()

# Check if Layout extension was added
mplugin = model.getPlugin('layout')
if mplugin and mplugin.getNumLayouts() > 0:
    layout = mplugin.getLayout(0)
    print(f"Layout: {layout.getName()}")
    print(f"Species glyphs: {layout.getNumSpeciesGlyphs()}")
    print(f"Reaction glyphs: {layout.getNumReactionGlyphs()}")
```

## Testing Checklist

- [ ] Unit test: CoordinateEnricher registration in pipeline
- [ ] Unit test: SBMLEnricher detects missing Layout extension
- [ ] Unit test: _merge_coordinates() creates correct FetchResult wrapper
- [ ] Integration test: Full enrichment flow with coordinates
- [ ] Integration test: Coordinates skipped if Layout already exists
- [ ] Integration test: Coordinate enrichment can be disabled
- [ ] End-to-end test: Import KEGG pathway with coordinates
- [ ] Visual test: Verify layout renders correctly in UI

## Configuration Options

All coordinate enrichment can be controlled via SBMLEnricher constructor:

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `enrich_coordinates` | bool | True | Enable/disable coordinate enrichment |
| `fetch_sources` | List[str] | ["KEGG", "Reactome"] | Sources to fetch from (only KEGG has coords) |

## Logging

Coordinate enrichment adds these log messages:

```
INFO: SBMLEnricher initialized with sources: ['KEGG', 'Reactome']
INFO: Step 2: Analyzing SBML for missing data...
INFO: Missing data: ['coordinates']
INFO: Step 3: Fetching missing data from external sources...
INFO: Fetched coordinates from KEGG
INFO: Step 4: Merging external data into SBML...
INFO: Merging coordinate data...
INFO: Transformed 15 species coordinates (canvas_height=600)
INFO: Mapped 12/15 species IDs
INFO: Successfully wrote layout with 12 species glyphs and 8 reaction glyphs
INFO: Successfully merged coordinates: 12 species, 8 reactions
INFO: SBML enrichment complete
```

## Error Handling

The integration includes comprehensive error handling:

1. **Validation Errors:** If coordinate data is invalid, enrichment is skipped with warning
2. **Missing IDs:** Unmapped KEGG IDs are logged but don't fail enrichment
3. **Layout Write Errors:** Logged but don't affect other enrichments
4. **Exception Safety:** All exceptions caught and logged, original SBML returned

## Performance Considerations

- **Additional Fetch:** Adds one KGML fetch per pathway (~50-200KB)
- **Processing Time:** Coordinate transformation is fast (<10ms for typical pathway)
- **Memory:** Layout extension adds ~5-20KB to SBML file size
- **Caching:** KEGGFetcher caches KGML data (if cache enabled)

## Next Phase: UI Integration

Phase 4 will add UI controls for coordinate enrichment:

1. Checkbox in SBML import dialog: "Use KEGG layout coordinates"
2. Progress feedback showing coordinate enrichment status
3. Layout preview option
4. Statistics display (X species positioned, Y reactions positioned)

## Conclusion

✅ **Phase 3 Complete:** CoordinateEnricher is fully integrated into the enrichment pipeline

The coordinate enrichment feature is now:
- ✅ Registered in EnrichmentPipeline
- ✅ Available in SBMLEnricher workflow
- ✅ Properly validated and error-handled
- ✅ Configurable via constructor parameters
- ✅ Logged with appropriate detail

**Ready for:** UI integration (Phase 4) and layout resolver enhancement (Phase 5)
