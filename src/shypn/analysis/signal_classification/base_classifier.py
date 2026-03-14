#!/usr/bin/env python3
"""Base Signal Classifier - Abstract base class for signal type detection.

This module defines the interface and common functionality for all signal
type classifiers. Each specific classifier (Energy, Spatial, Quorum, Regulatory)
inherits from this base class.

Author: Simão Eugénio
Date: December 31, 2025
"""

from abc import ABC, abstractmethod
from typing import Set, Dict, List, Tuple
import re
import logging

from .rate_normalizer import RateFunctionNormalizer


class BaseSignalClassifier(ABC):
    """Abstract base class for signal type classifiers.
    
    Each subclass implements detection logic for a specific signal type
    according to the Extended Bio-PN formalism:
    
    - EnergySignalClassifier: Detects energy orchestrators
    - SpatialSignalClassifier: Detects spatial constraints
    - QuorumSignalClassifier: Detects quorum sensing signals
    - RegulatorySignalClassifier: Detects regulatory decision variables
    
    The classification process analyzes:
    1. Place names (lexical patterns)
    2. Rate function references (dependency patterns)
    3. Network topology (arc connectivity)
    4. Dynamic behavior (threshold detection, accumulation)
    """
    
    # Common keywords to exclude from place name detection
    MATH_KEYWORDS = {
        'min', 'max', 'abs', 'exp', 'log', 'log10', 'log2', 'sqrt', 'pow',
        'sin', 'cos', 'tan', 'sinh', 'cosh', 'tanh',
        'asin', 'acos', 'atan', 'atan2',
        'ceil', 'floor', 'round', 'trunc',
        'pi', 'e', 'inf', 'nan',
        'time', 't', 'tau',
        'True', 'False', 'None',
    }
    
    def __init__(self, model, confidence_threshold: float = 0.5):
        """Initialize base classifier.
        
        Args:
            model: Bio-PN model instance with places and transitions
            confidence_threshold: Minimum confidence score (0.0-1.0) for classification
        """
        self.model = model
        self.confidence_threshold = confidence_threshold
        self.logger = logging.getLogger(self.__class__.__name__)
        self.rate_normalizer = RateFunctionNormalizer(self.logger)
        
    @abstractmethod
    def get_signal_type(self) -> str:
        """Return the signal type this classifier detects.
        
        Returns:
            Signal type string ('ENERGY', 'SPATIAL', 'QUORUM', 'REGULATORY')
        """
        pass
    
    @abstractmethod
    def get_lexical_patterns(self) -> List[str]:
        """Return regex patterns for place name detection.
        
        Returns:
            List of regex patterns that match typical place names for this signal type
        """
        pass
    
    @abstractmethod
    def get_biochemical_indicators(self) -> Set[str]:
        """Return biochemical compound names indicative of this signal type.
        
        Returns:
            Set of compound names (e.g., {'ATP', 'NADH'} for energy)
        """
        pass
    
    @abstractmethod
    def analyze_topology(self, place) -> float:
        """Analyze network topology to compute confidence score.
        
        Examines arc connectivity patterns specific to this signal type.
        
        Args:
            place: Place object to analyze
            
        Returns:
            Confidence score (0.0-1.0)
        """
        pass
    
    @abstractmethod
    def analyze_dynamics(self, place, rate_functions: List[str]) -> float:
        """Analyze dynamic behavior from rate functions.
        
        Args:
            place: Place object to analyze
            rate_functions: List of rate function strings that reference this place
            
        Returns:
            Confidence score (0.0-1.0)
        """
        pass
    
    def classify(self, place) -> Tuple[bool, float, Dict[str, float]]:
        """Classify a place and return confidence score with breakdown.
        
        Args:
            place: Place object to classify
            
        Returns:
            Tuple of (is_match, total_confidence, score_breakdown)
            - is_match: True if confidence >= threshold
            - total_confidence: Overall confidence score (0.0-1.0)
            - score_breakdown: Dict mapping criterion to individual score
        """
        scores = {}
        
        # 1. Lexical analysis (place name)
        scores['lexical'] = self._analyze_lexical(place)
        
        # 2. Biochemical analysis (compound matching)
        scores['biochemical'] = self._analyze_biochemical(place)
        
        # 3. Topology analysis (arc patterns)
        scores['topology'] = self.analyze_topology(place)
        
        # 4. Dynamic analysis (rate function patterns)
        rate_functions = self._get_rate_functions_referencing(place)
        scores['dynamics'] = self.analyze_dynamics(place, rate_functions)
        
        # Compute weighted average
        weights = {
            'lexical': 0.2,
            'biochemical': 0.3,
            'topology': 0.2,
            'dynamics': 0.3,
        }
        
        total_confidence = sum(
            scores[criterion] * weights[criterion]
            for criterion in scores
        )
        
        is_match = total_confidence >= self.confidence_threshold
        
        self.logger.debug(
            f"{self.__class__.__name__} analysis for '{place.name}': "
            f"confidence={total_confidence:.2f}, scores={scores}"
        )
        
        return is_match, total_confidence, scores
    
    def _analyze_lexical(self, place) -> float:
        """Analyze place name against lexical patterns.
        
        Args:
            place: Place object
            
        Returns:
            Confidence score (0.0-1.0)
        """
        place_name = place.name.lower()
        patterns = self.get_lexical_patterns()
        
        for pattern in patterns:
            if re.search(pattern, place_name, re.IGNORECASE):
                return 1.0
        
        return 0.0
    
    def _analyze_biochemical(self, place) -> float:
        """Analyze place name for biochemical compound indicators.
        
        Args:
            place: Place object
            
        Returns:
            Confidence score (0.0-1.0)
        """
        place_name = place.name.upper()
        indicators = self.get_biochemical_indicators()
        
        # Check for exact match or compound as part of name
        for compound in indicators:
            if compound in place_name:
                return 1.0
        
        return 0.0
    
    def _get_rate_functions_referencing(self, place) -> List[str]:
        """Get all rate functions that reference this place.
        
        Handles three rate types:
        1. Numeric: Simple float (e.g., rate = 2.5)
        2. Expression: String formula (e.g., rate = "2.0 * ATP * Glucose")
        3. Catalog: Kinetic metadata with formula and rate_type
        
        Args:
            place: Place object
            
        Returns:
            List of rate function strings that reference this place
        """
        rate_functions = []
        
        for transition in self.model.transitions:
            # Extract rate expressions from all possible sources
            expressions = self._extract_rate_expressions(transition)
            
            # Filter expressions that reference this place
            for expr in expressions:
                if self._expression_references_place(expr, place):
                    rate_functions.append(expr)
        
        return rate_functions
    
    def _extract_rate_expressions(self, transition) -> List[str]:
        """Extract all rate expressions from a transition.
        
        Handles:
        - transition.rate (numeric or expression string)
        - transition.properties['rate_function'] (GUI rate function field)
        - transition.rate_forward / rate_reverse (bidirectional)
        - transition.kinetic_metadata.formula (catalog functions)
        
        Excludes:
        - transition.properties['sbml_formula'] - SBML formulas with assignment rule dependencies
        
        Note: The transition property dialog has TWO rate fields:
        - "Rate" field: numeric immediate value → stored in transition.rate
        - "Rate function" field: complex expression → stored in properties['rate_function']
        
        All function call syntax (e.g., michaelis_menten(S, vmax=1.0, km=0.5))
        is normalized to biochemical expressions (e.g., Vmax * S / (Km + S))
        for pattern matching in dynamics analysis.
        
        IMPORTANT: SBML formulas stored in properties['sbml_formula'] are EXCLUDED
        because they often contain variables defined by SBML assignment rules.
        Assignment rules like "AMP = (P - ATP - ADP)" are algebraic relationships,
        not kinetic rate functions. Including them would cause incorrect signal
        classification. See BIOMD0000000061 for an example.
        
        Args:
            transition: Transition object
            
        Returns:
            List of normalized expression strings
        """
        expressions = []
        
        # 1. Check standard rate attribute
        if hasattr(transition, 'rate') and transition.rate:
            normalized = self.rate_normalizer.normalize(transition.rate)
            expressions.extend(normalized)
        
        # 2. Check GUI rate function field (separate from numeric rate)
        if hasattr(transition, 'properties') and transition.properties:
            rate_func = transition.properties.get('rate_function')
            if rate_func:
                normalized = self.rate_normalizer.normalize(rate_func)
                # Avoid duplicates
                for expr in normalized:
                    if expr not in expressions:
                        expressions.append(expr)
            
            # IMPORTANT: Skip sbml_formula - these often contain assignment rule variables
            # Assignment rules like "AMP = (P - ATP - ADP)" define algebraic relationships
            # that are NOT kinetic rate functions and should not be analyzed for
            # biological signal patterns.
            # See: BIOMD0000000061 (yeast glycolysis) for example of assignment rule issues
            # The sbml_formula is preserved for SBML kinetics service but excluded from
            # signal classification to avoid incorrect pattern matching.
        
        # 3. Check bidirectional rates (forward/reverse)
        if hasattr(transition, 'rate_forward') and transition.rate_forward:
            normalized = self.rate_normalizer.normalize(transition.rate_forward)
            expressions.extend(normalized)
        
        if hasattr(transition, 'rate_reverse') and transition.rate_reverse:
            normalized = self.rate_normalizer.normalize(transition.rate_reverse)
            expressions.extend(normalized)
        
        # 4. Check kinetic metadata (catalog functions)
        if hasattr(transition, 'kinetic_metadata') and transition.kinetic_metadata:
            metadata = transition.kinetic_metadata
            
            # Extract formula from metadata
            if hasattr(metadata, 'formula') and metadata.formula:
                formula_str = str(metadata.formula)
                normalized = self.rate_normalizer.normalize(formula_str)
                expressions.extend(normalized)
            
            # Extract rate_type specific patterns
            if hasattr(metadata, 'rate_type') and metadata.rate_type:
                # Construct pattern from rate_type and parameters
                catalog_expr = self._construct_catalog_expression(metadata)
                if catalog_expr and catalog_expr not in expressions:
                    expressions.append(catalog_expr)
        
        return expressions

    
    def _construct_catalog_expression(self, metadata) -> str:
        """Construct expression from catalog function metadata.
        
        Converts kinetic metadata (rate_type + parameters) into
        a pseudo-expression for pattern analysis.
        
        Args:
            metadata: KineticMetadata object
            
        Returns:
            Pseudo-expression string representing the catalog function
        """
        rate_type = getattr(metadata, 'rate_type', None)
        parameters = getattr(metadata, 'parameters', {})
        
        if not rate_type:
            return ""
        
        rate_type_lower = rate_type.lower()
        
        # Michaelis-Menten: Vmax * S / (Km + S)
        if 'michaelis' in rate_type_lower or 'mm' in rate_type_lower:
            substrate = parameters.get('substrate', 'S')
            return f"Vmax * {substrate} / (Km + {substrate})"
        
        # Hill equation: Vmax * S^n / (K^n + S^n)
        elif 'hill' in rate_type_lower:
            substrate = parameters.get('substrate', 'S')
            n = parameters.get('n', 2)
            return f"Vmax * {substrate}^{n} / (K^{n} + {substrate}^{n})"
        
        # Mass action: k * A * B
        elif 'mass_action' in rate_type_lower or 'ma' in rate_type_lower:
            # Extract reactant names from parameters
            reactants = []
            for key in parameters:
                if key.startswith('reactant') or key in ['A', 'B', 'C']:
                    reactants.append(str(parameters[key]))
            return f"k * {' * '.join(reactants)}" if reactants else "k"
        
        # Reversible mass action: kf * A * B - kr * C * D
        elif 'reversible' in rate_type_lower:
            return "kf * substrates - kr * products"
        
        # Generic: just return rate_type as placeholder
        return f"<{rate_type}>"
    
    def _expression_references_place(self, expression: str, place) -> bool:
        """Check if expression references a place.
        
        Args:
            expression: Rate expression string
            place: Place object
            
        Returns:
            True if expression references the place
        """
        if not expression:
            return False
        
        # Simple name matching
        place_name = place.name
        
        # Word boundary check to avoid partial matches
        import re
        pattern = r'\b' + re.escape(place_name) + r'\b'
        return bool(re.search(pattern, expression, re.IGNORECASE))
    
    def _extract_place_references(self, formula: str) -> Set[str]:
        """Extract place names referenced in a formula.
        
        Args:
            formula: Rate function string
            
        Returns:
            Set of place names found in formula
        """
        if not formula:
            return set()
        
        # Extract identifiers (alphabetic sequences)
        pattern = r'\b[A-Za-z_][A-Za-z0-9_]*\b'
        identifiers = set(re.findall(pattern, formula))
        
        # Remove math keywords
        identifiers -= self.MATH_KEYWORDS
        
        # Keep only identifiers that match actual place names
        place_names = {p.name for p in self.model.places}
        return identifiers & place_names
    
    def _get_input_places(self, transition) -> Set:
        """Get input places for a transition (consumed tokens).
        
        Args:
            transition: Transition object
            
        Returns:
            Set of input place objects
        """
        input_places = set()
        
        for arc in self.model.arcs:
            if arc.target == transition:
                input_places.add(arc.source)
        
        return input_places
    
    def _get_output_places(self, transition) -> Set:
        """Get output places for a transition (produced tokens).
        
        Args:
            transition: Transition object
            
        Returns:
            Set of output place objects
        """
        output_places = set()
        
        for arc in self.model.arcs:
            if arc.source == transition:
                output_places.add(arc.target)
        
        return output_places
    
    def _get_test_inhibitor_places(self, transition) -> Set:
        """Get test/inhibitor arc places for a transition.
        
        Args:
            transition: Transition object
            
        Returns:
            Set of place objects connected by test/inhibitor arcs
        """
        regulatory_places = set()
        
        for arc in self.model.arcs:
            if arc.target == transition:
                if hasattr(arc, 'arc_type') and arc.arc_type in ['test', 'inhibitor']:
                    regulatory_places.add(arc.source)
        
        return regulatory_places
