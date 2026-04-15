"""
Unit tests for Phase 1 Extractors

Tests all new extractors from Phase 1:
- EventExtractor
- AnnotationExtractor  
- UnitExtractor
- Enhanced CompartmentExtractor
"""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from shypn.data.pathway.extractors import (
    EventExtractor,
    AnnotationExtractor,
    UnitExtractor,
    CompartmentExtractor,
)
from shypn.data.pathway.pathway_data import Event, Annotation, Compartment, UnitDefinition


class TestEventExtractor(unittest.TestCase):
    """Test EventExtractor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = EventExtractor()
        
        # Mock libsbml model
        self.mock_model = Mock()
        self.mock_event = Mock()
        
        # Configure event mock
        self.mock_event.getId.return_value = "drug_addition"
        self.mock_event.getName.return_value = "Drug Addition Event"
        
        # Mock trigger
        mock_trigger = Mock()
        mock_trigger_math = Mock()
        mock_trigger_math.toInfix.return_value = "time >= 10.0"
        mock_trigger.getMath.return_value = mock_trigger_math
        self.mock_event.getTrigger.return_value = mock_trigger
        
        # Mock delay
        mock_delay = Mock()
        mock_delay_math = Mock()
        mock_delay_math.toInfix.return_value = "2.0"
        mock_delay.getMath.return_value = mock_delay_math
        self.mock_event.getDelay.return_value = mock_delay
        
        # Mock priority
        mock_priority = Mock()
        mock_priority_math = Mock()
        mock_priority_math.toInfix.return_value = "1"
        mock_priority.getMath.return_value = mock_priority_math
        self.mock_event.getPriority.return_value = mock_priority
        
        # Mock event assignments
        mock_assignment = Mock()
        mock_assignment.getVariable.return_value = "S1"
        mock_assignment_math = Mock()
        mock_assignment_math.toInfix.return_value = "S1 + 5.0"
        mock_assignment.getMath.return_value = mock_assignment_math
        
        self.mock_event.getNumEventAssignments.return_value = 1
        self.mock_event.getEventAssignment.return_value = mock_assignment
        
        self.mock_model.getNumEvents.return_value = 1
        self.mock_model.getEvent.return_value = self.mock_event
    
    def test_extract_events(self):
        """Test extracting events from model."""
        events = self.extractor.extract(self.mock_model)
        
        self.assertEqual(len(events), 1)
        event = events[0]
        
        self.assertIsInstance(event, Event)
        self.assertEqual(event.id, "drug_addition")
        self.assertEqual(event.trigger, "time >= 10.0")
        self.assertEqual(event.delay, 2.0)
        self.assertEqual(event.priority, 1)
        self.assertIn("S1", event.assignments)
        self.assertEqual(event.assignments["S1"], "S1 + 5.0")
    
    def test_extract_no_events(self):
        """Test extracting from model with no events."""
        self.mock_model.getNumEvents.return_value = 0
        events = self.extractor.extract(self.mock_model)
        
        self.assertEqual(len(events), 0)
    
    def test_extract_event_no_delay(self):
        """Test extracting event without delay."""
        self.mock_event.getDelay.return_value = None
        events = self.extractor.extract(self.mock_model)
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].delay, 0.0)
    
    def test_extract_event_no_priority(self):
        """Test extracting event without priority."""
        self.mock_event.getPriority.return_value = None
        events = self.extractor.extract(self.mock_model)
        
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].priority, 0)


class TestAnnotationExtractor(unittest.TestCase):
    """Test AnnotationExtractor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = AnnotationExtractor()
        
        # Mock SBML element with annotation
        self.mock_element = Mock()
        self.mock_element.isSetSBOTerm.return_value = True
        self.mock_element.getSBOTermID.return_value = "SBO:0000247"
        
        # Mock annotation XML
        mock_annotation = """
        <annotation>
          <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#"
                   xmlns:bqbiol="http://biomodels.net/biology-qualifiers/">
            <rdf:Description>
              <bqbiol:is>
                <rdf:Bag>
                  <rdf:li rdf:resource="http://identifiers.org/chebi/CHEBI:17234"/>
                  <rdf:li rdf:resource="http://identifiers.org/kegg.compound/C00031"/>
                </rdf:Bag>
              </bqbiol:is>
            </rdf:Description>
          </rdf:RDF>
        </annotation>
        """
        self.mock_element.getAnnotationString.return_value = mock_annotation
    
    def test_extract_annotation(self):
        """Test extracting annotation from element."""
        annotation = self.extractor.extract(self.mock_element)
        
        self.assertIsInstance(annotation, Annotation)
        self.assertEqual(annotation.sbo_term, "SBO:0000247")
        self.assertGreater(len(annotation.uris), 0)
        self.assertTrue(any("chebi" in uri.lower() for uri in annotation.uris))
        self.assertTrue(any("kegg" in uri.lower() for uri in annotation.uris))
    
    def test_extract_no_annotation(self):
        """Test extracting from element without annotation."""
        self.mock_element.getAnnotationString.return_value = ""
        self.mock_element.isSetSBOTerm.return_value = False
        
        annotation = self.extractor.extract(self.mock_element)
        
        self.assertIsNone(annotation)
    
    def test_parse_identifiers(self):
        """Test parsing identifiers from URIs."""
        uris = [
            "http://identifiers.org/chebi/CHEBI:17234",
            "http://identifiers.org/kegg.compound/C00031",
            "http://identifiers.org/ec-code/2.7.1.1",
        ]
        
        identifiers = self.extractor._parse_identifiers(uris)
        
        self.assertIn("chebi", identifiers)
        self.assertEqual(identifiers["chebi"], "CHEBI:17234")
        self.assertIn("kegg.compound", identifiers)
        self.assertEqual(identifiers["kegg.compound"], "C00031")
        self.assertIn("ec-code", identifiers)
        self.assertEqual(identifiers["ec-code"], "2.7.1.1")


class TestUnitExtractor(unittest.TestCase):
    """Test UnitExtractor class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = UnitExtractor()
        
        # Mock libsbml model
        self.mock_model = Mock()
        self.mock_unit_def = Mock()
        
        # Configure unit definition mock
        self.mock_unit_def.getId.return_value = "per_second"
        self.mock_unit_def.getNumUnits.return_value = 1
        
        # Mock unit
        mock_unit = Mock()
        mock_unit.getKind.return_value = 9  # UNIT_KIND_SECOND
        mock_unit.getExponent.return_value = -1
        mock_unit.getScale.return_value = 0
        mock_unit.getMultiplier.return_value = 1.0
        
        self.mock_unit_def.getUnit.return_value = mock_unit
        
        self.mock_model.getNumUnitDefinitions.return_value = 1
        self.mock_model.getUnitDefinition.return_value = self.mock_unit_def
    
    def test_extract_unit_definitions(self):
        """Test extracting unit definitions from model."""
        unit_defs = self.extractor.extract(self.mock_model)
        
        self.assertEqual(len(unit_defs), 1)
        unit_def = unit_defs[0]
        
        self.assertIsInstance(unit_def, UnitDefinition)
        self.assertEqual(unit_def.id, "per_second")
        self.assertEqual(len(unit_def.base_units), 1)
        
        kind, exp, scale, mult = unit_def.base_units[0]
        self.assertEqual(exp, -1)
        self.assertEqual(scale, 0)
        self.assertEqual(mult, 1.0)
    
    def test_extract_no_unit_definitions(self):
        """Test extracting from model with no unit definitions."""
        self.mock_model.getNumUnitDefinitions.return_value = 0
        unit_defs = self.extractor.extract(self.mock_model)
        
        self.assertEqual(len(unit_defs), 0)
    
    def test_calculate_si_conversion_simple(self):
        """Test SI conversion calculation for simple units."""
        # per_second: s^-1
        base_units = [("second", -1, 0, 1.0)]
        conversion = self.extractor._calculate_si_conversion_factor(base_units)
        self.assertEqual(conversion, 1.0)
    
    def test_calculate_si_conversion_scaled(self):
        """Test SI conversion calculation for scaled units."""
        # millisecond: 10^-3 s
        base_units = [("second", 1, -3, 1.0)]
        conversion = self.extractor._calculate_si_conversion_factor(base_units)
        self.assertEqual(conversion, 0.001)


class TestEnhancedCompartmentExtractor(unittest.TestCase):
    """Test enhanced CompartmentExtractor returning Compartment objects."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.extractor = CompartmentExtractor()
        
        # Mock libsbml model
        self.mock_model = Mock()
        self.mock_compartment = Mock()
        
        # Configure compartment mock
        self.mock_compartment.getId.return_value = "cytoplasm"
        self.mock_compartment.getName.return_value = "Cytoplasm"
        self.mock_compartment.getSize.return_value = 1.0
        self.mock_compartment.getSpatialDimensions.return_value = 3
        self.mock_compartment.getConstant.return_value = True
        
        self.mock_model.getNumCompartments.return_value = 1
        self.mock_model.getCompartment.return_value = self.mock_compartment
    
    def test_extract_compartments(self):
        """Test extracting compartments as objects."""
        compartments = self.extractor.extract(self.mock_model)
        
        self.assertEqual(len(compartments), 1)
        compartment = compartments[0]
        
        self.assertIsInstance(compartment, Compartment)
        self.assertEqual(compartment.id, "cytoplasm")
        self.assertEqual(compartment.name, "Cytoplasm")
        self.assertEqual(compartment.size, 1.0)
        self.assertEqual(compartment.spatial_dimensions, 3)
        self.assertTrue(compartment.constant)
    
    def test_extract_compartment_no_name(self):
        """Test extracting compartment without name."""
        self.mock_compartment.getName.return_value = ""
        compartments = self.extractor.extract(self.mock_model)
        
        self.assertEqual(len(compartments), 1)
        self.assertEqual(compartments[0].name, "cytoplasm")  # Uses ID as fallback
    
    def test_extract_compartment_default_size(self):
        """Test extracting compartment with default size."""
        self.mock_compartment.isSetSize.return_value = False
        self.mock_compartment.getSize.return_value = float('nan')
        compartments = self.extractor.extract(self.mock_model)
        
        self.assertEqual(len(compartments), 1)
        self.assertEqual(compartments[0].size, 1.0)  # Default size


if __name__ == '__main__':
    unittest.main()
