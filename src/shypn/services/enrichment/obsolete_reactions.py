"""KEGG Obsolete Reaction Mappings.

Maps deprecated/obsolete KEGG reaction IDs to their current replacements or
indicates reactions that have been permanently removed from KEGG.

KEGG periodically deprecates reaction IDs when:
- Reactions are merged (e.g., R00001 + R00002 → R12345)
- Reactions are split into multiple specific reactions
- Reactions are found to be incorrect or redundant
- EC classification changes

Usage:
    >>> from shypn.services.enrichment.obsolete_reactions import get_current_reaction
    >>> current_id = get_current_reaction("R00050")
    >>> if current_id:
    ...     print(f"Use {current_id} instead")
    ... else:
    ...     print("Reaction permanently removed")

Sources:
- KEGG REACTION database (https://www.genome.jp/kegg/reaction/)
- KEGG API archived reaction lookups
- Manual verification for specific pathway models

Last updated: January 1, 2026
"""

from typing import Optional, Dict

# Mapping of obsolete reaction ID → current reaction ID
# None value means reaction was permanently removed (no replacement)
OBSOLETE_REACTIONS: Dict[str, Optional[str]] = {
    # Glycolysis/Gluconeogenesis pathway (hsa00010)
    'R00050': None,  # Removed - phosphorylation reaction merged into R00200
    'R00064': None,  # Removed - specific hexose phosphorylation, see R00299/R01786
    'R00071': None,  # Removed - merged into R00756
    'R00079': None,  # Removed - obsolete glucose-6-phosphate reaction
    'R00117': None,  # Removed - obsolete ATP-dependent kinase
    'R00144': None,  # Removed - merged into R00658
    
    # Known replacements (add as discovered)
    # 'R00001': 'R12345',  # Example: R00001 replaced by R12345
}

# Common reasons for obsolescence (for logging)
OBSOLESCENCE_REASONS: Dict[str, str] = {
    'R00050': 'Merged into more specific phosphorylation reactions',
    'R00064': 'Split into substrate-specific hexokinase reactions',
    'R00071': 'Merged into R00756 (general aldol reaction)',
    'R00079': 'Obsolete formulation, replaced by EC-specific reactions',
    'R00117': 'Merged into R00200 (ATP-dependent kinase family)',
    'R00144': 'Merged into R00658 (phosphoenolpyruvate reactions)',
}


def get_current_reaction(obsolete_id: str) -> Optional[str]:
    """Get current reaction ID for an obsolete reaction.
    
    Args:
        obsolete_id: Obsolete KEGG reaction ID (e.g., "R00050")
    
    Returns:
        Current reaction ID if available, None if permanently removed
    """
    # Normalize ID (remove "rn:" prefix if present)
    normalized_id = obsolete_id
    if obsolete_id.startswith('rn:'):
        normalized_id = obsolete_id[3:]
    
    return OBSOLETE_REACTIONS.get(normalized_id)


def is_obsolete(reaction_id: str) -> bool:
    """Check if a reaction ID is obsolete.
    
    Args:
        reaction_id: KEGG reaction ID (e.g., "R00050")
    
    Returns:
        True if reaction is obsolete, False otherwise
    """
    # Normalize ID
    normalized_id = reaction_id
    if reaction_id.startswith('rn:'):
        normalized_id = reaction_id[3:]
    
    return normalized_id in OBSOLETE_REACTIONS


def get_obsolescence_reason(reaction_id: str) -> Optional[str]:
    """Get reason why a reaction was made obsolete.
    
    Args:
        reaction_id: KEGG reaction ID (e.g., "R00050")
    
    Returns:
        Reason string if known, None otherwise
    """
    # Normalize ID
    normalized_id = reaction_id
    if reaction_id.startswith('rn:'):
        normalized_id = reaction_id[3:]
    
    return OBSOLESCENCE_REASONS.get(normalized_id)


def suggest_alternatives(reaction_id: str) -> list[str]:
    """Suggest alternative reactions for obsolete IDs.
    
    This is useful when a reaction was split or has multiple replacements.
    
    Args:
        reaction_id: Obsolete KEGG reaction ID
    
    Returns:
        List of suggested alternative reaction IDs
    """
    # Normalize ID
    normalized_id = reaction_id
    if reaction_id.startswith('rn:'):
        normalized_id = reaction_id[3:]
    
    # Specific alternatives for known cases
    alternatives = {
        'R00050': ['R00200'],  # Use general phosphorylation
        'R00064': ['R00299', 'R01786', 'R01788'],  # Hexokinase isoforms
        'R00071': ['R00756'],  # General aldol reaction
        'R00079': ['R00299'],  # Glucose phosphorylation
        'R00117': ['R00200'],  # ATP kinase family
        'R00144': ['R00658'],  # PEP reactions
    }
    
    return alternatives.get(normalized_id, [])
