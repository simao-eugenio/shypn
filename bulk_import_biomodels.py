#!/usr/bin/env python3
"""Bulk import parameters from BioModels into local database.

This script populates the local database with kinetic parameters
extracted from curated BioModels SBML files.

Purpose: Provide training data for heuristic parameter selection

Usage:
    python bulk_import_biomodels.py [--models MODEL1 MODEL2 ...] [--all]

Examples:
    # Import specific models
    python bulk_import_biomodels.py --models BIOMD0000000206 BIOMD0000000010
    
    # Import all well-known models
    python bulk_import_biomodels.py --all
    
    # Import with custom database path
    python bulk_import_biomodels.py --all --db-path /path/to/db.sqlite

Author: Shypn Development Team
Date: November 2025
"""

import sys
import os
import argparse
import logging
from typing import List

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.crossfetch.fetchers.biomodels_kinetics_fetcher import BioModelsKineticsFetcher
from shypn.crossfetch.database import HeuristicDatabase

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Well-known BioModels with good kinetic parameters
WELL_KNOWN_MODELS = [
    # Metabolic pathways
    'BIOMD0000000206',  # Yeast glycolysis (Teusink 2000) - EXCELLENT
    'BIOMD0000000051',  # Glycolysis in pancreatic beta cells
    'BIOMD0000000064',  # TCA cycle (Beard 2005)
    'BIOMD0000000289',  # Central carbon metabolism E. coli
    
    # Signaling pathways
    'BIOMD0000000010',  # MAPK cascade (Kholodenko 2000)
    'BIOMD0000000048',  # EGF signaling
    'BIOMD0000000033',  # Tyson cell cycle (1991)
    
    # Enzyme kinetics
    'BIOMD0000000005',  # Cell cycle (Tyson 1991)
    'BIOMD0000000035',  # Circadian rhythm
    
    # Gene regulation
    'BIOMD0000000001',  # Repressilator
    'BIOMD0000000003',  # Lac operon
]


def import_model(fetcher: BioModelsKineticsFetcher, 
                db: HeuristicDatabase,
                model_id: str) -> int:
    """Import parameters from a single BioModels model.
    
    Args:
        fetcher: BioModels fetcher instance
        db: Database instance
        model_id: BioModels ID (e.g., 'BIOMD0000000206')
    
    Returns:
        Number of parameters imported
    """
    logger.info(f"=" * 60)
    logger.info(f"Importing model: {model_id}")
    logger.info(f"=" * 60)
    
    # Fetch parameters from model
    result = fetcher.fetch(model_id=model_id)
    
    if not result.is_successful():
        error_msg = ', '.join(result.errors) if result.errors else "Unknown error"
        logger.error(f"Failed to fetch model {model_id}: {error_msg}")
        return 0
    
    if not result.data or 'parameters' not in result.data:
        logger.warning(f"No parameters found in model {model_id}")
        return 0
    
    parameters = result.data['parameters']
    logger.info(f"Found {len(parameters)} parameter sets in model")
    
    # Store each parameter set in database
    imported_count = 0
    
    for param_set in parameters:
        try:
            # Store in database
            param_id = db.store_parameter(
                transition_type=param_set['transition_type'],
                organism=param_set.get('organism', 'unknown'),
                parameters=param_set['parameters'],
                source='BioModels',
                confidence_score=param_set.get('confidence_score', 0.85),
                biological_semantics=param_set.get('biological_semantics'),
                ec_number=param_set.get('ec_number'),
                enzyme_name=param_set.get('enzyme_name'),
                reaction_id=param_set.get('reaction_id'),
                temperature=param_set.get('temperature'),
                ph=param_set.get('ph'),
                source_id=model_id,
                notes=param_set.get('notes')
            )
            
            imported_count += 1
            
            # Log details
            if param_set.get('ec_number'):
                logger.info(f"  ✓ Imported parameter {param_id}: "
                          f"{param_set.get('enzyme_name', 'Unknown')} "
                          f"(EC {param_set['ec_number']}) - "
                          f"{param_set['transition_type']}")
            else:
                logger.info(f"  ✓ Imported parameter {param_id}: "
                          f"{param_set.get('reaction_name', 'Unknown reaction')} - "
                          f"{param_set['transition_type']}")
                
        except Exception as e:
            logger.error(f"  ✗ Failed to store parameter: {e}")
    
    logger.info(f"\nImported {imported_count}/{len(parameters)} parameters from {model_id}")
    return imported_count


def bulk_import(models: List[str], db_path: str = None):
    """Bulk import parameters from multiple models.
    
    Args:
        models: List of BioModels IDs
        db_path: Optional database path
    """
    logger.info("=" * 60)
    logger.info("BioModels Bulk Import")
    logger.info("=" * 60)
    logger.info(f"Models to import: {len(models)}")
    logger.info(f"Database: {db_path or 'default (~/.shypn/heuristic_parameters.db)'}")
    logger.info("")
    
    # Initialize fetcher and database
    fetcher = BioModelsKineticsFetcher()
    db = HeuristicDatabase(db_path)
    
    # Check API availability
    if not fetcher.is_available():
        logger.warning("BioModels API not accessible - will use cache if available")
    
    # Get initial stats
    initial_stats = db.get_statistics()
    initial_count = initial_stats['total_parameters']
    logger.info(f"Database has {initial_count} parameters before import\n")
    
    # Import each model
    total_imported = 0
    successful_models = 0
    failed_models = []
    
    for i, model_id in enumerate(models, 1):
        logger.info(f"\n[{i}/{len(models)}] Processing {model_id}...")
        
        try:
            count = import_model(fetcher, db, model_id)
            total_imported += count
            
            if count > 0:
                successful_models += 1
            else:
                failed_models.append((model_id, "No parameters found"))
                
        except Exception as e:
            logger.error(f"Failed to import {model_id}: {e}", exc_info=True)
            failed_models.append((model_id, str(e)))
    
    # Final statistics
    logger.info("\n" + "=" * 60)
    logger.info("IMPORT COMPLETE")
    logger.info("=" * 60)
    
    final_stats = db.get_statistics()
    final_count = final_stats['total_parameters']
    
    logger.info(f"\nResults:")
    logger.info(f"  Total models processed: {len(models)}")
    logger.info(f"  Successful imports: {successful_models}")
    logger.info(f"  Failed imports: {len(failed_models)}")
    logger.info(f"  Total parameters imported: {total_imported}")
    logger.info(f"\nDatabase statistics:")
    logger.info(f"  Parameters before: {initial_count}")
    logger.info(f"  Parameters after: {final_count}")
    logger.info(f"  Net increase: {final_count - initial_count}")
    
    if final_stats.get('by_type'):
        logger.info(f"\n  By transition type:")
        for t_type, count in final_stats['by_type'].items():
            logger.info(f"    {t_type}: {count}")
    
    if final_stats.get('by_source'):
        logger.info(f"\n  By source:")
        for source, count in final_stats['by_source'].items():
            logger.info(f"    {source}: {count}")
    
    if failed_models:
        logger.info(f"\nFailed models:")
        for model_id, error in failed_models:
            logger.info(f"  ✗ {model_id}: {error}")
    
    # Cache statistics
    fetcher_stats = fetcher.get_statistics()
    logger.info(f"\nFetcher statistics:")
    logger.info(f"  Cached SBML files: {fetcher_stats['cached_models']}")
    logger.info(f"  Cache directory: {fetcher_stats['cache_dir']}")
    
    logger.info("\n" + "=" * 60)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Bulk import kinetic parameters from BioModels into local database',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--models',
        nargs='+',
        help='BioModels IDs to import (e.g., BIOMD0000000206)'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Import all well-known models'
    )
    
    parser.add_argument(
        '--db-path',
        help='Path to SQLite database (default: ~/.shypn/heuristic_parameters.db)'
    )
    
    parser.add_argument(
        '--list',
        action='store_true',
        help='List available well-known models and exit'
    )
    
    args = parser.parse_args()
    
    # List models
    if args.list:
        print("Well-known BioModels with good kinetic parameters:")
        print()
        for model_id in WELL_KNOWN_MODELS:
            print(f"  {model_id}")
        print()
        print(f"Total: {len(WELL_KNOWN_MODELS)} models")
        sys.exit(0)
    
    # Determine which models to import
    if args.all:
        models = WELL_KNOWN_MODELS
    elif args.models:
        models = args.models
    else:
        parser.print_help()
        print()
        print("Error: Must specify either --models or --all")
        sys.exit(1)
    
    # Run bulk import
    try:
        bulk_import(models, args.db_path)
        sys.exit(0)
    except KeyboardInterrupt:
        logger.info("\n\nImport interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"\n\nImport failed: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()
