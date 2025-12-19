"""
Unit tests for Phase 1 Converters

Tests converter utilities from Phase 1:
- UnitConverter
- ConcentrationCalculator
"""

import sys
import unittest
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'src'))

from shypn.data.pathway.converters import UnitConverter, ConcentrationCalculator
from shypn.data.pathway.pathway_data import UnitDefinition, Compartment


class TestUnitConverter(unittest.TestCase):
    """Test UnitConverter class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample unit definitions dict
        self.unit_defs = {}
        self.converter = UnitConverter(self.unit_defs)
    
    def test_convert_time_units(self):
        """Test converting time units to SI (seconds)."""
        # Milliseconds to seconds
        unit_def = UnitDefinition(
            id="millisecond",
            base_units=[("second", 1, -3, 1.0)],
            si_conversion_factor=0.001
        )
        self.unit_defs["millisecond"] = unit_def
        
        value_in_ms = 1000.0
        value_in_s = self.converter.convert_parameter(value_in_ms, "millisecond")
        
        self.assertEqual(value_in_s, 1.0)  # 1000 ms = 1 s
    
    def test_convert_concentration_units(self):
        """Test converting concentration units."""
        # Millimolar to molar
        unit_def = UnitDefinition(
            id="millimolar",
            base_units=[("mole", 1, -3, 1.0), ("litre", -1, 0, 1.0)],
            si_conversion_factor=0.001
        )
        self.unit_defs["millimolar"] = unit_def
        
        value_in_mM = 5.0
        value_in_M = self.converter.convert_parameter(value_in_mM, "millimolar")
        
        self.assertEqual(value_in_M, 0.005)
    
    def test_no_conversion_needed(self):
        """Test when no conversion is needed."""
        unit_def = UnitDefinition(
            id="second",
            base_units=[("second", 1, 0, 1.0)],
            si_conversion_factor=1.0
        )
        self.unit_defs["second"] = unit_def
        
        value = 10.0
        converted = self.converter.convert_parameter(value, "second")
        
        self.assertEqual(converted, value)
    
    def test_convert_none_unit(self):
        """Test conversion with None unit (no conversion)."""
        value = 42.0
        converted = self.converter.convert_parameter(value, None)
        
        self.assertEqual(converted, value)


class TestConcentrationCalculator(unittest.TestCase):
    """Test ConcentrationCalculator class."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Create sample compartments dict
        self.compartments = {}
        self.calculator = ConcentrationCalculator(self.compartments)
    
    def test_concentration_to_amount(self):
        """Test converting concentration to substance amount."""
        compartment = Compartment(
            id="cell",
            name="Cell",
            size=1e-15,
            spatial_dimensions=3,
            constant=True
        )
        self.compartments["cell"] = compartment
        
        concentration = 1.0
        amount = self.calculator.concentration_to_amount(concentration, "cell")
        
        expected = 1.0 * 1e-15
        self.assertAlmostEqual(amount, expected, places=20)
    
    def test_amount_to_concentration(self):
        """Test converting substance amount to concentration."""
        compartment = Compartment(
            id="cell",
            name="Cell",
            size=1e-12,
            spatial_dimensions=3,
            constant=True
        )
        self.compartments["cell"] = compartment
        
        amount = 1e-12
        concentration = self.calculator.amount_to_concentration(amount, "cell")
        
        expected = 1e-12 / 1e-12
        self.assertAlmostEqual(concentration, expected, places=10)
    
    def test_zero_volume_handling(self):
        """Test that zero volume is handled gracefully."""
        compartment = Compartment(
            id="cell",
            name="Cell",
            size=0.0,
            spatial_dimensions=3,
            constant=True
        )
        self.compartments["cell"] = compartment
        
        # Should return original value with warning
        result = self.calculator.concentration_to_amount(1.0, "cell")
        self.assertEqual(result, 1.0)
    
    def test_unknown_compartment(self):
        """Test conversion with unknown compartment."""
        # Should assume volume=1.0 and log warning
        result = self.calculator.concentration_to_amount(5.0, "unknown_comp")
        self.assertEqual(result, 5.0)


if __name__ == '__main__':
    unittest.main()
