"""Fix sequencing for dependency-aware fix application.

Analyzes fix dependencies and orders them for optimal application.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Set, Optional, Tuple
from collections import defaultdict

from shypn.ui.panels.viability.investigation import Suggestion


@dataclass
class FixSequence:
    """Ordered sequence of fixes with dependency information.
    
    Attributes:
        batches: List of fix batches (each batch can be applied in parallel)
        dependencies: Map of fix_id -> list of prerequisite fix_ids
        conflicts: List of conflicting fix pairs
        total_fixes: Total number of fixes in sequence
    """
    batches: List[List[Suggestion]] = field(default_factory=list)
    dependencies: Dict[str, List[str]] = field(default_factory=dict)
    conflicts: List[Tuple[Suggestion, Suggestion]] = field(default_factory=list)
    total_fixes: int = 0
    
    def get_batch(self, index: int) -> List[Suggestion]:
        """Get fixes in a specific batch.
        
        Args:
            index: Batch index (0-based)
            
        Returns:
            List of suggestions in that batch
        """
        if 0 <= index < len(self.batches):
            return self.batches[index]
        return []
    
    def get_all_fixes(self) -> List[Suggestion]:
        """Get all fixes in sequence order.
        
        Returns:
            Flat list of all suggestions
        """
        result = []
        for batch in self.batches:
            result.extend(batch)
        return result
    
    def has_conflicts(self) -> bool:
        """Check if sequence has any conflicts.
        
        Returns:
            True if conflicts exist
        """
        return len(self.conflicts) > 0


class FixSequencer:
    """Sequences fixes by analyzing dependencies and conflicts.
    
    Analyzes suggestions to determine:
    1. Which fixes must happen before others
    2. Which fixes can be applied in parallel
    3. Which fixes conflict with each other
    
    Uses topological sort for dependency ordering.
    """
    
    def __init__(self):
        """Initialize fix sequencer."""
        self.fix_graph = defaultdict(set)  # fix_id -> set of prerequisite fix_ids
        self.fix_map = {}  # fix_id -> Suggestion
    
    def sequence(self, suggestions: List[Suggestion]) -> FixSequence:
        """Sequence fixes by dependencies.
        
        Args:
            suggestions: List of suggestions to sequence
            
        Returns:
            FixSequence with ordered batches
        """
        if not suggestions:
            return FixSequence(total_fixes=0)
        
        # Clear previous state
        self.fix_graph.clear()
        self.fix_map.clear()
        
        # Build fix map
        for i, suggestion in enumerate(suggestions):
            fix_id = self._get_fix_id(suggestion, i)
            self.fix_map[fix_id] = suggestion
        
        # Analyze dependencies
        self._analyze_dependencies(suggestions)
        
        # Detect conflicts
        conflicts = self._detect_conflicts(suggestions)
        
        # Create batches using topological sort
        batches = self._create_batches()
        
        return FixSequence(
            batches=batches,
            dependencies=dict(self.fix_graph),
            conflicts=conflicts,
            total_fixes=len(suggestions)
        )
    
    def _get_fix_id(self, suggestion: Suggestion, index: int) -> str:
        """Generate unique ID for a fix.
        
        Args:
            suggestion: The suggestion
            index: Index in list
            
        Returns:
            Unique fix ID
        """
        # Use target element and action as base
        base = f"{suggestion.target_element_id}_{suggestion.category}"
        return f"{base}_{index}"
    
    def _analyze_dependencies(self, suggestions: List[Suggestion]):
        """Analyze dependencies between fixes.
        
        Dependencies exist when:
        1. Fix B operates on element modified by Fix A
        2. Fix B addresses cascading issue from Fix A
        3. Category-based ordering (structural before kinetic)
        
        Args:
            suggestions: List of suggestions
        """
        # Category priority: structural > biological > kinetic
        category_priority = {
            'structural': 0,
            'biological': 1,
            'kinetic': 2,
            'flow': 1,
            'boundary': 1,
            'conservation': 0
        }
        
        fix_ids = list(self.fix_map.keys())
        
        for i, fix_id_a in enumerate(fix_ids):
            suggestion_a = self.fix_map[fix_id_a]
            
            for j, fix_id_b in enumerate(fix_ids):
                if i >= j:  # Skip self and already compared
                    continue
                
                suggestion_b = self.fix_map[fix_id_b]
                
                # Rule 1: Same element - apply in category priority order
                if suggestion_a.target_element_id == suggestion_b.target_element_id:
                    priority_a = category_priority.get(suggestion_a.category, 5)
                    priority_b = category_priority.get(suggestion_b.category, 5)
                    
                    if priority_a < priority_b:
                        # A must come before B
                        self.fix_graph[fix_id_b].add(fix_id_a)
                    elif priority_b < priority_a:
                        # B must come before A
                        self.fix_graph[fix_id_a].add(fix_id_b)
                
                # Rule 2: Cascading fixes - root cause first
                if self._is_cascading_fix(suggestion_a):
                    # Check if B is downstream
                    if self._is_downstream(suggestion_a, suggestion_b):
                        self.fix_graph[fix_id_b].add(fix_id_a)
                
                # Rule 3: Bottleneck fixes before flow balance
                if suggestion_a.category == 'flow' and 'bottleneck' in suggestion_a.action.lower():
                    if suggestion_b.category == 'flow' and 'balance' in suggestion_b.action.lower():
                        self.fix_graph[fix_id_b].add(fix_id_a)
    
    def _is_cascading_fix(self, suggestion: Suggestion) -> bool:
        """Check if fix addresses root cause of cascade.
        
        Args:
            suggestion: The suggestion to check
            
        Returns:
            True if this is a cascading root cause fix
        """
        details = suggestion.details or {}
        return (
            details.get('is_root_cause', False) or
            'root cause' in suggestion.action.lower() or
            'cascading' in suggestion.impact.lower()
        )
    
    def _is_downstream(self, fix_a: Suggestion, fix_b: Suggestion) -> bool:
        """Check if fix_b is downstream of fix_a.
        
        Args:
            fix_a: Potential upstream fix
            fix_b: Potential downstream fix
            
        Returns:
            True if B is affected by A
        """
        details_a = fix_a.details or {}
        affected = details_a.get('affected_transitions', [])
        
        return fix_b.target_element_id in affected
    
    def _detect_conflicts(self, suggestions: List[Suggestion]) -> List[Tuple[Suggestion, Suggestion]]:
        """Detect conflicting fixes.
        
        Conflicts occur when:
        1. Two fixes modify same property in incompatible ways
        2. Fix goals are contradictory
        
        Args:
            suggestions: List of suggestions
            
        Returns:
            List of conflicting suggestion pairs
        """
        conflicts = []
        
        for i, sug_a in enumerate(suggestions):
            for j, sug_b in enumerate(suggestions[i+1:], start=i+1):
                # Same element, different categories might conflict
                if sug_a.target_element_id == sug_b.target_element_id:
                    # Check for contradictory actions
                    if self._are_contradictory(sug_a, sug_b):
                        conflicts.append((sug_a, sug_b))
        
        return conflicts
    
    def _are_contradictory(self, sug_a: Suggestion, sug_b: Suggestion) -> bool:
        """Check if two suggestions have contradictory goals.
        
        Args:
            sug_a: First suggestion
            sug_b: Second suggestion
            
        Returns:
            True if contradictory
        """
        # Increase vs decrease on same parameter
        action_a = sug_a.action.lower()
        action_b = sug_b.action.lower()
        
        if 'increase' in action_a and 'decrease' in action_b:
            return True
        if 'decrease' in action_a and 'increase' in action_b:
            return True
        
        # Add vs remove same element type
        if 'add' in action_a and 'remove' in action_b:
            return True
        if 'remove' in action_a and 'add' in action_b:
            return True
        
        return False
    
    def _create_batches(self) -> List[List[Suggestion]]:
        """Create fix batches using topological sort.
        
        Uses Kahn's algorithm for topological sorting.
        Fixes with no dependencies go in first batch,
        then subsequent batches as dependencies are satisfied.
        
        Returns:
            List of batches (each batch = list of suggestions)
        """
        if not self.fix_map:
            return []
        
        # Calculate in-degree for each fix
        in_degree = {fix_id: 0 for fix_id in self.fix_map}
        for fix_id, prereqs in self.fix_graph.items():
            in_degree[fix_id] = len(prereqs)
        
        batches = []
        remaining = set(self.fix_map.keys())
        
        while remaining:
            # Find all fixes with no remaining dependencies
            batch = []
            for fix_id in list(remaining):
                if in_degree[fix_id] == 0:
                    batch.append(self.fix_map[fix_id])
                    remaining.remove(fix_id)
            
            if not batch:
                # Circular dependency detected - break it
                # Just take first remaining fix
                fix_id = next(iter(remaining))
                batch.append(self.fix_map[fix_id])
                remaining.remove(fix_id)
            
            batches.append(batch)
            
            # Update in-degrees
            for fix_id in [self._get_fix_id(s, i) for i, s in enumerate(batch)]:
                # For each fix that depends on completed fixes
                for other_id in remaining:
                    if fix_id in self.fix_graph.get(other_id, set()):
                        in_degree[other_id] -= 1
        
        return batches
    
    def explain_sequence(self, sequence: FixSequence) -> str:
        """Generate human-readable explanation of sequence.
        
        Args:
            sequence: The fix sequence
            
        Returns:
            Explanation text
        """
        lines = []
        lines.append(f"Fix Sequence: {sequence.total_fixes} fixes in {len(sequence.batches)} batches")
        lines.append("")
        
        if sequence.has_conflicts():
            lines.append(f"⚠️  {len(sequence.conflicts)} conflicts detected:")
            for sug_a, sug_b in sequence.conflicts:
                lines.append(f"  - {sug_a.action} ↔ {sug_b.action}")
            lines.append("")
        
        for i, batch in enumerate(sequence.batches, 1):
            lines.append(f"Batch {i}: {len(batch)} fixes")
            for suggestion in batch:
                lines.append(f"  • {suggestion.action}")
                if suggestion.impact:
                    lines.append(f"    → {suggestion.impact}")
            lines.append("")
        
        return "\n".join(lines)
