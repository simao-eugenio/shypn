"""
SBML Layout Resolver

Resolves SBML species/reactions to graphical positions using
cross-reference databases (KEGG, Reactome, WikiPathways).

Strategy:
1. Extract pathway-level cross-references from SBML
2. Fetch graphical layout from source database
3. Map SBML species → database entries by ID
4. Return position dictionary

Author: Shypn Development Team
Date: October 2025
"""

import logging
from typing import Dict, Tuple, Optional, List
import urllib.request
import urllib.parse

from .pathway_data import PathwayData


class SBMLLayoutResolver:
    """Resolves SBML elements to graphical positions via cross-references."""
    
    def __init__(self, pathway_data: PathwayData):
        """Initialize resolver with SBML pathway data.
        
        Args:
            pathway_data: Parsed SBML pathway with species annotations
        """
        self.pathway = pathway_data
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def resolve_layout(self) -> Optional[Dict[str, Tuple[float, float]]]:
        """Resolve positions using cross-reference databases.
        
        Returns:
            Dictionary {species_id: (x, y)} or None if resolution fails
        """
        self.logger.info("="*60)
        self.logger.info("SBML Cross-Reference Layout Resolution Starting...")
        self.logger.info("="*60)
        
        # Strategy 1: Try KEGG pathway mapping
        positions = self._try_kegg_pathway_mapping()
        if positions:
            coverage = len(positions) / len(self.pathway.species)
            self.logger.info(f"✓ KEGG layout resolved: {len(positions)}/{len(self.pathway.species)} species ({coverage:.0%} coverage)")
            return positions
        
        # Future: Add Reactome, WikiPathways strategies
        
        self.logger.info("✗ No cross-reference layout found, using fallback")
        return None
    
    def _try_kegg_pathway_mapping(self) -> Optional[Dict[str, Tuple[float, float]]]:
        """Try to map via KEGG pathway."""
        
        # Step 1: Find KEGG pathway ID
        pathway_id = self._find_kegg_pathway_id()
        if not pathway_id:
            self.logger.debug("No KEGG pathway ID found")
            return None
        
        self.logger.info(f"Found KEGG pathway: {pathway_id}")
        
        # Step 2: Fetch KGML
        try:
            from shypn.importer.kegg.fetcher import fetch_pathway
            from shypn.importer.kegg.parser import parse_kgml
            
            kgml_data = fetch_pathway(pathway_id)
            kegg_pathway = parse_kgml(kgml_data)
            self.logger.info(f"Fetched KEGG pathway with {len(kegg_pathway.entries)} entries")
        
        except Exception as e:
            self.logger.warning(f"Failed to fetch KEGG pathway: {e}")
            return None
        
        # Step 3: Map species by KEGG ID
        positions = {}
        scale_factor = 2.5  # KEGG coordinates need scaling
        
        for species in self.pathway.species:
            if not species.kegg_id:
                continue
            
            # Find compound in KEGG pathway
            kegg_entry = self._find_kegg_entry(kegg_pathway, species.kegg_id)
            if kegg_entry and kegg_entry.graphics:
                x = kegg_entry.graphics.x * scale_factor
                y = kegg_entry.graphics.y * scale_factor
                positions[species.id] = (x, y)
                self.logger.debug(f"Mapped {species.id} → KEGG {species.kegg_id} at ({x:.0f}, {y:.0f})")
        
        # Return only if we have good coverage
        coverage = len(positions) / len(self.pathway.species)
        if coverage < 0.3:  # Less than 30% coverage
            self.logger.warning(f"Low KEGG coverage ({coverage:.0%}), rejecting")
            return None
        
        return positions
    
    def _find_kegg_pathway_id(self) -> Optional[str]:
        """Find KEGG pathway ID from annotations or heuristics.
        
        Returns:
            KEGG pathway ID (e.g., "hsa00010") or None
        """
        # Method 1: Check model-level annotations
        model_pathway_id = self.pathway.metadata.get('kegg_pathway_id')
        if model_pathway_id:
            return model_pathway_id
        
        # Method 2: Heuristic - find most common pathway among species
        pathway_id = self._find_most_common_pathway()
        if pathway_id:
            return pathway_id
        
        return None
    
    def _find_most_common_pathway(self) -> Optional[str]:
        """Find most common KEGG pathway among species.
        
        Uses KEGG REST API to query which pathways contain each compound,
        then votes for the most frequent pathway.
        
        Returns:
            Most common pathway ID or None
        """
        from collections import Counter
        
        pathway_votes = Counter()
        
        for species in self.pathway.species:
            if not species.kegg_id:
                continue
            
            # Query KEGG for pathways containing this compound
            pathways = self._query_kegg_pathways_for_compound(species.kegg_id)
            pathway_votes.update(pathways)
            
            # Limit queries to avoid rate limiting
            if len(pathway_votes) > 50:
                break
        
        if not pathway_votes:
            return None
        
        # Return most common pathway
        most_common = pathway_votes.most_common(1)[0]
        pathway_id, count = most_common
        
        self.logger.info(f"Heuristic match: {pathway_id} ({count} species)")
        return pathway_id
    
    def _query_kegg_pathways_for_compound(self, kegg_id: str) -> List[str]:
        """Query KEGG REST API for pathways containing a compound.
        
        Args:
            kegg_id: KEGG compound ID (e.g., "C00031")
            
        Returns:
            List of pathway IDs (e.g., ["hsa00010", "mmu00010"])
        """
        try:
            url = f"https://rest.kegg.jp/link/pathway/{kegg_id}"
            with urllib.request.urlopen(url, timeout=5) as response:
                data = response.read().decode('utf-8')
            
            # Parse response: "cpd:C00031\tpath:hsa00010"
            pathways = []
            for line in data.strip().split('\n'):
                if '\t' in line:
                    _, pathway_ref = line.split('\t')
                    pathway_id = pathway_ref.replace('path:', '')
                    pathways.append(pathway_id)
            
            return pathways
        
        except Exception as e:
            self.logger.debug(f"Failed to query pathways for {kegg_id}: {e}")
            return []
    
    def _find_kegg_entry(self, kegg_pathway, kegg_compound_id: str):
        """Find KEGG entry in pathway by compound ID.
        
        Args:
            kegg_pathway: Parsed KEGG pathway object
            kegg_compound_id: Compound ID (e.g., "C00031")
            
        Returns:
            KEGGEntry or None
        """
        for entry in kegg_pathway.entries:
            if entry.type == 'compound' and kegg_compound_id in entry.name:
                return entry
        return None
