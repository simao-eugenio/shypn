#!/usr/bin/env python3
"""
Metadata Management System - Demo Example

This script demonstrates the complete metadata management system workflow.

Author: Shypn Development Team
Date: October 2025
"""

from pathlib import Path
import sys
import json
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.shypn.crossfetch.metadata import (
    create_metadata_manager,
    FileOperationsTracker,
    MetadataManagerFactory,
    MetadataFormat
)


def print_section(title):
    """Print section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


def demo_basic_usage():
    """Demonstrate basic metadata management."""
    print_section("Basic Usage")
    
    # Create metadata manager
    pathway_file = Path("demo_pathway.shy")
    manager = create_metadata_manager(pathway_file)
    
    print(f"\n✅ Created manager for: {pathway_file.name}")
    print(f"   Metadata file: {manager.get_path().name}")
    
    # Create metadata
    manager.create({
        "project": "demo_project",
        "description": "Demonstration pathway"
    })
    print(f"\n✅ Created metadata file")
    
    # Add enrichment record
    manager.add_enrichment_record(
        data_type="coordinates",
        source="KEGG",
        quality_score=0.85,
        fields_enriched=["species[0].x", "species[0].y"],
        details={
            "pathway_id": "hsa00010",
            "confidence": "high"
        }
    )
    print(f"\n✅ Added enrichment record:")
    print(f"   Data type: coordinates")
    print(f"   Source: KEGG")
    print(f"   Quality: 0.85")
    
    # Log operation
    manager.log_operation("save", {
        "user": "demo_user",
        "changes": {"added": ["species1", "reaction1"]}
    })
    print(f"\n✅ Logged save operation")
    
    # Get enrichment history
    history = manager.get_enrichment_history()
    print(f"\n✅ Enrichment history: {len(history)} record(s)")
    
    # Get statistics
    stats = manager.get_statistics()
    print(f"\n✅ Statistics:")
    print(f"   Total enrichments: {stats['total_enrichments']}")
    print(f"   Sources used: {', '.join(stats['sources_used'])}")
    print(f"   Quality scores: {stats['quality_scores']}")
    
    # Cleanup
    if manager.metadata_file.exists():
        manager.delete()
    print(f"\n✅ Cleanup complete")


def demo_file_operations():
    """Demonstrate file operations tracking."""
    print_section("File Operations Tracking")
    
    # Create tracker
    tracker = FileOperationsTracker()
    pathway_file = Path("demo_pathway2.shy")
    
    print(f"\n✅ Created file operations tracker")
    
    # Create file with metadata
    tracker.create_file(
        pathway_file,
        user="demo_user",
        initial_data={
            "project": "demo_project",
            "version": "1.0"
        }
    )
    print(f"\n✅ Created file with metadata: {pathway_file.name}")
    
    # Log save operation
    tracker.save_file(
        pathway_file,
        user="demo_user",
        changes={"added": ["enzyme1", "enzyme2"]}
    )
    print(f"\n✅ Logged save operation")
    
    # Log load operation
    tracker.load_file(pathway_file, user="another_user")
    print(f"\n✅ Logged load operation")
    
    # Verify metadata sync
    is_sync = tracker.verify_metadata_sync(pathway_file)
    print(f"\n✅ Metadata sync verified: {is_sync}")
    
    # Get metadata manager
    manager = tracker.get_metadata_manager(pathway_file)
    metadata = manager.read()
    
    print(f"\n✅ Metadata content:")
    print(f"   File: {metadata['pathway_file']}")
    print(f"   Created: {metadata['created']}")
    print(f"   Operations: {len(metadata['operations'])}")
    
    # Cleanup
    tracker.delete_file(pathway_file, user="demo_user", delete_metadata=True)
    print(f"\n✅ Cleanup complete")


def demo_multiple_enrichments():
    """Demonstrate multiple enrichments from different sources."""
    print_section("Multiple Enrichments")
    
    pathway_file = Path("demo_pathway3.shy")
    manager = create_metadata_manager(pathway_file)
    
    # Create metadata
    manager.create({"project": "multi_source_demo"})
    print(f"\n✅ Created metadata for: {pathway_file.name}")
    
    # Simulate enrichments from different sources
    enrichments = [
        {
            "data_type": "coordinates",
            "source": "KEGG",
            "quality_score": 0.85,
            "fields_enriched": ["species[0].x", "species[0].y"]
        },
        {
            "data_type": "concentrations",
            "source": "BioModels",
            "quality_score": 0.95,
            "fields_enriched": ["species[0].initial_concentration"]
        },
        {
            "data_type": "kinetics",
            "source": "BRENDA",
            "quality_score": 0.90,
            "fields_enriched": ["reactions[0].kinetic_law"]
        },
        {
            "data_type": "coordinates",
            "source": "Reactome",
            "quality_score": 0.88,
            "fields_enriched": ["species[1].x", "species[1].y"]
        },
        {
            "data_type": "annotations",
            "source": "UniProt",
            "quality_score": 0.92,
            "fields_enriched": ["species[0].uniprot_id"]
        }
    ]
    
    print(f"\n✅ Adding {len(enrichments)} enrichment records...")
    for i, enrichment in enumerate(enrichments, 1):
        manager.add_enrichment_record(**enrichment)
        print(f"   {i}. {enrichment['data_type']} from {enrichment['source']} (Q: {enrichment['quality_score']})")
    
    # Get statistics
    stats = manager.get_statistics()
    print(f"\n✅ Statistics after enrichments:")
    print(f"   Total enrichments: {stats['total_enrichments']}")
    print(f"   Sources used: {', '.join(stats['sources_used'])}")
    
    # Get quality report
    quality = manager.get_quality_report()
    print(f"\n✅ Quality report by data type:")
    for data_type, score in quality.items():
        print(f"   {data_type}: {score:.2f}")
    
    # Get enrichment history by type
    coords_history = manager.get_enrichment_history(data_type="coordinates")
    print(f"\n✅ Coordinates enriched {len(coords_history)} times:")
    for record in coords_history:
        print(f"   - From {record['source']} (Q: {record['quality_score']})")
    
    # Cleanup
    if manager.metadata_file.exists():
        manager.delete()
    print(f"\n✅ Cleanup complete")


def demo_factory_pattern():
    """Demonstrate factory pattern usage."""
    print_section("Factory Pattern")
    
    # Auto-detect format
    pathway_file = Path("demo_pathway4.shy")
    manager = MetadataManagerFactory.create(pathway_file)
    print(f"\n✅ Created manager (auto-detected): {type(manager).__name__}")
    
    # Explicit format
    manager = MetadataManagerFactory.create(
        pathway_file,
        format=MetadataFormat.JSON
    )
    print(f"✅ Created manager (explicit JSON): {type(manager).__name__}")
    
    # Check supported formats
    formats = MetadataManagerFactory.get_supported_formats()
    print(f"\n✅ Supported formats: {[f.value for f in formats]}")
    
    # Check default format
    default = MetadataManagerFactory.get_default_format()
    print(f"✅ Default format: {default.value}")
    
    # Create metadata
    manager.create({"demo": "factory_pattern"})
    
    # Read it back
    metadata = manager.read()
    print(f"\n✅ Metadata created with factory:")
    print(f"   File: {metadata['pathway_file']}")
    print(f"   Version: {metadata['version']}")
    
    # Cleanup
    if manager.metadata_file.exists():
        manager.delete()
    print(f"\n✅ Cleanup complete")


def demo_backup_restore():
    """Demonstrate backup and restore functionality."""
    print_section("Backup and Restore")
    
    pathway_file = Path("demo_pathway5.shy")
    manager = create_metadata_manager(pathway_file)
    
    # Create initial metadata
    manager.create({"version": "1.0"})
    print(f"\n✅ Created metadata: version 1.0")
    
    # Add enrichment
    manager.add_enrichment_record(
        data_type="coordinates",
        source="KEGG",
        quality_score=0.85,
        fields_enriched=["species[0].x"]
    )
    print(f"✅ Added enrichment")
    
    # Update metadata (creates backup automatically)
    manager.update({"version": "2.0"})
    print(f"✅ Updated metadata: version 2.0 (backup created)")
    
    # Check backup exists
    backup_file = manager.metadata_file.with_suffix('.bak')
    if backup_file.exists():
        print(f"✅ Backup file exists: {backup_file.name}")
    
    # Read current metadata
    current = manager.read()
    print(f"\n✅ Current metadata:")
    print(f"   Version: {current.get('version')}")
    print(f"   Enrichments: {len(current.get('enrichments', []))}")
    
    # Cleanup
    if manager.metadata_file.exists():
        manager.delete()
    if backup_file.exists():
        backup_file.unlink()
    print(f"\n✅ Cleanup complete")


def main():
    """Run all demos."""
    print("\n" + "="*60)
    print("  METADATA MANAGEMENT SYSTEM - DEMO")
    print("="*60)
    print("\nThis demo shows the complete metadata management workflow.")
    print("All operations are performed in-memory (no persistent files).")
    
    try:
        # Run demos
        demo_basic_usage()
        demo_file_operations()
        demo_multiple_enrichments()
        demo_factory_pattern()
        demo_backup_restore()
        
        # Summary
        print_section("Demo Complete")
        print("\n✅ All demos completed successfully!")
        print("\nKey Features Demonstrated:")
        print("  • Automatic metadata creation and tracking")
        print("  • Enrichment recording with source attribution")
        print("  • File operations logging")
        print("  • Multiple source enrichments")
        print("  • Quality score tracking")
        print("  • Factory pattern for flexible instantiation")
        print("  • Backup and restore functionality")
        print("\nNext Steps:")
        print("  • Integrate with PersistencyManager")
        print("  • Connect to enrichment pipeline")
        print("  • Add unit tests")
        print("  • Implement XML and SQLite managers")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
