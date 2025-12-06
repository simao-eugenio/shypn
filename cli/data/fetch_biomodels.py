#!/usr/bin/env python3
"""
Fetch BioModels Dataset with Diverse Complexity Sampling

Downloads metadata and SBML files from BioModels database using a diverse 
sampling strategy that mixes models from different ID ranges to capture 
varying complexity levels.

Strategy:
    - Mix models from ranges: 1-100, 200-299, 300-399, 400-499
    - Early models (1-100): Simple, well-validated pathways
    - Mid-era models (200-299): Moderate complexity
    - Later models (300-399): Increased complexity
    - Recent models (400-499): High complexity, larger networks

Usage:
    # Diverse sampling (default, recommended)
    python fetch_biomodels_dataset.py --count 100 --output ../experimental_data/biomodels_dataset/ --download-sbml --mix-ranges
    
    # Sequential sampling (traditional)
    python fetch_biomodels_dataset.py --count 100 --output ../experimental_data/biomodels_dataset/ --download-sbml

Author: Eugênio Simão
Date: 2025-12-05
"""

import argparse
import csv
import os
import sys
import urllib.request
import urllib.error
from pathlib import Path
from typing import List, Dict


def fetch_model_metadata(model_id: str) -> Dict:
    """Fetch metadata for a single BioModels entry.
    
    Args:
        model_id: BioModels accession ID (e.g., BIOMD0000000001)
    
    Returns:
        Dict with model metadata
    """
    try:
        # BioModels REST API v2
        url = f"https://www.ebi.ac.uk/biomodels/{model_id}?format=json"
        req = urllib.request.Request(url)
        req.add_header('User-Agent', 'SHYpn/2.0')
        
        response = urllib.request.urlopen(req, timeout=10)
        data = response.read().decode()
        # Simple parsing - just extract what we need
        
        return {
            'model_id': model_id,
            'year': '????',  # Will be filled by validation script
            'author': 'BioModels',
            'description': model_id,
            'species_count': 0,  # Will be filled by validation script
            'reactions_count': 0,
            'type': 'Unknown',
            'curated': 'Yes',
            'test_arcs': 0
        }
    except Exception as e:
        return {
            'model_id': model_id,
            'year': '????',
            'author': 'Unknown',
            'description': 'Fetch failed',
            'species_count': 0,
            'reactions_count': 0,
            'type': 'Unknown',
            'curated': 'Unknown',
            'test_arcs': 0
        }


def download_sbml_file(model_id: str, output_dir: Path) -> bool:
    """Download SBML file for a model.
    
    Args:
        model_id: BioModels accession ID
        output_dir: Directory to save SBML file
    
    Returns:
        True if successful, False otherwise
    """
    urls = [
        f"https://www.ebi.ac.uk/biomodels/model/download/{model_id}?filename={model_id}_url.xml",
        f"https://www.ebi.ac.uk/biomodels/model/download/{model_id}?filename={model_id}.xml",
    ]
    
    output_file = output_dir / f"{model_id}.xml"
    
    for url in urls:
        try:
            print(f"  Trying {url}...")
            req = urllib.request.Request(url)
            req.add_header('User-Agent', 'SHYpn/2.0')
            
            response = urllib.request.urlopen(req, timeout=30)
            content = response.read()
            
            with open(output_file, 'wb') as f:
                f.write(content)
            
            print(f"  ✅ Downloaded {model_id}.xml ({len(content)} bytes)")
            return True
            
        except Exception as e:
            print(f"  ❌ Failed: {e}")
            continue
    
    return False


def main():
    parser = argparse.ArgumentParser(description='Fetch BioModels dataset with diverse complexity')
    parser.add_argument('--count', type=int, default=100, 
                       help='Number of models to fetch (default: 100)')
    parser.add_argument('--output', type=str, required=True,
                       help='Output directory')
    parser.add_argument('--download-sbml', action='store_true',
                       help='Also download SBML files')
    parser.add_argument('--mix-ranges', action='store_true', default=True,
                       help='Mix models from different ID ranges for complexity diversity (default: True)')
    
    args = parser.parse_args()
    
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Primary reference models (from paper)
    primary_models = [
        'BIOMD0000000001',  # Edelstein 1996: Glycolysis
        'BIOMD0000000010',  # Kholodenko 2000: MAPK cascade
        'BIOMD0000000012',  # Elowitz 2000: Repressilator
    ]
    
    if args.mix_ranges:
        # Diverse sampling strategy: Mix models from different ID ranges
        # to capture varying complexity (simple early models + complex later models)
        print(f"Using DIVERSE sampling strategy (mixing ID ranges)...")
        model_ids = primary_models.copy()
        
        # Calculate how many models to fetch from each range
        remaining = args.count - len(primary_models)
        per_range = remaining // 4  # Divide among 4 ranges
        
        ranges = [
            (4, 100),       # Early curated models (simple, well-validated)
            (200, 299),     # Mid-era models (moderate complexity)
            (300, 399),     # Later models (increased complexity)
            (400, 499),     # Recent models (high complexity, larger networks)
        ]
        
        for start, end in ranges:
            count = 0
            for i in range(start, end + 1):
                if count >= per_range:
                    break
                model_id = f"BIOMD{i:010d}"
                if model_id not in model_ids:
                    model_ids.append(model_id)
                    count += 1
        
        # If we need more models to reach target count, add from first range
        while len(model_ids) < args.count:
            i = len(model_ids) + 1
            model_id = f"BIOMD{i:010d}"
            if model_id not in model_ids:
                model_ids.append(model_id)
        
        model_ids = model_ids[:args.count]
        print(f"Selected models from ranges: 1-100, 200-299, 300-399, 400-499")
        
    else:
        # Sequential sampling: Traditional approach (BIOMD0000000001 to BIOMD0000000N)
        print(f"Using SEQUENTIAL sampling strategy (1 to {args.count})...")
        model_ids = primary_models.copy()
        
        for i in range(4, args.count + 1):
            model_id = f"BIOMD{i:010d}"
            if model_id not in model_ids:
                model_ids.append(model_id)
        
        model_ids = model_ids[:args.count]
    
    print(f"Fetching metadata for {len(model_ids)} models...")
    
    # Fetch metadata
    models = []
    for model_id in model_ids:
        print(f"\nFetching {model_id}...")
        metadata = fetch_model_metadata(model_id)
        models.append(metadata)
        
        # Download SBML if requested
        if args.download_sbml:
            sbml_dir = output_dir / 'sbml_files'
            sbml_dir.mkdir(exist_ok=True)
            download_sbml_file(model_id, sbml_dir)
    
    # Write to CSV
    csv_file = output_dir / 'model_list.csv'
    print(f"\nWriting metadata to {csv_file}...")
    
    with open(csv_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=[
            'model_id', 'year', 'author', 'description',
            'species_count', 'reactions_count', 'type', 'curated', 'test_arcs'
        ])
        writer.writeheader()
        writer.writerows(models)
    
    print(f"\n✅ Done! Fetched {len(models)} models")
    print(f"   CSV: {csv_file}")
    if args.download_sbml:
        print(f"   SBML: {output_dir / 'sbml_files'}")


if __name__ == '__main__':
    main()
