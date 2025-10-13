# SBML Cross-Reference Layout Enhancement Plan

## Problem Statement
SBML files don't contain graphical positioning data, resulting in circular force-directed layouts that differ from literature diagrams. However, SBML files contain cross-references to other databases (KEGG, Reactome, BioCyc) that DO have graphical layouts.

## Solution Strategy
Use cross-reference IDs from SBML annotations to fetch pre-positioned layouts from graphical pathway databases, then map those positions back to SBML species/reactions.

---

## Phase 1: Cross-Reference Extraction (DONE ✓)

### Current Implementation
- ✅ SBML parser extracts KEGG compound IDs (`kegg_id`)
- ✅ SBML parser extracts ChEBI IDs (`chebi_id`)
- ✅ Species dataclass stores these IDs

### Example from BioModels
```xml
<species id="s1" name="Glucose">
  <annotation>
    <rdf:RDF>
      <rdf:Description rdf:about="#s1">
        <bqbiol:is>
          <rdf:Bag>
            <rdf:li rdf:resource="https://identifiers.org/kegg.compound/C00031"/>
            <rdf:li rdf:resource="https://identifiers.org/chebi/CHEBI:17234"/>
          </rdf:Bag>
        </bqbiol:is>
      </rdf:Description>
    </rdf:RDF>
  </annotation>
</species>
```

---

## Phase 2: Pathway-Level Mapping Strategy

### Approach A: Direct KEGG Pathway Mapping (RECOMMENDED)
**Strategy**: Find the KEGG pathway that best matches the SBML model

#### Step 1: Extract Model-Level Cross-References
Look for pathway annotations in SBML `<model>` element:
```xml
<model id="model1" name="Glycolysis">
  <annotation>
    <rdf:li rdf:resource="https://identifiers.org/kegg.pathway/hsa00010"/>
    <rdf:li rdf:resource="https://identifiers.org/reactome/R-HSA-70171"/>
  </annotation>
</model>
```

**Extraction points**:
- Model annotations (pathway-level IDs)
- Publication DOIs (cross-reference to papers)
- BioModels metadata (often includes pathway names)

#### Step 2: Fetch KEGG KGML for Matched Pathway
```python
# If SBML has kegg.pathway/hsa00010
kegg_pathway_id = "hsa00010"
kgml_data = fetch_kegg_kgml(kegg_pathway_id)
kegg_pathway = parse_kgml(kgml_data)
```

#### Step 3: Map SBML Species → KEGG Compounds
```python
species_to_kegg_entry = {}
for species in sbml_species:
    kegg_id = species.kegg_id  # e.g., "C00031"
    # Find in KEGG pathway
    kegg_entry = kegg_pathway.find_compound(kegg_id)
    if kegg_entry:
        species_to_kegg_entry[species.id] = kegg_entry
        # Use kegg_entry.graphics.x, kegg_entry.graphics.y
```

#### Step 4: Map SBML Reactions → KEGG Reactions
```python
# Match by reactants/products
for sbml_reaction in sbml_reactions:
    # Find KEGG reaction with matching compounds
    kegg_reaction = find_matching_kegg_reaction(
        sbml_reaction.reactants,
        sbml_reaction.products,
        kegg_pathway
    )
    if kegg_reaction:
        # Use kegg_reaction.graphics.x, kegg_reaction.graphics.y
```

### Approach B: Compound-Level Position Lookup
**Strategy**: For unmapped pathways, fetch individual compound positions from multiple KEGG pathways

#### Position Database
Build a database of compound positions across all pathways:
```python
compound_positions = {
    "C00031": [  # Glucose
        ("hsa00010", 100, 200),  # Glycolysis
        ("hsa00051", 150, 250),  # Fructose metabolism
        # ... average or select most common
    ]
}
```

#### Clustering Algorithm
```python
# Group species by pathway participation
# Use most frequent pathway as layout source
pathway_votes = Counter()
for species in sbml_species:
    if species.kegg_id:
        pathways = get_pathways_containing(species.kegg_id)
        pathway_votes.update(pathways)

best_pathway = pathway_votes.most_common(1)[0][0]
```

---

## Phase 3: Implementation Architecture

### New Module: `sbml_layout_resolver.py`

```python
class SBMLLayoutResolver:
    """Resolves SBML species/reactions to graphical positions
    using cross-reference databases."""
    
    def __init__(self, pathway_data: PathwayData):
        self.pathway = pathway_data
        self.kegg_client = KEGGClient()
        
    def resolve_layout(self) -> Dict[str, Tuple[float, float]]:
        """Main entry point: returns positions dict."""
        
        # Strategy 1: Try pathway-level mapping
        positions = self._try_pathway_mapping()
        if positions:
            return positions
        
        # Strategy 2: Try compound-level lookup
        positions = self._try_compound_lookup()
        if positions:
            return positions
        
        # Fallback: Return None (use force-directed)
        return None
    
    def _try_pathway_mapping(self):
        """Try to find matching KEGG pathway."""
        # 1. Check model annotations for pathway ID
        pathway_id = self._extract_pathway_id()
        if pathway_id:
            return self._fetch_kegg_layout(pathway_id)
        
        # 2. Heuristic: Find best matching pathway by species
        pathway_id = self._find_best_pathway_match()
        if pathway_id:
            return self._fetch_kegg_layout(pathway_id)
        
        return None
    
    def _fetch_kegg_layout(self, pathway_id):
        """Fetch KGML and extract positions."""
        kgml = self.kegg_client.fetch_pathway(pathway_id)
        kegg_pathway = parse_kgml(kgml)
        
        positions = {}
        for species in self.pathway.species:
            if species.kegg_id:
                entry = kegg_pathway.find_compound(species.kegg_id)
                if entry:
                    positions[species.id] = (
                        entry.graphics.x * 2.5,  # Scale factor
                        entry.graphics.y * 2.5
                    )
        
        return positions if positions else None
```

### Integration into Post-Processor

```python
class PathwayPostProcessor:
    def _calculate_layout_positions(self, processed_data):
        """Enhanced with cross-reference resolution."""
        
        # NEW: Try to resolve from cross-references first
        resolver = SBMLLayoutResolver(self.pathway)
        positions = resolver.resolve_layout()
        
        if positions:
            self.logger.info(f"Using cross-reference layout from KEGG")
            processed_data.positions = positions
            return
        
        # FALLBACK: Use force-directed layout
        if HAS_NETWORKX:
            self._calculate_force_directed_layout(processed_data)
        else:
            self._calculate_grid_layout(processed_data)
```

---

## Phase 4: Database Cross-Reference Sources

### Priority Order
1. **KEGG PATHWAY** (best graphical layouts)
   - Mature, well-positioned diagrams
   - Direct KGML XML format with coordinates
   - API: `https://rest.kegg.jp/get/{pathway_id}/kgml`

2. **Reactome PathwayDiagram** (good quality)
   - SVG/JSON diagram export
   - API: `https://reactome.org/ContentService/diagram/{pathway_id}`
   - Requires more complex parsing

3. **WikiPathways** (community curated)
   - GPML format with layout
   - API: `https://webservice.wikipathways.org/`

4. **BioCyc** (bacterial/metabolic)
   - Good for microbial pathways
   - Requires subscription for API

### Cross-Reference Mapping
```python
XREF_URLS = {
    'kegg.pathway': 'https://rest.kegg.jp/get/{id}/kgml',
    'reactome': 'https://reactome.org/ContentService/diagram/{id}',
    'wikipathways': 'https://webservice.wikipathways.org/getPathway?pwId={id}',
}
```

---

## Phase 5: Implementation Roadmap

### Stage 1: Basic KEGG Pathway Mapping (2-3 hours)
- [ ] Extract model-level pathway IDs from SBML annotations
- [ ] Implement `_extract_pathway_id()` in resolver
- [ ] Fetch KEGG KGML using existing `KEGGClient`
- [ ] Map species by `kegg_id` to KEGG entries
- [ ] Extract positions from KGML graphics

### Stage 2: Heuristic Pathway Matching (2-3 hours)
- [ ] Implement `_find_best_pathway_match()` 
- [ ] Query KEGG API for pathways containing each compound
- [ ] Vote-based pathway selection
- [ ] Fuzzy matching of unmapped species

### Stage 3: Reaction Position Mapping (1-2 hours)
- [ ] Map SBML reactions to KEGG reactions
- [ ] Extract reaction entry positions from KGML
- [ ] Handle reaction-specific graphics

### Stage 4: Quality & Fallbacks (1 hour)
- [ ] Coverage metrics (% species with positions)
- [ ] Hybrid: Use KEGG for mapped, force-directed for unmapped
- [ ] Scaling and coordinate transformation

### Stage 5: Extended Databases (Optional, 4-6 hours)
- [ ] Reactome diagram fetcher
- [ ] WikiPathways GPML parser
- [ ] Multi-database voting system

---

## Expected Outcomes

### Before (Current)
```
SBML Import → Force-Directed Layout → Circular "Ball of String"
```

### After (With Cross-Reference)
```
SBML Import → Extract KEGG IDs → Fetch KEGG Layout → Professional Literature Diagram
```

### Example: BIOMD0000000001 (Glycolysis)
- **Current**: 12 species in circle, hard to interpret
- **Enhanced**: Matches KEGG hsa00010 glycolysis pathway
- **Result**: Standard textbook glycolysis layout

### Success Metrics
- ✅ 70%+ species coverage (mapped to KEGG positions)
- ✅ Layout matches literature/textbook diagrams
- ✅ Automatic for BioModels curated models
- ✅ Graceful fallback to force-directed for unmapped

---

## Testing Strategy

### Test Cases
1. **BIOMD0000000001** (Glycolysis)
   - Should map to `kegg.pathway/hsa00010`
   - Expect >80% coverage

2. **BIOMD0000000002** (MAP Kinase Cascade)  
   - Should map to KEGG signaling pathway
   - Test reaction positioning

3. **Custom SBML** (No annotations)
   - Should fallback to force-directed
   - No errors/crashes

### Validation
```python
# Check coverage
coverage = len(mapped_positions) / len(all_species)
assert coverage > 0.7, "Low cross-reference coverage"

# Check position validity
for pos in positions.values():
    assert 0 < pos[0] < 5000, "X out of bounds"
    assert 0 < pos[1] < 5000, "Y out of bounds"
```

---

## Configuration Options

### UI Controls (Optional)
```python
# In SBML Import Panel
self.use_crossref_layout = Gtk.CheckButton(
    label="Use database layouts (KEGG, Reactome)"
)
self.use_crossref_layout.set_active(True)  # Default ON

self.layout_source_combo = Gtk.ComboBoxText()
self.layout_source_combo.append_text("Auto (best match)")
self.layout_source_combo.append_text("KEGG only")
self.layout_source_combo.append_text("Reactome only")
self.layout_source_combo.append_text("Force-directed (no DB)")
```

---

## Next Steps

1. **Immediate**: Implement Stage 1 (KEGG pathway mapping)
2. **Test**: Run on BIOMD0000000001 and compare to KEGG
3. **Iterate**: Add heuristic matching if direct mapping fails
4. **Polish**: Add UI controls and documentation

## Questions to Address

1. **Licensing**: KEGG REST API terms for academic use?
2. **Caching**: Store fetched KGML files locally?
3. **Scale**: Handle large pathways (100+ species)?
4. **Conflicts**: What if KEGG layout has different species subset?

---

**Status**: Ready for implementation
**Estimated Effort**: 8-12 hours for full pipeline
**Priority**: High (major UX improvement)
