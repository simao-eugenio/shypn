"""
Heuristic Parameters Controller

Minimal controller for integrating type-aware parameter inference
into the Pathway Operations panel.

Author: Shypn Development Team
Date: November 2025
"""

from typing import Dict, List, Optional, Any
import logging

from ..inference import HeuristicInferenceEngine
from ..models import InferenceResult


class HeuristicParametersController:
    """Controller for heuristic parameter inference.
    
    This controller bridges the inference engine with the UI,
    following the clean architecture pattern used in crossfetch.
    """
    
    def __init__(self, model_canvas_loader=None):
        """Initialize controller.
        
        Args:
            model_canvas_loader: Reference to model canvas loader
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.model_canvas_loader = model_canvas_loader
        
        # Initialize inference engine (fast mode by default)
        self.inference_engine = HeuristicInferenceEngine(use_background_fetch=False)
        
        # Cache for results
        self._results_cache: Dict[str, InferenceResult] = {}
    
    def set_fetch_mode(self, use_background_fetch: bool):
        """Set database fetching mode.
        
        Args:
            use_background_fetch: If True, fetch from databases; if False, use fast heuristics
        """
        self.inference_engine.use_background_fetch = use_background_fetch
        self.logger.info(f"Database fetch mode: {'Enhanced' if use_background_fetch else 'Fast'}")
    
    def analyze_model(self, organism: str = "Homo sapiens") -> Dict[str, List[InferenceResult]]:
        """Analyze current model and classify transitions by type.
        
        Args:
            organism: Target organism for parameter inference
            
        Returns:
            Dictionary mapping transition types to inference results
        """
        if not self.model_canvas_loader:
            self.logger.error("No model canvas loader available")
            return {}
        
        # Get current drawing area
        drawing_area = self.model_canvas_loader.get_current_document()
        if not drawing_area:
            self.logger.error("No active document")
            return {}
        
        # Get document model
        canvas_manager = self.model_canvas_loader.canvas_managers.get(drawing_area)
        if not canvas_manager:
            self.logger.error("No canvas manager for current document")
            return {}
        
        document_model = canvas_manager.to_document_model()
        if not document_model:
            self.logger.error("Failed to get document model")
            return {}
        
        # Classify transitions
        results = {
            'immediate': [],
            'timed': [],
            'stochastic': [],
            'continuous': [],
            'unknown': []
        }
        
        # Attach arcs to transitions for stoichiometry analysis
        for transition in document_model.transitions:
            # Find input arcs (Place → Transition)
            input_arcs = [arc for arc in document_model.arcs 
                         if hasattr(arc, 'target') and arc.target == transition]
            
            # Find output arcs (Transition → Place)
            output_arcs = [arc for arc in document_model.arcs 
                          if hasattr(arc, 'source') and arc.source == transition]
            
            # Attach as properties
            transition.input_arcs = input_arcs
            transition.output_arcs = output_arcs
        
        # Process each transition
        for transition in document_model.transitions:
            try:
                result = self.inference_engine.infer_parameters(transition, organism)
                
                # Cache result
                self._results_cache[result.transition_id] = result
                
                # Categorize by type
                type_key = result.parameters.transition_type.value
                if type_key in results:
                    results[type_key].append(result)
                else:
                    results['unknown'].append(result)
                    
            except Exception as e:
                self.logger.error(f"Error inferring parameters for {transition.id}: {e}")
        
        return results
    
    def infer_single(self, transition_id: str, organism: str = "Homo sapiens") -> Optional[InferenceResult]:
        """Infer parameters for a single transition.
        
        Args:
            transition_id: Transition ID
            organism: Target organism
            
        Returns:
            InferenceResult or None if failed
        """
        # Check cache first
        if transition_id in self._results_cache:
            return self._results_cache[transition_id]
        
        # Get transition from model
        drawing_area = self.model_canvas_loader.get_current_document()
        if not drawing_area:
            return None
        
        canvas_manager = self.model_canvas_loader.canvas_managers.get(drawing_area)
        if not canvas_manager:
            return None
        
        document_model = canvas_manager.to_document_model()
        if not document_model:
            return None
        
        # Find transition
        transition = None
        for t in document_model.transitions:
            if t.id == transition_id:
                transition = t
                break
        
        if not transition:
            self.logger.error(f"Transition {transition_id} not found")
            return None
        
        # Attach arcs for stoichiometry analysis
        transition.input_arcs = [arc for arc in document_model.arcs 
                                if hasattr(arc, 'target') and arc.target == transition]
        transition.output_arcs = [arc for arc in document_model.arcs 
                                 if hasattr(arc, 'source') and arc.source == transition]
        
        # Infer parameters
        try:
            result = self.inference_engine.infer_parameters(transition, organism)
            self._results_cache[transition_id] = result
            return result
        except Exception as e:
            self.logger.error(f"Error inferring parameters: {e}")
            return None
    
    def apply_parameters(self, transition_id: str, parameters: Dict[str, Any]) -> bool:
        """Apply inferred parameters to a transition.
        
        Args:
            transition_id: Transition ID
            parameters: Parameters dictionary to apply
            
        Returns:
            True if successful
        """
        try:
            # Get canvas manager
            drawing_area = self.model_canvas_loader.get_current_document()
            if not drawing_area:
                self.logger.error("No active document")
                return False
            
            canvas_manager = self.model_canvas_loader.canvas_managers.get(drawing_area)
            if not canvas_manager:
                self.logger.error("No canvas manager for current document")
                return False
            
            # Find transition in the CANVAS (not document_model)
            # canvas_manager.transitions contains the actual canvas transition objects
            transition = None
            for t in canvas_manager.transitions:
                if str(t.id) == str(transition_id):
                    transition = t
                    break
            
            if not transition:
                self.logger.error(f"Transition {transition_id} not found in canvas")
                return False
            
            # Apply parameters based on type
            transition_type = parameters.get('transition_type')
            params = parameters.get('parameters', {})
            
            self.logger.info(f"Applying {transition_type} parameters to {transition_id}: {params}")
            
            if transition_type == 'immediate':
                if 'priority' in params:
                    transition.priority = params['priority']
                if 'weight' in params:
                    transition.weight = params['weight']
                    
            elif transition_type == 'timed':
                if 'delay' in params:
                    transition.delay = params['delay']
                # Also set rate for compatibility
                transition.rate = params.get('delay', transition.rate)
                    
            elif transition_type == 'stochastic':
                if 'lambda' in params:
                    # Lambda is stored as rate
                    transition.rate = params['lambda']
                if 'rate_function' in params:
                    if not hasattr(transition, 'properties'):
                        transition.properties = {}
                    transition.properties['rate_function'] = params['rate_function']
                    
            elif transition_type == 'continuous':
                # Store parameters in properties dict
                if not hasattr(transition, 'properties'):
                    transition.properties = {}
                
                if 'vmax' in params and params['vmax'] is not None:
                    transition.properties['vmax'] = params['vmax']
                if 'km' in params and params['km'] is not None:
                    transition.properties['km'] = params['km']
                if 'kcat' in params and params['kcat'] is not None:
                    transition.properties['kcat'] = params['kcat']
                if 'ki' in params and params['ki'] is not None:
                    transition.properties['ki'] = params['ki']
                
                # Build or use rate_function
                if 'rate_function' in params and params['rate_function']:
                    transition.properties['rate_function'] = params['rate_function']
                elif params.get('vmax') and params.get('km'):
                    # Auto-generate rate_function using actual substrate place name
                    # Get substrate place from transition's input arcs
                    substrate_places = []
                    for arc in getattr(transition, 'input_arcs', []):
                        if hasattr(arc, 'source'):
                            substrate_places.append(arc.source)
                    
                    if substrate_places:
                        substrate_name = substrate_places[0].name if hasattr(substrate_places[0], 'name') else f"P{substrate_places[0].id}"
                        rate_function = f"michaelis_menten({substrate_name}, {params['vmax']}, {params['km']})"
                        transition.properties['rate_function'] = rate_function
                        self.logger.info(f"Generated rate_function: {rate_function}")
                    else:
                        self.logger.warning(f"No substrate place found for {transition_id}, using constant rate")
                        transition.rate = params['vmax']
            
            # Mark document as dirty (manager has mark_dirty directly)
            canvas_manager.mark_dirty()
            
            # Refresh canvas
            drawing_area.queue_draw()
            
            # Store in database for future use
            self._store_applied_parameters(transition_id, transition_type, parameters)
            
            self.logger.info(f"Successfully applied parameters to {transition_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error applying parameters to {transition_id}: {e}", exc_info=True)
            return False
    
    def clear_cache(self):
        """Clear results cache."""
        self._results_cache.clear()
    
    def _store_applied_parameters(self, 
                                  transition_id: str,
                                  transition_type: str,
                                  parameters: Dict[str, Any]):
        """Store applied parameters in database for future use.
        
        Args:
            transition_id: Transition ID
            transition_type: Type of transition
            parameters: Full parameters dict
        """
        try:
            params = parameters.get('parameters', {})
            
            # Only store if confidence is reasonable and source is not just heuristic
            confidence = parameters.get('confidence_score', 0.0)
            source = parameters.get('source', 'Heuristic')
            
            # Store parameter in database
            param_id = self.inference_engine.db.store_parameter(
                transition_type=transition_type,
                organism=parameters.get('organism', 'Homo sapiens'),
                parameters=params,
                source=source,
                confidence_score=confidence,
                biological_semantics=parameters.get('biological_semantics'),
                ec_number=parameters.get('ec_number'),
                enzyme_name=parameters.get('enzyme_name'),
                reaction_id=parameters.get('reaction_id'),
                temperature=parameters.get('temperature'),
                ph=parameters.get('ph'),
                notes=parameters.get('notes')
            )
            
            # Record enrichment
            pathway_id = getattr(self.model_canvas_loader, 'current_pathway_id', None)
            pathway_name = getattr(self.model_canvas_loader, 'current_pathway_name', None)
            
            self.inference_engine.db.record_enrichment(
                parameter_id=param_id,
                transition_id=transition_id,
                pathway_id=pathway_id,
                pathway_name=pathway_name,
                reaction_id=parameters.get('reaction_id')
            )
            
            self.logger.debug(f"Stored parameters for {transition_id} in database (ID: {param_id})")
            
        except Exception as e:
            self.logger.warning(f"Failed to store parameters in database: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get inference engine and database statistics.
        
        Returns:
            Dictionary with statistics
        """
        stats = {
            'cache_size': len(self._results_cache)
        }
        
        # Add database statistics
        try:
            db_stats = self.inference_engine.db.get_statistics()
            stats['database'] = db_stats
        except Exception as e:
            self.logger.warning(f"Failed to get database statistics: {e}")
        
        # Add fetcher statistics if available
        if self.inference_engine.sabio_rk_fetcher:
            try:
                stats['fetcher_stats'] = self.inference_engine.sabio_rk_fetcher.get_statistics()
            except Exception as e:
                self.logger.warning(f"Failed to get fetcher statistics: {e}")
        
        return stats
