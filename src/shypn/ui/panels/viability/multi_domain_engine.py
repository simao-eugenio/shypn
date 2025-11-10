#!/usr/bin/env python3
"""Multi-Domain Suggestion Engine.

The key innovation of the Viability Panel: combining structural, biological,
and kinetic knowledge to provide comprehensive suggestions.

For each issue, this engine:
1. Gets structural suggestions (from topology analysis)
2. Gets biological suggestions (from KEGG/compound knowledge)
3. Gets kinetic suggestions (from BRENDA/parameter knowledge)
4. Combines them into a MultiDomainSuggestion

This gives users the full picture from all knowledge layers.

Author: Simão Eugénio
Date: November 10, 2025
"""

from typing import List, Dict, Optional, Any
from .viability_dataclasses import (
    Issue, Suggestion, MultiDomainSuggestion
)


class MultiDomainEngine:
    """Engine for creating multi-domain suggestions.
    
    Combines knowledge from:
    - Structural domain (topology)
    - Biological domain (semantics)
    - Kinetic domain (parameters)
    """
    
    def __init__(self, knowledge_base=None):
        """Initialize multi-domain engine.
        
        Args:
            knowledge_base: ModelKnowledgeBase instance
        """
        self.kb = knowledge_base
    
    def get_multi_domain_suggestions(
        self, 
        issues: List[Issue],
        locality_id: Optional[str] = None
    ) -> List[MultiDomainSuggestion]:
        """Create multi-domain suggestions by combining issue suggestions.
        
        Groups issues by element_id and combines suggestions from
        different categories (structural, biological, kinetic).
        
        Args:
            issues: List of detected issues
            locality_id: Optional locality filter
            
        Returns:
            List of MultiDomainSuggestion instances
        """
        # Group issues by element_id
        by_element = self._group_issues_by_element(issues)
        
        multi_domain_suggestions = []
        
        for element_id, element_issues in by_element.items():
            # Get suggestions by category
            structural_suggestions = self._get_category_suggestions(
                element_issues, "structural"
            )
            biological_suggestions = self._get_category_suggestions(
                element_issues, "biological"
            )
            kinetic_suggestions = self._get_category_suggestions(
                element_issues, "kinetic"
            )
            
            # Only create multi-domain if at least 2 categories have suggestions
            has_multiple = sum([
                len(structural_suggestions) > 0,
                len(biological_suggestions) > 0,
                len(kinetic_suggestions) > 0
            ]) >= 2
            
            if not has_multiple:
                continue
            
            # Pick best suggestion from each category
            structural_best = self._pick_best_suggestion(structural_suggestions)
            biological_best = self._pick_best_suggestion(biological_suggestions)
            kinetic_best = self._pick_best_suggestion(kinetic_suggestions)
            
            # Create multi-domain suggestion
            mds = MultiDomainSuggestion(
                issue_id=element_issues[0].id,
                element_id=element_id,
                structural_suggestion=structural_best,
                biological_suggestion=biological_best,
                kinetic_suggestion=kinetic_best
            )
            
            # Calculate combined confidence and reasoning
            self._combine_suggestions(mds)
            
            multi_domain_suggestions.append(mds)
        
        return multi_domain_suggestions
    
    def _group_issues_by_element(
        self, 
        issues: List[Issue]
    ) -> Dict[str, List[Issue]]:
        """Group issues by element_id.
        
        Args:
            issues: List of issues
            
        Returns:
            Dict mapping element_id to list of issues for that element
        """
        grouped = {}
        for issue in issues:
            if issue.element_id not in grouped:
                grouped[issue.element_id] = []
            grouped[issue.element_id].append(issue)
        return grouped
    
    def _get_category_suggestions(
        self,
        issues: List[Issue],
        category: str
    ) -> List[Suggestion]:
        """Get all suggestions from a specific category.
        
        Args:
            issues: List of issues for an element
            category: Category to filter ("structural", "biological", "kinetic")
            
        Returns:
            List of suggestions from that category
        """
        suggestions = []
        for issue in issues:
            if issue.category == category:
                suggestions.extend(issue.suggestions)
        return suggestions
    
    def _pick_best_suggestion(
        self,
        suggestions: List[Suggestion]
    ) -> Optional[Suggestion]:
        """Pick the best suggestion based on confidence.
        
        Args:
            suggestions: List of suggestions
            
        Returns:
            Suggestion with highest confidence, or None
        """
        if not suggestions:
            return None
        return max(suggestions, key=lambda s: s.confidence)
    
    def _combine_suggestions(self, mds: MultiDomainSuggestion):
        """Combine suggestions into unified confidence and reasoning.
        
        Updates the MultiDomainSuggestion in-place.
        
        Args:
            mds: MultiDomainSuggestion to update
        """
        # Collect confidences and reasoning parts
        confidences = []
        reasoning_parts = []
        
        if mds.structural_suggestion:
            confidences.append(mds.structural_suggestion.confidence)
            reasoning_parts.append(
                f"🏗️ Structural: {mds.structural_suggestion.reasoning}"
            )
        
        if mds.biological_suggestion:
            confidences.append(mds.biological_suggestion.confidence)
            reasoning_parts.append(
                f"🧬 Biological: {mds.biological_suggestion.reasoning}"
            )
        
        if mds.kinetic_suggestion:
            confidences.append(mds.kinetic_suggestion.confidence)
            reasoning_parts.append(
                f"⚡ Kinetic: {mds.kinetic_suggestion.reasoning}"
            )
        
        # Combined confidence (average of available domains)
        mds.combined_confidence = sum(confidences) / len(confidences) if confidences else 0.0
        
        # Combined reasoning (all perspectives)
        mds.combined_reasoning = "\n".join(reasoning_parts)
    
    def create_synthetic_suggestion(
        self,
        element_id: str,
        element_type: str,
        action: str,
        parameters: Dict[str, Any],
        confidence: float,
        reasoning: str,
        category: str
    ) -> Suggestion:
        """Create a suggestion from inference method results.
        
        Helper method to convert inference engine outputs into Suggestion objects.
        
        Args:
            element_id: Target element ID
            element_type: "place", "transition", "arc"
            action: Action type (e.g., "set_marking", "set_rate")
            parameters: Parameters for the action
            confidence: Confidence score (0-1)
            reasoning: Explanation text
            category: "structural", "biological", or "kinetic"
            
        Returns:
            Suggestion instance
        """
        return Suggestion(
            action=action,
            category=category,
            parameters=parameters,
            confidence=confidence,
            reasoning=reasoning,
            preview_elements=[element_id]
        )
    
    def enrich_structural_with_biology(
        self,
        structural_suggestion: Suggestion,
        element_id: str
    ) -> Optional[Suggestion]:
        """Enrich a structural suggestion with biological context.
        
        Example: "Add 5 tokens to P3" becomes:
        "Add 5 tokens to P3 (ATP, C00002, typical range 1-10 mM)"
        
        Args:
            structural_suggestion: Original structural suggestion
            element_id: Element ID (place)
            
        Returns:
            Enriched biological suggestion, or None
        """
        if not self.kb:
            return None
        
        # Get compound info from KB
        place_data = self.kb.get_place(element_id)
        if not place_data or not place_data.get('compound_id'):
            return None
        
        compound_id = place_data['compound_id']
        compound_data = self.kb.get_compound(compound_id)
        
        if not compound_data:
            return None
        
        # Create enriched reasoning
        compound_name = compound_data.get('name', compound_id)
        formula = compound_data.get('formula', '')
        
        enriched_reasoning = (
            f"Place represents {compound_name} ({compound_id})"
        )
        if formula:
            enriched_reasoning += f", formula: {formula}"
        
        # Typical concentration context
        if structural_suggestion.action == "set_marking":
            enriched_reasoning += ". Typical cellular concentration: 1-10 mM"
        
        return Suggestion(
            action="annotate_biology",
            category="biological",
            parameters={
                "compound_id": compound_id,
                "compound_name": compound_name,
                "formula": formula
            },
            confidence=0.90,  # High confidence for known compounds
            reasoning=enriched_reasoning,
            preview_elements=[element_id]
        )
    
    def enrich_structural_with_kinetics(
        self,
        structural_suggestion: Suggestion,
        element_id: str
    ) -> Optional[Suggestion]:
        """Enrich a structural suggestion with kinetic context.
        
        Example: "Add source transition" becomes:
        "Add source transition with rate 0.5 mM/s (based on EC 2.7.1.1)"
        
        Args:
            structural_suggestion: Original structural suggestion
            element_id: Element ID (transition)
            
        Returns:
            Enriched kinetic suggestion, or None
        """
        if not self.kb:
            return None
        
        # Get transition/reaction info
        transition_data = self.kb.get_transition(element_id)
        if not transition_data or not transition_data.get('reaction_id'):
            return None
        
        reaction_id = transition_data['reaction_id']
        reaction_data = self.kb.get_reaction(reaction_id)
        
        if not reaction_data:
            return None
        
        # Get kinetic parameters
        ec_number = reaction_data.get('ec_number')
        current_rate = reaction_data.get('current_rate')
        
        if not current_rate and ec_number:
            # Suggest rate from BRENDA/literature
            enriched_reasoning = (
                f"Transition represents {reaction_id} (EC {ec_number}). "
                f"Suggested rate: 0.5 mM/s from BRENDA database"
            )
            
            return Suggestion(
                action="set_rate",
                category="kinetic",
                parameters={
                    "transition_id": element_id,
                    "rate": 0.5,
                    "ec_number": ec_number
                },
                confidence=0.75,  # Moderate confidence from database
                reasoning=enriched_reasoning,
                preview_elements=[element_id]
            )
        
        return None
