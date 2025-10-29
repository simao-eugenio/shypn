"""Generate lightweight summary for Report Panel.

This module creates concise summaries of topology analysis results
specifically for display in the Report Panel. It focuses on:
- High-level statistics per category
- Key findings and warnings
- Status indicators

This is NOT the full detailed report - that's handled separately
by the full report generator.

Author: Simão Eugénio
Date: 2025-10-29
"""

from typing import Dict, List, Any, Optional
from datetime import datetime


class TopologySummaryGenerator:
    """Generate concise topology summaries for Report Panel.
    
    This class creates lightweight summaries suitable for displaying
    in the Report Panel alongside other analyses (SBML, Pathway, etc.).
    
    Focus: Quick overview, not detailed results.
    
    Example output:
        {
            'category': 'Topology',
            'status': 'complete',
            'summary_lines': [
                '✓ Structural: 5 P-invariants (92% coverage)',
                '✓ Behavioral: Live, bounded, deadlock-free',
                '⚠️ Graph: 4 hub transitions detected'
            ],
            'statistics': {
                'p_invariants': 5,
                'siphons': 'blocked',
                'is_live': True,
                'has_deadlock': False
            }
        }
    """
    
    def generate_summary(self, all_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate lightweight summary for Report Panel.
        
        Args:
            all_results: Dict of {analyzer_name: AnalysisResult or data dict}
        
        Returns:
            Summary dict with:
            - category: 'Topology'
            - status: 'complete'/'partial'/'error'
            - summary_lines: List of short summary strings
            - statistics: Dict of key metrics
            - warnings: List of warning messages
        """
        # Extract data from results
        structural = self._summarize_structural(all_results)
        graph = self._summarize_graph(all_results)
        behavioral = self._summarize_behavioral(all_results)
        
        # Build summary lines (max 5-7 lines for Report Panel)
        summary_lines = []
        warnings = []
        
        # Structural summary
        structural_parts = []
        if structural['p_invariants_count'] is not None:
            structural_parts.append(f"{structural['p_invariants_count']} P-inv")
        if structural['t_invariants_count'] is not None:
            structural_parts.append(f"{structural['t_invariants_count']} T-inv")
        
        if structural_parts:
            coverage = structural['p_invariants_coverage']
            coverage_str = f" ({coverage:.0%} cov)" if coverage else ""
            summary_lines.append(f"✓ Structural: {', '.join(structural_parts)}{coverage_str}")
        
        # Behavioral summary (most important)
        behavioral_status = []
        if behavioral['is_live']:
            behavioral_status.append("live")
        if behavioral['is_bounded']:
            behavioral_status.append("bounded")
        if not behavioral['has_deadlock']:
            behavioral_status.append("deadlock-free")
        
        if behavioral_status:
            summary_lines.append(f"✓ Behavioral: {', '.join(behavioral_status).capitalize()}")
        elif behavioral['is_live'] is False or behavioral['has_deadlock']:
            # Show problems prominently
            problems = []
            if not behavioral['is_live']:
                problems.append("not live")
            if behavioral['has_deadlock']:
                problems.append("has deadlocks")
            summary_lines.append(f"⚠️ Behavioral: {', '.join(problems).capitalize()}")
        
        # Graph summary
        graph_parts = []
        if graph['cycles_count'] is not None:
            graph_parts.append(f"{graph['cycles_count']} cycles")
        if graph['hubs_count'] and graph['hubs_count'] > 0:
            graph_parts.append(f"{graph['hubs_count']} hubs")
        
        if graph_parts:
            summary_lines.append(f"✓ Graph: {', '.join(graph_parts)}")
        
        # Warnings for blocked analyses
        blocked = []
        if structural['siphons_status'] == 'blocked':
            blocked.append('Siphons')
        if structural['traps_status'] == 'blocked':
            blocked.append('Traps')
        if behavioral['reachability_status'] == 'blocked':
            blocked.append('Reachability')
        
        if blocked:
            warnings.append(f"⚠️ Blocked (model too large): {', '.join(blocked)}")
            summary_lines.append(f"⚠️ {len(blocked)} analyses blocked (model too large)")
        
        # Determine overall status
        status = 'complete'
        if len(blocked) > 0:
            status = 'partial'
        if not summary_lines:
            status = 'error'
        
        # Build statistics dict (for programmatic access)
        statistics = {
            'p_invariants': structural['p_invariants_count'],
            't_invariants': structural['t_invariants_count'],
            'siphons': structural['siphons_count'] if structural['siphons_status'] != 'blocked' else 'blocked',
            'traps': structural['traps_count'] if structural['traps_status'] != 'blocked' else 'blocked',
            'cycles': graph['cycles_count'],
            'hubs': graph['hubs_count'],
            'is_live': behavioral['is_live'],
            'is_bounded': behavioral['is_bounded'],
            'has_deadlock': behavioral['has_deadlock'],
            'reachable_states': behavioral['reachable_states']
        }
        
        return {
            'category': 'Topology',
            'status': status,
            'timestamp': datetime.now().isoformat(),
            'summary_lines': summary_lines,
            'statistics': statistics,
            'warnings': warnings
        }
    
    def _summarize_structural(self, all_results: Dict) -> Dict:
        """Summarize structural analysis results."""
        summary = {
            'p_invariants_count': None,
            'p_invariants_coverage': None,
            't_invariants_count': None,
            't_invariants_coverage': None,
            'siphons_count': None,
            'siphons_status': 'unknown',
            'traps_count': None,
            'traps_status': 'unknown'
        }
        
        # P-Invariants
        if 'p_invariants' in all_results:
            result = self._extract_data(all_results['p_invariants'])
            if result.get('success', True):
                summary['p_invariants_count'] = result.get('count', 0)
                summary['p_invariants_coverage'] = result.get('coverage_ratio', 0)
        
        # T-Invariants
        if 't_invariants' in all_results:
            result = self._extract_data(all_results['t_invariants'])
            if result.get('success', True):
                summary['t_invariants_count'] = result.get('count', 0)
                summary['t_invariants_coverage'] = result.get('coverage_ratio', 0)
        
        # Siphons
        if 'siphons' in all_results:
            result = self._extract_data(all_results['siphons'])
            if result.get('blocked', False):
                summary['siphons_status'] = 'blocked'
            elif result.get('success', True):
                summary['siphons_count'] = result.get('count', 0)
                summary['siphons_status'] = 'success'
        
        # Traps
        if 'traps' in all_results:
            result = self._extract_data(all_results['traps'])
            if result.get('blocked', False):
                summary['traps_status'] = 'blocked'
            elif result.get('success', True):
                summary['traps_count'] = result.get('count', 0)
                summary['traps_status'] = 'success'
        
        return summary
    
    def _summarize_graph(self, all_results: Dict) -> Dict:
        """Summarize graph analysis results."""
        summary = {
            'cycles_count': None,
            'paths_count': None,
            'hubs_count': None,
            'max_hub_degree': None
        }
        
        # Cycles
        if 'cycles' in all_results:
            result = self._extract_data(all_results['cycles'])
            if result.get('success', True):
                summary['cycles_count'] = result.get('count', 0)
        
        # Paths
        if 'paths' in all_results:
            result = self._extract_data(all_results['paths'])
            if result.get('success', True):
                summary['paths_count'] = result.get('count', 0)
        
        # Hubs
        if 'hubs' in all_results:
            result = self._extract_data(all_results['hubs'])
            if result.get('success', True):
                hubs = result.get('hubs', [])
                summary['hubs_count'] = len(hubs)
                if hubs:
                    summary['max_hub_degree'] = max(h.get('degree', 0) for h in hubs)
        
        return summary
    
    def _summarize_behavioral(self, all_results: Dict) -> Dict:
        """Summarize behavioral analysis results."""
        summary = {
            'is_live': None,
            'is_bounded': None,
            'has_deadlock': None,
            'reachable_states': None,
            'reachability_status': 'unknown'
        }
        
        # Liveness
        if 'liveness' in all_results:
            result = self._extract_data(all_results['liveness'])
            if result.get('success', True):
                summary['is_live'] = result.get('is_live', False)
        
        # Boundedness
        if 'boundedness' in all_results:
            result = self._extract_data(all_results['boundedness'])
            if result.get('success', True):
                summary['is_bounded'] = result.get('is_bounded', True)
        
        # Deadlocks
        if 'deadlocks' in all_results:
            result = self._extract_data(all_results['deadlocks'])
            if result.get('success', True):
                summary['has_deadlock'] = result.get('has_deadlock', False)
        
        # Reachability
        if 'reachability' in all_results:
            result = self._extract_data(all_results['reachability'])
            if result.get('blocked', False):
                summary['reachability_status'] = 'blocked'
            elif result.get('success', True):
                summary['reachable_states'] = result.get('total_states', 0)
                summary['reachability_status'] = 'success'
        
        return summary
    
    def _extract_data(self, result: Any) -> Dict:
        """Extract data dict from AnalysisResult object or raw dict.
        
        Args:
            result: AnalysisResult object or data dict
        
        Returns:
            Dict with 'success', 'blocked', 'count', etc.
        """
        if hasattr(result, 'success'):
            # AnalysisResult object
            data = {
                'success': result.success,
                'blocked': result.metadata.get('blocked', False) if hasattr(result, 'metadata') else False
            }
            if hasattr(result, 'data'):
                data.update(result.data)
            return data
        else:
            # Raw dict
            return result
    
    def format_for_report_panel(self, summary: Dict) -> str:
        """Format summary as text for Report Panel display.
        
        Args:
            summary: Result from generate_summary()
        
        Returns:
            Formatted text string with newlines
        """
        lines = []
        
        # Header
        status_icon = {
            'complete': '✓',
            'partial': '⚠️',
            'error': '⚠️'
        }.get(summary['status'], '?')
        
        lines.append(f"{status_icon} Topology Analysis ({summary['status'].upper()})")
        lines.append("")  # Blank line
        
        # Summary lines
        for line in summary['summary_lines']:
            lines.append(f"  {line}")
        
        # Warnings
        if summary.get('warnings'):
            lines.append("")
            for warning in summary['warnings']:
                lines.append(f"  {warning}")
        
        return '\n'.join(lines)
