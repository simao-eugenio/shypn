"""
Pathway Import Package

This package handles importing biochemical pathways from SBML files
and converting them to Petri net models.

Pipeline:
    1. Parse: SBML file → PathwayData (raw)
    2. Validate: Check data integrity
    3. Post-Process: Layout, colors, unit conversion
    4. Convert: PathwayData → DocumentModel (Petri net)
    5. Instantiate: Create Place, Transition, Arc objects on canvas

Modules:
    - pathway_data: Data classes for pathway representation
    - sbml_parser: Parse SBML files using python-libsbml
    - pathway_validator: Validate parsed pathway data
    - pathway_postprocessor: Enrich data with layout, colors, etc.
    - pathway_converter: Convert to Petri net DocumentModel
    - kinetics_mapper: Map kinetic laws to transition rates
    - pathway_layout: Layout algorithms for automatic positioning
"""

__version__ = "0.1.0"
__all__ = [
    "PathwayData",
    "Species",
    "Reaction",
    "KineticLaw",
    "ProcessedPathwayData",
    "SBMLParser",
    "PathwayValidator",
    "PathwayPostProcessor",
    "PathwayConverter",
]

# Version info
SBML_SUPPORT_VERSION = "L3V2"  # SBML Level 3 Version 2
