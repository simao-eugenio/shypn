#!/usr/bin/env python3
"""SABIO-RK REST API Client (Optimized).

This module provides a client for querying the SABIO-RK database via REST API.
SABIO-RK contains ~40,000 kinetic laws with rate constants for biochemical reactions.

API Documentation: https://sabiork.h-its.org/sabioRestWebServices/

Key Features:
- No authentication required (public API)
- Returns data in SBML format
- Query by EC number with organism filter to limit results
- Retrieve rate constants (k_forward, k_reverse, Km, Kcat, Ki)

Performance Notes:
- SABIO-RK REST API has no pagination support
- Queries returning >100 results can timeout (30-120+ seconds)
- **ALWAYS use organism filter** to limit results to manageable size
- Count endpoint works well - use it to check result size before fetching
"""

import sys
import logging
import xml.etree.ElementTree as ET
from typing import Optional, Dict, List, Any
from urllib.parse import quote

try:
    import requests
except ImportError:
    print("Warning: requests library not available. Install with: pip install requests", file=sys.stderr)
    requests = None


class SabioRKClient:
    """Client for querying SABIO-RK database via REST API.
    
    Provides methods to query kinetic parameters for biochemical reactions.
    No authentication required - SABIO-RK is a free public database.
    
    IMPORTANT: Always specify organism filter to avoid timeouts!
    SABIO-RK API has no pagination - large result sets (>100) will timeout.
    
    Attributes:
        base_url: SABIO-RK REST API base URL (HTTPS)
        logger: Logger instance
        timeout: Request timeout in seconds
    """
    
    def __init__(self, timeout: int = 60):
        """Initialize SABIO-RK REST client.
        
        Args:
            timeout: Request timeout in seconds (default: 60)
        """
        self.base_url = "https://sabiork.h-its.org/sabioRestWebServices"
        self.logger = logging.getLogger(self.__class__.__name__)
        self.timeout = timeout
        
        if not requests:
            self.logger.warning("requests library not available - API calls will fail")
    
    def query_by_ec_number(self, ec_number: str, organism: str = None) -> Optional[Dict[str, Any]]:
        """Query SABIO-RK by EC number with organism filter.
        
        IMPORTANT: Organism filter is strongly recommended to avoid timeouts!
        Without organism filter, queries may return hundreds of results and timeout.
        
        Args:
            ec_number: EC number (e.g., "2.7.1.1")
            organism: **REQUIRED** organism filter (e.g., "Homo sapiens")
        
        Returns:
            Dict with kinetic parameters or None if query fails
        """
        if not requests:
            self.logger.error("[SABIO-RK] requests library not available")
            return None
        
        if not organism:
            self.logger.warning("[SABIO-RK] No organism specified - query may timeout!")
            self.logger.warning("[SABIO-RK] Recommend specifying organism (e.g., 'Homo sapiens')")
        
        try:
            # Build query string with REQUIRED quotes around values
            query_parts = [f'ECNumber:"{ec_number}"']
            if organism:
                query_parts.append(f'Organism:"{organism}"')
            
            query = " AND ".join(query_parts)
            
            # Step 1: Check result count FIRST
            count = self._get_result_count(query)
            if count is None:
                return None
            
            if count == 0:
                self.logger.info(f"[SABIO-RK] No results found for EC {ec_number}" + (f" in {organism}" if organism else ""))
                return None
            
            # Batch optimization: Reject large result sets to prevent timeouts
            # Note: Manual queries (single EC) can handle more results than batch queries
            if count > 150:
                self.logger.warning(f"[SABIO-RK] Query would return {count} results - likely to timeout!")
                if organism:
                    self.logger.warning(f"[SABIO-RK] Even with organism filter '{organism}', too many results")
                    self.logger.warning(f"[SABIO-RK] Try a more specific organism or contact database administrators")
                else:
                    self.logger.warning(f"[SABIO-RK] Please specify organism filter to reduce results")
                return None
            
            self.logger.info(f"[SABIO-RK] Found {count} results for EC {ec_number}" + (f" in {organism}" if organism else ""))
            
            # Step 2: Fetch SBML data (with increased timeout for large results)
            timeout = self.timeout if count < 20 else min(count * 2, 120)
            result = self._fetch_sbml(query, ec_number, timeout)
            
            # Add query organism to result for display
            if result and organism:
                result['query_organism'] = organism
            
            if result and result.get('parameters'):
                self.logger.info(f"[SABIO-RK] ✓ Retrieved {len(result['parameters'])} kinetic parameters")
            
            return result
            
        except Exception as e:
            self.logger.error(f"[SABIO-RK] Error querying EC {ec_number}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_result_count(self, query: str) -> Optional[int]:
        """Get count of results for a query.
        
        Args:
            query: URL-encoded query string
        
        Returns:
            Number of results or None if error
        """
        try:
            encoded_query = quote(query)
            url = f"{self.base_url}/searchKineticLaws/count?q={encoded_query}&format=txt"
            
            self.logger.debug(f"[SABIO-RK] Counting results...")
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Response is plain text number
            count_text = response.text.strip()
            if "No results" in count_text:
                return 0
            
            try:
                count = int(count_text)
                return count
            except ValueError:
                self.logger.error(f"[SABIO-RK] Invalid count response: {count_text}")
                return None
                
        except requests.exceptions.Timeout:
            self.logger.error("[SABIO-RK] Timeout getting result count")
            return None
        except Exception as e:
            self.logger.error(f"[SABIO-RK] Error getting count: {e}")
            return None
    
    def _fetch_sbml(self, query: str, identifier: str, timeout: int) -> Optional[Dict[str, Any]]:
        """Fetch SBML data for a query.
        
        Args:
            query: Query string (not URL-encoded)
            identifier: EC number or reaction ID for logging
            timeout: Request timeout in seconds
        
        Returns:
            Dict with parsed kinetic parameters or None
        """
        try:
            encoded_query = quote(query)
            url = f"{self.base_url}/searchKineticLaws/sbml?q={encoded_query}"
            
            self.logger.debug(f"[SABIO-RK] Fetching SBML data (timeout={timeout}s)...")
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            # Parse SBML response
            result = self._parse_sbml_response(response.text, identifier)
            return result
            
        except requests.exceptions.Timeout:
            self.logger.error(f"[SABIO-RK] Timeout fetching data (waited {timeout}s)")
            return None
        except Exception as e:
            self.logger.error(f"[SABIO-RK] Error fetching SBML: {e}")
            return None
    
    def query_by_reaction_id(self, kegg_reaction_id: str) -> Optional[Dict[str, Any]]:
        """Query SABIO-RK by KEGG reaction ID.
        
        Args:
            kegg_reaction_id: KEGG reaction ID (e.g., "R00200" or "200")
        
        Returns:
            Dict with kinetic parameters or None if query fails
        """
        if not requests:
            self.logger.error("[SABIO-RK] requests library not available")
            return None
        
        try:
            # Normalize reaction ID
            if kegg_reaction_id.isdigit():
                kegg_reaction_id = f"R{int(kegg_reaction_id):05d}"
            elif kegg_reaction_id.startswith('R') and len(kegg_reaction_id) < 6:
                kegg_reaction_id = f"R{int(kegg_reaction_id[1:]):05d}"
            
            query = f'KeggReactionID:"{kegg_reaction_id}"'
            
            # Check count first
            count = self._get_result_count(query)
            if count is None or count == 0:
                self.logger.info(f"[SABIO-RK] No results found for {kegg_reaction_id}")
                return None
            
            if count > 150:
                self.logger.warning(f"[SABIO-RK] {count} results - may timeout. Consider adding organism filter.")
            
            self.logger.info(f"[SABIO-RK] Found {count} results for {kegg_reaction_id}")
            
            # Fetch data
            timeout = self.timeout if count < 50 else min(count * 2, 120)
            result = self._fetch_sbml(query, kegg_reaction_id, timeout)
            
            return result
            
        except Exception as e:
            self.logger.error(f"[SABIO-RK] Error querying reaction {kegg_reaction_id}: {e}")
            return None
    
    def query_by_compounds(self, substrate_ids: List[str], product_ids: List[str]) -> Optional[Dict[str, Any]]:
        """Query SABIO-RK by substrate and product compound IDs.
        
        Args:
            substrate_ids: List of substrate KEGG compound IDs (e.g., ["C00031", "C00002"])
            product_ids: List of product KEGG compound IDs
        
        Returns:
            Dict with kinetic parameters or None if query fails
        """
        self.logger.warning("[SABIO-RK] Query by compounds often returns too many results (timeouts)")
        self.logger.warning("[SABIO-RK] Consider using EC number with organism filter instead")
        return None
    
    def _parse_sbml_response(self, sbml_text: str, identifier: str) -> Optional[Dict[str, Any]]:
        """Parse SBML response from SABIO-RK.
        
        Extracts kinetic parameters from SBML kineticLaw elements.
        
        Args:
            sbml_text: SBML XML text
            identifier: EC number or reaction ID for logging
        
        Returns:
            Dict with parsed kinetic parameters
        """
        try:
            # Parse XML
            root = ET.fromstring(sbml_text)
            
            # SABIO-RK returns SBML Level 3 Version 1
            # Define SBML namespaces for both Level 2 and Level 3
            namespaces_l3 = {
                'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
                'math': 'http://www.w3.org/1998/Math/MathML'
            }
            namespaces_l2 = {
                'sbml': 'http://www.sbml.org/sbml/level2/version4',
                'math': 'http://www.w3.org/1998/Math/MathML'
            }
            
            # Try Level 3 first (current SABIO-RK format), fall back to Level 2
            reactions = root.findall('.//sbml:reaction', namespaces_l3)
            if not reactions:
                reactions = root.findall('.//sbml:reaction', namespaces_l2)
            
            # Use the correct namespace for the rest of parsing
            namespaces = namespaces_l3 if root.find('.//{http://www.sbml.org/sbml/level3/version1/core}reaction') else namespaces_l2
            
            if not reactions:
                self.logger.debug(f"[SABIO-RK] No reactions found in SBML for {identifier}")
                return None
            
            # Collect all kinetic parameters from all reactions
            all_parameters = []
            
            # Define RDF namespace for annotations
            rdf_ns = {'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
                      'bqbiol': 'http://biomodels.net/biology-qualifiers/'}
            
            for reaction in reactions:
                reaction_id = reaction.get('id', 'unknown')
                reaction_name = reaction.get('name', reaction_id)
                
                # Extract KEGG reaction ID and organism from RDF annotations
                kegg_reaction_id = None
                organism = None
                
                annotation = reaction.find('.//sbml:annotation', namespaces)
                if annotation is not None:
                    # Find KEGG reaction ID
                    kegg_refs = annotation.findall('.//rdf:li[@rdf:resource]', rdf_ns)
                    for ref in kegg_refs:
                        resource = ref.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource', '')
                        if 'kegg.reaction' in resource:
                            # Extract R00299 from https://identifiers.org/kegg.reaction/R00299
                            kegg_reaction_id = resource.split('/')[-1]
                            break
                    
                    # Find organism (BTO - BRENDA Tissue Ontology)
                    # Also check for Taxonomy references
                    for ref in kegg_refs:
                        resource = ref.get('{http://www.w3.org/1999/02/22-rdf-syntax-ns#}resource', '')
                        if 'taxonomy' in resource:
                            # Extract taxonomy ID and map to organism name (simplified)
                            tax_id = resource.split('/')[-1]
                            organism = self._map_taxonomy_id(tax_id)
                            break
                
                # Get kinetic law
                kinetic_law = reaction.find('.//sbml:kineticLaw', namespaces)
                if kinetic_law is None:
                    continue
                
                # Extract organism from SABIO-RK annotation if not found in RDF
                if not organism:
                    sbrk_ns = {'sbrk': 'http://sabiork.h-its.org'}
                    organism_elem = kinetic_law.find('.//sbrk:organism', sbrk_ns)
                    if organism_elem is not None and organism_elem.text:
                        organism = organism_elem.text
                
                # Extract parameters (SBML Level 2 uses <parameter>, Level 3 uses <localParameter>)
                parameters = kinetic_law.findall('.//sbml:parameter', namespaces)
                if not parameters:
                    parameters = kinetic_law.findall('.//sbml:localParameter', namespaces)
                
                for param in parameters:
                    param_id = param.get('id', '')
                    param_name = param.get('name', param_id)
                    param_value = param.get('value')
                    param_units = param.get('units', '')
                    
                    if param_value:
                        try:
                            value_float = float(param_value)
                            
                            # Store parameter with metadata
                            all_parameters.append({
                                'reaction_id': reaction_id,
                                'reaction_name': reaction_name,
                                'kegg_reaction_id': kegg_reaction_id,
                                'organism': organism or 'Unknown',
                                'parameter_id': param_id,
                                'parameter_name': param_name,
                                'value': value_float,
                                'units': param_units,
                                'parameter_type': self._classify_parameter(param_id, param_name)
                            })
                        except ValueError:
                            continue
            
            if not all_parameters:
                self.logger.debug(f"[SABIO-RK] No kinetic parameters found for {identifier}")
                return None
            
            return {
                'identifier': identifier,
                'parameters': all_parameters,
                'source': 'sabio_rk',
                'query_organism': None  # Will be set by caller if organism filter was used
            }
            
        except ET.ParseError as e:
            self.logger.error(f"[SABIO-RK] XML parse error: {e}")
            return None
        except Exception as e:
            self.logger.error(f"[SABIO-RK] Error parsing SBML: {e}")
            return None
    
    def _map_taxonomy_id(self, tax_id: str) -> str:
        """Map taxonomy ID to organism name (simplified mapping).
        
        Args:
            tax_id: NCBI Taxonomy ID
        
        Returns:
            Organism name or taxonomy ID if not in mapping
        """
        # Common organism taxonomy IDs
        tax_map = {
            '9606': 'Homo sapiens',
            '10090': 'Mus musculus',
            '10116': 'Rattus norvegicus',
            '562': 'Escherichia coli',
            '4932': 'Saccharomyces cerevisiae',
            '7227': 'Drosophila melanogaster',
            '6239': 'Caenorhabditis elegans',
            '3702': 'Arabidopsis thaliana'
        }
        return tax_map.get(tax_id, f'Tax:{tax_id}')
    
    def _classify_parameter(self, param_id: str, param_name: str) -> str:
        """Classify parameter type based on ID or name.
        
        Args:
            param_id: Parameter ID from SBML
            param_name: Parameter name from SBML
        
        Returns:
            Parameter type: 'k_forward', 'k_reverse', 'Km', 'Kcat', 'Ki', 'Vmax', or 'other'
        """
        combined = (param_id + param_name).lower()
        
        # Rate constants
        if 'kf' in combined or 'k_f' in combined or 'kfor' in combined or 'forward' in combined:
            return 'k_forward'
        elif 'kr' in combined or 'k_r' in combined or 'krev' in combined or 'reverse' in combined:
            return 'k_reverse'
        
        # Michaelis-Menten parameters
        elif 'km' in combined and 'kcat' not in combined:
            return 'Km'
        elif 'kcat' in combined or 'turnover' in combined:
            return 'Kcat'
        elif 'ki' in combined or 'inhibit' in combined:
            return 'Ki'
        elif 'vmax' in combined or 'v_max' in combined:
            return 'Vmax'
        
        # Catch-all
        return 'other'
    
    def get_organisms(self) -> List[str]:
        """Get list of available organisms in SABIO-RK.
        
        Returns:
            List of organism names
        """
        # Common organisms in SABIO-RK
        return [
            "Homo sapiens",
            "Mus musculus",
            "Rattus norvegicus",
            "Saccharomyces cerevisiae",
            "Escherichia coli",
            "Arabidopsis thaliana"
        ]
    
    def test_connection(self) -> bool:
        """Test connection to SABIO-RK REST API.
        
        Returns:
            True if API is reachable, False otherwise
        """
        if not requests:
            return False
        
        try:
            # Test with status endpoint
            url = f"{self.base_url}/status"
            response = requests.get(url, timeout=10)
            return response.status_code == 200 and "UP" in response.text
        except Exception:
            return False


# Module-level convenience function
def create_sabio_rk_client() -> SabioRKClient:
    """Create a SABIO-RK client instance.
    
    Returns:
        SabioRKClient instance
    """
    return SabioRKClient()
