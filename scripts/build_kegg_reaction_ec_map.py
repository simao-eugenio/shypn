#!/usr/bin/env python3
"""
KEGG Reaction to EC Mapping Builder

Extends the cross-reference database by fetching KEGG reaction → EC number mappings.
This enables the heuristic engine to extract EC numbers from reaction IDs when
the EC number is not directly provided in the model.

Usage:
    python scripts/build_kegg_reaction_ec_map.py [--output OUTPUT_PATH]

Author: Shypn Development Team
Date: January 2026
"""

import json
import logging
import argparse
from pathlib import Path
from typing import Dict, Optional
import time

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests library not available. Install with: pip install requests")


class KEGGReactionECMapper:
    """Fetches and builds KEGG reaction → EC number mapping.
    
    Queries KEGG REST API to build a comprehensive mapping of
    reaction IDs (R00001, R00002, etc.) to EC numbers.
    """
    
    KEGG_API_BASE = "https://rest.kegg.jp"
    
    def __init__(self):
        """Initialize mapper."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.reaction_to_ec: Dict[str, str] = {}
    
    def fetch_all_reactions(self) -> Dict[str, str]:
        """Fetch all KEGG reactions and their EC numbers.
        
        Returns:
            Dictionary mapping reaction_id → ec_number
        """
        if not REQUESTS_AVAILABLE:
            self.logger.error("requests library not available")
            return {}
        
        self.logger.info("Fetching KEGG reaction list...")
        
        try:
            # Step 1: Get list of all reactions
            response = requests.get(f"{self.KEGG_API_BASE}/list/reaction")
            response.raise_for_status()
            
            reaction_lines = response.text.strip().split('\n')
            self.logger.info(f"Found {len(reaction_lines)} reactions")
            
            # Step 2: Parse each reaction to extract EC number
            for i, line in enumerate(reaction_lines, 1):
                if not line.strip():
                    continue
                
                # Format: "rn:R00001\tDescription; EC:1.1.1.1"
                parts = line.split('\t')
                if len(parts) != 2:
                    continue
                
                reaction_id = parts[0].replace('rn:', '')
                description = parts[1]
                
                # Extract EC number from description
                ec_number = self._extract_ec_from_description(description)
                
                if ec_number:
                    self.reaction_to_ec[reaction_id] = ec_number
                    self.logger.debug(f"{reaction_id} → {ec_number}")
                
                # Progress reporting
                if i % 100 == 0:
                    self.logger.info(f"Processed {i}/{len(reaction_lines)} reactions...")
                
                # Rate limiting (KEGG API guidelines)
                time.sleep(0.1)  # 100ms delay between requests
            
            self.logger.info(
                f"Successfully mapped {len(self.reaction_to_ec)} reactions to EC numbers"
            )
            
            return self.reaction_to_ec
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch KEGG reactions: {e}")
            return {}
    
    def fetch_detailed_mapping(self, max_reactions: Optional[int] = None) -> Dict[str, str]:
        """Fetch detailed EC mapping by querying individual reaction entries.
        
        This is more accurate but slower than parsing the list endpoint.
        
        Args:
            max_reactions: Optional limit for testing (None = all reactions)
            
        Returns:
            Dictionary mapping reaction_id → ec_number
        """
        if not REQUESTS_AVAILABLE:
            self.logger.error("requests library not available")
            return {}
        
        self.logger.info("Fetching detailed KEGG reaction → EC mapping...")
        
        try:
            # Get list of reactions first
            response = requests.get(f"{self.KEGG_API_BASE}/list/reaction")
            response.raise_for_status()
            
            reaction_lines = response.text.strip().split('\n')
            total = len(reaction_lines)
            
            if max_reactions:
                reaction_lines = reaction_lines[:max_reactions]
                self.logger.info(f"Limited to {max_reactions} reactions for testing")
            
            # Query each reaction individually
            for i, line in enumerate(reaction_lines, 1):
                if not line.strip():
                    continue
                
                reaction_id = line.split('\t')[0].replace('rn:', '')
                
                # Fetch detailed entry
                ec_number = self._fetch_ec_for_reaction(reaction_id)
                
                if ec_number:
                    self.reaction_to_ec[reaction_id] = ec_number
                
                # Progress reporting
                if i % 50 == 0:
                    self.logger.info(f"Processed {i}/{len(reaction_lines)} reactions...")
                
                # Rate limiting
                time.sleep(0.2)  # 200ms delay for individual queries
            
            self.logger.info(
                f"Successfully mapped {len(self.reaction_to_ec)} reactions to EC numbers"
            )
            
            return self.reaction_to_ec
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch detailed reactions: {e}")
            return {}
    
    def _fetch_ec_for_reaction(self, reaction_id: str) -> Optional[str]:
        """Fetch EC number for a specific reaction.
        
        Args:
            reaction_id: KEGG reaction ID (e.g., "R00001")
            
        Returns:
            EC number or None
        """
        try:
            response = requests.get(f"{self.KEGG_API_BASE}/get/{reaction_id}")
            response.raise_for_status()
            
            # Parse entry for EC number
            # Format: "ENZYME      1.1.1.1"
            for line in response.text.split('\n'):
                if line.startswith('ENZYME'):
                    ec_number = line.split()[1].strip()
                    return ec_number
            
            return None
            
        except requests.RequestException:
            return None
    
    def _extract_ec_from_description(self, description: str) -> Optional[str]:
        """Extract EC number from reaction description.
        
        Args:
            description: Reaction description text
            
        Returns:
            EC number or None
        """
        import re
        
        # Pattern: EC:1.1.1.1 or [EC:1.1.1.1]
        pattern = r'(?:EC:?\s*)(\d+\.\d+\.\d+\.(?:\d+|-))'
        match = re.search(pattern, description)
        
        if match:
            return match.group(1)
        
        return None
    
    def save_mapping(self, output_path: Path):
        """Save mapping to JSON file.
        
        Args:
            output_path: Path to output JSON file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(
                self.reaction_to_ec,
                f,
                indent=2,
                ensure_ascii=False
            )
        
        self.logger.info(f"Saved mapping to {output_path}")
        self.logger.info(f"Total mappings: {len(self.reaction_to_ec)}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Build KEGG reaction → EC number mapping"
    )
    parser.add_argument(
        '--output',
        type=Path,
        default=Path('src/shypn/thermodynamics/database/xref/kegg_reaction_to_ec.json'),
        help='Output path for JSON mapping file'
    )
    parser.add_argument(
        '--detailed',
        action='store_true',
        help='Use detailed mode (slower but more accurate)'
    )
    parser.add_argument(
        '--max-reactions',
        type=int,
        default=None,
        help='Limit number of reactions for testing (None = all)'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger('main')
    
    if not REQUESTS_AVAILABLE:
        logger.error("requests library is required. Install with: pip install requests")
        return 1
    
    # Build mapping
    mapper = KEGGReactionECMapper()
    
    logger.info("Starting KEGG reaction → EC mapping builder...")
    logger.info(f"Output file: {args.output}")
    logger.info(f"Mode: {'Detailed' if args.detailed else 'Fast'}")
    
    if args.detailed:
        mapping = mapper.fetch_detailed_mapping(max_reactions=args.max_reactions)
    else:
        mapping = mapper.fetch_all_reactions()
    
    if not mapping:
        logger.error("Failed to build mapping")
        return 1
    
    # Save results
    mapper.save_mapping(args.output)
    
    # Print statistics
    logger.info("\nMapping Statistics:")
    logger.info(f"  Total reactions mapped: {len(mapping)}")
    
    # Count EC classes
    ec_classes = {}
    for ec in mapping.values():
        ec_class = ec.split('.')[0]
        ec_classes[ec_class] = ec_classes.get(ec_class, 0) + 1
    
    logger.info("\nEC Class Distribution:")
    for ec_class, count in sorted(ec_classes.items()):
        logger.info(f"  EC {ec_class}.x.x.x: {count} reactions")
    
    logger.info("\n✅ Mapping build complete!")
    logger.info(f"File saved: {args.output}")
    
    return 0


if __name__ == '__main__':
    exit(main())
