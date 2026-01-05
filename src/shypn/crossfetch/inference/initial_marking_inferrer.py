"""
Initial Marking Inference Module

OOP-based system for inferring biochemically-realistic initial markings
for Petri net places using compound identity resolution.

Author: Shypn Development Team
Date: January 2026
"""

from typing import Optional, Tuple, List, Dict, Any
from dataclasses import dataclass
from enum import Enum
import logging

from ...thermodynamics.compound_resolver import CompoundResolver


class CompoundClass(Enum):
    """Classification of biochemical compounds for concentration inference."""
    ENERGY_CURRENCY = "energy_currency"  # ATP, GTP, CTP, UTP
    COFACTOR = "cofactor"  # NAD, NADH, NADP, NADPH, FAD, FADH2
    COENZYME_A = "coenzyme_a"  # CoA derivatives
    CENTRAL_METABOLITE = "central_metabolite"  # Glucose, pyruvate, etc.
    AMINO_ACID = "amino_acid"  # Amino acids
    NUCLEOTIDE = "nucleotide"  # Nucleotides
    LIPID = "lipid"  # Fatty acids, phospholipids
    SECONDARY_METABOLITE = "secondary_metabolite"  # Less common compounds
    UNKNOWN = "unknown"  # Unclassified


@dataclass
class InitialMarkingSuggestion:
    """Suggestion for initial marking of a place.
    
    Attributes:
        place_id: ID of the place
        tokens: Suggested number of tokens
        confidence: Confidence score (0.0-1.0)
        reasoning: Human-readable explanation
        compound_class: Classification of the compound
        compound_id: KEGG compound ID (if available)
        compound_names: List of compound names
    """
    place_id: str
    tokens: int
    confidence: float
    reasoning: str
    compound_class: CompoundClass
    compound_id: Optional[str] = None
    compound_names: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'place_id': self.place_id,
            'tokens': self.tokens,
            'confidence': self.confidence,
            'reasoning': self.reasoning,
            'compound_class': self.compound_class.value,
            'compound_id': self.compound_id,
            'compound_names': self.compound_names
        }


class CompoundClassifier:
    """Classifies compounds into biochemical categories.
    
    Uses compound names and KEGG IDs to determine the role
    and typical concentration range of metabolites.
    """
    
    # KEGG IDs for well-known central metabolites
    CENTRAL_METABOLITES = {
        "C00031": "D-Glucose",
        "C00022": "Pyruvate", 
        "C00068": "Thiamine pyrophosphate",
        "C00074": "Phosphoenolpyruvate",
        "C00036": "Oxaloacetate",
        "C00024": "Acetyl-CoA",
        "C00149": "Malate",
        "C00158": "Citrate"
    }
    
    # Energy currency compound names
    ENERGY_CURRENCIES = ["ATP", "GTP", "CTP", "UTP", "ADP", "GDP", "CDP", "UDP"]
    
    # Cofactor names
    COFACTORS = ["NAD", "NADH", "NAD+", "NADP", "NADPH", "NADP+", 
                 "FAD", "FADH2", "FMN", "FMNH2"]
    
    # Amino acid KEGG prefix
    AMINO_ACID_PATTERN = "C00"  # Most amino acids are C000xx
    
    def __init__(self):
        """Initialize classifier."""
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def classify(self, compound_id: Optional[str], 
                compound_names: Optional[List[str]]) -> CompoundClass:
        """Classify compound based on ID and names.
        
        Args:
            compound_id: KEGG compound ID (e.g., "C00002")
            compound_names: List of compound names (e.g., ["ATP", "Adenosine triphosphate"])
            
        Returns:
            CompoundClass enum value
        """
        if not compound_id and not compound_names:
            return CompoundClass.UNKNOWN
        
        # Check names first (more reliable)
        if compound_names:
            names_upper = [name.upper() for name in compound_names]
            
            # Energy currency
            for name in names_upper:
                if any(ec in name for ec in self.ENERGY_CURRENCIES):
                    return CompoundClass.ENERGY_CURRENCY
            
            # Cofactors
            for name in names_upper:
                if any(cf in name for cf in self.COFACTORS):
                    return CompoundClass.COFACTOR
            
            # Coenzyme A derivatives
            for name in compound_names:
                if "CoA" in name or "Coenzyme A" in name:
                    return CompoundClass.COENZYME_A
        
        # Check KEGG ID patterns
        if compound_id:
            # Central metabolites (curated list)
            if compound_id in self.CENTRAL_METABOLITES:
                return CompoundClass.CENTRAL_METABOLITE
            
            # Amino acids (typically C000xx range)
            if compound_id.startswith("C000") and len(compound_id) == 6:
                # Many amino acids in this range
                return CompoundClass.AMINO_ACID
        
        # Default to secondary metabolite
        return CompoundClass.SECONDARY_METABOLITE


class ConcentrationEstimator:
    """Estimates typical cellular concentrations for compound classes.
    
    Provides literature-based default concentrations (in mM)
    for different classes of biochemical compounds.
    """
    
    # Typical cellular concentrations (mM) - Literature values
    # Source: Bionumbers database, biochemistry textbooks
    CONCENTRATION_RANGES = {
        CompoundClass.ENERGY_CURRENCY: (3.0, 10.0, 5.0),  # (min, max, typical)
        CompoundClass.COFACTOR: (0.1, 2.0, 1.0),
        CompoundClass.COENZYME_A: (0.1, 1.0, 0.5),
        CompoundClass.CENTRAL_METABOLITE: (0.5, 5.0, 2.0),
        CompoundClass.AMINO_ACID: (0.1, 1.0, 0.5),
        CompoundClass.NUCLEOTIDE: (0.5, 2.0, 1.0),
        CompoundClass.LIPID: (0.01, 0.5, 0.1),
        CompoundClass.SECONDARY_METABOLITE: (0.01, 1.0, 0.5),
        CompoundClass.UNKNOWN: (0.1, 1.0, 0.5),
    }
    
    # Confidence scores by compound class
    CONFIDENCE_SCORES = {
        CompoundClass.ENERGY_CURRENCY: 0.85,  # Well-known, literature values
        CompoundClass.COFACTOR: 0.75,
        CompoundClass.COENZYME_A: 0.70,
        CompoundClass.CENTRAL_METABOLITE: 0.75,
        CompoundClass.AMINO_ACID: 0.65,
        CompoundClass.NUCLEOTIDE: 0.65,
        CompoundClass.LIPID: 0.60,
        CompoundClass.SECONDARY_METABOLITE: 0.50,
        CompoundClass.UNKNOWN: 0.40,
    }
    
    def __init__(self, scale_factor: float = 10.0):
        """Initialize estimator.
        
        Args:
            scale_factor: Tokens per mM (default: 10)
        """
        self.scale_factor = scale_factor
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def estimate_tokens(self, compound_class: CompoundClass) -> Tuple[int, float, str]:
        """Estimate tokens for a compound class.
        
        Args:
            compound_class: Classification of the compound
            
        Returns:
            Tuple of (tokens, confidence, reasoning)
        """
        # Get concentration range
        min_conc, max_conc, typical_conc = self.CONCENTRATION_RANGES[compound_class]
        
        # Convert to tokens
        tokens = int(typical_conc * self.scale_factor)
        
        # Get confidence
        confidence = self.CONFIDENCE_SCORES[compound_class]
        
        # Build reasoning
        reasoning = self._build_reasoning(compound_class, typical_conc, tokens)
        
        return tokens, confidence, reasoning
    
    def _build_reasoning(self, compound_class: CompoundClass, 
                        concentration_mM: float, tokens: int) -> str:
        """Build human-readable reasoning string.
        
        Args:
            compound_class: Classification
            concentration_mM: Concentration in mM
            tokens: Calculated tokens
            
        Returns:
            Reasoning string
        """
        class_descriptions = {
            CompoundClass.ENERGY_CURRENCY: "energy currency (ATP, GTP, etc.)",
            CompoundClass.COFACTOR: "cofactor (NAD, FAD, etc.)",
            CompoundClass.COENZYME_A: "Coenzyme A derivative",
            CompoundClass.CENTRAL_METABOLITE: "central metabolite",
            CompoundClass.AMINO_ACID: "amino acid",
            CompoundClass.NUCLEOTIDE: "nucleotide",
            CompoundClass.LIPID: "lipid",
            CompoundClass.SECONDARY_METABOLITE: "secondary metabolite",
            CompoundClass.UNKNOWN: "compound",
        }
        
        desc = class_descriptions.get(compound_class, "compound")
        return f"Compound is {desc}, typical concentration: {concentration_mM} mM ({tokens} tokens)"


class InitialMarkingInferrer:
    """Main class for inferring initial markings from compound identities.
    
    Integrates compound resolution, classification, and concentration
    estimation to provide biochemically-realistic initial markings.
    
    Example:
        >>> inferrer = InitialMarkingInferrer()
        >>> suggestion = inferrer.infer_marking(place)
        >>> if suggestion:
        >>>     print(f"{place.id}: {suggestion.tokens} tokens (confidence: {suggestion.confidence})")
    """
    
    def __init__(self, scale_factor: float = 10.0):
        """Initialize inferrer.
        
        Args:
            scale_factor: Tokens per mM concentration (default: 10)
        """
        self.resolver = CompoundResolver()
        self.classifier = CompoundClassifier()
        self.estimator = ConcentrationEstimator(scale_factor=scale_factor)
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def infer_marking(self, place: Any) -> Optional[InitialMarkingSuggestion]:
        """Infer initial marking for a place.
        
        Args:
            place: Place object with name and/or metadata
            
        Returns:
            InitialMarkingSuggestion or None if unable to infer
        """
        # Extract identifier from place
        identifier = self._extract_identifier(place)
        if not identifier:
            self.logger.debug(f"Place {place.id}: No identifier found")
            return None
        
        # Resolve compound identity
        identity = self.resolver.resolve(identifier)
        if not identity:
            self.logger.debug(f"Place {place.id}: Could not resolve '{identifier}'")
            return None
        
        # Classify compound
        compound_class = self.classifier.classify(
            identity.kegg_id, 
            identity.names
        )
        
        # Estimate tokens
        tokens, confidence, reasoning = self.estimator.estimate_tokens(compound_class)
        
        # Build suggestion
        suggestion = InitialMarkingSuggestion(
            place_id=place.id,
            tokens=tokens,
            confidence=confidence,
            reasoning=reasoning,
            compound_class=compound_class,
            compound_id=identity.kegg_id,
            compound_names=identity.names
        )
        
        self.logger.info(
            f"Place {place.id} ({identifier}): Suggested {tokens} tokens "
            f"(class: {compound_class.value}, confidence: {confidence:.0%})"
        )
        
        return suggestion
    
    def infer_markings_batch(self, places: List[Any]) -> List[InitialMarkingSuggestion]:
        """Infer markings for multiple places.
        
        Args:
            places: List of place objects
            
        Returns:
            List of InitialMarkingSuggestion (only successful inferences)
        """
        suggestions = []
        
        for place in places:
            # Skip places that already have tokens
            if hasattr(place, 'tokens') and place.tokens > 0:
                self.logger.debug(f"Place {place.id}: Already has {place.tokens} tokens, skipping")
                continue
            
            suggestion = self.infer_marking(place)
            if suggestion:
                suggestions.append(suggestion)
        
        self.logger.info(
            f"Inferred markings for {len(suggestions)}/{len(places)} places"
        )
        
        return suggestions
    
    def _extract_identifier(self, place: Any) -> Optional[str]:
        """Extract compound identifier from place.
        
        Tries multiple sources in priority order:
        1. place.metadata['kegg_id']
        2. place.metadata['chebi_id']
        3. place.name
        
        Args:
            place: Place object
            
        Returns:
            Identifier string or None
        """
        # Try KEGG ID from metadata
        if hasattr(place, 'metadata') and isinstance(place.metadata, dict):
            kegg_id = place.metadata.get('kegg_id')
            if kegg_id:
                return kegg_id
            
            # Try ChEBI ID
            chebi_id = place.metadata.get('chebi_id')
            if chebi_id:
                return chebi_id
        
        # Fallback to place name
        if hasattr(place, 'name') and place.name:
            return place.name
        
        return None
