"""
Unit tests for Phase 1 Data Models

Tests enhanced data classes from Phase 1:
- Event
- Annotation
- Compartment (enhanced)
- UnitDefinition
"""

import sys
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from shypn.data.pathway.pathway_data import Event, Annotation, Compartment, UnitDefinition


class TestEvent(unittest.TestCase):
    """Test Event data class."""
    
    def test_create_event(self):
        """Test creating an Event instance."""
        event = Event(
            id="drug_addition",
            trigger="time >= 10.0",
            delay=2.0,
            assignments={"S1": "S1 + 5.0", "S2": "S2 * 0.5"},
            priority=1
        )
        
        self.assertEqual(event.id, "drug_addition")
        self.assertEqual(event.trigger, "time >= 10.0")
        self.assertEqual(event.delay, 2.0)
        self.assertEqual(len(event.assignments), 2)
        self.assertEqual(event.assignments["S1"], "S1 + 5.0")
        self.assertEqual(event.priority, 1)
    
    def test_event_no_delay(self):
        """Test creating event without delay."""
        event = Event(
            id="instant_event",
            trigger="S1 > threshold",
            delay=0.0,
            assignments={"S1": "0"},
            priority=0
        )
        
        self.assertEqual(event.delay, 0.0)
        self.assertEqual(event.priority, 0)
    
    def test_event_multiple_assignments(self):
        """Test event with multiple assignments."""
        assignments = {
            "species1": "species1 * 2",
            "species2": "species2 / 2",
            "parameter1": "0.5"
        }
        
        event = Event(
            id="multi_assign",
            trigger="time >= 5.0",
            delay=1.0,
            assignments=assignments,
            priority=2
        )
        
        self.assertEqual(len(event.assignments), 3)
        self.assertIn("species1", event.assignments)
        self.assertIn("species2", event.assignments)
        self.assertIn("parameter1", event.assignments)


class TestAnnotation(unittest.TestCase):
    """Test Annotation data class."""
    
    def test_create_annotation(self):
        """Test creating an Annotation instance."""
        annotation = Annotation(
            identifiers={"chebi": "CHEBI:17234", "kegg.compound": "C00031"},
            uris=[
                "http://identifiers.org/chebi/CHEBI:17234",
                "http://identifiers.org/kegg.compound/C00031"
            ],
            sbo_term="SBO:0000247"
        )
        
        self.assertEqual(len(annotation.identifiers), 2)
        self.assertEqual(annotation.identifiers["chebi"], "CHEBI:17234")
        self.assertEqual(len(annotation.uris), 2)
        self.assertEqual(annotation.sbo_term, "SBO:0000247")
    
    def test_annotation_no_sbo(self):
        """Test creating annotation without SBO term."""
        annotation = Annotation(
            identifiers={"uniprot": "P12345"},
            uris=["http://identifiers.org/uniprot/P12345"],
            sbo_term=None
        )
        
        self.assertIsNone(annotation.sbo_term)
        self.assertEqual(len(annotation.identifiers), 1)
    
    def test_annotation_empty_identifiers(self):
        """Test creating annotation with no identifiers."""
        annotation = Annotation(
            identifiers={},
            uris=[],
            sbo_term="SBO:0000247"
        )
        
        self.assertEqual(len(annotation.identifiers), 0)
        self.assertEqual(len(annotation.uris), 0)
    
    def test_annotation_multiple_databases(self):
        """Test annotation with multiple database references."""
        identifiers = {
            "chebi": "CHEBI:17234",
            "kegg.compound": "C00031",
            "pubchem.compound": "5793",
            "hmdb": "HMDB0000122"
        }
        
        annotation = Annotation(
            identifiers=identifiers,
            uris=[f"http://identifiers.org/{db}/{id_}" for db, id_ in identifiers.items()],
            sbo_term="SBO:0000247"
        )
        
        self.assertEqual(len(annotation.identifiers), 4)
        self.assertIn("chebi", annotation.identifiers)
        self.assertIn("hmdb", annotation.identifiers)


class TestCompartment(unittest.TestCase):
    """Test enhanced Compartment data class."""
    
    def test_create_compartment(self):
        """Test creating a Compartment instance."""
        compartment = Compartment(
            id="cytoplasm",
            name="Cytoplasm",
            size=1.0,
            spatial_dimensions=3,
            constant=True
        )
        
        self.assertEqual(compartment.id, "cytoplasm")
        self.assertEqual(compartment.name, "Cytoplasm")
        self.assertEqual(compartment.size, 1.0)
        self.assertEqual(compartment.spatial_dimensions, 3)
        self.assertTrue(compartment.constant)
    
    def test_compartment_default_values(self):
        """Test compartment with default values."""
        compartment = Compartment(
            id="cell",
            name="Cell"
        )
        
        self.assertEqual(compartment.size, 1.0)
        self.assertEqual(compartment.spatial_dimensions, 3)
        self.assertTrue(compartment.constant)
    
    def test_compartment_different_dimensions(self):
        """Test compartments with different spatial dimensions."""
        # 2D membrane
        membrane = Compartment(
            id="membrane",
            name="Membrane",
            size=100.0,
            spatial_dimensions=2,
            constant=True
        )
        
        self.assertEqual(membrane.spatial_dimensions, 2)
        
        # 1D line
        filament = Compartment(
            id="filament",
            name="Filament",
            size=10.0,
            spatial_dimensions=1,
            constant=True
        )
        
        self.assertEqual(filament.spatial_dimensions, 1)
    
    def test_compartment_varying_size(self):
        """Test non-constant compartment (can vary in time)."""
        compartment = Compartment(
            id="vesicle",
            name="Vesicle",
            size=0.1,
            spatial_dimensions=3,
            constant=False
        )
        
        self.assertFalse(compartment.constant)


class TestUnitDefinition(unittest.TestCase):
    """Test UnitDefinition data class."""
    
    def test_create_unit_definition(self):
        """Test creating a UnitDefinition instance."""
        unit_def = UnitDefinition(
            id="per_second",
            base_units=[("second", -1, 0, 1.0)],
            si_conversion_factor=1.0
        )
        
        self.assertEqual(unit_def.id, "per_second")
        self.assertEqual(len(unit_def.base_units), 1)
        self.assertEqual(unit_def.si_conversion_factor, 1.0)
        
        kind, exp, scale, mult = unit_def.base_units[0]
        self.assertEqual(kind, "second")
        self.assertEqual(exp, -1)
        self.assertEqual(scale, 0)
        self.assertEqual(mult, 1.0)
    
    def test_compound_unit_definition(self):
        """Test unit definition with multiple base units."""
        # molar: mol / L
        unit_def = UnitDefinition(
            id="molar",
            base_units=[
                ("mole", 1, 0, 1.0),
                ("litre", -1, 0, 1.0)
            ],
            si_conversion_factor=1.0
        )
        
        self.assertEqual(len(unit_def.base_units), 2)
        
        mol_unit = unit_def.base_units[0]
        self.assertEqual(mol_unit[0], "mole")
        self.assertEqual(mol_unit[1], 1)
        
        litre_unit = unit_def.base_units[1]
        self.assertEqual(litre_unit[0], "litre")
        self.assertEqual(litre_unit[1], -1)
    
    def test_scaled_unit_definition(self):
        """Test unit definition with scale factor."""
        # millisecond: 10^-3 s
        unit_def = UnitDefinition(
            id="millisecond",
            base_units=[("second", 1, -3, 1.0)],
            si_conversion_factor=0.001
        )
        
        self.assertEqual(unit_def.si_conversion_factor, 0.001)
        
        kind, exp, scale, mult = unit_def.base_units[0]
        self.assertEqual(scale, -3)
    
    def test_unit_with_multiplier(self):
        """Test unit definition with multiplier."""
        # minute: 60 s
        unit_def = UnitDefinition(
            id="minute",
            base_units=[("second", 1, 0, 60.0)],
            si_conversion_factor=60.0
        )
        
        kind, exp, scale, mult = unit_def.base_units[0]
        self.assertEqual(mult, 60.0)
    
    def test_complex_rate_unit(self):
        """Test complex rate constant unit."""
        # per_mM_per_sec: (mol/L)^-1 s^-1 with scale factor
        unit_def = UnitDefinition(
            id="per_mM_per_sec",
            base_units=[
                ("mole", -1, 3, 1.0),    # mol^-1 * 10^3
                ("litre", 1, 0, 1.0),    # L
                ("second", -1, 0, 1.0),  # s^-1
            ],
            si_conversion_factor=1000.0
        )
        
        self.assertEqual(len(unit_def.base_units), 3)
        self.assertEqual(unit_def.si_conversion_factor, 1000.0)


if __name__ == '__main__':
    unittest.main()
