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
from ..database.heuristic_db import HeuristicDatabase


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
    
    def __init__(self, use_background_fetch: bool = False, db_path: Optional[str] = None):
        """Initialize inference engine.
        
        Args:
            use_background_fetch: If True, enhance with database queries in background
            db_path: Optional path to database file (default: ~/.shypn/heuristic_parameters.db)
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Configuration
        self.use_background_fetch = use_background_fetch
        
        # Initialize database
        self.db = HeuristicDatabase(db_path)
        
        # Initialize fetchers (lazy - only if needed)
        self._sabio_rk_fetcher = None
        
        # Type detector
        self.type_detector = TransitionTypeDetector()
        
        # Local cache for database results (in-memory cache for session)
        self._parameter_cache: Dict[Tuple[str, str], ContinuousParameters] = {}
    
    @property
    def sabio_rk_fetcher(self):
        """Lazy initialization of SABIO-RK fetcher."""
        if self._sabio_rk_fetcher is None and self.use_background_fetch:
            self._sabio_rk_fetcher = SabioRKKineticsFetcher()
        return self._sabio_rk_fetcher
    
    def infer_parameters(self,
                        transition: Any,
                        organism: str = "Homo sapiens",
                        use_cache: bool = True) -> InferenceResult:
        """Infer parameters for a transition.
        
        Args:
            transition: Transition object from model
            organism: Target organism
            use_cache: If True, check database cache first
            
        Returns:
            InferenceResult with inferred parameters and alternatives
        """
        # Step 1: Detect transition type
        transition_type = self.type_detector.detect_type(transition)
        
        # Step 2: Infer biological semantics
        semantics = self.type_detector.infer_semantics(transition, transition_type)
        
        # Step 3: Infer parameters based on type (pure heuristics)
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
        
        # Step 4: Refine with stoichiometry analysis
        parameters = self.infer_from_stoichiometry(transition, parameters)
        
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
    
    def _query_database(self,
                       transition_type: TransitionType,
                       ec_number: Optional[str],
                       reaction_id: Optional[str],
                       organism: str) -> Optional[TransitionParameters]:
        """Query database for cached parameters.
        
        Args:
            transition_type: Type of transition
            ec_number: Optional EC number
            reaction_id: Optional reaction ID
            organism: Target organism
        
        Returns:
            Cached parameters if found, None otherwise
        """
        # Generate query key for cache lookup
        type_str = transition_type.value if transition_type != TransitionType.UNKNOWN else None
        if not type_str:
            return None
        
        # Try exact match first
        if ec_number:
            query_key = f"{type_str}|EC:{ec_number}|{organism}"
        elif reaction_id:
            query_key = f"{type_str}|R:{reaction_id}|{organism}"
        else:
            return None
        
        # Check query cache
        cached = self.db.get_cached_query(query_key)
        if cached:
            # Get full parameter details
            param = self.db.get_parameter(cached['recommended_parameter_id'])
            if param:
                self.logger.info(f"Database cache hit: {query_key}")
                return self._dict_to_parameters(param, transition_type)
        
        # Try direct parameter query
        results = self.db.query_parameters(
            transition_type=type_str,
            ec_number=ec_number,
            reaction_id=reaction_id,
            organism=organism,
            min_confidence=0.5,
            limit=1
        )
        
        if results:
            self.logger.info(f"Database parameter found: {ec_number or reaction_id}")
            return self._dict_to_parameters(results[0], transition_type)
        
        # Try cross-species match
        if organism != "generic":
            results = self.db.query_parameters(
                transition_type=type_str,
                ec_number=ec_number,
                reaction_id=reaction_id,
                min_confidence=0.5,
                limit=5
            )
            
            if results:
                # Get organism compatibility and adjust confidence
                best_result = None
                best_score = 0.0
                
                for result in results:
                    # Get enzyme class (first two parts of EC number, e.g., "2.7")
                    enzyme_class = '.'.join(ec_number.split('.')[0:2]) if ec_number and '.' in ec_number else None
                    
                    compat_score = self.db.get_compatibility_score(
                        result['organism'],
                        organism,
                        enzyme_class
                    )
                    
                    adjusted_confidence = result['confidence_score'] * compat_score
                    if adjusted_confidence > best_score:
                        best_score = adjusted_confidence
                        best_result = result
                
                if best_result and best_score >= 0.5:
                    self.logger.info(f"Database cross-species match: {best_result['organism']} → {organism}")
                    params = self._dict_to_parameters(best_result, transition_type)
                    # Adjust confidence for cross-species
                    params.confidence_score = best_score
                    params.notes = f"Cross-species: {best_result['organism']} → {organism}"
                    return params
        
        return None
    
    def _dict_to_parameters(self, 
                           param_dict: Dict[str, Any],
                           transition_type: TransitionType) -> TransitionParameters:
        """Convert database dict to TransitionParameters object.
        
        Args:
            param_dict: Database row as dict
            transition_type: Type of transition
        
        Returns:
            Appropriate TransitionParameters subclass
        """
        params = param_dict['parameters']  # JSON dict
        
        if transition_type == TransitionType.IMMEDIATE:
            return ImmediateParameters(
                biological_semantics=BiologicalSemantics(param_dict.get('biological_semantics', 'burst')),
                priority=params.get('priority', 50),
                weight=params.get('weight', 1.0),
                ec_number=param_dict.get('ec_number'),
                reaction_id=param_dict.get('reaction_id'),
                organism=param_dict['organism'],
                confidence_score=param_dict['confidence_score'],
                source=param_dict['source'],
                notes=param_dict.get('notes')
            )
        
        elif transition_type == TransitionType.TIMED:
            return TimedParameters(
                biological_semantics=BiologicalSemantics(param_dict.get('biological_semantics', 'deterministic')),
                delay=params.get('delay', 5.0),
                time_unit=params.get('time_unit', 'minutes'),
                ec_number=param_dict.get('ec_number'),
                reaction_id=param_dict.get('reaction_id'),
                organism=param_dict['organism'],
                confidence_score=param_dict['confidence_score'],
                source=param_dict['source'],
                notes=param_dict.get('notes')
            )
        
        elif transition_type == TransitionType.STOCHASTIC:
            return StochasticParameters(
                biological_semantics=BiologicalSemantics(param_dict.get('biological_semantics', 'mass_action')),
                lambda_param=params.get('lambda', 0.05),
                k_forward=params.get('k_forward'),
                k_reverse=params.get('k_reverse'),
                ec_number=param_dict.get('ec_number'),
                reaction_id=param_dict.get('reaction_id'),
                enzyme_name=param_dict.get('enzyme_name'),
                organism=param_dict['organism'],
                temperature=param_dict.get('temperature'),
                ph=param_dict.get('ph'),
                confidence_score=param_dict['confidence_score'],
                source=param_dict['source'],
                notes=param_dict.get('notes')
            )
        
        elif transition_type == TransitionType.CONTINUOUS:
            return ContinuousParameters(
                biological_semantics=BiologicalSemantics(param_dict.get('biological_semantics', 'enzyme_kinetics')),
                vmax=params.get('vmax', 100.0),
                km=params.get('km', 0.1),
                kcat=params.get('kcat'),
                ki=params.get('ki'),
                hill_coefficient=params.get('hill_coefficient'),
                ec_number=param_dict.get('ec_number'),
                reaction_id=param_dict.get('reaction_id'),
                enzyme_name=param_dict.get('enzyme_name'),
                organism=param_dict['organism'],
                temperature=param_dict.get('temperature'),
                ph=param_dict.get('ph'),
                confidence_score=param_dict['confidence_score'],
                source=param_dict['source'],
                notes=param_dict.get('notes')
            )
        
        # Fallback
        return TransitionParameters(
            transition_type=transition_type,
            biological_semantics=BiologicalSemantics.UNKNOWN,
            organism=param_dict['organism']
        )
    
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
        
        # KEGG gene symbols (common glycolysis/metabolism genes)
        # Hexokinases/Glucokinases
        if label.startswith('hk') or label.startswith('gck'):
            return (50.0, 0.05, 5.0)  # Hexokinase/Glucokinase
        # Pyruvate kinase (pk, pklr, pkm)
        elif label.startswith('pk') or label == 'pklr' or label == 'pkm':
            return (50.0, 0.05, 5.0)  # Pyruvate kinase
        # Phosphofructokinase
        elif label.startswith('pfk'):
            return (50.0, 0.05, 5.0)  # PFK
        # Phosphoglycerate kinase (pgk)
        elif label.startswith('pgk'):
            return (50.0, 0.05, 5.0)  # PGK
        # Dehydrogenases (gapdh, ldh, aldh, adh, pdh, idh, mdh, etc.)
        elif 'dh' in label or label.startswith('gapdh') or label.startswith('ldh') or label.startswith('aldh') or label.startswith('adh') or label.startswith('pdh') or label.startswith('idh') or label.startswith('mdh'):
            return (150.0, 0.2, 15.0)  # Dehydrogenases
        # Aldolases
        elif label.startswith('aldo') or label.startswith('ald'):
            return (90.0, 0.2, 9.0)  # Aldolases
        # Isomerases (tpi, gpi, etc.)
        elif label.startswith('tpi') or label.startswith('gpi'):
            return (70.0, 0.12, 7.0)  # Isomerases
        # Phosphoglycerate mutase (pgam)
        elif label.startswith('pgam'):
            return (70.0, 0.12, 7.0)  # Mutases
        # Phosphoglucomutase (pgm)
        elif label.startswith('pgm') and not label.startswith('pgam'):
            return (70.0, 0.12, 7.0)  # Phosphoglucomutase
        # Enolases
        elif label.startswith('eno'):
            return (90.0, 0.2, 9.0)  # Enolases (lyases)
        # Fructose-bisphosphatase (fbp, fbpase)
        elif label.startswith('fbp'):
            return (100.0, 0.1, 10.0)  # FBPase (phosphatase-like)
        # Reductases/Oxidases (akr, cox, etc.)
        elif label.startswith('akr') or label.startswith('cox') or label.startswith('nox'):
            return (120.0, 0.15, 12.0)  # Reductases/Oxidases
        # Transferases (dlat, glut, etc.)
        elif label.startswith('dlat') or label.startswith('glut'):
            return (55.0, 0.08, 5.5)  # Transferases
        
        # Enzyme name patterns (full names)
        if 'kinase' in label or 'phosphorylation' in label:
            return (50.0, 0.05, 5.0)  # Kinases
        elif 'phosphatase' in label or 'dephosphorylation' in label:
            return (100.0, 0.1, 10.0)  # Phosphatases
        elif 'dehydrogenase' in label:
            return (150.0, 0.2, 15.0)  # Dehydrogenases
        elif 'synthase' in label or 'synthesis' in label or 'synthetase' in label:
            return (80.0, 0.3, 8.0)  # Synthases
        elif 'protease' in label or 'peptidase' in label:
            return (200.0, 0.5, 20.0)  # Proteases
        elif 'glycosylase' in label or 'glycosyl' in label:
            return (120.0, 0.15, 12.0)  # Glycosylases
        elif 'reductase' in label or 'oxidase' in label:
            return (120.0, 0.15, 12.0)  # Oxidoreductases
        elif 'isomerase' in label or 'epimerase' in label or 'mutase' in label:
            return (70.0, 0.12, 7.0)  # Isomerases
        elif 'lyase' in label or 'decarboxylase' in label or 'aldolase' in label:
            return (90.0, 0.2, 9.0)  # Lyases
        elif 'ligase' in label or 'carboxylase' in label:
            return (45.0, 0.25, 4.5)  # Ligases
        elif 'transferase' in label or 'transaminase' in label:
            return (55.0, 0.08, 5.5)  # Transferases
        elif 'hydrolase' in label or 'lipase' in label or 'esterase' in label:
            return (180.0, 0.4, 18.0)  # Hydrolases
        elif 'polymerase' in label or 'polymerization' in label:
            return (30.0, 0.4, 3.0)  # Slow, high substrate requirement
        elif 'binding' in label or 'association' in label:
            return (200.0, 0.05, 20.0)  # Fast binding
        elif 'transport' in label or 'transporter' in label or 'channel' in label:
            return (150.0, 0.1, 15.0)  # Transport
        elif 'cleavage' in label or 'degradation' in label:
            return (100.0, 0.2, 10.0)  # Degradation
        
        # Generic enzymatic reaction
        return (100.0, 0.1, 10.0)
    
    def infer_from_stoichiometry(self, transition: Any, base_params: TransitionParameters) -> TransitionParameters:
        """Refine parameters using stoichiometry and network structure.
        
        Uses local balance (input/output stoichiometry) and global balance
        (overall network conservation) to adjust parameter values.
        
        Args:
            transition: Transition object with arc information
            base_params: Base parameters from label/type heuristics
            
        Returns:
            Refined parameters based on stoichiometry
        """
        # Extract stoichiometry information
        stoich_info = self._analyze_stoichiometry(transition)
        
        if not stoich_info:
            # No stoichiometry info available, return base params
            return base_params
        
        # Apply stoichiometry-based adjustments
        if isinstance(base_params, ContinuousParameters):
            return self._adjust_continuous_by_stoichiometry(base_params, stoich_info)
        elif isinstance(base_params, StochasticParameters):
            return self._adjust_stochastic_by_stoichiometry(base_params, stoich_info)
        
        return base_params
    
    def _analyze_stoichiometry(self, transition: Any) -> Optional[Dict[str, Any]]:
        """Analyze stoichiometry from transition arcs.
        
        Extracts:
        - Input places and weights (substrates)
        - Output places and weights (products)
        - Total input/output balance
        - Locality properties
        
        Args:
            transition: Transition object
            
        Returns:
            Dict with stoichiometry info or None
        """
        try:
            # Get input arcs (places → transition)
            inputs = []
            if hasattr(transition, 'input_arcs'):
                for arc in transition.input_arcs:
                    weight = getattr(arc, 'weight', 1)
                    place_id = getattr(arc, 'source_id', None) or getattr(arc, 'place_id', None)
                    initial_marking = getattr(arc.source, 'initial_marking', 0) if hasattr(arc, 'source') else 0
                    inputs.append({
                        'place_id': place_id,
                        'weight': weight,
                        'marking': initial_marking
                    })
            
            # Get output arcs (transition → places)
            outputs = []
            if hasattr(transition, 'output_arcs'):
                for arc in transition.output_arcs:
                    weight = getattr(arc, 'weight', 1)
                    place_id = getattr(arc, 'target_id', None) or getattr(arc, 'place_id', None)
                    initial_marking = getattr(arc.target, 'initial_marking', 0) if hasattr(arc, 'target') else 0
                    outputs.append({
                        'place_id': place_id,
                        'weight': weight,
                        'marking': initial_marking
                    })
            
            if not inputs and not outputs:
                return None
            
            # Calculate balance metrics
            total_input_weight = sum(inp['weight'] for inp in inputs)
            total_output_weight = sum(out['weight'] for out in outputs)
            total_input_marking = sum(inp['marking'] for inp in inputs)
            
            # Balance ratio (how balanced is the reaction)
            balance_ratio = min(total_input_weight, total_output_weight) / max(total_input_weight, total_output_weight, 1)
            
            # Locality metric (how localized are the markings)
            locality_score = total_input_marking / max(len(inputs), 1)
            
            return {
                'inputs': inputs,
                'outputs': outputs,
                'total_input_weight': total_input_weight,
                'total_output_weight': total_output_weight,
                'total_input_marking': total_input_marking,
                'balance_ratio': balance_ratio,
                'locality_score': locality_score,
                'num_substrates': len(inputs),
                'num_products': len(outputs)
            }
            
        except Exception as e:
            self.logger.warning(f"Failed to analyze stoichiometry: {e}")
            return None
    
    def _adjust_continuous_by_stoichiometry(self, 
                                           params: ContinuousParameters,
                                           stoich: Dict[str, Any]) -> ContinuousParameters:
        """Adjust continuous parameters based on stoichiometry.
        
        Heuristics:
        - Multi-substrate reactions → Lower Vmax (more complex)
        - High input weights → Higher Km (more substrate needed)
        - Balanced reactions → Higher confidence
        - High locality (concentrated substrates) → Higher Vmax
        
        Args:
            params: Base continuous parameters
            stoich: Stoichiometry information
            
        Returns:
            Adjusted parameters
        """
        vmax = params.vmax
        km = params.km
        confidence = params.confidence_score
        notes = params.notes or ""
        
        # Multi-substrate penalty
        num_substrates = stoich['num_substrates']
        if num_substrates > 2:
            vmax *= 0.7  # Complex reactions are slower
            notes += f" | Multi-substrate ({num_substrates}) penalty applied"
        
        # Stoichiometry adjustment for Km
        total_input_weight = stoich['total_input_weight']
        if total_input_weight > 2:
            # High stoichiometry → Higher Km (need more substrate)
            km *= (total_input_weight / 2.0)
            notes += f" | Km adjusted for stoichiometry ({total_input_weight})"
        
        # Balance bonus
        balance_ratio = stoich['balance_ratio']
        if balance_ratio > 0.8:  # Well balanced reaction
            confidence = min(confidence + 0.1, 0.85)
            notes += " | Balanced reaction (+10% confidence)"
        
        # Locality adjustment for Vmax
        locality_score = stoich['locality_score']
        if locality_score > 10:  # High concentration of substrates
            vmax *= 1.3  # Faster reaction with abundant substrates
            notes += f" | High substrate locality (×1.3 Vmax)"
        elif locality_score < 1:  # Low substrate availability
            vmax *= 0.7
            notes += f" | Low substrate locality (×0.7 Vmax)"
        
        return ContinuousParameters(
            biological_semantics=params.biological_semantics,
            vmax=vmax,
            km=km,
            kcat=params.kcat,
            ki=params.ki,
            hill_coefficient=params.hill_coefficient,
            ec_number=params.ec_number,
            reaction_id=params.reaction_id,
            enzyme_name=params.enzyme_name,
            organism=params.organism,
            temperature=params.temperature,
            ph=params.ph,
            confidence_score=confidence,
            source="Heuristic + Stoichiometry",
            notes=notes
        )
    
    def _adjust_stochastic_by_stoichiometry(self,
                                           params: StochasticParameters,
                                           stoich: Dict[str, Any]) -> StochasticParameters:
        """Adjust stochastic parameters based on stoichiometry.
        
        Heuristics:
        - More substrates → Lower rate (less likely to have all present)
        - High weights → Scale rate by stoichiometry
        - Balanced reactions → Higher confidence
        
        Args:
            params: Base stochastic parameters
            stoich: Stoichiometry information
            
        Returns:
            Adjusted parameters
        """
        lambda_param = params.lambda_param
        confidence = params.confidence_score
        notes = params.notes or ""
        
        # Multi-substrate penalty (harder to get all molecules together)
        num_substrates = stoich['num_substrates']
        if num_substrates > 1:
            # Each additional substrate decreases rate
            lambda_param *= (0.5 ** (num_substrates - 1))
            notes += f" | Multi-substrate ({num_substrates}) rate adjustment"
        
        # Stoichiometry scaling
        total_input_weight = stoich['total_input_weight']
        if total_input_weight > 1:
            # Higher order reactions are less frequent
            lambda_param /= total_input_weight
            notes += f" | Rate scaled by stoichiometry (/{total_input_weight})"
        
        # Balance bonus
        balance_ratio = stoich['balance_ratio']
        if balance_ratio > 0.8:
            confidence = min(confidence + 0.1, 0.85)
            notes += " | Balanced reaction (+10% confidence)"
        
        # Locality adjustment
        locality_score = stoich['locality_score']
        if locality_score > 10:
            lambda_param *= 1.5  # More molecules → More frequent reactions
            notes += f" | High locality (×1.5 rate)"
        elif locality_score < 1:
            lambda_param *= 0.5
            notes += f" | Low locality (×0.5 rate)"
        
        return StochasticParameters(
            biological_semantics=params.biological_semantics,
            lambda_param=lambda_param,
            k_forward=lambda_param,
            k_reverse=params.k_reverse,
            ec_number=params.ec_number,
            reaction_id=params.reaction_id,
            enzyme_name=params.enzyme_name,
            organism=params.organism,
            temperature=params.temperature,
            ph=params.ph,
            confidence_score=confidence,
            source="Heuristic + Stoichiometry",
            notes=notes
        )


