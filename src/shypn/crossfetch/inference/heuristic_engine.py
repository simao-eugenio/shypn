"""
Type-Aware Parameter Inference Engine

Intelligent inference system that detects transition types and infers
appropriate parameters using heuristics and multi-source data.

Author: Shypn Development Team
Date: November 2025
"""

from typing import Dict, Any, List, Optional, Tuple
import logging

from ..models.transition_types import (
    TransitionType, BiologicalSemantics,
    TransitionParameters, ImmediateParameters,
    TimedParameters, StochasticParameters,
    ContinuousParameters, InferenceResult
)
from ..fetchers.sabio_rk_kinetics_fetcher import SabioRKKineticsFetcher


class TransitionTypeDetector:
    """Detects transition type from model properties."""
    
    @staticmethod
    def detect_type(transition: Any) -> TransitionType:
        """Detect transition type from transition object.
        
        Args:
            transition: Transition object from model
            
        Returns:
            TransitionType enum
        """
        # Check if transition has transition_type attribute
        if hasattr(transition, 'transition_type'):
            type_str = str(transition.transition_type).lower()
            
            if 'immediate' in type_str:
                return TransitionType.IMMEDIATE
            elif 'timed' in type_str:
                return TransitionType.TIMED
            elif 'stochastic' in type_str:
                return TransitionType.STOCHASTIC
            elif 'continuous' in type_str:
                return TransitionType.CONTINUOUS
        
        # Fallback: infer from other properties
        # Check for rate function (continuous)
        if hasattr(transition, 'rate_function') and transition.rate_function:
            return TransitionType.CONTINUOUS
        
        # Check for delay (timed)
        if hasattr(transition, 'delay') and transition.delay is not None:
            return TransitionType.TIMED
        
        # Check for priority (immediate)
        if hasattr(transition, 'priority'):
            return TransitionType.IMMEDIATE
        
        # Default to unknown
        return TransitionType.UNKNOWN
    
    @staticmethod
    def infer_semantics(transition: Any, transition_type: TransitionType) -> BiologicalSemantics:
        """Infer biological semantics from transition label and type.
        
        Args:
            transition: Transition object
            transition_type: Detected transition type
            
        Returns:
            BiologicalSemantics enum
        """
        label = getattr(transition, 'label', '').lower()
        
        # Check for keywords in label
        if 'regulat' in label or 'activat' in label or 'inhibit' in label:
            return BiologicalSemantics.REGULATION
        
        if 'transport' in label or 'import' in label or 'export' in label:
            return BiologicalSemantics.TRANSPORT
        
        if 'burst' in label or 'pulse' in label:
            return BiologicalSemantics.BURST
        
        if 'expression' in label or 'gene' in label:
            return BiologicalSemantics.MASS_ACTION
        
        # Default by transition type
        if transition_type == TransitionType.IMMEDIATE:
            return BiologicalSemantics.BURST
        elif transition_type == TransitionType.TIMED:
            return BiologicalSemantics.DETERMINISTIC
        elif transition_type == TransitionType.STOCHASTIC:
            return BiologicalSemantics.MASS_ACTION
        elif transition_type == TransitionType.CONTINUOUS:
            return BiologicalSemantics.ENZYME_KINETICS
        
        return BiologicalSemantics.UNKNOWN


class HeuristicInferenceEngine:
    """Type-aware parameter inference engine.
    
    **Fast-First Strategy:**
    - Returns heuristic defaults immediately (no blocking)
    - Optionally enhances with database data in background
    - Builds local cache over time through platform use
    
    Data sources (progressive enhancement):
    - Heuristic defaults: Instant, 40-70% confidence
    - Local cache: Fast lookup from previous fetches
    - SABIO-RK: Background fetch, 80-95% confidence
    - BRENDA: Future, additional validation
    """
    
    def __init__(self, use_background_fetch: bool = False):
        """Initialize inference engine.
        
        Args:
            use_background_fetch: If True, enhance with database queries in background
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Configuration
        self.use_background_fetch = use_background_fetch
        
        # Initialize fetchers (lazy - only if needed)
        self._sabio_rk_fetcher = None
        
        # Type detector
        self.type_detector = TransitionTypeDetector()
        
        # Local cache for database results
        self._parameter_cache: Dict[Tuple[str, str], ContinuousParameters] = {}
    
    @property
    def sabio_rk_fetcher(self):
        """Lazy initialization of SABIO-RK fetcher."""
        if self._sabio_rk_fetcher is None and self.use_background_fetch:
            self._sabio_rk_fetcher = SabioRKKineticsFetcher()
        return self._sabio_rk_fetcher
    
    def infer_parameters(self,
                        transition: Any,
                        organism: str = "Homo sapiens") -> InferenceResult:
        """Infer parameters for a transition.
        
        Args:
            transition: Transition object from model
            organism: Target organism
            
        Returns:
            InferenceResult with inferred parameters and alternatives
        """
        # Step 1: Detect transition type
        transition_type = self.type_detector.detect_type(transition)
        
        # Step 2: Infer biological semantics
        semantics = self.type_detector.infer_semantics(transition, transition_type)
        
        # Step 3: Infer parameters based on type
        if transition_type == TransitionType.IMMEDIATE:
            parameters = self._infer_immediate(transition, semantics, organism)
        elif transition_type == TransitionType.TIMED:
            parameters = self._infer_timed(transition, semantics, organism)
        elif transition_type == TransitionType.STOCHASTIC:
            parameters = self._infer_stochastic(transition, semantics, organism)
        elif transition_type == TransitionType.CONTINUOUS:
            parameters = self._infer_continuous(transition, semantics, organism)
        else:
            self.logger.warning(f"Unknown transition type for {transition.id}")
            parameters = TransitionParameters(
                transition_type=TransitionType.UNKNOWN,
                biological_semantics=BiologicalSemantics.UNKNOWN,
                organism=organism
            )
        
        # Create result
        result = InferenceResult(
            transition_id=getattr(transition, 'id', 'unknown'),
            parameters=parameters,
            alternatives=[],
            inference_metadata={
                'detected_type': transition_type.value,
                'inferred_semantics': semantics.value
            }
        )
        
        return result
    
    def _infer_immediate(self,
                        transition: Any,
                        semantics: BiologicalSemantics,
                        organism: str) -> ImmediateParameters:
        """Infer parameters for immediate transitions.
        
        Heuristics:
        1. Regulatory events → High priority (90)
        2. Enzyme catalysis → Medium priority (60)
        3. Transport → Low priority (30)
        4. Default → Medium priority (50)
        """
        # Extract EC number if available
        ec_number = getattr(transition, 'ec_number', None)
        reaction_id = getattr(transition, 'reaction_id', None)
        enzyme_name = getattr(transition, 'enzyme_name', None)
        
        # Determine priority by semantics
        if semantics == BiologicalSemantics.REGULATION:
            priority = 90
            confidence = 0.80
        elif semantics == BiologicalSemantics.TRANSPORT:
            priority = 30
            confidence = 0.70
        elif ec_number:  # Enzyme catalysis
            priority = 60
            confidence = 0.75
        else:
            priority = 50
            confidence = 0.60
        
        return ImmediateParameters(
            biological_semantics=semantics,
            priority=priority,
            weight=1.0,
            ec_number=ec_number,
            reaction_id=reaction_id,
            enzyme_name=enzyme_name,
            organism=organism,
            confidence_score=confidence,
            source="Heuristic",
            notes="Inferred from biological semantics"
        )
    
    def _infer_timed(self,
                    transition: Any,
                    semantics: BiologicalSemantics,
                    organism: str) -> TimedParameters:
        """Infer parameters for timed transitions.
        
        Heuristics:
        1. Transcription → 10 minutes (eukaryotic)
        2. Translation → 5 minutes
        3. Transport → 2 minutes
        4. Default → 5 minutes
        """
        label = getattr(transition, 'label', '').lower()
        ec_number = getattr(transition, 'ec_number', None)
        reaction_id = getattr(transition, 'reaction_id', None)
        
        # Determine delay by label keywords
        if 'transcription' in label or 'mrna' in label:
            delay = 10.0
            confidence = 0.70
        elif 'translation' in label or 'protein' in label:
            delay = 5.0
            confidence = 0.70
        elif 'transport' in label:
            delay = 2.0
            confidence = 0.65
        else:
            delay = 5.0
            confidence = 0.50
        
        return TimedParameters(
            biological_semantics=semantics,
            delay=delay,
            time_unit="minutes",
            ec_number=ec_number,
            reaction_id=reaction_id,
            organism=organism,
            confidence_score=confidence,
            source="Heuristic",
            notes="Inferred from biological process type"
        )
    
    def _infer_stochastic(self,
                         transition: Any,
                         semantics: BiologicalSemantics,
                         organism: str) -> StochasticParameters:
        """Infer parameters for stochastic transitions.
        
        **Fast-First Strategy:**
        1. Check local cache (instant)
        2. Return heuristic defaults (instant)
        3. Optionally: Queue SABIO-RK fetch for future enhancement
        """
        ec_number = getattr(transition, 'ec_number', None)
        reaction_id = getattr(transition, 'reaction_id', None)
        enzyme_name = getattr(transition, 'enzyme_name', None)
        label = getattr(transition, 'label', '').lower()
        
        # Check cache first (from previous fetches)
        cache_key = (ec_number or reaction_id or 'generic', organism)
        if cache_key in self._parameter_cache:
            cached = self._parameter_cache[cache_key]
            if isinstance(cached, StochasticParameters):
                self.logger.info(f"Using cached parameters for {cache_key}")
                return cached
        
        # Fast heuristic defaults based on label
        if 'expression' in label or 'gene' in label or 'transcription' in label:
            lambda_param = 0.01  # Gene expression: ~0.01/s (literature avg)
            confidence = 0.65
            notes = "Gene expression rate (literature default)"
        elif 'degradation' in label or 'decay' in label:
            lambda_param = 0.001  # Degradation: ~0.001/s (half-life ~11 min)
            confidence = 0.65
            notes = "Protein degradation rate (literature default)"
        elif 'binding' in label or 'association' in label:
            lambda_param = 0.1  # Fast binding
            confidence = 0.55
            notes = "Binding association rate (typical range)"
        elif 'dissociation' in label or 'unbinding' in label:
            lambda_param = 0.01  # Slower dissociation
            confidence = 0.55
            notes = "Binding dissociation rate (typical range)"
        elif 'phosphorylation' in label or 'kinase' in label:
            lambda_param = 0.05  # Phosphorylation
            confidence = 0.60
            notes = "Phosphorylation rate (kinase activity)"
        else:
            lambda_param = 0.05  # Generic default
            confidence = 0.45
            notes = "Generic stochastic rate (to be refined with data)"
        
        return StochasticParameters(
            biological_semantics=semantics,
            lambda_param=lambda_param,
            k_forward=lambda_param,
            ec_number=ec_number,
            reaction_id=reaction_id,
            enzyme_name=enzyme_name,
            organism=organism,
            confidence_score=confidence,
            source="Heuristic",
            notes=notes
        )
    
    def _infer_continuous(self,
                         transition: Any,
                         semantics: BiologicalSemantics,
                         organism: str) -> ContinuousParameters:
        """Infer parameters for continuous transitions.
        
        **Fast-First Strategy:**
        1. Check local cache (instant)
        2. Return literature defaults by EC class (instant)
        3. Optionally: Queue SABIO-RK fetch for future refinement
        """
        ec_number = getattr(transition, 'ec_number', None)
        reaction_id = getattr(transition, 'reaction_id', None)
        enzyme_name = getattr(transition, 'enzyme_name', None)
        label = getattr(transition, 'label', '').lower()
        
        # Check cache first
        cache_key = (ec_number or reaction_id or 'generic', organism)
        if cache_key in self._parameter_cache:
            cached = self._parameter_cache[cache_key]
            if isinstance(cached, ContinuousParameters):
                self.logger.info(f"Using cached parameters for {cache_key}")
                return cached
        
        # Fast heuristic defaults by EC class and label
        vmax, km, kcat = self._get_default_kinetics(ec_number, label, organism)
        
        # Determine confidence based on specificity
        if ec_number and len(ec_number.split('.')) == 4:
            confidence = 0.70  # Specific EC number
            notes = f"Literature defaults for EC {ec_number} class"
        elif ec_number:
            confidence = 0.60  # Partial EC number
            notes = f"Literature defaults for EC {ec_number} family"
        else:
            confidence = 0.50  # Generic
            notes = "Generic enzyme kinetics (to be refined with data)"
        
        return ContinuousParameters(
            biological_semantics=semantics,
            vmax=vmax,
            km=km,
            kcat=kcat,
            ec_number=ec_number,
            reaction_id=reaction_id,
            enzyme_name=enzyme_name,
            organism=organism,
            temperature=37.0,
            ph=7.4,
            confidence_score=confidence,
            source="Heuristic",
            notes=notes
        )
    
    def _get_default_kinetics(self, ec_number: Optional[str], 
                             label: str, 
                             organism: str) -> Tuple[float, float, float]:
        """Get default kinetic parameters by EC class.
        
        Returns:
            Tuple of (vmax, km, kcat) based on enzyme class and label
        """
        # EC class-specific defaults (literature averages)
        if ec_number:
            ec_class = ec_number.split('.')[0] if '.' in ec_number else None
            
            if ec_class == '1':  # Oxidoreductases
                return (100.0, 0.1, 10.0)  # Fast, medium affinity
            elif ec_class == '2':  # Transferases (kinases, etc)
                return (50.0, 0.05, 5.0)  # Medium speed, high affinity
            elif ec_class == '3':  # Hydrolases
                return (200.0, 0.5, 20.0)  # Fast, lower affinity
            elif ec_class == '4':  # Lyases
                return (80.0, 0.2, 8.0)  # Medium parameters
            elif ec_class == '5':  # Isomerases
                return (60.0, 0.1, 6.0)  # Moderate speed
            elif ec_class == '6':  # Ligases
                return (40.0, 0.3, 4.0)  # Slower, moderate affinity
        
        # Label-based defaults (when no EC number)
        if 'kinase' in label or 'phosphorylation' in label:
            return (50.0, 0.05, 5.0)  # Kinases
        elif 'phosphatase' in label or 'dephosphorylation' in label:
            return (100.0, 0.1, 10.0)  # Phosphatases
        elif 'dehydrogenase' in label:
            return (150.0, 0.2, 15.0)  # Dehydrogenases
        elif 'synthase' in label or 'synthesis' in label:
            return (80.0, 0.3, 8.0)  # Synthases
        elif 'protease' in label or 'peptidase' in label:
            return (200.0, 0.5, 20.0)  # Proteases
        elif 'glycosylase' in label or 'glycosyl' in label:
            return (120.0, 0.15, 12.0)  # Glycosylases
        
        # Generic enzymatic reaction
        return (100.0, 0.1, 10.0)

