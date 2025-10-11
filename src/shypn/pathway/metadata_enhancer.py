"""Metadata enhancement processor.

Enriches Petri net elements with additional metadata from KEGG pathway:
- Compound names and descriptions
- Reaction information
- KEGG identifiers for linking
- Color and shape information
- Compartment detection
"""

from typing import Optional, Dict, List
import logging

from shypn.pathway.base import PostProcessorBase


logger = logging.getLogger(__name__)


class MetadataEnhancer(PostProcessorBase):
    """Enhance elements with metadata from KEGG pathway.
    
    Extracts additional information from the pathway and enriches
    Place and Transition objects with useful metadata for:
    - Display (tooltips, labels, descriptions)
    - Linking back to KEGG database
    - Visual styling (colors from pathway)
    - Functional classification
    
    Example:
        from shypn.pathway.metadata_enhancer import MetadataEnhancer
        from shypn.pathway.options import EnhancementOptions
        
        options = EnhancementOptions(
            metadata_extract_names=True,
            metadata_extract_kegg_ids=True,
            metadata_detect_compartments=True
        )
        
        enhancer = MetadataEnhancer(options)
        enhanced_document = enhancer.process(document, pathway)
        
        # Elements now have rich metadata
        for place in document.places:
            if hasattr(place, 'metadata'):
                print(f"Place {place.id}: {place.metadata.get('name')}")
                print(f"  KEGG ID: {place.metadata.get('kegg_id')}")
                print(f"  Compartment: {place.metadata.get('compartment')}")
    """
    
    def __init__(self, options: Optional['EnhancementOptions'] = None):
        """Initialize metadata enhancer.
        
        Args:
            options: Enhancement options with metadata parameters.
        """
        super().__init__(options)
        self.logger = logging.getLogger(f"{__name__}.MetadataEnhancer")
    
    def get_name(self) -> str:
        """Return processor name."""
        return "Metadata Enhancer"
    
    def is_applicable(self, document: 'DocumentModel', pathway: Optional['KEGGPathway'] = None) -> bool:
        """Check if metadata enhancement is applicable.
        
        Requires:
            - Metadata enhancement enabled
            - Pathway data available (for enrichment)
        """
        # Check if enabled
        if self.options and not self.options.enable_metadata_enhancement:
            return False
        
        # Check if pathway is provided
        if pathway is None:
            return False
        
        # Check minimum elements
        if len(document.places) + len(document.transitions) < 1:
            return False
        
        return True
    
    def _build_entry_map(self, pathway: 'KEGGPathway') -> Dict[str, 'KEGGEntry']:
        """Build mapping from entry IDs to KEGGEntry objects.
        
        Args:
            pathway: KEGG pathway data
            
        Returns:
            dict: Mapping from entry ID to KEGGEntry
        """
        return pathway.entries
    
    def _build_reaction_map(self, pathway: 'KEGGPathway') -> Dict[str, 'KEGGReaction']:
        """Build mapping from reaction IDs to KEGGReaction objects.
        
        Args:
            pathway: KEGG pathway data
            
        Returns:
            dict: Mapping from reaction ID to KEGGReaction
        """
        reaction_map = {}
        for reaction in pathway.reactions:
            reaction_map[reaction.id] = reaction
            # Also map by reaction name (e.g., "rn:R01068")
            if reaction.name:
                reaction_map[reaction.name] = reaction
        return reaction_map
    
    def _extract_compound_name(self, entry: 'KEGGEntry') -> str:
        """Extract clean compound name from KEGG entry.
        
        Args:
            entry: KEGG entry for compound
            
        Returns:
            str: Compound display name
        """
        # Use graphics name if available (usually most readable)
        if entry.graphics and entry.graphics.name:
            name = entry.graphics.name
            # Clean up formatting
            name = name.replace(',', ', ')  # Add space after commas
            name = ' '.join(name.split())  # Normalize whitespace
            return name
        
        # Fall back to entry name (KEGG ID format)
        kegg_ids = entry.get_kegg_ids()
        if kegg_ids:
            # Return first ID
            return kegg_ids[0]
        
        return "Compound"
    
    def _extract_reaction_name(self, entry: 'KEGGEntry', reaction: Optional['KEGGReaction'] = None) -> str:
        """Extract clean reaction name from KEGG entry/reaction.
        
        Args:
            entry: KEGG entry for gene/enzyme
            reaction: Optional associated KEGGReaction
            
        Returns:
            str: Reaction display name
        """
        # Try graphics name first
        if entry.graphics and entry.graphics.name:
            name = entry.graphics.name
            # Clean up gene list format (e.g., "Gene1, Gene2")
            if ',' in name:
                # For gene lists, show first gene + count
                genes = [g.strip() for g in name.split(',')]
                if len(genes) > 1:
                    return f"{genes[0]} (+{len(genes)-1})"
                return genes[0]
            return name
        
        # Try reaction name
        if reaction and reaction.name:
            return reaction.name
        
        # Fall back to entry name
        kegg_ids = entry.get_kegg_ids()
        if kegg_ids:
            return kegg_ids[0]
        
        return "Reaction"
    
    def _get_compound_type(self, entry: 'KEGGEntry') -> str:
        """Determine compound type from KEGG ID.
        
        Args:
            entry: KEGG entry for compound
            
        Returns:
            str: Compound type (metabolite, cofactor, etc.)
        """
        kegg_ids = entry.get_kegg_ids()
        if not kegg_ids:
            return "unknown"
        
        first_id = kegg_ids[0]
        
        # Common cofactors
        cofactors = {
            'cpd:C00001': 'cofactor',  # H2O
            'cpd:C00002': 'cofactor',  # ATP
            'cpd:C00003': 'cofactor',  # NAD+
            'cpd:C00004': 'cofactor',  # NADH
            'cpd:C00005': 'cofactor',  # NADPH
            'cpd:C00006': 'cofactor',  # NADP+
            'cpd:C00008': 'cofactor',  # ADP
            'cpd:C00009': 'cofactor',  # Orthophosphate
            'cpd:C00010': 'cofactor',  # CoA
            'cpd:C00080': 'cofactor',  # H+
        }
        
        if first_id in cofactors:
            return 'cofactor'
        
        return 'metabolite'
    
    def _detect_compartments(self, document: 'DocumentModel', pathway: 'KEGGPathway') -> Dict[str, List]:
        """Detect cellular compartments from element positions.
        
        Uses clustering or position-based heuristics to identify compartments.
        
        Args:
            document: Document model
            pathway: KEGG pathway data
            
        Returns:
            dict: Mapping from compartment name to list of element IDs
        """
        # For now, return empty dict (compartment detection is complex)
        # Future enhancement: Use K-means clustering or KEGG map regions
        return {}
    
    def process(self, document: 'DocumentModel', pathway: Optional['KEGGPathway'] = None) -> 'DocumentModel':
        """Enhance elements with metadata.
        
        Args:
            document: Document to enhance.
            pathway: Pathway data for extracting metadata.
        
        Returns:
            Enhanced document with rich metadata.
        """
        self.reset_stats()
        self.validate_inputs(document, pathway)
        
        if pathway is None:
            self.logger.warning("No pathway data provided, cannot enhance metadata")
            self.stats = {
                'places_enhanced': 0,
                'transitions_enhanced': 0,
                'kegg_ids_added': 0,
                'compartments_detected': 0,
                'implemented': True
            }
            return document
        
        # Get configuration
        extract_names = self.options.metadata_extract_names if self.options else True
        extract_colors = self.options.metadata_extract_colors if self.options else True
        
        # Build mappings
        entry_map = self._build_entry_map(pathway)
        reaction_map = self._build_reaction_map(pathway)
        
        # Track statistics
        places_enhanced = 0
        transitions_enhanced = 0
        kegg_ids_added = 0
        
        # Enhance places (compounds)
        for place in document.places:
            # Initialize metadata dict if not exists
            if not hasattr(place, 'metadata'):
                place.metadata = {}
            
            # Try to find corresponding KEGG entry
            # Check if metadata already has kegg_entry_id from conversion
            kegg_entry_id = place.metadata.get('kegg_entry_id')
            
            if kegg_entry_id and kegg_entry_id in entry_map:
                entry = entry_map[kegg_entry_id]
                
                # Extract compound name
                if extract_names:
                    compound_name = self._extract_compound_name(entry)
                    place.metadata['compound_name'] = compound_name
                    
                    # Update place label if desired
                    if not place.label or place.label == place.name:
                        place.label = compound_name
                
                # Store KEGG IDs
                kegg_ids = entry.get_kegg_ids()
                if kegg_ids:
                    place.metadata['kegg_compound_ids'] = kegg_ids
                    kegg_ids_added += len(kegg_ids)
                
                # Determine compound type
                compound_type = self._get_compound_type(entry)
                place.metadata['compound_type'] = compound_type
                
                # Extract colors if enabled
                if extract_colors and entry.graphics:
                    if entry.graphics.bgcolor:
                        place.metadata['kegg_bgcolor'] = entry.graphics.bgcolor
                    if entry.graphics.fgcolor:
                        place.metadata['kegg_fgcolor'] = entry.graphics.fgcolor
                
                places_enhanced += 1
        
        # Enhance transitions (reactions)
        for transition in document.transitions:
            # Initialize metadata dict if not exists
            if not hasattr(transition, 'metadata'):
                transition.metadata = {}
            
            # Try to find corresponding KEGG entry/reaction
            kegg_entry_id = transition.metadata.get('kegg_entry_id')
            reaction_id = transition.metadata.get('kegg_reaction_id')
            
            entry = None
            reaction = None
            
            if kegg_entry_id and kegg_entry_id in entry_map:
                entry = entry_map[kegg_entry_id]
            
            if reaction_id and reaction_id in reaction_map:
                reaction = reaction_map[reaction_id]
            
            if entry or reaction:
                # Extract reaction name
                if extract_names and entry:
                    reaction_name = self._extract_reaction_name(entry, reaction)
                    transition.metadata['reaction_name'] = reaction_name
                    
                    # Update transition label if desired
                    if not transition.label or transition.label == transition.name:
                        transition.label = reaction_name
                
                # Store KEGG IDs
                if entry:
                    kegg_ids = entry.get_kegg_ids()
                    if kegg_ids:
                        transition.metadata['kegg_gene_ids'] = kegg_ids
                        kegg_ids_added += len(kegg_ids)
                
                if reaction:
                    transition.metadata['kegg_reaction_name'] = reaction.name
                    transition.metadata['kegg_reaction_type'] = reaction.type
                    transition.metadata['is_reversible'] = reaction.is_reversible()
                    kegg_ids_added += 1
                
                # Extract colors if enabled
                if extract_colors and entry and entry.graphics:
                    if entry.graphics.bgcolor:
                        transition.metadata['kegg_bgcolor'] = entry.graphics.bgcolor
                    if entry.graphics.fgcolor:
                        transition.metadata['kegg_fgcolor'] = entry.graphics.fgcolor
                
                transitions_enhanced += 1
        
        # Detect compartments
        compartments = self._detect_compartments(document, pathway)
        
        # Store statistics
        self.stats = {
            'places_enhanced': places_enhanced,
            'transitions_enhanced': transitions_enhanced,
            'kegg_ids_added': kegg_ids_added,
            'compartments_detected': len(compartments),
            'implemented': True
        }
        
        return document
