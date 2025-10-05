# Locality-Based Analysis - REVISED Implementation Plan (OOP Architecture)

## Date: October 5, 2025

## Core Principles

1. **OOP Architecture**: No code in loaders, use base classes and inheritance
2. **Diagnostic Module**: Put locality detection under `src/shypn/diagnostic/`
3. **Context Menu**: "Add to Analysis" is object-sensitive context menu, not dialog
4. **Transition Dialog**: Use existing Diagnostics tab with Locality Information frame
5. **Clean Separation**: Loaders only instantiate and wire, business logic in classes

---

## Current Architecture Analysis

### Existing Structure ✅

```
src/shypn/
├── analyses/
│   ├── plot_panel.py              # Base class for analysis panels
│   ├── place_rate_panel.py        # Place token evolution plots
│   ├── transition_rate_panel.py   # Transition behavior plots
│   └── context_menu_handler.py    # Context menu "Add to Analysis"
│
├── helpers/
│   ├── model_canvas_loader.py     # Wires context menu handler
│   └── transition_prop_dialog_loader.py  # Instantiates dialog
│
└── ui/dialogs/
    └── transition_prop_dialog.ui  # HAS Diagnostics tab already!
        ├── Basic tab
        ├── Behavior tab (guard, rate)
        ├── Visual tab
        └── Diagnostics tab
            ├── Locality Information frame ✅
            └── Diagnostic Report frame ✅
```

**Key Discovery**: Transition dialog already has:
- ✅ Diagnostics tab
- ✅ Locality Information frame (`locality_info_container`)
- ✅ Diagnostic Report frame

---

## Revised Architecture

### New Structure

```
src/shypn/
├── diagnostic/              # NEW MODULE
│   ├── __init__.py
│   ├── locality_detector.py       # Detect transition neighborhoods
│   ├── locality_analyzer.py       # Analyze locality properties
│   └── locality_info_widget.py    # GTK widget for locality display
│
├── analyses/
│   ├── plot_panel.py              # NO CHANGES (base class)
│   ├── place_rate_panel.py        # NO CHANGES
│   ├── transition_rate_panel.py   # ENHANCE with locality
│   └── context_menu_handler.py    # ENHANCE with locality option
│
└── helpers/
    └── transition_prop_dialog_loader.py  # Wire locality widget
```

---

## Phase 1: Diagnostic Module (OOP, No Loader Code)

### File: `src/shypn/diagnostic/__init__.py`

```python
"""Diagnostic tools for Petri net analysis.

This module provides diagnostic tools for analyzing Petri net structure
and behavior, including locality detection and analysis.
"""

from .locality_detector import LocalityDetector
from .locality_analyzer import LocalityAnalyzer
from .locality_info_widget import LocalityInfoWidget

__all__ = [
    'LocalityDetector',
    'LocalityAnalyzer',
    'LocalityInfoWidget',
]
```

### File: `src/shypn/diagnostic/locality_detector.py`

```python
#!/usr/bin/env python3
"""Locality Detector - Detect transition neighborhoods (Place-Transition-Place).

This module provides the LocalityDetector class for identifying localities
in Petri nets based on arc connectivity.

Locality Concept (from legacy):
    "Place-transition-place defines what is called a Locality"
    
    A locality is: Input Places → Transition → Output Places
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field


@dataclass
class Locality:
    """Represents a transition-centered locality.
    
    Attributes:
        transition: The central transition
        input_places: List of places that feed TO transition
        output_places: List of places that receive FROM transition
        input_arcs: List of arcs (place → transition)
        output_arcs: List of arcs (transition → place)
    """
    transition: Any
    input_places: List[Any] = field(default_factory=list)
    output_places: List[Any] = field(default_factory=list)
    input_arcs: List[Any] = field(default_factory=list)
    output_arcs: List[Any] = field(default_factory=list)
    
    @property
    def is_valid(self) -> bool:
        """Check if locality is valid (has inputs AND outputs)."""
        return len(self.input_places) >= 1 and len(self.output_places) >= 1
    
    @property
    def place_count(self) -> int:
        """Total number of places in locality."""
        return len(self.input_places) + len(self.output_places)
    
    def get_summary(self) -> str:
        """Get human-readable summary."""
        return (f"{len(self.input_places)} inputs → "
                f"{self.transition.name} → "
                f"{len(self.output_places)} outputs")


class LocalityDetector:
    """Detector for transition-centered localities.
    
    This class analyzes Petri net structure to identify localities:
    each locality consists of a central transition with its connected
    input and output places.
    
    Attributes:
        model: Reference to PetriNetModel
    
    Example:
        detector = LocalityDetector(model)
        locality = detector.get_locality_for_transition(transition)
        
        if locality.is_valid:
            print(locality.get_summary())
            for place in locality.input_places:
                print(f"  Input: {place.name}")
            for place in locality.output_places:
                print(f"  Output: {place.name}")
    """
    
    def __init__(self, model: Any):
        """Initialize detector with model reference.
        
        Args:
            model: PetriNetModel instance
        """
        self.model = model
    
    def get_locality_for_transition(self, transition: Any) -> Locality:
        """Detect locality for a specific transition.
        
        Algorithm:
        1. Find all arcs connected to transition
        2. Classify arcs as input (place → transition) or output (transition → place)
        3. Extract places from arcs
        4. Build Locality object
        
        Args:
            transition: Transition object
            
        Returns:
            Locality object (may be invalid if no inputs/outputs)
        """
        locality = Locality(transition=transition)
        
        # Scan all arcs in model
        if not hasattr(self.model, 'arcs'):
            return locality
        
        for arc in self.model.arcs.values():
            # Input arc: place → transition
            if arc.target == transition:
                locality.input_arcs.append(arc)
                if arc.source not in locality.input_places:
                    locality.input_places.append(arc.source)
            
            # Output arc: transition → place
            elif arc.source == transition:
                locality.output_arcs.append(arc)
                if arc.target not in locality.output_places:
                    locality.output_places.append(arc.target)
        
        return locality
    
    def get_all_localities(self) -> List[Locality]:
        """Detect localities for all transitions in model.
        
        Returns:
            List of Locality objects (only valid ones)
        """
        localities = []
        
        if not hasattr(self.model, 'transitions'):
            return localities
        
        for transition in self.model.transitions.values():
            locality = self.get_locality_for_transition(transition)
            if locality.is_valid:
                localities.append(locality)
        
        return localities
    
    def find_shared_places(self) -> Dict[int, List[Any]]:
        """Find places that are shared by multiple localities.
        
        Returns:
            Dict mapping place_id -> list of transitions using that place
        """
        place_usage = {}
        
        for locality in self.get_all_localities():
            all_places = locality.input_places + locality.output_places
            for place in all_places:
                if place.id not in place_usage:
                    place_usage[place.id] = []
                if locality.transition not in place_usage[place.id]:
                    place_usage[place.id].append(locality.transition)
        
        # Filter to only shared places (used by >1 transition)
        shared = {pid: transitions for pid, transitions in place_usage.items() 
                  if len(transitions) > 1}
        
        return shared
```

### File: `src/shypn/diagnostic/locality_analyzer.py`

```python
#!/usr/bin/env python3
"""Locality Analyzer - Analyze locality properties and behavior.

This module provides analysis tools for locality characteristics,
including token flow, firing patterns, and structural properties.
"""

from typing import Dict, List, Any, Tuple
from .locality_detector import Locality, LocalityDetector


class LocalityAnalyzer:
    """Analyzer for locality properties.
    
    Provides methods to analyze locality structure and behavior,
    including token flow patterns, arc weights, and firing potential.
    
    Example:
        analyzer = LocalityAnalyzer(model)
        analysis = analyzer.analyze_locality(locality)
        
        print(f"Total arc weight: {analysis['total_weight']}")
        print(f"Token balance: {analysis['token_balance']}")
    """
    
    def __init__(self, model: Any):
        """Initialize analyzer.
        
        Args:
            model: PetriNetModel instance
        """
        self.model = model
        self.detector = LocalityDetector(model)
    
    def analyze_locality(self, locality: Locality) -> Dict[str, Any]:
        """Comprehensive locality analysis.
        
        Args:
            locality: Locality object to analyze
            
        Returns:
            Dict with analysis results
        """
        return {
            'is_valid': locality.is_valid,
            'place_count': locality.place_count,
            'input_count': len(locality.input_places),
            'output_count': len(locality.output_places),
            'arc_count': len(locality.input_arcs) + len(locality.output_arcs),
            'input_tokens': self._count_input_tokens(locality),
            'output_tokens': self._count_output_tokens(locality),
            'token_balance': self._calculate_token_balance(locality),
            'total_weight': self._calculate_total_weight(locality),
            'can_fire': self._check_firing_potential(locality),
            'summary': locality.get_summary()
        }
    
    def _count_input_tokens(self, locality: Locality) -> int:
        """Count total tokens in input places."""
        return sum(place.tokens for place in locality.input_places)
    
    def _count_output_tokens(self, locality: Locality) -> int:
        """Count total tokens in output places."""
        return sum(place.tokens for place in locality.output_places)
    
    def _calculate_token_balance(self, locality: Locality) -> int:
        """Calculate token balance (inputs - outputs)."""
        return self._count_input_tokens(locality) - self._count_output_tokens(locality)
    
    def _calculate_total_weight(self, locality: Locality) -> int:
        """Calculate total arc weight."""
        total = 0
        for arc in locality.input_arcs + locality.output_arcs:
            total += getattr(arc, 'weight', 1)
        return total
    
    def _check_firing_potential(self, locality: Locality) -> bool:
        """Check if transition has potential to fire (basic check)."""
        # Check if all input places have enough tokens for arc weights
        for arc in locality.input_arcs:
            place = arc.source
            required = getattr(arc, 'weight', 1)
            if place.tokens < required:
                return False
        return True
    
    def get_token_flow_description(self, locality: Locality) -> List[str]:
        """Get detailed token flow description.
        
        Returns:
            List of strings describing token flow
        """
        lines = []
        lines.append(f"Locality for {locality.transition.name}:")
        lines.append("")
        
        # Input flows
        lines.append("Input Flows:")
        for arc in locality.input_arcs:
            place = arc.source
            weight = getattr(arc, 'weight', 1)
            lines.append(f"  {place.name} ({place.tokens} tokens) --[{weight}]--> {locality.transition.name}")
        
        # Output flows
        lines.append("")
        lines.append("Output Flows:")
        for arc in locality.output_arcs:
            place = arc.target
            weight = getattr(arc, 'weight', 1)
            lines.append(f"  {locality.transition.name} --[{weight}]--> {place.name} ({place.tokens} tokens)")
        
        return lines
```

---

## Phase 2: Locality Info Widget (GTK Component)

### File: `src/shypn/diagnostic/locality_info_widget.py`

```python
#!/usr/bin/env python3
"""Locality Info Widget - GTK widget for displaying locality information.

This widget displays locality structure and analysis in the transition
properties dialog diagnostics tab.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Pango

from .locality_detector import Locality, LocalityDetector
from .locality_analyzer import LocalityAnalyzer


class LocalityInfoWidget(Gtk.Box):
    """GTK widget displaying locality information.
    
    This widget shows:
    - Locality summary (inputs → transition → outputs)
    - List of input places with token counts
    - List of output places with token counts
    - Token flow diagram
    - Analysis metrics
    
    Usage:
        # In transition_prop_dialog_loader
        widget = LocalityInfoWidget(model)
        widget.set_transition(transition)
        container.pack_start(widget, True, True, 0)
    """
    
    def __init__(self, model):
        """Initialize widget.
        
        Args:
            model: PetriNetModel instance
        """
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        
        self.model = model
        self.detector = LocalityDetector(model)
        self.analyzer = LocalityAnalyzer(model)
        self.locality = None
        
        self._build_ui()
    
    def _build_ui(self):
        """Build widget UI."""
        # Summary label
        self.summary_label = Gtk.Label()
        self.summary_label.set_markup("<b>Locality Structure</b>")
        self.summary_label.set_xalign(0)
        self.pack_start(self.summary_label, False, False, 0)
        
        # Separator
        self.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 5)
        
        # Scrolled window for details
        scrolled = Gtk.ScrolledWindow()
        scrolled.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        scrolled.set_min_content_height(150)
        
        # TextView for detailed info
        self.textview = Gtk.TextView()
        self.textview.set_editable(False)
        self.textview.set_wrap_mode(Gtk.WrapMode.WORD)
        self.textview.set_left_margin(10)
        self.textview.set_right_margin(10)
        
        # Monospace font for better alignment
        font_desc = Pango.FontDescription("Monospace 10")
        self.textview.override_font(font_desc)
        
        scrolled.add(self.textview)
        self.pack_start(scrolled, True, True, 0)
        
        self.show_all()
    
    def set_transition(self, transition):
        """Set transition and update display.
        
        Args:
            transition: Transition object
        """
        self.locality = self.detector.get_locality_for_transition(transition)
        self._update_display()
    
    def _update_display(self):
        """Update widget display with locality info."""
        if self.locality is None:
            self._show_no_transition()
            return
        
        if not self.locality.is_valid:
            self._show_invalid_locality()
            return
        
        # Update summary
        self.summary_label.set_markup(
            f"<b>Locality: {self.locality.get_summary()}</b>"
        )
        
        # Get analysis
        analysis = self.analyzer.analyze_locality(self.locality)
        flow_desc = self.analyzer.get_token_flow_description(self.locality)
        
        # Build detailed text
        text_lines = []
        text_lines.extend(flow_desc)
        text_lines.append("")
        text_lines.append("═" * 50)
        text_lines.append("Analysis:")
        text_lines.append(f"  Total Places: {analysis['place_count']}")
        text_lines.append(f"  Input Tokens: {analysis['input_tokens']}")
        text_lines.append(f"  Output Tokens: {analysis['output_tokens']}")
        text_lines.append(f"  Token Balance: {analysis['token_balance']}")
        text_lines.append(f"  Total Arc Weight: {analysis['total_weight']}")
        text_lines.append(f"  Can Fire: {'✓ Yes' if analysis['can_fire'] else '✗ No'}")
        
        # Set text
        buffer = self.textview.get_buffer()
        buffer.set_text("\n".join(text_lines))
    
    def _show_no_transition(self):
        """Show message when no transition set."""
        self.summary_label.set_markup("<i>No transition selected</i>")
        buffer = self.textview.get_buffer()
        buffer.set_text("Select a transition to view its locality information.")
    
    def _show_invalid_locality(self):
        """Show message for invalid locality."""
        self.summary_label.set_markup("<i>Invalid Locality</i>")
        buffer = self.textview.get_buffer()
        
        text = []
        text.append(f"Transition: {self.locality.transition.name}")
        text.append("")
        text.append("⚠ This transition does not form a valid locality.")
        text.append("")
        text.append("A valid locality requires:")
        text.append("  • At least 1 input place (provides tokens TO transition)")
        text.append("  • At least 1 output place (receives tokens FROM transition)")
        text.append("")
        text.append("Current state:")
        text.append(f"  • Input places: {len(self.locality.input_places)}")
        text.append(f"  • Output places: {len(self.locality.output_places)}")
        
        buffer.set_text("\n".join(text))
```

---

## Phase 3: Wire Locality Widget to Dialog (Loader Only)

### File: `src/shypn/helpers/transition_prop_dialog_loader.py` (MODIFY)

```python
# At the top, add import
from shypn.diagnostic import LocalityInfoWidget

class TransitionPropDialogLoader(GObject.GObject):
    def __init__(self, ...):
        # ... existing code ...
        
        # NEW: Create locality info widget
        self.locality_widget = None
    
    def _populate_fields(self):
        """Populate dialog fields with current Transition properties."""
        # ... existing code ...
        
        # NEW: Setup locality widget in diagnostics tab
        self._setup_locality_widget()
    
    def _setup_locality_widget(self):
        """Setup locality information widget in diagnostics tab."""
        # Get locality container from UI file
        locality_container = self.builder.get_object('locality_info_container')
        
        if locality_container and self.model:
            # Clear existing children
            for child in locality_container.get_children():
                locality_container.remove(child)
            
            # Create and add locality widget
            self.locality_widget = LocalityInfoWidget(self.model)
            self.locality_widget.set_transition(self.transition_obj)
            
            locality_container.pack_start(self.locality_widget, True, True, 0)
            locality_container.show_all()
            
            print("[TransitionPropDialogLoader] Locality widget initialized")
```

---

## Phase 4: Enhance Context Menu (No Dialog!)

### File: `src/shypn/analyses/context_menu_handler.py` (MODIFY)

```python
from shypn.diagnostic import LocalityDetector

class ContextMenuHandler:
    def __init__(self, place_panel=None, transition_panel=None, model=None):
        self.place_panel = place_panel
        self.transition_panel = transition_panel
        self.model = model  # NEW: need model for locality detection
        self.locality_detector = LocalityDetector(model) if model else None
    
    def add_analysis_menu_items(self, menu, obj):
        """Add analysis-related menu items to object's context menu."""
        from shypn.netobjs import Place, Transition
        
        # ... existing code ...
        
        # NEW: For transitions, add locality option
        if isinstance(obj, Transition) and self.locality_detector:
            self._add_locality_submenu(menu, obj)
    
    def _add_locality_submenu(self, menu, transition):
        """Add submenu for locality-based analysis.
        
        Shows:
        - Add Transition Only
        - Add Transition + Locality (inputs + outputs)
        """
        # Detect locality
        locality = self.locality_detector.get_locality_for_transition(transition)
        
        if not locality.is_valid:
            # No valid locality, just add transition normally
            return
        
        # Create submenu
        submenu_item = Gtk.MenuItem(label="Add to Transition Analysis")
        submenu = Gtk.Menu()
        
        # Option 1: Transition only
        transition_only = Gtk.MenuItem(label=f"Transition Only ({transition.name})")
        transition_only.connect("activate", 
                               lambda w: self._add_transition_only(transition))
        submenu.append(transition_only)
        
        # Option 2: Transition + locality
        with_locality = Gtk.MenuItem(label=f"With Locality ({locality.place_count} places)")
        with_locality.connect("activate",
                             lambda w: self._add_transition_with_locality(transition, locality))
        submenu.append(with_locality)
        
        submenu_item.set_submenu(submenu)
        submenu.show_all()
        menu.append(submenu_item)
    
    def _add_transition_only(self, transition):
        """Add transition without locality."""
        if self.transition_panel:
            self.transition_panel.add_object(transition)
            print(f"[ContextMenu] Added {transition.name} (transition only)")
    
    def _add_transition_with_locality(self, transition, locality):
        """Add transition with all locality places."""
        if self.transition_panel:
            # Add transition
            self.transition_panel.add_object(transition)
            
            # Add input places
            if hasattr(self.transition_panel, 'add_locality_places'):
                self.transition_panel.add_locality_places(transition, locality)
            
            print(f"[ContextMenu] Added {transition.name} with locality "
                  f"({len(locality.input_places)} inputs, {len(locality.output_places)} outputs)")
```

---

## Phase 5: Enhance TransitionRatePanel (Business Logic)

### File: `src/shypn/analyses/transition_rate_panel.py` (MODIFY)

```python
from shypn.diagnostic import LocalityDetector

class TransitionRatePanel(AnalysisPlotPanel):
    def __init__(self, data_collector, model):  # ADD model parameter
        super().__init__('transition', data_collector)
        self.model = model  # Store model reference
        self.locality_detector = LocalityDetector(model) if model else None
        self._locality_places = {}  # Maps transition_id -> {input_places, output_places}
    
    def add_locality_places(self, transition, locality):
        """Add locality places for a transition.
        
        This stores the locality places so they can be plotted
        together with the transition.
        
        Args:
            transition: Transition object
            locality: Locality object
        """
        self._locality_places[transition.id] = {
            'input_places': locality.input_places,
            'output_places': locality.output_places
        }
        
        print(f"[TransitionRatePanel] Locality registered for {transition.name}: "
              f"{len(locality.input_places)} inputs, {len(locality.output_places)} outputs")
        
        # Trigger replot
        self._plot_data()
    
    def _plot_data(self):
        """Plot transition behavior with optional locality places."""
        if not self.axes:
            return
        
        self.axes.clear()
        
        # Plot each transition
        for transition_id in self._tracked_objects:
            # Plot transition behavior (existing)
            self._plot_transition_behavior(transition_id)
            
            # Plot locality places if available
            if transition_id in self._locality_places:
                self._plot_locality_places(transition_id)
        
        self._finalize_plot()
    
    def _plot_locality_places(self, transition_id):
        """Plot input and output places for transition's locality."""
        locality_data = self._locality_places[transition_id]
        
        # Plot input places (dashed lines, blue family)
        for i, place in enumerate(locality_data['input_places']):
            place_data = self.data_collector.get_place_data(place.id)
            if place_data:
                times, tokens = zip(*place_data)
                self.axes.plot(times, tokens,
                             linestyle='--',
                             linewidth=1.5,
                             alpha=0.6,
                             label=f"  {place.name} (input)")
        
        # Plot output places (dotted lines, orange family)
        for i, place in enumerate(locality_data['output_places']):
            place_data = self.data_collector.get_place_data(place.id)
            if place_data:
                times, tokens = zip(*place_data)
                self.axes.plot(times, tokens,
                             linestyle=':',
                             linewidth=1.5,
                             alpha=0.6,
                             label=f"  {place.name} (output)")
```

---

## Testing Strategy

### Test 1: Locality Detection
```python
def test_locality_detection():
    from shypn.diagnostic import LocalityDetector
    
    # Create P-T-P model
    model = create_test_model()
    detector = LocalityDetector(model)
    
    transition = model.transitions[1]
    locality = detector.get_locality_for_transition(transition)
    
    assert locality.is_valid
    assert len(locality.input_places) >= 1
    assert len(locality.output_places) >= 1
    print(f"✓ Locality detected: {locality.get_summary()}")
```

### Test 2: Locality Widget
```python
def test_locality_widget():
    from shypn.diagnostic import LocalityInfoWidget
    
    model = create_test_model()
    widget = LocalityInfoWidget(model)
    
    transition = model.transitions[1]
    widget.set_transition(transition)
    
    # Widget should display locality info
    assert widget.locality is not None
    assert widget.locality.is_valid
    print("✓ Locality widget displays correctly")
```

### Test 3: Context Menu with Locality
```python
def test_context_menu_locality():
    from shypn.analyses import ContextMenuHandler
    
    model = create_test_model()
    handler = ContextMenuHandler(place_panel, transition_panel, model)
    
    # Right-click on transition should show locality submenu
    # User can choose "Transition Only" or "With Locality"
    print("✓ Context menu offers locality option")
```

---

## Summary of Changes

### New Files (3):
1. `src/shypn/diagnostic/__init__.py`
2. `src/shypn/diagnostic/locality_detector.py`
3. `src/shypn/diagnostic/locality_analyzer.py`
4. `src/shypn/diagnostic/locality_info_widget.py`

### Modified Files (3):
1. `src/shypn/analyses/context_menu_handler.py` - Add locality submenu
2. `src/shypn/analyses/transition_rate_panel.py` - Add locality plotting
3. `src/shypn/helpers/transition_prop_dialog_loader.py` - Wire locality widget

### No Changes Needed:
- ✅ `ui/dialogs/transition_prop_dialog.ui` (already has frames)
- ✅ `src/shypn/analyses/plot_panel.py` (base class unchanged)
- ✅ `src/shypn/helpers/model_canvas_loader.py` (already wires context menu)

---

## Benefits of OOP Architecture

✅ **Separation of Concerns**: Business logic in diagnostic module, UI in widget  
✅ **Reusability**: LocalityDetector can be used in multiple contexts  
✅ **Testability**: Each class can be unit tested independently  
✅ **Maintainability**: No business logic in loaders  
✅ **Extensibility**: Easy to add new diagnostic tools  

---

## Next Steps

1. ✅ Reviewed existing architecture
2. ⏳ Create `src/shypn/diagnostic/` module
3. ⏳ Implement `LocalityDetector` class
4. ⏳ Implement `LocalityAnalyzer` class
5. ⏳ Implement `LocalityInfoWidget` class
6. ⏳ Enhance `ContextMenuHandler` with locality submenu
7. ⏳ Enhance `TransitionRatePanel` with locality plotting
8. ⏳ Wire locality widget in transition dialog loader
9. ⏳ Test and document

Ready to implement! 🚀
