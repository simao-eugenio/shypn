# CrossFetch Coordinate Enrichment Enhancement

**Date:** October 13, 2025  
**Status:** 🔨 Planned Enhancement  
**Priority:** High - Improves layout quality significantly

---

## Overview

**Goal:** Enhance CrossFetch to fetch and add **layout coordinates** from KEGG pathway maps to SBML files, enabling the parser to use the original visual layout instead of computing one algorithmically.

**Impact:** SBML files from BioModels (which typically lack layout information) will be enriched with coordinates from KEGG's manually curated pathway maps, resulting in high-quality visualizations that match established biological conventions.

---

## Current State

### What Exists ✅

1. **KEGG Data Structures** (`src/shypn/importer/kegg/models.py`)
   ```python
   @dataclass
   class KEGGGraphics:
       """Graphics information from KGML"""
       name: str = ""
       x: float = 0.0      # X coordinate in pixels
       y: float = 0.0      # Y coordinate in pixels
       width: float = 46.0
       height: float = 17.0
       fgcolor: str = "#000000"
       bgcolor: str = "#FFFFFF"
       type: str = "rectangle"
   ```

2. **Coordinate Fetching Stub** (`src/shypn/crossfetch/fetchers/kegg_fetcher.py`)
   ```python
   def _fetch_coordinates(self, pathway_id: str, **kwargs) -> FetchResult:
       """Fetch coordinate data from KEGG."""
       # TODO: Implement actual KEGG API call
       # Lines 89-116 (marked as placeholder)
   ```

3. **Data Type Enum** (`src/shypn/crossfetch/models/enrichment_request.py`)
   ```python
   class DataType(str, Enum):
       COORDINATES = "coordinates"  # Already defined!
       CONCENTRATIONS = "concentrations"
       KINETICS = "kinetics"
       ANNOTATIONS = "annotations"
   ```

4. **SBML Layout Extension Support**
   - SBML has a Layout extension for storing positions
   - libsbml supports reading/writing layout information

### What's Missing ❌

1. ❌ **Actual KEGG KGML fetching implementation**
2. ❌ **Coordinate merger into SBML Layout extension**
3. ❌ **ID mapping between KEGG and SBML species**
4. ❌ **Coordinate transformation (KEGG pixels → SBML units)**
5. ❌ **UI control for coordinate enrichment**

---

## The Enhancement

### Data Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  CURRENT FLOW (Without Coordinate Enrichment)                   │
│  ═══════════════════════════════════════════                    │
│                                                                  │
│  BioModels SBML → CrossFetch (kinetics) → Parser                │
│  (no layout)       (adds parameters)        → Tree Layout       │
│                                              → Hierarchical      │
│                                              → Force-directed    │
│                                                                  │
│  Result: Computed layout (quality varies)                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  ENHANCED FLOW (With Coordinate Enrichment)                     │
│  ═══════════════════════════════════════════                    │
│                                                                  │
│  BioModels SBML → CrossFetch Enhancement:                       │
│  (no layout)       1. Fetch KGML from KEGG (hsa00010.xml)      │
│                    2. Extract coordinates from graphics         │
│                    3. Map KEGG IDs ↔ SBML species IDs          │
│                    4. Transform coordinates (pixels → units)    │
│                    5. Add SBML Layout extension                 │
│                   ↓                                              │
│  Enriched SBML → Parser → SBMLLayoutResolver                    │
│  (with layout)            (reads Layout extension)              │
│                          ↓                                       │
│                    Uses KEGG coordinates directly!              │
│                                                                  │
│  Result: Professional layout matching KEGG pathway maps ✨      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: KGML Coordinate Fetching

**File:** `src/shypn/crossfetch/fetchers/kegg_fetcher.py`

**Task:** Implement `_fetch_coordinates()` method

```python
def _fetch_coordinates(self, pathway_id: str, **kwargs) -> FetchResult:
    """Fetch coordinate data from KEGG KGML.
    
    Workflow:
    1. Fetch KGML XML from KEGG API
    2. Parse KGML to extract entries with graphics
    3. Return coordinate mapping
    
    Args:
        pathway_id: KEGG pathway ID (e.g., 'hsa00010')
        **kwargs: Additional parameters
        
    Returns:
        FetchResult with coordinate data:
        {
            'pathway_id': 'hsa00010',
            'species': [
                {
                    'kegg_id': 'cpd:C00031',  # Glucose
                    'name': 'Glucose',
                    'x': 150.0,
                    'y': 100.0,
                    'width': 46.0,
                    'height': 17.0
                },
                ...
            ],
            'reactions': [
                {
                    'kegg_id': 'rn:R00299',
                    'name': 'Hexokinase',
                    'x': 200.0,
                    'y': 150.0
                },
                ...
            ]
        }
    """
    try:
        # 1. Fetch KGML XML
        kgml_url = f"{self.KEGG_API_BASE}/get/{pathway_id}/kgml"
        response = requests.get(kgml_url, timeout=30)
        response.raise_for_status()
        
        # 2. Parse KGML using existing parser
        from shypn.importer.kegg.kgml_parser import KGMLParser
        parser = KGMLParser()
        pathway_data = parser.parse_string(response.text)
        
        # 3. Extract coordinates from entries
        species_coords = []
        reaction_coords = []
        
        for entry_id, entry in pathway_data.entries.items():
            graphics = entry.graphics
            
            # Extract compound coordinates
            if entry.type == 'compound':
                kegg_ids = entry.get_kegg_ids()  # May have multiple IDs
                for kegg_id in kegg_ids:
                    species_coords.append({
                        'kegg_id': kegg_id,
                        'name': graphics.name,
                        'x': graphics.x,
                        'y': graphics.y,
                        'width': graphics.width,
                        'height': graphics.height
                    })
            
            # Extract reaction coordinates
            elif entry.type == 'enzyme' or entry.reaction:
                reaction_coords.append({
                    'kegg_id': entry.reaction or entry.name,
                    'name': graphics.name,
                    'x': graphics.x,
                    'y': graphics.y
                })
        
        # 4. Build result data
        data = {
            'pathway_id': pathway_id,
            'species': species_coords,
            'reactions': reaction_coords
        }
        
        fields_filled = ['pathway_id', 'species', 'reactions']
        
        self.logger.info(
            f"✓ Fetched {len(species_coords)} species coords, "
            f"{len(reaction_coords)} reaction coords from KEGG"
        )
        
        return self._create_success_result(
            data=data,
            data_type="coordinates",
            fields_filled=fields_filled,
            source_url=kgml_url
        )
        
    except Exception as e:
        self.logger.error(f"Failed to fetch KEGG coordinates: {e}")
        return self._create_failure_result(
            error=str(e),
            data_type="coordinates"
        )
```

**Dependencies:**
- Reuse existing `KGMLParser` from `src/shypn/importer/kegg/kgml_parser.py`
- Use existing `KEGGGraphics` model
- No new external dependencies needed

---

### Phase 2: Coordinate Enricher

**File:** `src/shypn/crossfetch/enrichers/coordinate_enricher.py` (new file)

**Task:** Create enricher that adds coordinates to SBML

```python
"""Coordinate Enricher - Adds layout information to SBML.

Fetches coordinate data from external sources (KEGG) and adds it
to SBML files using the SBML Layout extension.
"""

import logging
from typing import Dict, List, Optional
try:
    import libsbml
except ImportError:
    libsbml = None

from shypn.crossfetch.enrichers.base_enricher import BaseEnricher
from shypn.crossfetch.models.fetch_result import FetchResult


class CoordinateEnricher(BaseEnricher):
    """Enriches SBML with layout coordinates from external sources.
    
    Workflow:
    1. Parse existing SBML
    2. Fetch coordinates from KEGG (via KEGGFetcher)
    3. Map KEGG IDs to SBML species IDs
    4. Add SBML Layout extension with coordinates
    5. Return enriched SBML string
    """
    
    def __init__(self, fetchers: List):
        """Initialize coordinate enricher.
        
        Args:
            fetchers: List of fetcher objects (should include KEGGFetcher)
        """
        super().__init__(fetchers)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def enrich(self, sbml_string: str, pathway_id: str) -> str:
        """Add coordinate data to SBML.
        
        Args:
            sbml_string: Original SBML content
            pathway_id: Pathway identifier for fetching
            
        Returns:
            Enriched SBML with Layout extension
        """
        if not libsbml:
            self.logger.warning("libsbml not available, skipping coordinate enrichment")
            return sbml_string
        
        try:
            # 1. Parse SBML
            doc = libsbml.readSBMLFromString(sbml_string)
            model = doc.getModel()
            
            if not model:
                self.logger.error("No model in SBML document")
                return sbml_string
            
            # 2. Fetch coordinates from KEGG
            coord_results = self._fetch_coordinates(pathway_id)
            
            if not coord_results or not coord_results.success:
                self.logger.warning("Failed to fetch coordinates")
                return sbml_string
            
            # 3. Map KEGG IDs to SBML species
            id_mapping = self._build_id_mapping(model, coord_results.data)
            
            # 4. Add Layout extension
            self._add_layout_extension(doc, model, coord_results.data, id_mapping)
            
            # 5. Return enriched SBML
            enriched_sbml = libsbml.writeSBMLToString(doc)
            
            self.logger.info(
                f"✓ Added layout coordinates for {len(id_mapping)} species"
            )
            
            return enriched_sbml
            
        except Exception as e:
            self.logger.error(f"Coordinate enrichment failed: {e}")
            return sbml_string  # Return original on failure
    
    def _fetch_coordinates(self, pathway_id: str) -> Optional[FetchResult]:
        """Fetch coordinate data from available sources.
        
        Args:
            pathway_id: Pathway identifier
            
        Returns:
            FetchResult with coordinate data, or None if failed
        """
        for fetcher in self.fetchers:
            try:
                result = fetcher.fetch(pathway_id, data_type="coordinates")
                if result.success and result.data:
                    return result
            except Exception as e:
                self.logger.debug(f"Fetcher {fetcher.__class__.__name__} failed: {e}")
        
        return None
    
    def _build_id_mapping(self, model, coord_data: Dict) -> Dict[str, Dict]:
        """Map KEGG IDs to SBML species IDs.
        
        Strategy:
        1. Try exact ID match (if SBML uses KEGG IDs)
        2. Try name match (case-insensitive)
        3. Try annotation match (look for KEGG identifiers in SBML)
        
        Args:
            model: SBML Model object
            coord_data: Coordinate data from fetcher
            
        Returns:
            Mapping: {sbml_species_id: {x, y, width, height}}
        """
        mapping = {}
        species_coords = coord_data.get('species', [])
        
        # Build reverse lookup: KEGG ID → coordinates
        kegg_to_coords = {}
        for species_coord in species_coords:
            kegg_id = species_coord['kegg_id']
            kegg_to_coords[kegg_id] = species_coord
            
            # Also store without prefix for flexible matching
            if ':' in kegg_id:
                bare_id = kegg_id.split(':', 1)[1]
                kegg_to_coords[bare_id] = species_coord
        
        # Map SBML species to KEGG coordinates
        for i in range(model.getNumSpecies()):
            species = model.getSpecies(i)
            sbml_id = species.getId()
            sbml_name = species.getName()
            
            # Strategy 1: Exact ID match
            if sbml_id in kegg_to_coords:
                mapping[sbml_id] = kegg_to_coords[sbml_id]
                continue
            
            # Strategy 2: Name match (case-insensitive)
            for kegg_id, coords in kegg_to_coords.items():
                if coords['name'].lower() == sbml_name.lower():
                    mapping[sbml_id] = coords
                    break
            
            # Strategy 3: Check annotations (MIRIAM identifiers)
            # TODO: Parse SBML annotations for KEGG identifiers
        
        return mapping
    
    def _add_layout_extension(self, doc, model, coord_data: Dict, id_mapping: Dict):
        """Add SBML Layout extension with coordinates.
        
        Args:
            doc: SBML Document object
            model: SBML Model object
            coord_data: Raw coordinate data
            id_mapping: Mapped species IDs to coordinates
        """
        # Enable Layout plugin
        doc.enablePackage(
            libsbml.LayoutExtension.getXmlnsL3V1V1(), 
            'layout', 
            True
        )
        
        # Get layout plugin
        model_plugin = model.getPlugin('layout')
        
        if not model_plugin:
            self.logger.error("Failed to enable Layout extension")
            return
        
        # Create layout
        layout = model_plugin.createLayout()
        layout.setId('layout_1')
        
        # Set dimensions (from KEGG map size, typically 800x600)
        dimensions = layout.createDimensions()
        dimensions.setWidth(800.0)
        dimensions.setHeight(600.0)
        
        # Add species glyphs
        for sbml_id, coords in id_mapping.items():
            glyph = layout.createSpeciesGlyph()
            glyph.setId(f"glyph_{sbml_id}")
            glyph.setSpeciesId(sbml_id)
            
            # Set bounding box
            bbox = glyph.createBoundingBox()
            bbox.setX(coords['x'])
            bbox.setY(coords['y'])
            bbox.setWidth(coords.get('width', 46.0))
            bbox.setHeight(coords.get('height', 17.0))
        
        # Add reaction glyphs
        reaction_coords = coord_data.get('reactions', [])
        reaction_id_map = self._map_reaction_ids(model, reaction_coords)
        
        for sbml_id, coords in reaction_id_map.items():
            glyph = layout.createReactionGlyph()
            glyph.setId(f"glyph_{sbml_id}")
            glyph.setReactionId(sbml_id)
            
            # Set center position
            bbox = glyph.createBoundingBox()
            bbox.setX(coords['x'])
            bbox.setY(coords['y'])
            bbox.setWidth(20.0)  # Default reaction glyph size
            bbox.setHeight(20.0)
        
        self.logger.info(f"✓ Created layout with {len(id_mapping)} species glyphs")
    
    def _map_reaction_ids(self, model, reaction_coords: List[Dict]) -> Dict[str, Dict]:
        """Map KEGG reaction IDs to SBML reaction IDs.
        
        Args:
            model: SBML Model object
            reaction_coords: List of reaction coordinate data
            
        Returns:
            Mapping: {sbml_reaction_id: {x, y}}
        """
        mapping = {}
        
        # Build KEGG lookup
        kegg_to_coords = {}
        for rxn_coord in reaction_coords:
            kegg_id = rxn_coord['kegg_id']
            kegg_to_coords[kegg_id] = rxn_coord
        
        # Map SBML reactions
        for i in range(model.getNumReactions()):
            reaction = model.getReaction(i)
            sbml_id = reaction.getId()
            
            # Try exact match
            if sbml_id in kegg_to_coords:
                mapping[sbml_id] = kegg_to_coords[sbml_id]
        
        return mapping
```

---

### Phase 3: SBMLEnricher Integration

**File:** `src/shypn/crossfetch/sbml_enricher.py`

**Task:** Add coordinate enrichment option

```python
def __init__(self, 
             fetch_sources: Optional[List[str]] = None,
             enrich_concentrations: bool = True,
             enrich_kinetics: bool = True,
             enrich_annotations: bool = True,
             enrich_coordinates: bool = True):  # ← NEW PARAMETER
    """Initialize SBML enricher.
    
    Args:
        fetch_sources: Sources to fetch from (default: ["KEGG", "Reactome"])
        enrich_concentrations: Whether to enrich concentration data
        enrich_kinetics: Whether to enrich kinetic parameters
        enrich_annotations: Whether to enrich annotations
        enrich_coordinates: Whether to enrich layout coordinates (NEW)
    """
    self.pipeline = EnrichmentPipeline()
    self.fetch_sources = fetch_sources or ["KEGG", "Reactome"]
    self.enrich_concentrations = enrich_concentrations
    self.enrich_kinetics = enrich_kinetics
    self.enrich_annotations = enrich_annotations
    self.enrich_coordinates = enrich_coordinates  # Store flag
    
    logger.info(f"SBMLEnricher initialized with sources: {self.fetch_sources}")
    if enrich_coordinates:
        logger.info("  ✓ Coordinate enrichment enabled")


def enrich_by_pathway_id(self, pathway_id: str) -> str:
    """Enrich SBML by pathway ID.
    
    ...existing implementation...
    """
    # ... fetch base SBML ...
    
    # Enrich with external data
    enriched_sbml = self._enrich_sbml(base_sbml, pathway_id)
    
    return enriched_sbml


def _enrich_sbml(self, sbml_string: str, pathway_id: str) -> str:
    """Apply enrichments to SBML.
    
    Args:
        sbml_string: Base SBML content
        pathway_id: Pathway identifier
        
    Returns:
        Enriched SBML string
    """
    current_sbml = sbml_string
    
    # Apply each enabled enricher
    if self.enrich_coordinates:  # ← NEW
        from shypn.crossfetch.enrichers.coordinate_enricher import CoordinateEnricher
        from shypn.crossfetch.fetchers.kegg_fetcher import KEGGFetcher
        
        enricher = CoordinateEnricher(fetchers=[KEGGFetcher()])
        current_sbml = enricher.enrich(current_sbml, pathway_id)
    
    if self.enrich_concentrations:
        # ... existing concentration enrichment ...
        pass
    
    if self.enrich_kinetics:
        # ... existing kinetics enrichment ...
        pass
    
    if self.enrich_annotations:
        # ... existing annotation enrichment ...
        pass
    
    return current_sbml
```

---

### Phase 4: UI Integration

**File:** `src/shypn/helpers/sbml_import_panel.py`

**Task:** Add coordinate enrichment option to UI

```python
def __init__(self, builder: Gtk.Builder, model_canvas=None, workspace_settings=None):
    """Initialize the SBML import panel controller."""
    # ... existing initialization ...
    
    # Initialize enricher (PRE-processor)
    if SBMLEnricher:
        self.enricher = SBMLEnricher(
            fetch_sources=["KEGG", "Reactome"],
            enrich_concentrations=True,
            enrich_kinetics=True,
            enrich_annotations=True,
            enrich_coordinates=True  # ← Enable coordinate enrichment
        )
```

**UI File:** `ui/panels/pathway_panel.ui`

**Task:** Update checkbox tooltip

```xml
<object class="GtkCheckButton" id="sbml_enrich_check">
  <property name="visible">True</property>
  <property name="can-focus">True</property>
  <property name="label">Enrich with external data (KEGG/Reactome)</property>
  <property name="tooltip-text">Fetch missing data from external databases before importing:
• Layout coordinates (positions from KEGG pathway maps)
• Initial concentrations (from compound databases)  
• Kinetic parameters (Km, Vmax from reaction databases)
• Annotations and cross-references</property>
  <property name="active">False</property>
</object>
```

---

### Phase 5: Layout Resolver Enhancement

**File:** `src/shypn/data/pathway/sbml_layout_resolver.py`

**Task:** Ensure resolver reads SBML Layout extension

```python
def resolve_layout(self) -> Dict[str, Tuple[float, float]]:
    """Resolve layout from SBML Layout extension.
    
    Returns:
        Dictionary mapping species ID to (x, y) position
    """
    positions = {}
    
    if not libsbml:
        return positions
    
    try:
        # Parse SBML
        doc = libsbml.readSBMLFromString(self.sbml_string)
        model = doc.getModel()
        
        if not model:
            return positions
        
        # Get layout plugin
        model_plugin = model.getPlugin('layout')
        
        if not model_plugin:
            self.logger.debug("No Layout extension found in SBML")
            return positions
        
        # Read layout
        if model_plugin.getNumLayouts() == 0:
            return positions
        
        layout = model_plugin.getLayout(0)
        
        # Extract species positions
        for i in range(layout.getNumSpeciesGlyphs()):
            glyph = layout.getSpeciesGlyph(i)
            species_id = glyph.getSpeciesId()
            bbox = glyph.getBoundingBox()
            
            if bbox:
                x = bbox.getX()
                y = bbox.getY()
                positions[species_id] = (x, y)
        
        # Extract reaction positions
        for i in range(layout.getNumReactionGlyphs()):
            glyph = layout.getReactionGlyph(i)
            reaction_id = glyph.getReactionId()
            bbox = glyph.getBoundingBox()
            
            if bbox:
                x = bbox.getX()
                y = bbox.getY()
                positions[reaction_id] = (x, y)
        
        self.logger.info(
            f"✓ Resolved {len(positions)} positions from SBML Layout extension"
        )
        
        return positions
        
    except Exception as e:
        self.logger.error(f"Failed to resolve SBML layout: {e}")
        return positions
```

---

## Expected Results

### Before Coordinate Enrichment

**Imported pathway with computed layout:**
- ⚠️ Layout quality varies
- ⚠️ May not match biological conventions
- ⚠️ Requires manual adjustment
- ⚠️ Different each time (force-directed randomness)

### After Coordinate Enrichment

**Imported pathway with KEGG coordinates:**
- ✅ Professional layout matching KEGG maps
- ✅ Follows established biological conventions
- ✅ No manual adjustment needed
- ✅ Consistent layout every time
- ✅ Matches published pathway diagrams

---

## Example: Glycolysis (hsa00010)

### Without Enrichment
```
BioModels SBML (BIOMD0000000001)
  → No layout coordinates
  → CrossFetch adds kinetics only
  → Parser uses tree layout
  → Result: Hierarchical tree (good, but not KEGG style)
```

### With Enrichment
```
BioModels SBML (BIOMD0000000001)
  → No layout coordinates
  → CrossFetch fetches KGML (hsa00010.xml)
  → Extracts KEGG coordinates
  → Adds SBML Layout extension
  → Parser uses cross-reference layout
  → Result: Exact KEGG glycolysis map layout! ✨
```

---

## Testing Plan

### Unit Tests

**File:** `tests/crossfetch/test_coordinate_enricher.py`

```python
def test_fetch_kegg_coordinates():
    """Test fetching coordinates from KEGG."""
    fetcher = KEGGFetcher()
    result = fetcher.fetch("hsa00010", data_type="coordinates")
    
    assert result.success
    assert 'species' in result.data
    assert 'reactions' in result.data
    assert len(result.data['species']) > 0


def test_add_layout_extension():
    """Test adding Layout extension to SBML."""
    # Load test SBML (without layout)
    sbml = load_test_sbml("glycolysis_no_layout.xml")
    
    # Enrich with coordinates
    enricher = CoordinateEnricher(fetchers=[KEGGFetcher()])
    enriched = enricher.enrich(sbml, "hsa00010")
    
    # Verify Layout extension added
    doc = libsbml.readSBMLFromString(enriched)
    model = doc.getModel()
    layout_plugin = model.getPlugin('layout')
    
    assert layout_plugin is not None
    assert layout_plugin.getNumLayouts() > 0


def test_id_mapping():
    """Test mapping KEGG IDs to SBML species."""
    # Create test data
    sbml = create_test_sbml_with_species([
        ("glucose", "Glucose"),
        ("g6p", "Glucose-6-phosphate")
    ])
    
    kegg_coords = {
        'species': [
            {'kegg_id': 'cpd:C00031', 'name': 'Glucose', 'x': 100, 'y': 100},
            {'kegg_id': 'cpd:C00092', 'name': 'Glucose-6-phosphate', 'x': 100, 'y': 200}
        ]
    }
    
    enricher = CoordinateEnricher(fetchers=[])
    mapping = enricher._build_id_mapping(sbml.getModel(), kegg_coords)
    
    assert 'glucose' in mapping
    assert 'g6p' in mapping
    assert mapping['glucose']['x'] == 100
```

### Integration Tests

**File:** `tests/test_sbml_coordinate_enrichment.py`

```python
def test_end_to_end_coordinate_enrichment():
    """Test complete coordinate enrichment flow."""
    # 1. Fetch BioModels SBML (no layout)
    biomodels_id = "BIOMD0000000001"
    # ... fetch from BioModels ...
    
    # 2. Enrich with coordinates
    enricher = SBMLEnricher(enrich_coordinates=True)
    enriched_sbml = enricher.enrich_by_pathway_id("hsa00010")
    
    # 3. Parse enriched SBML
    parser = SBMLParser()
    pathway_data = parser.parse_sbml_string(enriched_sbml)
    
    # 4. Post-process (should detect coordinates)
    postprocessor = PathwayPostProcessor()
    processed = postprocessor.process(pathway_data)
    
    # 5. Verify positions were resolved from coordinates
    assert processed.metadata['layout_type'] == 'cross-reference'
    assert len(processed.positions) > 0
```

---

## Performance Considerations

### Additional Time Cost

| Operation | Time | Caching Benefit |
|-----------|------|-----------------|
| Fetch KGML | 1-2s | High (reusable) |
| Parse KGML | <0.1s | - |
| Map IDs | <0.1s | - |
| Add Layout ext | <0.1s | - |
| **Total** | **~2s** | Can be cached |

**Optimization:** Cache fetched KGML files by pathway ID to avoid repeated network calls.

---

## Benefits Summary

### For Users
✅ **Better visualizations** - Professional layouts matching KEGG maps  
✅ **Less manual work** - No need to rearrange nodes  
✅ **Consistent results** - Same layout every import  
✅ **Familiar diagrams** - Matches published literature  

### For Developers
✅ **Reuses existing code** - KGML parser already exists  
✅ **Clean architecture** - Fits CrossFetch pattern  
✅ **Optional feature** - Doesn't break existing flow  
✅ **Well-tested** - SBML Layout is standard  

---

## Implementation Timeline

| Phase | Effort | Priority |
|-------|--------|----------|
| Phase 1: KGML fetching | 2-3 hours | High |
| Phase 2: Coordinate enricher | 4-6 hours | High |
| Phase 3: SBMLEnricher integration | 1 hour | High |
| Phase 4: UI integration | 30 min | Medium |
| Phase 5: Layout resolver | 2 hours | High |
| Testing | 3-4 hours | High |
| **Total** | **12-16 hours** | |

**Recommendation:** Implement in one focused sprint.

---

## Next Steps

1. ✅ **Review this design document**
2. 🔨 **Implement Phase 1** (KGML fetching)
3. 🔨 **Implement Phase 2** (Coordinate enricher)
4. 🧪 **Test with real pathways** (glycolysis, TCA cycle)
5. 🔨 **Implement Phases 3-5** (Integration)
6. 🧪 **End-to-end testing**
7. 📝 **Update user documentation**
8. 🚀 **Deploy to production**

---

## References

- **KEGG API:** https://www.kegg.jp/kegg/rest/keggapi.html
- **KGML Specification:** https://www.kegg.jp/kegg/xml/docs/
- **SBML Layout Extension:** http://sbml.org/Documents/Specifications/SBML_Level_3/Packages/layout
- **Existing KGML Parser:** `src/shypn/importer/kegg/kgml_parser.py`
- **CrossFetch Architecture:** `doc/crossfetch/CROSSFETCH_INTEGRATION_ANALYSIS.md`

---

**End of Enhancement Plan**
