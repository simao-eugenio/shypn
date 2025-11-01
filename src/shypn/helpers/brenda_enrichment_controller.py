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
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple

from ..data.enrichment_document import EnrichmentDocument
from ..data.project_models import Project


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
        
        transitions = []
        
        # TODO: Access transitions from canvas
        # This depends on the canvas architecture
        # For now, return empty list (will be implemented when wiring to UI)
        
        return transitions
    
    # ========================================================================
    # BRENDA API Integration (Future)
    # ========================================================================
    
    def fetch_from_brenda_api(self, ec_number: str, organism: str = None) -> Optional[Dict[str, Any]]:
        """Fetch kinetic data from BRENDA API.
        
        This will be implemented when BRENDA credentials are available.
        Requires BRENDA SOAP API client with authentication.
        
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
        # TODO: Implement BRENDA SOAP API integration
        # Requires zeep library and BRENDA credentials
        
        
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
        
    
    def apply_enrichment_to_transition(self, transition_id: str, parameters: Dict[str, Any]):
        """Apply BRENDA enrichment data to a specific transition.
        
        Args:
            transition_id: ID of transition to enrich
            parameters: Dict of parameters to add (km, kcat, ki, etc.)
        """
        if not self.current_enrichment:
            return
        
        # Track transition enrichment
        self.current_enrichment.add_transition(transition_id)
        
        # Track parameters added
        for param_type, value in parameters.items():
            self.current_enrichment.add_parameter(param_type)
        
        # TODO: Actually apply to canvas transition
        # This depends on canvas/model architecture
        
    
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
        
        # Query BRENDA for each EC number
        brenda_data = {}
        for ec_number in ec_numbers:
            data = self.fetch_from_brenda_api(ec_number, organism)
            if data:
                brenda_data[ec_number] = data
        
        # Match and apply enrichments
        enriched_count = 0
        for transition in transitions:
            ec = transition.get('ec_number')
            if ec in brenda_data:
                if override_existing or not transition.get('has_kinetics'):
                    # Apply enrichment
                    params = self._extract_parameters(brenda_data[ec])
                    self.apply_enrichment_to_transition(transition['id'], params)
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
            if ec and ec in brenda_data:
                if override_existing or not transition.get('has_kinetics'):
                    # Apply enrichment
                    params = self._extract_parameters(brenda_data[ec])
                    self.apply_enrichment_to_transition(transition['id'], params)
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
            Dict of parameter name -> value
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
        
        # Extract Ki values
        ki_values = brenda_entry.get('ki_values', [])
        if ki_values and isinstance(ki_values, list) and len(ki_values) > 0:
            params['ki'] = ki_values[0].get('value', 0.0)
        
        return params
