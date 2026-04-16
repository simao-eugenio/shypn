#!/usr/bin/env python3
"""Migration script: Convert JSON compound data to SQLite database.

This script migrates compound mapping data from JSON files to the new
SQLite compound database. It imports from:
1. compound_mappings.json (thermodynamics data)
2. xref JSON files (ChEBI/BiGG mappings)

Usage:
    python scripts/migrate_compound_db.py [--db-path PATH]
    
Options:
    --db-path PATH    Path to SQLite database (default: ~/.shypn/compound_xref.db)
    --dry-run         Show what would be imported without writing
    --verbose         Show detailed progress
"""

import sys
import argparse
import logging
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.thermodynamics.database.compound_db import SQLiteCompoundDatabase
from shypn.thermodynamics.database.compound_db.migrator import CompoundDatabaseMigrator


def main():
    parser = argparse.ArgumentParser(
        description='Migrate compound data from JSON to SQLite',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    parser.add_argument(
        '--db-path',
        type=Path,
        help='Path to SQLite database (default: ~/.shypn/compound_xref.db)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be imported without writing'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Show detailed progress'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
    
    # Find data files
    project_root = Path(__file__).parent.parent
    compound_mappings = project_root / 'src/shypn/thermodynamics/data/compound_mappings.json'
    xref_data_dir = project_root / 'src/shypn/thermodynamics/database/xref/data'
    
    if not compound_mappings.exists():
        logger.error(f"compound_mappings.json not found at {compound_mappings}")
        return 1
    
    if not xref_data_dir.exists():
        logger.warning(f"xref data directory not found at {xref_data_dir}")
    
    if args.dry_run:
        logger.info("DRY RUN - No changes will be made")
    
    # Create/open database
    try:
        db = SQLiteCompoundDatabase(db_path=args.db_path)
        logger.info(f"Database: {db.db_path}")
        
        # Show current stats
        stats_before = db.get_statistics()
        logger.info(f"Before migration: {stats_before['total']} compounds")
        
        if args.dry_run:
            logger.info("Would import:")
            logger.info(f"  - {compound_mappings}")
            if xref_data_dir.exists():
                logger.info(f"  - {xref_data_dir}/*.json")
            return 0
        
        # Perform migration
        migrator = CompoundDatabaseMigrator(db)
        
        # Import compound_mappings.json
        logger.info("\n=== Importing compound_mappings.json ===")
        count1 = migrator.import_from_compound_mappings(compound_mappings)
        
        # Import xref files
        if xref_data_dir.exists():
            logger.info("\n=== Importing xref data ===")
            results = migrator.import_all_from_directory(xref_data_dir)
            for filename, count in results.items():
                logger.info(f"  {filename}: {count} entries")
        
        # Show final stats
        stats_after = db.get_statistics()
        logger.info(f"\n=== Migration Complete ===")
        logger.info(f"Total compounds: {stats_after['total']}")
        logger.info(f"With ChEBI: {stats_after['with_chebi']}")
        logger.info(f"With BiGG: {stats_after['with_bigg']}")
        logger.info(f"Data sources: {stats_after['sources']}")
        
        added = stats_after['total'] - stats_before['total']
        logger.info(f"\nAdded {added} new compounds")
        
        db.close()
        return 0
        
    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
