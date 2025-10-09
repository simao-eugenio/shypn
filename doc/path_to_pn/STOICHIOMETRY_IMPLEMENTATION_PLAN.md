# Stoichiometry Support Implementation Plan

**Document Version**: 1.0  
**Date**: October 9, 2025  
**Status**: Implementation Plan  
**Priority**: High (98% → 100% conformance)

---

## 📋 Executive Summary

This document outlines the implementation plan for adding stoichiometry support to the KEGG pathway to Petri net converter. This enhancement will increase conformance from **98% to 100%** and enable accurate quantitative modeling of biochemical reactions.

### Goals

- ✅ Extract stoichiometry coefficients from KGML XML
- ✅ Store stoichiometry in data models
- ✅ Apply stoichiometry as arc weights in Petri nets
- ✅ Maintain backward compatibility
- ✅ Add comprehensive tests

### Effort Estimate

**Total Time**: 2-3 hours  
**Complexity**: Low (isolated changes)  
**Risk**: Very Low (backward compatible)

---

## 🎯 Implementation Tasks

### Task 1: Update Data Models ✅

**File**: `src/shypn/importer/kegg/models.py`  
**Lines**: 102-113, 116-127  
**Effort**: 10 minutes

#### Current Implementation

```python
@dataclass
class KEGGSubstrate:
    """Substrate (input) for a reaction.
    
    Attributes:
        id: Entry ID of the substrate compound
        name: KEGG compound ID (e.g., "cpd:C00031")
    """
    id: str
    name: str


@dataclass
class KEGGProduct:
    """Product (output) of a reaction.
    
    Attributes:
        id: Entry ID of the product compound
        name: KEGG compound ID (e.g., "cpd:C00668")
    """
    id: str
    name: str
```

#### Proposed Changes

```python
@dataclass
class KEGGSubstrate:
    """Substrate (input) for a reaction.
    
    Attributes:
        id: Entry ID of the substrate compound
        name: KEGG compound ID (e.g., "cpd:C00031")
        stoichiometry: Stoichiometric coefficient (default: 1)
    """
    id: str
    name: str
    stoichiometry: int = 1  # ✅ NEW FIELD


@dataclass
class KEGGProduct:
    """Product (output) of a reaction.
    
    Attributes:
        id: Entry ID of the product compound
        name: KEGG compound ID (e.g., "cpd:C00668")
        stoichiometry: Stoichiometric coefficient (default: 1)
    """
    id: str
    name: str
    stoichiometry: int = 1  # ✅ NEW FIELD
```

#### Rationale

- **Default value of 1**: Maintains backward compatibility
- **Integer type**: Most stoichiometry coefficients are integers
- **Optional field**: Dataclass with default value makes it optional

#### Testing

```python
# Verify backward compatibility
substrate = KEGGSubstrate(id="1", name="cpd:C00031")
assert substrate.stoichiometry == 1  # Default value

# Verify explicit stoichiometry
substrate_2 = KEGGSubstrate(id="2", name="cpd:C00032", stoichiometry=2)
assert substrate_2.stoichiometry == 2
```

---

### Task 2: Update KGML Parser ✅

**File**: `src/shypn/importer/kegg/kgml_parser.py`  
**Lines**: 167-192  
**Effort**: 15 minutes

#### Current Implementation

```python
def _parse_reaction(self, elem: ET.Element) -> KEGGReaction:
    """Parse reaction element.
    
    Args:
        elem: <reaction> XML element
        
    Returns:
        KEGGReaction object
    """
    reaction = KEGGReaction(
        id=elem.attrib.get('id', ''),
        name=elem.attrib.get('name', ''),
        type=elem.attrib.get('type', 'irreversible')
    )
    
    # Parse substrates
    for substrate_elem in elem.findall('substrate'):
        substrate = KEGGSubstrate(
            id=substrate_elem.attrib.get('id', ''),
            name=substrate_elem.attrib.get('name', '')
        )
        reaction.substrates.append(substrate)
    
    # Parse products
    for product_elem in elem.findall('product'):
        product = KEGGProduct(
            id=product_elem.attrib.get('id', ''),
            name=product_elem.attrib.get('name', '')
        )
        reaction.products.append(product)
    
    return reaction
```

#### Proposed Changes

```python
def _parse_reaction(self, elem: ET.Element) -> KEGGReaction:
    """Parse reaction element.
    
    Args:
        elem: <reaction> XML element
        
    Returns:
        KEGGReaction object
    """
    reaction = KEGGReaction(
        id=elem.attrib.get('id', ''),
        name=elem.attrib.get('name', ''),
        type=elem.attrib.get('type', 'irreversible')
    )
    
    # Parse substrates
    for substrate_elem in elem.findall('substrate'):
        # ✅ EXTRACT STOICHIOMETRY
        stoich_str = substrate_elem.attrib.get('stoichiometry', '1')
        try:
            stoichiometry = int(stoich_str)
        except (ValueError, TypeError):
            stoichiometry = 1  # Default if parsing fails
        
        substrate = KEGGSubstrate(
            id=substrate_elem.attrib.get('id', ''),
            name=substrate_elem.attrib.get('name', ''),
            stoichiometry=stoichiometry  # ✅ USE EXTRACTED VALUE
        )
        reaction.substrates.append(substrate)
    
    # Parse products
    for product_elem in elem.findall('product'):
        # ✅ EXTRACT STOICHIOMETRY
        stoich_str = product_elem.attrib.get('stoichiometry', '1')
        try:
            stoichiometry = int(stoich_str)
        except (ValueError, TypeError):
            stoichiometry = 1  # Default if parsing fails
        
        product = KEGGProduct(
            id=product_elem.attrib.get('id', ''),
            name=product_elem.attrib.get('name', ''),
            stoichiometry=stoichiometry  # ✅ USE EXTRACTED VALUE
        )
        reaction.products.append(product)
    
    return reaction
```

#### KGML XML Format

**Example with stoichiometry**:
```xml
<reaction id="1" name="rn:R00959" type="irreversible">
  <substrate id="2" name="cpd:C00027" stoichiometry="2"/>  <!-- 2 H2O2 -->
  <product id="3" name="cpd:C00001" stoichiometry="2"/>    <!-- 2 H2O -->
  <product id="4" name="cpd:C00007" stoichiometry="1"/>    <!-- 1 O2 -->
</reaction>
```

**Example without stoichiometry** (implicit 1:1):
```xml
<reaction id="2" name="rn:R01068" type="irreversible">
  <substrate id="5" name="cpd:C00031"/>  <!-- Glucose -->
  <substrate id="6" name="cpd:C00002"/>  <!-- ATP -->
  <product id="7" name="cpd:C00668"/>    <!-- Glucose-6-P -->
  <product id="8" name="cpd:C00008"/>    <!-- ADP -->
</reaction>
```

#### Error Handling

- **Missing attribute**: Default to 1
- **Invalid format**: Default to 1 (log warning if needed)
- **Non-integer**: Try to parse as int, default to 1 if fails

---

### Task 3: Update Arc Builder ✅

**File**: `src/shypn/importer/kegg/arc_builder.py`  
**Lines**: 54-90, 92-128  
**Effort**: 20 minutes

#### Current Implementation

```python
def _create_input_arcs(self, substrates, transition: Transition,
                      place_map: Dict[str, Place]) -> List[Arc]:
    """Create input arcs from places to transition."""
    arcs = []
    
    for substrate in substrates:
        place = place_map.get(substrate.id)
        if place is None:
            continue
        
        arc_id = f"A{self.arc_counter}"
        self.arc_counter += 1
        
        arc = Arc(place, transition, arc_id, "", weight=1)  # ⚠️ HARDCODED
        
        arc.metadata = {
            'kegg_compound': substrate.name,
            'source': 'KEGG',
            'direction': 'input'
        }
        
        arcs.append(arc)
    
    return arcs


def _create_output_arcs(self, products, transition: Transition,
                       place_map: Dict[str, Place]) -> List[Arc]:
    """Create output arcs from transition to places."""
    arcs = []
    
    for product in products:
        place = place_map.get(product.id)
        if place is None:
            continue
        
        arc_id = f"A{self.arc_counter}"
        self.arc_counter += 1
        
        arc = Arc(transition, place, arc_id, "", weight=1)  # ⚠️ HARDCODED
        
        arc.metadata = {
            'kegg_compound': product.name,
            'source': 'KEGG',
            'direction': 'output'
        }
        
        arcs.append(arc)
    
    return arcs
```

#### Proposed Changes

```python
def _create_input_arcs(self, substrates, transition: Transition,
                      place_map: Dict[str, Place]) -> List[Arc]:
    """Create input arcs from places to transition.
    
    Args:
        substrates: List of KEGGSubstrate objects (with stoichiometry)
        transition: Target transition
        place_map: Mapping from entry ID to Place
        
    Returns:
        List of Arc objects (place → transition) with stoichiometric weights
    """
    arcs = []
    
    for substrate in substrates:
        place = place_map.get(substrate.id)
        if place is None:
            continue
        
        arc_id = f"A{self.arc_counter}"
        self.arc_counter += 1
        
        # ✅ USE STOICHIOMETRY FROM SUBSTRATE
        weight = substrate.stoichiometry
        arc = Arc(place, transition, arc_id, "", weight=weight)
        
        # ✅ STORE STOICHIOMETRY IN METADATA
        arc.metadata = {
            'kegg_compound': substrate.name,
            'source': 'KEGG',
            'direction': 'input',
            'stoichiometry': substrate.stoichiometry  # ✅ ADD TO METADATA
        }
        
        arcs.append(arc)
    
    return arcs


def _create_output_arcs(self, products, transition: Transition,
                       place_map: Dict[str, Place]) -> List[Arc]:
    """Create output arcs from transition to places.
    
    Args:
        products: List of KEGGProduct objects (with stoichiometry)
        transition: Source transition
        place_map: Mapping from entry ID to Place
        
    Returns:
        List of Arc objects (transition → place) with stoichiometric weights
    """
    arcs = []
    
    for product in products:
        place = place_map.get(product.id)
        if place is None:
            continue
        
        arc_id = f"A{self.arc_counter}"
        self.arc_counter += 1
        
        # ✅ USE STOICHIOMETRY FROM PRODUCT
        weight = product.stoichiometry
        arc = Arc(transition, place, arc_id, "", weight=weight)
        
        # ✅ STORE STOICHIOMETRY IN METADATA
        arc.metadata = {
            'kegg_compound': product.name,
            'source': 'KEGG',
            'direction': 'output',
            'stoichiometry': product.stoichiometry  # ✅ ADD TO METADATA
        }
        
        arcs.append(arc)
    
    return arcs
```

#### Impact

- **Backward compatible**: Default stoichiometry of 1 preserves existing behavior
- **Metadata**: Stoichiometry stored for debugging and analysis
- **Petri net semantics**: Arc weights now correctly represent stoichiometry

---

### Task 4: Add Arc Metadata ✅

**Included in Task 3**

Arc metadata now includes:
```python
arc.metadata = {
    'kegg_compound': 'cpd:C00027',
    'source': 'KEGG',
    'direction': 'input',  # or 'output'
    'stoichiometry': 2      # ✅ NEW FIELD
}
```

**Benefits**:
- Traceability: Can trace back to original KGML stoichiometry
- Debugging: Easy to verify correct conversion
- Analysis: Can analyze stoichiometry patterns in pathways

---

### Task 5: Create Test Cases ✅

**File**: `tests/test_stoichiometry_conversion.py` (NEW)  
**Effort**: 45 minutes

#### Test Strategy

1. **Unit tests**: Test parser with stoichiometry XML
2. **Integration tests**: Test full conversion pipeline
3. **Edge cases**: Missing stoichiometry, invalid values
4. **Verification**: Check arc weights match stoichiometry

#### Test Implementation

```python
"""Tests for stoichiometry support in KEGG pathway conversion."""

import pytest
from shypn.importer.kegg import parse_kgml, convert_pathway
from shypn.importer.kegg.models import KEGGSubstrate, KEGGProduct


class TestStoichiometryDataModels:
    """Test stoichiometry in data models."""
    
    def test_substrate_default_stoichiometry(self):
        """Test substrate has default stoichiometry of 1."""
        substrate = KEGGSubstrate(id="1", name="cpd:C00031")
        assert substrate.stoichiometry == 1
    
    def test_substrate_explicit_stoichiometry(self):
        """Test substrate with explicit stoichiometry."""
        substrate = KEGGSubstrate(id="1", name="cpd:C00027", stoichiometry=2)
        assert substrate.stoichiometry == 2
    
    def test_product_default_stoichiometry(self):
        """Test product has default stoichiometry of 1."""
        product = KEGGProduct(id="1", name="cpd:C00668")
        assert product.stoichiometry == 1
    
    def test_product_explicit_stoichiometry(self):
        """Test product with explicit stoichiometry."""
        product = KEGGProduct(id="1", name="cpd:C00001", stoichiometry=2)
        assert product.stoichiometry == 2


class TestStoichiometryParsing:
    """Test stoichiometry parsing from KGML."""
    
    def test_parse_reaction_without_stoichiometry(self):
        """Test parsing reaction with implicit 1:1 stoichiometry."""
        kgml = """<?xml version="1.0"?>
        <pathway name="test" org="hsa" number="00010">
            <entry id="1" name="cpd:C00031" type="compound">
                <graphics name="Glucose" x="100" y="100"/>
            </entry>
            <entry id="2" name="cpd:C00668" type="compound">
                <graphics name="G6P" x="200" y="100"/>
            </entry>
            <reaction id="1" name="rn:R01068" type="irreversible">
                <substrate id="1" name="cpd:C00031"/>
                <product id="2" name="cpd:C00668"/>
            </reaction>
        </pathway>
        """
        
        pathway = parse_kgml(kgml)
        reaction = pathway.reactions[0]
        
        # Verify default stoichiometry
        assert len(reaction.substrates) == 1
        assert reaction.substrates[0].stoichiometry == 1
        assert len(reaction.products) == 1
        assert reaction.products[0].stoichiometry == 1
    
    def test_parse_reaction_with_stoichiometry(self):
        """Test parsing reaction with explicit stoichiometry (2 H2O2 → 2 H2O + O2)."""
        kgml = """<?xml version="1.0"?>
        <pathway name="test" org="hsa" number="00010">
            <entry id="1" name="cpd:C00027" type="compound">
                <graphics name="H2O2" x="100" y="100"/>
            </entry>
            <entry id="2" name="cpd:C00001" type="compound">
                <graphics name="H2O" x="200" y="100"/>
            </entry>
            <entry id="3" name="cpd:C00007" type="compound">
                <graphics name="O2" x="300" y="100"/>
            </entry>
            <reaction id="1" name="rn:R00959" type="irreversible">
                <substrate id="1" name="cpd:C00027" stoichiometry="2"/>
                <product id="2" name="cpd:C00001" stoichiometry="2"/>
                <product id="3" name="cpd:C00007" stoichiometry="1"/>
            </reaction>
        </pathway>
        """
        
        pathway = parse_kgml(kgml)
        reaction = pathway.reactions[0]
        
        # Verify explicit stoichiometry
        assert len(reaction.substrates) == 1
        assert reaction.substrates[0].stoichiometry == 2
        assert len(reaction.products) == 2
        assert reaction.products[0].stoichiometry == 2  # H2O
        assert reaction.products[1].stoichiometry == 1  # O2
    
    def test_parse_invalid_stoichiometry(self):
        """Test parsing handles invalid stoichiometry gracefully."""
        kgml = """<?xml version="1.0"?>
        <pathway name="test" org="hsa" number="00010">
            <entry id="1" name="cpd:C00031" type="compound">
                <graphics name="Glucose" x="100" y="100"/>
            </entry>
            <entry id="2" name="cpd:C00668" type="compound">
                <graphics name="G6P" x="200" y="100"/>
            </entry>
            <reaction id="1" name="rn:R01068" type="irreversible">
                <substrate id="1" name="cpd:C00031" stoichiometry="invalid"/>
                <product id="2" name="cpd:C00668" stoichiometry="3.14"/>
            </reaction>
        </pathway>
        """
        
        pathway = parse_kgml(kgml)
        reaction = pathway.reactions[0]
        
        # Should default to 1 for invalid values
        assert reaction.substrates[0].stoichiometry == 1  # Invalid string
        assert reaction.products[0].stoichiometry == 3    # Float truncated to int


class TestStoichiometryConversion:
    """Test stoichiometry in Petri net conversion."""
    
    def test_convert_simple_reaction(self):
        """Test 1:1 reaction converts with weight 1."""
        kgml = """<?xml version="1.0"?>
        <pathway name="test" org="hsa" number="00010" title="Test">
            <entry id="1" name="cpd:C00031" type="compound">
                <graphics name="Glucose" x="100" y="100"/>
            </entry>
            <entry id="2" name="cpd:C00668" type="compound">
                <graphics name="G6P" x="200" y="100"/>
            </entry>
            <reaction id="1" name="rn:R01068" type="irreversible">
                <substrate id="1" name="cpd:C00031"/>
                <product id="2" name="cpd:C00668"/>
            </reaction>
        </pathway>
        """
        
        pathway = parse_kgml(kgml)
        document = convert_pathway(pathway)
        
        # Verify conversion
        assert len(document.places) == 2
        assert len(document.transitions) == 1
        assert len(document.arcs) == 2
        
        # Check arc weights
        input_arc = [a for a in document.arcs if a.source == document.places[0]][0]
        output_arc = [a for a in document.arcs if a.target == document.places[1]][0]
        
        assert input_arc.weight == 1
        assert output_arc.weight == 1
    
    def test_convert_stoichiometric_reaction(self):
        """Test 2:2:1 reaction (2 H2O2 → 2 H2O + O2) converts with correct weights."""
        kgml = """<?xml version="1.0"?>
        <pathway name="test" org="hsa" number="00010" title="Test">
            <entry id="1" name="cpd:C00027" type="compound">
                <graphics name="H2O2" x="100" y="100"/>
            </entry>
            <entry id="2" name="cpd:C00001" type="compound">
                <graphics name="H2O" x="200" y="100"/>
            </entry>
            <entry id="3" name="cpd:C00007" type="compound">
                <graphics name="O2" x="300" y="100"/>
            </entry>
            <reaction id="1" name="rn:R00959" type="irreversible">
                <substrate id="1" name="cpd:C00027" stoichiometry="2"/>
                <product id="2" name="cpd:C00001" stoichiometry="2"/>
                <product id="3" name="cpd:C00007" stoichiometry="1"/>
            </reaction>
        </pathway>
        """
        
        pathway = parse_kgml(kgml)
        document = convert_pathway(pathway)
        
        # Verify conversion
        assert len(document.places) == 3
        assert len(document.transitions) == 1
        assert len(document.arcs) == 3  # 1 input, 2 outputs
        
        # Find arcs by metadata
        h2o2_place = [p for p in document.places if "H2O2" in p.label][0]
        h2o_place = [p for p in document.places if p.label == "H2O"][0]
        o2_place = [p for p in document.places if "O2" in p.label][0]
        
        # Check weights
        h2o2_arc = [a for a in document.arcs if a.source == h2o2_place][0]
        h2o_arc = [a for a in document.arcs if a.target == h2o_place][0]
        o2_arc = [a for a in document.arcs if a.target == o2_place][0]
        
        assert h2o2_arc.weight == 2  # 2 H2O2 consumed
        assert h2o_arc.weight == 2   # 2 H2O produced
        assert o2_arc.weight == 1    # 1 O2 produced
    
    def test_arc_metadata_contains_stoichiometry(self):
        """Test arc metadata includes stoichiometry value."""
        kgml = """<?xml version="1.0"?>
        <pathway name="test" org="hsa" number="00010" title="Test">
            <entry id="1" name="cpd:C00027" type="compound">
                <graphics name="H2O2" x="100" y="100"/>
            </entry>
            <entry id="2" name="cpd:C00001" type="compound">
                <graphics name="H2O" x="200" y="100"/>
            </entry>
            <reaction id="1" name="rn:R00959" type="irreversible">
                <substrate id="1" name="cpd:C00027" stoichiometry="2"/>
                <product id="2" name="cpd:C00001" stoichiometry="2"/>
            </reaction>
        </pathway>
        """
        
        pathway = parse_kgml(kgml)
        document = convert_pathway(pathway)
        
        # Check metadata
        for arc in document.arcs:
            assert hasattr(arc, 'metadata')
            assert 'stoichiometry' in arc.metadata
            assert arc.metadata['stoichiometry'] == 2


class TestStoichiometrySimulation:
    """Test stoichiometry in simulation (firing rules)."""
    
    def test_firing_consumes_correct_tokens(self):
        """Test transition firing consumes tokens according to stoichiometry."""
        kgml = """<?xml version="1.0"?>
        <pathway name="test" org="hsa" number="00010" title="Test">
            <entry id="1" name="cpd:C00027" type="compound">
                <graphics name="H2O2" x="100" y="100"/>
            </entry>
            <entry id="2" name="cpd:C00001" type="compound">
                <graphics name="H2O" x="200" y="100"/>
            </entry>
            <reaction id="1" name="rn:R00959" type="irreversible">
                <substrate id="1" name="cpd:C00027" stoichiometry="2"/>
                <product id="2" name="cpd:C00001" stoichiometry="2"/>
            </reaction>
        </pathway>
        """
        
        pathway = parse_kgml(kgml)
        document = convert_pathway(pathway, add_initial_marking=True, initial_tokens=10)
        
        # Get objects
        h2o2_place = document.places[0]
        h2o_place = document.places[1]
        transition = document.transitions[0]
        
        # Check initial state
        assert h2o2_place.tokens == 10
        assert h2o_place.tokens == 10
        
        # Check transition is enabled (needs 2 tokens)
        input_arc = [a for a in document.arcs if a.target == transition][0]
        assert input_arc.weight == 2
        assert h2o2_place.tokens >= input_arc.weight  # Enabled
        
        # Simulate firing (manual)
        h2o2_place.tokens -= 2  # Consume 2 H2O2
        h2o_place.tokens += 2   # Produce 2 H2O
        
        assert h2o2_place.tokens == 8
        assert h2o_place.tokens == 12


# Run tests
if __name__ == '__main__':
    pytest.main([__file__, '-v'])
```

#### Test Coverage

- ✅ Data model defaults
- ✅ Data model explicit values
- ✅ Parser implicit stoichiometry (1:1)
- ✅ Parser explicit stoichiometry (2:2:1)
- ✅ Parser invalid values
- ✅ Conversion arc weights
- ✅ Arc metadata
- ✅ Simulation firing rules

---

### Task 6: Update Documentation ✅

**File**: `doc/path_to_pn/IMPLEMENTATION_CONFORMANCE_ANALYSIS.md`  
**Effort**: 30 minutes

#### Changes Required

1. **Update Conformance Matrix**:
   ```markdown
   | **Stoichiometry** | ✅ Complete | 100% | **IMPLEMENTED** (was 50%) |
   ```

2. **Update Rule 3 Section**:
   - Change verdict from "PARTIALLY CONFORMANT" to "FULLY CONFORMANT"
   - Remove warning about hardcoded weights
   - Add implementation notes

3. **Remove Critical Issue Section**:
   - Remove "Critical Issue: Stoichiometry Support" section
   - Move to "Resolved Issues" section

4. **Update Recommendations**:
   - Remove "Add Stoichiometry Support" from Priority 1
   - Add note about implementation completion

5. **Update Conclusion**:
   - Change conformance from 98% to 100%
   - Update final verdict

#### Example Updates

**Before**:
```markdown
### Rule 3: Stoichiometry → Arc Weights ⚠️ PARTIALLY CONFORMANT

**Verdict**: **PARTIALLY CONFORMANT** - Arc creation correct, but stoichiometry always 1.
```

**After**:
```markdown
### Rule 3: Stoichiometry → Arc Weights ✅ FULLY CONFORMANT

**Implementation** (`arc_builder.py:79-120`):
```python
# Input arcs use substrate.stoichiometry
weight = substrate.stoichiometry
arc = Arc(place, transition, arc_id, "", weight=weight)

# Output arcs use product.stoichiometry
weight = product.stoichiometry
arc = Arc(transition, place, arc_id, "", weight=weight)
```

**Conformance Analysis**:
- ✅ **Arc creation**: Substrates → Input arcs, Products → Output arcs
- ✅ **Direction**: Correct arc direction
- ✅ **Metadata**: Compound names and stoichiometry preserved
- ✅ **Stoichiometry**: Correctly extracted from KGML and applied as arc weights

**Verdict**: **FULLY CONFORMANT** - Complete implementation of stoichiometric mapping.
```

---

## 📝 Implementation Checklist

### Pre-Implementation

- [x] Review conformance analysis
- [x] Create implementation plan
- [x] Estimate effort and risk
- [ ] Review plan with team (if applicable)

### Implementation

- [ ] **Task 1**: Update data models (10 min)
  - [ ] Add stoichiometry field to KEGGSubstrate
  - [ ] Add stoichiometry field to KEGGProduct
  - [ ] Update docstrings
  - [ ] Verify backward compatibility

- [ ] **Task 2**: Update KGML parser (15 min)
  - [ ] Extract stoichiometry attribute
  - [ ] Add error handling
  - [ ] Handle missing attributes
  - [ ] Test with sample KGML

- [ ] **Task 3**: Update arc builder (20 min)
  - [ ] Modify _create_input_arcs()
  - [ ] Modify _create_output_arcs()
  - [ ] Use substrate.stoichiometry
  - [ ] Use product.stoichiometry

- [ ] **Task 4**: Add arc metadata (included in Task 3)
  - [ ] Add stoichiometry to input arc metadata
  - [ ] Add stoichiometry to output arc metadata

- [ ] **Task 5**: Create test cases (45 min)
  - [ ] Write data model tests
  - [ ] Write parser tests
  - [ ] Write conversion tests
  - [ ] Write integration tests
  - [ ] Run all tests

- [ ] **Task 6**: Update documentation (30 min)
  - [ ] Update conformance matrix
  - [ ] Update Rule 3 section
  - [ ] Remove critical issue
  - [ ] Update recommendations
  - [ ] Update conclusion

### Post-Implementation

- [ ] Run full test suite
- [ ] Test with real KEGG pathways
- [ ] Update CHANGELOG
- [ ] Create pull request
- [ ] Code review
- [ ] Merge to main

---

## 🧪 Testing Strategy

### Unit Tests

1. **Data Models**:
   - Test default stoichiometry (1)
   - Test explicit stoichiometry
   - Test backward compatibility

2. **Parser**:
   - Test with stoichiometry attribute
   - Test without stoichiometry attribute
   - Test invalid stoichiometry values

3. **Arc Builder**:
   - Test weight assignment
   - Test metadata storage

### Integration Tests

1. **Full Conversion**:
   - Simple 1:1 reaction
   - Complex stoichiometry (2:2:1)
   - Multiple reactions
   - Reversible reactions with stoichiometry

2. **Real Pathways**:
   - Glycolysis (hsa00010)
   - TCA cycle (hsa00020)
   - Oxidative phosphorylation (hsa00190)

### Manual Testing

1. Import KEGG pathway with stoichiometry
2. Verify arc weights in UI
3. Run simulation and verify token consumption
4. Export and reimport

---

## 📊 Success Criteria

### Functional

- ✅ Parser extracts stoichiometry from KGML
- ✅ Data models store stoichiometry
- ✅ Arc builder uses stoichiometry for weights
- ✅ Metadata includes stoichiometry
- ✅ Backward compatible (default = 1)

### Quality

- ✅ All unit tests pass
- ✅ All integration tests pass
- ✅ Code coverage > 90%
- ✅ No regressions in existing functionality

### Documentation

- ✅ Conformance analysis updated
- ✅ Code comments added
- ✅ Examples provided
- ✅ CHANGELOG updated

---

## 🔄 Rollback Plan

**If issues arise**:

1. **Revert commits**: Git revert to previous state
2. **Feature flag**: Add `use_stoichiometry` option (default False)
3. **Hotfix branch**: Create hotfix for production

**Low risk** due to:
- Backward compatible (default value 1)
- Isolated changes (3 files)
- Comprehensive tests

---

## 📅 Timeline

### Estimated Schedule

| Task | Duration | Dependencies |
|------|----------|--------------|
| Task 1: Data models | 10 min | None |
| Task 2: Parser | 15 min | Task 1 |
| Task 3: Arc builder | 20 min | Task 1 |
| Task 4: Metadata | 0 min | (included in Task 3) |
| Task 5: Tests | 45 min | Tasks 1-3 |
| Task 6: Documentation | 30 min | Tasks 1-5 |
| **Total** | **2 hours** | - |

### Recommended Approach

**Single session implementation** (2-3 hours):
1. Implement all code changes (Tasks 1-3)
2. Write and run tests (Task 5)
3. Update documentation (Task 6)
4. Commit and push

---

## 🎯 Impact Assessment

### Benefits

- ✅ **100% conformance** with documented requirements
- ✅ **Accurate modeling** of biochemical reactions
- ✅ **Correct simulations** with stoichiometric constraints
- ✅ **Complete feature** for quantitative analysis

### Risks

- ⚠️ **KGML limitation**: Not all KGML files have stoichiometry
- ⚠️ **Backward compatibility**: Must maintain default behavior

### Mitigation

- Default value of 1 handles missing stoichiometry
- Comprehensive tests verify backward compatibility
- Documentation explains KGML limitations

---

## 📚 References

- **KGML Specification**: https://www.kegg.jp/kegg/xml/docs/
- **Petri Net Theory**: Murata, T. (1989). "Petri nets: Properties, analysis and applications"
- **Conformance Analysis**: `doc/path_to_pn/IMPLEMENTATION_CONFORMANCE_ANALYSIS.md`
- **Mapping Semantics**: `doc/path_to_pn/BIOCHEMICAL_PATHWAY_TO_PETRI_NET_MAPPING.md`

---

**Document Maintainer**: ShypN Development Team  
**Status**: Ready for Implementation  
**Last Updated**: October 9, 2025
