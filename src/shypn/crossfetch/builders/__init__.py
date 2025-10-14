"""Pathway builders for converting fetched data to Shypn models.

This module provides builders that convert FetchResult data from various sources
(KEGG, BioModels, Reactome) into Shypn Petri net objects (Place, Transition, Arc).

The workflow is:
1. User enters pathway ID
2. CrossFetch fetches data from external source
3. PathwayBuilder converts data to Place/Transition/Arc objects
4. Shypn renders the model and allows editing/simulation

Classes:
    PathwayBuilder: Converts FetchResult data to Shypn Petri net objects
"""

from shypn.crossfetch.builders.pathway_builder import PathwayBuilder

__all__ = [
    'PathwayBuilder',
]
