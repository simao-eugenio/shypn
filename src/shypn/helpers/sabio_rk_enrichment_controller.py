#!/usr/bin/env python3
"""SABIO-RK Enrichment Controller.

Business logic for enriching Petri net models with kinetic parameters from SABIO-RK database.
Handles scanning transitions, querying SABIO-RK, and applying parameters to model metadata.

Architecture:
- Scanner: Find transitions that need enrichment
- Matcher: Match transitions to SABIO-RK entries
- Applicator: Apply kinetic parameters to transitions
- Override Logic: Respect SBML curated data, override KEGG heuristics
"""

import sys
import logging
from typing import Optional, Dict, List, Any, Tuple

from shypn.helpers.kinetic_unit_converter import get_unit_converter
from shypn.crossfetch.database.heuristic_db import HeuristicDatabase
from shypn.crossfetch.cache.sabio_rk_cache_manager import SabioRKCacheManager
from shypn.crossfetch.tracking.parameter_tracker import ParameterTracker

# Phase 2: Rating dialog integration
try:
    from shypn.ui.dialogs.parameter_rating_dialog import ParameterRatingDialog
    RATING_DIALOG_AVAILABLE = True
except ImportError:
    RATING_DIALOG_AVAILABLE = False


class SabioRKEnrichmentController:
    """Controller for SABIO-RK enrichment workflow.
    
    Coordinates the enrichment process:
    1. Scan model for transitions
    2. Query SABIO-RK for each transition
    3. Match SABIO-RK entries to transitions
    4. Apply selected parameters to model
    
    Attributes:
        sabio_client: SABIO-RK API client
        logger: Logger instance
    """
    
    def __init__(self):
        """Initialize SABIO-RK enrichment controller."""
        self.logger = logging.getLogger(self.__class__.__name__)
        self.unit_converter = get_unit_converter()
        
        # Initialize knowledge base components
        try:
            self.db = HeuristicDatabase()
            self.cache_manager = SabioRKCacheManager(self.db)
            self.tracker = ParameterTracker(self.db)
            self.logger.info("KB integration enabled (cache + tracking)")
        except Exception as e:
            self.logger.warning(f"KB integration disabled: {e}")
            self.db = None
            self.cache_manager = None
            self.tracker = None
        
        # Import SABIO-RK client
        try:
            from shypn.data.sabio_rk_client import SabioRKClient
            self.sabio_client = SabioRKClient()
        except ImportError as e:
            self.logger.error(f"Cannot import SABIO-RK client: {e}")
            self.sabio_client = None
    
    def scan_transitions(self, document_model) -> List[Dict[str, Any]]:
        """Scan model for all transitions that can be enriched.
        
        Returns transitions with extractable identifiers (EC number, reaction ID, etc.).
        
        Args:
            document_model: DocumentModel instance
        
        Returns:
            List of dicts with transition info and identifiers
        """
        if not document_model or not hasattr(document_model, 'transitions'):
            self.logger.warning("Invalid document model")
            return []
        
        enrichable = []
        
        for transition in document_model.transitions:
            # Extract identifiers from metadata
            identifiers = self._extract_identifiers(transition)
            
            if identifiers:
                enrichable.append({
                    'transition': transition,
                    'transition_id': transition.id,
                    'transition_name': transition.name or transition.id,
                    'transition_type': getattr(transition, 'transition_type', 'continuous'),
                    'identifiers': identifiers,
                    'current_params': self._get_current_params(transition)
                })
        
        self.logger.info(f"[SABIO-RK] Found {len(enrichable)} enrichable transitions")
        return enrichable
    
    def _extract_identifiers(self, transition) -> Dict[str, str]:
        """Extract identifiers from transition metadata.
        
        Args:
            transition: Transition object
        
        Returns:
            Dict with available identifiers (ec_number, reaction_id, etc.)
        """
        identifiers = {}
        
        # Get metadata
        metadata = getattr(transition, 'metadata', {}) or {}
        
        # EC number
        ec_number = metadata.get('ec_number')
        if ec_number:
            identifiers['ec_number'] = ec_number
        
        # KEGG reaction ID
        reaction_id = metadata.get('kegg_reaction_id') or metadata.get('reaction_id')
        if reaction_id:
            identifiers['reaction_id'] = reaction_id
        
        # SBML reaction ID
        sbml_reaction_id = metadata.get('sbml_reaction_id')
        if sbml_reaction_id:
            identifiers['sbml_reaction_id'] = sbml_reaction_id
        
        return identifiers
    
    def _get_current_params(self, transition) -> Dict[str, Any]:
        """Get current kinetic parameters from transition.
        
        Args:
            transition: Transition object
        
        Returns:
            Dict with current parameter values and sources
        """
        metadata = getattr(transition, 'metadata', {}) or {}
        
        return {
            'Km': metadata.get('Km'),
            'Km_source': metadata.get('Km_source'),
            'Kcat': metadata.get('Kcat'),
            'Kcat_source': metadata.get('Kcat_source'),
            'Vmax': metadata.get('Vmax'),
            'Vmax_source': metadata.get('Vmax_source'),
            'k_forward': metadata.get('k_forward'),
            'k_forward_source': metadata.get('k_forward_source'),
            'k_reverse': metadata.get('k_reverse'),
            'k_reverse_source': metadata.get('k_reverse_source'),
            'Ki': metadata.get('Ki'),
            'Ki_source': metadata.get('Ki_source')
        }
    
    def query_for_transition(self, transition_info: Dict[str, Any], organism: str = None) -> Optional[Dict[str, Any]]:
        """Query SABIO-RK for a single transition.
        
        Args:
            transition_info: Dict with transition metadata (ec_number, reaction_id, etc.)
            organism: Optional organism filter
        
        Returns:
            Dict with SABIO-RK results or None
        """
        if not self.sabio_client:
            self.logger.error("SABIO-RK client not available")
            return None
        
        ec_number = transition_info.get('ec_number')
        if not ec_number:
            self.logger.warning(f"No EC number for transition {transition_info.get('transition_id')}")
            return None
        
        # Try cache first (if enabled)
        if self.cache_manager:
            query_key = self.cache_manager.build_query_key(ec_number, organism)
            cached = self.cache_manager.get_cached_result(query_key)
            if cached:
                self.logger.info(f"Cache hit: {query_key}")
                return cached
        
        # Cache miss - query SABIO-RK API
        try:
            result = self.sabio_client.query_by_ec(ec_number, organism)
            
            # Store in cache (if enabled)
            if result and self.cache_manager:
                query_key = self.cache_manager.build_query_key(ec_number, organism)
                self.cache_manager.store_result(query_key, result)
            
            return result
        except Exception as e:
            self.logger.error(f"SABIO-RK query failed: {e}")
            return None
    
    def query_all_transitions(self, document_model, organism: str = None, batch_size: int = 10) -> List[Dict[str, Any]]:
        """Query SABIO-RK for all enrichable transitions in model.
        
        Args:
            document_model: DocumentModel instance
            organism: Optional organism filter
            batch_size: Number of transitions to query before pausing (default: 10)
        
        Returns:
            List of dicts with transition info and SABIO-RK results
        """
        import time
        
        enrichable = self.scan_transitions(document_model)
        total = len(enrichable)
        
        if total > 20:
            self.logger.warning(f"[SABIO-RK] Querying {total} transitions - this may take a while!")
            self.logger.warning(f"[SABIO-RK] Processing in batches of {batch_size} to avoid API timeouts")
        
        results = []
        skipped_count = 0
        for i, transition_info in enumerate(enrichable, 1):
            try:
                transition_id = transition_info['transition_id']
                ec_number = transition_info.get('identifiers', {}).get('ec_number', 'unknown')
                
                self.logger.info(f"[SABIO-RK] Querying {i}/{total}: {transition_id} (EC {ec_number})")
                sabio_result = self.query_for_transition(transition_info, organism)
                
                if sabio_result:
                    results.append({
                        **transition_info,
                        'sabio_data': sabio_result
                    })
                else:
                    skipped_count += 1
                    self.logger.debug(f"[SABIO-RK] Skipped {transition_id}: No data or too many results")
                
                # Add small delay every batch_size queries to avoid overwhelming API
                if i % batch_size == 0 and i < total:
                    self.logger.debug(f"[SABIO-RK] Completed batch {i//batch_size}, pausing 2 seconds...")
                    time.sleep(2)  # 2 second pause between batches
                
            except Exception as e:
                self.logger.error(f"[SABIO-RK] Error querying {transition_info['transition_id']}: {e}")
                skipped_count += 1
                continue
        
        self.logger.info(f"[SABIO-RK] ✓ Found data for {len(results)}/{total} transitions (skipped {skipped_count})")
        if skipped_count > 0:
            self.logger.info(f"[SABIO-RK] Skipped transitions: either no data available or >200 results (too many)")
        return results
    
    def apply_parameters(self, 
                        transition_info: Dict[str, Any],
                        selected_params: Dict[str, Any],
                        override_kegg: bool = True,
                        override_sbml: bool = False) -> Tuple[bool, str]:
        """Apply SABIO-RK parameters to a transition.
        
        Args:
            transition_info: Dict with transition object
            selected_params: Dict with parameters to apply (param_type -> value)
            override_kegg: Whether to override KEGG heuristics (default: True)
            override_sbml: Whether to override SBML curated data (default: False)
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        self.logger.debug(f"[SABIO-RK] apply_parameters called with transition_info keys: {transition_info.keys()}")
        self.logger.debug(f"[SABIO-RK] selected_params: {selected_params}")
        
        transition = transition_info.get('transition')
        if not transition:
            self.logger.error(f"[SABIO-RK] No transition object in transition_info! Keys: {transition_info.keys()}")
            return (False, "No transition object found")
        
        self.logger.debug(f"[SABIO-RK] Transition object: {transition}, ID: {transition.id if hasattr(transition, 'id') else 'NO ID'}")
        
        metadata = getattr(transition, 'metadata', {}) or {}
        current_params = transition_info.get('current_params', {})
        
        applied = []
        skipped = []
        
        for param_type, param_value in selected_params.items():
            # Check if parameter already exists
            current_value = current_params.get(param_type)
            current_source = current_params.get(f'{param_type}_source')
            
            # Apply override logic
            should_apply = False
            
            if current_value is None:
                # No existing value - always apply
                should_apply = True
            elif current_source == 'kegg_heuristic' and override_kegg:
                # KEGG heuristic - apply if override enabled
                should_apply = True
            elif current_source == 'sbml_curated' and override_sbml:
                # SBML curated - apply only if override enabled
                should_apply = True
            elif override_sbml:
                # Other source with override enabled
                should_apply = True
            else:
                # Respect existing value
                skipped.append(f"{param_type} (existing: {current_source})")
                continue
            
            if should_apply:
                # Apply parameter with unit conversion
                original_value = param_value['value']
                original_units = param_value.get('units', '')
                
                # Convert to standard units
                converted_value, converted_units, warning = self.unit_converter.validate_parameter_units(
                    param_type, original_value, original_units, 'sabio_rk'
                )
                
                if warning:
                    self.logger.warning(warning)
                
                # Store converted value
                metadata[param_type] = converted_value
                metadata[f'{param_type}_source'] = 'sabio_rk_enriched'
                metadata[f'{param_type}_units'] = converted_units
                metadata[f'{param_type}_original_value'] = original_value
                metadata[f'{param_type}_original_units'] = original_units
                
                if converted_value != original_value:
                    self.logger.info(f"[SABIO-RK] Unit conversion: {param_type} {original_value} {original_units} → {converted_value} {converted_units}")
                
                applied.append(param_type)
        
        # Update transition metadata
        transition.metadata = metadata
        self.logger.info(f"[SABIO-RK] Updated transition.metadata: {list(metadata.keys())}")
        self.logger.info(f"[SABIO-RK] Applied parameters: {applied}")
        for param in applied:
            self.logger.info(f"[SABIO-RK]   {param} = {metadata.get(param)} {metadata.get(f'{param}_units', '')}")
        
        # Auto-generate Michaelis-Menten rate function ONLY if we have BOTH Km and (Vmax or Kcat)
        has_km = 'Km' in metadata and metadata['Km'] is not None
        has_vmax = 'Vmax' in metadata and metadata['Vmax'] is not None
        has_kcat = 'Kcat' in metadata and metadata['Kcat'] is not None
        
        if has_km and (has_vmax or has_kcat):
            self.logger.info(f"[SABIO-RK] Generating rate function (Km={metadata.get('Km')}, Vmax={metadata.get('Vmax')}, Kcat={metadata.get('Kcat')})")
            self._generate_rate_function_from_parameters(
                transition,
                metadata,
                override_kegg=override_kegg,
                override_sbml=override_sbml
            )
        else:
            self.logger.info(f"[SABIO-RK] Skipping rate function generation (missing Km or Vmax/Kcat)")
        
        # Track application in KB (if enabled)
        param_id = None
        if self.tracker and applied:
            try:
                param_id = self.tracker.track_application(
                    transition_id=transition_info['transition_id'],
                    parameters={
                        'vmax': metadata.get('Vmax'),
                        'km': metadata.get('Km'),
                        'kcat': metadata.get('Kcat'),
                        'ki': metadata.get('Ki')
                    },
                    source='SABIO-RK',
                    transition_type='continuous',
                    ec_number=transition_info.get('identifiers', {}).get('ec_number'),
                    reaction_id=transition_info.get('identifiers', {}).get('reaction_id'),
                    organism=metadata.get('organism'),
                    metadata={
                        'temperature': metadata.get('temperature'),
                        'ph': metadata.get('ph'),
                        'pubmed_id': metadata.get('pubmed_id')
                    }
                )
                self.logger.debug(f"Tracked application (param_id={param_id})")
            except Exception as e:
                self.logger.warning(f"Failed to track application: {e}")
        
        # Phase 2: Show rating dialog (if available and tracking succeeded)
        if param_id and RATING_DIALOG_AVAILABLE:
            self._show_rating_dialog(param_id, transition_info, applied)
        
        # Build result message
        if applied:
            message = f"Applied: {', '.join(applied)}"
            if skipped:
                message += f" | Skipped: {', '.join(skipped)}"
            return (True, message)
        else:
            return (False, f"No parameters applied. Skipped: {', '.join(skipped)}")
    
    def apply_batch(self,
                   enrichment_results: List[Dict[str, Any]],
                   selected_transitions: List[str],
                   override_kegg: bool = True,
                   override_sbml: bool = False) -> Dict[str, Any]:
        """Apply SABIO-RK parameters to multiple transitions.
        
        NOTE: This method now returns parameter options for user selection
        instead of auto-applying. Use apply_selected_parameter_set() to apply.
        
        Args:
            enrichment_results: List of enrichment results from query_all_transitions()
            selected_transitions: List of transition IDs to enrich
            override_kegg: Whether to override KEGG heuristics
            override_sbml: Whether to override SBML curated data
        
        Returns:
            Dict with:
            - parameter_options: List of dicts with transition_id and available parameter sets
            - total: Number of transitions processed
        """
        parameter_options = []
        
        for result in enrichment_results:
            transition_id = result['transition_id']
            
            if transition_id not in selected_transitions:
                continue
            
            # Get parameters from SABIO-RK result
            sabio_data = result.get('sabio_data', {})
            parameters = sabio_data.get('parameters', [])
            query_organism = sabio_data.get('query_organism')  # Organism filter used in query
            
            if not parameters:
                continue
            
            # Get multiple parameter sets for user to choose from
            # Pass query_organism: if user filtered by organism, SABIO-RK only returned
            # data for that organism (even if organism not in SBML annotations)
            parameter_sets = self._select_best_parameters(
                parameters, 
                max_results=15,
                query_organism=query_organism
            )
            
            if parameter_sets:
                parameter_options.append({
                    'transition_id': transition_id,
                    'transition_info': result,
                    'parameter_sets': parameter_sets,
                    'override_kegg': override_kegg,
                    'override_sbml': override_sbml
                })
                
                self.logger.info(
                    f"[SABIO-RK] {transition_id}: Found {len(parameter_sets)} parameter options"
                )
        
        return {
            'parameter_options': parameter_options,
            'total': len(selected_transitions)
        }
    
    def apply_selected_parameter_set(self,
                                    transition_info: Dict[str, Any],
                                    parameter_set: Dict[str, Any],
                                    override_kegg: bool = True,
                                    override_sbml: bool = False) -> Tuple[bool, str]:
        """Apply a specific parameter set selected by user.
        
        Args:
            transition_info: Dict with transition object
            parameter_set: Selected parameter set from _select_best_parameters()
            override_kegg: Whether to override KEGG heuristics
            override_sbml: Whether to override SBML curated data
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Convert parameter_set format to selected_params format expected by apply_parameters
        selected_params = {}
        for param_type, param_data in parameter_set.get('parameters', {}).items():
            selected_params[param_type] = param_data
        
        return self.apply_parameters(
            transition_info,
            selected_params,
            override_kegg,
            override_sbml
        )
    
    def _select_best_parameters(self, parameters: List[Dict[str, Any]], max_results: int = 15, query_organism: str = None) -> List[Dict[str, Any]]:
        """Select best parameter sets from SABIO-RK results.
        
        Instead of returning only median, returns multiple parameter sets
        for user to choose from (up to max_results).
        
        Strategy:
        1. Group by organism + reaction combination (substrate/temp/pH not always available)
        2. Sort by completeness (has Km + Vmax/Kcat)
        3. Remove duplicates
        4. Return top max_results options
        
        Args:
            parameters: List of parameter dicts from SABIO-RK
            max_results: Maximum number of parameter sets to return (default 15)
            query_organism: Organism used in SABIO-RK query filter (can be trusted)
        
        Returns:
            List of parameter set dicts, each with:
            - organism, substrate (reaction_name), temperature, pH
            - Km, Vmax, Kcat, Ki (if available)
            - completeness score
        """
        # Group by organism + reaction_id (each reaction from SABIO-RK represents different conditions)
        parameter_sets = {}
        
        for param in parameters:
            organism = param.get('organism')
            # If organism not in SBML but we have query_organism:
            # SABIO-RK filtered the results, so we can trust query_organism
            # (SABIO-RK only returned data for that organism)
            if organism is None and query_organism:
                organism = query_organism
            elif organism is None:
                organism = 'Unknown'
            
            reaction_id = param.get('reaction_id', 'unknown')
            reaction_name = param.get('reaction_name', 'Unknown reaction')
            kegg_reaction_id = param.get('kegg_reaction_id')
            
            # Use KEGG reaction ID as substrate if available (more meaningful than REACT_??)
            # Otherwise fall back to reaction_name
            substrate_display = kegg_reaction_id if kegg_reaction_id else reaction_name
            
            # Use reaction as a proxy for experimental conditions
            # (each SABIO-RK reaction entry represents a specific experiment)
            key = (organism, reaction_id)
            
            if key not in parameter_sets:
                parameter_sets[key] = {
                    'organism': organism,
                    'substrate': substrate_display,  # Show KEGG reaction ID or reaction name
                    'temperature': 'N/A',  # Not always available in SBML
                    'pH': 'N/A',  # Not always available in SBML
                    'reaction_id': reaction_id,
                    'parameters': {}
                }
            
            # Add parameter to set
            param_type = param.get('parameter_type')
            if param_type and param_type != 'other':
                if param_type not in parameter_sets[key]['parameters']:
                    parameter_sets[key]['parameters'][param_type] = {
                        'value': param['value'],
                        'units': param.get('units', '')
                    }
        
        # Convert to list and calculate completeness
        result_sets = []
        for key, pset in parameter_sets.items():
            params = pset['parameters']
            
            # Completeness score (prefer sets with multiple parameters)
            score = 0
            if 'Km' in params:
                score += 3  # Km is important
            if 'Vmax' in params or 'Kcat' in params:
                score += 3  # Need either Vmax or Kcat
            if 'Ki' in params:
                score += 1  # Bonus for inhibition constant
            if 'Kcat' in params:
                score += 1  # Bonus for turnover number
            
            pset['completeness_score'] = score
            
            # Only include sets with at least Km OR (Vmax/Kcat)
            if score >= 3:
                result_sets.append(pset)
        
        # Sort by completeness (descending)
        result_sets.sort(key=lambda x: x['completeness_score'], reverse=True)
        
        # Limit to max_results
        result_sets = result_sets[:max_results]
        
        self.logger.info(f"[SABIO-RK] _select_best_parameters: Input={len(parameters)} parameters, Grouped into={len(parameter_sets)} unique sets, After filtering={len(result_sets)} sets")
        self.logger.info(f"[SABIO-RK] Selected {len(result_sets)} parameter sets from {len(parameters)} individual parameters")
        for i, pset in enumerate(result_sets[:5]):  # Log first 5
            self.logger.info(
                f"[SABIO-RK]   Set {i+1}: {pset['organism']}, reaction={pset.get('reaction_id', 'N/A')}, "
                f"score={pset['completeness_score']}, params={list(pset['parameters'].keys())}"
            )
        
        return result_sets
    
    def _generate_rate_function_from_parameters(self, transition, metadata: Dict[str, Any],
                                               override_kegg: bool = True,
                                               override_sbml: bool = False):
        """Generate Michaelis-Menten rate function from SABIO-RK parameters.
        
        Creates rate_function string for continuous simulation:
        - Basic: michaelis_menten(substrate, vmax, km)
        - With inhibitor: michaelis_menten(substrate, vmax, km*(1 + inhibitor/ki))
        
        Args:
            transition: Transition object to update
            metadata: Metadata dict with Km, Vmax, Kcat, Ki values
            override_kegg: Whether to override KEGG heuristic functions
            override_sbml: Whether to override SBML curated functions
        """
        # Check if we should skip based on existing rate function
        if hasattr(transition, 'properties') and transition.properties:
            if 'rate_function' in transition.properties:
                existing_func = transition.properties['rate_function']
                existing_source = metadata.get('rate_function_source', '')
                
                # Skip if SBML curated and override not enabled
                if existing_source == 'sbml_curated' and not override_sbml:
                    return
                
                # Skip if non-KEGG source and override not enabled
                if existing_source not in ['kegg_heuristic', 'sabio_rk_enriched', ''] and not override_sbml:
                    return
        
        # Need at least Km and (Vmax or Kcat)
        km = metadata.get('Km')
        vmax = metadata.get('Vmax')
        kcat = metadata.get('Kcat')
        ki = metadata.get('Ki')
        
        if not km:
            return
        
        # Calculate Vmax from Kcat if needed (assumes [E]=1 or normalized)
        if not vmax and kcat:
            vmax = kcat
        
        if not vmax:
            return
        
        # Find substrate place - need to identify which place the Km refers to
        substrate_place = None
        inhibitor_place = None
        
        # Try to find connected places via arcs
        input_places = []
        output_places = []
        
        if hasattr(self, 'model_canvas') and self.model_canvas:
            if hasattr(self.model_canvas, 'arcs'):
                for arc in self.model_canvas.arcs:
                    # Input arcs (Place → Transition)
                    if (hasattr(arc, 'target') and hasattr(arc.target, 'id') and
                        str(arc.target.id) == str(transition.id)):
                        if hasattr(arc, 'source') and hasattr(arc.source, 'id'):
                            input_places.append(arc.source)
                    
                    # Output arcs (Transition → Place)
                    if (hasattr(arc, 'source') and hasattr(arc.source, 'id') and
                        str(arc.source.id) == str(transition.id)):
                        if hasattr(arc, 'target') and hasattr(arc.target, 'id'):
                            output_places.append(arc.target)
        
        # Heuristic to select substrate:
        # 1. If only one input place, use it
        # 2. If multiple inputs, prefer the one with highest tokens (most abundant)
        # 3. Check if transition name/metadata suggests which is the main substrate
        
        if input_places:
            if len(input_places) == 1:
                substrate_place = input_places[0].id
            else:
                # Multiple inputs - select based on tokens (concentration)
                max_tokens = -1
                for place in input_places:
                    tokens = getattr(place, 'tokens', 0)
                    if tokens > max_tokens:
                        max_tokens = tokens
                        substrate_place = place.id
                
                # Use second place for inhibitor if Ki available
                if ki and len(input_places) > 1:
                    for place in input_places:
                        if place.id != substrate_place:
                            inhibitor_place = place.id
                            break
        
        # If no input places or substrate not found, try output places
        # (for reverse reactions where Km might be for product)
        if not substrate_place and output_places:
            self.logger.info(f"[SABIO-RK] No input places found, using first output place for substrate")
            substrate_place = output_places[0].id
        
        # Fallback: use generic names
        if not substrate_place:
            substrate_place = 'S'
            self.logger.warning(f"[SABIO-RK] Could not identify substrate place, using generic 'S'")
        
        # Generate rate function
        if ki and inhibitor_place:
            # Michaelis-Menten with competitive inhibition
            rate_function = f"michaelis_menten({substrate_place}, vmax={vmax}, km={km} * (1 + {inhibitor_place} / {ki}))"
        else:
            # Basic Michaelis-Menten
            rate_function = f"michaelis_menten({substrate_place}, vmax={vmax}, km={km})"
        
        # Apply to transition
        if not hasattr(transition, 'properties') or transition.properties is None:
            transition.properties = {}
        
        transition.properties['rate_function'] = rate_function
        transition.rate_function = rate_function  # Store as rate_function, not rate
        
        # Mark source
        metadata['rate_function_source'] = 'sabio_rk_enriched'
        
        self.logger.info(f"[SABIO-RK] Generated rate function: {rate_function}")
    
    def _show_rating_dialog(self, param_id: int, transition_info: Dict[str, Any], applied_params: List[str]):
        """Show rating dialog for parameter application (Phase 2).
        
        Args:
            param_id: Parameter tracking ID
            transition_info: Transition information dict
            applied_params: List of applied parameter names
        """
        try:
            # Create dialog
            dialog = ParameterRatingDialog(
                parent=None,  # Will be set by caller if needed
                transition_name=transition_info.get('transition_name', 'Unknown'),
                parameters=applied_params,
                source='SABIO-RK'
            )
            
            # Show dialog and get feedback
            feedback = dialog.run_and_get_feedback()
            
            if feedback:
                rating = feedback.get('rating')
                comment = feedback.get('comment', '')
                
                # Store rating via tracker
                success = self.tracker.update_rating(
                    parameter_id=param_id,
                    rating=rating,
                    comment=comment
                )
                
                if success:
                    self.logger.info(
                        f"Stored user rating: {rating} "
                        f"for param_id={param_id}"
                    )
                else:
                    self.logger.warning(f"Failed to store rating for param_id={param_id}")
            else:
                self.logger.debug("User skipped rating")
                
        except Exception as e:
            self.logger.error(f"Rating dialog error: {e}")


def create_sabio_rk_controller() -> SabioRKEnrichmentController:
    """Create SABIO-RK enrichment controller instance.
    
    Returns:
        SabioRKEnrichmentController instance
    """
    return SabioRKEnrichmentController()
