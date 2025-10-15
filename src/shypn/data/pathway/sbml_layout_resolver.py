"""
SBML Layout Resolver

Resolves SBML species/reactions to graphical positions using multiple strategies:

Priority 1: SBML Layout Extension (if present from CrossFetch enrichment)
  - Read coordinates directly from SBML Layout package
  - Fastest and most accurate (no external fetching)
  - Already in Cartesian coordinate system

Priority 2: Cross-Reference Databases (fallback)
  - Extract pathway-level cross-references from SBML
  - Fetch graphical layout from source database (KEGG, Reactome, WikiPathways)
  - Map SBML species → database entries by ID

Priority 3: None (algorithmic layout will be used)
  - Return None to trigger tree_layout.py

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
        """Resolve positions using multiple strategies (priority order).
        
        Strategy Priority:
        1. SBML Layout extension (if present from enrichment)
        2. Cross-reference databases (KEGG, Reactome)
        3. None (fallback to algorithmic layout)
        
        Returns:
            Dictionary {species_id: (x, y)} or None if resolution fails
        """
        self.logger.info("="*60)
        self.logger.info("SBML Layout Resolution Starting...")
        self.logger.info("="*60)
        
        # PRIORITY 1: Check for SBML Layout extension first
        positions = self._try_sbml_layout_extension()
        if positions:
            coverage = len(positions) / len(self.pathway.species)
            self.logger.info(f"✓ SBML Layout extension found: {len(positions)}/{len(self.pathway.species)} species ({coverage:.0%} coverage)")
            return positions
        
        # PRIORITY 2: Try KEGG pathway mapping (fallback)
        positions = self._try_kegg_pathway_mapping()
        if positions:
            coverage = len(positions) / len(self.pathway.species)
            self.logger.info(f"✓ KEGG layout resolved: {len(positions)}/{len(self.pathway.species)} species ({coverage:.0%} coverage)")
            return positions
        
        # Future: Add Reactome, WikiPathways strategies
        
        self.logger.info("✗ No layout found, using algorithmic layout")
        return None
    
    def _try_sbml_layout_extension(self) -> Optional[Dict[str, Tuple[float, float]]]:
        """Try to read layout from SBML Layout extension.
        
        If the SBML was enriched with CrossFetch coordinate enrichment,
        it will contain a Layout extension with species/reaction glyphs.
        These coordinates are already in Cartesian system (first quadrant).
        
        Returns:
            Dictionary {species_id: (x, y)} or None if no Layout extension
        """
        self.logger.info("Checking for SBML Layout extension...")
        
        # Check if we have the SBML document
        if not hasattr(self.pathway, 'sbml_document') or not self.pathway.sbml_document:
            self.logger.debug("No SBML document available")
            return None
        
        try:
            import libsbml
            
            document = self.pathway.sbml_document
            model = document.getModel()
            
            if not model:
                self.logger.debug("No SBML model in document")
                return None
            
            # Get Layout plugin
            mplugin = model.getPlugin('layout')
            if not mplugin:
                self.logger.debug("No Layout plugin found")
                return None
            
            num_layouts = mplugin.getNumLayouts()
            if num_layouts == 0:
                self.logger.debug("No layouts in Layout plugin")
                return None
            
            # Use first layout (typically "kegg_layout_1" from coordinate enricher)
            layout = mplugin.getLayout(0)
            layout_id = layout.getId() if layout.isSetId() else "unknown"
            layout_name = layout.getName() if layout.isSetName() else "unknown"
            
            self.logger.info(f"Found SBML Layout: '{layout_id}' ({layout_name})")
            
            # Extract species positions from species glyphs
            positions = {}
            num_species_glyphs = layout.getNumSpeciesGlyphs()
            
            for i in range(num_species_glyphs):
                glyph = layout.getSpeciesGlyph(i)
                
                if not glyph.isSetSpeciesId():
                    continue
                
                species_id = glyph.getSpeciesId()
                
                # Get bounding box
                if not glyph.isSetBoundingBox():
                    continue
                
                bbox = glyph.getBoundingBox()
                
                # Extract position (x, y are already in Cartesian coordinates)
                x = bbox.getX()
                y = bbox.getY()
                
                positions[species_id] = (x, y)
                self.logger.debug(f"Layout glyph: {species_id} at ({x:.1f}, {y:.1f})")
            
            if not positions:
                self.logger.warning("Layout extension exists but contains no species glyphs")
                return None
            
            self.logger.info(f"Successfully extracted {len(positions)} positions from SBML Layout extension")
            return positions
            
        except ImportError:
            self.logger.warning("libsbml not available, cannot read Layout extension")
            return None
        except Exception as e:
            self.logger.warning(f"Error reading SBML Layout extension: {e}", exc_info=True)
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
