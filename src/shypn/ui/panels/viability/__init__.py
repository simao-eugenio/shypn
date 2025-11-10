"""Viability Panel - Intelligent Model Repair Assistant.

This package provides the UI components for the Viability Panel,
which diagnoses model issues and suggests fixes across multiple domains:
- Structural (topology-based)
- Biological (semantic/biochemical)
- Kinetic (BRENDA-based)
- Diagnosis (multi-domain + locality-aware)

Architecture follows Shypn panel pattern with category-based organization.
"""

from .viability_panel_new import ViabilityPanel

__all__ = ['ViabilityPanel']
