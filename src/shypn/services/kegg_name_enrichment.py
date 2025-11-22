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
    EC_NUMBER_PATTERN = re.compile(r'^EC_[\d\.]+$')  # Match EC_x.x.x.x format
    
    # Short, eval-safe names for common metabolites
    # These override KEGG API results for better simulation compatibility
    COMPOUND_SHORT_NAMES = {
        'C00002': 'ATP',
        'C00008': 'ADP',
        'C00020': 'AMP',
        'C00044': 'GTP',
        'C00035': 'GDP',
        'C00144': 'GMP',
        'C00063': 'CTP',
        'C00112': 'CDP',
        'C00055': 'CMP',
        'C00075': 'UTP',
        'C00015': 'UDP',
        'C00105': 'UMP',
        'C00003': 'NADplus',      # NAD+
        'C00004': 'NADH',
        'C00006': 'NADPplus',     # NADP+
        'C00005': 'NADPH',
        'C00016': 'FAD',
        'C00010': 'CoA',
        'C00024': 'AcetylCoA',
        'C00001': 'H2O',
        'C00007': 'O2',
        'C00011': 'CO2',
        'C00014': 'NH3',
        'C00009': 'Pi',            # Orthophosphate
        'C00013': 'PPi',           # Pyrophosphate
        'C00080': 'Hplus',         # H+
        'C00031': 'Glucose',       # D-Glucose
        'C00221': 'Glucose1P',     # alpha-D-Glucose 1-phosphate
        'C00668': 'Glucose6P',     # alpha-D-Glucose 6-phosphate
        'C00103': 'Glucose1P',     # D-Glucose 1-phosphate
        'C05345': 'Fructose6P',    # beta-D-Fructose 6-phosphate
        'C00085': 'Fructose6P',    # D-Fructose 6-phosphate
        'C00354': 'Fructose1P',    # D-Fructose 1-phosphate
        'C05378': 'Fructose16BP',  # beta-D-Fructose 1,6-bisphosphate
        'C00199': 'Fructose16BP',  # D-Fructose 1,6-bisphosphate
        'C00111': 'DHAP',          # Dihydroxyacetone phosphate
        'C00118': 'GAP',           # D-Glyceraldehyde 3-phosphate
        'C00236': 'BPG13',         # 3-Phospho-D-glyceroyl phosphate (1,3-BPG)
        'C00197': 'PG3',           # 3-Phospho-D-glycerate
        'C00631': 'PG2',           # 2-Phospho-D-glycerate
        'C00074': 'PEP',           # Phosphoenolpyruvate
        'C00022': 'Pyruvate',
        'C00186': 'Lactate',       # (S)-Lactate
        'C00025': 'Glutamate',     # L-Glutamate
        'C00026': 'Ketoglutarate', # 2-Oxoglutarate
        'C00036': 'Oxaloacetate',
        'C00042': 'Succinate',
        'C00122': 'Fumarate',
        'C00149': 'Malate',        # (S)-Malate
        'C00158': 'Citrate',
        'C00311': 'Isocitrate',
        'C00417': 'Isocitrate',    # cis-Aconitate
        'C00091': 'SuccinylCoA',
        'C00026': 'Akg',           # Alpha-ketoglutarate
    }
    
    # Common enzyme abbreviations (same as reaction_mapper.py)
    ENZYME_ABBREVIATIONS = {
        '2.7.1.1': 'HK',      # Hexokinase
        '2.7.1.11': 'PFK',    # Phosphofructokinase
        '2.7.1.40': 'PK',     # Pyruvate kinase
        '5.3.1.9': 'PGI',     # Phosphoglucose isomerase
        '4.1.2.13': 'ALDO',   # Aldolase
        '5.3.1.1': 'TPI',     # Triose phosphate isomerase
        '1.2.1.12': 'GAPDH',  # Glyceraldehyde-3-phosphate dehydrogenase
        '2.7.2.3': 'PGK',     # Phosphoglycerate kinase
        '5.4.2.11': 'PGM',    # Phosphoglycerate mutase
        '4.2.1.11': 'ENO',    # Enolase
        '1.1.1.1': 'ADH',     # Alcohol dehydrogenase
        '1.1.1.27': 'LDH',    # Lactate dehydrogenase
        '2.7.1.2': 'GK',      # Glucokinase
    }
    
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
            
            # Get KEGG reaction ID from metadata (format: "rn:R00710")
            reaction_id = None
            if hasattr(transition, 'metadata') and transition.metadata:
                kegg_name = transition.metadata.get('kegg_reaction_name', '')
                if kegg_name:
                    # Remove "rn:" prefix if present
                    reaction_id = kegg_name.replace('rn:', '').strip()
            
            # If no metadata, try to extract from name (if it's R#####)
            if not reaction_id and self.REACTION_CODE_PATTERN.match(transition.name):
                reaction_id = transition.name
            
            if reaction_id:
                new_name = self._fetch_reaction_name(reaction_id)
                api_calls += 1
                
                if new_name and new_name != transition.name:
                    details[transition.name] = new_name
                    transition.name = new_name
                    transitions_enriched += 1
                else:
                    transitions_failed += 1
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
            True if transition has KEGG reaction code OR EC number as name
        """
        # Must be KEGG import
        if not hasattr(transition, 'metadata') or not transition.metadata:
            return False
        if transition.metadata.get('data_source') != 'kegg_import':
            return False
        
        # Check for KEGG reaction code OR EC number format
        # This allows enrichment of EC numbers that might have better enzyme names
        return (bool(self.REACTION_CODE_PATTERN.match(transition.name)) or
                bool(self.EC_NUMBER_PATTERN.match(transition.name)))
    
    def _fetch_compound_name(self, compound_id: str) -> Optional[str]:
        """Fetch compound name from KEGG API.
        
        Args:
            compound_id: KEGG compound ID (e.g., "C00002")
            
        Returns:
            Biological name or None if fetch fails
        """
        # First, check if we have a curated short name
        if compound_id in self.COMPOUND_SHORT_NAMES:
            return self.COMPOUND_SHORT_NAMES[compound_id]
        
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
            Biological name (enzyme abbreviation or enzyme name) or None if fetch fails
        """
        try:
            # Query KEGG API
            response = self.client._make_request(f"https://rest.kegg.jp/get/{reaction_id}")
            
            if not response:
                return None
            
            # Parse ENZYME field first (most reliable for enzyme abbreviations)
            # Format:
            # NAME        long systematic name...
            # ENZYME      4.1.2.13 2.7.1.105
            
            lines = response.split('\n')
            ec_numbers = []
            enzyme_name = None
            
            for line in lines:
                if line.startswith('ENZYME'):
                    # Can have multiple EC numbers
                    ec_part = line[12:].strip()
                    ec_numbers.extend([ec.strip() for ec in ec_part.split()])
                elif line.startswith('NAME'):
                    enzyme_name = line[12:].strip()  # Fallback
            
            # Priority 1: Check if we have a common abbreviation for the EC number
            for ec in ec_numbers:
                if ec in self.ENZYME_ABBREVIATIONS:
                    return self.ENZYME_ABBREVIATIONS[ec]
            
            # Priority 2: Try to extract a good word from enzyme name
            if enzyme_name:
                # Try each word in the enzyme name
                words = enzyme_name.split()
                for word in words:
                    # Clean up word
                    clean_word = word.rstrip(';,.-').strip()
                    # Good enzyme name: at least 4 chars, starts with uppercase, not a formula
                    if (len(clean_word) >= 4 and 
                        clean_word[0].isupper() and
                        not clean_word.startswith('D-') and
                        not clean_word.startswith('L-') and
                        not clean_word[0].isdigit() and
                        '-' not in clean_word):  # Avoid compound names
                        return clean_word
            
            # Priority 3: Return first EC number (clean format without EC_ prefix)
            if ec_numbers:
                return ec_numbers[0]
            
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
