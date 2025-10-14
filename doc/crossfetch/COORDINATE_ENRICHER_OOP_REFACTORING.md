# Coordinate Enricher OOP Refactoring

**Date:** October 13, 2025  
**Status:** ✅ Complete

## Overview

Refactored the coordinate enrichment implementation to follow proper OOP architecture with separation of concerns and minimal code in loader/fetcher modules.

## Architecture

### Before (Monolithic)
- Single `coordinate_enricher.py` with all logic (330 lines)
- Mixed responsibilities: ID mapping, coordinate transformation, SBML writing
- Didn't properly inherit from `EnricherBase`
- Used `enrich()` method instead of `apply()`

### After (Modular OOP)
- **4 separate modules** with clear responsibilities
- Proper inheritance from `EnricherBase` abstract class
- Follows existing pattern used by other enrichers
- Minimal, focused code in each module

## New Module Structure

### 1. `coordinate_enricher.py` (281 lines)
**Role:** Main enricher orchestrator

**Responsibilities:**
- Inherits from `EnricherBase`
- Implements required abstract methods: `apply()`, `validate()`, `can_enrich()`
- Orchestrates the enrichment workflow
- Uses helper modules for specific tasks

**Key Methods:**
```python
def can_enrich(data_type: str) -> bool
def apply(pathway, fetch_result, **options) -> EnrichmentResult
def validate(pathway, fetch_result) -> tuple[bool, List[str]]
def _get_model_from_pathway(pathway) -> Model
```

### 2. `coordinate_transformer.py` (213 lines)
**Role:** Coordinate system transformation

**Responsibilities:**
- Transform between screen and Cartesian coordinate systems
- Handle KEGG's top-left origin → Shypn's bottom-left origin (first quadrant)
- Calculate canvas dimensions

**Key Insight:**
KEGG uses **screen coordinates** (0,0 at top-left, Y increases downward)  
Shypn uses **Cartesian coordinates** (0,0 at bottom-left, Y increases upward)

**Transformation:**
```
x_cartesian = x_screen
y_cartesian = canvas_height - y_screen - element_height
```

**Methods:**
```python
def screen_to_cartesian(coords, canvas_height) -> Dict
def cartesian_to_screen(coords, canvas_height) -> Dict
def transform_species_coordinates(species_data, canvas_height) -> List
def transform_reaction_coordinates(reaction_data, canvas_height) -> List
def calculate_canvas_height(data) -> float
```

### 3. `sbml_id_mapper.py` (155 lines)
**Role:** Cross-database ID mapping

**Responsibilities:**
- Map KEGG IDs to SBML species/reaction IDs
- Flexible matching strategies (exact, name-based, partial, annotation-based)
- Handle ID prefixes (cpd:C00031 → C00031)

**Matching Strategies:**
1. **Exact match:** Direct ID correspondence
2. **Name match:** Case-insensitive name matching
3. **Partial match:** Substring/contains matching
4. **Annotation match:** (Future) MIRIAM URIs in SBML annotations

**Methods:**
```python
def map_species_ids(model, external_data) -> Dict[str, Dict]
def map_reaction_ids(model, external_data) -> Dict[str, Dict]
```

### 4. `sbml_layout_writer.py` (248 lines)
**Role:** SBML Layout extension writer

**Responsibilities:**
- Write coordinate data to SBML Layout package structures
- Create layout elements: Layout, SpeciesGlyph, ReactionGlyph
- Handle bounding boxes and dimensions
- Conform to SBML Layout specification

**Key Components:**
- Layout definition with canvas dimensions
- Species glyphs with bounding boxes
- Reaction glyphs with center points
- (Future) Species reference glyphs for reaction curves

**Methods:**
```python
def write_layout(model, species_coords, reaction_coords, ...) -> bool
def _calculate_canvas_dimensions(species_coords, reaction_coords) -> Dict
def _add_species_glyphs(layout, model, species_coords) -> int
def _add_reaction_glyphs(layout, model, reaction_coords) -> int
```

## Design Principles Applied

### 1. Single Responsibility Principle
Each module has ONE clear responsibility:
- **CoordinateEnricher:** Orchestration
- **CoordinateTransformer:** Coordinate math
- **SBMLIDMapper:** ID cross-referencing
- **SBMLLayoutWriter:** SBML Layout XML generation

### 2. Dependency Inversion Principle
- `CoordinateEnricher` depends on abstractions (helper classes)
- Helper classes are independent and testable
- Can mock helpers for unit testing

### 3. Open/Closed Principle
- Enricher is open for extension (new coordinate sources)
- Closed for modification (core logic stable)
- Easy to add new ID matching strategies
- Easy to add new coordinate transformations

### 4. Separation of Concerns
- **Business logic** (enrichment workflow) in enricher
- **Math logic** (coordinate transformation) in transformer
- **Mapping logic** (ID matching) in mapper
- **XML generation** (SBML writing) in writer

## Integration with Existing Architecture

### Follows EnricherBase Pattern
```python
class EnricherBase(ABC):
    @abstractmethod
    def can_enrich(self, data_type: str) -> bool
    
    @abstractmethod
    def apply(self, pathway, fetch_result, **options) -> EnrichmentResult
    
    @abstractmethod
    def validate(self, pathway, fetch_result) -> tuple[bool, List[str]]
```

### Same Pattern as Other Enrichers
- `ConcentrationEnricher`
- `KineticsEnricher`
- `AnnotationEnricher`
- `InteractionEnricher`

All inherit from `EnricherBase` and implement the same interface.

## Coordinate System: Critical Detail

**User Requirement:** "we work on cartesian metric coordinates, first quadrant (0,0) on far left down"

This means:
- Origin (0,0) at **bottom-left corner**
- X-axis increases **rightward** (standard)
- Y-axis increases **upward** (mathematical convention)
- **First quadrant only** (all positive coordinates)

### Why This Matters
KEGG pathways use screen/image coordinates:
- Origin at top-left
- Y increases downward (opposite of Cartesian)

**Without transformation:** Pathways would render upside-down!

**With transformation:** Coordinates are flipped vertically to match Shypn's Cartesian system.

## Benefits of Refactoring

### 1. Maintainability
- Each module is <300 lines
- Clear separation makes code easy to understand
- Changes to one concern don't affect others

### 2. Testability
- Each module can be unit tested independently
- Mock dependencies for isolated testing
- Test coordinate transformation without SBML
- Test ID mapping without coordinates

### 3. Reusability
- `CoordinateTransformer` can be used by other importers
- `SBMLIDMapper` can map IDs from any external source
- `SBMLLayoutWriter` can write any layout data

### 4. Extensibility
- Add new coordinate sources (Reactome, BioPAX)
- Add new ID matching strategies
- Add new coordinate transformations (scaling, rotation)
- Add 3D coordinate support

### 5. Minimal Code in Loaders
As requested: "minimise code on loaders"
- `KEGGFetcher` only fetches KGML (stays focused)
- All enrichment logic in dedicated enricher modules
- Fetchers remain thin and simple

## Files Created/Modified

### Created (4 new modules)
1. `/src/shypn/crossfetch/enrichers/coordinate_enricher.py` - Main enricher
2. `/src/shypn/crossfetch/enrichers/coordinate_transformer.py` - Coordinate math
3. `/src/shypn/crossfetch/enrichers/sbml_id_mapper.py` - ID mapping
4. `/src/shypn/crossfetch/enrichers/sbml_layout_writer.py` - SBML Layout XML

### Modified
1. `/src/shypn/crossfetch/enrichers/__init__.py` - Added exports

### Already Modified (from previous work)
1. `/src/shypn/crossfetch/fetchers/kegg_fetcher.py` - Implements `_fetch_coordinates()`

## Next Steps

### Phase 3: SBMLEnricher Integration
Integrate `CoordinateEnricher` into main enrichment pipeline:
1. Register enricher in `SBMLEnricher` class
2. Add to enrichment workflow
3. Wire up with `KEGGFetcher` coordinate fetching

### Phase 4: UI Updates
1. Add checkbox in SBML import dialog: "Use KEGG layout coordinates"
2. Show coordinate statistics in progress feedback
3. Add layout preview option

### Phase 5: Layout Resolver Enhancement
Update `layout/resolvers.py`:
1. Check for SBML Layout extension first
2. Fall back to algorithmic layout if no coordinates
3. Hybrid mode: Use KEGG coords + algorithm for missing species

## Testing Checklist

- [ ] Unit test `CoordinateTransformer.screen_to_cartesian()`
- [ ] Unit test `CoordinateTransformer.cartesian_to_screen()`
- [ ] Unit test `SBMLIDMapper` matching strategies
- [ ] Unit test `SBMLLayoutWriter` with mock SBML model
- [ ] Integration test: KGML → Enriched SBML with Layout
- [ ] End-to-end test: Import pathway with coordinates
- [ ] Visual test: Verify layout renders correctly (not upside-down!)

## Documentation

This refactoring maintains the design documented in:
- `doc/crossfetch/COORDINATE_ENRICHMENT_ENHANCEMENT.md` (original plan)
- `doc/crossfetch/CROSSFETCH_INTEGRATION_ANALYSIS.md` (architecture)

## Conclusion

✅ **OOP Architecture:** Proper inheritance from `EnricherBase`  
✅ **Separation of Concerns:** 4 focused modules with clear responsibilities  
✅ **Minimal Loader Code:** Enrichment logic separated from fetchers  
✅ **Cartesian Coordinates:** Proper transformation from KEGG screen coords  
✅ **Extensible Design:** Easy to add new sources and strategies  
✅ **Testable:** Each module can be tested independently

The coordinate enrichment feature is now architecturally sound and ready for integration into the main enrichment pipeline.
