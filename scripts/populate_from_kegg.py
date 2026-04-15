#!/usr/bin/env python3
"""Auto-populate compound database from KEGG API.

This script enriches the compound database by fetching data from KEGG API
for compounds that are missing names or metadata.

Features:
- Batch processing with rate limiting
- Caches successful lookups
- Skips compounds with complete data
- Updates existing entries

Usage:
    python scripts/populate_from_kegg.py [--limit N] [--force]
    
Options:
    --limit N       Process only N compounds (for testing)
    --force         Re-fetch even if names exist
    --dry-run       Show what would be fetched
    --batch-size N  Number of compounds per batch (default: 50)
"""

import sys
import argparse
import logging
import time
import urllib.request
from pathlib import Path
from typing import Optional

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.thermodynamics.database.compound_db import SQLiteCompoundDatabase, CompoundIdentity


def fetch_compound_from_kegg(kegg_id: str) -> Optional[dict]:
    """Fetch compound data from KEGG API.
    
    Args:
        kegg_id: KEGG compound ID
        
    Returns:
        Dictionary with name, formula, etc., or None if not found
    """
    url = f"https://rest.kegg.jp/get/{kegg_id}"
    try:
        with urllib.request.urlopen(url, timeout=10) as response:
            text = response.read().decode('utf-8')
            
            result = {}
            for line in text.split('\n'):
                if line.startswith('NAME'):
                    name_line = line[4:].strip()
                    primary_name = name_line.split(';')[0].strip()
                    result['name'] = primary_name.rstrip('.,;:')
                elif line.startswith('FORMULA'):
                    result['formula'] = line[7:].strip()
            
            return result if result else None
            
    except Exception as e:
        logging.debug(f"Failed to fetch {kegg_id}: {e}")
        return None


def main():
    parser = argparse.ArgumentParser(
        description='Auto-populate compound database from KEGG API',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Process only N compounds (for testing)'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Re-fetch even if names exist'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be fetched without writing'
    )
    parser.add_argument(
        '--batch-size',
        type=int,
        default=50,
        help='Number of compounds per batch (default: 50)'
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
    
    if args.dry_run:
        logger.info("DRY RUN - No changes will be made")
    
    try:
        db = SQLiteCompoundDatabase()
        logger.info(f"Database: {db.db_path}")
        
        # Get compounds that need enrichment
        all_kegg_ids = db.get_all_kegg_ids()
        logger.info(f"Total compounds in database: {len(all_kegg_ids)}")
        
        # Filter compounds needing update
        to_update = []
        for kegg_id in all_kegg_ids:
            identity = db.get_by_kegg(kegg_id)
            if args.force or identity.primary_name == kegg_id or not identity.primary_name:
                to_update.append(kegg_id)
        
        logger.info(f"Compounds needing enrichment: {len(to_update)}")
        
        if args.limit:
            to_update = to_update[:args.limit]
            logger.info(f"Limited to first {args.limit} compounds")
        
        if args.dry_run:
            logger.info("Would fetch from KEGG:")
            for kegg_id in to_update[:10]:
                logger.info(f"  - {kegg_id}")
            if len(to_update) > 10:
                logger.info(f"  ... and {len(to_update) - 10} more")
            return 0
        
        # Process in batches
        updated = 0
        failed = 0
        
        for i, kegg_id in enumerate(to_update):
            if i > 0 and i % args.batch_size == 0:
                logger.info(f"Progress: {i}/{len(to_update)} ({updated} updated, {failed} failed)")
                time.sleep(1)  # Rate limiting
            
            # Fetch from KEGG
            data = fetch_compound_from_kegg(kegg_id)
            if data:
                identity = db.get_by_kegg(kegg_id)
                identity.primary_name = data.get('name', identity.primary_name)
                identity.formula = data.get('formula', identity.formula)
                identity.source = 'kegg_api'
                
                if db.update(identity):
                    updated += 1
                    logger.debug(f"Updated {kegg_id}: {identity.primary_name}")
            else:
                failed += 1
                logger.debug(f"Failed to fetch {kegg_id}")
        
        logger.info(f"\n=== Enrichment Complete ===")
        logger.info(f"Updated: {updated}")
        logger.info(f"Failed: {failed}")
        
        # Show final stats
        stats = db.get_statistics()
        logger.info(f"\nDatabase statistics:")
        logger.info(f"  Total: {stats['total']}")
        logger.info(f"  With ChEBI: {stats['with_chebi']}")
        logger.info(f"  With BiGG: {stats['with_bigg']}")
        
        db.close()
        return 0
        
    except Exception as e:
        logger.error(f"Enrichment failed: {e}", exc_info=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
