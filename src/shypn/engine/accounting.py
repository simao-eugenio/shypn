"""
Token Accounting Auditor for Simulation Engine

This module provides comprehensive token tracking and validation to ensure
no token leaks occur during simulation across all transition types.

Features:
- Pre/post-firing token snapshots
- Conservation law validation  
- Detailed leak detection
- Per-transition accounting
- Aggregate statistics

Usage:
    from shypn.engine.accounting import TokenAccountingAuditor
    
    auditor = TokenAccountingAuditor(model)
    auditor.enable()
    
    # Run simulation
    controller.run(duration=100)
    
    # Check for leaks
    report = auditor.generate_report()
    if report['leaks_detected']:
        print(f"TOKEN LEAK: {report['leak_details']}")
"""

import logging
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class TokenSnapshot:
    """Snapshot of place tokens at a specific time."""
    time: float
    place_id: str
    tokens: float
    event: str  # 'before_fire', 'after_fire', 'step_start', 'step_end'
    transition_id: Optional[str] = None


@dataclass
class FiringRecord:
    """Record of a single transition firing."""
    time: float
    transition_id: str
    transition_type: str
    consumed: Dict[str, float] = field(default_factory=dict)
    produced: Dict[str, float] = field(default_factory=dict)
    net_change: float = 0.0
    
    def __post_init__(self):
        """Calculate net token change."""
        total_consumed = sum(self.consumed.values())
        total_produced = sum(self.produced.values())
        self.net_change = total_produced - total_consumed


@dataclass
class ConservationViolation:
    """Record of a conservation law violation."""
    time: float
    transition_id: str
    expected_conservation: bool
    expected_net_change: float
    actual_net_change: float
    places_affected: List[str]
    leak_amount: float
    

@dataclass
class FiringCountDiscrepancy:
    """Record of firing count mismatch."""
    transition_id: str
    expected_firings: int  # From token flow analysis
    actual_firings: int    # From transition.firing_count
    discrepancy: int
    tokens_per_firing: float


class TokenAccountingAuditor:
    """Auditor for tracking token conservation in simulations."""
    
    def __init__(self, model: Any, strict_mode: bool = True):
        """Initialize token accounting auditor.
        
        Args:
            model: Petri net model with places and transitions
            strict_mode: If True, raises errors on violations; if False, logs warnings
        """
        self.model = model
        self.strict_mode = strict_mode
        self.logger = logging.getLogger(__name__)
        
        # Tracking data
        self.snapshots: List[TokenSnapshot] = []
        self.firing_records: List[FiringRecord] = []
        self.violations: List[ConservationViolation] = []
        self.firing_discrepancies: List[FiringCountDiscrepancy] = []
        
        # Statistics
        self.total_firings = 0
        self.total_consumed = 0.0
        self.total_produced = 0.0
        
        # Per-transition statistics
        self.transition_stats: Dict[str, Dict[str, Any]] = defaultdict(
            lambda: {
                'firings': 0,
                'consumed': 0.0,
                'produced': 0.0,
                'net_change': 0.0
            }
        )
        
        # Enabled flag
        self.enabled = False
        
        # Initial token inventory
        self.initial_tokens: Dict[str, float] = {}
        self.current_tokens: Dict[str, float] = {}
        
    def enable(self):
        """Enable token accounting."""
        self.enabled = True
        self._take_initial_snapshot()
        self.logger.info("Token accounting auditor enabled")
        
    def disable(self):
        """Disable token accounting."""
        self.enabled = False
        self.logger.info("Token accounting auditor disabled")
        
    def reset(self):
        """Reset all tracking data."""
        self.snapshots.clear()
        self.firing_records.clear()
        self.violations.clear()
        self.total_firings = 0
        self.total_consumed = 0.0
        self.total_produced = 0.0
        self.transition_stats.clear()
        self._take_initial_snapshot()
        
    def _take_initial_snapshot(self):
        """Record initial token counts."""
        if not hasattr(self.model, 'places'):
            return
        
        # Handle both list and dict for model.places
        places = self.model.places.values() if isinstance(self.model.places, dict) else self.model.places
            
        for place in places:
            self.initial_tokens[place.id] = float(place.tokens)
            self.current_tokens[place.id] = float(place.tokens)
            
    def snapshot_before_fire(self, transition: Any, time: float):
        """Take snapshot before transition fires.
        
        Args:
            transition: Transition about to fire
            time: Current simulation time
        """
        if not self.enabled:
            return
        
        # Handle both list and dict for model.places
        places = self.model.places.values() if isinstance(self.model.places, dict) else self.model.places
            
        for place in places:
            snapshot = TokenSnapshot(
                time=time,
                place_id=place.id,
                tokens=float(place.tokens),
                event='before_fire',
                transition_id=transition.id
            )
            self.snapshots.append(snapshot)
            
    def snapshot_after_fire(
        self,
        transition: Any,
        time: float,
        consumed: Dict[str, float],
        produced: Dict[str, float]
    ):
        """Take snapshot after transition fires and validate conservation.
        
        Args:
            transition: Transition that fired
            time: Current simulation time
            consumed: Dict of place_id -> tokens consumed
            produced: Dict of place_id -> tokens produced
        """
        if not self.enabled:
            return
        
        # Handle both list and dict for model.places
        places = self.model.places.values() if isinstance(self.model.places, dict) else self.model.places
            
        # Take post-fire snapshot
        post_tokens = {}
        for place in places:
            tokens = float(place.tokens)
            post_tokens[place.id] = tokens
            snapshot = TokenSnapshot(
                time=time,
                place_id=place.id,
                tokens=tokens,
                event='after_fire',
                transition_id=transition.id
            )
            self.snapshots.append(snapshot)
            
        # Create firing record
        record = FiringRecord(
            time=time,
            transition_id=transition.id,
            transition_type=getattr(transition, 'transition_type', 'unknown'),
            consumed=consumed.copy(),
            produced=produced.copy()
        )
        self.firing_records.append(record)
        
        # Update statistics
        self.total_firings += 1
        self.total_consumed += sum(consumed.values())
        self.total_produced += sum(produced.values())
        
        stats = self.transition_stats[transition.id]
        stats['firings'] += 1
        stats['consumed'] += sum(consumed.values())
        stats['produced'] += sum(produced.values())
        stats['net_change'] += record.net_change
        
        # Validate conservation
        self._validate_firing(transition, consumed, produced, post_tokens, time)
        
        # Update current tokens
        self.current_tokens.update(post_tokens)
        
    def _validate_firing(
        self,
        transition: Any,
        consumed: Dict[str, float],
        produced: Dict[str, float],
        post_tokens: Dict[str, float],
        time: float
    ):
        """Validate token conservation for a firing.
        
        Args:
            transition: Transition that fired
            consumed: Tokens consumed
            produced: Tokens produced
            post_tokens: Token counts after firing
            time: Current time
        """
        # Check for source/sink transitions
        is_source = getattr(transition, 'is_source', False)
        is_sink = getattr(transition, 'is_sink', False)
        
        total_consumed = sum(consumed.values())
        total_produced = sum(produced.values())
        net_change = total_produced - total_consumed
        
        # Expected behavior
        if is_source and not is_sink:
            # Source: should produce without consuming
            expected_net_change = total_produced
            expected_conservation = False  # Net creation
        elif is_sink and not is_source:
            # Sink: should consume without producing
            expected_net_change = -total_consumed
            expected_conservation = False  # Net destruction
        elif is_source and is_sink:
            # Both: should be balanced
            expected_net_change = 0.0
            expected_conservation = True
        else:
            # Normal: should conserve tokens
            expected_net_change = 0.0
            expected_conservation = True
            
        # Check for violations
        tolerance = 1e-9
        if expected_conservation:
            if abs(net_change) > tolerance:
                # Conservation violated
                leak_amount = net_change
                places_affected = list(set(list(consumed.keys()) + list(produced.keys())))
                
                violation = ConservationViolation(
                    time=time,
                    transition_id=transition.id,
                    expected_conservation=True,
                    expected_net_change=expected_net_change,
                    actual_net_change=net_change,
                    places_affected=places_affected,
                    leak_amount=leak_amount
                )
                self.violations.append(violation)
                
                msg = (
                    f"CONSERVATION VIOLATION at t={time:.6f}: "
                    f"{transition.id} (type={getattr(transition, 'transition_type', '?')}) "
                    f"leaked {leak_amount:+.6f} tokens "
                    f"(consumed={total_consumed:.6f}, produced={total_produced:.6f})"
                )
                
                if self.strict_mode:
                    raise RuntimeError(msg)
                else:
                    self.logger.error(msg)
                    
    def check_global_conservation(self) -> Tuple[bool, float]:
        """Check global token conservation across entire simulation.
        
        Returns:
            Tuple of (conserved: bool, leak_amount: float)
        """
        total_initial = sum(self.initial_tokens.values())
        total_current = sum(self.current_tokens.values())
        
        # Expected change from source/sink transitions
        expected_net = 0.0
        for trans_id, stats in self.transition_stats.items():
            expected_net += stats['net_change']
            
        expected_final = total_initial + expected_net
        actual_final = total_current
        
        leak = actual_final - expected_final
        tolerance = 1e-6
        
        conserved = abs(leak) < tolerance
        
        return conserved, leak
        
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive accounting report.
        
        Returns:
            Dictionary with:
                - leaks_detected: bool
                - global_conservation: bool
                - total_leak: float
                - violations: List[ConservationViolation]
                - firing_discrepancies: List[FiringCountDiscrepancy]
                - statistics: Dict
                - transition_summary: Dict
        """
        conserved, total_leak = self.check_global_conservation()
        firing_counts_valid = self.validate_firing_counts()
        
        report = {
            'leaks_detected': len(self.violations) > 0 or not conserved or not firing_counts_valid,
            'global_conservation': conserved,
            'firing_counts_valid': firing_counts_valid,
            'total_leak': total_leak,
            'violations': self.violations,
            'firing_discrepancies': self.firing_discrepancies,
            'statistics': {
                'total_firings': self.total_firings,
                'total_consumed': self.total_consumed,
                'total_produced': self.total_produced,
                'net_change': self.total_produced - self.total_consumed,
                'num_violations': len(self.violations),
                'num_firing_discrepancies': len(self.firing_discrepancies)
            },
            'initial_tokens': self.initial_tokens.copy(),
            'current_tokens': self.current_tokens.copy(),
            'transition_summary': {}
        }
        
        # Per-transition summary
        for trans_id, stats in self.transition_stats.items():
            report['transition_summary'][trans_id] = {
                'firings': stats['firings'],
                'total_consumed': stats['consumed'],
                'total_produced': stats['produced'],
                'net_change': stats['net_change'],
                'avg_net_per_fire': stats['net_change'] / stats['firings'] if stats['firings'] > 0 else 0.0
            }
            
        return report
        
    def print_report(self):
        """Print human-readable accounting report."""
        report = self.generate_report()
        
        print("\n" + "="*70)
        print("TOKEN ACCOUNTING REPORT")
        print("="*70)
        
        # Global status
        if report['leaks_detected']:
            print("❌ STATUS: TOKEN LEAKS OR FIRING DISCREPANCIES DETECTED")
        else:
            print("✅ STATUS: NO LEAKS - CONSERVATION MAINTAINED")
            
        print(f"\nGlobal Conservation: {'✅ PASS' if report['global_conservation'] else '❌ FAIL'}")
        print(f"Firing Counts Valid: {'✅ PASS' if report['firing_counts_valid'] else '❌ FAIL'}")
        print(f"Total Leak: {report['total_leak']:+.6f} tokens")
        
        # Statistics
        stats = report['statistics']
        print(f"\nStatistics:")
        print(f"  Total Firings: {stats['total_firings']}")
        print(f"  Total Consumed: {stats['total_consumed']:.2f}")
        print(f"  Total Produced: {stats['total_produced']:.2f}")
        print(f"  Net Change: {stats['net_change']:+.2f}")
        print(f"  Violations: {stats['num_violations']}")
        
        # Token inventory
        print(f"\nToken Inventory:")
        print(f"  Initial: {sum(report['initial_tokens'].values()):.2f}")
        print(f"  Current: {sum(report['current_tokens'].values()):.2f}")
        print(f"  Expected: {sum(report['initial_tokens'].values()) + stats['net_change']:.2f}")
        
        # Per-place details
        print(f"\nPer-Place Details:")
        for place_id in sorted(report['initial_tokens'].keys()):
            initial = report['initial_tokens'][place_id]
            current = report['current_tokens'][place_id]
            change = current - initial
            print(f"  {place_id}: {initial:.2f} → {current:.2f} ({change:+.2f})")
            
        # Violations
        if report['violations']:
            print(f"\nToken Violations ({len(report['violations'])}):")
            for i, v in enumerate(report['violations'][:10], 1):  # Show first 10
                print(f"  {i}. t={v.time:.6f}: {v.transition_id} leaked {v.leak_amount:+.6f} tokens")
        
        # Firing count discrepancies
        if report['firing_discrepancies']:
            print(f"\nFiring Count Discrepancies ({len(report['firing_discrepancies'])}):")
            for i, d in enumerate(report['firing_discrepancies'], 1):
                print(f"  {i}. {d.transition_id}: Expected {d.expected_firings}, Actual {d.actual_firings} ({d.discrepancy:+d} discrepancy)")
                
        # Transition summary
        if report['transition_summary']:
            print(f"\nPer-Transition Summary:")
            for trans_id, summary in sorted(report['transition_summary'].items()):
                print(f"  {trans_id}:")
                print(f"    Firings: {summary['firings']}")
                print(f"    Consumed: {summary['total_consumed']:.2f}")
                print(f"    Produced: {summary['total_produced']:.2f}")
                print(f"    Net: {summary['net_change']:+.2f}")
                
        print("="*70 + "\n")
