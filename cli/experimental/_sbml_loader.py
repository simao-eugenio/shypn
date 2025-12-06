#!/usr/bin/env python3
"""Helper to load SBML files and convert to DocumentModel"""
import _fix_imports
from pathlib import Path
from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor
from shypn.data.pathway.pathway_converter import PathwayConverter

def load_sbml_model(sbml_path: Path):
    """Load SBML file and convert to DocumentModel.
    
    Args:
        sbml_path: Path to SBML XML file
    
    Returns:
        DocumentModel ready for simulation
    """
    # Parse SBML
    parser = SBMLParser()
    pathway_data = parser.parse_file(str(sbml_path))
    
    # Postprocess (add positions, colors, etc.)
    postprocessor = PathwayPostProcessor()
    processed_pathway = postprocessor.process(pathway_data)
    
    # Convert to DocumentModel
    converter = PathwayConverter()
    model = converter.convert(processed_pathway)
    
    return model
