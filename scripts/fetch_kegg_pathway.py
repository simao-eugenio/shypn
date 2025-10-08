#!/usr/bin/env python3
"""Utility to fetch KEGG pathways and save them locally.

This script fetches pathways from KEGG API and saves them as KGML XML files
in the models/pathways directory for testing and reference.

Usage:
    python3 scripts/fetch_kegg_pathway.py hsa00010
    python3 scripts/fetch_kegg_pathway.py hsa00020 hsa00030
    python3 scripts/fetch_kegg_pathway.py --all-reference  # Fetch common reference pathways
"""

import sys
import os
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from shypn.importer.kegg.api_client import KEGGAPIClient


# Common pathways for testing
REFERENCE_PATHWAYS = [
    ('map00010', 'Glycolysis / Gluconeogenesis'),
    ('map00020', 'TCA Cycle'),
    ('map00030', 'Pentose Phosphate Pathway'),
    ('map00051', 'Fructose and mannose metabolism'),
    ('map00052', 'Galactose metabolism'),
]

HUMAN_PATHWAYS = [
    ('hsa00010', 'Glycolysis / Gluconeogenesis'),
    ('hsa00020', 'TCA Cycle'),
    ('hsa00030', 'Pentose Phosphate Pathway'),
    ('hsa04010', 'MAPK signaling pathway'),
]


def fetch_and_save(pathway_id: str, output_dir: Path) -> bool:
    """Fetch a pathway and save it.
    
    Args:
        pathway_id: KEGG pathway ID
        output_dir: Directory to save to
        
    Returns:
        True if successful
    """
    client = KEGGAPIClient()
    
    print(f"\nFetching {pathway_id}...")
    kgml = client.fetch_kgml(pathway_id)
    
    if not kgml:
        print(f"✗ Failed to fetch {pathway_id}")
        return False
    
    # Save to file
    output_file = output_dir / f"{pathway_id}.kgml"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(kgml)
    
    print(f"✓ Saved to {output_file} ({len(kgml)} bytes)")
    return True


def main():
    parser = argparse.ArgumentParser(
        description='Fetch KEGG pathways and save them locally'
    )
    parser.add_argument(
        'pathway_ids',
        nargs='*',
        help='Pathway IDs to fetch (e.g., hsa00010, map00020)'
    )
    parser.add_argument(
        '--all-reference',
        action='store_true',
        help='Fetch common reference pathways'
    )
    parser.add_argument(
        '--all-human',
        action='store_true',
        help='Fetch common human pathways'
    )
    parser.add_argument(
        '--output-dir',
        type=Path,
        default=Path(__file__).parent.parent / 'models' / 'pathways',
        help='Output directory (default: models/pathways)'
    )
    
    args = parser.parse_args()
    
    # Create output directory if needed
    args.output_dir.mkdir(parents=True, exist_ok=True)
    
    # Collect pathway IDs to fetch
    pathways_to_fetch = []
    
    if args.all_reference:
        pathways_to_fetch.extend([pid for pid, _ in REFERENCE_PATHWAYS])
        print(f"Fetching {len(REFERENCE_PATHWAYS)} reference pathways...")
    
    if args.all_human:
        pathways_to_fetch.extend([pid for pid, _ in HUMAN_PATHWAYS])
        print(f"Fetching {len(HUMAN_PATHWAYS)} human pathways...")
    
    if args.pathway_ids:
        pathways_to_fetch.extend(args.pathway_ids)
    
    if not pathways_to_fetch:
        print("No pathways specified. Use --help for usage information.")
        print("\nExamples:")
        print("  python3 scripts/fetch_kegg_pathway.py hsa00010")
        print("  python3 scripts/fetch_kegg_pathway.py --all-reference")
        return 1
    
    # Fetch pathways
    print(f"\n{'='*60}")
    print(f"Fetching {len(pathways_to_fetch)} pathway(s) to {args.output_dir}")
    print(f"{'='*60}")
    
    success_count = 0
    for pathway_id in pathways_to_fetch:
        if fetch_and_save(pathway_id, args.output_dir):
            success_count += 1
    
    # Summary
    print(f"\n{'='*60}")
    print(f"Completed: {success_count}/{len(pathways_to_fetch)} successful")
    print(f"{'='*60}")
    
    return 0 if success_count == len(pathways_to_fetch) else 1


if __name__ == '__main__':
    sys.exit(main())
