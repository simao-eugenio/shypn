"""
Unit tests for SBML kinetics integration.

Tests the integration of SBML kinetic data with Transition objects.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from shypn.netobjs.transition import Transition
from shypn.data.pathway.pathway_data import PathwayData, Reaction, KineticLaw
from shypn.data.kinetics import (
    SBMLKineticMetadata,
    KineticSource,
    ConfidenceLevel,
)
from shypn.services.sbml_kinetics_service import SBMLKineticsIntegrationService


def test_sbml_metadata_creation():
    """Test creating SBML kinetic metadata."""
    print("Test 1: SBML metadata creation")
    
    metadata = SBMLKineticMetadata(
        source_file="test.sbml",
        rate_type="michaelis_menten",
        formula="Vmax * S / (Km + S)",
        parameters={"Vmax": 10.0, "Km": 0.5},
        sbml_level=3,
        sbml_version=2,
        sbml_reaction_id="R1",
    )
    
    # Check defaults
    assert metadata.source == KineticSource.SBML
    assert metadata.confidence == ConfidenceLevel.DEFINITIVE
    assert metadata.confidence_score == 1.0
    assert metadata.locked is True
    
    print("  ✓ SBML metadata created with correct defaults")
    print(f"  ✓ Confidence: {metadata.confidence.value} ({metadata.confidence_score})")
    print(f"  ✓ Locked: {metadata.locked}")


def test_metadata_serialization():
    """Test metadata serialization/deserialization."""
    print("\nTest 2: Metadata serialization")
    
    metadata = SBMLKineticMetadata(
        source_file="test.sbml",
        rate_type="michaelis_menten",
        formula="Vmax * S / (Km + S)",
        parameters={"Vmax": 10.0, "Km": 0.5},
        sbml_level=3,
        sbml_reaction_id="R1",
    )
    
    # Serialize
    data = metadata.to_dict()
    assert data['source'] == 'sbml'
    assert data['confidence'] == 'definitive'
    assert data['rate_type'] == 'michaelis_menten'
    assert data['sbml_level'] == 3
    
    print("  ✓ Metadata serialized correctly")
    print(f"  ✓ Keys: {list(data.keys())[:5]}...")


def test_transition_metadata_attachment():
    """Test attaching metadata to Transition."""
    print("\nTest 3: Transition metadata attachment")
    
    # Create transition
    transition = Transition(
        x=100.0, y=100.0,
        id="T1", name="T1",
        label="Hexokinase"
    )
    
    # Create and attach metadata
    metadata = SBMLKineticMetadata(
        source_file="glycolysis.sbml",
        rate_type="michaelis_menten",
        formula="Vmax * Glucose / (Km + Glucose)",
        parameters={"Vmax": 10.0, "Km": 0.5},
    )
    
    transition.kinetic_metadata = metadata
    
    # Verify attachment (using object reference, no IDs)
    assert transition.kinetic_metadata is metadata
    assert transition.kinetic_metadata.source == KineticSource.SBML
    
    print("  ✓ Metadata attached to transition using object reference")
    print(f"  ✓ Source: {transition.kinetic_metadata.source.value}")
    print(f"  ✓ Formula: {transition.kinetic_metadata.formula[:30]}...")


def test_transition_serialization_with_metadata():
    """Test transition serialization with kinetic metadata."""
    print("\nTest 4: Transition serialization with metadata")
    
    # Create transition with metadata
    transition = Transition(
        x=100.0, y=100.0,
        id="T1", name="T1"
    )
    
    transition.kinetic_metadata = SBMLKineticMetadata(
        source_file="test.sbml",
        rate_type="mass_action",
        formula="k * A * B",
        parameters={"k": 2.5},
    )
    
    # Serialize
    data = transition.to_dict()
    
    assert 'kinetic_metadata' in data
    assert data['kinetic_metadata']['source'] == 'sbml'
    assert data['kinetic_metadata']['rate_type'] == 'mass_action'
    
    # Deserialize
    transition2 = Transition.from_dict(data)
    
    assert transition2.kinetic_metadata is not None
    assert transition2.kinetic_metadata.source == KineticSource.SBML
    assert transition2.kinetic_metadata.rate_type == 'mass_action'
    
    print("  ✓ Transition serialized with metadata")
    print("  ✓ Transition deserialized with metadata intact")


def test_integration_service():
    """Test SBML kinetics integration service."""
    print("\nTest 5: Integration service")
    
    # Create transitions
    transitions = [
        Transition(100, 100, "T1", "R1", label="Hexokinase"),
        Transition(200, 100, "T2", "R2", label="PGI"),
    ]
    
    # Create pathway data with reactions
    kinetic_law1 = KineticLaw(
        formula="Vmax * S / (Km + S)",
        rate_type="michaelis_menten",
        parameters={"Vmax": 10.0, "Km": 0.5}
    )
    kinetic_law1.sbml_metadata = {
        'sbml_level': 3,
        'sbml_version': 2,
        'sbml_reaction_id': 'R1',
    }
    
    pathway_data = PathwayData(
        reactions=[
            Reaction(
                id="R1",
                name="Hexokinase",
                kinetic_law=kinetic_law1
            ),
            Reaction(
                id="R2",
                name="PGI",
                kinetic_law=None  # No kinetics
            ),
        ]
    )
    
    # Integrate kinetics
    service = SBMLKineticsIntegrationService()
    results = service.integrate_kinetics(
        transitions,
        pathway_data,
        source_file="test.sbml"
    )
    
    # Check results
    assert results["R1"] is True  # Should integrate
    assert results["R2"] is False  # No kinetics to integrate
    
    # Check transition 1 has metadata (using object reference)
    assert transitions[0].kinetic_metadata is not None
    assert transitions[0].kinetic_metadata.source == KineticSource.SBML
    assert transitions[0].kinetic_metadata.formula == "Vmax * S / (Km + S)"
    
    # Check transition 2 has no metadata
    assert transitions[1].kinetic_metadata is None
    
    print("  ✓ Integration service works correctly")
    print(f"  ✓ Transition 1 has SBML kinetics: {transitions[0].kinetic_metadata.rate_type}")
    print(f"  ✓ Transition 2 has no kinetics: {transitions[1].kinetic_metadata}")


def test_preservation_logic():
    """Test that SBML kinetics are preserved."""
    print("\nTest 6: Preservation logic")
    
    # Create transition with existing SBML kinetics
    transition = Transition(100, 100, "T1", "R1")
    transition.kinetic_metadata = SBMLKineticMetadata(
        source_file="original.sbml",
        rate_type="michaelis_menten",
        formula="ORIGINAL",
        parameters={"Vmax": 5.0},
    )
    
    # Try to integrate different kinetics
    pathway_data = PathwayData(
        reactions=[
            Reaction(
                id="R1",
                kinetic_law=KineticLaw(
                    formula="NEW_FORMULA",
                    rate_type="mass_action",
                    parameters={"k": 1.0}
                )
            )
        ]
    )
    
    service = SBMLKineticsIntegrationService()
    results = service.integrate_kinetics(
        [transition],
        pathway_data,
        source_file="new.sbml"
    )
    
    # Should NOT integrate (preserved)
    assert results["R1"] is False
    assert transition.kinetic_metadata.formula == "ORIGINAL"
    assert transition.kinetic_metadata.source_file == "original.sbml"
    
    print("  ✓ SBML kinetics preserved (not overwritten)")
    print(f"  ✓ Original formula intact: {transition.kinetic_metadata.formula}")


def run_all_tests():
    """Run all tests."""
    print("=" * 60)
    print("SBML Kinetics Integration Tests")
    print("=" * 60)
    
    try:
        test_sbml_metadata_creation()
        test_metadata_serialization()
        test_transition_metadata_attachment()
        test_transition_serialization_with_metadata()
        test_integration_service()
        test_preservation_logic()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        return True
        
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)
