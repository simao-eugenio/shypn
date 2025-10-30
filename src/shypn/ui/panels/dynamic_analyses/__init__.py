#!/usr/bin/env python3
"""Dynamic Analyses Panel - Real-time visualization module.

This module provides the Dynamic Analyses Panel for real-time visualization
during simulation, organized into collapsible categories:

1. Transitions - Real-time transition firing rates/counts
2. Places - Real-time place marking evolution  
3. Diagnostics - Runtime performance metrics

Author: Simão Eugénio
Date: 2025-10-29
"""

from .dynamic_analyses_panel import DynamicAnalysesPanel
from .transitions_category import TransitionsCategory
from .places_category import PlacesCategory
from .diagnostics_category import DiagnosticsCategory

__all__ = [
    'DynamicAnalysesPanel',
    'TransitionsCategory',
    'PlacesCategory',
    'DiagnosticsCategory',
]
