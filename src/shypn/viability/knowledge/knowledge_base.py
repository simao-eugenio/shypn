"""Model Knowledge Base - Unified Intelligence Repository.

The ModelKnowledgeBase aggregates knowledge from all Shypn panels and modules
to enable intelligent model repair and inference.

Author: Simão Eugénio
Date: November 9, 2025
"""

import json
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path

from .data_structures import (
    PlaceKnowledge,
    TransitionKnowledge,
    ArcKnowledge,
    PInvariant,
    TInvariant,
    Siphon,
    PathwayInfo,
    CompoundInfo,
    ReactionInfo,
    KineticParams,
    SimulationTrace,
    Issue,
    RepairSuggestion
)


class ModelKnowledgeBase:
    """Unified knowledge repository for a single Petri Net model.
    
    Aggregates knowledge from:
    - Topology Panel (structural/behavioral analysis)
    - Pathway Panel (biological context)
    - BRENDA (biochemical parameters)
    - Analyses Panel (dynamic behavior)
    - User annotations
    
    Provides:
    - Update methods (called by panels to contribute knowledge)
    - Query methods (called by Viability Panel to retrieve knowledge)
    - Inference methods (called by inference engines for intelligent suggestions)
    - Persistence (save/load knowledge with model)
    """
    
    def __init__(self, model=None):
        """Initialize knowledge base for a model.
        
        Args:
            model: ShypnModel instance (can be None initially)
        """
        self.model = model
        
        # ====================================================================
        # 1. STRUCTURAL KNOWLEDGE (Petri Net graph)
        # ====================================================================
        self.places: Dict[str, PlaceKnowledge] = {}
        self.transitions: Dict[str, TransitionKnowledge] = {}
        self.arcs: Dict[str, ArcKnowledge] = {}
        
        # ====================================================================
        # 2. BEHAVIORAL KNOWLEDGE (Topology results)
        # ====================================================================
        self.p_invariants: List[PInvariant] = []
        self.t_invariants: List[TInvariant] = []
        self.siphons: List[Siphon] = []
        self.traps: List[Siphon] = []  # Same structure as siphons
        self.liveness_status: Dict[str, str] = {}  # transition_id -> liveness level
        self.deadlock_states: List[Dict[str, int]] = []  # List of deadlock markings
        self.boundedness: Dict[str, int] = {}  # place_id -> bound value
        
        # ====================================================================
        # 3. BIOLOGICAL KNOWLEDGE (KEGG/SBML)
        # ====================================================================
        self.pathway_info: Optional[PathwayInfo] = None
        self.compounds: Dict[str, CompoundInfo] = {}  # compound_id -> info
        self.reactions: Dict[str, ReactionInfo] = {}  # reaction_id -> info
        
        # ====================================================================
        # 4. BIOCHEMICAL KNOWLEDGE (BRENDA)
        # ====================================================================
        self.kinetic_parameters: Dict[str, KineticParams] = {}  # transition_id -> params
        self.enzyme_data: Dict[str, Dict] = {}  # ec_number -> enzyme data
        
        # ====================================================================
        # 5. DYNAMIC KNOWLEDGE (Simulation)
        # ====================================================================
        self.simulation_traces: List[SimulationTrace] = []
        self.steady_states: List[Dict[str, int]] = []
        
        # ====================================================================
        # 6. ISSUE DATABASE
        # ====================================================================
        self.issues: List[Issue] = []
        
        # ====================================================================
        # 7. METADATA
        # ====================================================================
        self.last_updated: Dict[str, datetime] = {}  # domain -> timestamp
        self.confidence: Dict[str, float] = {}  # knowledge_item -> confidence score
        self.version = "1.0"
    
    # ========================================================================
    # UPDATE METHODS (Called by Panels)
    # ========================================================================
    
    # === TOPOLOGY PANEL ===
    
    def update_topology_structural(self, places: List, transitions: List, arcs: List):
        """Update structural knowledge from Petri Net graph.
        
        Args:
            places: List of place objects from model
            transitions: List of transition objects from model
            arcs: List of arc objects from model
        """
        # Update places
        for place in places:
            place_id = getattr(place, 'id', str(place))
            if place_id not in self.places:
                self.places[place_id] = PlaceKnowledge(
                    place_id=place_id,
                    label=getattr(place, 'label', ''),
                    current_marking=getattr(place, 'tokens', 0)
                )
            else:
                # Update existing
                self.places[place_id].current_marking = getattr(place, 'tokens', 0)
        
        # Update transitions
        for transition in transitions:
            trans_id = getattr(transition, 'id', str(transition))
            if trans_id not in self.transitions:
                self.transitions[trans_id] = TransitionKnowledge(
                    transition_id=trans_id,
                    label=getattr(transition, 'label', '')
                )
        
        # Update arcs
        for arc in arcs:
            arc_id = getattr(arc, 'id', str(arc))
            if arc_id not in self.arcs:
                self.arcs[arc_id] = ArcKnowledge(
                    arc_id=arc_id,
                    source_id=getattr(arc, 'source_id', ''),
                    target_id=getattr(arc, 'target_id', ''),
                    arc_type=getattr(arc, 'arc_type', 'unknown'),
                    current_weight=getattr(arc, 'weight', 1)
                )
        
        self.last_updated['structural'] = datetime.now()
    
    def update_p_invariants(self, invariants: List[PInvariant]):
        """Update P-invariants from topology analysis.
        
        Args:
            invariants: List of P-invariant objects
        """
        self.p_invariants = invariants
        
        # Update place knowledge - mark which invariants each place belongs to
        for idx, inv in enumerate(invariants):
            for place_id in inv.place_ids:
                if place_id in self.places:
                    if idx not in self.places[place_id].in_p_invariants:
                        self.places[place_id].in_p_invariants.append(idx)
        
        self.last_updated['p_invariants'] = datetime.now()
    
    def update_t_invariants(self, invariants: List[TInvariant]):
        """Update T-invariants from topology analysis.
        
        Args:
            invariants: List of T-invariant objects
        """
        self.t_invariants = invariants
        
        # Update transition knowledge
        for idx, inv in enumerate(invariants):
            for trans_id in inv.transition_ids:
                if trans_id in self.transitions:
                    if idx not in self.transitions[trans_id].in_t_invariants:
                        self.transitions[trans_id].in_t_invariants.append(idx)
        
        self.last_updated['t_invariants'] = datetime.now()
    
    def update_siphons_traps(self, siphons: List[Siphon], traps: List[Siphon]):
        """Update siphons and traps from topology analysis.
        
        Args:
            siphons: List of siphon objects
            traps: List of trap objects
        """
        self.siphons = siphons
        self.traps = traps
        
        # Update place knowledge
        for idx, siphon in enumerate(siphons):
            for place_id in siphon.place_ids:
                if place_id in self.places:
                    if idx not in self.places[place_id].in_siphons:
                        self.places[place_id].in_siphons.append(idx)
        
        for idx, trap in enumerate(traps):
            for place_id in trap.place_ids:
                if place_id in self.places:
                    if idx not in self.places[place_id].in_traps:
                        self.places[place_id].in_traps.append(idx)
        
        self.last_updated['siphons_traps'] = datetime.now()
    
    def update_liveness(self, liveness_results: Dict[str, str]):
        """Update liveness analysis results.
        
        Args:
            liveness_results: Dict mapping transition_id -> liveness level
        """
        self.liveness_status = liveness_results
        
        # Update transition knowledge
        for trans_id, level in liveness_results.items():
            if trans_id in self.transitions:
                self.transitions[trans_id].liveness_level = level
                self.transitions[trans_id].must_be_live = (level == "dead")
        
        self.last_updated['liveness'] = datetime.now()
    
    def update_deadlocks(self, deadlock_states: List[Dict[str, int]]):
        """Update deadlock analysis results.
        
        Args:
            deadlock_states: List of markings that cause deadlock
        """
        self.deadlock_states = deadlock_states
        self.last_updated['deadlocks'] = datetime.now()
    
    def update_boundedness(self, boundedness: Dict[str, int]):
        """Update boundedness analysis results.
        
        Args:
            boundedness: Dict mapping place_id -> bound value (or -1 if unbounded)
        """
        self.boundedness = boundedness
        
        # Update place knowledge
        for place_id, bound in boundedness.items():
            if place_id in self.places:
                self.places[place_id].is_bounded = (bound >= 0)
                self.places[place_id].bound_value = bound if bound >= 0 else None
        
        self.last_updated['boundedness'] = datetime.now()
    
    # === PATHWAY PANEL ===
    
    def update_pathway_metadata(self, pathway_info: PathwayInfo):
        """Update pathway context from KEGG/SBML import.
        
        Args:
            pathway_info: PathwayInfo object with metadata
        """
        self.pathway_info = pathway_info
        self.last_updated['pathway'] = datetime.now()
    
    def update_compounds(self, compounds: Dict[str, CompoundInfo]):
        """Update compound information.
        
        Args:
            compounds: Dict mapping compound_id -> CompoundInfo
        """
        self.compounds.update(compounds)
        self.last_updated['compounds'] = datetime.now()
    
    def update_reactions(self, reactions: Dict[str, ReactionInfo]):
        """Update reaction information.
        
        Args:
            reactions: Dict mapping reaction_id -> ReactionInfo
        """
        self.reactions.update(reactions)
        self.last_updated['reactions'] = datetime.now()
    
    def update_compound_info(self, compound_id: str, compound_data: dict):
        """Update compound information from pathway metadata.
        
        Args:
            compound_id: KEGG compound ID (e.g., "cpd:C00031")
            compound_data: Dict with keys: name, formula, molecular_weight, place_ids
        """
        from .data_structures import CompoundInfo
        
        if compound_id not in self.compounds:
            # Create new CompoundInfo
            self.compounds[compound_id] = CompoundInfo(
                compound_id=compound_id,
                name=compound_data.get('name', ''),
                formula=compound_data.get('formula'),
                molecular_weight=compound_data.get('molecular_weight')
            )
        else:
            # Update existing
            if compound_data.get('name'):
                self.compounds[compound_id].name = compound_data['name']
            if compound_data.get('formula'):
                self.compounds[compound_id].formula = compound_data['formula']
            if compound_data.get('molecular_weight'):
                self.compounds[compound_id].molecular_weight = compound_data['molecular_weight']
        
        # Link to places
        place_ids = compound_data.get('place_ids', [])
        for place_id in place_ids:
            if place_id in self.places:
                self.places[place_id].compound_id = compound_id
                self.places[place_id].compound_name = self.compounds[compound_id].name
        
        self.last_updated['compounds'] = datetime.now()
    
    def update_reaction_info(self, reaction_id: str, reaction_data: dict):
        """Update reaction information from pathway metadata.
        
        Args:
            reaction_id: KEGG reaction ID (e.g., "R00200")
            reaction_data: Dict with keys: name, ec_number, ec_numbers, reversible, transition_id
        """
        from .data_structures import ReactionInfo
        
        if reaction_id not in self.reactions:
            # Create new ReactionInfo
            self.reactions[reaction_id] = ReactionInfo(
                reaction_id=reaction_id,
                name=reaction_data.get('name', ''),
                ec_number=reaction_data.get('ec_number'),
                reversible=reaction_data.get('reversible', False)
            )
        else:
            # Update existing
            if reaction_data.get('name'):
                self.reactions[reaction_id].name = reaction_data['name']
            if reaction_data.get('ec_number'):
                self.reactions[reaction_id].ec_number = reaction_data['ec_number']
            if 'reversible' in reaction_data:
                self.reactions[reaction_id].reversible = reaction_data['reversible']
        
        # Link to transition
        transition_id = reaction_data.get('transition_id')
        if transition_id and transition_id in self.transitions:
            self.transitions[transition_id].reaction_id = reaction_id
            self.transitions[transition_id].reaction_name = self.reactions[reaction_id].name
            # Handle both single ec_number and list of ec_numbers
            ec_numbers = reaction_data.get('ec_numbers', [])
            if ec_numbers:
                self.transitions[transition_id].ec_number = ec_numbers[0]
            elif reaction_data.get('ec_number'):
                self.transitions[transition_id].ec_number = reaction_data['ec_number']
        
        self.last_updated['reactions'] = datetime.now()
    
    def link_place_to_compound(self, place_id: str, compound_id: str):
        """Link a place to a KEGG compound.
        
        Args:
            place_id: ID of the place
            compound_id: KEGG compound ID
        """
        if place_id in self.places:
            self.places[place_id].compound_id = compound_id
            if compound_id in self.compounds:
                self.places[place_id].compound_name = self.compounds[compound_id].name
                # Copy basal concentration if available
                if self.compounds[compound_id].basal_concentration:
                    self.places[place_id].basal_concentration = self.compounds[compound_id].basal_concentration
    
    def link_transition_to_reaction(self, transition_id: str, reaction_id: str):
        """Link a transition to a KEGG reaction.
        
        Args:
            transition_id: ID of the transition
            reaction_id: KEGG reaction ID
        """
        if transition_id in self.transitions:
            self.transitions[transition_id].reaction_id = reaction_id
            if reaction_id in self.reactions:
                reaction = self.reactions[reaction_id]
                self.transitions[transition_id].reaction_name = reaction.name
                self.transitions[transition_id].ec_number = reaction.ec_number
    
    # === BRENDA INTEGRATION ===
    
    def update_kinetic_parameters(self, transition_id: str, params: KineticParams):
        """Update kinetic parameters from BRENDA query.
        
        Args:
            transition_id: ID of the transition
            params: KineticParams object
        """
        self.kinetic_parameters[transition_id] = params
        
        # Update transition knowledge
        if transition_id in self.transitions:
            self.transitions[transition_id].km_values = params.km_values
            self.transitions[transition_id].vmax = params.vmax
            self.transitions[transition_id].kcat = params.kcat
        
        self.last_updated['kinetics'] = datetime.now()
    
    def update_basal_concentrations(self, concentrations: Dict[str, float]):
        """Update basal metabolite concentrations.
        
        Args:
            concentrations: Dict mapping compound_id -> concentration (mM)
        """
        for compound_id, conc in concentrations.items():
            if compound_id in self.compounds:
                self.compounds[compound_id].basal_concentration = conc
            
            # Update linked places
            for place in self.places.values():
                if place.compound_id == compound_id:
                    place.basal_concentration = conc
        
        self.last_updated['concentrations'] = datetime.now()
    
    # === ANALYSES PANEL ===
    
    def add_simulation_trace(self, trace: SimulationTrace):
        """Add simulation results.
        
        Args:
            trace: SimulationTrace object
        """
        self.simulation_traces.append(trace)
        
        # Update place knowledge with simulation data
        for place_id, token_trace in trace.place_traces.items():
            if place_id in self.places:
                self.places[place_id].token_history = token_trace
                if token_trace:
                    self.places[place_id].avg_tokens = sum(token_trace) / len(token_trace)
                    self.places[place_id].peak_tokens = max(token_trace)
        
        # Update transition knowledge
        for trans_id, firing_times in trace.transition_firings.items():
            if trans_id in self.transitions:
                self.transitions[trans_id].firing_count = len(firing_times)
                if len(trace.time_points) > 0:
                    total_time = trace.time_points[-1]
                    self.transitions[trans_id].avg_firing_rate = len(firing_times) / total_time if total_time > 0 else 0
        
        self.last_updated['simulation'] = datetime.now()
    
    def update_current_marking(self, marking: Dict[str, int]):
        """Update current model state.
        
        Args:
            marking: Dict mapping place_id -> token count
        """
        for place_id, tokens in marking.items():
            if place_id in self.places:
                self.places[place_id].current_marking = tokens
        
        self.last_updated['marking'] = datetime.now()
    
    # === ISSUE MANAGEMENT ===
    
    def add_issue(self, issue: Issue):
        """Register a detected issue.
        
        Args:
            issue: Issue object
        """
        # Check if issue already exists
        for existing in self.issues:
            if existing.issue_id == issue.issue_id:
                # Update existing issue
                existing.description = issue.description
                existing.timestamp = datetime.now()
                return
        
        # Add new issue
        self.issues.append(issue)
        self.last_updated['issues'] = datetime.now()
    
    def add_suggestion(self, issue_id: str, suggestion: RepairSuggestion):
        """Add a repair suggestion to an issue.
        
        Args:
            issue_id: ID of the issue
            suggestion: RepairSuggestion object
        """
        for issue in self.issues:
            if issue.issue_id == issue_id:
                issue.suggestions.append(suggestion)
                break
    
    # ========================================================================
    # QUERY METHODS (Called by Viability Panel)
    # ========================================================================
    
    # === STRUCTURAL QUERIES ===
    
    def get_place(self, place_id: str) -> Optional[PlaceKnowledge]:
        """Get complete knowledge about a place."""
        return self.places.get(place_id)
    
    def get_transition(self, transition_id: str) -> Optional[TransitionKnowledge]:
        """Get complete knowledge about a transition."""
        return self.transitions.get(transition_id)
    
    def get_dead_transitions(self) -> List[str]:
        """Get all dead transitions."""
        return [tid for tid, level in self.liveness_status.items() if level == "dead"]
    
    def get_unbounded_places(self) -> List[str]:
        """Get all unbounded places."""
        return [pid for pid, bound in self.boundedness.items() if bound < 0]
    
    # === BIOLOGICAL QUERIES ===
    
    def get_compound_for_place(self, place_id: str) -> Optional[CompoundInfo]:
        """Get biological compound info for a place."""
        place = self.places.get(place_id)
        if place and place.compound_id:
            return self.compounds.get(place.compound_id)
        return None
    
    def get_reaction_for_transition(self, transition_id: str) -> Optional[ReactionInfo]:
        """Get biological reaction info for a transition."""
        trans = self.transitions.get(transition_id)
        if trans and trans.reaction_id:
            return self.reactions.get(trans.reaction_id)
        return None
    
    def get_basal_concentration(self, place_id: str) -> Optional[float]:
        """Get basal concentration for a place's compound."""
        place = self.places.get(place_id)
        if place:
            return place.basal_concentration
        return None
    
    # === BIOCHEMICAL QUERIES ===
    
    def get_kinetic_params(self, transition_id: str) -> Optional[KineticParams]:
        """Get kinetic parameters for a transition."""
        return self.kinetic_parameters.get(transition_id)
    
    def get_km_value(self, transition_id: str, substrate_place_id: str) -> Optional[float]:
        """Get Km value for a specific substrate."""
        params = self.kinetic_parameters.get(transition_id)
        if params:
            return params.km_values.get(substrate_place_id)
        return None
    
    # === BEHAVIORAL QUERIES ===
    
    def get_conserved_places(self, place_id: str) -> List[str]:
        """Get places conserved with this place (same P-invariant)."""
        place = self.places.get(place_id)
        if not place or not place.in_p_invariants:
            return []
        
        # Get all places in the same invariants
        conserved = set()
        for inv_idx in place.in_p_invariants:
            if inv_idx < len(self.p_invariants):
                conserved.update(self.p_invariants[inv_idx].place_ids)
        
        # Remove the place itself
        conserved.discard(place_id)
        return list(conserved)
    
    def get_cycle_transitions(self, transition_id: str) -> List[str]:
        """Get transitions in same T-invariant cycle."""
        trans = self.transitions.get(transition_id)
        if not trans or not trans.in_t_invariants:
            return []
        
        # Get all transitions in the same cycles
        cycle_trans = set()
        for inv_idx in trans.in_t_invariants:
            if inv_idx < len(self.t_invariants):
                cycle_trans.update(self.t_invariants[inv_idx].transition_ids)
        
        # Remove the transition itself
        cycle_trans.discard(transition_id)
        return list(cycle_trans)
    
    def is_in_siphon(self, place_id: str) -> bool:
        """Check if place is in any siphon."""
        place = self.places.get(place_id)
        return bool(place and place.in_siphons)
    
    # === ISSUE QUERIES ===
    
    def get_all_issues(self) -> List[Issue]:
        """Get all detected issues."""
        return self.issues
    
    def get_critical_issues(self) -> List[Issue]:
        """Get only critical issues."""
        return [issue for issue in self.issues if issue.severity == "critical"]
    
    def get_issues_for_element(self, element_id: str) -> List[Issue]:
        """Get all issues affecting an element."""
        return [issue for issue in self.issues if element_id in issue.affected_elements]
    
    # ========================================================================
    # INFERENCE METHODS (To be implemented in Phase 4)
    # ========================================================================
    
    def infer_initial_marking(self, place_id: str) -> Optional[int]:
        """Infer appropriate initial marking (STUB - Phase 4)."""
        # TODO: Implement inference logic
        place = self.places.get(place_id)
        if place and place.basal_concentration:
            # Simple heuristic: 1 token per 1 mM
            return int(place.basal_concentration)
        return None
    
    def infer_arc_weight(self, arc_id: str) -> Optional[int]:
        """Infer appropriate arc weight (STUB - Phase 4)."""
        # TODO: Implement inference logic
        arc = self.arcs.get(arc_id)
        if arc and arc.stoichiometry:
            return arc.stoichiometry
        return None
    
    def infer_firing_rate(self, transition_id: str) -> Optional[float]:
        """Infer appropriate firing rate (STUB - Phase 4)."""
        # TODO: Implement inference logic
        params = self.kinetic_parameters.get(transition_id)
        if params and params.vmax:
            return params.vmax
        return None
    
    def suggest_source_placement(self) -> List[Tuple[str, float]]:
        """Suggest where to add sources (STUB - Phase 4)."""
        # TODO: Implement inference logic
        suggestions = []
        for siphon in self.siphons:
            if not siphon.is_properly_marked and siphon.place_ids:
                # Suggest source at first place in siphon
                place_id = siphon.place_ids[0]
                rate = 0.1  # Default rate
                suggestions.append((place_id, rate))
        return suggestions
    
    # ========================================================================
    # PERSISTENCE
    # ========================================================================
    
    def save_to_file(self, filepath: str):
        """Save knowledge base to JSON file.
        
        Args:
            filepath: Path to save file (e.g., "model.shypn.kb.json")
        """
        # TODO: Implement serialization (Phase 1)
        print(f"[KB] Saving to {filepath} (not yet implemented)")
    
    @classmethod
    def load_from_file(cls, filepath: str) -> 'ModelKnowledgeBase':
        """Load knowledge base from JSON file.
        
        Args:
            filepath: Path to knowledge base file
            
        Returns:
            ModelKnowledgeBase instance
        """
        # TODO: Implement deserialization (Phase 1)
        print(f"[KB] Loading from {filepath} (not yet implemented)")
        return cls()


__all__ = ['ModelKnowledgeBase']
