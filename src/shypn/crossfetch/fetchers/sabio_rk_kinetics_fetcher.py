"""
SABIO-RK Kinetics Fetcher

Fetches kinetic parameters from SABIO-RK database for enzyme kinetics
and stochastic mass action rates.

Author: Shypn Development Team
Date: November 2025
"""

from typing import Dict, Any, List, Optional
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime

from .base_fetcher import BaseFetcher
from ..models import FetchResult, FetchStatus


class SabioRKKineticsFetcher(BaseFetcher):
    """Fetcher for SABIO-RK kinetic parameters.
    
    Supports:
    - Continuous transitions: Vmax, Km, Kcat, Ki (Michaelis-Menten)
    - Stochastic transitions: Rate constants (mass action)
    """
    
    # SBML namespaces for parsing
    SBML_NS = {
        'sbml': 'http://www.sbml.org/sbml/level3/version1/core',
        'sbml2': 'http://www.sbml.org/sbml/level2/version4',
        'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#'
    }
    
    def __init__(self):
        super().__init__(
            source_name="SABIO-RK",
            source_reliability=0.95  # High reliability
        )
        self.base_url = "http://sabiork.h-its.org/sabioRestWebServices/searchKineticLaws/sbml"
    
    def fetch(self,
             ec_number: str,
             organism: str = "Homo sapiens",
             **kwargs) -> FetchResult:
        """Fetch kinetic parameters by EC number.
        
        Args:
            ec_number: EC number (e.g., "2.7.1.1")
            organism: Target organism
            **kwargs: Additional parameters (temperature, pH, etc.)
            
        Returns:
            FetchResult with kinetic parameters
        """
        start_time = datetime.now()
        
        try:
            # Build query
            query_parts = [f"ECNumber:{ec_number}"]
            if organism:
                query_parts.append(f"Organism:{organism}")
            
            query = " AND ".join(query_parts)
            params = urllib.parse.urlencode({'q': query})
            url = f"{self.base_url}?{params}"
            
            self.logger.info(f"Querying SABIO-RK: {url}")
            
            # Fetch data
            with urllib.request.urlopen(url, timeout=30) as response:
                xml_content = response.read().decode('utf-8')
            
            # Parse SBML
            root = ET.fromstring(xml_content)
            
            # Extract parameters
            parameters = self._parse_sbml_parameters(root, ec_number, organism)
            
            if not parameters:
                return self._create_failed_result(
                    data_type="kinetics",
                    error=f"No kinetic parameters found for EC {ec_number}",
                    status=FetchStatus.NOT_FOUND
                )
            
            # Calculate fetch duration
            duration_ms = (datetime.now() - start_time).total_seconds() * 1000
            
            # Create success result
            fields_filled = [k for k, v in parameters.items() if v is not None]
            
            return self._create_success_result(
                data=parameters,
                data_type="kinetics",
                fields_filled=fields_filled,
                fetch_duration_ms=duration_ms,
                source_url=url
            )
            
        except urllib.error.URLError as e:
            self.logger.error(f"Network error fetching from SABIO-RK: {e}")
            return self._create_failed_result(
                data_type="kinetics",
                error=f"Network error: {str(e)}",
                status=FetchStatus.NETWORK_ERROR
            )
        except Exception as e:
            self.logger.error(f"Error fetching from SABIO-RK: {e}")
            return self._create_failed_result(
                data_type="kinetics",
                error=str(e)
            )
    
    def _parse_sbml_parameters(self,
                              root: ET.Element,
                              ec_number: str,
                              organism: str) -> Dict[str, Any]:
        """Parse SBML XML to extract kinetic parameters.
        
        Args:
            root: XML root element
            ec_number: EC number
            organism: Organism name
            
        Returns:
            Dictionary of kinetic parameters
        """
        parameters = {
            'ec_number': ec_number,
            'organism': organism,
            'vmax': None,
            'km': None,
            'kcat': None,
            'ki': None,
            'k_forward': None,
            'k_reverse': None,
            'temperature': None,
            'ph': None,
            'kinetic_law_type': None,
            'entries': []
        }
        
        # Try both SBML Level 2 and Level 3 namespaces
        for ns_key in ['sbml', 'sbml2']:
            models = root.findall(f'.//{{{self.SBML_NS[ns_key]}}}model')
            if models:
                break
        
        if not models:
            self.logger.warning("No SBML models found in response")
            return parameters
        
        # Process each model (multiple entries possible)
        for model in models:
            entry = self._parse_model_entry(model, ns_key)
            if entry:
                parameters['entries'].append(entry)
                
                # Update main parameters with first valid entry
                if parameters['vmax'] is None and entry.get('vmax'):
                    parameters['vmax'] = entry['vmax']
                if parameters['km'] is None and entry.get('km'):
                    parameters['km'] = entry['km']
                if parameters['kcat'] is None and entry.get('kcat'):
                    parameters['kcat'] = entry['kcat']
                if parameters['ki'] is None and entry.get('ki'):
                    parameters['ki'] = entry['ki']
                if parameters['k_forward'] is None and entry.get('k_forward'):
                    parameters['k_forward'] = entry['k_forward']
                if parameters['temperature'] is None and entry.get('temperature'):
                    parameters['temperature'] = entry['temperature']
                if parameters['ph'] is None and entry.get('ph'):
                    parameters['ph'] = entry['ph']
                if parameters['kinetic_law_type'] is None and entry.get('kinetic_law_type'):
                    parameters['kinetic_law_type'] = entry['kinetic_law_type']
        
        return parameters
    
    def _parse_model_entry(self, model: ET.Element, ns_key: str) -> Optional[Dict[str, Any]]:
        """Parse a single SBML model entry.
        
        Args:
            model: SBML model element
            ns_key: Namespace key ('sbml' or 'sbml2')
            
        Returns:
            Dictionary of parameters for this entry
        """
        entry = {}
        
        # Find reaction with kinetic law
        reactions = model.findall(f'.//{{{self.SBML_NS[ns_key]}}}reaction')
        
        for reaction in reactions:
            kinetic_law = reaction.find(f'{{{self.SBML_NS[ns_key]}}}kineticLaw')
            if kinetic_law is None:
                continue
            
            # Extract kinetic law type from math
            math_elem = kinetic_law.find('.//{http://www.w3.org/1998/Math/MathML}math')
            if math_elem is not None:
                # Simple heuristic: check for common patterns
                math_str = ET.tostring(math_elem, encoding='unicode')
                if 'michaelis' in math_str.lower() or 'km' in math_str.lower():
                    entry['kinetic_law_type'] = 'michaelis_menten'
                elif 'mass_action' in math_str.lower() or 'k_' in math_str.lower():
                    entry['kinetic_law_type'] = 'mass_action'
            
            # Extract parameters
            params = kinetic_law.findall(f'{{{self.SBML_NS[ns_key]}}}parameter')
            for param in params:
                param_id = param.get('id', '').lower()
                param_value = param.get('value')
                
                if param_value:
                    try:
                        value = float(param_value)
                        
                        # Map parameter IDs to standard names
                        if 'vmax' in param_id or 'v_max' in param_id:
                            entry['vmax'] = value
                        elif 'km' in param_id or 'k_m' in param_id:
                            entry['km'] = value
                        elif 'kcat' in param_id or 'k_cat' in param_id:
                            entry['kcat'] = value
                        elif 'ki' in param_id or 'k_i' in param_id:
                            entry['ki'] = value
                        elif 'k_forward' in param_id or 'kf' in param_id:
                            entry['k_forward'] = value
                        elif 'k_reverse' in param_id or 'kr' in param_id:
                            entry['k_reverse'] = value
                    except ValueError:
                        pass
        
        return entry if entry else None
    
    def is_available(self) -> bool:
        """Check if SABIO-RK is available.
        
        Returns:
            True if service is accessible
        """
        try:
            url = f"{self.base_url}?q=ECNumber:1.1.1.1"
            with urllib.request.urlopen(url, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False
    
    def get_supported_data_types(self) -> List[str]:
        """Get supported data types.
        
        Returns:
            List of data types
        """
        return ["kinetics", "enzyme_parameters", "rate_constants"]
