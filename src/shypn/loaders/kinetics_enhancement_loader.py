"""
Import Enhancement Loader

Thin wrapper for enhancing imported models with kinetic properties.
This is the integration point between importers and the heuristic system.

Usage in KEGG Importer:
    from shypn.loaders.kinetics_enhancement_loader import enhance_kegg_transitions
    
    enhance_kegg_transitions(transitions, reactions)

Usage in SBML Importer:
    from shypn.loaders.kinetics_enhancement_loader import enhance_sbml_transitions
    
    enhance_sbml_transitions(transitions, reactions)
"""

from typing import List, Dict, Optional
import logging

from shypn.heuristic import KineticsAssigner, AssignmentResult


class KineticsEnhancementLoader:
    """
    Thin loader for kinetics enhancement.
    
    Minimal logic - just delegates to KineticsAssigner.
    Supports hybrid API database with offline mode.
    """
    
    def __init__(self, offline_mode: bool = False):
        """
        Initialize loader.
        
        Args:
            offline_mode: If True, skip API calls (cache + fallback only)
        """
        self.assigner = KineticsAssigner(offline_mode=offline_mode)
        self.logger = logging.getLogger(__name__)
        self.offline_mode = offline_mode
    
    def enhance_transitions(
        self,
        transitions: List,
        reactions: Optional[List] = None,
        source: str = 'kegg'
    ) -> Dict[str, AssignmentResult]:
        """
        Enhance transitions with kinetic properties.
        
        Args:
            transitions: List of Transition objects
            reactions: List of corresponding reaction objects (optional)
            source: Source type ('kegg', 'sbml', 'biomodels')
        
        Returns:
            Dict mapping transition.name → AssignmentResult
        """
        if not transitions:
            self.logger.warning("No transitions to enhance")
            return {}
        
        # Prepare reactions list
        if reactions is None:
            reactions = [None] * len(transitions)
        elif len(reactions) < len(transitions):
            # Pad with None
            reactions = reactions + [None] * (len(transitions) - len(reactions))
        
        self.logger.info(
            f"Enhancing {len(transitions)} transitions from {source.upper()}"
        )
        
        # Delegate to assigner
        results = {}
        
        for i, transition in enumerate(transitions):
            # Skip source/sink transitions
            if transition.is_source or transition.is_sink:
                self.logger.debug(f"Skipping source/sink: {transition.name}")
                continue
            
            reaction = reactions[i] if i < len(reactions) else None
            
            # TODO: Extract substrate/product places from transition's arcs
            # For now, pass None and let assigner handle it
            
            result = self.assigner.assign(
                transition=transition,
                reaction=reaction,
                substrate_places=None,
                product_places=None,
                source=source
            )
            
            results[transition.name] = result
        
        # Log summary
        self._log_summary(results)
        
        return results
    
    def _log_summary(self, results: Dict[str, AssignmentResult]) -> None:
        """Log summary of enhancement results."""
        total = len(results)
        successful = sum(1 for r in results.values() if r.success)
        
        # Count by confidence
        high_conf = sum(
            1 for r in results.values()
            if r.success and r.confidence.value == 'high'
        )
        medium_conf = sum(
            1 for r in results.values()
            if r.success and r.confidence.value == 'medium'
        )
        low_conf = sum(
            1 for r in results.values()
            if r.success and r.confidence.value == 'low'
        )
        
        self.logger.info(
            f"Enhancement complete: {successful}/{total} successful "
            f"(High: {high_conf}, Medium: {medium_conf}, Low: {low_conf})"
        )


# Convenience functions for importers

_loader = None
_offline_mode = False

def _get_loader(offline_mode: bool = False) -> KineticsEnhancementLoader:
    """
    Get singleton loader instance.
    
    Args:
        offline_mode: If True, skip API calls (cache + fallback only)
    """
    global _loader, _offline_mode
    if _loader is None or _offline_mode != offline_mode:
        _loader = KineticsEnhancementLoader(offline_mode=offline_mode)
        _offline_mode = offline_mode
    return _loader


def enhance_kegg_transitions(
    transitions: List,
    reactions: Optional[List] = None,
    offline_mode: bool = False
) -> Dict[str, AssignmentResult]:
    """
    Enhance KEGG-imported transitions with kinetic properties.
    
    Uses hybrid three-tier database:
    - Tier 1: Local cache (fast)
    - Tier 2: External APIs (BRENDA - future, if online)
    - Tier 3: Fallback database (10 glycolysis enzymes)
    
    Args:
        transitions: List of Transition objects from KEGG import
        reactions: List of KEGG reaction objects (optional)
        offline_mode: If True, skip API calls (default: False)
    
    Returns:
        Dict mapping transition.name → AssignmentResult
    """
    loader = _get_loader(offline_mode=offline_mode)
    return loader.enhance_transitions(transitions, reactions, source='kegg')


def enhance_sbml_transitions(
    transitions: List,
    reactions: Optional[List] = None,
    offline_mode: bool = False
) -> Dict[str, AssignmentResult]:
    """
    Enhance SBML-imported transitions with kinetic properties.
    
    Note: SBML should already have explicit kinetics, so this will
    mostly skip transitions. Use for filling gaps only.
    
    Args:
        transitions: List of Transition objects from SBML import
        reactions: List of SBML reaction objects (optional)
        offline_mode: If True, skip API calls (default: False)
    
    Returns:
        Dict mapping transition.name → AssignmentResult
    """
    loader = _get_loader(offline_mode=offline_mode)
    return loader.enhance_transitions(transitions, reactions, source='sbml')


def enhance_biomodels_transitions(
    transitions: List,
    reactions: Optional[List] = None,
    offline_mode: bool = False
) -> Dict[str, AssignmentResult]:
    """
    Enhance BioModels-imported transitions with kinetic properties.
    
    Args:
        transitions: List of Transition objects from BioModels import
        reactions: List of reaction objects (optional)
        offline_mode: If True, skip API calls (default: False)
    
    Returns:
        Dict mapping transition.name → AssignmentResult
    """
    loader = _get_loader(offline_mode=offline_mode)
    return loader.enhance_transitions(transitions, reactions, source='biomodels')
