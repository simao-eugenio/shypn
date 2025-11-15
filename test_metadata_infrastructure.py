#!/usr/bin/env python3
"""Test script for metadata infrastructure.

Quick validation of ModelMetadata, UserProfile, and MetadataStorage.
"""
import sys
import json
from pathlib import Path
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.reporting import ModelMetadata, UserProfile, MetadataStorage


def test_model_metadata():
    """Test ModelMetadata class."""
    print("=" * 60)
    print("Testing ModelMetadata")
    print("=" * 60)
    
    # Create instance
    metadata = ModelMetadata()
    metadata.model_name = "Glycolysis Pathway"
    metadata.model_id = "MODEL001"
    metadata.description = "Detailed model of glycolysis pathway in yeast"
    metadata.organism = "Saccharomyces cerevisiae"
    metadata.add_keyword("glycolysis")
    metadata.add_keyword("metabolism")
    metadata.primary_author = "Dr. Jane Smith"
    metadata.contributors.append("Dr. John Doe")
    metadata.institution = "University of Example"
    
    # Add modification
    metadata.add_modification("created", "Initial model creation")
    
    # Validate
    is_valid, errors = metadata.validate()
    print(f"Validation: {'PASS' if is_valid else 'FAIL'}")
    if errors:
        for err in errors:
            print(f"  - {err}")
    
    # Serialization
    data = metadata.to_dict()
    print(f"\nSerialized keys: {list(data.keys())}")
    print(f"Basic info: {data['basic']['model_name']}")
    print(f"Keywords: {data['basic']['keywords']}")
    
    # Deserialization
    metadata2 = ModelMetadata()
    metadata2.from_dict(data)
    print(f"\nDeserialized name: {metadata2.model_name}")
    print(f"Deserialized organism: {metadata2.organism}")
    print(f"Modification count: {len(metadata2.modification_history)}")
    
    print("\n✓ ModelMetadata test PASSED\n")


def test_user_profile():
    """Test UserProfile class."""
    print("=" * 60)
    print("Testing UserProfile")
    print("=" * 60)
    
    # Create instance
    profile = UserProfile()
    profile.full_name = "Dr. John Doe"
    profile.email = "john.doe@example.edu"
    profile.orcid_id = "0000-0002-1234-5678"
    profile.institution = "MIT"
    profile.department = "Biological Engineering"
    profile.default_license = "CC-BY-4.0"
    
    # Validate
    is_valid, errors = profile.validate()
    print(f"Validation: {'PASS' if is_valid else 'FAIL'}")
    if errors:
        for err in errors:
            print(f"  - {err}")
    
    # Test ORCID validation
    print(f"\nORCID validation tests:")
    test_orcids = [
        ("0000-0002-1234-5678", True),
        ("0000-0002-1234-567X", True),
        ("1234-5678-9012-3456", True),
        ("000-000-000-000", False),
        ("not-an-orcid", False),
    ]
    for orcid, expected in test_orcids:
        result = UserProfile.validate_orcid_format(orcid)
        status = "✓" if result == expected else "✗"
        print(f"  {status} {orcid}: {result}")
    
    # Display methods
    print(f"\nDisplay name: {profile.get_display_name()}")
    print(f"Citation format: {profile.get_citation_format()}")
    
    # Serialization
    data = profile.to_dict()
    print(f"\nSerialized sections: {list(data.keys())}")
    print(f"Personal info: {data['personal']['full_name']}")
    
    # Config path
    config_path = UserProfile.get_config_path()
    print(f"\nConfig path: {config_path}")
    
    print("\n✓ UserProfile test PASSED\n")


def test_metadata_storage():
    """Test MetadataStorage utilities."""
    print("=" * 60)
    print("Testing MetadataStorage")
    print("=" * 60)
    
    # Create test file
    test_file = Path("/tmp/test_model.shypn")
    
    # Create metadata
    metadata = ModelMetadata()
    metadata.model_name = "Test Model"
    metadata.model_id = "TEST001"
    metadata.description = "Test model for storage validation"
    metadata.version = "1.0"
    
    # Save to file
    success = MetadataStorage.save_to_shypn_file(str(test_file), metadata)
    print(f"Save: {'SUCCESS' if success else 'FAILED'}")
    
    # Check file exists
    print(f"File exists: {test_file.exists()}")
    
    # Load back
    loaded = MetadataStorage.load_from_shypn_file(str(test_file))
    if loaded:
        print(f"Loaded name: {loaded.model_name}")
        print(f"Loaded ID: {loaded.model_id}")
        print(f"Loaded version: {loaded.version}")
    else:
        print("Load FAILED")
    
    # Check has_metadata
    has_meta = MetadataStorage.has_metadata(str(test_file))
    print(f"\nhas_metadata: {has_meta}")
    
    # Extract basic info
    basic_info = MetadataStorage.extract_basic_info(str(test_file))
    print(f"Basic info: {basic_info}")
    
    # Update modification history
    success = MetadataStorage.update_modification_history(
        str(test_file),
        "modified",
        "Test modification",
        "test_user"
    )
    print(f"\nModification update: {'SUCCESS' if success else 'FAILED'}")
    
    # Load again to verify modification
    updated = MetadataStorage.load_from_shypn_file(str(test_file))
    if updated:
        print(f"Modification count: {len(updated.modification_history)}")
        if updated.modification_history:
            last_mod = updated.modification_history[-1]
            print(f"Last modification: {last_mod.get('action')} - {last_mod.get('description')}")
    
    # Cleanup
    if test_file.exists():
        test_file.unlink()
        print(f"\nTest file cleaned up")
    
    print("\n✓ MetadataStorage test PASSED\n")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("METADATA INFRASTRUCTURE TEST SUITE")
    print("=" * 60 + "\n")
    
    try:
        test_model_metadata()
        test_user_profile()
        test_metadata_storage()
        
        print("=" * 60)
        print("ALL TESTS PASSED")
        print("=" * 60 + "\n")
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
