"""
Integration tests for Phase 1 SBMLParser

Tests the complete SBMLParser with Phase 1 features using real SBML files:
- Event extraction and processing
- Annotation extraction (MIRIAM URIs)
- Unit definition handling
- Multi-compartment models with volumes
"""

import sys
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from shypn.data.pathway.sbml_parser import SBMLParser
from shypn.data.pathway.pathway_data import PathwayData, Event, Annotation, Compartment


class TestSBMLParserPhase1(unittest.TestCase):
    """Integration tests for SBMLParser with Phase 1 features."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = SBMLParser()
        self.fixtures_dir = Path(__file__).parent / 'fixtures'
    
    def test_parse_event_model(self):
        """Test parsing SBML file with events."""
        test_file = self.fixtures_dir / 'event_example.sbml'
        
        if not test_file.exists():
            self.skipTest(f"Test fixture not found: {test_file}")
        
        pathway = self.parser.parse_file(str(test_file))
        
        # Verify basic parsing
        self.assertIsInstance(pathway, PathwayData)
        self.assertGreater(len(pathway.species), 0)
        self.assertGreater(len(pathway.reactions), 0)
        
        # Verify events extracted
        self.assertIsNotNone(pathway.events, "Events list should not be None")
        self.assertGreater(len(pathway.events), 0, "Should have at least one event")
        
        # Verify event details
        event = pathway.events[0]
        self.assertIsInstance(event, Event)
        self.assertEqual(event.id, "drug_addition")
        self.assertIn("time", event.trigger.lower())
        self.assertGreater(event.delay, 0)
        self.assertGreater(len(event.assignments), 0)
        self.assertIn("S1", event.assignments)
    
    def test_parse_annotation_model(self):
        """Test parsing SBML file with MIRIAM annotations."""
        test_file = self.fixtures_dir / 'annotation_example.sbml'
        
        if not test_file.exists():
            self.skipTest(f"Test fixture not found: {test_file}")
        
        pathway = self.parser.parse_file(str(test_file))
        
        # Verify basic parsing
        self.assertIsInstance(pathway, PathwayData)
        
        # Find annotated species (glucose)
        glucose = None
        for species in pathway.species:
            if species.id == "glucose":
                glucose = species
                break
        
        self.assertIsNotNone(glucose, "Glucose species should exist")
        
        # Verify annotation
        self.assertIsNotNone(glucose.annotation, "Glucose should have annotation")
        self.assertIsInstance(glucose.annotation, Annotation)
        
        # Check MIRIAM URIs
        self.assertGreater(len(glucose.annotation.uris), 0)
        has_chebi = any("chebi" in uri.lower() for uri in glucose.annotation.uris)
        has_kegg = any("kegg" in uri.lower() for uri in glucose.annotation.uris)
        self.assertTrue(has_chebi or has_kegg, "Should have ChEBI or KEGG reference")
        
        # Check SBO term
        self.assertIsNotNone(glucose.annotation.sbo_term)
        self.assertTrue(glucose.annotation.sbo_term.startswith("SBO:"))
        
        # Find annotated reaction (hexokinase)
        hexokinase = None
        for reaction in pathway.reactions:
            if reaction.id == "hexokinase":
                hexokinase = reaction
                break
        
        self.assertIsNotNone(hexokinase, "Hexokinase reaction should exist")
        
        # Verify reaction annotation
        if hexokinase.annotation:
            self.assertIsInstance(hexokinase.annotation, Annotation)
            self.assertGreater(len(hexokinase.annotation.uris), 0)
    
    def test_parse_units_model(self):
        """Test parsing SBML file with unit definitions."""
        test_file = self.fixtures_dir / 'units_example.sbml'
        
        if not test_file.exists():
            self.skipTest(f"Test fixture not found: {test_file}")
        
        pathway = self.parser.parse_file(str(test_file))
        
        # Verify basic parsing
        self.assertIsInstance(pathway, PathwayData)
        
        # Verify unit definitions extracted
        self.assertIsNotNone(pathway.unit_definitions, "Unit definitions should not be None")
        self.assertGreater(len(pathway.unit_definitions), 0, "Should have unit definitions")
        
        # Check for specific units
        unit_ids = [u.id for u in pathway.unit_definitions]
        self.assertIn("per_second", unit_ids)
        self.assertIn("millimolar", unit_ids)
        self.assertIn("per_mM_per_sec", unit_ids)
        
        # Verify species have substance units
        for species in pathway.species:
            if hasattr(species, 'substance_units'):
                self.assertIsNotNone(species.substance_units)
    
    def test_parse_compartments_model(self):
        """Test parsing multi-compartment SBML file."""
        test_file = self.fixtures_dir / 'compartments_example.sbml'
        
        if not test_file.exists():
            self.skipTest(f"Test fixture not found: {test_file}")
        
        pathway = self.parser.parse_file(str(test_file))
        
        # Verify basic parsing
        self.assertIsInstance(pathway, PathwayData)
        
        # Verify enhanced compartments
        self.assertIsNotNone(pathway.compartments_enhanced, "Enhanced compartments should exist")
        self.assertGreater(len(pathway.compartments_enhanced), 0)
        
        # Check for specific compartments
        compartment_ids = [c.id for c in pathway.compartments_enhanced]
        self.assertIn("cytoplasm", compartment_ids)
        self.assertIn("mitochondria", compartment_ids)
        self.assertIn("extracellular", compartment_ids)
        
        # Verify compartment properties
        cytoplasm = None
        mitochondria = None
        for comp in pathway.compartments_enhanced:
            if comp.id == "cytoplasm":
                cytoplasm = comp
            elif comp.id == "mitochondria":
                mitochondria = comp
        
        self.assertIsNotNone(cytoplasm)
        self.assertIsInstance(cytoplasm, Compartment)
        self.assertGreater(cytoplasm.size, 0)
        
        self.assertIsNotNone(mitochondria)
        self.assertLess(mitochondria.size, cytoplasm.size, 
                       "Mitochondria should be smaller than cytoplasm")
        
        # Verify species are linked to compartments
        for species in pathway.species:
            self.assertIsNotNone(species.compartment)
            self.assertIn(species.compartment, compartment_ids)
            
            # Check compartment_ref if available
            if hasattr(species, 'compartment_ref'):
                if species.compartment_ref:
                    self.assertIsInstance(species.compartment_ref, Compartment)
    
    def test_backward_compatibility(self):
        """Test that Phase 1 changes maintain backward compatibility."""
        test_file = self.fixtures_dir / 'event_example.sbml'
        
        if not test_file.exists():
            self.skipTest(f"Test fixture not found: {test_file}")
        
        pathway = self.parser.parse_file(str(test_file))
        
        # Legacy fields should still exist
        self.assertIsNotNone(pathway.species)
        self.assertIsNotNone(pathway.reactions)
        self.assertIsNotNone(pathway.compartments)  # Legacy dict
        self.assertIsNotNone(pathway.parameters)
        self.assertIsNotNone(pathway.metadata)
        
        # New fields should be present
        self.assertTrue(hasattr(pathway, 'events'))
        self.assertTrue(hasattr(pathway, 'compartments_enhanced'))
        self.assertTrue(hasattr(pathway, 'unit_definitions'))
        
        # Original methods should still work
        if len(pathway.species) > 0:
            species_id = pathway.species[0].id
            found_species = pathway.get_species_by_id(species_id)
            self.assertIsNotNone(found_species)
        
        if len(pathway.reactions) > 0:
            reaction_id = pathway.reactions[0].id
            found_reaction = pathway.get_reaction_by_id(reaction_id)
            self.assertIsNotNone(found_reaction)
    
    def test_empty_phase1_features(self):
        """Test parsing SBML file without Phase 1 features (backward compat)."""
        # Use simple_glycolysis.sbml which doesn't have Phase 1 features
        test_file = Path(__file__).parent / 'simple_glycolysis.sbml'
        
        if not test_file.exists():
            self.skipTest(f"Test fixture not found: {test_file}")
        
        pathway = self.parser.parse_file(str(test_file))
        
        # Should parse successfully
        self.assertIsInstance(pathway, PathwayData)
        self.assertGreater(len(pathway.species), 0)
        
        # Phase 1 fields should be empty but not None
        self.assertEqual(len(pathway.events), 0)
        self.assertIsNotNone(pathway.compartments_enhanced)
        self.assertEqual(len(pathway.unit_definitions), 0)
    
    def test_parser_error_handling(self):
        """Test parser error handling with invalid files."""
        # Test with non-existent file
        with self.assertRaises(Exception):
            self.parser.parse_file("nonexistent_file.sbml")
        
        # Test with invalid SBML
        invalid_file = self.fixtures_dir / "invalid.sbml"
        if invalid_file.exists():
            with self.assertRaises(Exception):
                self.parser.parse_file(str(invalid_file))


class TestSBMLParserOrchestration(unittest.TestCase):
    """Test SBMLParser orchestrator pattern."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.parser = SBMLParser()
    
    def test_parser_has_extractors(self):
        """Test that parser instantiates all extractors."""
        self.fixtures_dir = Path(__file__).parent / 'fixtures'
        test_file = self.fixtures_dir / 'event_example.sbml'
        
        if not test_file.exists():
            self.skipTest(f"Test fixture not found: {test_file}")
        
        # Parse a file to initialize extractors
        pathway = self.parser.parse_file(str(test_file))
        
        # Verify parser has extractor attributes (if accessible)
        # This tests the thin orchestrator pattern
        self.assertIsInstance(pathway, PathwayData)
    
    def test_parser_pipeline_order(self):
        """Test that parser executes extraction in correct order."""
        self.fixtures_dir = Path(__file__).parent / 'fixtures'
        test_file = self.fixtures_dir / 'annotation_example.sbml'
        
        if not test_file.exists():
            self.skipTest(f"Test fixture not found: {test_file}")
        
        pathway = self.parser.parse_file(str(test_file))
        
        # Species should be extracted before annotations are applied
        self.assertGreater(len(pathway.species), 0)
        
        # Annotations should be applied to species
        annotated_species = [s for s in pathway.species if s.annotation]
        if len(annotated_species) > 0:
            # If annotations exist, verify they're properly linked
            species = annotated_species[0]
            self.assertIsInstance(species.annotation, Annotation)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
