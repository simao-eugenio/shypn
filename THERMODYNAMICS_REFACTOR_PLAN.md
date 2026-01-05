# Thermodynamics Refactoring Plan - Option A + Universal Category

**Date:** January 5, 2026  
**Branch:** Usability-and-Manuscripts  
**Objective:** Create unified Thermodynamics category in Pathway Operations Panel

---

## �️ **Coding Standards & Architecture**

### **OOP Design Principles**
1. **Separation of Concerns:**
   - Base classes define interfaces
   - Subclasses implement specific behavior
   - One class per file (except small related classes)
   - Logic separated from UI presentation

2. **Minimal Loaders:**
   - UI loader files only handle widget assembly
   - Business logic in separate model/controller classes
   - Data transformation in dedicated utilities
   - Event handlers delegate to service classes

3. **File Organization:**
   - `/src/shypn/thermodynamics/` - Core thermodynamics engine
   - `/src/shypn/ui/panels/` - UI components (thin loaders)
   - `/doc/` - User documentation, guides, examples
   - `/scripts/` - Utility scripts, migration tools
   - `/tests/` - Unit tests, integration tests

4. **Wayland Compatibility:**
   - Use GTK3 properly (not deprecated GTK2 code)
   - Avoid X11-specific calls
   - Use `Gtk.Window` not `GdkWindow` directly
   - Proper `Gdk.Display` and `Gdk.Monitor` usage
   - No hardcoded screen dimensions

5. **No Deprecated Widgets:**
   - ✅ Use `Gtk.Grid` instead of `Gtk.Table`
   - ✅ Use `Gtk.Box` with orientation instead of `Gtk.HBox`/`Gtk.VBox`
   - ✅ Use `Gtk.HeaderBar` for modern toolbars
   - ✅ Use `Gtk.Popover` instead of `Gtk.Menu` where appropriate
   - ✅ Use `Gio.SimpleAction` for actions
   - ❌ Avoid `Gtk.Stock` constants (use icon names)
   - ❌ Avoid `Gtk.UIManager` (use `Gtk.Builder` + `Gio.Menu`)
   - ❌ Avoid `Gtk.Alignment` (use widget properties)

---

## �🎯 **Design Goals**

1. **Universal Access:** All models can use thermodynamics (not just SBML)
2. **Central Configuration:** One place to set pH, temperature, tolerance
3. **Validation On-Demand:** User triggers validation when needed
4. **Integration:** SBML import uses this category instead of embedded validation
5. **Topology Upgrade:** Replace basic analyzer with real thermodynamics

---

## 📐 **Architecture Overview**

```
┌─────────────────────────────────────────────────────────────┐
│                    DocumentModel                            │
│  • thermodynamic_settings (pH, T, tolerance, etc.)         │
│  • compound_mappings (place_id → KEGG/ChEBI)               │
│  • Persisted with .shy file                                 │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ reads settings
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         Pathway Operations Panel                            │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  THERMODYNAMICS (NEW - ALL CAPS)                    │   │
│  │  ────────────────────────────────────────────────   │   │
│  │  Settings Section:                                  │   │
│  │    • Preset selector                                │   │
│  │    • pH, Temperature, Ionic Strength sliders        │   │
│  │    • Tolerance slider                               │   │
│  │    • Enable/Disable checkbox                        │   │
│  │                                                      │   │
│  │  Validation Section:                                │   │
│  │    • [Validate Current Model] button                │   │
│  │    • Status: "Last validated: 2 hours ago"          │   │
│  │    • Results summary (✓12 valid, ⚠3 warnings)      │   │
│  │                                                      │   │
│  │  Compound Mapping Section:                          │   │
│  │    • TreeView: Place → KEGG/ChEBI mapping           │   │
│  │    • [Auto-map from labels] button                  │   │
│  │    • [Import mappings from SBML] button             │   │
│  │    • Manual edit capability                         │   │
│  └─────────────────────────────────────────────────────┘   │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ triggers validation
                       ▼
┌─────────────────────────────────────────────────────────────┐
│    ThermodynamicSimulationValidator                         │
│  • Reads document.thermodynamic_settings                    │
│  • Uses GibbsCalculator + CompoundResolver                  │
│  • Validates reversible reactions                           │
│  • Stores results in document.metadata                      │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       │ results displayed in
                       ▼
┌─────────────────────────────────────────────────────────────┐
│    Report Panel → THERMODYNAMICS (ALL CAPS)                 │
│  • Enhanced statistics dashboard                            │
│  • Settings banner showing active configuration             │
│  • Export to CSV/JSON                                       │
│  • Action bar (re-validate, copy, help)                     │
│  • Link back to Pathway Operations for settings             │
└─────────────────────────────────────────────────────────────┘
                       │
                       IOLOGICAL ANALYSIS (ALL CAPS)          │
│  • Replace basic ThermodynamicAnalyzer with adapter         │
│  • Display real ΔG values and K_eq                          │
│  • Use cached validation results from Report Panel──────────┐
│    Topology Panel → Biological Analysis                     │
│  • Replace basic ThermodynamicAnalyzer                      │
│  • Use cached validation results                            │
│  • Or trigger on-demand validation                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📋 **Phase 1: Core Infrastructure (Priority 1)**

### **1.1 Store Compound Mappings in DocumentModel**

**Why:** Need persistent place → compound_id mapping for any model type

**Changes to `document_model.py`:**
```python
def __init__(self):
    # ... existing code ...
    self.thermodynamic_settings = self._get_default_thermodynamic_settings()
    
    # NEW: Store compound mappings and validation results
    self.compound_mappings = {}  # {place_id: compound_id (KEGG/ChEBI)}
    self.thermodynamic_validation_results = None  # Cache last validation
```

**Serialization:**
```python
def to_dict(self):
    return {
        # ... existing ...
        "thermodynamic_settings": self.thermodynamic_settings,
        "compound_mappings": self.compound_mappings,  # NEW
        # validation_results stored in metadata, not serialized directly
    }
```

**Files:**
- `src/shypn/data/canvas/document_model.py` ✅ (partially done, need to add mappings)

---

### **1.2 Update ThermodynamicSimulationValidator to Use Document**

**Current:** Hardcoded pH=7.0, temperature=298.15

**New:** Read from document

**Changes to `simulation_integration.py`:**
```python
class ThermodynamicSimulationValidator:
    def __init__(
        self,
        document=None,  # NEW parameter
        tolerance: float = None,
        enable_web: bool = False,
        emit_warnings: bool = True
    ):
        # Read from document if provided
        if document and hasattr(document, 'thermodynamic_settings'):
            settings = document.thermodynamic_settings
            self.default_ph = settings.get('ph', 7.0)
            self.default_temperature = settings.get('temperature', 298.15)
            self.default_ionic_strength = settings.get('ionic_strength', 0.1)
            
            # Use document tolerance if not explicitly overridden
            if tolerance is None:
                tolerance = settings.get('tolerance', 0.5)
            
            self.enabled = settings.get('enable_validation', True)
        else:
            # Fallback to defaults
            self.default_ph = 7.0
            self.default_temperature = 298.15
            self.default_ionic_strength = 0.1
            self.enabled = True
        
        # ... rest of init ...
        self.document = document  # Keep reference
    
    def validate_reversible_reaction(
        self,
        reaction_id: str,
        k_forward: float,
        k_reverse: float,
        reactants: Dict[str, int],
        products: Dict[str, int],
        ph: float = None,  # NEW: optional, uses document default
        temperature: float = None,  # NEW: optional, uses document default
        suppress_warnings: bool = False
    ) -> ThermodynamicValidation:
        # Use document defaults if not provided
        if ph is None:
            ph = self.default_ph
        if temperature is None:
            temperature = self.default_temperature
        
        # ... rest of method ...
```

**Files:**
- `src/shypn/thermodynamics/simulation_integration.py`

---

### **1.3 Create Modular Compound Mapping System**

**OOP Architecture:**

**Base class: `src/shypn/thermodynamics/mappers/base_mapper.py`**
```python
"""Base class for compound mapping strategies."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, List

class CompoundMapperBase(ABC):
    """Abstract base for place → compound ID mapping strategies."""
    
    @abstractmethod
    def map_places(self, places: List) -> Dict[str, str]:
        """Map places to compound IDs.
        
        Args:
            places: List of Place objects
            
        Returns:
            {place_id: compound_id}
        """
        pass
    
    @abstractmethod
    def get_confidence(self, place_id: str) -> float:
        """Get mapping confidence score (0.0-1.0)."""
        pass
```

**Subclass 1: `src/shypn/thermodynamics/mappers/label_matcher.py`**
```python
"""Label-based compound matching."""

from .base_mapper import CompoundMapperBase
from shypn.thermodynamics.compound_resolver import CompoundResolver
import re

class LabelBasedMapper(CompoundMapperBase):
    """Maps compounds by parsing place labels."""
    
    def __init__(self):
        self.resolver = CompoundResolver()
        self._common_mappings = self._load_common_mappings()
    
    def map_places(self, places: List) -> Dict[str, str]:
        """Extract compound IDs from labels."""
        mappings = {}
        
        for place in places:
            # Try direct ID extraction
            compound_id = self._extract_id_from_label(place.label)
            
            if not compound_id:
                # Try fuzzy matching
                compound_id = self._fuzzy_match(place.label)
            
            if compound_id:
                mappings[place.id] = compound_id
        
        return mappings
    
    def get_confidence(self, place_id: str) -> float:
        """0.9 for direct match, 0.6 for fuzzy."""
        # Implementation
        pass
    
    def _extract_id_from_label(self, label: str) -> Optional[str]:
        """Extract KEGG/ChEBI ID using regex."""
        # KEGG: C00002
        kegg_match = re.search(r'\bC\d{5}\b', label)
        if kegg_match:
            return kegg_match.group(0)
        
        # ChEBI: CHEBI:12345
        chebi_match = re.search(r'CHEBI:(\d+)', label, re.IGNORECASE)
        if chebi_match:
            return f"CHEBI:{chebi_match.group(1)}"
        
        return None
    
    def _fuzzy_match(self, label: str) -> Optional[str]:
        """Fuzzy match against common compounds."""
        label_clean = label.lower().strip()
        return self._common_mappings.get(label_clean)
    
    def _load_common_mappings(self) -> Dict[str, str]:
        """Load common name → ID mappings."""
        return {
            'atp': 'C00002',
            'adp': 'C00008',
            'amp': 'C00020',
            'nadh': 'C00004',
            'nad+': 'C00003',
            'nadph': 'C00005',
            'glucose': 'C00031',
            'pyruvate': 'C00022',
            'h2o': 'C00001',
            'water': 'C00001',
            # Load from JSON file in production
        }
```

**Subclass 2: `src/shypn/thermodynamics/mappers/sbml_annotator.py`**
```python
"""SBML annotation-based mapping."""

from .base_mapper import CompoundMapperBase

class SBMLAnnotationMapper(CompoundMapperBase):
    """Extracts mappings from SBML species annotations."""
    
    def __init__(self, document):
        self.document = document
    
    def map_places(self, places: List) -> Dict[str, str]:
        """Extract from SBML metadata."""
        if not self.document or not hasattr(self.document, 'metadata'):
            return {}
        
        sbml_species = self.document.metadata.get('sbml_species', {})
        mappings = {}
        
        for place in places:
            species_data = sbml_species.get(place.name) or sbml_species.get(place.id)
            if not species_data:
                continue
            
            annotations = species_data.get('annotations', {})
            
            # Prefer KEGG
            if 'kegg.compound' in annotations:
                mappings[place.id] = annotations['kegg.compound']
            # Fall back to ChEBI
            elif 'chebi' in annotations:
                mappings[place.id] = f"CHEBI:{annotations['chebi']}"
        
        return mappings
    
    def get_confidence(self, place_id: str) -> float:
        """High confidence for SBML annotations."""
        return 1.0
```

**Facade: `src/shypn/thermodynamics/mappers/compound_mapper_service.py`**
```python
"""Service facade for compound mapping."""

from typing import Dict, List, Tuple
from .label_matcher import LabelBasedMapper
from .sbml_annotator import SBMLAnnotationMapper

class CompoundMapperService:
    """Orchestrates multiple mapping strategies."""
    
    def __init__(self, document=None):
        self.document = document
        self.strategies = [
            SBMLAnnotationMapper(document),  # Try SBML first (high confidence)
            LabelBasedMapper(),              # Fall back to label matching
        ]
    
    def map_all_places(self, places: List) -> Tuple[Dict[str, str], Dict[str, float]]:
        """Apply all strategies, return mappings and confidence scores.
        
        Returns:
            (mappings, confidences) where:
            - mappings: {place_id: compound_id}
            - confidences: {place_id: confidence_score}
        """
        mappings = {}
        confidences = {}
        
        for strategy in self.strategies:
            strategy_mappings = strategy.map_places(places)
            
            for place_id, compound_id in strategy_mappings.items():
                if place_id not in mappings:  # First match wins
                    mappings[place_id] = compound_id
                    confidences[place_id] = strategy.get_confidence(place_id)
        
        return mappings, confidences
    
    def suggest_missing_mappings(self, places: List, existing_mappings: Dict[str, str]) -> Dict[str, str]:
        """Suggest mappings for unmapped places."""
        unmapped_places = [p for p in places if p.id not in existing_mappings]
        suggestions, _ = self.map_all_places(unmapped_places)
        return suggestions
```

**Files (NEW):**
- `src/shypn/thermodynamics/mappers/__init__.py`
- `src/shypn/thermodynamics/mappers/base_mapper.py` (base class)
- `src/shypn/thermodynamics/mappers/label_matcher.py` (strategy 1)
- `src/shypn/thermodynamics/mappers/sbml_annotator.py` (strategy 2)
- `src/shypn/thermodynamics/mappers/compound_mapper_service.py` (facade)

---

## 📋 **Phase 2: UI - THERMODYNAMICS Category (Priority 1)**

### **2.1 Create Modular UI Architecture**

**OOP Structure:**

**Base widget: `src/shypn/ui/panels/pathway_operations/thermodynamics/base_section.py`**
```python
"""Base class for thermodynamics UI sections."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
from abc import ABC, abstractmethod

class ThermodynamicsSectionBase(ABC):
    """Base class for sections within THERMODYNAMICS category."""
    
    def __init__(self, model_canvas=None):
        self.model_canvas = model_canvas
        self.document = None
    
    @abstractmethod
    def build_widget(self) -> Gtk.Widget:
        """Build and return the section widget."""
        pass
    
    @abstractmethod
    def refresh_data(self):
        """Refresh display from document model."""
        pass
    
    @abstractmethod
    def save_to_document(self):
        """Save current UI state to document.
    """Maps place labels to KEGG/ChEBI compound IDs.
    
    Used for models where compounds aren't explicitly tagged with IDs.
    """
    
    def __init__(self, document=None):
        self.document = document
        self.compound_resolver = CompoundResolver()
    
    def auto_map_from_labels(self, places: List) -> Dict[str, str]:
        """Automatically map places based on label matching.
        
        Returns:
            {place_id: compound_id}
        """
        mappings = {}
        
        for place in places:
            # Try to extract compound ID from label
            compound_id = self._extract_compound_id(place.label)
            
            if compound_id:
                mappings[place.id] = compound_id
            else:
                # Try fuzzy matching against common compounds
                compound_id = self._fuzzy_match(place.label)
                if compound_id:
                    mappings[place.id] = compound_id
        
        return mappings
    
    def _extract_compound_id(self, label: str) -> Optional[str]:
        """Extract KEGG C-number or ChEBI ID from label."""
        # KEGG pattern: C00002, C12345
        kegg_match = re.search(r'C\d{5}', label)
        if kegg_match:
            return kegg_match.group(0)
        
        # ChEBI pattern: CHEBI:12345, ChEBI:12345
        chebi_match = re.search(r'(?:CHEBI|ChEBI):(\d+)', label, re.IGNORECASE)
        if chebi_match:
            return f"CHEBI:{chebi_match.group(1)}"
        
        return None
    
    def _fuzzy_match(self, label: str) -> Optional[str]:
        """Fuzzy match label to common compounds."""
        # Use compound resolver's name matching
        label_clean = label.lower().strip()
        
        # Common biochemical compounds
        common_mappings = {
            'atp': 'C00002',
            'adp': 'C00008',
            'amp': 'C00020',
            'nadh': 'C00004',
            'nad+': 'C00003',
            'nadph': 'C00005',
            'nadp+': 'C00006',
            'glucose': 'C00031',
            'pyruvate': 'C00022',
            # ... more common compounds
        }
        
        return common_mappings.get(label_clean)
    
    def import_from_sbml_metadata(self) -> Dict[str, str]:
        """Import compound mappings from SBML metadata if available."""
        if not self.document or not hasattr(self.document, 'metadata'):
            return {}
        
        # Check if document has SBML species annotations
        sbml_species = self.document.metadata.get('sbml_species', {})
        
        mappings = {}
        for place in self.document.places:
            # Try to find corresponding SBML species
            species_data = sbml_species.get(place.name) or sbml_species.get(place.id)
            if species_data:
                # Extract compound ID from annotations
                annotations = species_data.get('annotations', {})
                
                # Check for KEGG annotation
                if 'kegg.compound' in annotations:
                    mappings[place.id] = annotations['kegg.compound']
                # Check for ChEBI annotation
                elif 'chebi' in annotations:
                    mappings[place.id] = f"CHEBI:{annotations['chebi']}"
        
        return mappings
```

**Files:**
- `src/shypn/thermodynamics/place_compound_mapper.py` (NEW)

---

## 📋 **Phase 2: UI - Thermodynamics Category (Priority 1)**

### **2.1 Create Thermodynamics Category**

**New file: `src/shypn/ui/panels/pathway_operations/thermodynamics_category.py`:**

```python
"""Thermodynamics configuration and validation category."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib

from shypn.thermodynamics import ThermodynamicSimulationValidator
from shypn.thermodynamics.place_compound_mapper import PlaceCompoundMapper


class ThermodynamicsCategory:
    """Thermodynamics configuration and validation for any model type.
    
    Provides:
    1. Settings panel (pH, temperature, tolerance, presets)
    2. Compound mapping editor (place → KEGG/ChEBI)
    3. Validation trigger and results display
    4. Integration with simulation and topology analyzers
    """
    
    def __init__(self, model_canvas=None):
        self.model_canvas = model_canvas
        self.document = None
        self.validator = None
        self.mapper = None
        
        # UI widgets (created in _build_ui)
        self.preset_combo = None
        self.ph_scale = None
        self.temp_entry = None
        self.ionic_scale = None
        self.tolerance_scale = None
        self.enable_check = None
        
        self.mapping_store = None
        self.mapping_treeview = None
        
        self.status_label = None
        self.results_label = None
    
    def build_ui(self) -> Gtk.Expander:
        """Build and return the category UI."""
        # Use ALL CAPS for category title consistency
        expander = Gtk.Expander(label="THERMODYNAMICS")
        expander.set_expanded(False)
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_start(12)
        main_box.set_margin_end(12)
        main_box.set_margin_top(12)
        main_box.set_margin_bottom(12)
        
        # === INFO HEADER ===
        info_label = Gtk.Label()
        info_laig><b>THERMODYNAMICS</b></big>\n"
            "<small>Configure conditions and validate reversible reactions</small>
            "Configure conditions and validate reversible reactions"
        )
        info_label.set_xalign(0)
        main_box.pack_start(info_label, False, False, 0)
        
        # === SETTINGS SECTION ===
        settings_frame = self._build_settings_section()
        main_box.pack_start(settings_frame, False, False, 0)
        
        # === COMPOUND MAPPING SECTION ===
        mapping_frame = self._build_mapping_section()
        main_box.pack_start(mapping_frame, True, True, 0)
        
        # === VALIDATION SECTION ===
        validation_frame = self._build_validation_section()
        main_box.pack_start(validation_frame, False, False, 0)
        
        expander.add(main_box)
        return expander
    
    def _build_settings_section(self) -> Gtk.Frame:
        """Build settings configuration frame."""
        frame = Gtk.Frame()
        frame.set_label("Settings")
        
        grid = Gtk.Grid()
        grid.set_row_spacing(6)
        grid.set_column_spacing(12)
        grid.set_margin_start(12)
        grid.set_margin_end(12)
        grid.set_margin_top(6)
        grid.set_margin_bottom(6)
        
        row = 0
        
        # Preset selector
        label = Gtk.Label(label="Preset:")
        label.set_xalign(0)
        grid.attach(label, 0, row, 1, 1)
        
        self.preset_combo = Gtk.ComboBoxText()
        for preset_name, preset_data in self._get_presets().items():
            self.preset_combo.append(preset_name, preset_data['description'])
        self.preset_combo.set_active(0)
        self.preset_combo.connect('changed', self._on_preset_changed)
        grid.attach(self.preset_combo, 1, row, 2, 1)
        row += 1
        
        # pH scale
        label = Gtk.Label(label="pH:")
        label.set_xalign(0)
        grid.attach(label, 0, row, 1, 1)
        
        self.ph_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 2.0, 10.0, 0.1)
        self.ph_scale.set_value(7.0)
        self.ph_scale.set_hexpand(True)
        self.ph_scale.set_draw_value(True)
        self.ph_scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.ph_scale.connect('value-changed', self._on_setting_changed)
        grid.attach(self.ph_scale, 1, row, 2, 1)
        row += 1
        
        # Temperature entry
        label = Gtk.Label(label="Temperature:")
        label.set_xalign(0)
        grid.attach(label, 0, row, 1, 1)
        
        temp_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.temp_entry = Gtk.SpinButton()
        self.temp_entry.set_range(0, 150)
        self.temp_entry.set_increments(1, 10)
        self.temp_entry.set_value(25)
        self.temp_entry.connect('value-changed', self._on_setting_changed)
        temp_box.pack_start(self.temp_entry, False, False, 0)
        
        temp_label = Gtk.Label(label="°C")
        temp_box.pack_start(temp_label, False, False, 0)
        
        # Show Kelvin equivalent
        self.temp_kelvin_label = Gtk.Label(label="(298.15 K)")
        self.temp_kelvin_label.set_sensitive(False)
        temp_box.pack_start(self.temp_kelvin_label, False, False, 0)
        
        grid.attach(temp_box, 1, row, 2, 1)
        row += 1
        
        # Ionic strength scale
        label = Gtk.Label(label="Ionic Strength:")
        label.set_xalign(0)
        grid.attach(label, 0, row, 1, 1)
        
        self.ionic_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.01, 0.5, 0.01)
        self.ionic_scale.set_value(0.1)
        self.ionic_scale.set_hexpand(True)
        self.ionic_scale.set_draw_value(True)
        self.ionic_scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.ionic_scale.set_digits(2)
        self.ionic_scale.connect('value-changed', self._on_setting_changed)
        grid.attach(self.ionic_scale, 1, row, 1, 1)
        
        ionic_unit = Gtk.Label(label="M")
        grid.attach(ionic_unit, 2, row, 1, 1)
        row += 1
        
        # Tolerance scale
        label = Gtk.Label(label="Tolerance:")
        label.set_xalign(0)
        grid.attach(label, 0, row, 1, 1)
        
        self.tolerance_scale = Gtk.Scale.new_with_range(Gtk.Orientation.HORIZONTAL, 0.1, 1.0, 0.05)
        self.tolerance_scale.set_value(0.5)
        self.tolerance_scale.set_hexpand(True)
        self.tolerance_scale.set_draw_value(True)
        self.tolerance_scale.set_value_pos(Gtk.PositionType.RIGHT)
        self.tolerance_scale.set_digits(2)
        
        # Add marks
        self.tolerance_scale.add_mark(0.1, Gtk.PositionType.BOTTOM, "±10%")
        self.tolerance_scale.add_mark(0.5, Gtk.PositionType.BOTTOM, "±50%")
        self.tolerance_scale.add_mark(1.0, Gtk.PositionType.BOTTOM, "±100%")
        
        self.tolerance_scale.connect('value-changed', self._on_setting_changed)
        grid.attach(self.tolerance_scale, 1, row, 2, 1)
        row += 1
        
        # Enable checkbox
        self.enable_check = Gtk.CheckButton(label="Enable thermodynamic validation")
        self.enable_check.set_active(True)
        self.enable_check.connect('toggled', self._on_setting_changed)
        grid.attach(self.enable_check, 0, row, 3, 1)
        row += 1
        
        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        apply_btn = Gtk.Button(label="Apply Settings")
        apply_btn.connect('clicked', self._on_apply_settings)
        button_box.pack_start(apply_btn, False, False, 0)
        
        reset_btn = Gtk.Button(label="Reset to Preset")
        reset_btn.connect('clicked', self._on_reset_to_preset)
        button_box.pack_start(reset_btn, False, False, 0)
        
        grid.attach(button_box, 0, row, 3, 1)
        
        frame.add(grid)
        return frame
    
    def _build_mapping_section(self) -> Gtk.Frame:
        """Build compound mapping editor frame."""
        frame = Gtk.Frame()
        frame.set_label("Compound Mappings")
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        
        # Info label
        info = Gtk.Label()
        info.set_markup("<small>Map places to KEGG/ChEBI compound IDs for thermodynamic calculations</small>")
        info.set_xalign(0)
        box.pack_start(info, False, False, 0)
        
        # TreeView with scrolling
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(200)
        scrolled.set_max_content_height(400)
        
        # ListStore: place_id, place_label, compound_id, compound_name, has_data
        self.mapping_store = Gtk.ListStore(str, str, str, str, bool)
        
        self.mapping_treeview = Gtk.TreeView(model=self.mapping_store)
        self.mapping_treeview.set_enable_search(True)
        self.mapping_treeview.set_search_column(1)  # Search by place label
        
        # Columns
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Place ID", renderer, text=0)
        column.set_sort_column_id(0)
        self.mapping_treeview.append_column(column)
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Place Label", renderer, text=1)
        column.set_sort_column_id(1)
        column.set_expand(True)
        self.mapping_treeview.append_column(column)
        
        # Editable compound ID column
        renderer = Gtk.CellRendererText()
        renderer.set_property('editable', True)
        renderer.connect('edited', self._on_compound_id_edited)
        column = Gtk.TreeViewColumn("Compound ID", renderer, text=2)
        column.set_sort_column_id(2)
        self.mapping_treeview.append_column(column)
        
        renderer = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn("Compound Name", renderer, text=3)
        column.set_expand(True)
        self.mapping_treeview.append_column(column)
        
        # Status indicator
        renderer = Gtk.CellRendererPixbuf()
        column = Gtk.TreeViewColumn("Data", renderer)
        column.set_cell_data_func(renderer, self._render_data_status)
        self.mapping_treeview.append_column(column)
        
        scrolled.add(self.mapping_treeview)
        box.pack_start(scrolled, True, True, 0)
        
        # Buttons
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        
        auto_btn = Gtk.Button(label="Auto-map from Labels")
        auto_btn.connect('clicked', self._on_auto_map)
        button_box.pack_start(auto_btn, False, False, 0)
        
        import_btn = Gtk.Button(label="Import from SBML Metadata")
        import_btn.connect('clicked', self._on_import_sbml_mappings)
        button_box.pack_start(import_btn, False, False, 0)
        
        clear_btn = Gtk.Button(label="Clear All")
        clear_btn.connect('clicked', self._on_clear_mappings)
        button_box.pack_start(clear_btn, False, False, 0)
        
        box.pack_start(button_box, False, False, 0)
        
        frame.add(box)
        return frame
    
    def _build_validation_section(self) -> Gtk.Frame:
        """Build validation trigger and results frame."""
        frame = Gtk.Frame()
        frame.set_label("Validation")
        
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        
        # Status
        self.status_label = Gtk.Label()
        self.status_label.set_markup("<i>No validation performed yet</i>")
        self.status_label.set_xalign(0)
        box.pack_start(self.status_label, False, False, 0)
        
        # Results summary
        self.results_label = Gtk.Label()
        self.results_label.set_xalign(0)
        self.results_label.set_line_wrap(True)
        box.pack_start(self.results_label, False, False, 0)
        
        # Validate button
        validate_btn = Gtk.Button(label="Validate Current Model")
        validate_btn.connect('clicked', self._on_validate)
        box.pack_start(validate_btn, False, False, 0)
        
        # Link to report
        link_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        link_label = Gtk.Label(label="View detailed results in")
        link_box.pack_start(link_label, False, False, 0)
        
        report_link = Gtk.LinkButton.new_with_label(
            "",  # No actual URL, handled by clicked signal
            "Report Panel"
        )
        report_link.connect('clicked', self._on_open_report_panel)
        link_box.pack_start(report_link, False, False, 0)
        
        box.pack_start(link_box, False, False, 0)
        
        frame.add(box)
        return frame
    
    # ... Event handlers and helper methods ...
    # (Would continue with implementation of all the _on_* methods)
```

**Files:**
- `src/shypn/ui/panels/pathway_operations/thermodynamics_category.py` (NEW, ~800 lines)

---

### **2.2 Register Category in PathwayOperationsPanel**

**Changes to `pathway_operations_panel.py`:**
```python
from shypn.ui.panels.pathway_operations.thermodynamics_category import ThermodynamicsCategory

class PathwayOperationsPanel:
    def _build_categories(self):
        # ... existing categories ...
        
        # Thermodynamics Category (NEW - universal for all models)
        thermo_category = ThermodynamicsCategory(model_canvas=self.model_canvas)
        thermo_expander = thermo_category.build_ui()
        self.categories_box.pack_start(thermo_expander, False, False, 0)
        self.categories['thermodynamics'] = thermo_category
```

**Files:**
- `src/shypn/ui/panels/pathway_operations_panel.py`

---

## 📋 **Phase 3: Refactor SBML Integration (Priority 2)**

### **3.1 Remove Embedded Thermodynamic Section from SBML Category**

**Current state:** SBML category has its own `_build_thermodynamic_section()`

**New state:** SBML shows link to Thermodynamics category

**Changes to `sbml_category.py`:**
```python
# REMOVE _build_thermodynamic_section() method
# REMOVE thermodynamic_expander, thermodynamic_status widgets

# ADD link to thermodynamics category
def _build_import_info_section(self):
    # ... existing code ...
    
    # Add thermodynamics link
    thermo_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
    thermo_label = Gtk.Label(label="For thermodynamic validation, see")
    thermo_box.pack_start(thermo_label, False, False, 0)
    
    thermo_link = Gtk.LinkButton.new_with_label("", "Thermodynamics category")
    thermo_link.connect('clicked', self._on_open_thermodynamics_category)
    thermo_box.pack_start(thermo_link, False, False, 0)
    
    return thermo_box
```

**Changes to SBML import workflow:**
```python
def _on_import_clicked(self, button):
    # ... import SBML ...
    
    # After successful import:
    # 1. Extract compound mappings from SBML annotations
    mappings = self._extract_compound_mappings_from_sbml(sbml_doc)
    document.compound_mappings.update(mappings)
    
    # 2. Optionally trigger auto-validation
    if self._should_auto_validate():
        self._trigger_thermodynamic_validation()
    
    # 3. Show notification with link to Thermodynamics category
    self._show_notification_with_link(
        "Import complete. Compound mappings extracted.",
        "Configure validation in Thermodynamics category"
    )
```

**Files:**
- `src/shypn/ui/panels/pathway_operations/sbml_category.py`

---

### **3.2 Update SBML Parser to Store Compound Mappings**

**Changes to `sbml_parser.py`:**
```python
class SBMLParser:
    def parse(self, sbml_file, document):
        # ... existing parsing ...
        
        # Extract compound annotations
        compound_mappings = self._extract_compound_annotations(sbml_model)
        document.compound_mappings = compound_mappings
        
        # Store SBML metadata (for later reference)
        if not hasattr(document, 'metadata'):
            document.metadata = {}
        
        document.metadata['sbml_species'] = self._get_species_metadata(sbml_model)
        document.metadata['sbml_reactions'] = self._get_reactions_metadata(sbml_model)
    
    def _extract_compound_annotations(self, sbml_model) -> Dict[str, str]:
        """Extract compound ID annotations from SBML species.
        
        Returns:
            {place_id: compound_id}
        """
        mappings = {}
        
        for species in sbml_model.getListOfSpecies():
            species_id = species.getId()
            
            # Check for KEGG annotation
            kegg_id = self._get_annotation_value(species, 'kegg.compound')
            if kegg_id:
                mappings[species_id] = kegg_id
                continue
            
            # Check for ChEBI annotation
            chebi_id = self._get_annotation_value(species, 'chebi')
            if chebi_id:
                mappings[species_id] = f"CHEBI:{chebi_id}"
        
        return mappings
```

**Files:**
- `src/shypn/data/pathway/sbml_parser.py`

---

## 📋 **Phase 4: Update Topology Panel (Priority 2)**

### **4.1 Replace Basic ThermodynamicAnalyzer**

**Option 1: Adapter Pattern (Recommended)**

Create adapter that wraps `ThermodynamicSimulationValidator` with topology analyzer interface:

**New file: `src/shypn/topology/biological/thermodynamics_adapter.py`:**
```python
"""Adapter for advanced thermodynamics module to topology analyzer interface."""

from shypn.topology.base.topology_analyzer import TopologyAnalyzer
from shypn.topology.base.analysis_result import AnalysisResult
from shypn.thermodynamics import ThermodynamicSimulationValidator


class ThermodynamicAnalyzerAdapter(TopologyAnalyzer):
    """Adapter that uses real thermodynamics module for topology analysis.
    
    Replaces the basic heuristic analyzer with production thermodynamics.
    """
    
    def __init__(self, model: Any):
        super().__init__(model)
        self.validator = ThermodynamicSimulationValidator(
            document=getattr(model, 'document', None)
        )
    
    def analyze(self, **kwargs) -> AnalysisResult:
        """Perform thermodynamic validation using production module."""
        
        # Check if compound mappings exist
        if not hasattr(self.model, 'document') or \
           not self.model.document.compound_mappings:
            return self._no_mappings_result()
        
        # Get reversible reactions from model
        reversible_reactions = self._find_reversible_reactions()
        
        if not reversible_reactions:
            return self._no_reversible_reactions_result()
        
        # Validate each reversible reaction
        results = []
        for reaction in reversible_reactions:
            validation = self.validator.validate_reversible_reaction(
                reaction_id=reaction['transition_id'],
                k_forward=reaction['k_forward'],
                k_reverse=reaction['k_reverse'],
                reactants=reaction['reactants'],
                products=reaction['products']
            )
            results.append(validation)
        
        # Format results for topology display
        return self._format_results(results)
    
    def _find_reversible_reactions(self) -> List[Dict]:
        """Extract reversible reactions from model."""
        reactions = []
        
        for transition in self.model.transitions:
            if not hasattr(transition, 'reversible') or not transition.reversible:
                continue
            
            # Get k_forward and k_reverse from transition properties
            k_forward = getattr(transition, 'rate_forward', None)
            k_reverse = getattr(transition, 'rate_reverse', None)
            
            if k_forward is None or k_reverse is None:
                continue
            
            # Map places to compounds using document mappings
            reactants = self._get_compound_stoichiometry(transition, input=True)
            products = self._get_compound_stoichiometry(transition, input=False)
            
            reactions.append({
                'transition_id': transition.id,
                'k_forward': k_forward,
                'k_reverse': k_reverse,
                'reactants': reactants,
                'products': products
            })
        
        return reactions
    
    def _get_compound_stoichiometry(self, transition, input: bool) -> Dict[str, int]:
        """Get compound stoichiometry for transition."""
        stoich = {}
        document = self.model.document
        
        for arc in self.model.arcs:
            if input and arc.target_id == transition.id:
                place_id = arc.source_id
            elif not input and arc.source_id == transition.id:
                place_id = arc.target_id
            else:
                continue
            
            # Map place to compound
            compound_id = document.compound_mappings.get(place_id)
            if compound_id:
                stoich[compound_id] = arc.weight
        
        return stoich
```

**Changes to `biological_category.py`:**
```python
# REPLACE import
from shypn.topology.biological.thermodynamics_adapter import ThermodynamicAnalyzerAdapter

def _get_analyzers(self):
    return {
        # ... other analyzers ...
        'thermodynamics': ThermodynamicAnalyzerAdapter,  # Use adapter instead
    }
```

**Files:**
- `src/shypn/topology/biological/thermodynamics_adapter.py` (NEW)
- `src/shypn/ui/panels/topology/biological_category.py`
- `src/shypn/topology/biological/thermodynamics.py` (DEPRECATE with comment)

---

## 📋 **Phase 5: Enhance Report Panel Integration (Priority 2)**

### **5.1 Upgrade Thermodynamic Validation Category in Report Panel**

**Objective:** Make thermodynamics a first-class citizen in the Report Panel with comprehensive display

**Current Issues:**
- Results are read-only with no context about settings used
- No indication of model's thermodynamic configuration
- Missing summary statistics and trends
- No export capability

**Enhanced Design:**

```python
# src/shypn/ui/panels/report/thermodynamic_validation_category.py

class ThermodynamicValidationCategory(BaseReportCategory):
    """Enhanced thermodynamic validation report with full context."""
    
    def _build_content(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        
        # === SETTINGS BANNER (NEW) ===
        settings_banner = self._build_settings_banner()
        box.pack_start(settings_banner, False, False, 0)
        
        # === STATUS INDICATOR (Enhanced) ===
        status_box = self._build_status_indicator()
        box.pack_start(status_box, False, False, 0)
        
        # === STATISTICS DASHBOARD (NEW) ===
        stats_frame = self._build_statistics_dashboard()
        box.pack_start(stats_frame, False, False, 0)
        
        # === VIOLATIONS TABLE (Enhanced with filtering) ===
        violations_section = self._build_violations_section()
        box.pack_start(violations_section, True, True, 0)
        
        # === WARNINGS TABLE (Enhanced with filtering) ===
        warnings_section = self._build_warnings_section()
        box.pack_start(warnings_section, True, True, 0)
        
        # === VALID REACTIONS SUMMARY (NEW) ===
        valid_section = self._build_valid_reactions_section()
        box.pack_start(valid_section, False, False, 0)
        
        # === ACTION BUTTONS (NEW) ===
        action_bar = self._build_action_bar()
        box.pack_start(action_bar, False, False, 0)
        
        return box
    
    def _build_settings_banner(self) -> Gtk.Widget:
        """Display current model's thermodynamic settings.
        
        Shows:
        - Active preset or "Custom"
        - pH, Temperature, Ionic Strength
        - Tolerance
        - Last validation timestamp
        """
        frame = Gtk.Frame()
        frame.set_label("Active Settings")
        frame.set_shadow_type(Gtk.ShadowType.IN)
        
        grid = Gtk.Grid()
        grid.set_row_spacing(3)
        grid.set_column_spacing(12)
        grid.set_margin_start(12)
        grid.set_margin_end(12)
        grid.set_margin_top(6)
        grid.set_margin_bottom(6)
        
        # Get document settings
        doc = self._get_document()
        if not doc or not hasattr(doc, 'thermodynamic_settings'):
            label = Gtk.Label(label="⚠️ No thermodynamic settings found")
            grid.attach(label, 0, 0, 4, 1)
            frame.add(grid)
            return frame
        
        settings = doc.thermodynamic_settings
        
        row = 0
        
        # Preset indicator
        preset = settings.get('preset', 'custom')
        preset_label = Gtk.Label()
        preset_label.set_markup(f"<b>Preset:</b> {preset.replace('_', ' ').title()}")
        preset_label.set_xalign(0)
        grid.attach(preset_label, 0, row, 2, 1)
        
        # Enable status
        enabled = settings.get('enable_validation', True)
        status_icon = "✓" if enabled else "✗"
        status_label = Gtk.Label()
        status_label.set_markup(f"<b>Validation:</b> {status_icon} {'Enabled' if enabled else 'Disabled'}")
        status_label.set_xalign(0)
        grid.attach(status_label, 2, row, 2, 1)
        row += 1
        
        # Conditions row 1
        ph_label = Gtk.Label(label=f"pH: {settings.get('ph', 7.0):.1f}")
        ph_label.set_xalign(0)
        grid.attach(ph_label, 0, row, 1, 1)
        
        temp_c = settings.get('temperature', 298.15) - 273.15
        temp_label = Gtk.Label(label=f"T: {temp_c:.1f}°C ({settings.get('temperature', 298.15):.2f} K)")
        temp_label.set_xalign(0)
        grid.attach(temp_label, 1, row, 1, 1)
        
        ionic_label = Gtk.Label(label=f"I: {settings.get('ionic_strength', 0.1):.2f} M")
        ionic_label.set_xalign(0)
        grid.attach(ionic_label, 2, row, 1, 1)
        
        tolerance_pct = settings.get('tolerance', 0.5) * 100
        tol_label = Gtk.Label(label=f"Tolerance: ±{tolerance_pct:.0f}%")
        tol_label.set_xalign(0)
        grid.attach(tol_label, 3, row, 1, 1)
        row += 1
        
        # Edit settings link
        link_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        link_icon = Gtk.Label(label="⚙️")
        link_box.pack_start(link_icon, False, False, 0)
        
        settings_link = Gtk.LinkButton.new_with_label(
            "",
            "Edit in Pathway Operations → THERMODYNAMICS"
        )
        settings_link.connect('clicked', self._on_open_thermodynamics_settings)
        link_box.pack_start(settings_link, False, False, 0)
        
        grid.attach(link_box, 0, row, 4, 1)
        
        frame.add(grid)
        return frame
    
    def _build_statistics_dashboard(self) -> Gtk.Widget:
        """Build comprehensive statistics dashboard.
        
        Shows:
        - Total reactions validated
        - Valid count/percentage
        - Warnings count/percentage  
        - Violations count/percentage
        - Missing data count
        - ΔG range (min/max/mean)
        - K_eq range (min/max/mean)
        - Deviation statistics
        """
        frame = Gtk.Frame()
        frame.set_label("Statistics Dashboard")
        
        grid = Gtk.Grid()
        grid.set_row_spacing(6)
        grid.set_column_spacing(24)
        grid.set_margin_start(12)
        grid.set_margin_end(12)
        grid.set_margin_top(6)
        grid.set_margin_bottom(6)
        
        results = self._get_validation_results()
        if not results:
            label = Gtk.Label(label="No validation results available")
            grid.attach(label, 0, 0, 4, 1)
            frame.add(grid)
            return frame
        
        stats = results.get('statistics', {})
        
        # Column 1: Counts
        col1_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        col1_box.pack_start(self._make_stat_label("📊 Validation Summary", bold=True), False, False, 0)
        col1_box.pack_start(self._make_stat_label(f"Total Reactions: {stats.get('total', 0)}"), False, False, 0)
        col1_box.pack_start(self._make_stat_label(f"✓ Valid: {stats.get('valid', 0)} ({self._percentage(stats.get('valid', 0), stats.get('total', 1))}%)"), False, False, 0)
        col1_box.pack_start(self._make_stat_label(f"⚠️ Warnings: {stats.get('warnings', 0)} ({self._percentage(stats.get('warnings', 0), stats.get('total', 1))}%)"), False, False, 0)
        col1_box.pack_start(self._make_stat_label(f"❌ Violations: {stats.get('violations', 0)} ({self._percentage(stats.get('violations', 0), stats.get('total', 1))}%)"), False, False, 0)
        col1_box.pack_start(self._make_stat_label(f"ℹ️ Missing Data: {stats.get('missing_data', 0)}"), False, False, 0)
        grid.attach(col1_box, 0, 0, 1, 1)
        
        # Column 2: Thermodynamic ranges
        col2_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        col2_box.pack_start(self._make_stat_label("🔬 ΔG°' Range (kJ/mol)", bold=True), False, False, 0)
        col2_box.pack_start(self._make_stat_label(f"Minimum: {stats.get('delta_g_min', 'N/A')}"), False, False, 0)
        col2_box.pack_start(self._make_stat_label(f"Maximum: {stats.get('delta_g_max', 'N/A')}"), False, False, 0)
        col2_box.pack_start(self._make_stat_label(f"Mean: {stats.get('delta_g_mean', 'N/A')}"), False, False, 0)
        col2_box.pack_start(self._make_stat_label(f"Std Dev: {stats.get('delta_g_std', 'N/A')}"), False, False, 0)
        grid.attach(col2_box, 1, 0, 1, 1)
        
        # Column 3: K_eq ranges
        col3_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        col3_box.pack_start(self._make_stat_label("⚖️ K_eq Range", bold=True), False, False, 0)
        col3_box.pack_start(self._make_stat_label(f"Minimum: {stats.get('k_eq_min', 'N/A')}"), False, False, 0)
        col3_box.pack_start(self._make_stat_label(f"Maximum: {stats.get('k_eq_max', 'N/A')}"), False, False, 0)
        col3_box.pack_start(self._make_stat_label(f"Log Range: {stats.get('log_k_eq_range', 'N/A')} orders"), False, False, 0)
        grid.attach(col3_box, 2, 0, 1, 1)
        
        # Column 4: Deviation statistics
        col4_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=3)
        col4_box.pack_start(self._make_stat_label("📈 Deviation Analysis", bold=True), False, False, 0)
        col4_box.pack_start(self._make_stat_label(f"Mean Deviation: {stats.get('mean_deviation', 'N/A')}"), False, False, 0)
        col4_box.pack_start(self._make_stat_label(f"Max Deviation: {stats.get('max_deviation', 'N/A')}"), False, False, 0)
        col4_box.pack_start(self._make_stat_label(f"Within Tolerance: {stats.get('within_tolerance_pct', 'N/A')}%"), False, False, 0)
        grid.attach(col4_box, 3, 0, 1, 1)
        
        frame.add(grid)
        return frame
    
    def _build_action_bar(self) -> Gtk.Widget:
        """Build action button bar.
        
        Actions:
        - Re-validate with current settings
        - Export results to CSV
        - Export results to JSON
        - Copy summary to clipboard
        - Show thermodynamic landscape plot (future)
        """
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_start(12)
        box.set_margin_end(12)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        
        # Re-validate button
        revalidate_btn = Gtk.Button(label="🔄 Re-validate")
        revalidate_btn.set_tooltip_text("Re-run thermodynamic validation with current settings")
        revalidate_btn.connect('clicked', self._on_revalidate)
        box.pack_start(revalidate_btn, False, False, 0)
        
        # Export to CSV
        export_csv_btn = Gtk.Button(label="📊 Export CSV")
        export_csv_btn.set_tooltip_text("Export validation results to CSV file")
        export_csv_btn.connect('clicked', self._on_export_csv)
        box.pack_start(export_csv_btn, False, False, 0)
        
        # Export to JSON
        export_json_btn = Gtk.Button(label="📄 Export JSON")
        export_json_btn.set_tooltip_text("Export validation results to JSON file")
        export_json_btn.connect('clicked', self._on_export_json)
        box.pack_start(export_json_btn, False, False, 0)
        
        # Copy summary
        copy_btn = Gtk.Button(label="📋 Copy Summary")
        copy_btn.set_tooltip_text("Copy statistics summary to clipboard")
        copy_btn.connect('clicked', self._on_copy_summary)
        box.pack_start(copy_btn, False, False, 0)
        
        # Spacer
        box.pack_start(Gtk.Label(), True, True, 0)
        
        # Help button
        help_btn = Gtk.Button(label="❓ Help")
        help_btn.connect('clicked', self._on_show_help)
        box.pack_start(help_btn, False, False, 0)
        
        return box
    
    def _on_export_csv(self, button):
        """Export validation results to CSV format."""
        dialog = Gtk.FileChooserDialog(
            title="Export Thermodynamic Validation Results",
            action=Gtk.FileChooserAction.SAVE,
            buttons=(
                Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                Gtk.STOCK_SAVE, Gtk.ResponseType.OK
            )
        )
        dialog.set_current_name("thermodynamic_validation.csv")
        
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            filepath = dialog.get_filename()
            self._write_csv_report(filepath)
            self._show_notification(f"Results exported to {filepath}")
        
        dialog.destroy()
    
    def _write_csv_report(self, filepath: str):
        """Write validation results to CSV file."""
        import csv
        
        results = self._get_validation_results()
        if not results:
            return
        
        with open(filepath, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Header with metadata
            doc = self._get_document()
            settings = doc.thermodynamic_settings if doc and hasattr(doc, 'thermodynamic_settings') else {}
            
            writer.writerow(['# Thermodynamic Validation Report'])
            writer.writerow(['# Model:', doc.metadata.get('model_name', 'Unknown') if doc and hasattr(doc, 'metadata') else 'Unknown'])
            writer.writerow(['# Date:', datetime.now().isoformat()])
            writer.writerow(['# Settings:'])
            writer.writerow(['#   pH:', settings.get('ph', 7.0)])
            writer.writerow(['#   Temperature (K):', settings.get('temperature', 298.15)])
            writer.writerow(['#   Ionic Strength (M):', settings.get('ionic_strength', 0.1)])
            writer.writerow(['#   Tolerance:', settings.get('tolerance', 0.5)])
            writer.writerow([])
            
            # Statistics
            stats = results.get('statistics', {})
            writer.writerow(['# Statistics'])
            writer.writerow(['Total Reactions', stats.get('total', 0)])
            writer.writerow(['Valid', stats.get('valid', 0)])
            writer.writerow(['Warnings', stats.get('warnings', 0)])
            writer.writerow(['Violations', stats.get('violations', 0)])
            writer.writerow([])
            
            # Validation results table
            writer.writerow([
                'Reaction ID',
                'Transition Name',
                'Status',
                'k_forward',
                'k_reverse',
                'k_ratio (kinetic)',
                'K_eq (thermodynamic)',
                'ΔG°\' (kJ/mol)',
                'Deviation',
                'Message'
            ])
            
            for result in results.get('results', []):
                writer.writerow([
                    result.get('reaction_id', ''),
                    result.get('transition_name', ''),
                    result.get('status', ''),
                    result.get('k_forward', ''),
                    result.get('k_reverse', ''),
                    result.get('k_ratio', ''),
                    result.get('k_eq', ''),
                    result.get('delta_g', ''),
                    result.get('deviation', ''),
                    result.get('message', '')
                ])
```

**Files:**
- `src/shypn/ui/panels/report/thermodynamic_validation_category.py` (major enhancement)

---

### **5.2 Add Thermodynamics to Report Panel Category List**

**Ensure THERMODYNAMICS appears prominently:**

**Changes to `report_panel.py`:**
```python
def _build_categories(self):
    # ... existing categories ...
    
    # THERMODYNAMICS - Make it a prominent top-level category
    # (Currently may be nested or hidden)
    thermo_category = ThermodynamicValidationCategory(
        project=self.project,
        model_canvas=self.model_canvas
    )
    thermo_expander = thermo_category.build_expander()
    thermo_expander.set_expanded(True)  # Expand by default
    self.categories_box.pack_start(thermo_expander, False, False, 0)
    self.categories['thermodynamics'] = thermo_category
```

**Files:**
- `src/shypn/ui/panels/report/report_panel.py`

---

## 📋 **Phase 6: Documentation & Testing (Priority 3)**

### **6.1 Update User Documentation**

**New file: `doc/THERMODYNAMICS_USER_GUIDE.md`:**
- How to configure settings
- How to map compounds
- How to interpret validation results
- Troubleshooting guide

**Update existing docs:**
- `doc/thermodynamics_simulation_integration.md` - Add UI workflow
- `doc/thermodynamics_quick_reference.md` - Add UI screenshots

### **6.2 Unit Tests**

**New test file: `tests/thermodynamics/test_document_integration.py`:**
```python
def test_document_settings_persistence():
    """Test that thermodynamic settings are saved/loaded."""
    
def test_preset_application():
    """Test applying presets updates document correctly."""
    
def test_validator_reads_document_settings():
    """Test validator uses document pH/temperature."""
    
def test_compound_mapping_serialization():
    """Test compound mappings persist in .shy file."""
```

**New test file: `tests/ui/test_thermodynamics_category.py`:**
```python
def test_ui_creates_without_error():
    """Test UI builds successfully."""
    
def test_preset_combo_populates():
    """Test preset dropdown has all presets."""
    
def test_settings_update_document():
    """Test changing UI updates document model."""
```

---

## 🗂️ **File Changes Summary**

### **New Files (9):**
1. `src/shypn/thermodynamics/place_compound_mapper.py` - Compound mapping utilities
2. `src/shypn/ui/panels/pathway_operations/thermodynamics_category.py` - Main UI category (ALL CAPS)
3. `src/shypn/topology/biological/thermodynamics_adapter.py` - Topology adapter
4. `src/shypn/thermodynamics/report_exporter.py` - CSV/JSON export utilities (NEW)
5. `doc/THERMODYNAMICS_USER_GUIDE.md` - User documentation
6. `tests/thermodynamics/test_document_integration.py` - Integration tests
7. `tests/thermodynamics/test_place_compound_mapper.py` - Mapper tests
8. `tests/ui/test_thermodynamics_category.py` - UI tests
9. `THERMODYNAMICS_REFACTOR_PLAN.md` - This document

### **Modified Files (13):**
1. `src/shypn/data/canvas/document_model.py` - Add compound_mappings
2. `src/shypn/thermodynamics/simulation_integration.py` - Read document settings
3. `src/shypn/thermodynamics/__init__.py` - Export new classes
4. `src/shypn/ui/panels/pathway_operations_panel.py` - Register category
5. `src/shypn/ui/panels/pathway_operations/sbml_category.py` - Remove embedded section
6. `src/shypn/data/pathway/sbml_parser.py` - Store compound mappings
7. `src/shypn/ui/panels/topology/biological_category.py` - Use adapter
8. `src/shypn/ui/panels/report/thermodynamic_validation_category.py` - Add link
9. `src/shypn/engine/simulation/controller.py` - Use document settings
10. `doc/thermodynamics_simulation_integration.md` - Update with UI workflow
11. `doc/thermodynamics_quick_reference.md` - Add UI reference
12. `pyproject.toml` - Potentially add new dependencies

### **Deprecated Files (1):**
1. `src/shypn/topology/biological/thermodynamics.py` - Add deprecation notice

---

## ⏱️ **Implementation Timeline**

### **Week 1: Core Infrastructure**
- Phase 1.1: Document model compound mappings
- Phase 1.2: Validator reads document settings
- Phase 1.3: PlaceCompoundMapper utility
- **Milestone:** Backend ready for UI

### **Week 2: UI Development**
- Phase 2.1: THERMODYNAMICS category UI (main effort, ~800 lines)
- Phase 2.2: Register in pathway panel (ALL CAPS consistency)
- **Milestone:** UI functional, no SBML integration yet

### **Week 3: Integration & Enhanced Reporting**
- Phase 3.1: Refactor SBML category
- Phase 3.2: Update SBML parser
- Phase 4.1: Topology adapter
- Phase 5.1: Enhanced Report Panel with statistics dashboard
- Phase 5.2: Export functionality (CSV/JSON)
- **Milestone:** Full integration + comprehensive reporting

### **Week 4: Polish & Testing**
- Phase 6.1: Documentation (user guide + API docs)
- Phase 6.2: Unit tests (document, UI, validation)
- Phase 6.3: Integration tests (full workflow)
- **Milestone:** Production ready with full test coverage

---

## 🚀 **Migration Path for Existing Users**

### **Legacy Models:**
- Load old .shy files → thermodynamic_settings auto-created with defaults
- No compound mappings → User prompted to auto-map or import from SBML

### **SBML Models:**
- Already have annotations → Automatically imported to compound_mappings
- Validation runs seamlessly with stored settings

### **Manual Models:**
- User creates model from scratch
- Can manually map compounds or rely on label matching
- Optional: add compound IDs to place labels (e.g., "ATP [C00002]")

---

## ✅ **Success Criteria**
THERMODYNAMICS
2. **Settings Persistence:** pH/temperature saved with model
3. **SBML Integration:** Seamless import with auto-mapping
4. **Topology Integration:** Real ΔG values in topology panel
5. **Enhanced Reporting:** Comprehensive statistics dashboard with export
6. **Consistent Naming:** ALL CAPS for "THERMODYNAMICS" across all panels
7. **No Regression:** Existing SBML imports still work
8. **Performance:** Validation completes in <5s for typical models
9. **Usability:** User can configure without reading docs
10. **Export Capability:** CSV/JSON export for external analysical models
7. **Usability:** User can configure without reading docs

---

## 🔄 **Backward Compatibility Checklist**

- [x] Old .shy files load without error (default settings applied)
- [ ] SBML import workflow unchanged from user perspective
- [ ] Topology panel shows results (even if no mappings, shows info)
- [ ] Report panel still displays validation results
- [ ] No breaking API changes to thermodynamics module
- [ ] Legacy code can coexist during transition period

---

**Status:** 📝 PLAN READY FOR REVIEW - UPDATED WITH OOP ARCHITECTURE

**Next Action:** Approve plan and begin Phase 1 implementation

---

## 📚 **Appendix: Detailed Coding Guidelines**

### **A1. GTK3 Best Practices (Wayland-Safe)**

#### **Widget Creation:**
```python
# ✅ CORRECT - Modern GTK3
grid = Gtk.Grid()
grid.set_row_spacing(6)
grid.set_column_spacing(12)
grid.attach(label, 0, 0, 1, 1)

# ❌ WRONG - Deprecated
table = Gtk.Table(rows=2, columns=2)  # Deprecated!
table.attach(label, 0, 1, 0, 1)

# ✅ CORRECT - Box with orientation
box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
box.pack_start(widget, expand=False, fill=False, padding=0)

# ❌ WRONG - Deprecated HBox/VBox
hbox = Gtk.HBox(spacing=6)  # Deprecated!
```

#### **Display/Monitor Access (Wayland-safe):**
```python
# ✅ CORRECT - Works with Wayland
display = Gdk.Display.get_default()
monitor = display.get_primary_monitor()
geometry = monitor.get_geometry()
scale_factor = monitor.get_scale_factor()

# ❌ WRONG - X11-specific, breaks on Wayland
screen = Gdk.Screen.get_default()  # May not work
width = screen.get_width()  # X11 only
```

#### **Icons:**
```python
# ✅ CORRECT - Named icons
icon = Gtk.Image.new_from_icon_name("document-save", Gtk.IconSize.BUTTON)

# ❌ WRONG - Stock icons (deprecated in GTK 3.10)
icon = Gtk.Image.new_from_stock(Gtk.STOCK_SAVE, Gtk.IconSize.BUTTON)
```

#### **Actions:**
```python
# ✅ CORRECT - Gio.SimpleAction
action = Gio.SimpleAction.new("save", None)
action.connect("activate", self._on_save)
action_group.add_action(action)

# ❌ WRONG - Gtk.Action (deprecated in GTK 3.10)
action = Gtk.Action(name="save", stock_id=Gtk.STOCK_SAVE)
```

---

### **A2. File Organization Standards**

```
src/shypn/
├── thermodynamics/              # Core engine (business logic)
│   ├── __init__.py
│   ├── base.py                  # Base classes/interfaces
│   ├── gibbs_calculator.py      # Main calculator
│   ├── simulation_integration.py
│   ├── mappers/                 # Compound mapping (OOP)
│   │   ├── __init__.py
│   │   ├── base_mapper.py       # Abstract base
│   │   ├── label_matcher.py     # Concrete impl 1
│   │   ├── sbml_annotator.py    # Concrete impl 2
│   │   └── compound_mapper_service.py  # Facade
│   ├── validators/              # Validation (OOP)
│   │   ├── __init__.py
│   │   ├── base_validator.py
│   │   └── equilibrium_validator.py
│   └── database/                # Data providers
│       └── ...
├── ui/
│   └── panels/
│       ├── pathway_operations/
│       │   └── thermodynamics/  # UI components (thin loaders)
│       │       ├── __init__.py
│       │       ├── base_section.py        # Base UI class
│       │       ├── settings_section.py    # Settings widget
│       │       ├── mapping_section.py     # Mapping editor
│       │       ├── validation_section.py  # Validation trigger
│       │       └── thermodynamics_category.py  # Main loader (assembles sections)
│       └── report/
│           └── thermodynamics/
│               ├── __init__.py
│               ├── base_report.py
│               ├── statistics_panel.py
│               ├── results_table.py
│               └── thermodynamic_validation_category.py  # Main loader
├── data/
│   └── canvas/
│       └── document_model.py    # Data model (no UI code)
└── ...

doc/                             # Documentation
├── THERMODYNAMICS_USER_GUIDE.md
├── thermodynamics_api.md
└── examples/
    ├── basic_validation.py
    └── custom_mapper.py

scripts/                         # Utility scripts
├── migrate_legacy_models.py     # Migration utilities
├── export_validation_report.py
└── batch_validate.py

tests/
├── thermodynamics/
│   ├── test_mappers.py
│   ├── test_validators.py
│   └── test_document_integration.py
└── ui/
    ├── test_thermodynamics_category.py
    └── test_report_panel.py
```

---

### **A3. Class Design Pattern**

#### **Base Class Example:**
```python
# src/shypn/thermodynamics/mappers/base_mapper.py

from abc import ABC, abstractmethod
from typing import Dict, List, Optional

class CompoundMapperBase(ABC):
    """Abstract base for compound mapping strategies.
    
    Subclasses must implement:
    - map_places(): Core mapping logic
    - get_confidence(): Confidence scoring
    
    This enables multiple mapping strategies (SBML annotations,
    label parsing, database lookup) with a common interface.
    """
    
    @abstractmethod
    def map_places(self, places: List) -> Dict[str, str]:
        """Map places to compound IDs.
        
        Args:
            places: List of Place objects
            
        Returns:
            Dictionary mapping place_id → compound_id
        """
        pass
    
    @abstractmethod
    def get_confidence(self, place_id: str) -> float:
        """Get confidence score for a mapping.
        
        Args:
            place_id: Place identifier
            
        Returns:
            Confidence score between 0.0 (uncertain) and 1.0 (certain)
        """
        pass
    
    def validate_compound_id(self, compound_id: str) -> bool:
        """Validate compound ID format (KEGG or ChEBI).
        
        Default implementation, can be overridden.
        """
        # KEGG: C##### (5 digits)
        if re.match(r'^C\d{5}$', compound_id):
            return True
        # ChEBI: CHEBI:#####
        if re.match(r'^CHEBI:\d+$', compound_id):
            return True
        return False
```

#### **Concrete Implementation:**
```python
# src/shypn/thermodynamics/mappers/label_matcher.py

from .base_mapper import CompoundMapperBase
import re

class LabelBasedMapper(CompoundMapperBase):
    """Maps compounds by parsing place labels.
    
    Strategy:
    1. Try direct ID extraction (C00002, CHEBI:12345)
    2. Fall back to fuzzy name matching (ATP → C00002)
    3. Return confidence based on match type
    """
    
    def __init__(self):
        self._load_common_names()
    
    def map_places(self, places: List) -> Dict[str, str]:
        """Extract compound IDs from labels."""
        mappings = {}
        self._confidence_cache = {}  # Store for get_confidence()
        
        for place in places:
            compound_id, confidence = self._map_single_place(place)
            if compound_id:
                mappings[place.id] = compound_id
                self._confidence_cache[place.id] = confidence
        
        return mappings
    
    def get_confidence(self, place_id: str) -> float:
        """Return cached confidence from last mapping."""
        return self._confidence_cache.get(place_id, 0.0)
    
    def _map_single_place(self, place) -> Tuple[Optional[str], float]:
        """Map single place, return (compound_id, confidence)."""
        # Try direct extraction
        compound_id = self._extract_id(place.label)
        if compound_id:
            return compound_id, 0.95  # High confidence
        
        # Try fuzzy matching
        compound_id = self._fuzzy_match(place.label)
        if compound_id:
            return compound_id, 0.60  # Medium confidence
        
        return None, 0.0
    
    # Private helper methods...
```

#### **Thin Loader Pattern:**
```python
# src/shypn/ui/panels/pathway_operations/thermodynamics/thermodynamics_category.py

from .settings_section import SettingsSection
from .mapping_section import MappingSection
from .validation_section import ValidationSection

class ThermodynamicsCategory:
    """Thin loader that assembles THERMODYNAMICS category.
    
    Responsibilities:
    - Create and layout child sections
    - Wire up inter-section communication
    - Delegate business logic to services
    
    Does NOT:
    - Implement validation logic (that's in validators)
    - Handle compound mapping (that's in mappers)
    - Process data (that's in services)
    """
    
    def __init__(self, model_canvas=None):
        self.model_canvas = model_canvas
        
        # Create sections (each is self-contained)
        self.settings_section = SettingsSection(model_canvas)
        self.mapping_section = MappingSection(model_canvas)
        self.validation_section = ValidationSection(model_canvas)
        
        # Services (business logic)
        from shypn.thermodynamics.mappers import CompoundMapperService
        from shypn.thermodynamics import ThermodynamicSimulationValidator
        
        self.mapper_service = CompoundMapperService()
        self.validator = None  # Created when document available
    
    def build_ui(self) -> Gtk.Expander:
        """Assemble UI from sections."""
        expander = Gtk.Expander(label="THERMODYNAMICS")
        expander.set_expanded(False)
        
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        
        # Add sections
        main_box.pack_start(self.settings_section.build_widget(), False, False, 0)
        main_box.pack_start(self.mapping_section.build_widget(), True, True, 0)
        main_box.pack_start(self.validation_section.build_widget(), False, False, 0)
        
        expander.add(main_box)
        return expander
    
    def set_document(self, document):
        """Update all sections with new document."""
        self.settings_section.set_document(document)
        self.mapping_section.set_document(document)
        self.validation_section.set_document(document)
        
        # Create validator for this document
        self.validator = ThermodynamicSimulationValidator(document=document)
    
    # Event handlers delegate to services...
```

---

### **A4. Testing Structure**

#### **Unit Test Example:**
```python
# tests/thermodynamics/test_mappers.py

import unittest
from shypn.thermodynamics.mappers import LabelBasedMapper

class TestLabelBasedMapper(unittest.TestCase):
    """Test label-based compound mapping."""
    
    def setUp(self):
        self.mapper = LabelBasedMapper()
    
    def test_extract_kegg_id(self):
        """Should extract KEGG C-numbers from labels."""
        place = MockPlace(id="p1", label="ATP (C00002)")
        mappings = self.mapper.map_places([place])
        
        self.assertEqual(mappings["p1"], "C00002")
        self.assertGreater(self.mapper.get_confidence("p1"), 0.9)
    
    def test_fuzzy_match_atp(self):
        """Should fuzzy match common compound names."""
        place = MockPlace(id="p1", label="ATP")
        mappings = self.mapper.map_places([place])
        
        self.assertEqual(mappings["p1"], "C00002")
        self.assertGreater(self.mapper.get_confidence("p1"), 0.5)
    
    def test_no_match_returns_empty(self):
        """Should return empty dict for unmatchable labels."""
        place = MockPlace(id="p1", label="Unknown Metabolite XYZ")
        mappings = self.mapper.map_places([place])
        
        self.assertEqual(len(mappings), 0)
```

#### **Integration Test Example:**
```python
# tests/thermodynamics/test_document_integration.py

import unittest
from shypn.data.canvas.document_model import DocumentModel

class TestDocumentIntegration(unittest.TestCase):
    """Test thermodynamic settings integration with document model."""
    
    def test_default_settings_applied(self):
        """New documents should have default thermodynamic settings."""
        doc = DocumentModel()
        
        self.assertEqual(doc.thermodynamic_settings['ph'], 7.0)
        self.assertEqual(doc.thermodynamic_settings['temperature'], 298.15)
        self.assertTrue(doc.thermodynamic_settings['enable_validation'])
    
    def test_preset_application(self):
        """Should apply preset correctly."""
        doc = DocumentModel()
        doc.set_thermodynamic_preset('e_coli_cytoplasm')
        
        self.assertEqual(doc.thermodynamic_settings['ph'], 7.4)
        self.assertEqual(doc.thermodynamic_settings['temperature'], 310.15)
    
    def test_serialization_roundtrip(self):
        """Settings should survive save/load cycle."""
        doc = DocumentModel()
        doc.update_thermodynamic_settings(ph=6.5, temperature=303.15)
        
        # Serialize
        data = doc.to_dict()
        
        # Deserialize
        doc2 = DocumentModel.from_dict(data)
        
        self.assertEqual(doc2.thermodynamic_settings['ph'], 6.5)
        self.assertEqual(doc2.thermodynamic_settings['temperature'], 303.15)
```

---

### **A5. Documentation Standards**

#### **Module Docstring:**
```python
"""Thermodynamic compound mapping strategies.

This module provides multiple strategies for mapping Petri net places to
biochemical compound identifiers (KEGG, ChEBI). Each strategy is implemented
as a subclass of CompoundMapperBase, allowing flexible composition.

Available Strategies:
    - LabelBasedMapper: Extracts IDs from place labels
    - SBMLAnnotationMapper: Uses SBML species annotations
    - DatabaseLookupMapper: Queries external databases (future)

Usage Example:
    >>> from shypn.thermodynamics.mappers import CompoundMapperService
    >>> 
    >>> service = CompoundMapperService(document)
    >>> mappings, confidences = service.map_all_places(places)
    >>> 
    >>> for place_id, compound_id in mappings.items():
    ...     conf = confidences[place_id]
    ...     print(f"{place_id} → {compound_id} (confidence: {conf:.2f})")

See Also:
    - doc/THERMODYNAMICS_USER_GUIDE.md: End-user documentation
    - doc/thermodynamics_api.md: API reference
    - tests/thermodynamics/test_mappers.py: Unit tests

Author: SHYPN Development Team
Date: January 2026
License: See LICENSE file
"""
```

---

### **A6. Wayland Compatibility Checklist**

- [ ] No direct `GdkWindow` manipulation
- [ ] Use `Gdk.Display.get_default()` instead of `Gdk.Screen`
- [ ] No hardcoded screen dimensions
- [ ] No X11-specific calls (`gdk_x11_*`)
- [ ] Use `Gtk.Window.set_default_size()` not absolute positioning
- [ ] Use `Gtk.HeaderBar` for modern window chrome
- [ ] Test on both X11 and Wayland sessions
- [ ] No `Gtk.Stock` constants (use icon names)
- [ ] Use `Gio.Application` for proper lifecycle
- [ ] No deprecated `Gtk.UIManager` (use `Gtk.Builder`)

---

**Implementation Checklist:**

- [ ] All base classes in separate files
- [ ] Subclasses properly inherit and override
- [ ] UI loaders are thin (<200 lines)
- [ ] Business logic in services/models
- [ ] Utilities in /scripts
- [ ] Documentation in /doc
- [ ] Tests in /tests with >80% coverage
- [ ] No deprecated GTK widgets
- [ ] Wayland-safe code
- [ ] Type hints on all public methods
- [ ] Docstrings on all classes/methods

---
