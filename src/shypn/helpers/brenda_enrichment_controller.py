#!/usr/bin/env python3
"""BRENDA Enrichment Controller.

This controller manages the BRENDA enrichment workflow:
1. Scan canvas for transitions (enzymes)
2. Query BRENDA API or load from local file
3. Match BRENDA data to transitions
4. Generate enrichment report
5. Apply selected enrichments
6. Track enrichment metadata in project

The controller integrates with the project system to track:
- What enrichments were applied
- Which transitions were enriched
- What parameters were added
- Source citations and confidence
"""

import os
import json
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from ..data.enrichment_document import EnrichmentDocument
from ..data.project_models import Project
from ..data.kegg_ec_fetcher import KEGGECFetcher

# Import BRENDA API client
try:
    from ..data.brenda_soap_client import BRENDAAPIClient, ZEEP_AVAILABLE
except ImportError:
    BRENDAAPIClient = None
    ZEEP_AVAILABLE = False


class BRENDAEnrichmentController:
    """Controller for BRENDA enrichment workflow with project integration.
    
    This controller handles the complete BRENDA enrichment lifecycle:
    - Canvas scanning to find transitions
    - BRENDA API queries (when credentials available)
    - Local BRENDA file loading
    - Enrichment application to transitions
    - Project metadata tracking
    
    Attributes:
        project: Current project (for metadata tracking)
        model_canvas: Canvas widget (for transition access)
        current_enrichment: Current EnrichmentDocument being built
    """
    
    def __init__(self, model_canvas=None, project=None):
        """Initialize BRENDA enrichment controller.
        
        Args:
            model_canvas: Canvas widget for accessing transitions
            project: Current project for metadata tracking
        """
        self.model_canvas = model_canvas
        self.project = project
        self.current_enrichment = None
        self.kegg_ec_fetcher = KEGGECFetcher()  # For fetching EC numbers from KEGG reaction IDs
        
        # Initialize BRENDA API client (will be authenticated when user provides credentials)
        self.brenda_api = None
        if BRENDAAPIClient:
            self.brenda_api = BRENDAAPIClient()
    
    def set_project(self, project: Optional[Project]):
        """Set or update the current project.
        
        Args:
            project: Project instance or None
        """
        self.project = project
    
    def set_model_canvas(self, model_canvas):
        """Set or update the model canvas.
        
        Args:
            model_canvas: Canvas widget
        """
        self.model_canvas = model_canvas
    
    # ========================================================================
    # Canvas Scanning
    # ========================================================================
    
    def scan_canvas_transitions(self) -> List[Dict[str, Any]]:
        """Scan canvas for all transitions (potential enzymes).
        
        Extracts information about each transition that could be enriched:
        - Transition ID
        - Transition name
        - Existing EC number (if any)
        - Existing kinetic parameters
        
        Returns:
            List of transition dictionaries with structure:
            {
                'id': str,
                'name': str,
                'ec_number': str or None,
                'has_kinetics': bool,
                'parameters': Dict[str, float]
            }
        """
        if not self.model_canvas:
            return []
        
        if hasattr(self.model_canvas, 'transitions'):
            pass
        
        # Debug: list all attributes
        
        transitions = []
        
        # Access transitions from ModelCanvasManager
        if hasattr(self.model_canvas, 'transitions'):
            pass
            
            for transition in self.model_canvas.transitions:
                if not transition:
                    continue
                
                # Extract transition info
                transition_info = {
                    'id': transition.id if hasattr(transition, 'id') else None,
                    'name': transition.name if hasattr(transition, 'name') else 'Unknown',
                    'ec_number': None,
                    'has_kinetics': False,
                    'data_source': 'unknown',
                    'parameters': {},
                    'transition_obj': transition  # Keep reference for updates
                }
                
                # Get EC number and data source from metadata
                if hasattr(transition, 'metadata') and transition.metadata:
                    pass
                    # Extract data source
                    transition_info['data_source'] = transition.metadata.get('data_source', 'unknown')
                    ec_val = transition.metadata.get('ec_number',
                             transition.metadata.get('ec_numbers', []))
                    
                    
                    if isinstance(ec_val, list) and len(ec_val) > 0:
                        transition_info['ec_number'] = ec_val[0]
                    elif ec_val and ec_val != '-':
                        transition_info['ec_number'] = str(ec_val)
                    else:
                    
                    # Check for existing kinetic data
                    has_km = 'km' in transition.metadata or 'Km' in transition.metadata
                    has_kcat = 'kcat' in transition.metadata or 'Kcat' in transition.metadata
                    has_vmax = 'vmax' in transition.metadata or 'Vmax' in transition.metadata
                    
                    # Also check kinetic_parameters dict (for SBML imports)
                    kinetic_params = transition.metadata.get('kinetic_parameters', {})
                    if kinetic_params and isinstance(kinetic_params, dict):
                        has_km = has_km or 'km' in kinetic_params or 'Km' in kinetic_params
                        has_kcat = has_kcat or 'kcat' in kinetic_params or 'Kcat' in kinetic_params
                        has_vmax = has_vmax or 'vmax' in kinetic_params or 'Vmax' in kinetic_params
                    
                    transition_info['has_kinetics'] = has_km or has_kcat or has_vmax
                    
                    # Extract existing parameters
                    if has_km:
                        transition_info['parameters']['km'] = transition.metadata.get('km', transition.metadata.get('Km'))
                    if has_kcat:
                        transition_info['parameters']['kcat'] = transition.metadata.get('kcat', transition.metadata.get('Kcat'))
                    if has_vmax:
                        transition_info['parameters']['vmax'] = transition.metadata.get('vmax', transition.metadata.get('Vmax'))
                
                # If no EC number found in metadata, try to extract from KEGG reaction ID
                if not transition_info['ec_number']:
                    pass
                    # Check if transition has a label with KEGG reaction ID (e.g., "R00710")
                    label = getattr(transition, 'label', None) or transition_info['name']
                    if label and re.match(r'^R\d{5}$', label):
                        pass
                        # This is a KEGG reaction ID - fetch EC numbers from KEGG API
                        try:
                            ec_numbers = self.kegg_ec_fetcher.fetch_ec_numbers(label)
                            if ec_numbers:
                                transition_info['ec_number'] = ec_numbers[0]
                                transition_info['data_source'] = 'kegg_import'
                                
                                # Also store in transition metadata for future use
                                if not hasattr(transition, 'metadata'):
                                    transition.metadata = {}
                                if not transition.metadata:
                                    transition.metadata = {}
                                transition.metadata['ec_numbers'] = ec_numbers
                                transition.metadata['ec_number'] = ec_numbers[0]
                            else:
                        except Exception as e:
                
                transitions.append(transition_info)
        
        return transitions
    
    # ========================================================================
    # BRENDA API Integration
    # ========================================================================
    
    def authenticate_brenda(self, email: str, password: str) -> bool:
        """Authenticate with BRENDA API.
        
        Args:
            email: BRENDA account email
            password: BRENDA account password
        
        Returns:
            True if authentication successful, False otherwise
        """
        if not self.brenda_api:
            return False
        
        success = self.brenda_api.authenticate(email, password)
        
        if success:
        else:
        
        return success
    
    def is_brenda_authenticated(self) -> bool:
        """Check if BRENDA API is authenticated."""
        return self.brenda_api and self.brenda_api.is_authenticated()
    
    def fetch_from_brenda_api(self, ec_number: str, organism: str = None) -> Optional[Dict[str, Any]]:
        """Fetch kinetic data from BRENDA API.
        
        Args:
            ec_number: EC number to query (e.g., "2.7.1.1")
            organism: Optional organism filter (e.g., "Homo sapiens")
        
        Returns:
            Dict with BRENDA data or None if not available:
            {
                'ec_number': str,
                'enzyme_name': str,
                'organism': str,
                'km_values': List[Dict],
                'kcat_values': List[Dict],
                'ki_values': List[Dict],
                'citations': List[str]
            }
        """
        if not self.brenda_api:
            return None
        
        if not self.brenda_api.is_authenticated():
            return None
        
        
        try:
            pass
            # Query Km values
            km_values = self.brenda_api.get_km_values(ec_number, organism)
            
            # Query kcat (turnover number) values
            kcat_values = self.brenda_api.get_kcat_values(ec_number, organism)
            
            # Query Ki (inhibition constant) values
            ki_values = self.brenda_api.get_ki_values(ec_number, organism)
            
            # If we got any data, package it
            if km_values or kcat_values or ki_values:
                result = {
                    'ec_number': ec_number,
                    'organism': organism or 'all',
                    'km_values': km_values,
                    'kcat_values': kcat_values,
                    'ki_values': ki_values,
                }
                
                      f"{len(km_values)} Km, {len(kcat_values)} kcat, {len(ki_values)} Ki values")
                
                return result
            else:
                return None
        
        except Exception as e:
            return None
    
    # ========================================================================
    # Local File Loading
    # ========================================================================
    
    def load_from_local_file(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Load BRENDA data from local CSV or JSON file.
        
        Supports two formats:
        - CSV: BRENDA export format (columns: EC, Name, Organism, Km, Kcat, etc.)
        - JSON: Structured BRENDA data
        
        Args:
            file_path: Path to BRENDA data file
        
        Returns:
            Dict with parsed BRENDA data or None on error
        """
        if not os.path.exists(file_path):
            return None
        
        try:
            if file_path.endswith('.json'):
                with open(file_path, 'r') as f:
                    data = json.load(f)
                return data
            elif file_path.endswith('.csv'):
                pass
                # TODO: Implement CSV parsing
                return None
            else:
                return None
        except Exception as e:
            return None
    
    # ========================================================================
    # Enrichment Application
    # ========================================================================
    
    def start_enrichment(self, source: str = "brenda_api", query_params: Dict[str, Any] = None):
        """Start a new enrichment session.
        
        Creates an EnrichmentDocument to track this enrichment.
        
        Args:
            source: Source type ("brenda_api" or "brenda_local")
            query_params: Query parameters used (EC number, organism, etc.)
        """
        self.current_enrichment = EnrichmentDocument(
            type="kinetics",
            source=source
        )
        
        if query_params:
            self.current_enrichment.source_query = query_params
        
    
    def apply_enrichment_to_transition(self, transition_id: str, parameters: Dict[str, Any],
                                       transition_obj=None):
        """Apply BRENDA enrichment data to a specific transition.
        
        Args:
            transition_id: ID of transition to enrich
            parameters: Dict of parameters to add (km, kcat, ki, etc.)
            transition_obj: Optional transition object (for direct update)
        """
        if not self.current_enrichment:
            return
        
        # Track transition enrichment
        self.current_enrichment.add_transition(transition_id)
        
        # Track parameters added
        for param_type, value in parameters.items():
            self.current_enrichment.add_parameter(param_type)
        
        # Apply parameters to transition object
        if transition_obj and hasattr(transition_obj, 'metadata'):
            if not transition_obj.metadata:
                transition_obj.metadata = {}
            
            # Check if we should override existing parameters
            override_mode = parameters.get('_override_rate_function', False)
            
            
            # Add/update kinetic parameters with source tracking
            for param_name, param_value in parameters.items():
                pass
                # Skip internal flags
                if param_name.startswith('_'):
                    continue
                
                param_exists = param_name in transition_obj.metadata
                
                if not param_exists:
                    pass
                    # New parameter - always add
                    transition_obj.metadata[param_name] = param_value
                    transition_obj.metadata[f'{param_name}_source'] = 'brenda_enriched'
                elif override_mode:
                    pass
                    # Parameter exists but override is enabled - replace it
                    old_value = transition_obj.metadata[param_name]
                    transition_obj.metadata[param_name] = param_value
                    transition_obj.metadata[f'{param_name}_source'] = 'brenda_enriched'
                else:
                    pass
                    # Parameter exists and override disabled - skip
            
            # Mark that enrichment occurred (don't overwrite original data_source)
            # Original data_source stays as 'kegg_import' or 'sbml_import'
            if 'enrichment_source' not in transition_obj.metadata:
                transition_obj.metadata['enrichment_source'] = 'brenda'
            
            
            # Auto-generate Michaelis-Menten rate function from parameters
            try:
                # Check if we should override existing rate functions
                override = parameters.get('_override_rate_function', False)
                self._generate_rate_function_from_parameters(transition_obj, parameters, override=override)
            except Exception as e:
                pass
                import traceback
                traceback.print_exc()

    
    def _generate_rate_function_from_parameters(self, transition, parameters: Dict[str, Any], override: bool = False):
        """Generate Michaelis-Menten rate function from BRENDA parameters.
        
        Creates rate_function string for continuous simulation:
        - Basic: michaelis_menten(substrate, vmax, km)
        - With inhibitor: michaelis_menten(substrate, vmax, km*(1 + inhibitor/ki))
        
        Args:
            transition: Transition object to update
            parameters: Dict with km, kcat, vmax, ki values
            override: If True, overwrite existing rate functions (use for BRENDA-enriched models)
        """
        print(f"\n[BRENDA_MM] ========== RATE FUNCTION GENERATOR CALLED ==========")
        
        if transition is None:
            return
        
        # Check if already has rate_function
        if hasattr(transition, 'properties') and transition.properties:
            if 'rate_function' in transition.properties:
                existing_func = transition.properties['rate_function']
                
                if not override:
                    return
                else:

        
        # Need at least Vmax (or Kcat) and Km
        vmax = parameters.get('vmax')
        km = parameters.get('km')
        ki = parameters.get('ki')
        kcat = parameters.get('kcat')
        
        if not km:
            return
        
        # Calculate Vmax if only kcat provided
        if not vmax and kcat:
            pass
            # Vmax = kcat * [E]total
            # For now, use kcat directly (assumes [E]=1 or normalized)
            vmax = kcat
        
        # If no Vmax/Kcat provided, try to preserve existing Vmax from transition
        if not vmax:
            pass
            # Check if transition already has Vmax in metadata or properties
            existing_vmax = None
            
            if hasattr(transition, 'metadata') and transition.metadata:
                existing_vmax = transition.metadata.get('vmax') or transition.metadata.get('Vmax')
            
            if not existing_vmax and hasattr(transition, 'properties') and transition.properties:
                pass
                # Try to parse existing rate_function for Vmax value
                existing_func = transition.properties.get('rate_function', '')
                if 'vmax=' in existing_func:
                    import re
                    match = re.search(r'vmax=(\d+(?:\.\d+)?)', existing_func)
                    if match:
                        existing_vmax = float(match.group(1))
            
            if existing_vmax:
                vmax = existing_vmax
            else:
                return
        
        # Find substrate place (first input place)
        substrate_place = None
        inhibitor_place = None
        
        # Try to get input places from model canvas arcs
        if self.model_canvas and hasattr(self.model_canvas, 'arcs'):
            input_places = []
            for arc in self.model_canvas.arcs:
                pass
                # Check if arc points to this transition (Place → Transition)
                if hasattr(arc, 'target') and hasattr(arc.target, 'id'):
                    if str(arc.target.id) == str(transition.id):
                        pass
                        # This arc feeds into our transition
                        if hasattr(arc, 'source') and hasattr(arc.source, 'label'):
                            place_name = arc.source.label if arc.source.label else arc.source.name
                            input_places.append(place_name)
            
            if len(input_places) > 0:
                substrate_place = input_places[0]
                
                if len(input_places) > 1 and ki and ki > 0:
                    inhibitor_place = input_places[1]
        
        # Fallback if no input places found
        if not substrate_place:
            if hasattr(transition, 'id'):
                substrate_place = f"P{transition.id}"
            else:
                substrate_place = "substrate"
        
        # Build rate function with NAMED PARAMETERS (self-documenting)
        if ki and ki > 0 and inhibitor_place:
            pass
            # Competitive inhibition form with actual inhibitor place
            # v = (Vmax * [S]) / (Km * (1 + [I]/Ki) + [S])
            # Expanded: michaelis_menten(S, Vmax, Km * (1 + I/Ki))
            rate_function = f"michaelis_menten({substrate_place}, vmax={vmax}, km={km} * (1 + {inhibitor_place} / {ki}))"
        elif ki and ki > 0:
            pass
            # Ki available but no inhibitor place detected
            rate_function = f"michaelis_menten({substrate_place}, vmax={vmax}, km={km})"
        else:
            pass
            # Simple Michaelis-Menten with named parameters
            rate_function = f"michaelis_menten({substrate_place}, vmax={vmax}, km={km})"
        
        # Set rate function in transition properties
        if not hasattr(transition, 'properties'):
            transition.properties = {}
        
        transition.properties['rate_function'] = rate_function
        transition.properties['rate_function_source'] = 'brenda_auto_generated'
        
        # Ensure transition is continuous (needed for rate functions)
        if not hasattr(transition, 'transition_type') or transition.transition_type != 'continuous':
            transition.transition_type = 'continuous'
        
        
        # VERIFICATION: Read back the values to confirm they were set
        verify_func = transition.properties.get('rate_function')
        verify_type = getattr(transition, 'transition_type', 'unknown')
        
        if verify_func == rate_function:
        else:
        
        if verify_type == 'continuous':
        else:
        
    
    def add_citations(self, citations: List[str]):
        """Add citations to current enrichment.
        
        Args:
            citations: List of citation IDs (e.g., "PMID:12345678")
        """
        if not self.current_enrichment:
            return
        
        for citation in citations:
            self.current_enrichment.add_citation(citation)
    
    def set_confidence(self, confidence: str):
        """Set confidence level for current enrichment.
        
        Args:
            confidence: "high", "medium", or "low"
        """
        if self.current_enrichment:
            self.current_enrichment.set_confidence(confidence)
    
    # ========================================================================
    # Project Integration
    # ========================================================================
    
    def save_enrichment_to_project(self, brenda_data: Dict[str, Any] = None) -> bool:
        """Save enrichment metadata to project.
        
        This method:
        1. Saves BRENDA data to project/enrichments/ directory
        2. Updates EnrichmentDocument with file path
        3. Links enrichment to the current pathway (if any)
        4. Saves project metadata
        
        Args:
            brenda_data: Optional BRENDA data to save as JSON
        
        Returns:
            True if successful, False otherwise
        """
        if not self.project:
            return False
        
        if not self.current_enrichment:
            return False
        
        try:
            pass
            # 1. Save BRENDA data file if provided
            if brenda_data:
                enrichments_dir = self.project.get_enrichments_dir()
                if enrichments_dir:
                    os.makedirs(enrichments_dir, exist_ok=True)
                    
                    # Generate filename
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    filename = f"brenda_enrichment_{timestamp}.json"
                    file_path = os.path.join(enrichments_dir, filename)
                    
                    # Save data
                    with open(file_path, 'w') as f:
                        json.dump(brenda_data, f, indent=2)
                    
                    # Update enrichment document
                    self.current_enrichment.data_file = filename
            
            # 2. Find current pathway (if model is linked to pathway)
            current_pathway = self._find_current_pathway()
            
            # 3. Register enrichment with project
            if current_pathway:
                pass
                # Link enrichment to pathway
                current_pathway.enrichments.append(self.current_enrichment.id)
            
            # 4. Add enrichment to project's enrichments collection
            # (This would need a new method on Project class)
            # For now, we store it in the pathway's enrichments list
            
            # 5. Save project
            self.project.save()
            
            return True
            
        except Exception as e:
            import traceback
            traceback.print_exc()
            return False
    
    def _find_current_pathway(self) -> Optional[Any]:
        """Find the pathway document for the current model.
        
        This searches the project's pathways for one that links to the
        current model on the canvas.
        
        Returns:
            PathwayDocument if found, None otherwise
        """
        if not self.project or not self.model_canvas:
            return None
        
        # TODO: Get current model ID from canvas
        # For now, return the most recently added pathway
        # This is a simplification - proper implementation needs canvas integration
        
        pathways = self.project.pathways.list_pathways()
        if pathways:
            pass
            # Return most recent pathway with a model
            for pathway in reversed(pathways):
                if pathway.model_id:
                    return pathway
        
        return None
    
    def finish_enrichment(self) -> Optional[EnrichmentDocument]:
        """Finish the current enrichment session.
        
        Returns:
            Completed EnrichmentDocument or None if no session active
        """
        if not self.current_enrichment:
            return None
        
        enrichment = self.current_enrichment
        self.current_enrichment = None
        
              f"{enrichment.get_transition_count()} transitions, "
              f"{enrichment.get_total_parameters()} parameters, "
              f"{enrichment.get_citation_count()} citations")
        
        return enrichment
    
    # ========================================================================
    # High-Level Workflow Methods
    # ========================================================================
    
    def enrich_canvas_from_api(self, ec_numbers: List[str], organism: str = None,
                                override_existing: bool = False) -> Dict[str, Any]:
        """Complete workflow: enrich canvas from BRENDA API.
        
        Args:
            ec_numbers: List of EC numbers to query
            organism: Optional organism filter
            override_existing: Whether to override existing parameters
        
        Returns:
            Summary dict with results
        """
        # Start enrichment session
        self.start_enrichment(
            source="brenda_api",
            query_params={
                'ec_numbers': ec_numbers,
                'organism': organism,
                'override': override_existing
            }
        )
        
        # Scan canvas
        transitions = self.scan_canvas_transitions()
        
        
        # Query BRENDA for each EC number (with mock data for now)
        brenda_data = {}
        for ec_number in ec_numbers:
            data = self.fetch_from_brenda_api(ec_number, organism)
            if data:
                brenda_data[ec_number] = data
            else:
        
        
        # Match and apply enrichments
        enriched_count = 0
        skipped_count = 0
        for transition in transitions:
            ec = transition.get('ec_number')
            trans_id = transition.get('id')
            has_kin = transition.get('has_kinetics')
            data_source = transition.get('data_source', 'unknown')
            
            
            if ec in brenda_data:
                pass
                # Determine if we should enrich based on override mode and data source
                should_enrich = False
                
                if not has_kin:
                    pass
                    # No kinetics at all - always enrich
                    should_enrich = True
                elif data_source == 'kegg_import':
                    pass
                    # KEGG import - always override (all kinetics are heuristics)
                    should_enrich = True
                elif override_existing:
                    pass
                    # User explicitly requested override for all sources
                    should_enrich = True
                else:
                    pass
                    # Has kinetics from curated source (SBML/BioPAX) and override disabled
                    should_enrich = False
                
                if should_enrich:
                    pass
                    # Apply enrichment
                    params = self._extract_parameters(brenda_data[ec])
                    # Add override flag for rate function regeneration
                    params['_override_rate_function'] = True  # Always regenerate rate functions when enriching
                    self.apply_enrichment_to_transition(
                        transition['id'], 
                        params,
                        transition_obj=transition.get('transition_obj')
                    )
                    enriched_count += 1
                else:
                    skipped_count += 1
            else:
                if ec:
                else:
        
        
        # Save to project
        self.save_enrichment_to_project(brenda_data)
        
        # Finish session
        enrichment = self.finish_enrichment()
        
        return {
            'success': True,
            'transitions_scanned': len(transitions),
            'transitions_enriched': enriched_count,
            'enrichment_id': enrichment.id if enrichment else None
        }
    
    def enrich_canvas_from_file(self, file_path: str, override_existing: bool = False) -> Dict[str, Any]:
        """Complete workflow: enrich canvas from local BRENDA file.
        
        Args:
            file_path: Path to BRENDA data file
            override_existing: Whether to override existing parameters
        
        Returns:
            Summary dict with results
        """
        # Load data
        brenda_data = self.load_from_local_file(file_path)
        if not brenda_data:
            return {'success': False, 'error': 'Failed to load file'}
        
        # Start enrichment session
        self.start_enrichment(
            source="brenda_local",
            query_params={'file': os.path.basename(file_path)}
        )
        
        # Scan canvas
        transitions = self.scan_canvas_transitions()
        
        # Match and apply enrichments
        enriched_count = 0
        for transition in transitions:
            ec = transition.get('ec_number')
            has_kin = transition.get('has_kinetics')
            data_source = transition.get('data_source', 'unknown')
            trans_id = transition.get('id')
            
            if ec and ec in brenda_data:
                pass
                # Determine if we should enrich based on override mode and data source
                should_enrich = False
                
                if not has_kin:
                    pass
                    # No kinetics at all - always enrich
                    should_enrich = True
                elif data_source == 'kegg_import':
                    pass
                    # KEGG import - always override (all kinetics are heuristics)
                    should_enrich = True
                elif override_existing:
                    pass
                    # User explicitly requested override for all sources
                    should_enrich = True
                else:
                    pass
                    # Has kinetics from curated source and override disabled
                    should_enrich = False
                
                if should_enrich:
                    pass
                    # Apply enrichment
                    params = self._extract_parameters(brenda_data[ec])
                    # Add override flag for rate function regeneration
                    params['_override_rate_function'] = True  # Always regenerate when enriching
                    self.apply_enrichment_to_transition(
                        transition['id'], 
                        params,
                        transition_obj=transition.get('transition_obj')
                    )
                    enriched_count += 1
        
        # Save to project
        self.save_enrichment_to_project(brenda_data)
        
        # Finish session
        enrichment = self.finish_enrichment()
        
        return {
            'success': True,
            'transitions_scanned': len(transitions),
            'transitions_enriched': enriched_count,
            'enrichment_id': enrichment.id if enrichment else None
        }
    
    def _extract_parameters(self, brenda_entry: Dict[str, Any]) -> Dict[str, float]:
        """Extract kinetic parameters from BRENDA data entry.
        
        Args:
            brenda_entry: BRENDA data for one EC number
        
        Returns:
            Dict of parameter name -> value (km, kcat, vmax, ki)
        """
        params = {}
        
        # Extract Km values (take first/best)
        km_values = brenda_entry.get('km_values', [])
        if km_values and isinstance(km_values, list) and len(km_values) > 0:
            params['km'] = km_values[0].get('value', 0.0)
        
        # Extract kcat values
        kcat_values = brenda_entry.get('kcat_values', [])
        if kcat_values and isinstance(kcat_values, list) and len(kcat_values) > 0:
            params['kcat'] = kcat_values[0].get('value', 0.0)
        
        # Extract Ki values (inhibition constants)
        ki_values = brenda_entry.get('ki_values', [])
        if ki_values and isinstance(ki_values, list) and len(ki_values) > 0:
            params['ki'] = ki_values[0].get('value', 0.0)
        
        # Extract or calculate Vmax
        # Vmax can be provided directly or calculated from kcat and enzyme concentration
        vmax_values = brenda_entry.get('vmax_values', [])
        if vmax_values and isinstance(vmax_values, list) and len(vmax_values) > 0:
            params['vmax'] = vmax_values[0].get('value', 0.0)
        elif 'kcat' in params and params['kcat'] > 0:
            pass
            # If kcat available but not Vmax, we could calculate it if we had [E]total
            # For now, just note that Vmax = kcat * [E]total
            # We'll leave it to the user to provide enzyme concentration
            pass
        
        return params
