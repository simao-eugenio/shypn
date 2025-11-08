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
            print(f"[BRENDA_SCAN] No model_canvas set!")
            return []
        
        print(f"[BRENDA_SCAN] Scanning model: {self.model_canvas.get_display_name() if hasattr(self.model_canvas, 'get_display_name') else 'Unknown'}")
        print(f"[BRENDA_SCAN] Model ID: {id(self.model_canvas)}")
        print(f"[BRENDA_SCAN] Model type: {type(self.model_canvas)}")
        print(f"[BRENDA_SCAN] Has 'transitions' attr: {hasattr(self.model_canvas, 'transitions')}")
        if hasattr(self.model_canvas, 'transitions'):
            print(f"[BRENDA_SCAN] Transitions type: {type(self.model_canvas.transitions)}")
        
        # Debug: list all attributes
        print(f"[BRENDA_SCAN] Model attributes: {[a for a in dir(self.model_canvas) if not a.startswith('_')][:20]}")
        
        transitions = []
        
        # Access transitions from ModelCanvasManager
        if hasattr(self.model_canvas, 'transitions'):
            print(f"[BRENDA_SCAN] Found {len(self.model_canvas.transitions)} transitions in model")
            
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
                    # Extract data source
                    transition_info['data_source'] = transition.metadata.get('data_source', 'unknown')
                    ec_val = transition.metadata.get('ec_number',
                             transition.metadata.get('ec_numbers', []))
                    
                    print(f"[BRENDA_SCAN] Transition {transition_info['name']}: ec_val={ec_val}, type={type(ec_val)}")
                    
                    if isinstance(ec_val, list) and len(ec_val) > 0:
                        transition_info['ec_number'] = ec_val[0]
                        print(f"[BRENDA_SCAN]   -> Extracted EC from list: {ec_val[0]}")
                    elif ec_val and ec_val != '-':
                        transition_info['ec_number'] = str(ec_val)
                        print(f"[BRENDA_SCAN]   -> Extracted EC directly: {ec_val}")
                    else:
                        print(f"[BRENDA_SCAN]   -> No valid EC number (ec_val={ec_val})")
                    
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
                    # Check if transition has a label with KEGG reaction ID (e.g., "R00710")
                    label = getattr(transition, 'label', None) or transition_info['name']
                    if label and re.match(r'^R\d{5}$', label):
                        # This is a KEGG reaction ID - fetch EC numbers from KEGG API
                        print(f"[BRENDA_SCAN] Fetching EC numbers for KEGG reaction {label}...")
                        try:
                            ec_numbers = self.kegg_ec_fetcher.fetch_ec_numbers(label)
                            if ec_numbers:
                                transition_info['ec_number'] = ec_numbers[0]
                                transition_info['data_source'] = 'kegg_import'
                                print(f"[BRENDA_SCAN]   -> Found EC number(s) from KEGG: {ec_numbers}")
                                
                                # Also store in transition metadata for future use
                                if not hasattr(transition, 'metadata'):
                                    transition.metadata = {}
                                if not transition.metadata:
                                    transition.metadata = {}
                                transition.metadata['ec_numbers'] = ec_numbers
                                transition.metadata['ec_number'] = ec_numbers[0]
                            else:
                                print(f"[BRENDA_SCAN]   -> No EC numbers found for {label}")
                        except Exception as e:
                            print(f"[BRENDA_SCAN]   -> Error fetching EC for {label}: {e}")
                
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
            print("[BRENDA_AUTH] BRENDA API client not available (zeep library missing?)")
            return False
        
        print(f"[BRENDA_AUTH] Authenticating with email: {email}")
        success = self.brenda_api.authenticate(email, password)
        
        if success:
            print("[BRENDA_AUTH] ✓ Authentication successful")
        else:
            print("[BRENDA_AUTH] ✗ Authentication failed")
        
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
            print(f"[QUERY_BRENDA] BRENDA API client not available")
            return None
        
        if not self.brenda_api.is_authenticated():
            print(f"[QUERY_BRENDA] Not authenticated with BRENDA. Please authenticate first.")
            return None
        
        print(f"[QUERY_BRENDA] Querying BRENDA API for EC {ec_number}, organism={organism or 'all'}")
        
        try:
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
                
                print(f"[QUERY_BRENDA] Found data for EC {ec_number}: "
                      f"{len(km_values)} Km, {len(kcat_values)} kcat, {len(ki_values)} Ki values")
                
                return result
            else:
                print(f"[QUERY_BRENDA] No Km data found for EC {ec_number}")
                return None
        
        except Exception as e:
            print(f"[QUERY_BRENDA] Error querying BRENDA for EC {ec_number}: {e}")
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
            
            print(f"[BRENDA] Applying parameters to transition {transition_id} (override={override_mode})")
            print(f"[BRENDA]   Before: {transition_obj.metadata}")
            
            # Add/update kinetic parameters with source tracking
            for param_name, param_value in parameters.items():
                # Skip internal flags
                if param_name.startswith('_'):
                    continue
                
                param_exists = param_name in transition_obj.metadata
                
                if not param_exists:
                    # New parameter - always add
                    transition_obj.metadata[param_name] = param_value
                    transition_obj.metadata[f'{param_name}_source'] = 'brenda_enriched'
                    print(f"[BRENDA]   Added {param_name}={param_value}, source=brenda_enriched")
                elif override_mode:
                    # Parameter exists but override is enabled - replace it
                    old_value = transition_obj.metadata[param_name]
                    transition_obj.metadata[param_name] = param_value
                    transition_obj.metadata[f'{param_name}_source'] = 'brenda_enriched'
                    print(f"[BRENDA]   Overrode {param_name}: {old_value} → {param_value}, source=brenda_enriched")
                else:
                    # Parameter exists and override disabled - skip
                    print(f"[BRENDA]   Skipped {param_name} (already exists: {transition_obj.metadata[param_name]})")
            
            # Mark that enrichment occurred (don't overwrite original data_source)
            # Original data_source stays as 'kegg_import' or 'sbml_import'
            if 'enrichment_source' not in transition_obj.metadata:
                transition_obj.metadata['enrichment_source'] = 'brenda'
            
            print(f"[BRENDA]   After: {transition_obj.metadata}")
            
            # Auto-generate Michaelis-Menten rate function from parameters
            try:
                print(f"[BRENDA] >>> About to call _generate_rate_function_from_parameters for T{transition_obj.id}")
                # Check if we should override existing rate functions
                override = parameters.get('_override_rate_function', False)
                self._generate_rate_function_from_parameters(transition_obj, parameters, override=override)
                print(f"[BRENDA] >>> Finished _generate_rate_function_from_parameters for T{transition_obj.id}")
            except Exception as e:
                print(f"[BRENDA] ⚠️ ERROR in rate function generation for T{transition_obj.id}: {e}")
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
        print(f"[BRENDA_MM] Transition object: {transition}")
        print(f"[BRENDA_MM] Transition type: {type(transition)}")
        print(f"[BRENDA_MM] Parameters: {parameters}")
        print(f"[BRENDA_MM] Override mode: {override}")
        
        if transition is None:
            print(f"[BRENDA_MM] ERROR: transition object is None!")
            return
        
        # Check if already has rate_function
        if hasattr(transition, 'properties') and transition.properties:
            if 'rate_function' in transition.properties:
                existing_func = transition.properties['rate_function']
                print(f"[BRENDA_MM] Transition {transition.id} already has rate_function: {existing_func}")
                
                if not override:
                    print(f"[BRENDA_MM] Override=False, skipping auto-generation (keeping existing)")
                    return
                else:
                    print(f"[BRENDA_MM] Override=True, will replace with BRENDA-optimized rate function")

        
        # Need at least Vmax (or Kcat) and Km
        vmax = parameters.get('vmax')
        km = parameters.get('km')
        ki = parameters.get('ki')
        kcat = parameters.get('kcat')
        
        if not km:
            print(f"[BRENDA_MM] Missing Km for T{transition.id}, cannot generate rate function")
            return
        
        # Calculate Vmax if only kcat provided
        if not vmax and kcat:
            # Vmax = kcat * [E]total
            # For now, use kcat directly (assumes [E]=1 or normalized)
            vmax = kcat
            print(f"[BRENDA_MM] Using kcat={kcat} as Vmax for T{transition.id} (assumes [E]=1)")
        
        # If no Vmax/Kcat provided, try to preserve existing Vmax from transition
        if not vmax:
            # Check if transition already has Vmax in metadata or properties
            existing_vmax = None
            
            if hasattr(transition, 'metadata') and transition.metadata:
                existing_vmax = transition.metadata.get('vmax') or transition.metadata.get('Vmax')
            
            if not existing_vmax and hasattr(transition, 'properties') and transition.properties:
                # Try to parse existing rate_function for Vmax value
                existing_func = transition.properties.get('rate_function', '')
                if 'vmax=' in existing_func:
                    import re
                    match = re.search(r'vmax=(\d+(?:\.\d+)?)', existing_func)
                    if match:
                        existing_vmax = float(match.group(1))
                        print(f"[BRENDA_MM] Extracted existing Vmax={existing_vmax} from rate_function")
            
            if existing_vmax:
                vmax = existing_vmax
                print(f"[BRENDA_MM] ⚠️ No Kcat provided, reusing existing Vmax={vmax} with new Km={km}")
                print(f"[BRENDA_MM] Note: For accurate kinetics, select both Km and Kcat parameters from BRENDA")
            else:
                print(f"[BRENDA_MM] ❌ Missing Vmax/Kcat for T{transition.id}, cannot generate rate function")
                print(f"[BRENDA_MM] ℹ️  TIP: Select BOTH a Km and a Kcat parameter from BRENDA results to generate complete rate function")
                return
        
        # Find substrate place (first input place)
        substrate_place = None
        inhibitor_place = None
        
        # Try to get input places from model canvas arcs
        if self.model_canvas and hasattr(self.model_canvas, 'arcs'):
            input_places = []
            for arc in self.model_canvas.arcs:
                # Check if arc points to this transition (Place → Transition)
                if hasattr(arc, 'target') and hasattr(arc.target, 'id'):
                    if str(arc.target.id) == str(transition.id):
                        # This arc feeds into our transition
                        if hasattr(arc, 'source') and hasattr(arc.source, 'label'):
                            place_name = arc.source.label if arc.source.label else arc.source.name
                            input_places.append(place_name)
                            print(f"[BRENDA_MM] Found input place: {place_name}")
            
            if len(input_places) > 0:
                substrate_place = input_places[0]
                print(f"[BRENDA_MM] Using first input place as substrate: {substrate_place}")
                
                if len(input_places) > 1 and ki and ki > 0:
                    inhibitor_place = input_places[1]
                    print(f"[BRENDA_MM] Found potential inhibitor place: {inhibitor_place}")
        
        # Fallback if no input places found
        if not substrate_place:
            if hasattr(transition, 'id'):
                substrate_place = f"P{transition.id}"
                print(f"[BRENDA_MM] No input places found, using placeholder: {substrate_place}")
            else:
                substrate_place = "substrate"
                print(f"[BRENDA_MM] Warning: Using generic substrate name")
        
        # Build rate function with NAMED PARAMETERS (self-documenting)
        if ki and ki > 0 and inhibitor_place:
            # Competitive inhibition form with actual inhibitor place
            # v = (Vmax * [S]) / (Km * (1 + [I]/Ki) + [S])
            # Expanded: michaelis_menten(S, Vmax, Km * (1 + I/Ki))
            rate_function = f"michaelis_menten({substrate_place}, vmax={vmax}, km={km} * (1 + {inhibitor_place} / {ki}))"
            print(f"[BRENDA_MM] Generated MM with competitive inhibition:")
            print(f"[BRENDA_MM]   Substrate: {substrate_place}")
            print(f"[BRENDA_MM]   Inhibitor: {inhibitor_place}, Ki={ki}")
            print(f"[BRENDA_MM]   Rate function: {rate_function}")
        elif ki and ki > 0:
            # Ki available but no inhibitor place detected
            rate_function = f"michaelis_menten({substrate_place}, vmax={vmax}, km={km})"
            print(f"[BRENDA_MM] Generated simple MM (Ki={ki} available but no inhibitor place found)")
            print(f"[BRENDA_MM] Rate function: {rate_function}")
        else:
            # Simple Michaelis-Menten with named parameters
            rate_function = f"michaelis_menten({substrate_place}, vmax={vmax}, km={km})"
            print(f"[BRENDA_MM] Generated simple MM: {rate_function}")
        
        # Set rate function in transition properties
        if not hasattr(transition, 'properties'):
            transition.properties = {}
        
        transition.properties['rate_function'] = rate_function
        transition.properties['rate_function_source'] = 'brenda_auto_generated'
        
        # Ensure transition is continuous (needed for rate functions)
        if not hasattr(transition, 'transition_type') or transition.transition_type != 'continuous':
            transition.transition_type = 'continuous'
        
        print(f"[BRENDA_MM] ✅ Successfully set rate_function on transition T{transition.id}")
        print(f"[BRENDA_MM]    transition.properties['rate_function'] = '{rate_function}'")
        print(f"[BRENDA_MM]    transition.transition_type = '{transition.transition_type}'")
        
        # VERIFICATION: Read back the values to confirm they were set
        verify_func = transition.properties.get('rate_function')
        verify_type = getattr(transition, 'transition_type', 'unknown')
        
        if verify_func == rate_function:
            print(f"[BRENDA_MM] ✓ VERIFIED: rate_function correctly stored")
        else:
            print(f"[BRENDA_MM] ✗ WARNING: rate_function mismatch!")
            print(f"[BRENDA_MM]   Expected: '{rate_function}'")
            print(f"[BRENDA_MM]   Got:      '{verify_func}'")
        
        if verify_type == 'continuous':
            print(f"[BRENDA_MM] ✓ VERIFIED: transition_type = 'continuous'")
        else:
            print(f"[BRENDA_MM] ✗ WARNING: transition_type = '{verify_type}' (expected 'continuous')")
        
        print(f"[BRENDA_MM] ========================================================\n")
    
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
        
        print(f"[BRENDA_CONTROLLER] Finished enrichment: "
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
        
        print(f"[BRENDA] === ENRICHMENT DEBUG ===")
        print(f"[BRENDA] Scanned {len(transitions)} transitions")
        print(f"[BRENDA] EC numbers to query: {ec_numbers}")
        print(f"[BRENDA] Override existing: {override_existing}")
        
        # Query BRENDA for each EC number (with mock data for now)
        brenda_data = {}
        for ec_number in ec_numbers:
            data = self.fetch_from_brenda_api(ec_number, organism)
            if data:
                brenda_data[ec_number] = data
                print(f"[BRENDA] Found BRENDA data for EC {ec_number}: {data.get('enzyme_name')}")
            else:
                print(f"[BRENDA] No BRENDA data for EC {ec_number}")
        
        print(f"[BRENDA] Total BRENDA entries found: {len(brenda_data)}")
        
        # Match and apply enrichments
        enriched_count = 0
        skipped_count = 0
        for transition in transitions:
            ec = transition.get('ec_number')
            trans_id = transition.get('id')
            has_kin = transition.get('has_kinetics')
            data_source = transition.get('data_source', 'unknown')
            
            print(f"[BRENDA] Transition {trans_id}: EC={ec}, has_kinetics={has_kin}, data_source={data_source}")
            
            if ec in brenda_data:
                # Determine if we should enrich based on override mode and data source
                should_enrich = False
                
                if not has_kin:
                    # No kinetics at all - always enrich
                    should_enrich = True
                    print(f"[BRENDA]   → No kinetics, will enrich")
                elif data_source == 'kegg_import':
                    # KEGG import - always override (all kinetics are heuristics)
                    should_enrich = True
                    print(f"[BRENDA]   → KEGG import detected, will override heuristics with BRENDA data")
                elif override_existing:
                    # User explicitly requested override for all sources
                    should_enrich = True
                    print(f"[BRENDA]   → Override mode enabled, will replace existing kinetics")
                else:
                    # Has kinetics from curated source (SBML/BioPAX) and override disabled
                    should_enrich = False
                    print(f"[BRENDA]   → Curated kinetics from {data_source}, respecting existing data")
                
                if should_enrich:
                    # Apply enrichment
                    params = self._extract_parameters(brenda_data[ec])
                    # Add override flag for rate function regeneration
                    params['_override_rate_function'] = True  # Always regenerate rate functions when enriching
                    print(f"[BRENDA] ✓ ENRICHING transition {trans_id} with {params}")
                    self.apply_enrichment_to_transition(
                        transition['id'], 
                        params,
                        transition_obj=transition.get('transition_obj')
                    )
                    enriched_count += 1
                else:
                    print(f"[BRENDA] ✗ SKIPPING transition {trans_id} - has curated kinetics")
                    skipped_count += 1
            else:
                if ec:
                    print(f"[BRENDA] ✗ No BRENDA data for EC {ec}")
                else:
                    print(f"[BRENDA] ✗ No EC number for transition {trans_id}")
        
        print(f"[BRENDA] === ENRICHMENT SUMMARY ===")
        print(f"[BRENDA] Enriched: {enriched_count}, Skipped: {skipped_count}")
        
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
                # Determine if we should enrich based on override mode and data source
                should_enrich = False
                
                if not has_kin:
                    # No kinetics at all - always enrich
                    should_enrich = True
                elif data_source == 'kegg_import':
                    # KEGG import - always override (all kinetics are heuristics)
                    should_enrich = True
                    print(f"[BRENDA] Transition {trans_id}: KEGG import, overriding heuristics")
                elif override_existing:
                    # User explicitly requested override for all sources
                    should_enrich = True
                    print(f"[BRENDA] Transition {trans_id}: Override mode, replacing curated kinetics")
                else:
                    # Has kinetics from curated source and override disabled
                    should_enrich = False
                    print(f"[BRENDA] Transition {trans_id}: Curated kinetics from {data_source}, skipping")
                
                if should_enrich:
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
            # If kcat available but not Vmax, we could calculate it if we had [E]total
            # For now, just note that Vmax = kcat * [E]total
            # We'll leave it to the user to provide enzyme concentration
            pass
        
        return params
