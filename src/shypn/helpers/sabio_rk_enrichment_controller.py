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
        """Query SABIO-RK for a specific transition.
        
        Tries multiple query strategies in order of preference:
        1. EC number (most specific)
        2. KEGG reaction ID
        3. SBML reaction ID
        
        Args:
            transition_info: Dict with transition and identifiers
            organism: Optional organism filter
        
        Returns:
            Dict with SABIO-RK results or None
        """
        if not self.sabio_client:
            self.logger.error("SABIO-RK client not available")
            return None
        
        identifiers = transition_info.get('identifiers', {})
        
        # Try EC number first (most reliable)
        ec_number = identifiers.get('ec_number')
        if ec_number:
            result = self.sabio_client.query_by_ec_number(ec_number, organism)
            if result:
                return result
        
        # Try KEGG reaction ID
        reaction_id = identifiers.get('reaction_id')
        if reaction_id:
            result = self.sabio_client.query_by_reaction_id(reaction_id)
            if result:
                return result
        
        # No results
        self.logger.debug(f"[SABIO-RK] No data found for {transition_info['transition_id']}")
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
        for i, transition_info in enumerate(enrichable, 1):
            try:
                self.logger.info(f"[SABIO-RK] Querying transition {i}/{total}: {transition_info['transition_id']}")
                sabio_result = self.query_for_transition(transition_info, organism)
                
                if sabio_result:
                    results.append({
                        **transition_info,
                        'sabio_data': sabio_result
                    })
                
                # Add small delay every batch_size queries to avoid overwhelming API
                if i % batch_size == 0 and i < total:
                    self.logger.debug(f"[SABIO-RK] Completed batch {i//batch_size}, pausing 2 seconds...")
                    time.sleep(2)  # 2 second pause between batches
                
            except Exception as e:
                self.logger.error(f"[SABIO-RK] Error querying {transition_info['transition_id']}: {e}")
                continue
        
        self.logger.info(f"[SABIO-RK] Found data for {len(results)}/{total} transitions")
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
        transition = transition_info['transition']
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
                # Apply parameter
                metadata[param_type] = param_value['value']
                metadata[f'{param_type}_source'] = 'sabio_rk_enriched'
                metadata[f'{param_type}_units'] = param_value.get('units', '')
                applied.append(param_type)
        
        # Update transition metadata
        transition.metadata = metadata
        
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
        
        Args:
            enrichment_results: List of enrichment results from query_all_transitions()
            selected_transitions: List of transition IDs to enrich
            override_kegg: Whether to override KEGG heuristics
            override_sbml: Whether to override SBML curated data
        
        Returns:
            Dict with summary statistics
        """
        success_count = 0
        failed_count = 0
        skipped_count = 0
        
        for result in enrichment_results:
            transition_id = result['transition_id']
            
            if transition_id not in selected_transitions:
                continue
            
            # Get parameters from SABIO-RK result
            sabio_data = result.get('sabio_data', {})
            parameters = sabio_data.get('parameters', [])
            
            if not parameters:
                skipped_count += 1
                continue
            
            # Group parameters by type and select best values
            selected_params = self._select_best_parameters(parameters)
            
            if not selected_params:
                skipped_count += 1
                continue
            
            # Apply parameters
            success, message = self.apply_parameters(
                result,
                selected_params,
                override_kegg,
                override_sbml
            )
            
            if success:
                success_count += 1
                self.logger.info(f"[SABIO-RK] ✓ {transition_id}: {message}")
            else:
                failed_count += 1
                self.logger.warning(f"[SABIO-RK] ✗ {transition_id}: {message}")
        
        return {
            'success': success_count,
            'failed': failed_count,
            'skipped': skipped_count,
            'total': len(selected_transitions)
        }
    
    def _select_best_parameters(self, parameters: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Select best parameter values from SABIO-RK results.
        
        When multiple values exist for the same parameter type,
        selects based on criteria (e.g., median value, most common organism).
        
        Args:
            parameters: List of parameter dicts from SABIO-RK
        
        Returns:
            Dict with selected parameters {param_type: {value, units}}
        """
        # Group parameters by type
        by_type = {}
        for param in parameters:
            param_type = param.get('parameter_type')
            if param_type and param_type != 'other':
                if param_type not in by_type:
                    by_type[param_type] = []
                by_type[param_type].append(param)
        
        # Select best value for each type (use median)
        selected = {}
        for param_type, param_list in by_type.items():
            values = [p['value'] for p in param_list]
            if values:
                # Use median value
                values.sorted()
                median_value = values[len(values) // 2]
                
                # Find parameter with median value
                for p in param_list:
                    if p['value'] == median_value:
                        selected[param_type] = {
                            'value': p['value'],
                            'units': p.get('units', '')
                        }
                        break
        
        return selected


def create_sabio_rk_controller() -> SabioRKEnrichmentController:
    """Create SABIO-RK enrichment controller instance.
    
    Returns:
        SabioRKEnrichmentController instance
    """
    return SabioRKEnrichmentController()
