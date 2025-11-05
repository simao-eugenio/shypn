#!/usr/bin/env python3
"""BioModels Kinetics Fetcher

Fetches kinetic parameters from BioModels database by extracting
kinetic laws from curated SBML models.

BioModels Database: https://www.ebi.ac.uk/biomodels/
- Peer-reviewed, curated models
- Full kinetic laws with parameter values
- SBML Level 2 & 3 support
- Cross-reference with KEGG, UniProt, ChEBI

Author: Shypn Development Team
Date: November 2025
"""

import logging
import xml.etree.ElementTree as ET
import re
import requests
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from urllib.parse import urljoin

from .base_fetcher import BaseFetcher
from ..models.fetch_result import FetchResult, FetchStatus
from ..models import QualityMetrics, SourceAttribution


class BioModelsKineticsFetcher(BaseFetcher):
    """Fetches kinetic parameters from BioModels SBML files.
    
    Features:
    - Download models by BioModels ID
    - Parse SBML kinetic laws (Level 2 & 3)
    - Extract Vmax, Km, Kcat, Ki, rate constants
    - Map reactions to enzymes/EC numbers
    - Store parameters in local database
    
    Attributes:
        base_url: BioModels REST API base URL
        cache_dir: Local cache directory for SBML files
        logger: Logger instance
    """
    
    # BioModels REST API endpoints
    BASE_URL = "https://www.ebi.ac.uk/biomodels/"
    MODEL_DOWNLOAD_URL = BASE_URL + "model/download/"
    SEARCH_URL = BASE_URL + "search"
    
    # SBML namespaces
    SBML_NS = {
        'sbml2': 'http://www.sbml.org/sbml/level2/version4',
        'sbml3': 'http://www.sbml.org/sbml/level3/version1/core',
        'math': 'http://www.w3.org/1998/Math/MathML'
    }
    
    def __init__(self, cache_dir: Optional[str] = None):
        """Initialize BioModels fetcher.
        
        Args:
            cache_dir: Directory for caching SBML files
        """
        super().__init__(source_name='BioModels', source_reliability=0.85)
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Setup cache directory
        if cache_dir:
            self.cache_dir = Path(cache_dir)
        else:
            # Default: ~/.shypn/biomodels_cache/
            import os
            data_home = os.environ.get('XDG_DATA_HOME')
            if data_home:
                base_dir = Path(data_home) / 'shypn'
            else:
                base_dir = Path.home() / '.shypn'
            self.cache_dir = base_dir / 'biomodels_cache'
        
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.logger.info(f"BioModels cache: {self.cache_dir}")
    
    def is_available(self) -> bool:
        """Check if BioModels API is accessible.
        
        Returns:
            True if API responds
        """
        try:
            response = requests.get(self.BASE_URL, timeout=5)
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"BioModels not accessible: {e}")
            return False
    
    def get_supported_data_types(self) -> List[str]:
        """Get list of supported data types.
        
        Returns:
            List of data type strings
        """
        return [
            'kinetic_parameters',
            'enzyme_kinetics',
            'rate_constants',
            'michaelis_menten',
            'mass_action'
        ]
    
    def fetch(self, pathway_id: str = None, data_type: str = 'kinetic_parameters', **kwargs) -> FetchResult:
        """Fetch kinetic parameters from BioModels.
        
        Args:
            pathway_id: Not used (kept for interface compatibility)
            data_type: Type of data to fetch (default: 'kinetic_parameters')
            **kwargs: Additional parameters:
                - model_id: BioModels ID (e.g., 'BIOMD0000000206')
                - ec_number: Optional EC number filter
                - reaction_id: Optional reaction ID filter
                - query: Dict with query parameters (alternative to kwargs)
        
        Returns:
            FetchResult with extracted parameters
        """
        # Support both old query dict and new kwargs style
        if 'query' in kwargs:
            query = kwargs['query']
        else:
            query = kwargs
        
        model_id = query.get('model_id') or kwargs.get('model_id')
        if not model_id:
            return FetchResult(
                data={},
                data_type=data_type,
                status=FetchStatus.FAILED,
                quality_metrics=QualityMetrics(
                    completeness=0.0,
                    source_reliability=0.85,
                    consistency=0.0,
                    validation_status=0.0
                ),
                attribution=SourceAttribution(source_name='BioModels'),
                errors=["No model_id provided"]
            )
        
        try:
            # Download SBML file
            sbml_path = self._download_model(model_id)
            if not sbml_path:
                return FetchResult(
                    data={},
                    data_type=data_type,
                    status=FetchStatus.FAILED,
                    quality_metrics=QualityMetrics(
                        completeness=0.0,
                        source_reliability=0.85,
                        consistency=0.0,
                        validation_status=0.0
                    ),
                    attribution=SourceAttribution(source_name='BioModels'),
                    errors=[f"Failed to download model {model_id}"]
                )
            
            # Parse SBML and extract parameters
            parameters = self._parse_sbml(sbml_path, query)
            
            if not parameters:
                return FetchResult(
                    data={},
                    data_type=data_type,
                    status=FetchStatus.PARTIAL,
                    quality_metrics=QualityMetrics(
                        completeness=0.0,
                        source_reliability=0.85,
                        consistency=1.0,
                        validation_status=0.5
                    ),
                    attribution=SourceAttribution(source_name='BioModels', source_url=f"{self.BASE_URL}{model_id}"),
                    warnings=["No kinetic parameters found in model"]
                )
            
            return FetchResult(
                data={'parameters': parameters},
                data_type=data_type,
                status=FetchStatus.SUCCESS,
                quality_metrics=QualityMetrics(
                    completeness=1.0,
                    source_reliability=0.85,
                    consistency=1.0,
                    validation_status=1.0
                ),
                attribution=SourceAttribution(
                    source_name='BioModels',
                    source_url=f"{self.BASE_URL}{model_id}",
                    database_version='latest'
                ),
                fields_filled=['parameters'],
                query_params={'model_id': model_id}
            )
            
        except Exception as e:
            self.logger.error(f"Error fetching from BioModels: {e}", exc_info=True)
            return FetchResult(
                data={},
                data_type=data_type,
                status=FetchStatus.FAILED,
                quality_metrics=QualityMetrics(
                    completeness=0.0,
                    source_reliability=0.85,
                    consistency=0.0,
                    validation_status=0.0
                ),
                attribution=SourceAttribution(source_name='BioModels'),
                errors=[str(e)]
            )
    
    def _download_model(self, model_id: str) -> Optional[Path]:
        """Download SBML model from BioModels.
        
        Args:
            model_id: BioModels ID (e.g., 'BIOMD0000000206')
        
        Returns:
            Path to downloaded SBML file, or None if failed
        """
        # Check cache first
        cache_file = self.cache_dir / f"{model_id}.xml"
        if cache_file.exists():
            self.logger.info(f"Using cached model: {cache_file}")
            return cache_file
        
        # Download from BioModels
        try:
            url = f"{self.MODEL_DOWNLOAD_URL}{model_id}?filename={model_id}_url.xml"
            self.logger.info(f"Downloading model {model_id} from BioModels...")
            
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Save to cache
            with open(cache_file, 'wb') as f:
                f.write(response.content)
            
            self.logger.info(f"Downloaded and cached: {cache_file}")
            return cache_file
            
        except Exception as e:
            self.logger.error(f"Failed to download model {model_id}: {e}")
            return None
    
    def _parse_sbml(self, sbml_path: Path, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse SBML file and extract kinetic parameters.
        
        Args:
            sbml_path: Path to SBML file
            query: Query dict with optional filters
        
        Returns:
            List of parameter dicts
        """
        try:
            tree = ET.parse(sbml_path)
            root = tree.getroot()
            
            # Detect SBML level
            sbml_level = self._detect_sbml_level(root)
            self.logger.info(f"Parsing SBML Level {sbml_level}")
            
            # Get namespace from root element tag
            ns = root.tag.split('}')[0].strip('{') if '}' in root.tag else self.SBML_NS.get(f'sbml{sbml_level}', self.SBML_NS['sbml3'])
            self.logger.debug(f"Using namespace: {ns}")
            
            # Find model element (direct child of sbml root)
            model = root.find(f'{{{ns}}}model')
            if model is None:
                self.logger.warning("No model element found in SBML")
                return []
            
            # Extract model metadata
            model_metadata = self._extract_model_metadata(root, ns)
            
            # Extract global parameters
            global_parameters = self._extract_global_parameters(model, ns)
            self.logger.info(f"Found {len(global_parameters)} global parameters")
            
            # Extract parameters from reactions
            parameters = []
            
            list_of_reactions = model.find(f'{{{ns}}}listOfReactions')
            if list_of_reactions is None:
                self.logger.warning("No reactions found in model")
                return parameters
            
            for reaction in list_of_reactions.findall(f'{{{ns}}}reaction'):
                reaction_params = self._parse_reaction(reaction, ns, model_metadata, global_parameters, query)
                if reaction_params:
                    parameters.extend(reaction_params)
            
            self.logger.info(f"Extracted {len(parameters)} parameter sets")
            return parameters
            
        except Exception as e:
            self.logger.error(f"Error parsing SBML: {e}", exc_info=True)
            return []
    
    def _detect_sbml_level(self, root: ET.Element) -> int:
        """Detect SBML level from root element.
        
        Args:
            root: XML root element
        
        Returns:
            SBML level (2 or 3)
        """
        # Check namespace in tag
        tag = root.tag
        if 'level2' in tag:
            return 2
        elif 'level3' in tag:
            return 3
        
        # Check level attribute
        level = root.get('level')
        if level:
            try:
                return int(level)
            except ValueError:
                pass
        
        # Default to 3
        self.logger.warning("Could not detect SBML level, defaulting to 3")
        return 3
    
    def _extract_model_metadata(self, root: ET.Element, ns: str) -> Dict[str, Any]:
        """Extract model-level metadata.
        
        Args:
            root: XML root element (sbml element)
            ns: SBML namespace
        
        Returns:
            Metadata dict
        """
        metadata = {
            'organism': 'unknown',
            'model_name': 'unknown',
            'temperature': None,
            'ph': None
        }
        
        model = root.find(f'{{{ns}}}model')
        if model is not None:
            metadata['model_name'] = model.get('name', 'unknown')
            
            # Try to extract organism from notes
            # (BioModels often includes this in annotations)
            notes = model.find(f'{{{ns}}}notes')
            if notes is not None:
                notes_text = ET.tostring(notes, encoding='unicode', method='text')
                
                # Common organism patterns
                if 'Homo sapiens' in notes_text or 'human' in notes_text.lower():
                    metadata['organism'] = 'Homo sapiens'
                elif 'Saccharomyces cerevisiae' in notes_text or 'yeast' in notes_text.lower():
                    metadata['organism'] = 'Saccharomyces cerevisiae'
                elif 'Escherichia coli' in notes_text or 'E. coli' in notes_text:
                    metadata['organism'] = 'Escherichia coli'
        
        return metadata
    
    def _extract_global_parameters(self, model: ET.Element, ns: str) -> Dict[str, float]:
        """Extract global parameter definitions from model.
        
        Args:
            model: SBML model element
            ns: SBML namespace
        
        Returns:
            Dict mapping parameter IDs to their values
        """
        params = {}
        
        list_of_params = model.find(f'{{{ns}}}listOfParameters')
        if list_of_params is not None:
            for param in list_of_params.findall(f'{{{ns}}}parameter'):
                param_id = param.get('id')
                param_value = param.get('value')
                
                if param_id and param_value:
                    try:
                        params[param_id.lower()] = float(param_value)
                    except ValueError:
                        pass
        
        return params
    
    def _parse_reaction(self, 
                       reaction: ET.Element, 
                       ns: str,
                       model_metadata: Dict[str, Any],
                       global_parameters: Dict[str, float],
                       query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Parse a single reaction and extract kinetic parameters.
        
        Args:
            reaction: Reaction XML element
            ns: SBML namespace
            model_metadata: Model-level metadata
            global_parameters: Global parameter definitions
            query: Query dict with filters
        
        Returns:
            List of parameter dicts (can be multiple per reaction)
        """
        parameters = []
        
        # Get reaction ID and name
        reaction_id = reaction.get('id', 'unknown')
        reaction_name = reaction.get('name', reaction_id)
        
        # Check if reaction matches filters
        if 'reaction_id' in query and query['reaction_id'] not in reaction_id:
            return parameters
        
        # Find kinetic law
        kinetic_law = reaction.find(f'{{{ns}}}kineticLaw')
        if kinetic_law is None:
            return parameters
        
        # Extract parameters from kinetic law (local) and merge with global
        param_dict = self._extract_parameters_from_kinetic_law(kinetic_law, ns, global_parameters)
        
        if not param_dict:
            return parameters
        
        # Try to identify enzyme/EC number from annotations
        ec_number = self._extract_ec_number(reaction, ns)
        enzyme_name = self._extract_enzyme_name(reaction, ns)
        
        # Check EC number filter
        if 'ec_number' in query and query['ec_number']:
            if not ec_number or query['ec_number'] not in ec_number:
                return parameters
        
        # Classify parameter type based on what we found
        # This is heuristic - we identify Michaelis-Menten, mass action, etc.
        param_sets = self._classify_kinetic_law(param_dict, reaction_name)
        
        for param_set in param_sets:
            param_set.update({
                'reaction_id': reaction_id,
                'reaction_name': reaction_name,
                'ec_number': ec_number,
                'enzyme_name': enzyme_name or reaction_name,
                'organism': model_metadata['organism'],
                'temperature': model_metadata.get('temperature'),
                'ph': model_metadata.get('ph'),
                'source': 'BioModels',
                'confidence_score': 0.85  # BioModels are peer-reviewed
            })
            
            parameters.append(param_set)
        
        return parameters
    
    def _extract_parameters_from_kinetic_law(self, 
                                            kinetic_law: ET.Element,
                                            ns: str,
                                            global_parameters: Dict[str, float]) -> Dict[str, float]:
        """Extract parameter values from kinetic law and merge with global parameters.
        
        Args:
            kinetic_law: KineticLaw XML element
            ns: SBML namespace
            global_parameters: Global parameter definitions from model
        
        Returns:
            Dict mapping parameter names to values
        """
        # Start with global parameters (will be overridden by local if present)
        params = global_parameters.copy()
        
        # Find listOfParameters (local parameters in kinetic law)
        list_of_params = kinetic_law.find(f'{{{ns}}}listOfParameters')
        if list_of_params is None:
            list_of_params = kinetic_law.find(f'{{{ns}}}listOfLocalParameters')
        
        if list_of_params is not None:
            for param in list_of_params.findall(f'{{{ns}}}parameter') + \
                        list_of_params.findall(f'{{{ns}}}localParameter'):
                name = param.get('id') or param.get('name')
                value = param.get('value')
                
                if name and value:
                    try:
                        params[name.lower()] = float(value)
                    except ValueError:
                        pass
        
        return params
    
    def _classify_kinetic_law(self, 
                             param_dict: Dict[str, float],
                             reaction_name: str) -> List[Dict[str, Any]]:
        """Classify kinetic law type and structure parameters.
        
        Args:
            param_dict: Raw parameter dict from SBML
            reaction_name: Reaction name for context
        
        Returns:
            List of structured parameter dicts
        """
        param_sets = []
        
        # Common parameter name patterns
        vmax_patterns = ['vmax', 'v_max', 'vm', 'kcat']
        km_patterns = ['km', 'k_m', 'michaelis', 'ks']
        kcat_patterns = ['kcat', 'k_cat', 'turnover']
        ki_patterns = ['ki', 'k_i', 'inhibition']
        k_forward_patterns = ['k1', 'kf', 'k_f', 'forward', 'kon']
        k_reverse_patterns = ['k2', 'kr', 'k_r', 'reverse', 'koff']
        
        def find_param(patterns: List[str]) -> Optional[float]:
            """Find parameter matching patterns."""
            for key, value in param_dict.items():
                if any(pattern in key for pattern in patterns):
                    return value
            return None
        
        # Try to identify Michaelis-Menten parameters
        vmax = find_param(vmax_patterns)
        km = find_param(km_patterns)
        kcat = find_param(kcat_patterns)
        ki = find_param(ki_patterns)
        
        if vmax or km or kcat:
            # Looks like enzyme kinetics (continuous transition)
            param_sets.append({
                'transition_type': 'continuous',
                'biological_semantics': 'enzyme_kinetics',
                'parameters': {
                    'vmax': vmax or (kcat * 100 if kcat else 100.0),  # Estimate if missing
                    'km': km or 0.1,  # Default if missing
                    'kcat': kcat,
                    'ki': ki
                }
            })
        
        # Try to identify mass action rate constants
        k_forward = find_param(k_forward_patterns)
        k_reverse = find_param(k_reverse_patterns)
        
        if k_forward or k_reverse:
            # Looks like mass action (stochastic transition)
            param_sets.append({
                'transition_type': 'stochastic',
                'biological_semantics': 'mass_action',
                'parameters': {
                    'lambda': k_forward or 0.05,
                    'k_forward': k_forward,
                    'k_reverse': k_reverse
                }
            })
        
        # If nothing matched, return raw parameters
        if not param_sets and param_dict:
            # Generic continuous (we have some numbers)
            param_sets.append({
                'transition_type': 'continuous',
                'biological_semantics': 'enzyme_kinetics',
                'parameters': {
                    'vmax': list(param_dict.values())[0] if param_dict else 100.0,
                    'km': 0.1
                },
                'notes': f"Generic parameters from {reaction_name}: {param_dict}"
            })
        
        return param_sets
    
    def _extract_ec_number(self, reaction: ET.Element, ns: str) -> Optional[str]:
        """Extract EC number from reaction annotations.
        
        Args:
            reaction: Reaction XML element
            ns: SBML namespace
        
        Returns:
            EC number string or None
        """
        # Check in annotation
        annotation = reaction.find(f'{{{ns}}}annotation')
        if annotation is not None:
            # Convert to string and search for EC number pattern
            annotation_str = ET.tostring(annotation, encoding='unicode')
            
            # EC number pattern: EC X.X.X.X or ec-code/X.X.X.X
            ec_match = re.search(r'EC[:\s]?(\d+\.\d+\.\d+\.\d+)', annotation_str, re.IGNORECASE)
            if ec_match:
                return ec_match.group(1)
            
            ec_match = re.search(r'ec-code/(\d+\.\d+\.\d+\.\d+)', annotation_str)
            if ec_match:
                return ec_match.group(1)
        
        # Check in notes
        notes = reaction.find(f'{{{ns}}}notes')
        if notes is not None:
            notes_str = ET.tostring(notes, encoding='unicode', method='text')
            ec_match = re.search(r'EC[:\s]?(\d+\.\d+\.\d+\.\d+)', notes_str, re.IGNORECASE)
            if ec_match:
                return ec_match.group(1)
        
        return None
    
    def _extract_enzyme_name(self, reaction: ET.Element, ns: str) -> Optional[str]:
        """Extract enzyme name from reaction.
        
        Args:
            reaction: Reaction XML element
            ns: SBML namespace
        
        Returns:
            Enzyme name or None
        """
        # Try reaction name first
        name = reaction.get('name')
        if name and len(name) > 3:  # Avoid short IDs
            return name
        
        # Try notes
        notes = reaction.find(f'{{{ns}}}notes')
        if notes is not None:
            notes_str = ET.tostring(notes, encoding='unicode', method='text')
            # Simple heuristic: find enzyme names (usually capitalized words)
            enzyme_match = re.search(r'([A-Z][a-z]+(?:\s+[a-z]+)?ase)', notes_str)
            if enzyme_match:
                return enzyme_match.group(1)
        
        return None
    
    def search_models(self, 
                     organism: Optional[str] = None,
                     pathway: Optional[str] = None,
                     limit: int = 10) -> List[str]:
        """Search BioModels for relevant models.
        
        Args:
            organism: Organism name (e.g., 'Homo sapiens')
            pathway: Pathway name (e.g., 'glycolysis')
            limit: Maximum number of results
        
        Returns:
            List of BioModels IDs
        """
        # For now, return well-known models
        # TODO: Implement REST API search
        
        known_models = {
            'glycolysis': ['BIOMD0000000206'],  # Yeast glycolysis
            'mapk': ['BIOMD0000000010'],        # MAPK cascade
            'cell_cycle': ['BIOMD0000000005'],  # Cell cycle
        }
        
        if pathway and pathway.lower() in known_models:
            return known_models[pathway.lower()]
        
        # Default: return some popular models
        return ['BIOMD0000000206', 'BIOMD0000000010', 'BIOMD0000000005']
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get fetcher statistics.
        
        Returns:
            Statistics dict
        """
        # Count cached models
        cached_models = len(list(self.cache_dir.glob('*.xml'))) if self.cache_dir.exists() else 0
        
        return {
            'cached_models': cached_models,
            'cache_dir': str(self.cache_dir),
            'api_available': self.is_available()
        }
