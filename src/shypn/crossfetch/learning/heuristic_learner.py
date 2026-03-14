"""
Heuristic Learning Engine

Learns parameter patterns from enrichment history to improve
heuristic parameter inference over time.

Author: Shypn Development Team
Date: November 2025
"""

import logging
import statistics
import math
import json
from typing import Dict, List, Optional, Tuple, Any

from ..database.heuristic_db import HeuristicDatabase


class HeuristicLearner:
    """Statistical learning engine for heuristic parameters.
    
    Learns from enrichment history to extract parameter patterns:
    - EC class patterns (e.g., "EC 2.7 kinases typically have Vmax≈50")
    - Organism-specific patterns (e.g., "Human vs yeast differ by 30%")
    - Pathway context patterns (e.g., "Glycolysis has higher Vmax")
    
    Features:
    - Statistical pattern extraction with confidence scoring
    - Outlier detection and removal
    - Minimum sample size requirements
    - Variance penalties for unstable patterns
    - Biological sanity checks
    
    Attributes:
        db: HeuristicDatabase instance
        min_sample_size: Minimum samples to trust pattern (default 5)
        min_confidence: Minimum confidence for learned patterns (default 0.5)
        outlier_threshold: Z-score threshold for outliers (default 3.0)
    """
    
    def __init__(self, 
                 db: Optional[HeuristicDatabase] = None,
                 min_sample_size: int = 5,
                 min_confidence: float = 0.5,
                 outlier_threshold: float = 3.0):
        """Initialize learning engine.
        
        Args:
            db: Optional database instance (creates default if None)
            min_sample_size: Minimum samples required for pattern
            min_confidence: Minimum confidence threshold
            outlier_threshold: Z-score threshold for outlier detection
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        self.db = db or HeuristicDatabase()
        
        # Configuration
        self.min_sample_size = min_sample_size
        self.min_confidence = min_confidence
        self.outlier_threshold = outlier_threshold
        
        # Biological sanity check ranges
        self.param_ranges = {
            'vmax': (0.001, 10000.0),    # Reasonable Vmax range
            'km': (0.0001, 1000.0),       # Km typically 0.1-100 mM
            'kcat': (0.001, 1000000.0),   # Wide range for turnover
            'lambda': (0.0001, 100.0),    # Stochastic rates
            'delay': (0.001, 10000.0)     # Delay in minutes
        }
    
    def learn_from_history(self, force_refresh: bool = False) -> Dict[str, Any]:
        """Learn patterns from enrichment history.
        
        Extracts patterns from transition_parameters table:
        1. EC class patterns (by enzyme class)
        2. EC-specific patterns (exact EC number)
        3. Organism patterns (organism-specific)
        
        Args:
            force_refresh: If True, recompute all patterns
            
        Returns:
            Summary statistics dict
        """
        self.logger.info("Starting pattern learning from enrichment history...")
        
        summary = {
            'ec_class_patterns': 0,
            'ec_specific_patterns': 0,
            'organism_patterns': 0,
            'total_samples_processed': 0,
            'outliers_removed': 0,
            'failed_validations': 0
        }
        
        # Learn EC class patterns
        ec_class_stats = self._learn_ec_class_patterns()
        summary['ec_class_patterns'] = ec_class_stats['patterns_created']
        summary['total_samples_processed'] += ec_class_stats['samples_processed']
        summary['outliers_removed'] += ec_class_stats['outliers_removed']
        
        # Learn EC-specific patterns
        ec_specific_stats = self._learn_ec_specific_patterns()
        summary['ec_specific_patterns'] = ec_specific_stats['patterns_created']
        summary['total_samples_processed'] += ec_specific_stats['samples_processed']
        summary['outliers_removed'] += ec_specific_stats['outliers_removed']
        
        # Learn organism patterns
        organism_stats = self._learn_organism_patterns()
        summary['organism_patterns'] = organism_stats['patterns_created']
        summary['total_samples_processed'] += organism_stats['samples_processed']
        summary['outliers_removed'] += organism_stats['outliers_removed']
        
        self.logger.info(f"Learning complete: {summary}")
        return summary
    
    def _learn_ec_class_patterns(self) -> Dict[str, Any]:
        """Learn patterns by EC class (e.g., EC 2.7 for all kinases).
        
        Returns:
            Statistics dict
        """
        stats = {'patterns_created': 0, 'samples_processed': 0, 'outliers_removed': 0}
        
        # Query enrichments grouped by EC class
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            # Get all continuous parameters with good ratings from non-heuristic sources
            cursor.execute("""
                SELECT ec_number, organism, parameters, confidence_score, id, user_rating
                FROM transition_parameters
                WHERE transition_type = 'continuous'
                  AND ec_number IS NOT NULL
                  AND source IN ('SABIO-RK', 'BRENDA')
                  AND undone = 0
                  AND (user_rating IS NULL OR user_rating >= 0)
            """)
            
            enrichments = [dict(row) for row in cursor.fetchall()]
        
        if not enrichments:
            self.logger.info("No enrichment data available for EC class learning")
            return stats
        
        # Group by EC class (first two parts: e.g., "2.7")
        ec_class_groups: Dict[str, List[Any]] = {}
        for enrich in enrichments:
            ec_num = enrich['ec_number']
            parts = ec_num.split('.')
            if len(parts) >= 2:
                ec_class = f"{parts[0]}.{parts[1]}"
                if ec_class not in ec_class_groups:
                    ec_class_groups[ec_class] = []
                ec_class_groups[ec_class].append(enrich)
        
        # Extract patterns for each EC class
        for ec_class, enrichments_list in ec_class_groups.items():
            if len(enrichments_list) < self.min_sample_size:
                continue
            
            # Extract parameter values
            param_data = self._extract_continuous_parameters(enrichments_list)
            
            # Learn patterns for each parameter type
            for param_type, values_with_ids in param_data.items():
                if len(values_with_ids) < self.min_sample_size:
                    continue
                
                # Remove outliers
                clean_values, clean_ids, outliers = self._remove_outliers(values_with_ids)
                stats['outliers_removed'] += outliers
                stats['samples_processed'] += len(values_with_ids)
                
                if len(clean_values) < self.min_sample_size:
                    continue
                
                # Calculate statistics
                param_stats = self._calculate_parameter_statistics(clean_values)
                
                # Validate biological sanity
                if not self._validate_parameter_range(param_type, param_stats['mean']):
                    continue
                
                # Calculate confidence score
                confidence = self._calculate_confidence(
                    param_stats, 
                    sample_size=len(clean_values),
                    pattern_type='ec_class'
                )
                
                if confidence < self.min_confidence:
                    continue
                
                # Store pattern
                try:
                    self.db.store_learned_pattern(
                        pattern_type='ec_class',
                        param_type=param_type,
                        param_mean=param_stats['mean'],
                        param_std_dev=param_stats['std_dev'],
                        param_median=param_stats['median'],
                        param_min=param_stats['min'],
                        param_max=param_stats['max'],
                        sample_size=len(clean_values),
                        confidence_score=confidence,
                        variance_penalty=param_stats.get('variance_penalty', 0.0),
                        source_ids=clean_ids,
                        ec_class=ec_class
                    )
                    stats['patterns_created'] += 1
                    self.logger.info(
                        f"Learned EC class pattern: {ec_class} {param_type}="
                        f"{param_stats['mean']:.3g}±{param_stats['std_dev']:.3g} "
                        f"(n={len(clean_values)}, conf={confidence:.2f})"
                    )
                except Exception as e:
                    self.logger.error(f"Failed to store EC class pattern: {e}")
        
        return stats
    
    def _learn_ec_specific_patterns(self) -> Dict[str, Any]:
        """Learn patterns by specific EC number.
        
        Returns:
            Statistics dict
        """
        stats = {'patterns_created': 0, 'samples_processed': 0, 'outliers_removed': 0}
        
        # Query enrichments grouped by exact EC number
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT ec_number, organism, parameters, confidence_score, id, user_rating
                FROM transition_parameters
                WHERE transition_type = 'continuous'
                  AND ec_number IS NOT NULL
                  AND source IN ('SABIO-RK', 'BRENDA')
                  AND undone = 0
                  AND (user_rating IS NULL OR user_rating >= 0)
            """)
            
            enrichments = [dict(row) for row in cursor.fetchall()]
        
        if not enrichments:
            return stats
        
        # Group by exact EC number
        ec_groups: Dict[str, List[Any]] = {}
        for enrich in enrichments:
            ec_num = enrich['ec_number']
            if ec_num not in ec_groups:
                ec_groups[ec_num] = []
            ec_groups[ec_num].append(enrich)
        
        # Extract patterns for each EC number
        for ec_number, enrichments_list in ec_groups.items():
            if len(enrichments_list) < self.min_sample_size:
                continue
            
            param_data = self._extract_continuous_parameters(enrichments_list)
            
            for param_type, values_with_ids in param_data.items():
                if len(values_with_ids) < self.min_sample_size:
                    continue
                
                clean_values, clean_ids, outliers = self._remove_outliers(values_with_ids)
                stats['outliers_removed'] += outliers
                stats['samples_processed'] += len(values_with_ids)
                
                if len(clean_values) < self.min_sample_size:
                    continue
                
                param_stats = self._calculate_parameter_statistics(clean_values)
                
                if not self._validate_parameter_range(param_type, param_stats['mean']):
                    continue
                
                confidence = self._calculate_confidence(
                    param_stats,
                    sample_size=len(clean_values),
                    pattern_type='ec_specific'
                )
                
                if confidence < self.min_confidence:
                    continue
                
                try:
                    self.db.store_learned_pattern(
                        pattern_type='ec_specific',
                        param_type=param_type,
                        param_mean=param_stats['mean'],
                        param_std_dev=param_stats['std_dev'],
                        param_median=param_stats['median'],
                        param_min=param_stats['min'],
                        param_max=param_stats['max'],
                        sample_size=len(clean_values),
                        confidence_score=confidence,
                        variance_penalty=param_stats.get('variance_penalty', 0.0),
                        source_ids=clean_ids,
                        ec_number=ec_number
                    )
                    stats['patterns_created'] += 1
                    self.logger.info(
                        f"Learned EC-specific pattern: {ec_number} {param_type}="
                        f"{param_stats['mean']:.3g}±{param_stats['std_dev']:.3g} "
                        f"(n={len(clean_values)}, conf={confidence:.2f})"
                    )
                except Exception as e:
                    self.logger.error(f"Failed to store EC-specific pattern: {e}")
        
        return stats
    
    def _learn_organism_patterns(self) -> Dict[str, Any]:
        """Learn organism-specific patterns.
        
        Returns:
            Statistics dict
        """
        stats = {'patterns_created': 0, 'samples_processed': 0, 'outliers_removed': 0}
        
        # Query enrichments grouped by organism
        with self.db._get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT ec_number, organism, parameters, confidence_score, id, user_rating
                FROM transition_parameters
                WHERE transition_type = 'continuous'
                  AND organism IS NOT NULL
                  AND source IN ('SABIO-RK', 'BRENDA')
                  AND undone = 0
                  AND (user_rating IS NULL OR user_rating >= 0)
            """)
            
            enrichments = [dict(row) for row in cursor.fetchall()]
        
        if not enrichments:
            return stats
        
        # Group by organism
        organism_groups: Dict[str, List[Any]] = {}
        for enrich in enrichments:
            organism = enrich['organism']
            if organism not in organism_groups:
                organism_groups[organism] = []
            organism_groups[organism].append(enrich)
        
        # Extract patterns for each organism
        for organism, enrichments_list in organism_groups.items():
            if len(enrichments_list) < self.min_sample_size:
                continue
            
            param_data = self._extract_continuous_parameters(enrichments_list)
            
            for param_type, values_with_ids in param_data.items():
                if len(values_with_ids) < self.min_sample_size:
                    continue
                
                clean_values, clean_ids, outliers = self._remove_outliers(values_with_ids)
                stats['outliers_removed'] += outliers
                stats['samples_processed'] += len(values_with_ids)
                
                if len(clean_values) < self.min_sample_size:
                    continue
                
                param_stats = self._calculate_parameter_statistics(clean_values)
                
                if not self._validate_parameter_range(param_type, param_stats['mean']):
                    continue
                
                confidence = self._calculate_confidence(
                    param_stats,
                    sample_size=len(clean_values),
                    pattern_type='organism'
                )
                
                if confidence < self.min_confidence:
                    continue
                
                try:
                    self.db.store_learned_pattern(
                        pattern_type='organism',
                        param_type=param_type,
                        param_mean=param_stats['mean'],
                        param_std_dev=param_stats['std_dev'],
                        param_median=param_stats['median'],
                        param_min=param_stats['min'],
                        param_max=param_stats['max'],
                        sample_size=len(clean_values),
                        confidence_score=confidence,
                        variance_penalty=param_stats.get('variance_penalty', 0.0),
                        source_ids=clean_ids,
                        organism=organism
                    )
                    stats['patterns_created'] += 1
                    self.logger.info(
                        f"Learned organism pattern: {organism} {param_type}="
                        f"{param_stats['mean']:.3g}±{param_stats['std_dev']:.3g} "
                        f"(n={len(clean_values)}, conf={confidence:.2f})"
                    )
                except Exception as e:
                    self.logger.error(f"Failed to store organism pattern: {e}")
        
        return stats
    
    def _extract_continuous_parameters(self, 
                                      enrichments: List[Dict[str, Any]]) -> Dict[str, List[Tuple[float, int]]]:
        """Extract continuous parameter values from enrichments.
        
        Args:
            enrichments: List of enrichment dicts
            
        Returns:
            Dict mapping param_type to list of (value, id) tuples
        """
        param_data: Dict[str, List[Any]] = {
            'vmax': [],
            'km': [],
            'kcat': []
        }
        
        for enrich in enrichments:
            params = json.loads(enrich['parameters']) if isinstance(enrich['parameters'], str) else enrich['parameters']
            enrich_id = enrich['id']
            
            if 'vmax' in params and params['vmax'] is not None:
                param_data['vmax'].append((float(params['vmax']), enrich_id))
            
            if 'km' in params and params['km'] is not None:
                param_data['km'].append((float(params['km']), enrich_id))
            
            if 'kcat' in params and params['kcat'] is not None:
                param_data['kcat'].append((float(params['kcat']), enrich_id))
        
        return param_data
    
    def _remove_outliers(self, 
                        values_with_ids: List[Tuple[float, int]]) -> Tuple[List[float], List[int], int]:
        """Remove statistical outliers using Z-score.
        
        Args:
            values_with_ids: List of (value, id) tuples
            
        Returns:
            Tuple of (clean_values, clean_ids, num_outliers)
        """
        if len(values_with_ids) < 3:
            # Need at least 3 points for meaningful outlier detection
            values = [v for v, _ in values_with_ids]
            ids = [i for _, i in values_with_ids]
            return values, ids, 0
        
        values = [v for v, _ in values_with_ids]
        ids = [i for _, i in values_with_ids]
        
        mean = statistics.mean(values)
        std_dev = statistics.stdev(values)
        
        if std_dev == 0:
            return values, ids, 0
        
        # Calculate Z-scores
        z_scores = [(v - mean) / std_dev for v in values]
        
        # Filter outliers
        clean_values = []
        clean_ids = []
        outliers = 0
        
        for value, z_score, enrich_id in zip(values, z_scores, ids):
            if abs(z_score) <= self.outlier_threshold:
                clean_values.append(value)
                clean_ids.append(enrich_id)
            else:
                outliers += 1
                self.logger.debug(f"Removed outlier: value={value}, z={z_score:.2f}")
        
        return clean_values, clean_ids, outliers
    
    def _calculate_parameter_statistics(self, values: List[float]) -> Dict[str, float]:
        """Calculate statistical metrics for parameter values.
        
        Args:
            values: List of parameter values
            
        Returns:
            Statistics dict
        """
        if not values:
            return {}
        
        mean_val = statistics.mean(values)
        median_val = statistics.median(values)
        
        if len(values) > 1:
            std_dev = statistics.stdev(values)
            # Coefficient of variation (relative std dev)
            cv = std_dev / mean_val if mean_val != 0 else float('inf')
        else:
            std_dev = 0.0
            cv = 0.0
        
        # Variance penalty: high CV reduces confidence
        # CV < 0.3: no penalty
        # CV 0.3-1.0: linear penalty 0-0.15
        # CV > 1.0: max penalty 0.20
        if cv < 0.3:
            variance_penalty = 0.0
        elif cv <= 1.0:
            variance_penalty = (cv - 0.3) * 0.15 / 0.7  # Scale 0-0.15
        else:
            variance_penalty = 0.20
        
        return {
            'mean': mean_val,
            'median': median_val,
            'std_dev': std_dev,
            'min': min(values),
            'max': max(values),
            'cv': cv,
            'variance_penalty': variance_penalty
        }
    
    def _validate_parameter_range(self, param_type: str, value: float) -> bool:
        """Validate parameter is within biological reasonable range.
        
        Args:
            param_type: Parameter type
            value: Parameter value
            
        Returns:
            True if valid, False otherwise
        """
        if param_type not in self.param_ranges:
            return True  # Unknown param, allow it
        
        min_val, max_val = self.param_ranges[param_type]
        
        if value < min_val or value > max_val:
            self.logger.warning(
                f"Parameter {param_type}={value} outside reasonable range "
                f"[{min_val}, {max_val}]"
            )
            return False
        
        return True
    
    def _calculate_confidence(self,
                             param_stats: Dict[str, float],
                             sample_size: int,
                             pattern_type: str) -> float:
        """Calculate confidence score for learned pattern.
        
        Confidence factors:
        - Base confidence by pattern type (ec_specific > ec_class > organism)
        - Sample size boost (more samples = more confident)
        - Variance penalty (high variance = less confident)
        
        Args:
            param_stats: Parameter statistics
            sample_size: Number of samples
            pattern_type: Type of pattern
            
        Returns:
            Confidence score (0.0-1.0)
        """
        # Base confidence by pattern type
        base_confidence = {
            'ec_specific': 0.70,  # Most specific
            'ec_class': 0.65,     # Class-level
            'organism': 0.60,     # Organism-level
            'pathway': 0.65       # Pathway context
        }.get(pattern_type, 0.50)
        
        # Sample size boost (logarithmic)
        # N=5: +0.00, N=10: +0.05, N=20: +0.08, N=50: +0.12, N=100: +0.15
        if sample_size >= self.min_sample_size:
            sample_boost = min(0.15, 0.05 * math.log10(sample_size / self.min_sample_size + 1))
        else:
            sample_boost = 0.0
        
        # Variance penalty
        variance_penalty = param_stats.get('variance_penalty', 0.0)
        
        # Combined confidence
        confidence = base_confidence + sample_boost - variance_penalty
        
        # Clamp to [0.0, 1.0]
        confidence = max(0.0, min(1.0, confidence))
        
        return confidence
    
    def get_learned_parameter(self,
                             param_type: str,
                             ec_number: Optional[str] = None,
                             organism: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Query for learned parameter pattern.
        
        Args:
            param_type: Parameter type ('vmax', 'km', 'kcat')
            ec_number: Optional EC number
            organism: Optional organism
            
        Returns:
            Pattern dict or None
        """
        return self.db.query_learned_pattern(
            param_type=param_type,
            ec_number=ec_number,
            organism=organism,
            min_confidence=self.min_confidence
        )
