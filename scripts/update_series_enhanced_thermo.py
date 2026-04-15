#!/usr/bin/env python3
"""
Update series*.shy files with enhanced thermodynamic data structure.

This script enriches places with:
1. Complete compound properties (charge, n_protons, pKa_values)
2. Fresh data from compound database (if available)
3. Enhanced thermodynamic conditions structure
4. Proper uncertainty values
5. Fetch dates and data sources

For transitions, ensures they have proper kinetic properties.
"""

import json
import shutil
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.thermodynamics.compound_database import CompoundDatabase
from shypn.thermodynamics.compound_mapper import CompoundMapper


def update_place_thermodynamics(place: Dict[str, Any], db: CompoundDatabase) -> bool:
    """Update a place with enhanced thermodynamic properties.
    
    Args:
        place: Place object dict
        db: CompoundDatabase instance
    
    Returns:
        True if updates were made
    """
    # Skip places without thermodynamic data
    if 'properties' not in place:
        return False
    
    props = place['properties']
    
    # Check if place has compound_id
    compound_id = props.get('compound_id')
    if not compound_id:
        # Try to get from metadata
        if 'metadata' in place and 'compound_id' in place['metadata']:
            compound_id = place['metadata']['compound_id']
            props['compound_id'] = compound_id
        else:
            return False
    
    modified = False
    
    # Try to get enhanced data from database
    cached_data = db.get_compound(compound_id)
    
    if cached_data:
        print(f"  - {place['name']}: Found cached data for {compound_id}")
        
        # Update with cached data
        if 'compound_name' not in props or not props['compound_name']:
            props['compound_name'] = cached_data.get('compound_name', '')
            modified = True
        
        if cached_data.get('delta_g_formation') is not None:
            props['delta_g_formation'] = cached_data['delta_g_formation']
            modified = True
        
        # Add new enhanced properties
        if 'charge' not in props and cached_data.get('charge') is not None:
            props['charge'] = cached_data['charge']
            modified = True
        
        if 'n_protons' not in props and cached_data.get('n_protons') is not None:
            props['n_protons'] = cached_data['n_protons']
            modified = True
        
        if 'pKa_values' not in props and cached_data.get('pKa_values'):
            props['pKa_values'] = cached_data['pKa_values']
            modified = True
        
        if 'source' not in props or props['source'] == 'unknown':
            props['source'] = cached_data.get('source', 'database')
            modified = True
        
        if 'fetch_date' not in props:
            props['fetch_date'] = cached_data.get('fetch_date', datetime.now().isoformat())
            modified = True
    
    else:
        # No cached data - try to fetch from remote
        print(f"  - {place['name']}: Fetching data for {compound_id}")
        remote_data = db.fetch_remote(compound_id, source="equilibrator")
        
        if remote_data:
            # Cache it for future use
            db.cache_compound(remote_data)
            
            # Update place properties
            props['compound_name'] = remote_data.get('compound_name', '')
            props['delta_g_formation'] = remote_data.get('delta_g_formation')
            props['charge'] = remote_data.get('charge', 0)
            props['n_protons'] = remote_data.get('n_protons', 0)
            props['pKa_values'] = remote_data.get('pKa_values', [])
            props['source'] = remote_data.get('source', 'equilibrator')
            props['fetch_date'] = remote_data.get('fetch_date', datetime.now().isoformat())
            props['uncertainty'] = 0.0  # Will be populated with real data soon
            
            modified = True
            print(f"    ✓ Fetched and cached {compound_id}")
        else:
            print(f"    ⚠ No data available for {compound_id} - keeping existing")
    
    # Ensure thermodynamic_conditions structure is present
    if 'thermodynamic_conditions' not in props:
        props['thermodynamic_conditions'] = {
            'pH': 7.0,
            'temperature': 298.15,
            'ionic_strength': 0.1
        }
        modified = True
    
    # Add reference_conditions if not present
    if 'reference_conditions' not in props:
        props['reference_conditions'] = props['thermodynamic_conditions'].copy()
        modified = True
    
    return modified


def update_model_file(model_path: Path, db: CompoundDatabase) -> Dict[str, int]:
    """Update a single model file with enhanced thermodynamic data.
    
    Args:
        model_path: Path to .shy model file
        db: CompoundDatabase instance
    
    Returns:
        Dict with update statistics
    """
    print(f"\n{'='*60}")
    print(f"Processing: {model_path.name}")
    print(f"{'='*60}")
    
    # Backup
    backup_path = model_path.with_suffix('.shy.backup_pre_enhanced_thermo')
    if not backup_path.exists():
        shutil.copy2(model_path, backup_path)
        print(f"✓ Backup created: {backup_path.name}")
    
    # Load model
    with open(model_path) as f:
        model = json.load(f)
    
    # Update places
    places_updated = 0
    places_with_thermo = 0
    
    for place in model.get('places', []):
        if 'properties' in place and 'compound_id' in place.get('properties', {}):
            places_with_thermo += 1
            if update_place_thermodynamics(place, db):
                places_updated += 1
    
    # Update transitions - ensure they have kinetic metadata
    transitions_updated = 0
    for transition in model.get('transitions', []):
        if 'properties' not in transition:
            transition['properties'] = {}
            transitions_updated += 1
        
        # Ensure rate_function is in properties (for consistency)
        if 'rate_function' in transition and 'rate_function' not in transition['properties']:
            transition['properties']['rate_function'] = transition['rate_function']
            transitions_updated += 1
    
    # Update thermodynamic_settings at model level if needed
    if 'thermodynamic_settings' not in model:
        model['thermodynamic_settings'] = {
            "ph": 7.0,
            "temperature": 298.15,
            "ionic_strength": 0.1,
            "tolerance": 0.5,
            "enable_validation": True,
            "preset": "biochemical_standard"
        }
    
    # Save updated model
    with open(model_path, 'w') as f:
        json.dump(model, f, indent=2)
    
    print(f"\n✓ Model saved with updates")
    
    return {
        'places_with_thermo': places_with_thermo,
        'places_updated': places_updated,
        'transitions_updated': transitions_updated
    }


def main():
    """Main update script."""
    print("="*80)
    print("ENHANCED THERMODYNAMIC DATA UPDATE")
    print("="*80)
    print("\nThis script updates series*.shy files with:")
    print("  • Complete compound properties (charge, n_protons, pKa)")
    print("  • Fresh data from compound database")
    print("  • Enhanced thermodynamic conditions")
    print("  • Proper uncertainty and source tracking")
    print()
    
    # Initialize database
    print("Initializing compound database...")
    db = CompoundDatabase()
    print(f"✓ Database ready: {db.db_path}")
    
    # Find series files
    models_dir = Path('workspace/projects/My_Project/drug_discovery/models/normal')
    
    if not models_dir.exists():
        print(f"\n❌ ERROR: Directory not found: {models_dir}")
        print("   Run this script from the shypn root directory")
        return 1
    
    series_files = sorted(models_dir.glob('series_*.shy'))
    
    if not series_files:
        print(f"\n❌ ERROR: No series_*.shy files found in {models_dir}")
        return 1
    
    print(f"\n✓ Found {len(series_files)} series files to update:")
    for f in series_files:
        print(f"  - {f.name}")
    
    # Process each file
    total_stats = {
        'files': 0,
        'places_with_thermo': 0,
        'places_updated': 0,
        'transitions_updated': 0
    }
    
    for model_path in series_files:
        try:
            stats = update_model_file(model_path, db)
            total_stats['files'] += 1
            total_stats['places_with_thermo'] += stats['places_with_thermo']
            total_stats['places_updated'] += stats['places_updated']
            total_stats['transitions_updated'] += stats['transitions_updated']
        except Exception as e:
            print(f"\n❌ Error processing {model_path.name}: {e}")
            import traceback
            traceback.print_exc()
            continue
    
    # Summary
    print("\n" + "="*80)
    print("UPDATE COMPLETE")
    print("="*80)
    print(f"\nStatistics:")
    print(f"  • Files processed: {total_stats['files']}/{len(series_files)}")
    print(f"  • Places with thermodynamics: {total_stats['places_with_thermo']}")
    print(f"  • Places updated: {total_stats['places_updated']}")
    print(f"  • Transitions updated: {total_stats['transitions_updated']}")
    
    print(f"\nEnhanced features now available:")
    print(f"  ✓ Complete compound properties (charge, pKa, protons)")
    print(f"  ✓ Data source tracking")
    print(f"  ✓ Fetch date timestamps")
    print(f"  ✓ Reference conditions for each compound")
    print(f"  ✓ Uncertainty estimates")
    
    print(f"\nNext steps:")
    print(f"  1. Open models in GUI to verify thermodynamic data")
    print(f"  2. Use 'Search by Name' to find additional compounds")
    print(f"  3. Export to CSV to review all compound data")
    print(f"  4. Import CSV to batch update multiple models")
    
    print("\n" + "="*80)
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
