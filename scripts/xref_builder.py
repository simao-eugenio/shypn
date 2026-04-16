#!/usr/bin/env python3
"""Build cross-reference mapping files from online sources.

This script downloads and processes cross-reference data from:
- KEGG REST API (KEGG ↔ ChEBI)
- BiGG Models API (BiGG ↔ KEGG)

Run to generate static mapping files:
    python doc/scripts/xref_builder.py

Output: JSON files in src/shypn/thermodynamics/database/xref/data/

Note: This script is Wayland-safe (no GUI, pure CLI).
"""

import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

try:
    import requests
except ImportError:
    print("ERROR: requests module not installed")
    print("Install with: pip install requests")
    sys.exit(1)


class CrossReferenceBuilder:
    """Build cross-reference mapping database from online sources."""
    
    def __init__(self, output_dir: Path):
        """
        Initialize builder.
        
        Args:
            output_dir: Directory to write mapping files
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Mapping dictionaries
        self.kegg_to_chebi: Dict[str, List[str]] = defaultdict(list)
        self.chebi_to_kegg: Dict[str, str] = {}
        self.bigg_to_kegg: Dict[str, str] = {}
        self.compound_aliases: Dict[str, str] = {}
    
    def build_all(self):
        """Build all mapping files."""
        self.logger.info("="*60)
        self.logger.info("Building cross-reference database...")
        self.logger.info("="*60)
        
        try:
            # 1. KEGG ↔ ChEBI from KEGG REST API
            self.logger.info("\n[1/4] Fetching KEGG ↔ ChEBI mappings...")
            self._fetch_kegg_chebi_mappings()
            
            # 2. BiGG → KEGG from BiGG API
            self.logger.info("\n[2/4] Fetching BiGG → KEGG mappings...")
            self._fetch_bigg_kegg_mappings()
            
            # 3. Build alias map from KEGG names
            self.logger.info("\n[3/4] Building compound alias map...")
            self._build_alias_map()
            
            # 4. Write JSON files
            self.logger.info("\n[4/4] Writing mapping files...")
            self._write_mappings()
            
            self.logger.info("\n✅ Cross-reference database built successfully!")
            self._print_statistics()
            
        except Exception as e:
            self.logger.error(f"\n❌ Failed to build cross-reference database: {e}")
            raise
    
    def _fetch_kegg_chebi_mappings(self):
        """Fetch KEGG ↔ ChEBI mappings from KEGG REST API."""
        url = "https://rest.kegg.jp/conv/chebi/compound"
        
        try:
            self.logger.info(f"Requesting: {url}")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            # Parse tab-separated format: cpd:C00002\tchebi:15422
            lines = response.text.strip().split('\n')
            self.logger.info(f"Received {len(lines)} lines")
            
            for line in lines:
                if not line.strip():
                    continue
                
                parts = line.split('\t')
                if len(parts) != 2:
                    continue
                
                kegg_id = parts[0].replace('cpd:', '')
                chebi_id = parts[1].replace('chebi:', 'CHEBI:')
                
                # Build bidirectional mappings
                self.kegg_to_chebi[kegg_id].append(chebi_id)
                
                # ChEBI → KEGG (one-to-one, prefer first mapping)
                if chebi_id not in self.chebi_to_kegg:
                    self.chebi_to_kegg[chebi_id] = kegg_id
            
            self.logger.info(
                f"✓ Loaded {len(self.kegg_to_chebi)} KEGG → ChEBI mappings"
            )
            
        except requests.RequestException as e:
            self.logger.warning(f"⚠ Failed to fetch KEGG-ChEBI mappings: {e}")
            self.logger.warning("Continuing without KEGG-ChEBI mappings...")
    
    def _fetch_bigg_kegg_mappings(self):
        """Fetch BiGG → KEGG mappings from BiGG Models API."""
        url = "http://bigg.ucsd.edu/api/v2/universal/metabolites"
        
        try:
            self.logger.info(f"Requesting: {url}")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            metabolites = response.json()['results']
            self.logger.info(f"Found {len(metabolites)} BiGG metabolites")
            
            # Process each metabolite (with rate limiting)
            for i, metabolite in enumerate(metabolites):
                bigg_id = metabolite['bigg_id']
                
                # Get detailed info for each metabolite
                detail_url = f"http://bigg.ucsd.edu/api/v2/universal/metabolites/{bigg_id}"
                
                try:
                    detail_response = requests.get(detail_url, timeout=10)
                    detail_response.raise_for_status()
                    detail = detail_response.json()
                    
                    # Extract KEGG ID from database_links
                    db_links = detail.get('database_links', {})
                    kegg_links = db_links.get('KEGG Compound', [])
                    
                    if kegg_links:
                        # Use first KEGG ID
                        kegg_id = kegg_links[0]['id']
                        self.bigg_to_kegg[bigg_id] = kegg_id
                    
                    # Rate limiting: sleep every 10 requests
                    if (i + 1) % 10 == 0:
                        self.logger.info(f"  Processed {i + 1}/{len(metabolites)} metabolites...")
                        time.sleep(0.5)  # Be nice to BiGG API
                    
                except requests.RequestException:
                    # Skip metabolites that fail (rate limiting, not found, etc.)
                    continue
            
            self.logger.info(
                f"✓ Loaded {len(self.bigg_to_kegg)} BiGG → KEGG mappings"
            )
            
        except requests.RequestException as e:
            self.logger.warning(f"⚠ Failed to fetch BiGG-KEGG mappings: {e}")
            self.logger.warning("Continuing without BiGG-KEGG mappings...")
    
    def _build_alias_map(self):
        """Build compound alias map from KEGG compound names."""
        url = "https://rest.kegg.jp/list/compound"
        
        try:
            self.logger.info(f"Requesting: {url}")
            response = requests.get(url, timeout=60)
            response.raise_for_status()
            
            # Parse: cpd:C00002\tATP; Adenosine 5'-triphosphate
            lines = response.text.strip().split('\n')
            self.logger.info(f"Received {len(lines)} compound names")
            
            for line in lines:
                if not line.strip():
                    continue
                
                parts = line.split('\t')
                if len(parts) != 2:
                    continue
                
                kegg_id = parts[0].replace('cpd:', '')
                names_str = parts[1]
                
                # Split multiple names (separated by ;)
                names = [n.strip() for n in names_str.split(';')]
                
                # Add all names as aliases
                for name in names:
                    if name:
                        self.compound_aliases[name] = kegg_id
                        # Also add lowercase version
                        self.compound_aliases[name.lower()] = kegg_id
            
            self.logger.info(
                f"✓ Built {len(self.compound_aliases)} compound aliases"
            )
            
        except requests.RequestException as e:
            self.logger.warning(f"⚠ Failed to build alias map: {e}")
            self.logger.warning("Continuing without alias map...")
    
    def _write_mappings(self):
        """Write all mapping dictionaries to JSON files."""
        # Convert defaultdict to dict for JSON serialization
        kegg_to_chebi_dict = dict(self.kegg_to_chebi)
        
        # Write KEGG → ChEBI
        kegg_chebi_file = self.output_dir / "kegg_to_chebi.json"
        with open(kegg_chebi_file, 'w', encoding='utf-8') as f:
            json.dump(kegg_to_chebi_dict, f, indent=2)
        self.logger.info(f"✓ Wrote {kegg_chebi_file}")
        
        # Write ChEBI → KEGG
        chebi_kegg_file = self.output_dir / "chebi_to_kegg.json"
        with open(chebi_kegg_file, 'w', encoding='utf-8') as f:
            json.dump(self.chebi_to_kegg, f, indent=2)
        self.logger.info(f"✓ Wrote {chebi_kegg_file}")
        
        # Write BiGG → KEGG
        bigg_kegg_file = self.output_dir / "bigg_to_kegg.json"
        with open(bigg_kegg_file, 'w', encoding='utf-8') as f:
            json.dump(self.bigg_to_kegg, f, indent=2)
        self.logger.info(f"✓ Wrote {bigg_kegg_file}")
        
        # Write compound aliases
        aliases_file = self.output_dir / "compound_aliases.json"
        with open(aliases_file, 'w', encoding='utf-8') as f:
            json.dump(self.compound_aliases, f, indent=2)
        self.logger.info(f"✓ Wrote {aliases_file}")
    
    def _print_statistics(self):
        """Print database statistics."""
        print("\n" + "="*60)
        print("Cross-Reference Database Statistics")
        print("="*60)
        print(f"KEGG → ChEBI mappings:  {len(self.kegg_to_chebi):>6,}")
        print(f"ChEBI → KEGG mappings:  {len(self.chebi_to_kegg):>6,}")
        print(f"BiGG → KEGG mappings:   {len(self.bigg_to_kegg):>6,}")
        print(f"Compound aliases:       {len(self.compound_aliases):>6,}")
        print("="*60)
        print(f"\nMapping files written to: {self.output_dir}")
        print("="*60)


def main():
    """Main entry point for building cross-reference database."""
    # Determine output directory
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent.parent
    output_dir = repo_root / "src" / "shypn" / "thermodynamics" / "database" / "xref" / "data"
    
    print("Cross-Reference Database Builder")
    print("="*60)
    print(f"Output directory: {output_dir}")
    print("="*60)
    print("\nThis will download mappings from:")
    print("  - KEGG REST API (https://rest.kegg.jp/)")
    print("  - BiGG Models API (http://bigg.ucsd.edu/)")
    print("\nNote: BiGG API queries may take several minutes due to rate limiting.")
    print("="*60)
    
    # Confirm before proceeding
    response = input("\nProceed? [Y/n]: ").strip().lower()
    if response and response != 'y':
        print("Aborted.")
        return
    
    # Build database
    builder = CrossReferenceBuilder(output_dir)
    builder.build_all()


if __name__ == '__main__':
    main()
