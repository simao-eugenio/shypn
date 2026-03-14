#!/usr/bin/env python3
"""Thermodynamic Analyzer Adapter for Topology Panel.

This adapter bridges the topology analyzer interface with the advanced
thermodynamics module, providing seamless integration with the topology
panel while leveraging the full power of the compound database system.

Architecture:
- Implements TopologyAnalyzer interface (topology panel contract)
- Delegates to advanced thermodynamics module (production code)
- Reads settings from DocumentModel (universal configuration)
- Maintains backward compatibility with legacy analyzer interface

Phase 3 of Thermodynamics Refactor (Week 3)
Coding Standards: OOP, Wayland-safe, GTK3, ALL CAPS naming

Author: GitHub Copilot
Date: January 2026
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass

from shypn.topology.base.topology_analyzer import TopologyAnalyzer
from shypn.topology.base.analysis_result import AnalysisResult


@dataclass
class ThermodynamicIssue:
    """Issue detected by thermodynamic analysis.
    
    This dataclass maintains compatibility with the legacy analyzer
    interface while providing structured access to validation results.
    """
    transition_id: str
    issue_type: str
    severity: str  # 'info', 'warning', 'error'
    description: str
    suggestion: Optional[str] = None


class ThermodynamicAnalyzerAdapter(TopologyAnalyzer):
    """Adapter for advanced thermodynamics module.
    
    This adapter provides a bridge between the topology analyzer interface
    and the advanced thermodynamics module. It reads settings from the
    DocumentModel (universal configuration) and delegates to the production
    thermodynamics code.
    
    Key Features:
    - Reads pH, temperature, ionic_strength from document settings
    - Uses compound database for accurate ΔG°' calculations
    - Supports multiple mapping strategies (label-based, SBML annotations)
    - Provides detailed validation results with color-coded severity
    - Maintains backward compatibility with topology panel
    
    Example:
        >>> adapter = ThermodynamicAnalyzerAdapter(model)
        >>> result = adapter.analyze()
        >>> print(result.report)
    """
    
    def __init__(self, model: Any, document: Optional[Any] = None):
        """Initialize adapter.
        
        Args:
            model: Petri net model to analyze
            document: Optional DocumentModel for settings (recommended)
        """
        super().__init__(model)
        self.document = document
        self.issues: List[ThermodynamicIssue] = []
        
    def analyze(self, **kwargs) -> AnalysisResult:
        """Perform thermodynamic analysis using advanced module.
        
        This method:
        1. Reads settings from document (or uses defaults)
        2. Creates validator with settings
        3. Runs validation on reversible transitions
        4. Converts results to topology analyzer format
        
        Args:
            **kwargs: Optional parameters (unused, for compatibility)
        
        Returns:
            AnalysisResult with formatted report and structured data
        """
        self.issues.clear()
        
        try:
            # Import advanced thermodynamics module
            from shypn.thermodynamics.simulation_integration import ThermodynamicSimulationValidator
            
            # Create validator with document (reads pH, temperature, etc.)
            validator = ThermodynamicSimulationValidator(document=self.document)
            
            # Get reversible transitions
            reversible_transitions = [
                t for t in self.model.transitions
                if getattr(t, 'reversible', False)
            ]
            
            if not reversible_transitions:
                # No reversible transitions - nothing to validate
                return AnalysisResult(
                    success=True,
                    summary=self._format_no_reversible_report(),
                    data={
                        'issues': [],
                        'statistics': {
                            'total_transitions': len(self.model.transitions),
                            'reversible_transitions': 0,
                            'validated': 0,
                            'valid': 0,
                            'warnings': 0,
                            'violations': 0
                        }
                    }
                )
            
            # Build compound mapping from document
            compound_mappings = {}
            if self.document and hasattr(self.document, 'compound_mappings'):
                compound_mappings = self.document.compound_mappings
            
            # Validate transitions (returns dict of transition_name → validation)
            validation_results = validator.validate_model_transitions(
                reversible_transitions,
                compound_mapping=compound_mappings
            )
            
            # Convert to results format
            results = self._convert_validation_results_to_results_format(validation_results)
            
            # Convert results to issues
            self._convert_results_to_issues(results)
            
            # Generate report
            report = self._format_report(results)
            
            # Determine success (no violations)
            violations = results.get('violations', [])
            success = len(violations) == 0
            
            return AnalysisResult(
                success=success,
                summary=report,
                data={
                    'issues': [
                        {
                            'transition_id': i.transition_id,
                            'type': i.issue_type,
                            'severity': i.severity,
                            'description': i.description,
                            'suggestion': i.suggestion
                        }
                        for i in self.issues
                    ],
                    'results': results,
                    'statistics': {
                        'total_transitions': len(self.model.transitions),
                        'reversible_transitions': len(reversible_transitions),
                        'validated': len(results.get('valid', [])) + len(results.get('warnings', [])) + len(results.get('violations', [])),
                        'valid': len(results.get('valid', [])),
                        'warnings': len(results.get('warnings', [])),
                        'violations': len(results.get('violations', []))
                    }
                }
            )
            
        except Exception as e:
            # Graceful degradation on error
            error_msg = f"Thermodynamic validation failed: {str(e)}"
            self.issues.append(ThermodynamicIssue(
                transition_id='N/A',
                issue_type='validation_error',
                severity='error',
                description=error_msg,
                suggestion='Check that compound mappings are configured in THERMODYNAMICS category'
            ))
            
            return AnalysisResult(
                success=False,
                summary=self._format_error_report(error_msg),
                data={
                    'issues': [
                        {
                            'transition_id': i.transition_id,
                            'type': i.issue_type,
                            'severity': i.severity,
                            'description': i.description,
                            'suggestion': i.suggestion
                        }
                        for i in self.issues
                    ],
                    'error': str(e),
                    'statistics': {
                        'total_transitions': len(self.model.transitions),
                        'reversible_transitions': 0,
                        'validated': 0,
                        'valid': 0,
                        'warnings': 0,
                        'violations': 0
                    }
                }
            )
    
    def _convert_validation_results_to_results_format(
        self,
        validation_results: Dict[str, Any]
    ) -> Dict[str, List]:
        """Convert validation results to expected results format.
        
        Args:
            validation_results: Dict of transition_name → ThermodynamicValidation
            
        Returns:
            Dict with 'valid', 'warnings', 'violations' lists
        """
        valid = []
        warnings = []
        violations = []
        
        for transition_name, validation in validation_results.items():
            result_dict = {
                'transition_id': transition_name,
                'delta_g': validation.delta_g if hasattr(validation, 'delta_g') else 0.0
            }
            
            if validation.is_valid:
                valid.append(result_dict)
            else:
                # Check severity based on delta_g
                if hasattr(validation, 'delta_g'):
                    if validation.delta_g > 10.0:
                        violations.append(result_dict)
                    else:
                        warnings.append(result_dict)
                else:
                    warnings.append(result_dict)
        
        return {
            'valid': valid,
            'warnings': warnings,
            'violations': violations
        }
    
    def _convert_results_to_issues(self, results: Dict[str, List]) -> None:
        """Convert validation results to topology analyzer issues.
        
        Args:
            results: Validation results from ThermodynamicSimulationValidator
        """
        # Process violations (severity: error)
        for result in results.get('violations', []):
            transition_id = result.get('transition_id', 'unknown')
            delta_g = result.get('delta_g', 0)
            
            self.issues.append(ThermodynamicIssue(
                transition_id=transition_id,
                issue_type='thermodynamic_violation',
                severity='error',
                description=f"Thermodynamically unfavorable (ΔG = {delta_g:+.1f} kJ/mol)",
                suggestion='Check reaction direction or add energy coupling (ATP/GTP)'
            ))
        
        # Process warnings (severity: warning)
        for result in results.get('warnings', []):
            transition_id = result.get('transition_id', 'unknown')
            delta_g = result.get('delta_g', 0)
            
            self.issues.append(ThermodynamicIssue(
                transition_id=transition_id,
                issue_type='thermodynamic_warning',
                severity='warning',
                description=f"Near equilibrium (ΔG = {delta_g:+.1f} kJ/mol)",
                suggestion='Reaction may be slow or require coupling'
            ))
        
        # Process valid reactions (severity: info)
        for result in results.get('valid', []):
            transition_id = result.get('transition_id', 'unknown')
            delta_g = result.get('delta_g', 0)
            
            self.issues.append(ThermodynamicIssue(
                transition_id=transition_id,
                issue_type='thermodynamic_valid',
                severity='info',
                description=f"Thermodynamically favorable (ΔG = {delta_g:+.1f} kJ/mol)",
                suggestion=None
            ))
    
    def _format_no_reversible_report(self) -> str:
        """Format report when no reversible transitions exist.
        
        Returns:
            Formatted report string
        """
        lines = [
            "═" * 70,
            "THERMODYNAMIC ANALYSIS REPORT",
            "═" * 70,
            "",
            "No reversible transitions found in model.",
            "",
            "Thermodynamic validation only applies to reversible reactions.",
            "To enable validation:",
            "  1. Mark transitions as reversible in the model",
            "  2. Configure compound mappings in THERMODYNAMICS category",
            "",
            "═" * 70
        ]
        return "\n".join(lines)
    
    def _format_error_report(self, error_msg: str) -> str:
        """Format report when validation fails.
        
        Args:
            error_msg: Error message
            
        Returns:
            Formatted report string
        """
        lines = [
            "═" * 70,
            "THERMODYNAMIC ANALYSIS REPORT - ERROR",
            "═" * 70,
            "",
            f"❌ {error_msg}",
            "",
            "Common issues:",
            "  • Compound mappings not configured",
            "  • Missing compound IDs in model",
            "  • Database connection failure",
            "",
            "Solution:",
            "  Configure compound mappings in THERMODYNAMICS category",
            "",
            "═" * 70
        ]
        return "\n".join(lines)
    
    def _format_report(self, results: Dict[str, List]) -> str:
        """Format validation results as text report.
        
        Args:
            results: Validation results from ThermodynamicSimulationValidator
            
        Returns:
            Formatted report string
        """
        valid = results.get('valid', [])
        warnings = results.get('warnings', [])
        violations = results.get('violations', [])
        
        lines = [
            "═" * 70,
            "THERMODYNAMIC ANALYSIS REPORT",
            "═" * 70,
            "",
            f"✓ Valid:      {len(valid)} reactions",
            f"⚠ Warnings:   {len(warnings)} reactions",
            f"✗ Violations: {len(violations)} reactions",
            "",
        ]
        
        # Settings summary
        if self.document and hasattr(self.document, 'thermodynamic_settings'):
            settings = self.document.thermodynamic_settings
            ph = settings.get('ph', 7.0)
            temp = settings.get('temperature', 298.15)
            ionic = settings.get('ionic_strength', 0.25)
            
            lines.extend([
                "Settings:",
                f"  pH:              {ph:.1f}",
                f"  Temperature:     {temp:.1f} K ({temp-273.15:.1f}°C)",
                f"  Ionic Strength:  {ionic:.2f} M",
                ""
            ])
        
        # Violations (highest priority)
        if violations:
            lines.append("═" * 70)
            lines.append("VIOLATIONS (Thermodynamically Unfavorable)")
            lines.append("═" * 70)
            for result in violations:
                tid = result.get('transition_id', 'unknown')
                delta_g = result.get('delta_g', 0)
                lines.append(f"✗ {tid}: ΔG = {delta_g:+.1f} kJ/mol")
            lines.append("")
        
        # Warnings
        if warnings:
            lines.append("═" * 70)
            lines.append("WARNINGS (Near Equilibrium)")
            lines.append("═" * 70)
            for result in warnings:
                tid = result.get('transition_id', 'unknown')
                delta_g = result.get('delta_g', 0)
                lines.append(f"⚠ {tid}: ΔG = {delta_g:+.1f} kJ/mol")
            lines.append("")
        
        # Valid reactions
        if valid:
            lines.append("═" * 70)
            lines.append("VALID (Thermodynamically Favorable)")
            lines.append("═" * 70)
            for result in valid:
                tid = result.get('transition_id', 'unknown')
                delta_g = result.get('delta_g', 0)
                lines.append(f"✓ {tid}: ΔG = {delta_g:+.1f} kJ/mol")
            lines.append("")
        
        lines.append("═" * 70)
        return "\n".join(lines)
