#!/usr/bin/env python3
"""Module Analysis Tool - Analyze modular Bio-PN architecture.

This CLI tool provides comprehensive analysis of module structure, signal coupling,
and architectural quality metrics for modular Biological Petri Nets following the
13-tuple formalism with Ψ signal places.

Features:
- Module connectivity graph visualization
- Signal coupling strength matrix
- Module independence scoring
- Boundary signal usage statistics
- Architectural quality assessment

Usage:
    python -m cli.analysis.module_analysis <model_file.json>
    python -m cli.analysis.module_analysis --help
"""

from typing import Dict, List, Set, Tuple, Optional, Any
import json
import sys
import argparse
from pathlib import Path
from collections import defaultdict


class ModuleAnalyzer:
    """Analyzer for modular Bio-PN architecture metrics."""
    
    def __init__(self, document_data: Dict[str, Any]):
        """Initialize analyzer with document data.
        
        Args:
            document_data: Parsed JSON document containing modules, places, transitions, arcs
        """
        self.document = document_data
        self.modules = document_data.get('modules', {})
        self.places = {p['id']: p for p in document_data.get('places', [])}
        self.transitions = {t['id']: t for t in document_data.get('transitions', [])}
        self.arcs = document_data.get('arcs', [])
        
        # Build reverse lookups
        self._build_module_contents()
        self._build_arc_connections()
    
    def _build_module_contents(self):
        """Build module → contents mappings."""
        self.module_places: Dict[str, Set[str]] = defaultdict(set)
        self.module_transitions: Dict[str, Set[str]] = defaultdict(set)
        self.module_boundary_signals: Dict[str, Set[str]] = defaultdict(set)
        
        # From places
        for place_id, place in self.places.items():
            module_id = place.get('module_id')
            if module_id:
                self.module_places[module_id].add(place_id)
                if place.get('is_signal_place') or place.get('signal_type'):
                    self.module_boundary_signals[module_id].add(place_id)
        
        # From transitions
        for trans_id, trans in self.transitions.items():
            module_id = trans.get('module_id')
            if module_id:
                self.module_transitions[module_id].add(trans_id)
    
    def _build_arc_connections(self):
        """Build arc connectivity mappings."""
        self.place_inputs: Dict[str, List[Dict]] = defaultdict(list)
        self.place_outputs: Dict[str, List[Dict]] = defaultdict(list)
        self.transition_inputs: Dict[str, List[Dict]] = defaultdict(list)
        self.transition_outputs: Dict[str, List[Dict]] = defaultdict(list)
        
        for arc in self.arcs:
            source_id = arc.get('source_id')
            target_id = arc.get('target_id')
            
            # Determine arc type by looking at source/target types
            if source_id in self.places and target_id in self.transitions:
                # Place → Transition
                self.place_outputs[source_id].append(arc)
                self.transition_inputs[target_id].append(arc)
            elif source_id in self.transitions and target_id in self.places:
                # Transition → Place
                self.transition_outputs[source_id].append(arc)
                self.place_inputs[target_id].append(arc)
    
    def analyze_module_connectivity(self) -> Dict[str, Any]:
        """Analyze module connectivity graph.
        
        Returns:
            Dictionary with connectivity metrics:
            - adjacency_matrix: Module → Module connections
            - signal_coupling: Module → Module signal counts
            - isolated_modules: List of modules with no connections
            - hub_modules: Modules with most connections
        """
        # Build adjacency via shared signals
        adjacency: Dict[str, Set[str]] = defaultdict(set)
        signal_coupling: Dict[Tuple[str, str], Set[str]] = defaultdict(set)
        
        for signal_id, place in self.places.items():
            if not (place.get('is_signal_place') or place.get('signal_type')):
                continue
            
            # Find which modules this signal connects
            connected_modules = set()
            
            # Check input arcs (transitions producing to signal)
            for arc in self.place_inputs.get(signal_id, []):
                trans_id = arc.get('source_id')
                trans = self.transitions.get(trans_id)
                if trans and trans.get('module_id'):
                    connected_modules.add(trans.get('module_id'))
            
            # Check output arcs (transitions reading from signal)
            for arc in self.place_outputs.get(signal_id, []):
                trans_id = arc.get('target_id')
                trans = self.transitions.get(trans_id)
                if trans and trans.get('module_id'):
                    connected_modules.add(trans.get('module_id'))
            
            # Build adjacency for all pairs
            connected_list = list(connected_modules)
            for i, mod_i in enumerate(connected_list):
                for mod_j in connected_list[i+1:]:
                    adjacency[mod_i].add(mod_j)
                    adjacency[mod_j].add(mod_i)
                    # Track which signal couples them
                    signal_coupling[(mod_i, mod_j)].add(signal_id)
                    signal_coupling[(mod_j, mod_i)].add(signal_id)
        
        # Find isolated modules
        all_modules = set(self.modules.keys())
        isolated = [m for m in all_modules if len(adjacency[m]) == 0]
        
        # Find hub modules (most connections)
        hub_threshold = 3
        hubs = [(m, len(adjacency[m])) for m in all_modules if len(adjacency[m]) >= hub_threshold]
        hubs.sort(key=lambda x: x[1], reverse=True)
        
        return {
            'adjacency_matrix': {m: list(adjacency[m]) for m in all_modules},
            'signal_coupling': {f"{m1}->{m2}": list(sigs) for (m1, m2), sigs in signal_coupling.items()},
            'isolated_modules': isolated,
            'hub_modules': hubs,
            'total_modules': len(all_modules),
            'avg_connections': sum(len(v) for v in adjacency.values()) / max(len(all_modules), 1)
        }
    
    def analyze_signal_coupling_strength(self) -> Dict[str, Any]:
        """Analyze signal coupling strength between modules.
        
        Returns:
            Dictionary with coupling metrics:
            - coupling_matrix: Module × Module signal counts
            - strongest_coupling: Top N module pairs by signal count
            - coupling_types: Breakdown by signal type (quorum, energy, etc.)
        """
        coupling_matrix: Dict[Tuple[str, str], int] = defaultdict(int)
        coupling_by_type: Dict[Tuple[str, str], Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        
        for signal_id, place in self.places.items():
            if not (place.get('is_signal_place') or place.get('signal_type')):
                continue
            
            signal_type = place.get('signal_type', 'unknown')
            
            # Find producing and consuming modules
            producers = set()
            consumers = set()
            
            for arc in self.place_inputs.get(signal_id, []):
                trans = self.transitions.get(arc.get('source_id'))
                if trans and trans.get('module_id'):
                    producers.add(trans.get('module_id'))
            
            for arc in self.place_outputs.get(signal_id, []):
                trans = self.transitions.get(arc.get('target_id'))
                if trans and trans.get('module_id'):
                    consumers.add(trans.get('module_id'))
            
            # Count couplings
            for prod in producers:
                for cons in consumers:
                    if prod != cons:
                        coupling_matrix[(prod, cons)] += 1
                        coupling_by_type[(prod, cons)][signal_type] += 1
        
        # Sort by strength
        strongest = sorted(coupling_matrix.items(), key=lambda x: x[1], reverse=True)
        
        return {
            'coupling_matrix': {f"{m1}->{m2}": count for (m1, m2), count in coupling_matrix.items()},
            'strongest_coupling': [(f"{m1}->{m2}", count) for (m1, m2), count in strongest[:10]],
            'coupling_by_type': {
                f"{m1}->{m2}": dict(types) 
                for (m1, m2), types in coupling_by_type.items()
            },
            'total_couplings': len(coupling_matrix),
            'avg_coupling_strength': sum(coupling_matrix.values()) / max(len(coupling_matrix), 1)
        }
    
    def analyze_module_independence(self) -> Dict[str, Any]:
        """Analyze module independence and architectural quality.
        
        Returns:
            Dictionary with independence metrics:
            - independence_scores: Per-module independence (0-1)
            - arc_violations: Arcs crossing module boundaries (should be 0)
            - signal_only_coupling: Whether coupling is signal-only (ideal)
            - overall_quality: Architecture quality score (0-1)
        """
        independence_scores: Dict[str, float] = {}
        arc_violations: List[Dict[str, str]] = []
        
        # Check arc boundary violations
        for arc in self.arcs:
            source_id = arc.get('source_id')
            target_id = arc.get('target_id')
            
            # Get modules for source and target
            source_module = None
            target_module = None
            
            if source_id in self.places:
                source_module = self.places[source_id].get('module_id')
            elif source_id in self.transitions:
                source_module = self.transitions[source_id].get('module_id')
            
            if target_id in self.places:
                target_module = self.places[target_id].get('module_id')
            elif target_id in self.transitions:
                target_module = self.transitions[target_id].get('module_id')
            
            # Check if arc crosses boundary (excluding signals)
            if source_module and target_module and source_module != target_module:
                # Check if target is a signal place (allowed to cross)
                target_is_signal = False
                if target_id in self.places:
                    place = self.places[target_id]
                    target_is_signal = place.get('is_signal_place') or place.get('signal_type')
                
                if not target_is_signal:
                    arc_violations.append({
                        'arc_id': arc.get('id', 'unknown'),
                        'source': source_id,
                        'target': target_id,
                        'source_module': source_module,
                        'target_module': target_module,
                        'type': 'regular_arc_crosses_boundary'
                    })
        
        # Calculate per-module independence
        for module_id in self.modules.keys():
            places = self.module_places.get(module_id, set())
            transitions = self.module_transitions.get(module_id, set())
            signals = self.module_boundary_signals.get(module_id, set())
            
            # Count internal vs external connections
            internal_arcs = 0
            external_arcs = 0
            
            for trans_id in transitions:
                for arc in self.transition_inputs.get(trans_id, []):
                    place_id = arc.get('source_id')
                    if place_id in places:
                        internal_arcs += 1
                    else:
                        external_arcs += 1
                
                for arc in self.transition_outputs.get(trans_id, []):
                    place_id = arc.get('target_id')
                    if place_id in places:
                        internal_arcs += 1
                    else:
                        external_arcs += 1
            
            # Independence = internal / (internal + external)
            # High score = mostly internal connections
            total = internal_arcs + external_arcs
            independence = internal_arcs / total if total > 0 else 1.0
            independence_scores[module_id] = round(independence, 3)
        
        # Overall quality score
        avg_independence = sum(independence_scores.values()) / max(len(independence_scores), 1)
        violation_penalty = len(arc_violations) * 0.1
        overall_quality = max(0.0, min(1.0, avg_independence - violation_penalty))
        
        return {
            'independence_scores': independence_scores,
            'arc_violations': arc_violations,
            'signal_only_coupling': len(arc_violations) == 0,
            'overall_quality': round(overall_quality, 3),
            'avg_independence': round(avg_independence, 3),
            'total_violations': len(arc_violations)
        }
    
    def analyze_boundary_signal_usage(self) -> Dict[str, Any]:
        """Analyze boundary signal usage patterns.
        
        Returns:
            Dictionary with signal usage metrics:
            - signals_by_type: Count by signal type
            - signals_by_module: Signals per module
            - unused_signals: Signals with no connections
            - broadcast_signals: Signals read by multiple modules
        """
        signals_by_type: Dict[str, int] = defaultdict(int)
        signals_by_module: Dict[str, List[str]] = defaultdict(list)
        unused_signals: List[str] = []
        broadcast_signals: List[Dict[str, Any]] = []
        
        for signal_id, place in self.places.items():
            if not (place.get('is_signal_place') or place.get('signal_type')):
                continue
            
            signal_type = place.get('signal_type', 'unknown')
            signals_by_type[signal_type] += 1
            
            module_id = place.get('module_id')
            if module_id:
                signals_by_module[module_id].append(signal_id)
            
            # Count readers
            reader_modules = set()
            for arc in self.place_outputs.get(signal_id, []):
                trans = self.transitions.get(arc.get('target_id'))
                if trans and trans.get('module_id'):
                    reader_modules.add(trans.get('module_id'))
            
            # Check usage
            if len(reader_modules) == 0:
                unused_signals.append(signal_id)
            elif len(reader_modules) >= 2:
                broadcast_signals.append({
                    'signal_id': signal_id,
                    'signal_type': signal_type,
                    'reader_modules': list(reader_modules),
                    'reader_count': len(reader_modules)
                })
        
        return {
            'signals_by_type': dict(signals_by_type),
            'signals_by_module': {k: len(v) for k, v in signals_by_module.items()},
            'unused_signals': unused_signals,
            'broadcast_signals': broadcast_signals,
            'total_signals': sum(signals_by_type.values()),
            'broadcast_ratio': len(broadcast_signals) / max(sum(signals_by_type.values()), 1)
        }
    
    def generate_report(self) -> str:
        """Generate comprehensive module analysis report.
        
        Returns:
            Formatted text report
        """
        lines = []
        lines.append("=" * 80)
        lines.append("MODULE ARCHITECTURE ANALYSIS REPORT")
        lines.append("=" * 80)
        lines.append("")
        
        # Overview
        lines.append("OVERVIEW")
        lines.append("-" * 80)
        lines.append(f"Total Modules:     {len(self.modules)}")
        lines.append(f"Total Places:      {len(self.places)}")
        lines.append(f"Total Transitions: {len(self.transitions)}")
        lines.append(f"Total Arcs:        {len(self.arcs)}")
        lines.append("")
        
        # Module connectivity
        connectivity = self.analyze_module_connectivity()
        lines.append("MODULE CONNECTIVITY")
        lines.append("-" * 80)
        lines.append(f"Average Connections:  {connectivity['avg_connections']:.2f}")
        lines.append(f"Isolated Modules:     {len(connectivity['isolated_modules'])}")
        if connectivity['isolated_modules']:
            lines.append(f"  {', '.join(connectivity['isolated_modules'])}")
        lines.append(f"Hub Modules (≥3 conn): {len(connectivity['hub_modules'])}")
        if connectivity['hub_modules']:
            for mod, conn_count in connectivity['hub_modules'][:5]:
                lines.append(f"  {mod}: {conn_count} connections")
        lines.append("")
        
        # Signal coupling
        coupling = self.analyze_signal_coupling_strength()
        lines.append("SIGNAL COUPLING STRENGTH")
        lines.append("-" * 80)
        lines.append(f"Total Couplings:      {coupling['total_couplings']}")
        lines.append(f"Avg Coupling Strength: {coupling['avg_coupling_strength']:.2f} signals")
        lines.append("Strongest Couplings (Top 5):")
        for pair, strength in coupling['strongest_coupling'][:5]:
            lines.append(f"  {pair}: {strength} signals")
        lines.append("")
        
        # Independence
        independence = self.analyze_module_independence()
        lines.append("MODULE INDEPENDENCE")
        lines.append("-" * 80)
        lines.append(f"Overall Quality Score: {independence['overall_quality']:.3f}")
        lines.append(f"Avg Independence:      {independence['avg_independence']:.3f}")
        lines.append(f"Arc Violations:        {independence['total_violations']}")
        lines.append(f"Signal-Only Coupling:  {'✓ YES' if independence['signal_only_coupling'] else '✗ NO'}")
        if independence['arc_violations']:
            lines.append("\nViolations (regular arcs crossing boundaries):")
            for violation in independence['arc_violations'][:5]:
                lines.append(f"  {violation['source']} → {violation['target']} "
                           f"({violation['source_module']} → {violation['target_module']})")
        lines.append("")
        
        # Signal usage
        signals = self.analyze_boundary_signal_usage()
        lines.append("BOUNDARY SIGNAL USAGE")
        lines.append("-" * 80)
        lines.append(f"Total Signals:    {signals['total_signals']}")
        lines.append(f"Broadcast Ratio:  {signals['broadcast_ratio']:.2%}")
        lines.append(f"Unused Signals:   {len(signals['unused_signals'])}")
        lines.append("\nSignals by Type:")
        for sig_type, count in signals['signals_by_type'].items():
            lines.append(f"  {sig_type}: {count}")
        if signals['broadcast_signals']:
            lines.append("\nBroadcast Signals (multi-module):")
            for bcast in signals['broadcast_signals'][:5]:
                lines.append(f"  {bcast['signal_id']} ({bcast['signal_type']}): "
                           f"{bcast['reader_count']} readers")
        lines.append("")
        
        lines.append("=" * 80)
        return "\n".join(lines)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Analyze modular Bio-PN architecture",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Analyze model file
  python -m cli.analysis.module_analysis model.json
  
  # Save report to file
  python -m cli.analysis.module_analysis model.json > analysis_report.txt
  
  # Generate JSON output
  python -m cli.analysis.module_analysis model.json --format json
        """
    )
    
    parser.add_argument(
        'model_file',
        type=Path,
        help='Path to model JSON file'
    )
    
    parser.add_argument(
        '--format',
        choices=['text', 'json'],
        default='text',
        help='Output format (default: text)'
    )
    
    args = parser.parse_args()
    
    # Load model
    if not args.model_file.exists():
        print(f"Error: File not found: {args.model_file}", file=sys.stderr)
        sys.exit(1)
    
    try:
        with open(args.model_file, 'r') as f:
            document_data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Analyze
    analyzer = ModuleAnalyzer(document_data)
    
    if args.format == 'json':
        # JSON output
        results = {
            'connectivity': analyzer.analyze_module_connectivity(),
            'coupling': analyzer.analyze_signal_coupling_strength(),
            'independence': analyzer.analyze_module_independence(),
            'signal_usage': analyzer.analyze_boundary_signal_usage()
        }
        print(json.dumps(results, indent=2))
    else:
        # Text report
        report = analyzer.generate_report()
        print(report)


if __name__ == '__main__':
    main()
