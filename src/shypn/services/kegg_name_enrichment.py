"""KEGG Name Enrichment Service.

Post-import enrichment to fetch biological names from KEGG REST API
for compounds (C#####) and reactions (R#####) that lack proper names.

This is a USER-TRIGGERED operation, not part of the import flow,
because API queries are slow and should be opt-in.
"""

import re
import time
from typing import Dict, List, Set, Tuple, Optional
from dataclasses import dataclass

from shypn.importer.kegg.api_client import KEGGAPIClient
from shypn.data.canvas.document_model import DocumentModel


@dataclass
class EnrichmentResult:
    """Result of name enrichment operation."""
    
    places_enriched: int
    transitions_enriched: int
    places_failed: int
    transitions_failed: int
    total_api_calls: int
    duration_seconds: float
    details: Dict[str, str]  # old_name -> new_name


class KEGGNameEnricher:
    """Enriches KEGG model with biological names from KEGG API.
    
    Replaces KEGG codes (C#####, R#####) with actual biological names
    by querying the KEGG REST API.
    
    Usage:
        enricher = KEGGNameEnricher()
        result = enricher.enrich_document(document)
        print(f"Enriched {result.places_enriched} places, {result.transitions_enriched} transitions")
    """
    
    # Pattern to detect KEGG codes
    COMPOUND_CODE_PATTERN = re.compile(r'^C\d{5}$')
    REACTION_CODE_PATTERN = re.compile(r'^R\d{5}$')
    
    def __init__(self, api_client: Optional[KEGGAPIClient] = None, 
                 progress_callback=None):
        """Initialize enricher.
        
        Args:
            api_client: KEGG API client (creates default if None)
            progress_callback: Optional function(current, total, message) for progress updates
        """
        self.client = api_client or KEGGAPIClient()
        self.progress_callback = progress_callback
        
    def enrich_document(self, document: DocumentModel) -> EnrichmentResult:
        """Enrich all places and transitions in document with KEGG names.
        
        Only enriches items that:
        - Have KEGG codes as names (C#####, R#####)
        - Are tagged with data_source='kegg_import'
        
        Args:
            document: Document to enrich
            
        Returns:
            EnrichmentResult with statistics and details
        """
        start_time = time.time()
        
        places_enriched = 0
        transitions_enriched = 0
        places_failed = 0
        transitions_failed = 0
        api_calls = 0
        details = {}
        
        # Find places needing enrichment
        places_to_enrich = []
        for place in document.places:
            if self._needs_enrichment_place(place):
                places_to_enrich.append(place)
        
        # Find transitions needing enrichment
        transitions_to_enrich = []
        for transition in document.transitions:
            if self._needs_enrichment_transition(transition):
                transitions_to_enrich.append(transition)
        
        total_items = len(places_to_enrich) + len(transitions_to_enrich)
        
        if total_items == 0:
            return EnrichmentResult(
                places_enriched=0,
                transitions_enriched=0,
                places_failed=0,
                transitions_failed=0,
                total_api_calls=0,
                duration_seconds=time.time() - start_time,
                details={}
            )
        
        current = 0
        
        # Enrich places (compounds)
        for place in places_to_enrich:
            current += 1
            if self.progress_callback:
                self.progress_callback(current, total_items, f"Enriching place {place.name}")
            
            new_name = self._fetch_compound_name(place.name)
            api_calls += 1
            
            if new_name and new_name != place.name:
                details[place.name] = new_name
                place.name = new_name
                places_enriched += 1
            else:
                places_failed += 1
        
        # Enrich transitions (reactions)
        for transition in transitions_to_enrich:
            current += 1
            if self.progress_callback:
                self.progress_callback(current, total_items, f"Enriching transition {transition.name}")
            
            new_name = self._fetch_reaction_name(transition.name)
            api_calls += 1
            
            if new_name and new_name != transition.name:
                details[transition.name] = new_name
                transition.name = new_name
                transitions_enriched += 1
            else:
                transitions_failed += 1
        
        duration = time.time() - start_time
        
        return EnrichmentResult(
            places_enriched=places_enriched,
            transitions_enriched=transitions_enriched,
            places_failed=places_failed,
            transitions_failed=transitions_failed,
            total_api_calls=api_calls,
            duration_seconds=duration,
            details=details
        )
    
    def _needs_enrichment_place(self, place) -> bool:
        """Check if place needs name enrichment.
        
        Args:
            place: Place to check
            
        Returns:
            True if place has KEGG compound code as name
        """
        # Must be KEGG import
        if not hasattr(place, 'metadata') or not place.metadata:
            return False
        if place.metadata.get('data_source') != 'kegg_import':
            return False
        
        # Must have KEGG compound code as name
        return bool(self.COMPOUND_CODE_PATTERN.match(place.name))
    
    def _needs_enrichment_transition(self, transition) -> bool:
        """Check if transition needs name enrichment.
        
        Args:
            transition: Transition to check
            
        Returns:
            True if transition has KEGG reaction code as name
        """
        # Must be KEGG import
        if not hasattr(transition, 'metadata') or not transition.metadata:
            return False
        if transition.metadata.get('data_source') != 'kegg_import':
            return False
        
        # Must have KEGG reaction code as name
        return bool(self.REACTION_CODE_PATTERN.match(transition.name))
    
    def _fetch_compound_name(self, compound_id: str) -> Optional[str]:
        """Fetch compound name from KEGG API.
        
        Args:
            compound_id: KEGG compound ID (e.g., "C00002")
            
        Returns:
            Biological name or None if fetch fails
        """
        try:
            # Query KEGG API
            response = self.client._make_request(f"https://rest.kegg.jp/get/{compound_id}")
            
            if not response:
                return None
            
            # Parse NAME field
            # Format:
            # NAME        ATP;
            #             Adenosine 5'-triphosphate
            
            lines = response.split('\n')
            name_section = []
            in_name_section = False
            
            for line in lines:
                if line.startswith('NAME'):
                    in_name_section = True
                    # Extract first name after NAME
                    name_part = line[12:].strip()  # Skip "NAME        "
                    if name_part:
                        name_section.append(name_part)
                elif in_name_section:
                    if line.startswith(' '):
                        # Continuation of NAME section
                        name_section.append(line.strip())
                    else:
                        # End of NAME section
                        break
            
            if name_section:
                # First name is usually the common abbreviation
                first_name = name_section[0].rstrip(';').strip()
                
                # Validate it's not just the compound code
                if first_name and not self.COMPOUND_CODE_PATTERN.match(first_name):
                    return first_name
                
                # Try second name if first is code or too short
                if len(name_section) > 1:
                    second_name = name_section[1].rstrip(';').strip()
                    if second_name:
                        # Extract first word (usually good name)
                        first_word = second_name.split()[0]
                        if len(first_word) >= 3:
                            return first_word
            
            return None
            
        except Exception as e:
            return None
    
    def _fetch_reaction_name(self, reaction_id: str) -> Optional[str]:
        """Fetch reaction name from KEGG API.
        
        Args:
            reaction_id: KEGG reaction ID (e.g., "R00001")
            
        Returns:
            Biological name (enzyme name) or None if fetch fails
        """
        try:
            # Query KEGG API
            response = self.client._make_request(f"https://rest.kegg.jp/get/{reaction_id}")
            
            if not response:
                return None
            
            # Parse NAME field (enzyme name)
            # Format:
            # NAME        polyphosphate polyphosphohydrolase
            # ENZYME      3.6.1.10
            
            lines = response.split('\n')
            enzyme_name = None
            ec_number = None
            
            for line in lines:
                if line.startswith('NAME'):
                    enzyme_name = line[12:].strip()  # Skip "NAME        "
                elif line.startswith('ENZYME'):
                    ec_number = line[12:].strip()  # Skip "ENZYME      "
            
            # Prefer enzyme name over EC number
            if enzyme_name:
                # Extract first word (usually good enzyme name)
                first_word = enzyme_name.split()[0]
                if len(first_word) >= 3 and not first_word.startswith('R'):
                    return first_word
            
            # Fallback to EC number
            if ec_number:
                return f"EC_{ec_number}"
            
            return None
            
        except Exception as e:
            return None


def enrich_kegg_names(document: DocumentModel, 
                     progress_callback=None) -> EnrichmentResult:
    """Convenience function to enrich KEGG document with biological names.
    
    Args:
        document: Document to enrich
        progress_callback: Optional function(current, total, message) for progress
        
    Returns:
        EnrichmentResult with statistics
        
    Example:
        >>> result = enrich_kegg_names(document, lambda c, t, m: print(f"{c}/{t}: {m}"))
        >>> print(f"Enriched {result.places_enriched} places in {result.duration_seconds:.1f}s")
    """
    enricher = KEGGNameEnricher(progress_callback=progress_callback)
    return enricher.enrich_document(document)
