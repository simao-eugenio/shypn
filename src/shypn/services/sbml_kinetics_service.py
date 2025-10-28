"""
SBML Kinetics Integration Service

Service for integrating SBML kinetic data into Petri net transitions.

Architecture:
- Uses object references (not IDs) to avoid ID conflicts
- Creates SBMLKineticMetadata for transitions with kinetic laws
- Respects existing metadata (never overwrites SBML or manual data)
- Thin service layer - delegates to domain classes

Design Principles:
- Object-oriented: Works with Transition objects directly
- Reference-based: Passes object references, not string IDs
- Immutable source: SBML kinetics are locked by default
- Separation of concerns: Service orchestrates, metadata classes handle logic
"""

from typing import List, Dict, Optional, Tuple
import logging

from shypn.data.pathway.pathway_data import PathwayData, Reaction, KineticLaw
from shypn.data.kinetics import (
    SBMLKineticMetadata,
    KineticMetadata,
    ConfidenceLevel,
    KineticSource
)


class SBMLKineticsIntegrationService:
    """
    Service for integrating SBML kinetic data into transitions.
    
    Uses object references to map reactions to transitions.
    Creates SBMLKineticMetadata for definitive kinetic tracking.
    """
    
    def __init__(self):
        """Initialize the service."""
        self.logger = logging.getLogger(__name__)
    
    def integrate_kinetics(
        self,
        transitions: List,  # List of Transition objects
        pathway_data: PathwayData,
        transition_reaction_map: Optional[Dict] = None,
        source_file: Optional[str] = None
    ) -> Dict[str, bool]:
        """
        Integrate SBML kinetic laws into transitions.
        
        Uses object references to map transitions to reactions.
        Only integrates kinetics that don't already exist (preservation logic).
        
        Args:
            transitions: List of Transition objects to enhance
            pathway_data: PathwayData with reactions and kinetic laws
            transition_reaction_map: Optional dict mapping transition object → reaction object
                                    If None, uses transition.name to match reaction.id
            source_file: SBML source filename (for metadata tracking)
        
        Returns:
            Dict mapping transition.name → success (True/False)
        """
        if not transitions:
            self.logger.warning("No transitions to integrate")
            return {}
        
        self.logger.info(f"Integrating SBML kinetics for {len(transitions)} transitions")
        
        # Build mapping if not provided (uses object references)
        if transition_reaction_map is None:
            transition_reaction_map = self._build_transition_reaction_map(
                transitions,
                pathway_data.reactions
            )
        
        results = {}
        integrated_count = 0
        skipped_count = 0
        
        for transition in transitions:
            # Skip source/sink transitions
            if transition.is_source or transition.is_sink:
                self.logger.debug(f"Skipping source/sink transition: {transition.name}")
                results[transition.name] = False
                skipped_count += 1
                continue
            
            # Check if should preserve existing kinetics
            if self._should_preserve_existing(transition):
                self.logger.debug(
                    f"Preserving existing kinetics for {transition.name} "
                    f"(source: {transition.kinetic_metadata.source.value})"
                )
                results[transition.name] = False
                skipped_count += 1
                continue
            
            # Get corresponding reaction (using object reference from map)
            reaction = transition_reaction_map.get(transition)
            if reaction is None:
                self.logger.debug(f"No reaction found for transition: {transition.name}")
                results[transition.name] = False
                skipped_count += 1
                continue
            
            # Check if reaction has kinetic law
            if reaction.kinetic_law is None:
                self.logger.debug(f"No kinetic law for reaction: {reaction.id}")
                results[transition.name] = False
                skipped_count += 1
                continue
            
            # Integrate the kinetic law
            success = self._integrate_kinetic_law(
                transition,
                reaction,
                reaction.kinetic_law,
                source_file
            )
            
            results[transition.name] = success
            if success:
                integrated_count += 1
            else:
                skipped_count += 1
        
        self.logger.info(
            f"SBML kinetics integration complete: "
            f"{integrated_count} integrated, {skipped_count} skipped"
        )
        
        return results
    
    def _build_transition_reaction_map(
        self,
        transitions: List,
        reactions: List[Reaction]
    ) -> Dict:
        """
        Build mapping from transition objects to reaction objects.
        
        Uses object references (not IDs) to avoid ID conflicts.
        Matches by name: transition.name → reaction.id
        
        Args:
            transitions: List of Transition objects
            reactions: List of Reaction objects
        
        Returns:
            Dict mapping transition object → reaction object
        """
        # Create reaction lookup by ID (for matching)
        reaction_by_id = {reaction.id: reaction for reaction in reactions}
        
        # Build object reference map
        transition_reaction_map = {}
        
        for transition in transitions:
            # Try to match transition.name to reaction.id
            # (Common convention: transition name matches reaction ID)
            reaction = reaction_by_id.get(transition.name)
            
            if reaction is not None:
                # Store object reference (not ID string)
                transition_reaction_map[transition] = reaction
            else:
                self.logger.debug(
                    f"No reaction match for transition: {transition.name}"
                )
        
        self.logger.info(
            f"Built transition→reaction map: "
            f"{len(transition_reaction_map)}/{len(transitions)} matched"
        )
        
        return transition_reaction_map
    
    def _should_preserve_existing(self, transition) -> bool:
        """
        Check if existing kinetics should be preserved.
        
        Preserves:
        - SBML kinetics (definitive)
        - Manual kinetics (high confidence)
        - Locked metadata
        
        Args:
            transition: Transition object
        
        Returns:
            True if should preserve, False if can overwrite
        """
        if not hasattr(transition, 'kinetic_metadata') or transition.kinetic_metadata is None:
            return False
        
        return KineticMetadata.should_preserve(transition.kinetic_metadata)
    
    def _integrate_kinetic_law(
        self,
        transition,
        reaction: Reaction,
        kinetic_law: KineticLaw,
        source_file: Optional[str]
    ) -> bool:
        """
        Integrate kinetic law into transition with metadata.
        
        Args:
            transition: Transition object (passed by reference)
            reaction: Reaction object (passed by reference)
            kinetic_law: KineticLaw from SBML
            source_file: SBML source filename
        
        Returns:
            True if integrated successfully
        """
        try:
            # Extract SBML metadata from kinetic law (if available)
            sbml_metadata = getattr(kinetic_law, 'sbml_metadata', {})
            
            # Create SBMLKineticMetadata
            metadata = SBMLKineticMetadata(
                source_file=source_file,
                rate_type=kinetic_law.rate_type,
                formula=kinetic_law.formula,
                parameters=kinetic_law.parameters.copy(),
                sbml_level=sbml_metadata.get('sbml_level'),
                sbml_version=sbml_metadata.get('sbml_version'),
                sbml_reaction_id=sbml_metadata.get('sbml_reaction_id'),
                sbml_model_id=sbml_metadata.get('sbml_model_id'),
            )
            
            # Attach metadata to transition (object reference, no ID storage)
            transition.kinetic_metadata = metadata
            
            # Also update transition.rate if parameters available
            if kinetic_law.parameters:
                # For Michaelis-Menten, use Vmax as rate
                if kinetic_law.rate_type == 'michaelis_menten':
                    vmax = kinetic_law.parameters.get('Vmax') or kinetic_law.parameters.get('vmax')
                    if vmax is not None:
                        transition.rate = vmax
                # For mass action, use rate constant
                elif kinetic_law.rate_type == 'mass_action':
                    k = kinetic_law.parameters.get('k') or kinetic_law.parameters.get('k1')
                    if k is not None:
                        transition.rate = k
            
            self.logger.debug(
                f"Integrated {kinetic_law.rate_type} kinetics for {transition.name} "
                f"(formula: {kinetic_law.formula[:50]}...)"
            )
            
            return True
            
        except Exception as e:
            self.logger.error(
                f"Failed to integrate kinetics for {transition.name}: {e}"
            )
            return False
    
    def get_integration_summary(self, transitions: List) -> Dict[str, int]:
        """
        Get summary statistics of kinetic integration.
        
        Args:
            transitions: List of Transition objects
        
        Returns:
            Dict with statistics
        """
        total = len(transitions)
        with_sbml_kinetics = 0
        with_manual_kinetics = 0
        with_other_kinetics = 0
        without_kinetics = 0
        
        for transition in transitions:
            if not hasattr(transition, 'kinetic_metadata') or transition.kinetic_metadata is None:
                without_kinetics += 1
            elif transition.kinetic_metadata.source == KineticSource.SBML:
                with_sbml_kinetics += 1
            elif transition.kinetic_metadata.source == KineticSource.MANUAL:
                with_manual_kinetics += 1
            else:
                with_other_kinetics += 1
        
        return {
            'total': total,
            'sbml_kinetics': with_sbml_kinetics,
            'manual_kinetics': with_manual_kinetics,
            'other_kinetics': with_other_kinetics,
            'without_kinetics': without_kinetics,
        }


# Convenience function for importers

def integrate_sbml_kinetics(
    transitions: List,
    pathway_data: PathwayData,
    source_file: Optional[str] = None
) -> Dict[str, bool]:
    """
    Convenience function to integrate SBML kinetics.
    
    Usage in SBML importer:
        from shypn.services.sbml_kinetics_service import integrate_sbml_kinetics
        
        results = integrate_sbml_kinetics(transitions, pathway_data, "model.sbml")
    
    Args:
        transitions: List of Transition objects
        pathway_data: PathwayData from SBML parser
        source_file: SBML source filename
    
    Returns:
        Dict mapping transition.name → success
    """
    service = SBMLKineticsIntegrationService()
    return service.integrate_kinetics(transitions, pathway_data, None, source_file)
