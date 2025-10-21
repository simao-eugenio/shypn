"""UI components for Shypn.

This package contains UI-related modules that decouple GTK interface
definitions from business logic, following clean architecture principles.

Modules:
    topology_tab_loader: Loaders for topology analysis tabs in property dialogs
    highlighting_manager: Manager for canvas highlighting features
    master_palette: Main vertical toolbar for panel category buttons
    palette_button: Individual button widget used in master palette

Architecture:
    - UI definitions: /ui/*.ui (GTK XML files)
    - UI loaders: /src/shypn/ui/*.py (this package)
    - Business logic: /src/shypn/topology/* (analyzers)

This ensures:
    - Separation of concerns
    - Testable components
    - Wayland compatibility
    - Easy SwissKnifePalette integration
"""

from .topology_tab_loader import (
    TopologyTabLoader,
    PlaceTopologyTabLoader,
    TransitionTopologyTabLoader,
    ArcTopologyTabLoader,
    create_place_topology_tab,
    create_transition_topology_tab,
    create_arc_topology_tab,
)

from .highlighting_manager import (
    HighlightingManager,
    HighlightType,
    HighlightStyle,
    HighlightLayer,
    create_highlighting_manager,
    STYLE_CYCLE,
    STYLE_PATH,
    STYLE_HUB,
    STYLE_P_INV,
    STYLE_T_INV,
)

from .master_palette import MasterPalette
from .palette_button import PaletteButton

__all__ = [
    # Topology tab loaders
    'TopologyTabLoader',
    'PlaceTopologyTabLoader',
    'TransitionTopologyTabLoader',
    'ArcTopologyTabLoader',
    'create_place_topology_tab',
    'create_transition_topology_tab',
    'create_arc_topology_tab',
    # Highlighting
    'HighlightingManager',
    'HighlightType',
    'HighlightStyle',
    'HighlightLayer',
    'create_highlighting_manager',
    'STYLE_CYCLE',
    'STYLE_PATH',
    'STYLE_HUB',
    'STYLE_P_INV',
    'STYLE_T_INV',
    # Master palette
    'MasterPalette',
    'PaletteButton',
]
