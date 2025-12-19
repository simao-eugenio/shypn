# Codebase Assessment: Module Architecture for Signal Places Integration

**Date:** December 19, 2025  
**Branch:** Signal-Information-Flow  
**Purpose:** Review current architecture to identify integration points for modular Bio-PN

---

## Executive Summary

**Current Architecture:** ✅ Well-structured OOP design
- Base classes with proper inheritance (`PetriNetObject` → `Place`, `Transition`)
- Separate modules for each class (already follows best practices)
- Service layer exists (`sbml_kinetics_service.py`)
- Converter pattern with `BaseConverter` → specialized converters
- Thin loaders pattern evident in pathway processing pipeline

**Integration Readiness:** 🟢 **Good foundation for signal places + modules**

---

## Current Architecture Review

### 1. Data Model Layer (OOP ✅)

#### **Petri Net Objects** (`src/shypn/netobjs/`)

**Base Class:**
- `petri_net_object.py` → `PetriNetObject`
  - Properties: `id`, `name`, `label`, `selected`
  - Callback: `on_changed`
  - Immutable identity, mutable user properties ✅

**Subclasses (Separate Modules ✅):**
- `place.py` → `Place(PetriNetObject)`
  - Already has: `is_signal_place`, `is_compartment_place` attributes
  - Visual distinction: hexagons for signal places, violet for compartments
  - Properties: `tokens`, `initial_marking`, `capacity`
  - **Integration Point:** Add signal_type enum, signal_scope
  
- `transition.py` → `Transition(PetriNetObject)`
  - Already has: `signal_places` list (13-tuple formalism Ψ support)
  - Properties: `rate`, `guard`, `priority`, `kinetic_metadata`
  - **Integration Point:** Add module_id reference
  
- `arc.py` → `Arc(PetriNetObject)`
  - Connects places/transitions with weights
  - Subclasses: `curved_arc.py`, `inhibitor_arc.py`, `test_arc.py`
  - **Integration Point:** Add module boundary validation

**Assessment:** ✅ Already has signal place foundation, ready for enhancement

---

### 2. Document Model (`src/shypn/data/`)

#### **Main Documents:**
- `pathway_document.py` → `PathwayDocument`
  - Represents imported KEGG/SBML files
  - Tracks enrichments, metadata, provenance
  - Links to converted model via `model_id`
  
- `canvas/document_model.py` → `DocumentModel`
  - Main Petri net container (not yet read, but referenced)
  - Likely holds collections: `places`, `transitions`, `arcs`
  - **Integration Point:** Add `modules` collection

**Assessment:** 🟡 Need to verify DocumentModel structure for module collection

---

### 3. Service Layer (Thin ✅)

#### **SBML Integration Service:**
- `services/sbml_kinetics_service.py` → `SBMLKineticsIntegrationService`
  - Clean OOP design: Works with object references (not IDs)
  - Delegates to domain classes (`SBMLKineticMetadata`)
  - Preserves existing metadata (immutability principle)
  - **Pattern:** Service orchestrates, domain objects handle logic ✅

**Architecture Principles (from code comments):**
```python
# Design Principles:
# - Object-oriented: Works with Transition objects directly
# - Reference-based: Passes object references, not string IDs
# - Immutable source: SBML kinetics are locked by default
# - Separation of concerns: Service orchestrates, metadata classes handle logic
```

**Assessment:** ✅ Excellent pattern - replicate for signal detection service

---

### 4. Converter Layer (Thin Coordinators ✅)

#### **Pathway Converter:**
- `data/pathway/pathway_converter.py`
  - Uses `BaseConverter` abstract base class
  - Specialized converters: `SpeciesConverter`, `ReactionConverter` (not shown)
  - Maps biology → Petri net: Species → Places, Reactions → Transitions
  - **Integration Point:** Add `CompartmentConverter` for SBML compartments → modules

**Architecture (from code):**
```python
class BaseConverter:
    """Abstract base class for all converters."""
    def convert(self) -> Dict:
        raise NotImplementedError("Subclasses must implement convert()")

class SpeciesConverter(BaseConverter):
    """Converts species to places."""
    def __init__(self, pathway, document, default_compartment=None):
        # Already handles compartment distinctions!
        self.default_compartment = default_compartment
```

**Assessment:** ✅ Perfect extension point - add `CompartmentConverter`, `ModuleConverter`

---

### 5. Pathway Data Pipeline

#### **Data Classes:**
- `data/pathway/pathway_data.py` → `ProcessedPathwayData`, `Species`, `Reaction`, `KineticLaw`
  - Intermediate representation between SBML and Petri net
  - Species already has compartment attribute
  - **Integration Point:** Add compartment hierarchy parsing

#### **Processors (Not Yet Reviewed):**
- `sbml_parser.py` - Parses SBML XML
- `pathway_postprocessor.py` - Handles layout, positions
- `pathway_validator.py` - Validates pathway data
- **Integration Point:** Add module detection in postprocessor

---

## Integration Points for Signal Places + Modules

### Phase 1: Extend Data Model

#### 1.1 Enhance `Place` class (`netobjs/place.py`)

**Current state:**
```python
class Place(PetriNetObject):
    # Already exists:
    self.is_signal_place = False
    self.is_compartment_place = False
```

**Additions needed:**
```python
from enum import Enum

class SignalType(Enum):
    """Signal place classification (13-tuple formalism Ψ)."""
    QUORUM = "quorum"         # Cell-cell communication (AHL, QS molecules)
    ENERGY = "energy"         # Metabolic state (ATP/ADP ratio, NADH/NAD+)
    REGULATORY = "regulatory" # Gene expression (transcription factors)
    SPATIAL = "spatial"       # Compartment sensing (location markers)

class Place(PetriNetObject):
    def __init__(self, ...):
        # Existing...
        self.is_signal_place = False
        
        # NEW: Signal place properties
        self.signal_type: Optional[SignalType] = None
        self.signal_scope: List[str] = []  # Module IDs that can read this signal
        
        # NEW: Module assignment
        self.module_id: Optional[str] = None
```

**Location:** `src/shypn/netobjs/place.py`  
**Design:** Enum in separate file `src/shypn/netobjs/signal_type.py` for clean imports

---

#### 1.2 Create `Module` class (NEW)

**Design:**
```python
# File: src/shypn/netobjs/module.py
from typing import Set, Optional

class Module:
    """Represents a partition of Bio-PN (modular architecture)."""
    
    def __init__(self, 
                 module_id: str,
                 name: str,
                 compartment_id: Optional[str] = None):
        """Initialize module.
        
        Args:
            module_id: Unique identifier (e.g., "M1", "M_cytoplasm")
            name: Display name (e.g., "Cytoplasm", "Mitochondria")
            compartment_id: SBML compartment ID if mapped from SBML
        """
        self.module_id = module_id
        self.name = name
        self.compartment_id = compartment_id
        
        # Collections (object references, not IDs)
        self.places: Set[Place] = set()
        self.transitions: Set[Transition] = set()
        self.boundary_signals: Set[Place] = set()  # Ψ_shared
        
        # Hierarchy
        self.parent_module: Optional[Module] = None
        self.child_modules: List[Module] = []
        
        # Visual properties (for GUI later)
        self.color: Tuple[float, float, float] = (0.9, 0.9, 0.9)
        self.collapsed: bool = False
    
    def add_place(self, place: Place):
        """Add place to module and set bidirectional reference."""
        self.places.add(place)
        place.module_id = self.module_id
    
    def add_transition(self, transition: Transition):
        """Add transition to module and set bidirectional reference."""
        self.transitions.add(transition)
        transition.module_id = self.module_id
    
    def add_boundary_signal(self, signal_place: Place):
        """Mark signal place as boundary (Ψ_shared)."""
        if not signal_place.is_signal_place:
            raise ValueError(f"Place {signal_place.name} is not a signal place")
        self.boundary_signals.add(signal_place)
```

**Location:** `src/shypn/netobjs/module.py` (new file)  
**Pattern:** Same style as `Place`, `Transition` - separate module ✅

---

#### 1.3 Add `module_id` to `Transition`

**File:** `src/shypn/netobjs/transition.py`

**Addition:**
```python
class Transition(PetriNetObject):
    def __init__(self, ...):
        # Existing...
        self.signal_places = []  # Already exists!
        
        # NEW: Module assignment
        self.module_id: Optional[str] = None
```

**Assessment:** Minimal change, follows existing pattern

---

### Phase 2: Service Layer

#### 2.1 Create Signal Detection Service (NEW)

**File:** `src/shypn/services/signal_detection_service.py`

**Design (following `sbml_kinetics_service.py` pattern):**
```python
"""
Signal Place Detection Service

Service for identifying signal place candidates in imported pathways.

Architecture:
- Object-oriented: Works with Place objects directly
- Heuristic-based: Multiple detection strategies
- Non-destructive: Suggests candidates, doesn't force conversion
- Thin service layer: Delegates to detection algorithms

Design Principles:
- Object references (not IDs)
- Strategy pattern for detection heuristics
- Confidence scoring for suggestions
"""

from typing import List, Dict, Tuple
from enum import Enum
import logging

from shypn.netobjs.place import Place, SignalType
from shypn.netobjs.transition import Transition


class DetectionStrategy(Enum):
    """Signal detection strategies."""
    MODIFIER_ONLY = "modifier_only"  # Places with no arc connections
    ENERGY_METABOLITE = "energy"     # ATP, ADP, NADH, etc.
    REGULATORY = "regulatory"        # Transcription factors
    SPATIAL = "spatial"              # Compartment markers


class SignalDetectionService:
    """Service for detecting signal place candidates."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def detect_signals(
        self,
        places: List[Place],
        transitions: List[Transition],
        arcs: List  # Arc objects
    ) -> Dict[Place, Tuple[SignalType, float]]:
        """
        Detect signal place candidates.
        
        Args:
            places: List of Place objects
            transitions: List of Transition objects
            arcs: List of Arc objects
        
        Returns:
            Dict mapping Place → (suggested SignalType, confidence 0-1)
        """
        candidates = {}
        
        # Strategy 1: Modifier-only (highest confidence)
        modifier_only = self._detect_modifier_only(places, arcs)
        for place in modifier_only:
            candidates[place] = (SignalType.QUORUM, 0.95)
        
        # Strategy 2: Energy metabolites
        energy_places = self._detect_energy_metabolites(places)
        for place in energy_places:
            if place not in candidates:  # Don't override higher confidence
                candidates[place] = (SignalType.ENERGY, 0.80)
        
        # Strategy 3: Regulatory (transcription factors)
        regulatory = self._detect_regulatory(places, transitions)
        for place in regulatory:
            if place not in candidates:
                candidates[place] = (SignalType.REGULATORY, 0.70)
        
        self.logger.info(f"Detected {len(candidates)} signal place candidates")
        return candidates
    
    def _detect_modifier_only(self, places: List[Place], arcs: List) -> List[Place]:
        """Detect places with no arc connections (modifier-only)."""
        # Implementation: Check which places have no arcs
        places_with_arcs = set()
        for arc in arcs:
            if hasattr(arc, 'source'):
                places_with_arcs.add(arc.source)
            if hasattr(arc, 'target'):
                places_with_arcs.add(arc.target)
        
        return [p for p in places if p not in places_with_arcs]
    
    def _detect_energy_metabolites(self, places: List[Place]) -> List[Place]:
        """Detect energy metabolites by name pattern."""
        energy_keywords = ['ATP', 'ADP', 'AMP', 'GTP', 'GDP', 'NADH', 'NAD+', 'NADPH', 'FADH']
        return [p for p in places if any(kw in p.label.upper() for kw in energy_keywords)]
    
    def _detect_regulatory(self, places: List[Place], transitions: List[Transition]) -> List[Place]:
        """Detect regulatory factors (transcription factors, etc.)."""
        # Check if place is already marked in transition.signal_places
        regulatory_places = set()
        for transition in transitions:
            for signal_place_id in transition.signal_places:
                # Find place by ID (need to convert ID to object reference)
                matching = [p for p in places if p.id == signal_place_id]
                if matching:
                    regulatory_places.add(matching[0])
        return list(regulatory_places)
```

**Location:** `src/shypn/services/signal_detection_service.py` (new file)  
**Pattern:** Follows `SBMLKineticsIntegrationService` architecture ✅

---

#### 2.2 Create Module Coupling Service (NEW)

**File:** `src/shypn/services/module_coupling_service.py`

**Purpose:** Validate module boundaries, detect arc violations

**Design:**
```python
"""
Module Coupling Validation Service

Service for validating modular Bio-PN coupling semantics.

Validates:
- No arcs cross module boundaries (structural isolation)
- Signal-only coupling between modules
- Module independence (Pᵢ ∩ Pⱼ ⊆ Ψ_shared)

Architecture:
- Object-oriented: Works with Module, Place, Arc objects
- Validation-focused: Detects violations, generates reports
- Coupling matrix: Shows signal-mediated dependencies
"""

from typing import List, Dict, Set, Tuple
import logging

from shypn.netobjs.module import Module
from shypn.netobjs.place import Place
from shypn.netobjs.arc import Arc


class ModuleCouplingService:
    """Service for validating module coupling semantics."""
    
    def validate_coupling(
        self,
        modules: List[Module],
        arcs: List[Arc]
    ) -> Dict[str, any]:
        """
        Validate module coupling semantics.
        
        Args:
            modules: List of Module objects
            arcs: List of Arc objects
        
        Returns:
            Validation report with violations and coupling matrix
        """
        violations = []
        
        # Check: No arcs cross module boundaries
        for arc in arcs:
            source_module = self._get_module_for_object(arc.source, modules)
            target_module = self._get_module_for_object(arc.target, modules)
            
            if source_module != target_module:
                violations.append({
                    'type': 'arc_crosses_boundary',
                    'arc': arc,
                    'source_module': source_module.name if source_module else None,
                    'target_module': target_module.name if target_module else None
                })
        
        # Build coupling matrix
        coupling_matrix = self._build_coupling_matrix(modules)
        
        return {
            'valid': len(violations) == 0,
            'violations': violations,
            'coupling_matrix': coupling_matrix
        }
```

**Location:** `src/shypn/services/module_coupling_service.py` (new file)

---

### Phase 3: Converter Extension

#### 3.1 Create `CompartmentConverter` (NEW)

**File:** `src/shypn/data/pathway/compartment_converter.py`

**Design:**
```python
"""
Compartment to Module Converter

Converts SBML compartments to Bio-PN modules.

Maps:
- SBML <compartment> → Module
- Compartment hierarchy → Module parent/child
- Species compartment attribute → Place module assignment
"""

from .pathway_converter import BaseConverter
from shypn.netobjs.module import Module


class CompartmentConverter(BaseConverter):
    """Converts SBML compartments to modules."""
    
    def convert(self) -> Dict[str, Module]:
        """
        Convert SBML compartments to modules.
        
        Returns:
            Dict mapping compartment_id → Module object
        """
        compartment_to_module = {}
        
        # Parse compartments from pathway data
        if hasattr(self.pathway, 'compartments'):
            for comp_id, comp_data in self.pathway.compartments.items():
                module = Module(
                    module_id=f"M_{comp_id}",
                    name=comp_data.get('name', comp_id),
                    compartment_id=comp_id
                )
                compartment_to_module[comp_id] = module
                self.document.add_module(module)
        
        # Handle hierarchy (outside/inside relationships)
        self._build_module_hierarchy(compartment_to_module)
        
        return compartment_to_module
```

**Location:** `src/shypn/data/pathway/compartment_converter.py` (new file)  
**Pattern:** Extends `BaseConverter` like `SpeciesConverter` ✅

---

### Phase 4: DocumentModel Extension

**File:** `src/shypn/data/canvas/document_model.py` (need to review first)

**Expected additions:**
```python
class DocumentModel:
    def __init__(self):
        # Existing collections
        self.places = []
        self.transitions = []
        self.arcs = []
        
        # NEW: Module collection
        self.modules: Dict[str, Module] = {}
    
    def add_module(self, module: Module):
        """Add module to document."""
        self.modules[module.module_id] = module
    
    def get_module(self, module_id: str) -> Optional[Module]:
        """Get module by ID."""
        return self.modules.get(module_id)
```

---

## Coupling Points Summary

### Data Flow: SBML → Petri Net (with Modules)

```
SBML File
   ↓
[sbml_parser.py] → PathwayData (compartments, species, reactions)
   ↓
[pathway_postprocessor.py] → ProcessedPathwayData (with positions)
   ↓
[CompartmentConverter] → Modules (NEW)
   ↓
[SpeciesConverter] → Places (assign to modules)
   ↓
[ReactionConverter] → Transitions (assign to modules)
   ↓
[SignalDetectionService] → Mark signal places (NEW)
   ↓
[ModuleCouplingService] → Validate boundaries (NEW)
   ↓
DocumentModel (with modules collection)
```

---

## Architectural Compliance Check

### ✅ OOP Design
- Base class `PetriNetObject` ✅
- Subclasses in separate modules ✅
- New classes will follow same pattern

### ✅ Thin Loaders
- `sbml_kinetics_service.py` already demonstrates pattern ✅
- Loaders parse, services orchestrate, domain objects handle logic ✅
- New services will follow same architecture

### ✅ Wayland Safe
- Current code uses Cairo for rendering (Wayland compatible) ✅
- No X11-specific calls detected
- GUI changes will wait for approval ✅

### 🔄 UI Changes (Approval Required)
- Module visualization (boxes, colors) - NOT IMPLEMENTED YET
- Signal place icons (Ψ symbol) - Already exists (hexagons)
- Collapse/expand controls - DEFERRED

---

## Next Steps (Phase 1 Implementation)

### Immediate Actions:

1. **Create `SignalType` enum**
   - File: `src/shypn/netobjs/signal_type.py`
   - Clean import for `Place` class

2. **Extend `Place` class**
   - Add: `signal_type`, `signal_scope`, `module_id`
   - File: `src/shypn/netobjs/place.py`

3. **Create `Module` class**
   - New file: `src/shypn/netobjs/module.py`
   - Follow `Place`/`Transition` pattern

4. **Extend `Transition` class**
   - Add: `module_id`
   - File: `src/shypn/netobjs/transition.py`

5. **Review `DocumentModel`**
   - Read full structure
   - Plan `modules` collection addition

---

## Risk Assessment

### Low Risk ✅
- Data model extensions (backward compatible properties)
- New service classes (additive, no breaking changes)
- New converter classes (extends existing pattern)

### Medium Risk 🟡
- DocumentModel changes (need to review persistence/serialization)
- Arc validation (need to ensure doesn't break existing models)

### High Risk (Deferred) 🔴
- GUI changes (wait for user approval)
- Simulation engine modifications (test thoroughly)

---

## Conclusion

**Architecture Quality:** 🟢 **Excellent**

The codebase is well-structured for modular architecture integration:
- Clean OOP with proper inheritance
- Separate modules for each class
- Service layer already established
- Converter pattern ready for extension
- Signal place foundation already present

**Recommended Approach:**
1. Start with data model (Place, Module, Transition)
2. Add services (SignalDetectionService, ModuleCouplingService)
3. Extend converters (CompartmentConverter)
4. Update DocumentModel
5. **Defer UI until approved by user**

**Confidence Level:** High - Can proceed with Phase 1 implementation safely.
