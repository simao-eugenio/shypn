# KEGG Pathway Import - Implementation Plan

**Date**: October 7, 2025  
**Status**: 📋 PLANNING

## Implementation Phases

### Phase 1: Core Infrastructure (Days 1-2)
**Goal**: Set up basic API client and XML parsing

#### Tasks:
1. Create module structure: `src/shypn/import/kegg/`
2. Implement `api_client.py`:
   - `fetch_kgml(pathway_id)` → XML string
   - Error handling (404, network errors)
   - Basic caching (optional)
3. Implement `kgml_parser.py`:
   - Parse XML using `xml.etree.ElementTree`
   - Extract entries, reactions, relations
   - Build `KEGGPathway` data structure
4. Unit tests with sample KGML files

**Deliverable**: Can fetch and parse KGML files into Python objects

---

### Phase 2: Conversion Engine (Days 3-4)
**Goal**: Convert KGML to Petri net model

#### Tasks:
1. Implement `pathway_converter.py`:
   - `convert_compounds_to_places()` 
   - `convert_reactions_to_transitions()`
   - `create_arcs_from_substrates_products()`
   - Coordinate scaling and translation
2. Handle stoichiometry (arc weights)
3. Handle reversible reactions
4. Create `DocumentModel` with all objects
5. Test with glycolysis pathway

**Deliverable**: Working conversion from KGML → DocumentModel

---

### Phase 3: Import Dialog UI (Days 5-6)
**Goal**: User-friendly import interface

#### Tasks:
1. Create `kegg_import_dialog.py` (GTK dialog)
2. UI elements:
   - Pathway ID text entry
   - Organism dropdown
   - Options checkboxes
   - Preview panel
   - Academic use confirmation
3. Wire dialog to menu: File → Import → KEGG Pathway
4. Progress indicator for download
5. Error dialogs for failures

**Deliverable**: Complete import workflow from UI

---

### Phase 4: Advanced Features (Days 7-8)
**Goal**: Handle complex scenarios

#### Tasks:
1. Regulatory relations (activation/inhibition)
2. Cofactor filtering options
3. Layout optimization (spread out overlapping nodes)
4. Metadata preservation (KEGG IDs, enzyme names)
5. Multiple pathway formats (map, ko, ec, rn, org-specific)
6. Caching system for downloaded pathways

**Deliverable**: Production-ready import with options

---

### Phase 5: Testing & Documentation (Days 9-10)
**Goal**: Validate and document

#### Tasks:
1. Test with multiple pathways:
   - Glycolysis (`hsa00010`)
   - TCA cycle (`hsa00020`)
   - Pentose phosphate (`hsa00030`)
   - MAPK signaling (`hsa04010`)
2. Validate biochemical correctness
3. User documentation
4. Developer API documentation
5. Example workflows
6. Known limitations document

**Deliverable**: Documented, tested feature

---

## Technical Specifications

### Dependencies

```python
# Already available in shypn
import xml.etree.ElementTree as ET  # XML parsing
import requests  # HTTP requests (may need to add)
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple

# GTK for dialog
from gi.repository import Gtk, GLib
```

### File Structure

```
src/shypn/import/
├── __init__.py
├── kegg/
│   ├── __init__.py
│   ├── api_client.py          # 150 lines
│   ├── kgml_parser.py         # 300 lines
│   ├── pathway_converter.py   # 400 lines
│   ├── mapping_rules.py       # 200 lines
│   └── models.py              # 100 lines
└── dialogs/
    ├── __init__.py
    └── kegg_import_dialog.py  # 350 lines
```

**Total new code**: ~1500 lines

---

## Code Samples

### API Client Example

```python
# api_client.py
import requests
from typing import Optional

class KEGGAPIClient:
    """Client for KEGG REST API."""
    
    BASE_URL = "https://rest.kegg.jp"
    
    def fetch_kgml(self, pathway_id: str) -> Optional[str]:
        """Fetch KGML XML for pathway.
        
        Args:
            pathway_id: e.g., "hsa00010", "map00020"
            
        Returns:
            XML string or None on error
        """
        url = f"{self.BASE_URL}/get/{pathway_id}/kgml"
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {pathway_id}: {e}")
            return None
    
    def list_pathways(self, organism: str = None) -> List[Tuple[str, str]]:
        """List available pathways.
        
        Args:
            organism: Optional org code (e.g., "hsa"), None for reference
            
        Returns:
            List of (pathway_id, title) tuples
        """
        path = f"pathway/{organism}" if organism else "pathway"
        url = f"{self.BASE_URL}/list/{path}"
        # ... implementation
```

### Parser Example

```python
# kgml_parser.py
import xml.etree.ElementTree as ET
from .models import KEGGPathway, KEGGEntry, KEGGReaction

class KGMLParser:
    """Parse KGML XML into structured data."""
    
    def parse(self, xml_string: str) -> KEGGPathway:
        """Parse KGML XML.
        
        Args:
            xml_string: KGML XML content
            
        Returns:
            KEGGPathway object
        """
        root = ET.fromstring(xml_string)
        
        pathway = KEGGPathway(
            id=root.attrib.get('number'),
            name=root.attrib.get('name'),
            organism=root.attrib.get('org'),
            title=root.attrib.get('title'),
            entries={},
            reactions=[],
            relations=[]
        )
        
        # Parse entries
        for entry_elem in root.findall('entry'):
            entry = self._parse_entry(entry_elem)
            pathway.entries[entry.id] = entry
        
        # Parse reactions
        for reaction_elem in root.findall('reaction'):
            reaction = self._parse_reaction(reaction_elem)
            pathway.reactions.append(reaction)
        
        return pathway
    
    def _parse_entry(self, elem: ET.Element) -> KEGGEntry:
        graphics_elem = elem.find('graphics')
        graphics = {}
        if graphics_elem is not None:
            graphics = {
                'x': float(graphics_elem.attrib.get('x', 0)),
                'y': float(graphics_elem.attrib.get('y', 0)),
                'width': float(graphics_elem.attrib.get('width', 46)),
                'height': float(graphics_elem.attrib.get('height', 17)),
                'name': graphics_elem.attrib.get('name', '')
            }
        
        return KEGGEntry(
            id=elem.attrib.get('id'),
            name=elem.attrib.get('name'),
            type=elem.attrib.get('type'),
            reaction=elem.attrib.get('reaction'),
            graphics=graphics
        )
```

### Converter Example

```python
# pathway_converter.py
from shypn.data.canvas.document_model import DocumentModel
from shypn.netobjs import Place, Transition, Arc
from .models import KEGGPathway

class PathwayConverter:
    """Convert KEGG pathway to Petri net."""
    
    def __init__(self, options: dict = None):
        self.options = options or {}
        self.coordinate_scale = self.options.get('coordinate_scale', 2.5)
    
    def convert(self, pathway: KEGGPathway) -> DocumentModel:
        """Convert pathway to Petri net.
        
        Args:
            pathway: Parsed KEGG pathway
            
        Returns:
            DocumentModel with places, transitions, arcs
        """
        doc = DocumentModel()
        
        # Map to track KEGG entry ID → Place/Transition
        entry_map = {}
        
        # Create places for compounds
        for entry_id, entry in pathway.entries.items():
            if entry.type == 'compound':
                place = self._create_place_from_entry(entry)
                doc.places.append(place)
                entry_map[entry_id] = place
        
        # Create transitions for reactions
        for reaction in pathway.reactions:
            transition = self._create_transition_from_reaction(reaction, pathway)
            doc.transitions.append(transition)
            
            # Create arcs for substrates (input)
            for substrate_id, compound_id in reaction.substrates:
                if substrate_id in entry_map:
                    arc = Arc(
                        entry_map[substrate_id],  # place
                        transition,
                        f"A{doc._next_arc_id}",
                        "",
                        weight=1
                    )
                    doc.arcs.append(arc)
                    doc._next_arc_id += 1
            
            # Create arcs for products (output)
            for product_id, compound_id in reaction.products:
                if product_id in entry_map:
                    arc = Arc(
                        transition,
                        entry_map[product_id],  # place
                        f"A{doc._next_arc_id}",
                        "",
                        weight=1
                    )
                    doc.arcs.append(arc)
                    doc._next_arc_id += 1
        
        return doc
    
    def _create_place_from_entry(self, entry: KEGGEntry) -> Place:
        x = entry.graphics['x'] * self.coordinate_scale
        y = entry.graphics['y'] * self.coordinate_scale
        label = entry.graphics['name'].split(',')[0]  # First compound name
        
        place = Place(x, y, entry.id, 0)
        place.label = label
        return place
```

---

## Risk Assessment

### Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| KGML format changes | Low | High | Parse with error handling, version checks |
| API rate limiting | Medium | Medium | Caching, user warnings |
| Complex pathways too large | High | Medium | Filtering options, hierarchical import |
| Coordinate overlap | High | Low | Auto-layout adjustment |
| Missing Python `requests` | Low | Low | Add to `requirements.txt` |

### Biological Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Oversimplified mapping | High | Medium | Document assumptions, expert review |
| Loss of kinetic information | High | Medium | Preserve metadata, future enhancement |
| Incorrect stoichiometry | Low | High | Careful parsing, validation tests |

---

## Success Criteria

### Minimum Viable Product (MVP)
- ✅ Import glycolysis pathway (hsa00010)
- ✅ Compounds mapped to places
- ✅ Reactions mapped to transitions
- ✅ Arcs created with correct direction
- ✅ UI dialog functional
- ✅ Academic use warning

### Extended Features
- ⬜ Multiple pathway types supported
- ⬜ Regulatory relations preserved
- ⬜ Cofactor filtering
- ⬜ Coordinate optimization
- ⬜ Batch import
- ⬜ Caching system

---

## Timeline Estimate

**Conservative**: 10 working days (2 weeks)  
**Optimistic**: 6 working days (1.2 weeks)  
**Realistic**: 8 working days (1.6 weeks)

---

## Questions to Resolve

1. **Should we add `requests` library?**
   - Check if already in `requirements.txt`
   - Alternative: use `urllib` (built-in)

2. **Coordinate system**
   - KEGG uses top-left origin
   - shypn uses... (center? bottom-left?)
   - May need Y-axis flip

3. **Initial marking**
   - Should compounds have initial tokens?
   - User option or always 0?

4. **Compound groups**
   - KEGG has compound groups (e.g., "ATP + H2O")
   - How to represent in Petri net?

5. **Pathway hierarchies**
   - Some entries are links to other pathways
   - Import recursively or ignore?

---

## Next Action

**Recommendation**: Start with Phase 1 (Core Infrastructure)

1. Create directory structure
2. Implement `api_client.py` with `fetch_kgml()`
3. Test with `hsa00010` (glycolysis)
4. Examine actual KGML structure

**Estimated time**: 2-3 hours

Would you like to proceed with implementation?
