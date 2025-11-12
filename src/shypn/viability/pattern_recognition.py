#!/usr/bin/env python3
"""Pattern Recognition for Model Viability Analysis.

Detects structural, biochemical, and kinetic patterns that indicate
model issues, then generates specific repair suggestions.

Architecture:
  Pattern Detection → Diagnosis → Repair Suggestion → Confidence Scoring

Author: Simão Eugénio
Date: November 11, 2025
"""

from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum


class PatternType(Enum):
    """Types of patterns that can be detected."""
    # Structural
    DEAD_END = "dead_end"
    BOTTLENECK = "bottleneck"
    UNUSED_PATH = "unused_path"
    SOURCE_NO_RATE = "source_no_rate"
    TIMING_CONFLICT = "timing_conflict"
    STEADY_STATE_TRAP = "steady_state_trap"
    
    # Biochemical
    STOICHIOMETRY_MISMATCH = "stoichiometry_mismatch"
    MISSING_COFACTOR = "missing_cofactor"
    REVERSIBILITY_ISSUE = "reversibility_issue"
    
    # Kinetic
    RATE_TOO_LOW = "rate_too_low"
    KM_MISMATCH = "km_mismatch"
    MISSING_SUBSTRATE_DEPENDENCE = "missing_substrate_dependence"
    PATHWAY_IMBALANCE = "pathway_imbalance"


@dataclass
class Pattern:
    """Base class for detected patterns."""
    pattern_type: PatternType
    confidence: float  # 0.0 - 1.0
    evidence: Dict[str, Any]
    affected_elements: List[str]  # IDs of affected places/transitions
    
    def __str__(self):
        return f"{self.pattern_type.value} (confidence={self.confidence:.2f})"


@dataclass
class RepairSuggestion:
    """Actionable repair suggestion."""
    action: str  # e.g., "add_output_transition", "update_arc_weight"
    target: str  # ID of element to modify
    description: str  # Human-readable explanation
    confidence: float
    parameters: Dict[str, Any]  # Action-specific parameters
    rationale: str  # Why this suggestion makes sense
    data_source: Optional[str] = None  # e.g., "KEGG", "BRENDA", "simulation"


# ============================================================================
# STRUCTURAL PATTERN DETECTION
# ============================================================================

class StructuralPatternDetector:
    """Detects structural/topological patterns."""
    
    def detect_dead_ends(self, kb) -> List[Pattern]:
        """Detect places with no output arcs that accumulate tokens.
        
        Pattern: Place receives tokens but cannot pass them forward.
        Evidence: No output arcs + current_marking > 0
        """
        patterns = []
        
        for place_id, place in kb.places.items():
            output_arcs = kb.get_output_arcs_for_place(place_id)
            
            if not output_arcs and place.current_marking > 0:
                patterns.append(Pattern(
                    pattern_type=PatternType.DEAD_END,
                    confidence=0.9,
                    evidence={
                        'current_tokens': place.current_marking,
                        'initial_tokens': place.initial_marking if hasattr(place, 'initial_marking') else 0,
                        'output_arcs': 0,
                        'compound': place.compound_name if place.compound_name else place.place_id
                    },
                    affected_elements=[place_id]
                ))
        
        return patterns
    
    def detect_bottlenecks(self, kb) -> List[Pattern]:
        """Detect places where tokens accumulate due to output constraints.
        
        Pattern: High token accumulation + high output arc weights
        Evidence: avg_tokens >> baseline AND output_weight > input_weight
        """
        patterns = []
        
        for place_id, place in kb.places.items():
            # Need simulation data to detect bottlenecks
            if not place.avg_tokens or place.avg_tokens <= 1:
                continue
            
            input_arcs = kb.get_input_arcs_for_place(place_id)
            output_arcs = kb.get_output_arcs_for_place(place_id)
            
            if not output_arcs:
                continue  # This is a dead-end, not a bottleneck
            
            input_weight = sum(arc.current_weight for arc in input_arcs) if input_arcs else 0
            output_weight = sum(arc.current_weight for arc in output_arcs)
            
            # Bottleneck: tokens accumulate AND output requirements are high
            # Use current_marking as baseline if available, otherwise use 1
            baseline = max(place.current_marking if place.current_marking > 0 else 1, 1)
            accumulation_ratio = place.avg_tokens / baseline
            weight_ratio = output_weight / max(input_weight, 1) if input_weight > 0 else output_weight
            
            if accumulation_ratio > 3.0 and weight_ratio > 1.5:
                patterns.append(Pattern(
                    pattern_type=PatternType.BOTTLENECK,
                    confidence=0.85,
                    evidence={
                        'avg_tokens': place.avg_tokens,
                        'current_marking': place.current_marking,
                        'accumulation_ratio': accumulation_ratio,
                        'input_weight': input_weight,
                        'output_weight': output_weight,
                        'weight_ratio': weight_ratio,
                        'compound': place.compound_name if place.compound_name else place.place_id
                    },
                    affected_elements=[place_id] + [arc.target_id for arc in output_arcs]
                ))
        
        return patterns
    
    def detect_unused_paths(self, kb) -> List[Pattern]:
        """Detect competing transitions where some never fire.
        
        Pattern: Multiple transitions with same inputs, but unequal usage
        Evidence: One fires frequently, others never fire
        """
        patterns = []
        
        # Group transitions by their input places
        input_groups = {}
        for trans_id in kb.transitions.keys():
            input_arcs = kb.get_input_arcs_for_transition(trans_id)
            input_set = frozenset(arc.source_id for arc in input_arcs)
            
            if input_set:  # Skip sources
                if input_set not in input_groups:
                    input_groups[input_set] = []
                input_groups[input_set].append(trans_id)
        
        # Check for groups with competing transitions
        for input_set, transitions in input_groups.items():
            if len(transitions) <= 1:
                continue
            
            firings = {t: kb.transitions[t].firing_count for t in transitions}
            max_firing = max(firings.values())
            min_firing = min(firings.values())
            
            # Pattern: One fires, others don't
            if max_firing > 0 and min_firing == 0:
                active = [t for t, f in firings.items() if f > 0]
                unused = [t for t, f in firings.items() if f == 0]
                
                patterns.append(Pattern(
                    pattern_type=PatternType.UNUSED_PATH,
                    confidence=0.75,
                    evidence={
                        'active_transitions': active,
                        'unused_transitions': unused,
                        'max_firings': max_firing,
                        'input_places': list(input_set)
                    },
                    affected_elements=transitions
                ))
        
        return patterns
    
    def detect_timing_conflicts(self, kb) -> List[Pattern]:
        """Detect timing window conflicts between timed transitions.
        
        Pattern: Timed transitions interfere with each other's timing windows
        Evidence: Shared input places + cyclic dependency + timing requirements
        """
        patterns = []
        
        # Get all timed transitions
        timed_transitions = [
            (tid, trans) for tid, trans in kb.transitions.items()
            if trans.transition_type == 'timed'
        ]
        
        if len(timed_transitions) < 2:
            return patterns
        
        # Build input place mapping
        input_places = {}
        for tid, trans in timed_transitions:
            places = set()
            input_arcs = kb.get_input_arcs_for_transition(tid)
            for arc in input_arcs:
                places.add(arc.source_id)
            input_places[tid] = places
        
        # Check for conflicts
        for i, (t1_id, t1) in enumerate(timed_transitions):
            for t2_id, t2 in timed_transitions[i+1:]:
                shared = input_places[t1_id] & input_places[t2_id]
                
                # Check if they form a cycle (even without shared inputs)
                t1_outputs = set()
                t2_outputs = set()
                
                output_arcs_t1 = kb.get_output_arcs_for_transition(t1_id)
                for arc in output_arcs_t1:
                    t1_outputs.add(arc.target_id)
                
                output_arcs_t2 = kb.get_output_arcs_for_transition(t2_id)
                for arc in output_arcs_t2:
                    t2_outputs.add(arc.target_id)
                
                # Check if T1's outputs feed T2 and T2's outputs feed T1
                t1_feeds_t2 = bool(t1_outputs & input_places[t2_id])
                t2_feeds_t1 = bool(t2_outputs & input_places[t1_id])
                is_cyclic = t1_feeds_t2 and t2_feeds_t1
                
                # Report conflict if they share inputs OR form a cycle
                if shared or is_cyclic:
                    # Get timing info
                    t1_rate = getattr(t1, 'current_rate', None) or 1.0
                    t2_rate = getattr(t2, 'current_rate', None) or 1.0
                    
                    patterns.append(Pattern(
                        pattern_type=PatternType.TIMING_CONFLICT,
                        confidence=0.95 if is_cyclic else 0.75,
                        evidence={
                            't1': t1_id,
                            't2': t2_id,
                            'shared_input_places': list(shared),
                            'cyclic_dependency': is_cyclic,
                            't1_window': f"[{t1_rate}, {t1_rate}]",
                            't2_window': f"[{t2_rate}, {t2_rate}]",
                            't1_outputs': list(t1_outputs),
                            't2_outputs': list(t2_outputs)
                        },
                        affected_elements=[t1_id, t2_id] + list(shared) + list(t1_outputs & input_places[t2_id]) + list(t2_outputs & input_places[t1_id])
                    ))
        
        return patterns


# ============================================================================
# BIOCHEMICAL PATTERN DETECTION
# ============================================================================

class BiochemicalPatternDetector:
    """Detects biochemical consistency patterns."""
    
    def __init__(self, kegg_api=None):
        """Initialize with optional KEGG API client."""
        self.kegg_api = kegg_api
    
    def detect_missing_cofactors(self, kb) -> List[Pattern]:
        """Detect transitions missing required cofactors.
        
        Pattern: Reaction requires compounds not in model
        Evidence: KEGG reaction lists substrates/products not connected
        """
        patterns = []
        
        if not self.kegg_api:
            return patterns  # Need KEGG API
        
        for trans_id, trans in kb.transitions.items():
            if not trans.reaction_id:
                continue
            
            try:
                # Get KEGG reaction
                reaction = self.kegg_api.get_reaction(trans.reaction_id)
                if not reaction:
                    continue
                
                # Get all compounds in KEGG reaction
                kegg_compounds = set()
                if hasattr(reaction, 'substrates'):
                    kegg_compounds.update(reaction.substrates)
                if hasattr(reaction, 'products'):
                    kegg_compounds.update(reaction.products)
                
                # Get compounds connected to transition in model
                model_compounds = set()
                for arc in kb.get_input_arcs_for_transition(trans_id):
                    place = kb.places.get(arc.source_id)
                    if place and place.compound_id:
                        model_compounds.add(place.compound_id)
                
                for arc in kb.get_output_arcs_for_transition(trans_id):
                    place = kb.places.get(arc.target_id)
                    if place and place.compound_id:
                        model_compounds.add(place.compound_id)
                
                # Find missing compounds
                missing = kegg_compounds - model_compounds
                
                if missing:
                    patterns.append(Pattern(
                        pattern_type=PatternType.MISSING_COFACTOR,
                        confidence=0.85,
                        evidence={
                            'missing_compounds': list(missing),
                            'reaction_id': trans.reaction_id,
                            'reaction_name': trans.reaction_name,
                            'model_compounds': list(model_compounds)
                        },
                        affected_elements=[trans_id]
                    ))
            except Exception as e:
                print(f"[PATTERN] Error checking cofactors for {trans_id}: {e}")
                continue
        
        return patterns


# ============================================================================
# KINETIC PATTERN DETECTION
# ============================================================================

class KineticPatternDetector:
    """Detects kinetic formulation patterns."""
    
    def detect_rate_too_low(self, kb) -> List[Pattern]:
        """Detect transitions with insufficient rates.
        
        Pattern: Has kinetic_law but never fires despite sufficient tokens
        Evidence: firing_count=0 AND all input places have enough tokens
        """
        patterns = []
        
        for trans_id, trans in kb.transitions.items():
            # Must have kinetic law and never fired
            if not trans.kinetic_law or trans.firing_count > 0:
                continue
            
            # Check if input places have sufficient tokens
            input_arcs = kb.get_input_arcs_for_transition(trans_id)
            if not input_arcs:
                continue  # Source transitions handled elsewhere
            
            all_sufficient = True
            place_states = []
            for arc in input_arcs:
                place = kb.places.get(arc.source_id)
                if place:
                    has_enough = place.current_marking >= arc.current_weight
                    all_sufficient = all_sufficient and has_enough
                    place_states.append({
                        'place_id': arc.source_id,
                        'tokens': place.current_marking,
                        'required': arc.current_weight,
                        'sufficient': has_enough
                    })
            
            if all_sufficient:
                patterns.append(Pattern(
                    pattern_type=PatternType.RATE_TOO_LOW,
                    confidence=0.8,
                    evidence={
                        'kinetic_law': trans.kinetic_law,
                        'firing_count': trans.firing_count,
                        'input_places': place_states,
                        'ec_number': trans.ec_number,
                        'reaction_name': trans.reaction_name
                    },
                    affected_elements=[trans_id]
                ))
        
        return patterns
    
    def detect_missing_substrate_dependence(self, kb) -> List[Pattern]:
        """Detect enzymatic reactions using constant rates.
        
        Pattern: Has EC number (enzyme) but uses constant rate
        Evidence: ec_number exists but kinetic_law is None or constant
        """
        patterns = []
        
        for trans_id, trans in kb.transitions.items():
            # Has EC number (is enzymatic)
            if not trans.ec_number:
                continue
            
            # But no kinetic law
            if not trans.kinetic_law:
                input_arcs = kb.get_input_arcs_for_transition(trans_id)
                if input_arcs:  # Not a source
                    patterns.append(Pattern(
                        pattern_type=PatternType.MISSING_SUBSTRATE_DEPENDENCE,
                        confidence=0.85,
                        evidence={
                            'ec_number': trans.ec_number,
                            'reaction_name': trans.reaction_name,
                            'has_kinetic_law': False,
                            'has_rate': trans.current_rate is not None,
                            'num_substrates': len(input_arcs)
                        },
                        affected_elements=[trans_id]
                    ))
        
        return patterns
    
    def detect_pathway_imbalance(self, kb) -> List[Pattern]:
        """Detect rate mismatches in linear pathways.
        
        Pattern: Sequential transitions with very different firing rates
        Evidence: T1 fires 1000x, T2 fires 10x, causes accumulation
        """
        patterns = []
        
        # Find linear pathways: P1 → T1 → P2 → T2 → P3
        for place_id, place in kb.places.items():
            input_trans = [arc.source_id for arc in kb.get_input_arcs_for_place(place_id)]
            output_trans = [arc.target_id for arc in kb.get_output_arcs_for_place(place_id)]
            
            # Linear segment: one input, one output
            if len(input_trans) == 1 and len(output_trans) == 1:
                t1_id = input_trans[0]
                t2_id = output_trans[0]
                
                t1 = kb.transitions[t1_id]
                t2 = kb.transitions[t2_id]
                
                # Check firing rate imbalance
                if t1.firing_count > 0 and t2.firing_count > 0:
                    rate_ratio = t1.firing_count / t2.firing_count
                    
                    # Significant imbalance AND token accumulation
                    # Use avg_tokens > current_marking as indicator of accumulation
                    if rate_ratio > 5.0 and place.avg_tokens and place.avg_tokens > place.current_marking * 2:
                        patterns.append(Pattern(
                            pattern_type=PatternType.PATHWAY_IMBALANCE,
                            confidence=0.75,
                            evidence={
                                'upstream_transition': t1_id,
                                'downstream_transition': t2_id,
                                'bottleneck_place': place_id,
                                'upstream_firings': t1.firing_count,
                                'downstream_firings': t2.firing_count,
                                'rate_ratio': rate_ratio,
                                'avg_tokens': place.avg_tokens
                            },
                            affected_elements=[t1_id, place_id, t2_id]
                        ))
        
        return patterns


# ============================================================================
# REPAIR SUGGESTION GENERATION
# ============================================================================

class RepairSuggester:
    """Generates actionable repair suggestions from detected patterns."""
    
    def __init__(self, kb, kegg_api=None, brenda_api=None):
        """Initialize with KB and optional external APIs."""
        self.kb = kb
        self.kegg_api = kegg_api
        self.brenda_api = brenda_api
    
    def suggest_repairs(self, pattern: Pattern) -> List[RepairSuggestion]:
        """Generate repair suggestions for a pattern."""
        if pattern.pattern_type == PatternType.DEAD_END:
            return self._suggest_dead_end_repairs(pattern)
        elif pattern.pattern_type == PatternType.BOTTLENECK:
            return self._suggest_bottleneck_repairs(pattern)
        elif pattern.pattern_type == PatternType.UNUSED_PATH:
            return self._suggest_unused_path_repairs(pattern)
        elif pattern.pattern_type == PatternType.MISSING_COFACTOR:
            return self._suggest_cofactor_repairs(pattern)
        elif pattern.pattern_type == PatternType.RATE_TOO_LOW:
            return self._suggest_rate_repairs(pattern)
        elif pattern.pattern_type == PatternType.MISSING_SUBSTRATE_DEPENDENCE:
            return self._suggest_kinetic_law_repairs(pattern)
        elif pattern.pattern_type == PatternType.PATHWAY_IMBALANCE:
            return self._suggest_balance_repairs(pattern)
        elif pattern.pattern_type == PatternType.TIMING_CONFLICT:
            return self._suggest_timing_conflict_repairs(pattern)
        elif pattern.pattern_type == PatternType.STEADY_STATE_TRAP:
            return self._suggest_steady_state_escape_repairs(pattern)
        else:
            return []
    
    def _suggest_dead_end_repairs(self, pattern: Pattern) -> List[RepairSuggestion]:
        """Suggest fixes for dead-end places."""
        place_id = pattern.affected_elements[0]
        place = self.kb.places[place_id]
        
        return [
            RepairSuggestion(
                action="add_output_transition",
                target=place_id,
                description=f"Add output transition from {place.compound_name or place_id}",
                confidence=0.9,
                parameters={
                    'place_id': place_id,
                    'suggested_label': f"Consume_{place.compound_name or place_id}"
                },
                rationale=f"Place accumulates {pattern.evidence['current_tokens']} tokens with no way to remove them",
                data_source="topology"
            ),
            RepairSuggestion(
                action="mark_as_sink",
                target=place_id,
                description=f"Mark {place.compound_name or place_id} as intentional sink",
                confidence=0.7,
                parameters={'is_sink': True},
                rationale="If token accumulation is intentional (e.g., waste product)",
                data_source="topology"
            )
        ]
    
    def _suggest_bottleneck_repairs(self, pattern: Pattern) -> List[RepairSuggestion]:
        """Suggest fixes for bottlenecks."""
        place_id = pattern.affected_elements[0]
        place = self.kb.places[place_id]
        ev = pattern.evidence
        
        new_weight = max(1, int(ev['output_weight'] / 2))
        
        suggestions = [
            RepairSuggestion(
                action="reduce_arc_weights",
                target=place_id,
                description=f"Reduce output arc weights from {ev['output_weight']} to {new_weight}",
                confidence=0.85,
                parameters={
                    'current_weight': ev['output_weight'],
                    'suggested_weight': new_weight
                },
                rationale=f"Output requires {ev['output_weight']} tokens but place accumulates to {ev['avg_tokens']:.1f} (ratio: {ev['accumulation_ratio']:.1f}x)",
                data_source="simulation"
            ),
            RepairSuggestion(
                action="add_parallel_transition",
                target=place_id,
                description=f"Add parallel output transition to increase throughput",
                confidence=0.7,
                parameters={},
                rationale=f"Tokens accumulate (avg={ev['avg_tokens']:.1f}) faster than consumed",
                data_source="simulation"
            )
        ]
        
        # Check if downstream transitions have low rates
        output_arcs = self.kb.get_output_arcs_for_place(place_id)
        for arc in output_arcs:
            trans = self.kb.transitions[arc.target_id]
            if trans.kinetic_law:
                suggestions.append(RepairSuggestion(
                    action="increase_downstream_rate",
                    target=arc.target_id,
                    description=f"Increase rate of downstream transition {trans.reaction_name or arc.target_id}",
                    confidence=0.75,
                    parameters={
                        'transition_id': arc.target_id,
                        'current_kinetic_law': trans.kinetic_law
                    },
                    rationale="Downstream transition may be too slow to process accumulated tokens",
                    data_source="simulation"
                ))
        
        return suggestions
    
    def _suggest_unused_path_repairs(self, pattern: Pattern) -> List[RepairSuggestion]:
        """Suggest fixes for unused parallel paths."""
        ev = pattern.evidence
        unused = ev['unused_transitions']
        
        suggestions = []
        for trans_id in unused:
            trans = self.kb.transitions[trans_id]
            suggestions.append(RepairSuggestion(
                action="balance_competition",
                target=trans_id,
                description=f"Adjust arc weights or priority for {trans.reaction_name or trans_id}",
                confidence=0.7,
                parameters={
                    'transition_id': trans_id,
                    'competing_with': ev['active_transitions']
                },
                rationale="Transition never fires because competing transition always wins",
                data_source="simulation"
            ))
        
        return suggestions
    
    def _suggest_cofactor_repairs(self, pattern: Pattern) -> List[RepairSuggestion]:
        """Suggest adding missing cofactors."""
        trans_id = pattern.affected_elements[0]
        ev = pattern.evidence
        
        suggestions = []
        for compound_id in ev['missing_compounds']:
            suggestions.append(RepairSuggestion(
                action="add_cofactor_place",
                target=trans_id,
                description=f"Add place for cofactor {compound_id}",
                confidence=0.85,
                parameters={
                    'compound_id': compound_id,
                    'transition_id': trans_id,
                    'reaction_id': ev['reaction_id']
                },
                rationale=f"KEGG reaction {ev['reaction_id']} requires {compound_id}",
                data_source="KEGG"
            ))
        
        return suggestions
    
    def _suggest_rate_repairs(self, pattern: Pattern) -> List[RepairSuggestion]:
        """Suggest rate parameter adjustments."""
        trans_id = pattern.affected_elements[0]
        trans = self.kb.transitions[trans_id]
        ev = pattern.evidence
        
        suggestions = []
        
        # Suggest increasing vmax
        if 'vmax' in ev['kinetic_law'].lower():
            suggestions.append(RepairSuggestion(
                action="increase_vmax",
                target=trans_id,
                description=f"Increase vmax parameter (transition never fires despite sufficient substrates)",
                confidence=0.75,
                parameters={
                    'transition_id': trans_id,
                    'current_kinetic_law': ev['kinetic_law'],
                    'suggestion': 'Multiply vmax by 10'
                },
                rationale="Transition has substrates but never fires - rate likely too low",
                data_source="simulation"
            ))
        
        # Query BRENDA if available
        if self.brenda_api and trans.ec_number:
            suggestions.append(RepairSuggestion(
                action="use_brenda_parameters",
                target=trans_id,
                description=f"Query BRENDA for realistic kinetic parameters (EC {trans.ec_number})",
                confidence=0.8,
                parameters={
                    'ec_number': trans.ec_number,
                    'organism': 'human'  # Could be configurable
                },
                rationale="Use experimentally determined kinetic parameters",
                data_source="BRENDA"
            ))
        
        return suggestions
    
    def _suggest_kinetic_law_repairs(self, pattern: Pattern) -> List[RepairSuggestion]:
        """Suggest adding kinetic laws to enzymatic reactions."""
        trans_id = pattern.affected_elements[0]
        trans = self.kb.transitions[trans_id]
        ev = pattern.evidence
        
        # Get substrate places
        input_arcs = self.kb.get_input_arcs_for_transition(trans_id)
        substrate_ids = [arc.source_id for arc in input_arcs]
        
        kinetic_law = f"michaelis_menten({substrate_ids[0]}, vmax=1.0, km=0.1)" if substrate_ids else "1.0"
        
        return [
            RepairSuggestion(
                action="add_kinetic_law",
                target=trans_id,
                description=f"Add Michaelis-Menten kinetics for enzyme {trans.reaction_name or trans_id}",
                confidence=0.9,
                parameters={
                    'kinetic_law': kinetic_law,
                    'substrates': substrate_ids
                },
                rationale=f"Enzyme (EC {ev['ec_number']}) should have substrate-dependent rate",
                data_source="biochemistry"
            )
        ]
    
    def _suggest_balance_repairs(self, pattern: Pattern) -> List[RepairSuggestion]:
        """Suggest fixes for pathway imbalance."""
        ev = pattern.evidence
        upstream_id = ev['upstream_transition']
        downstream_id = ev['downstream_transition']
        
        return [
            RepairSuggestion(
                action="balance_pathway_rates",
                target=downstream_id,
                description=f"Increase rate of {downstream_id} to match {upstream_id}",
                confidence=0.75,
                parameters={
                    'upstream_firings': ev['upstream_firings'],
                    'downstream_firings': ev['downstream_firings'],
                    'suggested_multiplier': ev['rate_ratio']
                },
                rationale=f"Upstream fires {ev['rate_ratio']:.1f}x faster, causing accumulation",
                data_source="simulation"
            )
        ]
    
    def _suggest_timing_conflict_repairs(self, pattern: Pattern) -> List[RepairSuggestion]:
        """Suggest fixes for timing window conflicts between timed transitions.
        
        This detector addresses synchronization issues where timed transitions
        with identical or conflicting timing windows create livelock patterns,
        especially in cyclic metabolic pathways.
        """
        ev = pattern.evidence
        t1_id = ev['t1']
        t2_id = ev['t2']
        shared_places = ev['shared_input_places']
        is_cyclic = ev['cyclic_dependency']
        
        # Get timing information for detailed rationale
        t1 = self.kb.get_transition(t1_id)
        t2 = self.kb.get_transition(t2_id)
        t1_window = ev.get('t1_window', '[unknown, unknown]')
        t2_window = ev.get('t2_window', '[unknown, unknown]')
        
        suggestions = []
        
        # Repair 1: Convert to continuous (BEST for biological models)
        suggestions.append(RepairSuggestion(
            action="convert_to_continuous",
            target=f"{t1_id},{t2_id}",
            description=f"Convert {t1_id} and {t2_id} to continuous transitions",
            confidence=0.95,
            parameters={
                'transitions': [t1_id, t2_id],
                'new_type': 'continuous',
                'preserve_rate': True
            },
            rationale=(
                f"Biological reactions should fire continuously when substrates are available. "
                f"Current timing windows {t1_window} and {t2_window} create artificial delays "
                f"that can cause livelock when transitions mutually reset each other's timers."
                + (" This is especially critical for cyclic metabolic pathways." if is_cyclic else "")
            ),
            data_source="biological_semantics"
        ))
        
        # Repair 2: Use different firing policies to break synchronization
        suggestions.append(RepairSuggestion(
            action="adjust_firing_policies",
            target=f"{t1_id},{t2_id}",
            description=f"Set different firing policies for {t1_id} and {t2_id}",
            confidence=0.85,
            parameters={
                'transitions': [t1_id, t2_id],
                't1_policy': 'priority',
                't2_policy': 'random',
                't1_priority': 1,
                't2_priority': 0,
                'rationale_for_policies': 'Different policies prevent synchronized firing'
            },
            rationale=(
                f"Setting {t1_id} to priority-based firing and {t2_id} to random firing "
                f"breaks the synchronization pattern. When both transitions are enabled "
                f"simultaneously, the priority-based one fires first, preventing mutual "
                f"timer resets. This preserves timed behavior while resolving conflicts."
            ),
            data_source="firing_policy"
        ))
        
        # Repair 3: Add stochastic variance to rate parameters
        suggestions.append(RepairSuggestion(
            action="add_rate_variance",
            target=f"{t1_id},{t2_id}",
            description=f"Add stochastic variance to timing windows",
            confidence=0.80,
            parameters={
                'transitions': [t1_id, t2_id],
                't1_rate_function': 'normal(1.0, 0.1)',  # mean=1.0, stddev=0.1
                't2_rate_function': 'normal(1.0, 0.15)',  # slightly different variance
                'distribution_type': 'normal',
                'explanation': 'Slightly different variances prevent lock-step behavior'
            },
            rationale=(
                f"Replace fixed timing windows {t1_window} and {t2_window} with stochastic "
                f"rate functions (e.g., normal(1.0, 0.1) for {t1_id}, normal(1.0, 0.15) for {t2_id}). "
                f"The small difference in variance (0.1 vs 0.15) prevents the transitions from "
                f"firing in perfect synchrony, breaking the livelock while maintaining similar "
                f"average firing rates."
            ),
            data_source="stochastic_modeling"
        ))
        
        # Repair 4: Offset timing windows to create sequential behavior
        suggestions.append(RepairSuggestion(
            action="offset_timing_windows",
            target=f"{t1_id},{t2_id}",
            description=f"Offset timing windows to prevent simultaneous enablement",
            confidence=0.75,
            parameters={
                'transitions': [t1_id, t2_id],
                't1_new_window': [1.0, 1.0],  # Keep original
                't2_new_window': [1.5, 1.5],  # Offset by 0.5 seconds
                't1_old_window': t1_window,
                't2_old_window': t2_window,
                'offset_amount': 0.5
            },
            rationale=(
                f"Change {t2_id}'s timing window from {t2_window} to [1.5, 1.5] while keeping "
                f"{t1_id} at {t1_window}. This creates a sequential pattern where {t1_id} fires "
                f"first, then {t2_id} fires 0.5 seconds later. The offset breaks the mutual "
                f"interference pattern while maintaining deterministic timing."
            ),
            data_source="timing_analysis"
        ))
        
        # Repair 5: Widen one timing window to allow flexibility
        suggestions.append(RepairSuggestion(
            action="widen_timing_window",
            target=t2_id,
            description=f"Widen {t2_id}'s timing window to allow flexible firing",
            confidence=0.70,
            parameters={
                'transition': t2_id,
                'new_window': [0.5, 2.0],  # Wide window
                'old_window': t2_window,
                'rationale': 'Flexible window allows firing whenever enabled'
            },
            rationale=(
                f"Change {t2_id}'s timing window from {t2_window} to [0.5, 2.0]. "
                f"This wide window allows {t2_id} to fire at any time between 0.5 and 2.0 seconds "
                f"after enablement, giving it flexibility to fire without interfering with {t1_id}'s "
                f"fixed window {t1_window}. Keep {t1_id}'s precise timing for critical reactions."
            ),
            data_source="timing_analysis"
        ))
        
        # Repair 6: Convert to immediate (removes timing, may not preserve semantics)
        suggestions.append(RepairSuggestion(
            action="convert_to_immediate",
            target=f"{t1_id},{t2_id}",
            description=f"Convert {t1_id} and {t2_id} to immediate transitions",
            confidence=0.60,
            parameters={
                'transitions': [t1_id, t2_id],
                'new_type': 'immediate',
                'add_priorities': True,
                't1_priority': 1,
                't2_priority': 0
            },
            rationale=(
                f"Remove timing windows entirely by converting to immediate transitions. "
                f"Add priorities ({t1_id}=1, {t2_id}=0) to ensure deterministic firing order. "
                f"This eliminates timing conflicts but loses temporal dynamics - only use "
                f"if precise timing is not biologically relevant."
            ),
            data_source="structural"
        ))
        
        # Repair 7: Add initial tokens (only for cyclic dependencies)
        if is_cyclic:
            # For cyclic dependencies, target the places that are in the cycle
            # Get places involved in the cycle (outputs that feed each other)
            t1_id = ev['t1']
            t2_id = ev['t2']
            t1_outputs = ev.get('t1_outputs', [])
            t2_outputs = ev.get('t2_outputs', [])
            cycle_places = t1_outputs + t2_outputs
            
            # Prefer shared places if they exist, otherwise use cycle places
            target_places = shared_places if shared_places else cycle_places
            target_place = target_places[0] if target_places else "P1"  # Fallback
            
            suggestions.append(RepairSuggestion(
                action="add_initial_tokens",
                target=target_place,
                description=f"Add initial tokens to break cyclic timing dependency",
                confidence=0.50,
                parameters={
                    'places': target_places,
                    'tokens_to_add': 1,
                    'reason': 'break_timing_deadlock'
                },
                rationale=(
                    f"Add initial token to {target_place} to ensure one transition can "
                    f"complete its timing window before the other. "
                    f"This is a structural workaround that may not reflect biological reality. "
                    f"Adjusting firing policies or rate functions is strongly preferred."
                ),
                data_source="structural"
            ))
        
        return suggestions
    
    def _suggest_steady_state_escape_repairs(self, pattern: Pattern) -> List[RepairSuggestion]:
        """Suggest strategies to escape steady states in continuous Petri nets.
        
        Continuous transitions can reach stable equilibria where inflow = outflow,
        causing the system to become "stuck" at certain token distributions.
        These suggestions provide ways to perturb the system and restore dynamics.
        """
        ev = pattern.evidence
        transitions = ev.get('continuous_transitions', [])
        places = ev.get('steady_state_places', [])
        
        suggestions = []
        
        # Strategy 1: Add stochastic noise to rates (BEST for biological realism)
        suggestions.append(RepairSuggestion(
            action="add_stochastic_noise",
            target=','.join(transitions[:3]),  # Show first 3
            description="Add stochastic noise to continuous transition rates",
            confidence=0.95,
            parameters={
                'transitions': transitions,
                'noise_type': 'wiener',  # Brownian motion
                'noise_amplitude': 0.1,  # 10% of base rate
                'example_rate': 'rate * (1 + 0.1 * wiener(t))',
                'biological_basis': 'Molecular noise from finite molecule numbers'
            },
            rationale=(
                "Add Wiener process noise (Brownian motion) to continuous rates. "
                "This represents biological stochasticity from finite molecule numbers. "
                "The noise amplitude of 0.1 means ±10% fluctuation around base rate, "
                "which prevents exact balance and escapes steady states. "
                "Example: rate=1.0 becomes rate=1.0*(1 + 0.1*wiener(t)), "
                "giving values between 0.9-1.1 with continuous fluctuation."
            ),
            data_source="stochastic_modeling"
        ))
        
        # Strategy 2: Use piecewise rate functions with thresholds
        suggestions.append(RepairSuggestion(
            action="add_threshold_switching",
            target=','.join(transitions[:3]),
            description="Add threshold-based switching to transition rates",
            confidence=0.90,
            parameters={
                'transitions': transitions,
                'function_type': 'piecewise',
                'example': 'if(P1 > 0.5, rate*2, rate*0.5)',
                'thresholds': [p + ':0.5' for p in places[:3]],
                'biological_basis': 'Allosteric regulation, feedback inhibition'
            },
            rationale=(
                "Use piecewise functions that change behavior at concentration thresholds. "
                "Example: if(P1 > 0.5, rate*2, rate*0.5) doubles the rate when P1 exceeds "
                "0.5 tokens, halves it otherwise. This creates non-linear dynamics that "
                "prevent steady states. Biologically represents cooperative binding, "
                "allosteric effects, or ultrasensitive switches (Hill functions)."
            ),
            data_source="nonlinear_dynamics"
        ))
        
        # Strategy 3: Add periodic perturbations (circadian/ultradian rhythms)
        suggestions.append(RepairSuggestion(
            action="add_periodic_forcing",
            target=','.join(transitions[:3]),
            description="Add periodic oscillations to transition rates",
            confidence=0.85,
            parameters={
                'transitions': transitions,
                'function_type': 'sinusoidal',
                'period': 24.0,  # 24-hour circadian
                'amplitude': 0.2,  # ±20% variation
                'example': 'rate * (1 + 0.2 * sin(2*pi*t/24))',
                'biological_basis': 'Circadian rhythms, cell cycle oscillations'
            },
            rationale=(
                "Add sinusoidal variation to mimic circadian or ultradian rhythms. "
                "Example: rate * (1 + 0.2*sin(2*pi*t/24)) creates 24-hour oscillation "
                "with ±20% amplitude. The periodic forcing prevents steady states by "
                "continuously changing system parameters. Biologically represents "
                "circadian clock regulation, cell cycle phases, or metabolic rhythms."
            ),
            data_source="temporal_dynamics"
        ))
        
        # Strategy 4: Implement substrate inhibition (product feedback)
        suggestions.append(RepairSuggestion(
            action="add_substrate_inhibition",
            target=','.join(transitions[:3]),
            description="Add substrate/product inhibition to prevent accumulation",
            confidence=0.80,
            parameters={
                'transitions': transitions,
                'inhibition_type': 'substrate',
                'ki_value': 10.0,  # Inhibition constant
                'example': 'vmax * S / (km + S + S^2/ki)',
                'biological_basis': 'Substrate inhibition, product feedback'
            },
            rationale=(
                "Add substrate inhibition where high concentrations slow the reaction. "
                "Example: vmax * S / (km + S + S^2/ki) includes S^2/ki term that "
                "reduces rate at high [S]. This prevents unlimited accumulation and "
                "creates oscillatory or limit-cycle behavior. Common in metabolic "
                "pathways (e.g., phosphofructokinase in glycolysis)."
            ),
            data_source="enzyme_kinetics"
        ))
        
        # Strategy 5: Add time delays (transcription/translation lag)
        suggestions.append(RepairSuggestion(
            action="add_time_delays",
            target=','.join(transitions[:3]),
            description="Add time delays to create dynamic behavior",
            confidence=0.75,
            parameters={
                'transitions': transitions,
                'delay_type': 'discrete',
                'delay_amount': 1.0,  # 1 time unit
                'example': 'rate * P1(t-1.0)',  # Use place value from 1 time unit ago
                'biological_basis': 'Transcription/translation lag, transport delays'
            },
            rationale=(
                "Add time delays where rates depend on past concentrations. "
                "Example: rate * P1(t-1.0) uses P1's value from 1 time unit ago. "
                "Delays create phase lags that can generate oscillations and prevent "
                "steady states. Biologically represents transcription/translation lag "
                "(genes → mRNA → protein takes minutes to hours)."
            ),
            data_source="delay_differential_equations"
        ))
        
        # Strategy 6: Convert to hybrid (mix continuous with discrete events)
        suggestions.append(RepairSuggestion(
            action="convert_to_hybrid",
            target=','.join(transitions[:2]),
            description="Mix continuous flow with discrete stochastic events",
            confidence=0.70,
            parameters={
                'transitions_to_convert': transitions[:len(transitions)//2],
                'new_type': 'stochastic',
                'keep_continuous': transitions[len(transitions)//2:],
                'biological_basis': 'Low-copy-number molecules fire discretely'
            },
            rationale=(
                f"Convert some continuous transitions to stochastic while keeping others continuous. "
                f"For example, convert {transitions[0]} to stochastic (fires in discrete bursts) "
                f"while keeping others continuous. This hybrid approach breaks perfect balance "
                f"by introducing discrete jumps. Biologically accurate for low-copy-number "
                f"molecules (transcription factors, signaling proteins)."
            ),
            data_source="hybrid_modeling"
        ))
        
        # Strategy 7: Add external pulse perturbations
        suggestions.append(RepairSuggestion(
            action="add_pulse_perturbations",
            target=places[0] if places else "P1",
            description="Add periodic token pulses to break steady state",
            confidence=0.65,
            parameters={
                'target_places': places[:2],
                'pulse_interval': 10.0,  # Every 10 time units
                'pulse_amount': 1.0,  # Add 1 token
                'pulse_type': 'periodic',
                'biological_basis': 'External stimuli, feeding cycles, hormone pulses'
            },
            rationale=(
                f"Inject token pulses into {places[0] if places else 'key places'} every 10 time units. "
                "This simulates external perturbations (feeding, hormone pulses, stress responses). "
                "The pulses break steady state by adding sudden changes that the system must "
                "accommodate. Can be periodic or stochastic. Biologically represents "
                "pulsatile hormone release (insulin, GnRH) or feeding cycles."
            ),
            data_source="forced_perturbation"
        ))
        
        return suggestions


# ============================================================================
# MAIN PATTERN RECOGNITION ENGINE
# ============================================================================

class PatternRecognitionEngine:
    """Main engine that coordinates pattern detection and repair suggestions."""
    
    def __init__(self, kb, kegg_api=None, brenda_api=None):
        """Initialize the pattern recognition engine."""
        self.kb = kb
        self.structural_detector = StructuralPatternDetector()
        self.biochemical_detector = BiochemicalPatternDetector(kegg_api)
        self.kinetic_detector = KineticPatternDetector()
        self.repair_suggester = RepairSuggester(kb, kegg_api, brenda_api)
    
    def analyze(self) -> Dict[str, List]:
        """Run complete pattern analysis.
        
        Returns:
            Dict with 'patterns' and 'suggestions' keys
        """
        print("[PATTERN_ENGINE] Starting multi-domain analysis...")
        
        # Detect patterns across all domains
        patterns = []
        
        # Structural patterns
        print("[PATTERN_ENGINE] Detecting structural patterns...")
        patterns.extend(self.structural_detector.detect_dead_ends(self.kb))
        patterns.extend(self.structural_detector.detect_bottlenecks(self.kb))
        patterns.extend(self.structural_detector.detect_unused_paths(self.kb))
        patterns.extend(self.structural_detector.detect_timing_conflicts(self.kb))
        
        # Biochemical patterns
        print("[PATTERN_ENGINE] Detecting biochemical patterns...")
        patterns.extend(self.biochemical_detector.detect_missing_cofactors(self.kb))
        
        # Kinetic patterns
        print("[PATTERN_ENGINE] Detecting kinetic patterns...")
        patterns.extend(self.kinetic_detector.detect_rate_too_low(self.kb))
        patterns.extend(self.kinetic_detector.detect_missing_substrate_dependence(self.kb))
        patterns.extend(self.kinetic_detector.detect_pathway_imbalance(self.kb))
        
        print(f"[PATTERN_ENGINE] Detected {len(patterns)} patterns")
        
        # Generate repair suggestions
        print("[PATTERN_ENGINE] Generating repair suggestions...")
        all_suggestions = []
        for pattern in patterns:
            suggestions = self.repair_suggester.suggest_repairs(pattern)
            all_suggestions.extend(suggestions)
        
        print(f"[PATTERN_ENGINE] Generated {len(all_suggestions)} repair suggestions")
        
        return {
            'patterns': patterns,
            'suggestions': all_suggestions
        }
    
    def get_patterns_by_type(self, pattern_type: PatternType) -> List[Pattern]:
        """Get all patterns of a specific type."""
        result = self.analyze()
        return [p for p in result['patterns'] if p.pattern_type == pattern_type]
    
    def get_suggestions_for_element(self, element_id: str) -> List[RepairSuggestion]:
        """Get all suggestions affecting a specific element."""
        result = self.analyze()
        return [s for s in result['suggestions'] if s.target == element_id]
