#!/usr/bin/env python3
"""Viability Analyzer - Multi-level analysis pipeline executor.

Extracted from ViabilityPanel as part of Phase 2.2 Quality Improvements.
Executes the complete viability analysis workflow independent of UI.

ARCHITECTURE:
- Stateless analyzer (no UI dependencies)
- Coordinates multiple specialized analyzers
- Builds analysis context from model and KB
- Returns structured analysis results

USAGE:
    analyzer = ViabilityAnalyzer(model, kb, simulation)
    result = analyzer.analyze(transition, mode='standard')
    
    for issue in result.issues:
        print(f"{issue.severity}: {issue.message}")

Author: Simão Eugénio
Date: February 12, 2026 (Phase 2.2 Extraction)
"""
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import logging

# Import specialized analyzers
from ..analysis import LocalityAnalyzer, DependencyAnalyzer, BoundaryAnalyzer, ConservationAnalyzer
from ..data.data_puller import DataPuller
from ..data.data_cache import CachedDataPuller, DataCache


@dataclass
class AnalysisResult:
    """Result of viability analysis.
    
    Attributes:
        transition: TransitionKnowledge object analyzed
        issues: List of detected issues
        suggestions: List of generated suggestions (if requested)
        context: Analysis context dict
        errors: List of errors encountered during analysis
    """
    transition: Any
    issues: List[Any]
    suggestions: List[Any] = None
    context: Dict[str, Any] = None
    errors: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []
        if self.context is None:
            self.context = {}
        if self.errors is None:
            self.errors = []


class ViabilityAnalyzer:
    """Multi-level viability analysis pipeline executor.
    
    Orchestrates execution of specialized analyzers (locality, dependency,
    boundary, conservation) to identify model issues and generate fix suggestions.
    
    This class is STATELESS - all state passed via parameters.
    Safe to use in batch operations, CLI tools, and automated workflows.
    """
    
    def __init__(self, model, kb=None, simulation=None, data_cache=None):
        """Initialize viability analyzer.
        
        Args:
            model: DocumentModel instance
            kb: KnowledgeBase instance (optional, for context-aware analysis)
            simulation: SimulationController instance (optional, for sim data)
            data_cache: DataCache instance (optional, defaults to new cache)
        """
        self.model = model
        self.kb = kb
        self.simulation = simulation
        self.logger = logging.getLogger(__name__)
        
        # Data access layer
        self.data_cache = data_cache if data_cache is not None else DataCache(default_ttl=60.0)
        self.data_puller = DataPuller(kb, simulation=simulation) if kb else None
        
        # Initialize specialized analyzers (all stateless)
        self.locality_analyzer = LocalityAnalyzer()
        self.dependency_analyzer = DependencyAnalyzer()
        self.boundary_analyzer = BoundaryAnalyzer()
        self.conservation_analyzer = ConservationAnalyzer()
    
    def analyze(self, transition, mode: str = 'standard', 
                generate_suggestions: bool = False) -> AnalysisResult:
        """Execute viability analysis pipeline.
        
        Args:
            transition: TransitionKnowledge object to analyze
            mode: Analysis mode ('standard', 'deep', 'quick')
            generate_suggestions: If True, generate fix suggestions from issues
        
        Returns:
            AnalysisResult with detected issues and optional suggestions
        """
        # Get transition object from model
        transition_obj = self._get_transition_object(transition)
        if not transition_obj:
            return AnalysisResult(
                transition=transition,
                issues=[],
                errors=[f"Transition {transition.transition_id} not found in model"]
            )
        
        # Build locality context
        locality = self._get_locality(transition_obj)
        
        # Build analysis context
        context = self._build_context(transition, transition_obj, locality)
        
        # Execute analysis levels based on mode
        if mode == 'quick':
            issues = self._execute_quick_analysis(context)
        elif mode == 'deep':
            issues = self._execute_deep_analysis(context)
        else:  # standard
            issues = self._execute_standard_analysis(context)
        
        # Generate suggestions if requested
        suggestions = []
        if generate_suggestions and issues:
            suggestions = self._generate_suggestions(issues, context)
        
        return AnalysisResult(
            transition=transition,
            issues=issues,
            suggestions=suggestions,
            context=context
        )
    
    def _get_transition_object(self, transition):
        """Get transition object from model by ID.
        
        Args:
            transition: TransitionKnowledge or object with transition_id
        
        Returns:
            Transition object or None
        """
        target_id = getattr(transition, 'transition_id', None)
        if not target_id:
            return None
        
        for t in self.model.transitions:
            if t.id == target_id:
                return t
        
        return None
    
    def _get_locality(self, transition_obj):
        """Detect locality for transition.
        
        Args:
            transition_obj: Transition object from model
        
        Returns:
            Locality object or None
        """
        try:
            from shypn.diagnostic import LocalityDetector
            locality_detector = LocalityDetector(self.model)
            return locality_detector.get_locality_for_transition(transition_obj)
        except (ImportError, AttributeError, KeyError) as e:
            logger.debug(f"Failed to detect locality for transition: {e}")
            return None
    
    def _build_context(self, transition, transition_obj, locality) -> Dict[str, Any]:
        """Build analysis context dictionary.
        
        Args:
            transition: TransitionKnowledge object
            transition_obj: Transition object from model
            locality: Detected locality
        
        Returns:
            Context dict for analyzers
        """
        # Get cached data puller
        cached_puller = None
        if self.data_puller:
            cached_puller = CachedDataPuller(self.data_puller, self.data_cache)
        
        # Get simulation data if available
        sim_data = None
        if cached_puller and hasattr(cached_puller, 'get_simulation_data'):
            try:
                sim_data = cached_puller.get_simulation_data()
            except (AttributeError, TypeError, KeyError) as e:
                self.logger.debug(f"Failed to get simulation data from cached puller: {e}")
        
        return {
            'transition': transition,
            'transition_obj': transition_obj,
            'locality': locality,
            'kb': self.kb,
            'sim_data': sim_data,
            'data_puller': cached_puller,
            'model': self.model
        }
    
    def _execute_quick_analysis(self, context) -> List[Any]:
        """Execute quick analysis (locality only).
        
        Args:
            context: Analysis context dict
        
        Returns:
            List of Issue objects
        """
        issues = []
        
        # Level 1: Locality Analysis
        try:
            locality_issues = self.locality_analyzer.analyze(context)
            issues.extend(locality_issues)
        except Exception as e:
            # Silently continue - don't break pipeline
            self.logger.debug("Locality analysis failed in quick mode: %s", e)
        
        return issues
    
    def _execute_standard_analysis(self, context) -> List[Any]:
        """Execute standard analysis (locality + boundary + conservation).
        
        Args:
            context: Analysis context dict
        
        Returns:
            List of Issue objects
        """
        issues = []
        
        # Level 1: Locality Analysis
        try:
            locality_issues = self.locality_analyzer.analyze(context)
            issues.extend(locality_issues)
        except Exception as e:
            self.logger.debug(f"Locality analysis failed: {e}")
            pass
        
        # Level 3: Boundary Analysis
        try:
            boundary_issues = self.boundary_analyzer.analyze(context)
            issues.extend(boundary_issues)
        except Exception as e:
            self.logger.debug(f"Boundary analysis failed: {e}")
            pass
        
        # Level 4: Conservation Analysis
        try:
            conservation_issues = self.conservation_analyzer.analyze(context)
            issues.extend(conservation_issues)
        except Exception as e:
            self.logger.debug(f"Conservation analysis failed: {e}")
            pass
        
        return issues
    
    def _execute_deep_analysis(self, context) -> List[Any]:
        """Execute deep analysis (all levels including dependency).
        
        Args:
            context: Analysis context dict
        
        Returns:
            List of Issue objects
        """
        issues = []
        
        # Level 1: Locality Analysis
        try:
            locality_issues = self.locality_analyzer.analyze(context)
            issues.extend(locality_issues)
        except Exception as e:
            self.logger.debug(f"Deep locality analysis failed: {e}")
            pass
        
        # Level 2: Dependency Analysis (requires subnet context)
        try:
            dependency_issues = self.dependency_analyzer.analyze(context)
            issues.extend(dependency_issues)
        except Exception as e:
            self.logger.debug(f"Dependency analysis failed: {e}")
            pass
        
        # Level 3: Boundary Analysis
        try:
            boundary_issues = self.boundary_analyzer.analyze(context)
            issues.extend(boundary_issues)
        except Exception as e:
            self.logger.debug(f"Deep boundary analysis failed: {e}")
            pass
        
        # Level 4: Conservation Analysis
        try:
            conservation_issues = self.conservation_analyzer.analyze(context)
            issues.extend(conservation_issues)
        except Exception as e:
            self.logger.debug(f"Deep conservation analysis failed: {e}")
            pass
        
        return issues
    
    def _generate_suggestions(self, issues: List[Any], context: Dict[str, Any]) -> List[Any]:
        """Generate fix suggestions from detected issues.
        
        Args:
            issues: List of Issue objects
            context: Analysis context dict
        
        Returns:
            List of Suggestion objects
        """
        all_suggestions = []
        
        for issue in issues:
            try:
                # Determine which analyzer to use based on issue category
                if 'locality' in issue.message.lower() or 'structural' in issue.category.lower():
                    suggestions = self.locality_analyzer.generate_suggestions([issue], context)
                elif 'boundary' in issue.message.lower():
                    suggestions = self.boundary_analyzer.generate_suggestions([issue], context)
                elif 'conservation' in issue.message.lower():
                    suggestions = self.conservation_analyzer.generate_suggestions([issue], context)
                else:
                    # Default to locality analyzer
                    suggestions = self.locality_analyzer.generate_suggestions([issue], context)
                
                all_suggestions.extend(suggestions)
            except Exception as e:
                # Continue on error - don't break suggestion generation
                self.logger.debug("Suggestion generation failed for issue: %s", e)
        
        return all_suggestions
    
    def batch_analyze(self, transitions: List[Any], mode: str = 'standard',
                     generate_suggestions: bool = False) -> List[AnalysisResult]:
        """Analyze multiple transitions in batch.
        
        Args:
            transitions: List of TransitionKnowledge objects
            mode: Analysis mode ('standard', 'deep', 'quick')
            generate_suggestions: If True, generate fix suggestions
        
        Returns:
            List of AnalysisResult objects
        """
        results = []
        
        for transition in transitions:
            try:
                result = self.analyze(transition, mode=mode, 
                                    generate_suggestions=generate_suggestions)
                results.append(result)
            except Exception as e:
                # Create error result
                results.append(AnalysisResult(
                    transition=transition,
                    issues=[],
                    errors=[f"Analysis failed: {str(e)}"]
                ))
        
        return results
