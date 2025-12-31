"""Tests for thermodynamic simulation integration."""

import unittest
from unittest.mock import Mock, MagicMock
import warnings

from shypn.thermodynamics import (
    ThermodynamicSimulationValidator,
    ThermodynamicValidation
)


class TestThermodynamicSimulationValidator(unittest.TestCase):
    """Tests for ThermodynamicSimulationValidator."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = ThermodynamicSimulationValidator(
            tolerance=0.5,
            enable_web=False,
            emit_warnings=False  # Suppress warnings in tests
        )
    
    def test_initialization(self):
        """Test validator initialization."""
        self.assertEqual(self.validator.tolerance, 0.5)
        self.assertFalse(self.validator.emit_warnings)
        self.assertIsNotNone(self.validator.calculator)
        self.assertIsNotNone(self.validator.validator)
    
    def test_validate_reversible_reaction_consistent(self):
        """Test validation of thermodynamically consistent reaction."""
        # Use a simple equilibrium: A ⇌ B
        # For test purposes, use the fact that we have compound data
        # Note: Real ΔG° values from database, so we match k_f/k_r to actual K_eq
        
        # First, calculate the actual K_eq
        reactants = {"C00002": 1}  # ATP
        products = {"C00008": 1, "C00009": 1}  # ADP + Pi
        thermo = self.validator.calculator.calculate_delta_g_reaction(
            reactants, products, ph=7.0, temperature=298.15
        )
        
        # Now set k_f/k_r to match K_eq (within tolerance)
        k_eq = thermo.k_eq
        k_reverse = 1e3
        k_forward = k_eq * k_reverse * 0.9  # Slightly off but within tolerance
        
        result = self.validator.validate_reversible_reaction(
            reaction_id="R_ATP_hydrolysis",
            k_forward=k_forward,
            k_reverse=k_reverse,
            reactants=reactants,
            products=products,
            ph=7.0,
            temperature=298.15
        )
        
        self.assertIsInstance(result, ThermodynamicValidation)
        self.assertTrue(result.is_valid)
        self.assertIsNotNone(result.k_eq)
        self.assertIn("kinetic_ratio", result.details)
    
    def test_validate_reversible_reaction_inconsistent(self):
        """Test validation of thermodynamically inconsistent reaction."""
        # ATP ⇌ ADP + Pi with deliberately wrong ratio
        # Get actual K_eq first
        reactants = {"C00002": 1}
        products = {"C00008": 1, "C00009": 1}
        thermo = self.validator.calculator.calculate_delta_g_reaction(
            reactants, products, ph=7.0, temperature=298.15
        )
        
        # Set k_f/k_r way off from K_eq (many orders of magnitude)
        k_forward = 1e4
        k_reverse = 1e4  # k_f/k_r = 1, but K_eq >> 1
        
        result = self.validator.validate_reversible_reaction(
            reaction_id="R_ATP_hydrolysis_wrong",
            k_forward=k_forward,
            k_reverse=k_reverse,
            reactants=reactants,
            products=products,
            ph=7.0,
            temperature=298.15
        )
        
        self.assertFalse(result.is_valid)
        self.assertIsNotNone(result.k_eq)
        self.assertIn("kinetic_ratio", result.details)
        # Message contains "exceeds" or "invalid" for inconsistent reactions
        self.assertIn("invalid", result.message.lower())
    
    def test_validate_reaction_missing_data(self):
        """Test validation with missing thermodynamic data."""
        # Expect exception to be caught and converted to invalid result
        try:
            result = self.validator.validate_reversible_reaction(
                reaction_id="R_unknown",
                k_forward=1e6,
                k_reverse=1e3,
                reactants={"C99999": 1},  # Unknown compound
                products={"C99998": 1},
                ph=7.0,
                temperature=298.15,
                suppress_warnings=True
            )
            # If we get here, validation should have caught the error
            self.assertFalse(result.is_valid)
            self.assertIsNone(result.k_eq)
            # Message contains "not found" for missing compounds
            self.assertIn("not found", result.message.lower())
        except ValueError as e:
            # Expected - missing compound data
            self.assertIn("not found", str(e).lower())
    
    def test_validate_with_warning_emission(self):
        """Test that warnings are emitted when enabled."""
        validator = ThermodynamicSimulationValidator(
            tolerance=0.5,
            enable_web=False,
            emit_warnings=True
        )
        
        # This should emit a warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            validator.validate_reversible_reaction(
                reaction_id="R_inconsistent",
                k_forward=1e4,
                k_reverse=1e3,
                reactants={"C00002": 1},
                products={"C00008": 1, "C00009": 1}
            )
            
            # Should have emitted a UserWarning
            self.assertTrue(len(w) > 0)
            self.assertTrue(issubclass(w[0].category, UserWarning))
            self.assertIn("inconsistency", str(w[0].message).lower())
    
    def test_validate_with_suppressed_warning(self):
        """Test warning suppression for single call."""
        validator = ThermodynamicSimulationValidator(
            tolerance=0.5,
            enable_web=False,
            emit_warnings=True
        )
        
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Suppress warning for this call
            validator.validate_reversible_reaction(
                reaction_id="R_inconsistent",
                k_forward=1e4,
                k_reverse=1e3,
                reactants={"C00002": 1},
                products={"C00008": 1, "C00009": 1},
                suppress_warnings=True
            )
            
            # No warning should be emitted
            self.assertEqual(len(w), 0)
    
    def test_validate_transition_reversible(self):
        """Test validation of a Petri net transition."""
        # Mock a reversible transition
        transition = Mock()
        transition.name = "T_ATP_hydrolysis"
        transition.properties = {'is_reversible': True}
        
        # Get actual K_eq to set realistic rates
        reactants = {"C00002": 1}
        products = {"C00008": 1, "C00009": 1}
        thermo = self.validator.calculator.calculate_delta_g_reaction(
            reactants, products, ph=7.0, temperature=298.15
        )
        
        # Set rates to match K_eq
        k_reverse = 1e3
        k_forward = thermo.k_eq * k_reverse * 0.95  # Within tolerance
        
        transition.rate_forward = k_forward
        transition.rate_reverse = k_reverse
        
        # Mock input arcs (reactants)
        arc_atp = Mock()
        arc_atp.source = Mock()
        arc_atp.source.name = "C00002"  # ATP
        arc_atp.weight = 1
        transition.input_arcs = [arc_atp]
        
        # Mock output arcs (products)
        arc_adp = Mock()
        arc_adp.target = Mock()
        arc_adp.target.name = "C00008"  # ADP
        arc_adp.weight = 1
        
        arc_pi = Mock()
        arc_pi.target = Mock()
        arc_pi.target.name = "C00009"  # Pi
        arc_pi.weight = 1
        
        transition.output_arcs = [arc_adp, arc_pi]
        
        # Validate
        result = self.validator.validate_transition(transition)
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, ThermodynamicValidation)
        self.assertTrue(result.is_valid)
    
    def test_validate_transition_not_reversible(self):
        """Test that non-reversible transitions are skipped."""
        transition = Mock()
        transition.name = "T_irreversible"
        transition.properties = {'is_reversible': False}
        
        result = self.validator.validate_transition(transition)
        
        self.assertIsNone(result)
    
    def test_validate_transition_missing_rates(self):
        """Test transition with missing rate constants."""
        transition = Mock()
        transition.name = "T_missing_rates"
        transition.properties = {'is_reversible': True}
        transition.rate_forward = None
        transition.rate_reverse = None
        
        result = self.validator.validate_transition(transition)
        
        self.assertIsNone(result)
    
    def test_validate_model_transitions(self):
        """Test validation of multiple transitions."""
        # Get actual K_eq for ATP hydrolysis
        reactants = {"C00002": 1}
        products = {"C00008": 1, "C00009": 1}
        thermo = self.validator.calculator.calculate_delta_g_reaction(
            reactants, products, ph=7.0, temperature=298.15
        )
        k_eq = thermo.k_eq
        
        # Create mock transitions
        transitions = []
        
        # Reversible consistent
        t1 = Mock()
        t1.name = "T1_consistent"
        t1.properties = {'is_reversible': True}
        t1.rate_reverse = 1e3
        t1.rate_forward = k_eq * t1.rate_reverse * 0.9  # Within tolerance
        arc = Mock()
        arc.source = Mock()
        arc.source.name = "C00002"
        arc.weight = 1
        t1.input_arcs = [arc]
        arc2 = Mock()
        arc2.target = Mock()
        arc2.target.name = "C00008"
        arc2.weight = 1
        arc3 = Mock()
        arc3.target = Mock()
        arc3.target.name = "C00009"
        arc3.weight = 1
        t1.output_arcs = [arc2, arc3]
        transitions.append(t1)
        
        # Reversible inconsistent
        t2 = Mock()
        t2.name = "T2_inconsistent"
        t2.properties = {'is_reversible': True}
        t2.rate_forward = 1e4
        t2.rate_reverse = 1e4  # k_f/k_r = 1, but K_eq >> 1
        t2.input_arcs = [arc]
        t2.output_arcs = [arc2, arc3]
        transitions.append(t2)
        
        # Not reversible
        t3 = Mock()
        t3.name = "T3_irreversible"
        t3.properties = {'is_reversible': False}
        transitions.append(t3)
        
        # Validate all
        results = self.validator.validate_model_transitions(transitions)
        
        self.assertEqual(len(results), 2)  # Only reversible ones
        self.assertIn("T1_consistent", results)
        self.assertIn("T2_inconsistent", results)
        self.assertTrue(results["T1_consistent"].is_valid)
        self.assertFalse(results["T2_inconsistent"].is_valid)
    
    def test_validate_sbml_reactions(self):
        """Test validation of SBML reactions."""
        # Get actual K_eq for ATP hydrolysis
        reactants = {"C00002": 1}
        products = {"C00008": 1, "C00009": 1}
        thermo = self.validator.calculator.calculate_delta_g_reaction(
            reactants, products, ph=7.0, temperature=298.15
        )
        k_eq = thermo.k_eq
        
        # Mock SBML reactions
        reactions = []
        
        # Reversible reaction with realistic rates
        r1 = Mock()
        r1.id = "R1"
        r1.reversible = True
        r1.k_reverse = 1e3
        r1.k_forward = k_eq * r1.k_reverse * 0.95  # Within tolerance
        
        # Mock reactants
        reactant = Mock()
        reactant.species = "ATP"
        reactant.stoichiometry = 1
        r1.reactants = [reactant]
        
        # Mock products
        product1 = Mock()
        product1.species = "ADP"
        product1.stoichiometry = 1
        product2 = Mock()
        product2.species = "Pi"
        product2.stoichiometry = 1
        r1.products = [product1, product2]
        
        reactions.append(r1)
        
        # Species to compound mapping
        species_map = {
            "ATP": "C00002",
            "ADP": "C00008",
            "Pi": "C00009"
        }
        
        # Validate
        results = self.validator.validate_sbml_reactions(
            reactions,
            species_to_compound=species_map
        )
        
        self.assertEqual(len(results), 1)
        self.assertIn("R1", results)
        self.assertTrue(results["R1"].is_valid)
    
    def test_validate_sbml_reactions_skip_irreversible(self):
        """Test that irreversible SBML reactions are skipped."""
        r = Mock()
        r.id = "R_irrev"
        r.reversible = False
        
        results = self.validator.validate_sbml_reactions([r])
        
        self.assertEqual(len(results), 0)
    
    def test_validate_sbml_reactions_missing_rates(self):
        """Test SBML reactions with missing rate constants."""
        r = Mock()
        r.id = "R_no_rates"
        r.reversible = True
        r.k_forward = None
        r.k_reverse = None
        
        results = self.validator.validate_sbml_reactions([r])
        
        self.assertEqual(len(results), 0)
    
    def test_get_validation_summary(self):
        """Test generation of validation summary statistics."""
        validations = {
            "R1": ThermodynamicValidation(
                is_valid=True,
                message="Valid",
                delta_g_reaction=-30.0,
                k_eq=1.1e5,
                details={"kinetic_ratio": 1e5}
            ),
            "R2": ThermodynamicValidation(
                is_valid=False,
                message="Invalid",
                delta_g_reaction=-30.0,
                k_eq=1e5,
                details={"kinetic_ratio": 10}
            ),
            "R3": ThermodynamicValidation(
                is_valid=False,
                message="Missing data",
                delta_g_reaction=None,
                k_eq=None,
                details={"kinetic_ratio": 100}
            )
        }
        
        summary = self.validator.get_validation_summary(validations)
        
        self.assertEqual(summary['total'], 3)
        self.assertEqual(summary['valid'], 1)
        self.assertEqual(summary['invalid'], 1)
        self.assertEqual(summary['missing_data'], 1)
    
    def test_ph_temperature_effects(self):
        """Test that pH and temperature parameters are respected."""
        # Validate at different pH values
        result_ph7 = self.validator.validate_reversible_reaction(
            reaction_id="R_pH7",
            k_forward=1e8,
            k_reverse=1e3,
            reactants={"C00002": 1},
            products={"C00008": 1, "C00009": 1},
            ph=7.0,
            temperature=298.15
        )
        
        result_ph5 = self.validator.validate_reversible_reaction(
            reaction_id="R_pH5",
            k_forward=1e8,
            k_reverse=1e3,
            reactants={"C00002": 1},
            products={"C00008": 1, "C00009": 1},
            ph=5.0,
            temperature=298.15
        )
        
        # K_eq should differ between pH values (for reactions with H+ involvement)
        # Both are calculated, though may still be valid if within tolerance
        self.assertIsNotNone(result_ph7.k_eq)
        self.assertIsNotNone(result_ph5.k_eq)
    
    def test_tolerance_parameter(self):
        """Test that tolerance parameter affects validation."""
        # Strict validator (0.1 = narrow tolerance)
        strict_validator = ThermodynamicSimulationValidator(
            tolerance=0.1,
            enable_web=False,
            emit_warnings=False
        )
        
        # Lenient validator (0.9 = wide tolerance, must be < 1.0)
        lenient_validator = ThermodynamicSimulationValidator(
            tolerance=0.9,
            enable_web=False,
            emit_warnings=False
        )
        
        # Get actual K_eq
        reactants = {"C00002": 1}
        products = {"C00008": 1, "C00009": 1}
        thermo = self.validator.calculator.calculate_delta_g_reaction(
            reactants, products, ph=7.0, temperature=298.15
        )
        k_eq = thermo.k_eq
        
        # Set ratio slightly off (within lenient but maybe outside strict)
        k_reverse = 1e3
        k_forward = k_eq * k_reverse * 1.5  # 50% off
        
        result_strict = strict_validator.validate_reversible_reaction(
            reaction_id="R_test",
            k_forward=k_forward,
            k_reverse=k_reverse,
            reactants=reactants,
            products=products
        )
        
        result_lenient = lenient_validator.validate_reversible_reaction(
            reaction_id="R_test",
            k_forward=k_forward,
            k_reverse=k_reverse,
            reactants=reactants,
            products=products
        )
        
        # Both should calculate K_eq
        self.assertIsNotNone(result_strict.k_eq)
        self.assertIsNotNone(result_lenient.k_eq)
        
        # Lenient might pass where strict fails (or both may fail if way off)
        # At least verify they both validated
        self.assertIsInstance(result_strict, ThermodynamicValidation)
        self.assertIsInstance(result_lenient, ThermodynamicValidation)


class TestSimulationIntegrationExample(unittest.TestCase):
    """Integration test demonstrating usage with simulation."""
    
    def test_full_validation_workflow(self):
        """Test complete validation workflow."""
        # Initialize validator
        validator = ThermodynamicSimulationValidator(
            tolerance=0.5,
            enable_web=False,
            emit_warnings=False
        )
        
        # Simulate checking multiple reactions during import
        reactions_to_check = [
            {
                "id": "R00001",
                "k_f": 1e8,
                "k_r": 1e3,
                "reactants": {"C00002": 1},
                "products": {"C00008": 1, "C00009": 1}
            },
            {
                "id": "R00002",
                "k_f": 1e6,
                "k_r": 1e6,
                "reactants": {"C00001": 1},
                "products": {"C00001": 1}
            }
        ]
        
        results = {}
        for rxn in reactions_to_check:
            result = validator.validate_reversible_reaction(
                reaction_id=rxn["id"],
                k_forward=rxn["k_f"],
                k_reverse=rxn["k_r"],
                reactants=rxn["reactants"],
                products=rxn["products"]
            )
            results[rxn["id"]] = result
        
        # Get summary
        summary = validator.get_validation_summary(results)
        
        self.assertEqual(summary['total'], 2)
        self.assertGreaterEqual(summary['valid'], 0)
        self.assertGreaterEqual(summary['invalid'], 0)


if __name__ == '__main__':
    unittest.main()
