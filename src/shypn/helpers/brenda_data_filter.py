#!/usr/bin/env python3
"""BRENDA Data Filtering and Ranking System.

This module provides intelligent filtering and ranking of BRENDA query results
to select the most relevant kinetic parameters for model application.

Filtering Strategy:
1. Organism matching (prefer exact organism or taxonomic proximity)
2. Substrate matching (match substrate names to model compounds)
3. Quality scoring (literature citations, data completeness)
4. Statistical aggregation (mean, median, confidence intervals)

Usage:
    filter = BRENDADataFilter(model_organism='Homo sapiens')
    filtered = filter.filter_km_values(brenda_results, substrate='glucose')
    best = filter.select_best_value(filtered)
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import statistics


class BRENDADataFilter:
    """Filter and rank BRENDA kinetic parameter data for model application."""
    
    # Common organism name mappings
    ORGANISM_ALIASES = {
        'human': 'Homo sapiens',
        'mouse': 'Mus musculus',
        'rat': 'Rattus norvegicus',
        'yeast': 'Saccharomyces cerevisiae',
        'e. coli': 'Escherichia coli',
        'ecoli': 'Escherichia coli',
    }
    
    # Taxonomic groups (for proximity scoring)
    TAXONOMIC_GROUPS = {
        'mammals': ['Homo sapiens', 'Mus musculus', 'Rattus norvegicus', 
                    'Bos taurus', 'Sus scrofa', 'Oryctolagus cuniculus'],
        'bacteria': ['Escherichia coli', 'Bacillus subtilis', 'Pseudomonas'],
        'fungi': ['Saccharomyces cerevisiae', 'Candida', 'Aspergillus'],
        'plants': ['Arabidopsis thaliana', 'Zea mays', 'Solanum'],
    }
    
    def __init__(self, model_organism: Optional[str] = None):
        """Initialize filter with target organism preference.
        
        Args:
            model_organism: Target organism (e.g., 'Homo sapiens' or 'human')
        """
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Normalize organism name
        if model_organism:
            model_organism = self.ORGANISM_ALIASES.get(
                model_organism.lower(), 
                model_organism
            )
        self.model_organism = model_organism
    
    def filter_km_values(
        self,
        km_values: List[Dict[str, Any]],
        substrate: Optional[str] = None,
        organism: Optional[str] = None,
        min_quality: float = 0.0
    ) -> List[Dict[str, Any]]:
        """Filter Km values by substrate, organism, and quality.
        
        Args:
            km_values: List of Km value records from BRENDA
            substrate: Optional substrate name to filter by
            organism: Optional organism to filter by (overrides model_organism)
            min_quality: Minimum quality score (0.0 - 1.0)
        
        Returns:
            Filtered and scored list of Km values
        """
        target_organism = organism or self.model_organism
        filtered = []
        
        for km in km_values:
            # Skip invalid/placeholder values
            if km.get('value', 0) <= 0 or km.get('value') == -999.0:
                continue
            
            # Calculate quality score
            score = self._calculate_quality_score(km, target_organism, substrate)
            
            if score >= min_quality:
                km_copy = km.copy()
                km_copy['quality_score'] = score
                filtered.append(km_copy)
        
        # Sort by quality score (descending)
        filtered.sort(key=lambda x: x['quality_score'], reverse=True)
        
        return filtered
    
    def _calculate_quality_score(
        self,
        km: Dict[str, Any],
        target_organism: Optional[str],
        target_substrate: Optional[str]
    ) -> float:
        """Calculate quality score for a Km value (0.0 - 1.0).
        
        Scoring factors:
        - Organism match: 0.4
        - Substrate match: 0.3
        - Has literature: 0.2
        - Value reasonableness: 0.1
        """
        score = 0.0
        
        # Organism matching (0.4 max)
        if target_organism:
            organism_score = self._score_organism_match(
                km.get('organism', ''),
                target_organism
            )
            score += organism_score * 0.4
        
        # Substrate matching (0.3 max)
        if target_substrate:
            substrate_score = self._score_substrate_match(
                km.get('substrate', ''),
                target_substrate
            )
            score += substrate_score * 0.3
        
        # Literature citation (0.2 max)
        if km.get('literature') and str(km['literature']).strip():
            score += 0.2
        
        # Value reasonableness (0.1 max)
        # Typical Km values: 0.001 - 100 mM
        value = km.get('value', 0)
        if 0.001 <= value <= 100:
            score += 0.1
        elif 0.0001 <= value <= 1000:
            score += 0.05
        
        return score
    
    def _score_organism_match(self, data_organism: str, target_organism: str) -> float:
        """Score organism match (1.0 = exact, 0.7 = same group, 0.0 = no match)."""
        if not data_organism or not target_organism:
            return 0.0
        
        # Exact match
        if data_organism.lower() == target_organism.lower():
            return 1.0
        
        # Partial match (genus level)
        data_genus = data_organism.split()[0] if ' ' in data_organism else ''
        target_genus = target_organism.split()[0] if ' ' in target_organism else ''
        if data_genus and data_genus == target_genus:
            return 0.8
        
        # Same taxonomic group
        for group_members in self.TAXONOMIC_GROUPS.values():
            if target_organism in group_members and data_organism in group_members:
                return 0.6
        
        return 0.0
    
    def _score_substrate_match(self, data_substrate: str, target_substrate: str) -> float:
        """Score substrate match (1.0 = exact, 0.5 = partial, 0.0 = no match)."""
        if not data_substrate or not target_substrate:
            return 0.0
        
        data_sub = data_substrate.lower().strip()
        target_sub = target_substrate.lower().strip()
        
        # Exact match
        if data_sub == target_sub:
            return 1.0
        
        # Partial match (one contains the other)
        if data_sub in target_sub or target_sub in data_sub:
            return 0.7
        
        # Common synonyms (e.g., glucose vs D-glucose)
        synonyms = {
            'glucose': ['d-glucose', 'dextrose', 'glc'],
            'fructose': ['d-fructose', 'fru'],
            'atp': ['adenosine triphosphate'],
            'adp': ['adenosine diphosphate'],
        }
        
        for key, aliases in synonyms.items():
            if (key in data_sub or any(a in data_sub for a in aliases)) and \
               (key in target_sub or any(a in target_sub for a in aliases)):
                return 0.8
        
        return 0.0
    
    def select_best_value(
        self,
        filtered_km_values: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Select the single best Km value from filtered results.
        
        Returns the highest quality score value, or None if no valid values.
        """
        if not filtered_km_values:
            return None
        
        # Already sorted by quality score in filter_km_values
        return filtered_km_values[0]
    
    def aggregate_statistics(
        self,
        km_values: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate statistical summary of Km values.
        
        Returns:
            Dict with mean, median, std_dev, min, max, count, and confidence interval
        """
        if not km_values:
            return {
                'count': 0,
                'mean': None,
                'median': None,
                'std_dev': None,
                'min': None,
                'max': None,
                'confidence_95': None
            }
        
        values = [km['value'] for km in km_values if km.get('value', 0) > 0]
        
        if not values:
            return {'count': 0}
        
        mean_val = statistics.mean(values)
        median_val = statistics.median(values)
        std_dev = statistics.stdev(values) if len(values) > 1 else 0.0
        
        # 95% confidence interval (mean ± 1.96 * std_err)
        std_err = std_dev / (len(values) ** 0.5) if len(values) > 1 else 0.0
        ci_95 = (
            mean_val - 1.96 * std_err,
            mean_val + 1.96 * std_err
        )
        
        return {
            'count': len(values),
            'mean': mean_val,
            'median': median_val,
            'std_dev': std_dev,
            'min': min(values),
            'max': max(values),
            'confidence_95': ci_95,
            'unit': km_values[0].get('unit', 'mM')
        }
    
    def group_by_organism(
        self,
        km_values: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group Km values by organism."""
        grouped = defaultdict(list)
        
        for km in km_values:
            organism = km.get('organism', 'Unknown')
            grouped[organism].append(km)
        
        return dict(grouped)
    
    def group_by_substrate(
        self,
        km_values: List[Dict[str, Any]]
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Group Km values by substrate."""
        grouped = defaultdict(list)
        
        for km in km_values:
            substrate = km.get('substrate', 'Unknown')
            grouped[substrate].append(km)
        
        return dict(grouped)
    
    def get_top_organisms(
        self,
        km_values: List[Dict[str, Any]],
        top_n: int = 5
    ) -> List[Tuple[str, int]]:
        """Get top N organisms by number of Km values.
        
        Returns:
            List of (organism, count) tuples sorted by count (descending)
        """
        organism_counts = defaultdict(int)
        
        for km in km_values:
            organism = km.get('organism', 'Unknown')
            organism_counts[organism] += 1
        
        # Sort by count (descending)
        sorted_organisms = sorted(
            organism_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return sorted_organisms[:top_n]
