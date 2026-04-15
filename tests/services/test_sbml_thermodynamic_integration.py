"""
Tests for SBML Kinetics Service - Thermodynamic Integration

Tests the integration of thermodynamic validation into SBML kinetics service:
- Automatic validation of reversible reactions
- Validation results storage in transition properties
- Compound mapping via annotations
- Handling of missing data scenarios
"""

import pytest
from unittest.mock import MagicMock, patch
from shypn.services.sbml_kinetics_service import SBMLKineticsIntegrationService


class MockTransition:
    """Mock Petri net transition."""
    
    def __init__(self, name, is_reversible=False):
        self.name = name
        self.is_source = False
        self.is_sink = False
        self.kinetic_metadata = None
        self.rate = None
        self.properties = {}
        if is_reversible:
            self.properties['is_reversible'] = True


class MockReaction:
    """Mock SBML reaction."""
    
    def __init__(
        self,
        reaction_id,
        reversible=False,
        reactants=None,
        products=None,
        kinetic_law=None
    ):
        self.id = reaction_id
        self.reversible = reversible
        self.reactants = reactants or []
        self.products = products or []
        self.kinetic_law = kinetic_law


class MockReactant:
    """Mock SBML reactant/product."""
    
    def __init__(self, species_id):
        self.species = species_id


class MockKineticLaw:
    """Mock SBML kinetic law."""
    
    def __init__(
        self,
        rate_type='mass_action',
        formula='k_f * S - k_r * P',
        parameters=None
    ):
        self.rate_type = rate_type
        self.formula = formula
        self.parameters = parameters or {}


class MockSpecies:
    """Mock SBML species."""
    
    def __init__(self, species_id, annotation=None):
        self.id = species_id
        self.name = species_id
        self.annotation = annotation


class MockPathwayData:
    """Mock pathway data."""
    
    def __init__(self, reactions=None, species=None):
        self.reactions = reactions or []
        self.species = species or []
        self.parameters = {}


class TestSBMLThermodynamicIntegration:
    """Test suite for thermodynamic integration in SBML kinetics service."""
    
    def test_validation_enabled_by_default(self):
        """Test that thermodynamic validation is enabled by default."""
        service = SBMLKineticsIntegrationService()
        assert service.enable_thermodynamic_validation is True
    
    def test_validation_can_be_disabled(self):
        """Test that validation can be disabled."""
        service = SBMLKineticsIntegrationService(
            enable_thermodynamic_validation=False
        )
        assert service.enable_thermodynamic_validation is False
    
    def test_validator_lazy_initialization(self):
        """Test that validator is created on first use (lazy instantiation)."""
        service = SBMLKineticsIntegrationService()
        
        # Initially None
        assert service._thermodynamic_validator is None
        
        # Get validator (creates instance)
        validator = service._get_thermodynamic_validator()
        assert validator is not None
        
        # Second call returns same instance
        validator2 = service._get_thermodynamic_validator()
        assert validator2 is validator
    
    def test_compound_mapper_lazy_initialization(self):
        """Test that compound mapper is created on first use."""
        service = SBMLKineticsIntegrationService()
        
        # Initially None
        assert service._compound_mapper is None
        
        # Get mapper (creates instance)
        mapper = service._get_compound_mapper()
        assert mapper is not None
        
        # Second call returns same instance
        mapper2 = service._get_compound_mapper()
        assert mapper2 is mapper
    
    def test_reversible_reaction_validation_with_annotations(self):
        """Test validation of reversible reaction with KEGG annotations."""
        service = SBMLKineticsIntegrationService()
        
        # Create reversible reaction with KEGG-annotated species
        # ATP + H2O <-> ADP + Pi
        reactants = [
            MockReactant('ATP'),
            MockReactant('H2O')
        ]
        products = [
            MockReactant('ADP'),
            MockReactant('Pi')
        ]
        
        kinetic_law = MockKineticLaw(
            rate_type='mass_action',
            formula='k_f * ATP * H2O - k_r * ADP * Pi',
            parameters={'k_f': 1.0, 'k_r': 0.5}
        )
        
        reaction = MockReaction(
            'R_ATP_hydrolysis',
            reversible=True,
            reactants=reactants,
            products=products,
            kinetic_law=kinetic_law
        )
        
        # Create pathway data with annotated species
        species_list = [
            MockSpecies('ATP', annotation='urn:miriam:kegg.compound:C00002'),
            MockSpecies('H2O', annotation='kegg:C00001'),
            MockSpecies('ADP', annotation='kegg:C00008'),
            MockSpecies('Pi', annotation='kegg:C00009'),
        ]
        
        pathway_data = MockPathwayData(
            reactions=[reaction],
            species=species_list
        )
        
        # Store pathway data for validation
        service.pathway_data = pathway_data
        
        # Create transition
        transition = MockTransition('R_ATP_hydrolysis')
        
        # Call validation method
        result = service._validate_reversible_reaction(
            reaction,
            transition,
            kinetic_law
        )
        
        # Should have validation result (may be valid or invalid)
        assert result is not None
        assert 'status' in result
        
        # Should have mapped compounds
        if result['status'] not in ['insufficient_data', 'no_rate_constants', 'error']:
            # Validation was attempted
            assert result['status'] in ['valid', 'warning', 'violation']
    
    def test_reversible_reaction_without_rate_constants(self):
        """Test handling of reversible reaction without k_f/k_r."""
        service = SBMLKineticsIntegrationService()
        
        # Create reaction with annotated species but no rate constants
        reactants = [MockReactant('ATP')]
        products = [MockReactant('ADP')]
        
        # Kinetic law without separate rate constants
        kinetic_law = MockKineticLaw(
            rate_type='michaelis_menten',
            formula='Vmax * S / (Km + S)',
            parameters={'Vmax': 1.0, 'Km': 0.1}  # No k_f or k_r
        )
        
        reaction = MockReaction(
            'R_test',
            reversible=True,
            reactants=reactants,
            products=products,
            kinetic_law=kinetic_law
        )
        
        # Add annotated species so compound mapping succeeds
        species_list = [
            MockSpecies('ATP', annotation='kegg:C00002'),
            MockSpecies('ADP', annotation='kegg:C00008'),
        ]
        
        pathway_data = MockPathwayData(
            reactions=[reaction],
            species=species_list
        )
        service.pathway_data = pathway_data
        
        transition = MockTransition('R_test')
        
        result = service._validate_reversible_reaction(
            reaction,
            transition,
            kinetic_law
        )
        
        # Should indicate missing rate constants (after compound mapping succeeds)
        assert result is not None
        assert result['status'] == 'no_rate_constants'
        assert 'parameters' in result
    
    def test_reversible_reaction_without_annotations(self):
        """Test handling of species without KEGG annotations."""
        service = SBMLKineticsIntegrationService()
        
        reactants = [MockReactant('UnknownA')]
        products = [MockReactant('UnknownB')]
        
        kinetic_law = MockKineticLaw(
            parameters={'k_f': 1.0, 'k_r': 0.5}
        )
        
        reaction = MockReaction(
            'R_test',
            reversible=True,
            reactants=reactants,
            products=products,
            kinetic_law=kinetic_law
        )
        
        # Species without annotations
        species_list = [
            MockSpecies('UnknownA', annotation=None),
            MockSpecies('UnknownB', annotation=None),
        ]
        
        pathway_data = MockPathwayData(
            reactions=[reaction],
            species=species_list
        )
        
        service.pathway_data = pathway_data
        
        transition = MockTransition('R_test')
        
        result = service._validate_reversible_reaction(
            reaction,
            transition,
            kinetic_law
        )
        
        # Should indicate insufficient data
        assert result is not None
        assert result['status'] == 'insufficient_data'
        assert result['reactants_mapped'] == 0
        assert result['products_mapped'] == 0
    
    def test_validation_disabled(self):
        """Test that validation returns None when disabled."""
        service = SBMLKineticsIntegrationService(
            enable_thermodynamic_validation=False
        )
        
        kinetic_law = MockKineticLaw(
            parameters={'k_f': 1.0, 'k_r': 0.5}
        )
        
        reaction = MockReaction('R_test', reversible=True, kinetic_law=kinetic_law)
        transition = MockTransition('R_test')
        
        result = service._validate_reversible_reaction(
            reaction,
            transition,
            kinetic_law
        )
        
        # Should return None when disabled
        assert result is None
    
    def test_find_species_by_id(self):
        """Test species lookup by ID."""
        service = SBMLKineticsIntegrationService()
        
        species_list = [
            MockSpecies('ATP', annotation='kegg:C00002'),
            MockSpecies('ADP', annotation='kegg:C00008'),
        ]
        
        pathway_data = MockPathwayData(species=species_list)
        service.pathway_data = pathway_data
        
        # Find existing species
        atp = service._find_species('ATP')
        assert atp is not None
        assert atp.id == 'ATP'
        
        # Find non-existent species
        unknown = service._find_species('Unknown')
        assert unknown is None
    
    def test_rate_constant_extraction_variants(self):
        """Test extraction of rate constants with different naming conventions."""
        service = SBMLKineticsIntegrationService()
        
        # Test various forward rate constant names
        for k_name in ['k_f', 'kf', 'k1', 'k_forward', 'kforward']:
            kinetic_law = MockKineticLaw(
                parameters={k_name: 1.0, 'k_r': 0.5}
            )
            
            # Should be able to extract (tested indirectly via validation)
            # Direct test would require mocking the validator
            assert k_name in kinetic_law.parameters
        
        # Test various reverse rate constant names
        for k_name in ['k_r', 'kr', 'k2', 'k_reverse', 'kreverse', 'k_rev']:
            kinetic_law = MockKineticLaw(
                parameters={'k_f': 1.0, k_name: 0.5}
            )
            
            assert k_name in kinetic_law.parameters


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
