"""KEGG pathway import module.

This module provides functionality to import biochemical pathways
from the KEGG database and convert them to Petri net models.

Main components:
- api_client: Fetch pathway data from KEGG REST API
- kgml_parser: Parse KGML XML into structured data
- pathway_converter: Convert KEGG pathways to Petri nets
- models: Data structures for pathway elements

Example usage:
    >>> from shypn.import.kegg import fetch_pathway, parse_kgml, convert_to_petri_net
    >>> kgml_xml = fetch_pathway("hsa00010")
    >>> pathway = parse_kgml(kgml_xml)
    >>> document = convert_to_petri_net(pathway)

⚠️ ACADEMIC USE ONLY:
The KEGG API and data are provided for academic use only.
Users must comply with KEGG's usage policies.
"""

from .api_client import KEGGAPIClient, fetch_pathway
from .kgml_parser import KGMLParser, parse_kgml
from .pathway_converter import PathwayConverter, convert_pathway
from .models import (
    KEGGPathway,
    KEGGEntry,
    KEGGReaction,
    KEGGRelation,
    KEGGGraphics,
    KEGGSubstrate,
    KEGGProduct,
    KEGGRelationSubtype
)

__all__ = [
    'KEGGAPIClient',
    'fetch_pathway',
    'KGMLParser',
    'parse_kgml',
    'PathwayConverter',
    'convert_pathway',
    'KEGGPathway',
    'KEGGEntry',
    'KEGGReaction',
    'KEGGRelation',
    'KEGGGraphics',
    'KEGGSubstrate',
    'KEGGProduct',
    'KEGGRelationSubtype',
]
