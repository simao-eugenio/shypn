"""
Integration test for heuristic kinetics in PathwayConverter.

Tests that PathwayConverter correctly uses heuristic estimators
when no kinetic law is provided in the pathway data.
"""

import pytest
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.data.pathway.pathway_data import (
    PathwayData, ProcessedPathwayData, Species, Reaction
)
from shypn.data.pathway.pathway_converter import PathwayConverter
from shypn.data.pathway.pathway_postprocessor import PathwayPostProcessor


class TestHeuristicIntegration:
    """Test heuristic integration in pathway conversion."""
    
    def test_reaction_without_kinetic_law_uses_heuristics(self):
        """Reactions without kinetic laws get heuristic estimation."""
        # Create simple pathway without kinetic laws
        glucose = Species(
            id="glucose",
            name="Glucose",
            compartment="cytosol",
            initial_concentration=10.0
        )
        
        g6p = Species(
            id="g6p",
            name="Glucose-6-phosphate",
            compartment="cytosol",
            initial_concentration=0.0
        )
        
        # Reaction WITHOUT kinetic law
        hexokinase = Reaction(
            id="hexokinase",
            name="Hexokinase",
            reactants=[("glucose", 1.0)],
            products=[("g6p", 1.0)],
            kinetic_law=None  # No kinetic law - should trigger heuristics
        )
        
        pathway = PathwayData(
            species=[glucose, g6p],
            reactions=[hexokinase],
            compartments={"cytosol": "Cytoplasm"},
            metadata={"name": "Test Pathway"}
        )
        
        # Post-process
        postprocessor = PathwayPostProcessor()
        processed = postprocessor.process(pathway)
        
        # Convert (should use heuristics)
        converter = PathwayConverter()
        document = converter.convert(processed)
        
        # Verify transition was created
        assert len(document.transitions) == 1
        transition = document.transitions[0]
        
        # Verify heuristic kinetics were applied
        assert transition.transition_type == "continuous"
        assert 'rate_function' in transition.properties
        
        # Verify rate function contains michaelis_menten
        rate_func = transition.properties['rate_function']
        assert 'michaelis_menten' in rate_func.lower()
        # Note: Places get auto-generated names (P1, P2, etc.) from DocumentModel
        assert 'P' in rate_func  # Uses place name (P1, P2, etc.)
        
        # Verify parameters were estimated (Vmax should be ~10.0)
        assert transition.rate > 0
        assert transition.rate == 10.0  # Default Vmax for single product stoich=1
    
    def test_multiple_substrates_sequential_mm(self):
        """Multiple substrates get sequential Michaelis-Menten."""
        atp = Species(
            id="atp",
            name="ATP",
            compartment="cytosol",
            initial_concentration=5.0
        )
        
        glucose = Species(
            id="glucose",
            name="Glucose",
            compartment="cytosol",
            initial_concentration=10.0
        )
        
        adp = Species(
            id="adp",
            name="ADP",
            compartment="cytosol",
            initial_concentration=0.0
        )
        
        g6p = Species(
            id="g6p",
            name="G6P",
            compartment="cytosol",
            initial_concentration=0.0
        )
        
        # Two substrates, no kinetic law
        hexokinase = Reaction(
            id="hexokinase",
            name="Hexokinase",
            reactants=[("atp", 1.0), ("glucose", 1.0)],
            products=[("adp", 1.0), ("g6p", 1.0)],
            kinetic_law=None
        )
        
        pathway = PathwayData(
            species=[atp, glucose, adp, g6p],
            reactions=[hexokinase],
            compartments={"cytosol": "Cytoplasm"},
            metadata={"name": "Test Pathway"}
        )
        
        postprocessor = PathwayPostProcessor()
        processed = postprocessor.process(pathway)
        
        converter = PathwayConverter()
        document = converter.convert(processed)
        
        transition = document.transitions[0]
        rate_func = transition.properties['rate_function']
        
        # Verify sequential MM format
        assert 'michaelis_menten' in rate_func.lower()
        # Places get auto-generated names (P1, P2, etc.)
        assert 'P1' in rate_func or 'P2' in rate_func
        # Second substrate as saturation term
        assert '/' in rate_func  # Division for saturation
        assert '*' in rate_func  # Multiplication for sequential
    
    def test_existing_kinetic_law_not_overridden(self):
        """Existing kinetic laws should not be replaced by heuristics."""
        from shypn.data.pathway.pathway_data import KineticLaw
        
        glucose = Species(
            id="glucose",
            name="Glucose",
            compartment="cytosol",
            initial_concentration=10.0
        )
        
        g6p = Species(
            id="g6p",
            name="G6P",
            compartment="cytosol",
            initial_concentration=0.0
        )
        
        # Reaction WITH explicit kinetic law
        hexokinase = Reaction(
            id="hexokinase",
            name="Hexokinase",
            reactants=[("glucose", 1.0)],
            products=[("g6p", 1.0)],
            kinetic_law=KineticLaw(
                formula="Vmax * glucose / (Km + glucose)",
                rate_type="michaelis_menten",
                parameters={"Vmax": 25.0, "Km": 0.5}  # Explicit parameters
            )
        )
        
        pathway = PathwayData(
            species=[glucose, g6p],
            reactions=[hexokinase],
            compartments={"cytosol": "Cytoplasm"},
            metadata={"name": "Test Pathway"}
        )
        
        postprocessor = PathwayPostProcessor()
        processed = postprocessor.process(pathway)
        
        converter = PathwayConverter()
        document = converter.convert(processed)
        
        transition = document.transitions[0]
        rate_func = transition.properties['rate_function']
        
        # Verify explicit parameters were used (not heuristic estimates)
        assert '25.0' in rate_func  # Vmax from kinetic law
        assert '0.5' in rate_func   # Km from kinetic law
        assert transition.rate == 25.0  # Should use explicit Vmax
    
    def test_reaction_with_no_substrates(self):
        """Reactions with no substrates get simple default."""
        # Production from nothing (e.g., transcription)
        mrna = Species(
            id="mrna",
            name="mRNA",
            compartment="nucleus",
            initial_concentration=0.0
        )
        
        transcription = Reaction(
            id="transcription",
            name="Transcription",
            reactants=[],  # No substrates
            products=[("mrna", 1.0)],
            kinetic_law=None
        )
        
        pathway = PathwayData(
            species=[mrna],
            reactions=[transcription],
            compartments={"nucleus": "Nucleus"},
            metadata={"name": "Test Pathway"}
        )
        
        postprocessor = PathwayPostProcessor()
        processed = postprocessor.process(pathway)
        
        converter = PathwayConverter()
        document = converter.convert(processed)
        
        transition = document.transitions[0]
        
        # Should fall back to simple default
        assert transition.transition_type == "continuous"
        assert transition.rate == 1.0
        # No rate function (can't estimate without substrates)
        assert 'rate_function' not in transition.properties or \
               transition.properties.get('rate_function') is None


class TestHeuristicParameters:
    """Test parameter estimation quality."""
    
    def test_vmax_scales_with_stoichiometry(self):
        """Vmax should scale with product stoichiometry."""
        substrate = Species(
            id="s",
            name="S",
            compartment="c",
            initial_concentration=10.0
        )
        
        product = Species(
            id="p",
            name="P",
            compartment="c",
            initial_concentration=0.0
        )
        
        # Reaction producing 2 products
        reaction = Reaction(
            id="r1",
            name="R1",
            reactants=[("s", 1.0)],
            products=[("p", 2.0)],  # Stoichiometry = 2
            kinetic_law=None
        )
        
        pathway = PathwayData(
            species=[substrate, product],
            reactions=[reaction],
            compartments={"c": "Compartment"},
            metadata={"name": "Test"}
        )
        
        postprocessor = PathwayPostProcessor()
        processed = postprocessor.process(pathway)
        
        converter = PathwayConverter()
        document = converter.convert(processed)
        
        transition = document.transitions[0]
        
        # Vmax should be 10.0 * 2 = 20.0
        assert transition.rate == 20.0
    
    def test_km_from_substrate_concentration(self):
        """Km should be estimated from substrate concentration."""
        substrate = Species(
            id="s",
            name="S",
            compartment="c",
            initial_concentration=20.0  # High concentration
        )
        
        product = Species(
            id="p",
            name="P",
            compartment="c",
            initial_concentration=0.0
        )
        
        reaction = Reaction(
            id="r1",
            name="R1",
            reactants=[("s", 1.0)],
            products=[("p", 1.0)],
            kinetic_law=None
        )
        
        pathway = PathwayData(
            species=[substrate, product],
            reactions=[reaction],
            compartments={"c": "Compartment"},
            metadata={"name": "Test"}
        )
        
        postprocessor = PathwayPostProcessor()
        processed = postprocessor.process(pathway)
        
        converter = PathwayConverter()
        document = converter.convert(processed)
        
        transition = document.transitions[0]
        rate_func = transition.properties['rate_function']
        
        # Km should be concentration / 2 = 20 / 2 = 10.0
        # (tokens are normalized: 20.0 conc -> 20 tokens)
        assert '10.0' in rate_func or '10' in rate_func  # Km parameter
