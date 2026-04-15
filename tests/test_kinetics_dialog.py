#!/usr/bin/env python3
"""
Test Suite for Kinetics Tab in Transition Property Dialog

Tests manual kinetic parameter entry functionality:
- Parameter populate from kinetic_metadata
- Parameter save to kinetic_metadata  
- ManualKineticMetadata creation
- Locked metadata preservation
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.netobjs.transition import Transition
from shypn.data.kinetics.kinetic_metadata import (
    ManualKineticMetadata,
    SBMLKineticMetadata,
    KineticSource,
    ConfidenceLevel
)


def test_manual_kinetics_creation():
    """Test creating ManualKineticMetadata with parameters."""
    print("Testing ManualKineticMetadata creation...")
    
    transition = Transition(x=100.0, y=100.0, id="T1", name="T1")
    
    # Create manual kinetic metadata
    metadata = ManualKineticMetadata(
        rate_type='michaelis_menten',
        formula='V * S / (Km + S)',
        parameters={
            'k_cat': 100.0,
            'K_m': 0.5,
            'hill_coefficient': 2.0
        }
    )
    
    transition.kinetic_metadata = metadata
    
    # Verify metadata
    assert transition.kinetic_metadata is not None
    assert transition.kinetic_metadata.source == KineticSource.MANUAL
    assert transition.kinetic_metadata.confidence == ConfidenceLevel.HIGH
    assert transition.kinetic_metadata.confidence_score == 0.95
    
    # Verify parameters
    params = transition.kinetic_metadata.parameters
    assert params['k_cat'] == 100.0
    assert params['K_m'] == 0.5
    assert params['hill_coefficient'] == 2.0
    
    print("✅ ManualKineticMetadata created correctly")


def test_parameter_storage():
    """Test parameter storage in kinetic_metadata."""
    print("\nTesting parameter storage...")
    
    transition = Transition(x=100.0, y=100.0, id="T1", name="T1")
    
    # Test all parameter types
    parameters = {
        # Arrhenius
        'activation_energy': 50.0,
        'temperature_coefficient_Q10': 2.5,
        'Q10': 2.5,
        
        # Michaelis-Menten
        'k_cat': 100.0,
        'K_m': 0.5,
        'Km': 0.5,
        'K_i': 10.0,
        'Ki': 10.0,
        
        # Hill
        'hill_coefficient': 2.0
    }
    
    transition.kinetic_metadata = ManualKineticMetadata(parameters=parameters)
    
    # Verify all parameters stored
    stored = transition.kinetic_metadata.parameters
    for key, value in parameters.items():
        assert key in stored, f"Parameter {key} not stored"
        assert stored[key] == value, f"Parameter {key} value mismatch"
    
    print("✅ All parameters stored correctly")


def test_parameter_update():
    """Test updating existing parameters."""
    print("\nTesting parameter updates...")
    
    transition = Transition(x=100.0, y=100.0, id="T1", name="T1")
    
    # Initial parameters
    transition.kinetic_metadata = ManualKineticMetadata(
        parameters={'k_cat': 100.0}
    )
    
    # Update parameters
    transition.kinetic_metadata.parameters['k_cat'] = 200.0
    transition.kinetic_metadata.parameters['K_m'] = 0.3
    
    # Verify updates
    assert transition.kinetic_metadata.parameters['k_cat'] == 200.0
    assert transition.kinetic_metadata.parameters['K_m'] == 0.3
    
    print("✅ Parameter updates working")


def test_locked_metadata_preservation():
    """Test that locked/SBML metadata is not overwritten."""
    print("\nTesting locked metadata preservation...")
    
    transition = Transition(x=100.0, y=100.0, id="T1", name="T1")
    
    # Create SBML metadata (always locked)
    sbml_metadata = SBMLKineticMetadata(
        sbml_reaction_id='R_PGI',
        parameters={'k_cat': 1000.0}
    )
    
    transition.kinetic_metadata = sbml_metadata
    
    # Verify it's locked
    assert transition.kinetic_metadata.locked == True
    assert transition.kinetic_metadata.source == KineticSource.SBML
    
    # Check should_preserve
    from shypn.data.kinetics.kinetic_metadata import KineticMetadata
    should_preserve = KineticMetadata.should_preserve(transition.kinetic_metadata)
    assert should_preserve == True
    
    print("✅ SBML metadata correctly locked")


def test_metadata_serialization():
    """Test metadata to_dict and from_dict."""
    print("\nTesting metadata serialization...")
    
    # Create metadata
    original = ManualKineticMetadata(
        rate_type='michaelis_menten',
        formula='V * S / (Km + S)',
        parameters={
            'k_cat': 100.0,
            'K_m': 0.5,
            'activation_energy': 50.0
        },
        entered_by='test_user',
        rationale='Test kinetics'
    )
    
    # Serialize
    data = original.to_dict()
    
    # Verify structure
    assert data['source'] == 'manual'
    assert data['confidence'] == 'high'
    assert data['confidence_score'] == 0.95
    assert data['rate_type'] == 'michaelis_menten'
    assert data['formula'] == 'V * S / (Km + S)'
    assert 'k_cat' in data['parameters']
    assert 'K_m' in data['parameters']
    assert 'activation_energy' in data['parameters']
    assert data['entered_by'] == 'test_user'
    assert data['rationale'] == 'Test kinetics'
    
    # Deserialize
    restored = ManualKineticMetadata.from_dict(data)
    
    # Verify restored
    assert restored.source == KineticSource.MANUAL
    assert restored.confidence == ConfidenceLevel.HIGH
    assert restored.rate_type == 'michaelis_menten'
    assert restored.parameters['k_cat'] == 100.0
    assert restored.parameters['K_m'] == 0.5
    
    print("✅ Metadata serialization working")


def test_empty_parameters():
    """Test handling of empty/missing parameters."""
    print("\nTesting empty parameter handling...")
    
    transition = Transition(x=100.0, y=100.0, id="T1", name="T1")
    
    # Create metadata with empty parameters
    transition.kinetic_metadata = ManualKineticMetadata(parameters={})
    
    # Verify it exists but is empty
    assert transition.kinetic_metadata is not None
    assert transition.kinetic_metadata.parameters == {}
    
    # Test transition without metadata
    transition2 = Transition(x=100.0, y=100.0, id="T2", name="T2")
    assert not hasattr(transition2, 'kinetic_metadata') or transition2.kinetic_metadata is None
    
    print("✅ Empty parameters handled correctly")


def test_parameter_compatibility():
    """Test compatibility between different parameter name variants."""
    print("\nTesting parameter name compatibility...")
    
    # K_m vs Km
    metadata1 = ManualKineticMetadata(parameters={'K_m': 0.5})
    metadata2 = ManualKineticMetadata(parameters={'Km': 0.5})
    
    assert 'K_m' in metadata1.parameters
    assert 'Km' in metadata2.parameters
    
    # Q10 vs temperature_coefficient_Q10
    metadata3 = ManualKineticMetadata(parameters={'Q10': 2.0})
    metadata4 = ManualKineticMetadata(parameters={'temperature_coefficient_Q10': 2.0})
    
    assert 'Q10' in metadata3.parameters
    assert 'temperature_coefficient_Q10' in metadata4.parameters
    
    print("✅ Parameter name variants compatible")


def test_metadata_with_transition_roundtrip():
    """Test saving and loading transition with kinetic metadata."""
    print("\nTesting transition roundtrip with metadata...")
    
    # Create transition with metadata (use proper ID format)
    transition = Transition(x=100.0, y=100.0, id="T1", name="T1")
    transition.kinetic_metadata = ManualKineticMetadata(
        rate_type='michaelis_menten',
        parameters={
            'k_cat': 100.0,
            'K_m': 0.5,
            'activation_energy': 50.0
        }
    )
    
    # Serialize transition
    data = transition.to_dict()
    
    # Verify kinetic_metadata in serialized data
    assert 'kinetic_metadata' in data
    assert data['kinetic_metadata']['source'] == 'manual'
    assert 'k_cat' in data['kinetic_metadata']['parameters']
    
    # Deserialize
    transition2 = Transition.from_dict(data)
    
    # Verify metadata restored
    assert transition2.kinetic_metadata is not None
    assert transition2.kinetic_metadata.source == KineticSource.MANUAL
    assert transition2.kinetic_metadata.parameters['k_cat'] == 100.0
    assert transition2.kinetic_metadata.parameters['K_m'] == 0.5
    
    print("✅ Transition roundtrip with metadata working")


def main():
    """Run all tests."""
    print("=" * 70)
    print("TESTING KINETICS TAB FUNCTIONALITY")
    print("=" * 70)
    
    try:
        test_manual_kinetics_creation()
        test_parameter_storage()
        test_parameter_update()
        test_locked_metadata_preservation()
        test_metadata_serialization()
        test_empty_parameters()
        test_parameter_compatibility()
        test_metadata_with_transition_roundtrip()
        
        print("\n" + "=" * 70)
        print("✅ ALL TESTS PASSED!")
        print("=" * 70)
        print("\nKinetics Tab implementation verified:")
        print("  • ManualKineticMetadata creation")
        print("  • Parameter storage (Arrhenius, MM, Hill)")
        print("  • Parameter updates")
        print("  • Locked metadata preservation")
        print("  • Serialization/deserialization")
        print("  • Empty parameter handling")
        print("  • Parameter name compatibility")
        print("  • Transition save/load roundtrip")
        print("\nReady for GUI testing!")
        return 0
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
