"""τ-Leaping Simulation Engine.

Main engine for approximate stochastic simulation using τ-leaping method.
Coordinates leap selection, Poisson sampling (for irreversible reactions),
Skellam sampling (for reversible reactions), and state updates.

Supports:
- Irreversible reactions: Poisson(λ) for non-negative rates
- Reversible reactions: Skellam(λ_forward, λ_reverse) for net flux
"""

import logging
import numpy as np
from typing import List, Dict, Any, Tuple, Optional, Set

from .leap_selector import LeapSelector
from .poisson_sampler import PoissonSampler
from .skellam_sampler import SkellamSampler
from .parallel_scheduler import ParallelStochasticScheduler


class TauLeapingEngine:
    """Sequential τ-leaping simulation engine.
    
    Implements approximate stochastic simulation:
    1. Select time leap τ (adaptive based on propensities)
    2. Sample firings for each transition:
       - Irreversible: Kⱼ ~ Poisson(aⱼ·τ)
       - Reversible: ΔKⱼ ~ Skellam(a_forward·τ, a_reverse·τ)
    3. Apply all firings simultaneously
    4. Advance time by τ
    
    This provides significant speedup over exact SSA while maintaining
    controlled accuracy (error bounded by ε parameter).
    
    Example:
        >>> engine = TauLeapingEngine(epsilon=0.03)
        >>> success = engine.execute_step(controller)
        >>> # Transitions fire approximately, time advances by τ
    """
    
    def __init__(
        self,
        epsilon: float = 0.03,
        critical_threshold: float = 10.0,
        max_tau: float = 1.0,
        seed: Optional[int] = None,
        use_parallel: bool = False,
        n_critical: int = 10,
        verbose: bool = True
    ):
        """Initialize τ-leaping engine.
        
        Args:
            epsilon: Leap condition tolerance (smaller = more accurate)
            critical_threshold: Propensity below this triggers exact SSA
            max_tau: Maximum leap size
            seed: Random seed for reproducibility
            use_parallel: Enable parallel sampling for weakly independent transitions.
                         Worker count automatically determined from system capabilities.
            verbose: If False, suppress warnings (for batch mode performance)
        """
        self.leap_selector = LeapSelector(
            epsilon=epsilon,
            critical_threshold=critical_threshold,
            max_tau=max_tau,
            n_critical=n_critical,
        )
        self.poisson_sampler = PoissonSampler(seed=seed)
        self.skellam_sampler = SkellamSampler(seed=seed)  # For reversible reactions
        self.use_parallel = use_parallel
        self.verbose = verbose
        
        # Parallel scheduler (initialized lazily)
        self._parallel_scheduler: Optional[Any] = None
        
        # Control flag for time advancement (can be disabled for hybrid models)
        self._advance_time = True

        # Phase 2.2: dirty-flag tracking — IDs of places modified by the last
        # _apply_firings call.  None on the very first step (forces full sync).
        # Replaces update_y_from_model() on subsequent steps with a partial
        # update touching only the places whose token counts actually changed.
        self._changed_place_ids: Optional[Set[str]] = None

        self.logger = logging.getLogger(__name__)
        
        # Suppress warnings if not verbose
        if not verbose:
            self.logger.setLevel(logging.ERROR)  # Only show errors, not warnings
        
        # Statistics
        self.stats = {
            'total_leaps': 0,
            'total_firings': 0,
            'mean_tau': 0.0,
            'exact_ssa_fallbacks': 0,
            'reversible_reactions': 0,  # Count of Skellam samples
            'irreversible_reactions': 0,  # Count of Poisson samples
            # S4 (engine_stability_audit 2026-04-29):
            # Track Poisson over-sampling that gets silently clamped by the
            # token-availability cap.  Used to surface low-copy bias.
            'requested_firings': 0,    # Sum of Poisson/Skellam draws BEFORE clamping
            'truncated_firings': 0,    # Sum of (requested - actual) when clamp triggered
            'truncation_events': 0,    # Number of (transition, leap) pairs that clamped
        }
    
    def execute_step(
        self,
        controller: Any
    ) -> bool:
        """Execute one τ-leaping step.
        
        Args:
            controller: Simulation controller with model and settings
        
        Returns:
            True if simulation should continue, False if complete
        """
        # Store controller reference for _get_behavior access
        self._controller = controller
        
        model = controller.model
        current_time = controller.time
        
        # Get all stochastic transitions (including adaptive in stochastic mode)
        stochastic_transitions = [
            t for t in model.transitions
            if t.transition_type in ('stochastic', 'adaptive')
        ]
        
        if not stochastic_transitions:
            return False  # No stochastic transitions to execute

        # ── Propensity acceleration ────────────────────────────────────────────
        # Compute the full propensity vector via the C accelerator (once per
        # step) so that both select_tau and _sample_firings share the result
        # instead of each calling _evaluate_rate_at_enablement × N.
        self._accel_props = None
        if hasattr(controller, '_ensure_propensity_accelerator'):
            controller._ensure_propensity_accelerator()
        _prop_accel = getattr(controller, '_propensity_accelerator', None)
        # Guard: only use a real PropensityAccelerator, not a Mock auto-attribute.
        # Real accelerators define 'ready' at the class level; Mock's do not.
        if _prop_accel is not None and getattr(type(_prop_accel), 'ready', None) is None:
            _prop_accel = None
        if _prop_accel is not None and _prop_accel.ready:
            try:
                # Phase 2.2: partial y[] update — only sync places that changed
                # last step; fall back to full update on the first step.
                if self._changed_place_ids is not None:
                    _prop_accel.update_y_partial(self._changed_place_ids)
                else:
                    _prop_accel.update_y_from_model()
                _prop_accel.update_thermo_params()
                _a_net, _a_fwd, _a_rev = _prop_accel.compute(current_time)
                self._accel_props = {
                    tid: (
                        float(_a_net[i]),
                        float(_a_fwd[i]),
                        float(_a_rev[i]),
                    )
                    for i, tid in enumerate(_prop_accel.transition_ids_order)
                }
            except Exception as _exc:
                self.logger.debug(
                    "PropensityAccelerator.compute failed (%s); "
                    "falling back to Python eval",
                    _exc,
                )
                self._accel_props = None
        # ──────────────────────────────────────────────────────────────────────

        # Phase 2.1: pass precomputed arc table to leap selector so
        # _get_min_input_tokens uses O(k) lookup instead of O(|arcs|) scan.
        _arc_table_raw = (
            _prop_accel._input_arc_table
            if _prop_accel is not None and _prop_accel.ready
            else None
        )
        _arc_table = _arc_table_raw if isinstance(_arc_table_raw, dict) else None

        # Phase 3: pass stoichiometry data so the Cao et al. (2006) full leap
        # condition can be used instead of the simplified ε/max(a) formula.
        _cao_data = None
        if (
            _prop_accel is not None
            and _prop_accel.ready
            and _prop_accel._stoich_matrix is not None
            and self._accel_props is not None
        ):
            _cao_data = (
                _prop_accel._stoich_matrix,
                _prop_accel._stoich_matrix_sq,
                _prop_accel._y_arr,
                _prop_accel._g_vec,
                _prop_accel.transition_ids_order,
            )

        # Step 1: Select leap size τ
        tau, leap_info = self.leap_selector.select_tau(
            stochastic_transitions,
            model,
            current_time,
            controller,
            propensity_hint=self._accel_props,
            arc_table=_arc_table,
            cao_data=_cao_data,
        )
        
        # Log tau selection for debugging
        self.logger.debug(
            f"τ-leaping: selected tau={tau:.6f}, "
            f"propensities={leap_info.get('propensities', [])}, "
            f"epsilon={self.leap_selector.epsilon}"
        )
        
        # Check if should fall back to exact SSA
        if tau == 0.0 or leap_info.get('reason') == 'all_critical':
            self.stats['exact_ssa_fallbacks'] += 1
            return self._execute_exact_ssa_step(controller, stochastic_transitions)
        
        # Step 2: Calculate propensities and sample firings
        firings_map = self._sample_firings(
            stochastic_transitions,
            tau,
            current_time
        )
        
        # Log sampled firings for debugging
        self.logger.debug(
            f"τ-leaping: sampled firings={dict((t.name, f) for t, f in firings_map.items() if f > 0)}"
        )
        
        # Step 3: Apply firings (consume/produce tokens)
        # Reset dirty-flag set; _apply_firings will populate it.
        self._changed_place_ids = set()
        total_firings = self._apply_firings(
            firings_map,
            controller
        )
        
        # Step 4: Advance time (only if enabled - disabled for hybrid models)
        if self._advance_time:
            controller.time += tau

        # S5 (engine_stability_audit 2026-04-29): expose τ so the data
        # collector can force-record transient steps.
        _dc = getattr(controller, 'data_collector', None)
        if _dc is not None and hasattr(_dc, 'notify_step_size'):
            _dc.notify_step_size(tau)
        
        # Step 4.5: Update assignment rule-defined species (Option 3)
        if getattr(controller, 'enable_assignment_rule_reevaluation', False) is True:
            self._update_assignment_rules(controller)
        
        # NOTE: State recording moved to controller.step() to avoid duplicate recording
        # Controller records state once per step after all phases complete
        
        # Step 5: Update statistics
        self.stats['total_leaps'] += 1
        self.stats['total_firings'] += total_firings
        self.stats['mean_tau'] = (
            (self.stats['mean_tau'] * (self.stats['total_leaps'] - 1) + tau)
            / self.stats['total_leaps']
        )
        
        # Step 6: Record leap event
        if hasattr(controller, 'data_collector') and controller.data_collector:
            controller.data_collector.record_event(
                time=controller.time,
                event_type='tau_leap',
                data={
                    'tau': tau,
                    'total_firings': total_firings,
                    'num_transitions': len([k for k in firings_map.values() if k > 0]),
                    'leap_info': leap_info
                }
            )
        
        # Check if simulation should continue
        # If duration is None, run indefinitely (return True)
        duration_s = controller.settings.get_duration_seconds()
        if duration_s is None:
            return True
        return controller.time < duration_s
    
    def _sample_firings(
        self,
        transitions: List[Any],
        tau: float,
        current_time: float
    ) -> Dict[Any, int]:
        """Sample number of firings for each transition.
        
        Detects reversible reactions (formulas with subtraction) and uses
        Skellam distribution. Otherwise uses Poisson distribution.
        
        Args:
            transitions: List of stochastic transitions
            tau: Time leap size
            current_time: Current simulation time
        
        Returns:
            Dictionary mapping transition -> number of firings (can be negative for reversible)
        """
        propensities = []

        for transition in transitions:
            # ── Fast path: use pre-computed propensity from C accelerator ─────
            _cached = (self._accel_props or {}).get(
                getattr(transition, 'id', None)
            )
            if _cached is not None:
                net, fwd, rev = _cached
                propensities.append(net)
                # Only trust rev > 0 as reversible; otherwise leave existing flag
                if rev > 0.0:
                    transition._skellam_reversible = True
                    transition._accel_fwd_prop = fwd
                    transition._accel_rev_prop = rev
                else:
                    # Clear stale accelerator props if present
                    transition.__dict__.pop('_accel_fwd_prop', None)
                    transition.__dict__.pop('_accel_rev_prop', None)
                continue
            # ── Python eval fallback ──────────────────────────────────────────
            behavior = self._get_behavior(transition)
            if behavior is None:
                propensities.append(0.0)
                continue

            # Calculate propensity
            try:
                propensity = behavior._evaluate_rate_at_enablement(current_time)

                # Check if this is a reversible reaction
                if hasattr(behavior, 'rate_function_expr') and behavior.rate_function_expr:
                    is_reversible, forward_expr, reverse_expr = (
                        SkellamSampler.detect_reversible_formula(behavior.rate_function_expr)
                    )

                    if is_reversible:
                        # Mark for Skellam sampling
                        transition._skellam_reversible = True
                        transition._forward_expr = forward_expr
                        transition._reverse_expr = reverse_expr
                    else:
                        transition._skellam_reversible = False
                else:
                    transition._skellam_reversible = False

            except Exception as e:
                self.logger.warning(
                    f"Could not evaluate propensity for {transition.name}: {e}. Using default rate."
                )
                propensity = getattr(behavior, 'rate', 1.0)
                transition._skellam_reversible = False

            propensities.append(propensity)
        
        # Use parallel or sequential sampling
        if self.use_parallel and len(transitions) >= 4:
            # Lazy initialize parallel scheduler
            if self._parallel_scheduler is None:
                # Prefer controller reference (set in execute_step) over the
                # now-removed transition.parent_model attribute.
                model = None
                if hasattr(self, '_controller') and self._controller is not None:
                    model = getattr(self._controller, 'model', None)

                if model:
                    self._parallel_scheduler = ParallelStochasticScheduler(
                        model=model,
                        enable_parallel=True
                    )
                else:
                    # Fallback to sequential (should not happen in normal use)
                    self.logger.debug("Could not access model for parallel scheduler, using sequential")
                    self.use_parallel = False

            if self._parallel_scheduler:
                # Apply inhibitor-arc constraints after parallel sampling.
                # The parallel path samples all transitions independently;
                # without this step any transition with a curved_inhibitor_arc
                # (or any inhibitor arc variant) runs unconstrained — the
                # inhibitor check must be applied regardless of the sampling
                # path used.
                firings_map = self._parallel_scheduler.sample_parallel(
                    transitions, propensities, tau
                )
                firings_map = self._apply_inhibitor_constraints(
                    firings_map, transitions
                )
                return firings_map
        
        # Sequential sampling with Skellam support for reversible reactions
        firings_map = {}
        
        # Diagnostic: Check for extreme propensities before sampling
        if np.any(np.array(propensities) > 1e10):
            max_prop = max(propensities)
            max_idx = propensities.index(max_prop)
            problem_transition = transitions[max_idx]
            
            # Get transition details - try multiple attribute names
            trans_name = getattr(problem_transition, 'label', getattr(problem_transition, 'name', f"T{max_idx}"))
            trans_id = getattr(problem_transition, 'id', f"transition_{max_idx}")
            
            # Try to get behavior and formula
            formula_str = 'N/A'
            input_info = []
            
            try:
                behavior = self._get_behavior(problem_transition)
                if behavior:
                    # Get formula from behavior
                    if hasattr(behavior, 'formula'):
                        formula_str = str(behavior.formula)
                    elif hasattr(behavior, 'rate_expression'):
                        formula_str = str(behavior.rate_expression)
                    
                    # Get input places and their markings
                    if hasattr(behavior, 'input_places'):
                        for place in behavior.input_places:
                            place_name = getattr(place, 'label', getattr(place, 'name', getattr(place, 'id', 'unknown')))
                            marking = getattr(place, 'marking', 0)
                            input_info.append(f"{place_name}={marking:.2e}")
                    
                    # Also try to evaluate the formula with current context to see what values are being used
                    if hasattr(behavior, 'context') or hasattr(behavior, '_context'):
                        context = getattr(behavior, 'context', getattr(behavior, '_context', {}))
                        if context and isinstance(context, dict):
                            # Show a sample of context values
                            context_items = list(context.items())[:5]
                            context_str = ", ".join([f"{k}={v:.2e}" if isinstance(v, (int, float)) else f"{k}={v}" 
                                                    for k, v in context_items])
                            formula_str += f" [Context sample: {context_str}]"
            except Exception as diag_err:
                # Don't let diagnostic failure block the error report
                formula_str += f" [Diagnostic error: {diag_err}]"
            
            inputs_str = ", ".join(input_info) if input_info else "Unknown inputs"
            
            self.logger.warning(
                f"Extreme propensity detected:\n"
                f"  Transition #{max_idx}: {trans_name} (id={trans_id})\n"
                f"  Propensity: {max_prop:.2e}\n"
                f"  Tau: {tau:.2e}\n"
                f"  Lambda (propensity*tau): {max_prop*tau:.2e}\n"
                f"  Input places: {inputs_str}\n"
                f"  Kinetic law: {formula_str[:200]}{'...' if len(formula_str) > 200 else ''}"
            )
        
        # Phase 4b: Single vectorized Poisson call for all irreversible transitions.
        # Reversible reactions (Skellam) are sampled individually — they are a small
        # minority in metabolic/signalling models.  For GATA: ~3 reversible out of 29.
        _irrev_trans: List[Any] = []
        _irrev_lam:   List[float] = []
        for _t, _p in zip(transitions, propensities):
            if not getattr(_t, '_skellam_reversible', False):
                _irrev_trans.append(_t)
                _irrev_lam.append(max(0.0, _p))
        if _irrev_trans:
            _lam_arr = np.array(_irrev_lam, dtype=np.float64) * tau
            _k_arr   = self.poisson_sampler.rng.poisson(lam=_lam_arr)  # ONE C call
            for _t, _k in zip(_irrev_trans, _k_arr):
                firings_map[_t] = int(_k)
            self.stats['irreversible_reactions'] += len(_irrev_trans)

        # Reversible reactions: individual Skellam sampling
        for transition, propensity in zip(transitions, propensities):
            if not getattr(transition, '_skellam_reversible', False):
                continue
            try:
                if hasattr(transition, '_accel_fwd_prop'):
                    forward_prop = transition._accel_fwd_prop
                    reverse_prop = transition._accel_rev_prop
                elif propensity >= 0:
                    forward_prop = propensity
                    reverse_prop = 0.0
                else:
                    forward_prop = 0.0
                    reverse_prop = abs(propensity)
                firings = self.skellam_sampler.sample(forward_prop, reverse_prop, tau)
                firings_map[transition] = firings
                self.stats['reversible_reactions'] += 1
            except Exception as e:
                self.logger.warning(
                    f"Skellam sampling failed for {transition.name}: {e}. Using Poisson."
                )
                firings = self.poisson_sampler.sample(max(0, propensity), tau)
                firings_map[transition] = firings
                self.stats['irreversible_reactions'] += 1

        # Apply inhibitor arc constraints to limit firings
        firings_map = self._apply_inhibitor_constraints(firings_map, transitions)
        
        return firings_map
    
    def _apply_inhibitor_constraints(
        self,
        firings_map: Dict[Any, int],
        transitions: List[Any]
    ) -> Dict[Any, int]:
        """Apply inhibitor arc constraints to limit firings.
        
        For each transition with inhibitor arcs, check if the products
        would exceed their thresholds and reduce firings accordingly.
        
        Args:
            firings_map: Dictionary mapping transition -> sampled firings
            transitions: List of transitions
        
        Returns:
            Modified firings_map with inhibitor constraints applied
        """
        from shypn.utils.threshold_evaluator import ThresholdEvaluator
        import sys
        
        constrained_map = {}
        
        for transition in transitions:
            original_firings = firings_map.get(transition, 0)
            if original_firings <= 0:
                constrained_map[transition] = original_firings
                continue
            
            # Get behavior to access arcs
            behavior = self._get_behavior(transition)
            if behavior is None:
                constrained_map[transition] = original_firings
                continue
            
            # Get arcs
            try:
                input_arcs = behavior.get_input_arcs()
                output_arcs = behavior.get_output_arcs()
            except Exception as e:
                print(f"❌ Could not get arcs for {getattr(transition, 'name', 'unknown')}: {e}", file=sys.stderr)
                self.logger.debug(f"Could not get arcs for {transition.name}: {e}")
                constrained_map[transition] = original_firings
                continue
            
            # Find inhibitor arcs (Product → Transition) using defensive pattern
            # FIXED v2.1.2: Detect ALL inhibitor arc variants (includes curved_inhibitor_arc)
            def _arc_type_str(arc: Any) -> str:
                v = getattr(arc, 'arc_type', None)
                return v if isinstance(v, str) else 'normal'

            inhibitor_arcs = [arc for arc in input_arcs if
                            _arc_type_str(arc) == 'inhibitor' or
                            'inhibitor' in _arc_type_str(arc) or
                            getattr(arc, 'kind', None) == 'inhibitor']
            
            if not inhibitor_arcs:
                # No inhibitors, use original firings
                constrained_map[transition] = original_firings
                continue
            
            # Found inhibitors - evaluate constraints
            trans_name = getattr(transition, 'name', getattr(transition, 'label', 'unknown'))
            
            # Calculate maximum allowed firings based on inhibitors
            max_allowed_firings = original_firings
            
            for inh_arc in inhibitor_arcs:
                try:
                    # The source of inhibitor arc is the product place
                    product_place = behavior._get_place(inh_arc.source_id)
                    if not product_place:
                        continue
                    
                    # Evaluate threshold dynamically
                    evaluator = ThresholdEvaluator(behavior.model)
                    context = {'time': behavior.model.time if hasattr(behavior.model, 'time') else 0.0}
                    threshold = evaluator.evaluate(inh_arc, context)
                    
                    # Current tokens in product place
                    current_tokens = product_place.tokens
                    
                    # Find how much this transition produces to that place
                    # Note: output_arcs should be arc objects, but handle strings just in case
                    tokens_per_firing = 0.0
                    
                    for out_arc_ref in output_arcs:
                        # Get actual arc object if we have an ID string
                        if isinstance(out_arc_ref, str):
                            # It's an arc ID, need to get the arc object from model
                            out_arc = behavior._get_arc(out_arc_ref)
                            if not out_arc:
                                continue
                        else:
                            out_arc = out_arc_ref
                        
                        if out_arc.target_id == product_place.id:
                            tokens_per_firing = out_arc.weight
                            break
                    
                    if tokens_per_firing > 0:
                        # Calculate remaining capacity
                        remaining = threshold - current_tokens
                        
                        if remaining <= 0:
                            # Already at or above threshold, no firings allowed
                            max_allowed_firings = 0
                            break
                        
                        # Calculate max firings before exceeding threshold
                        max_firings_for_this_inhibitor = int(remaining / tokens_per_firing)
                        
                        # Keep the most restrictive constraint
                        max_allowed_firings = min(max_allowed_firings, max_firings_for_this_inhibitor)
                
                except Exception as e:
                    import traceback
                    self.logger.error(
                        f"❌ Error evaluating inhibitor for {trans_name}: {e}\n"
                        f"Traceback: {traceback.format_exc()}"
                    )
                    print(f"❌ Error evaluating inhibitor for {trans_name}: {e}", file=sys.stderr)
                    continue
            
            # Apply the constraint
            if max_allowed_firings < original_firings:
                trans_name = getattr(transition, 'name', getattr(transition, 'label', 'unknown'))
                self.logger.info(
                    f"🔒 Inhibitor constraint: {trans_name} firings reduced "
                    f"{original_firings} → {max_allowed_firings}"
                )
            
            constrained_map[transition] = max_allowed_firings
        
        return constrained_map

    def _k_arr_to_firings_map(
        self,
        k_arr: Any,
        accel: Any,
        stochastic_transitions: List[Any],
    ) -> Dict[Any, int]:
        """Convert a JIT firing-count array to a transition→count dict.

        Maps the integer array aligned with ``accel.transition_ids_order``
        to ``{transition_obj: num_firings}`` so the existing
        ``_apply_inhibitor_constraints`` and ``_apply_firings_fast`` machinery
        can be reused without modification.  Called only in the Phase 6 JIT
        path.

        Args:
            k_arr: int64 array of firing counts (JIT kernel output).
            accel: PropensityAccelerator with ``transition_ids_order``.
            stochastic_transitions: Transition objects with matching IDs.

        Returns:
            Dict mapping transition object → integer firing count.
        """
        trans_by_id: Dict[str, Any] = {
            getattr(t, 'id', None): t for t in stochastic_transitions
        }
        firings_map: Dict[Any, int] = {}
        for j, tid in enumerate(accel.transition_ids_order):
            k = int(k_arr[j])
            trans = trans_by_id.get(tid)
            if trans is not None:
                firings_map[trans] = k
        return firings_map

    def _apply_firings_fast(
        self,
        firings_map: Dict[Any, int],
        controller: Any,
        accel: Any,
    ) -> int:
        """Vectorised _apply_firings using the stoichiometry matrix (Phase 3).

        Replaces the sequential per-arc ``set_tokens`` loop with a single BLAS
        ``S @ k`` matrix-vector product, then writes all place tokens back from
        the ``_y_arr`` buffer.  Consumed/produced maps are derived from the
        precomputed arc tables so no ``behavior.get_*_arcs()`` calls are needed.
        """
        import numpy as np

        n_t = accel._n_transitions
        k_arr = np.zeros(n_t, dtype=np.float64)
        tid_to_j: Dict[str, int] = {
            tid: j for j, tid in enumerate(accel.transition_ids_order)
        }
        _in_tbl  = accel._input_arc_table
        _out_tbl = accel._output_arc_table
        per_trans: List[Tuple[Any, int, Dict, Dict]] = []

        for transition, num_firings in firings_map.items():
            if num_firings == 0:
                continue
            _tid = getattr(transition, 'id', None)

            # Cap firings using precomputed input arc table (O(k) per transition)
            in_entries = _in_tbl.get(_tid, [])
            max_poss = num_firings
            for _p, _w in in_entries:
                if _w > 0.0:
                    max_poss = min(max_poss, int(_p.tokens // _w))
            actual = max(0, min(num_firings, max_poss))
            # S4: track Poisson over-sampling clamped by token availability.
            self.stats['requested_firings'] += int(num_firings)
            if actual < num_firings:
                self.stats['truncated_firings'] += int(num_firings - actual)
                self.stats['truncation_events'] += 1
            if actual == 0:
                continue

            consumed_map: Dict[str, float] = {
                _p.id: _w * actual for _p, _w in in_entries
            }
            produced_map: Dict[str, float] = {
                _p.id: _w * actual for _p, _w in _out_tbl.get(_tid, [])
            }
            per_trans.append((transition, actual, consumed_map, produced_map))

            j = tid_to_j.get(_tid)
            if j is not None:
                k_arr[j] = float(actual)

        total_firings = sum(act for _, act, _, _ in per_trans)

        if total_firings > 0:
            # ── Vectorised token update ─────────────────────────────────────
            delta = accel._stoich_matrix @ k_arr   # shape (n_places,)
            y = accel._y_arr
            y += delta
            np.clip(y, 0.0, None, out=y)
            # Write back to place objects
            for pid, idx in accel._all_place_index.items():
                p = accel._places_by_id.get(pid)
                if p is not None:
                    p.tokens = float(y[idx])
            # ────────────────────────────────────────────────────────────────

        # ── Recording + dirty-flag tracking ─────────────────────────────────
        _dc = getattr(controller, 'data_collector', None)
        _listeners = getattr(controller, 'step_listeners', [])
        for transition, actual, consumed_map, produced_map in per_trans:
            # Phase 2.2: dirty-flag tracks which places changed
            if self._changed_place_ids is not None:
                self._changed_place_ids.update(consumed_map)
                self._changed_place_ids.update(produced_map)
            if _dc is not None:
                _dc.record_firing(
                    time=controller.time,
                    transition=transition,
                    consumed=consumed_map,
                    produced=produced_map,
                    mode='tau_leaping',
                    firings=actual,
                )
            if _listeners:
                details = {
                    'consumed': consumed_map,
                    'produced': produced_map,
                    'mode': 'tau_leaping',
                    'firings': actual,
                }
                for listener in _listeners:
                    listener_obj = getattr(listener, '__self__', listener)
                    if hasattr(listener_obj, 'on_transition_fired'):
                        for _ in range(actual):
                            listener_obj.on_transition_fired(
                                transition, controller.time, details
                            )
        # ────────────────────────────────────────────────────────────────────
        return total_firings

    def _apply_firings(
        self,
        firings_map: Dict[Any, int],
        controller: Any
    ) -> int:
        """Apply sampled firings to update state.
        
        Args:
            firings_map: Dictionary of transition -> firings
            controller: Simulation controller
        
        Returns:
            Total number of firings applied
        """
        # Phase 3: dispatch to vectorised fast path when stoich matrix is ready.
        _prop_accel = getattr(controller, '_propensity_accelerator', None)
        # Guard: reject Mock auto-attributes (no class-level 'ready' property)
        if _prop_accel is not None and getattr(type(_prop_accel), 'ready', None) is None:
            _prop_accel = None
        if (
            _prop_accel is not None
            and _prop_accel.ready
            and _prop_accel._stoich_matrix is not None
        ):
            return self._apply_firings_fast(firings_map, controller, _prop_accel)

        total_firings = 0
        
        for transition, num_firings in firings_map.items():
            if num_firings == 0:
                continue
            
            # Get behavior
            behavior = self._get_behavior(transition)
            if behavior is None:
                continue
            
            # Get input/output arcs
            input_arcs = behavior.get_input_arcs()
            output_arcs = behavior.get_output_arcs()
            
            # Check token availability (conservative: ensure we don't go negative)
            max_possible_firings = self._calculate_max_firings(
                transition,
                input_arcs,
                num_firings
            )
            
            actual_firings = min(num_firings, max_possible_firings)

            # S4: track Poisson over-sampling clamped by token availability.
            self.stats['requested_firings'] += int(num_firings)
            if actual_firings < num_firings:
                self.stats['truncated_firings'] += int(num_firings - actual_firings)
                self.stats['truncation_events'] += 1
                # Log if we had to cap firings due to insufficient tokens (debug level only)
                self.logger.debug(
                    f"τ-leaping: Capped {transition.name} firings from {num_firings} to {actual_firings} "
                    f"(insufficient tokens). Consider reducing tau or epsilon."
                )
            
            if actual_firings == 0:
                continue
            
            # Apply firings
            consumed_map, produced_map = self._fire_transition_multiple(
                transition,
                input_arcs,
                output_arcs,
                actual_firings,
                behavior
            )

            # Phase 2.2: record which place IDs changed for the dirty-flag
            if self._changed_place_ids is not None:
                self._changed_place_ids.update(consumed_map)
                self._changed_place_ids.update(produced_map)

            total_firings += actual_firings
            
            # Record firing event in engine's data collector (for reports)
            if hasattr(controller, 'data_collector') and controller.data_collector:
                controller.data_collector.record_firing(
                    time=controller.time,
                    transition=transition,
                    consumed=consumed_map,
                    produced=produced_map,
                    mode='tau_leaping',
                    firings=actual_firings
                )
            
            # Notify step listeners that have on_transition_fired (for analyses/plotting)
            _listeners = getattr(controller, 'step_listeners', None)
            if isinstance(_listeners, (list, tuple)) and _listeners:
                details = {
                    'consumed': consumed_map,
                    'produced': produced_map,
                    'mode': 'tau_leaping',
                    'firings': actual_firings
                }
                for listener in _listeners:
                    # Listeners are bound methods, check the object they're bound to
                    listener_obj = getattr(listener, '__self__', listener)
                    if hasattr(listener_obj, 'on_transition_fired'):
                        # Notify once per actual firing for cumulative count tracking
                        for _ in range(actual_firings):
                            listener_obj.on_transition_fired(transition, controller.time, details)
        
        return total_firings
    
    def _calculate_max_firings(
        self,
        transition: Any,
        input_arcs: List[Any],
        requested_firings: int
    ) -> int:
        """Calculate maximum possible firings given available tokens.
        
        Args:
            transition: Transition object
            input_arcs: List of input arcs
            requested_firings: Requested number of firings
        
        Returns:
            Maximum firings possible (may be < requested)
        """
        # Source transitions have unlimited firings
        if getattr(transition, 'is_source', False):
            return requested_firings
        
        max_firings = requested_firings
        
        for arc in input_arcs:
            # Per 13-tuple Bio-PN formalism + classical PN literature:
            # test and inhibitor (incl. curved_inhibitor_arc) arcs are
            # non-consuming presence/absence checks and therefore do NOT
            # constrain max_firings. Use Arc.consumes_tokens() as the
            # single source of truth (mirrors _fire_transition_multiple).
            if not arc.consumes_tokens():
                continue
            
            source_place = arc.source
            if source_place is None:
                continue
            
            available_tokens = source_place.tokens
            tokens_per_firing = arc.weight
            
            if tokens_per_firing > 0:
                max_from_place = int(available_tokens // tokens_per_firing)
                max_firings = min(max_firings, max_from_place)
        
        return max(0, max_firings)
    
    def _fire_transition_multiple(
        self,
        transition: Any,
        input_arcs: List[Any],
        output_arcs: List[Any],
        num_firings: int,
        behavior: Any
    ) -> Tuple[Dict[int, float], Dict[int, float]]:
        """Fire a transition multiple times.
        
        Args:
            transition: Transition to fire
            input_arcs: Input arcs
            output_arcs: Output arcs
            num_firings: Number of times to fire
            behavior: Transition behavior
        
        Returns:
            Tuple of (consumed_map, produced_map)
        """
        consumed_map = {}
        produced_map = {}
        
        # Check if source/sink
        is_source = getattr(transition, 'is_source', False)
        is_sink = getattr(transition, 'is_sink', False)
        
        # Phase 1: Consume tokens (skip if source)
        # Per 13-tuple Bio-PN formalism: only TEST arcs are non-consuming.
        # signal_flow and inhibitor arcs consume tokens (see SignalFlowArc
        # docstring + immediate_behavior.py "v2.1.1: Only TEST arcs skip").
        # Use the cached arc_type property as the single source of truth;
        # the legacy properties['kind'] alias is intentionally NOT consulted
        # here to avoid silent dual-source-of-truth divergence.
        if not is_source:
            for arc in input_arcs:
                # Per 13-tuple Bio-PN formalism + classical PN literature:
                # test and inhibitor (all variants) arcs are non-consuming.
                # Use Arc.consumes_tokens() as single source of truth.
                if not arc.consumes_tokens():
                    continue

                source_place = arc.source
                if source_place is None:
                    continue

                amount = arc.weight * num_firings
                source_place.set_tokens(source_place.tokens - amount)
                consumed_map[source_place.id] = float(amount)
        
        # Phase 2: Produce tokens (skip if sink)
        if not is_sink:
            for arc in output_arcs:
                target_place = arc.target
                if target_place is None:
                    continue
                
                amount = arc.weight * num_firings
                target_place.set_tokens(target_place.tokens + amount)
                produced_map[target_place.id] = float(amount)
        
        # NOTE: firing_count is incremented by data_collector.record_firing() 
        # in _apply_firings(), not here. Removed duplicate increment that was
        # causing 2× firing counts and 50% token loss bug.
        
        return consumed_map, produced_map
    
    def _execute_exact_ssa_step(
        self,
        controller: Any,
        stochastic_transitions: List[Any]
    ) -> bool:
        """Fall back to exact SSA for one step.
        
        Used when all transitions are critical (low propensity).
        
        Args:
            controller: Simulation controller
            stochastic_transitions: List of stochastic transitions
        
        Returns:
            True if simulation continues
        """
        # Find enabled transitions
        enabled = []
        for transition in stochastic_transitions:
            behavior = self._get_behavior(transition)
            if behavior:
                can_fire, _ = behavior.can_fire()
                if can_fire:
                    enabled.append(transition)
        
        if not enabled:
            # No enabled transitions - advance time slightly
            controller.time += 0.001
            duration_s = controller.settings.get_duration_seconds()
            return duration_s is None or controller.time < duration_s
        
        # Select one transition (priority/random based on controller settings)
        transition = controller._select_transition(enabled)
        
        # Fire it using exact SSA
        controller._fire_transition(transition)
        
        duration_s = controller.settings.get_duration_seconds()
        return duration_s is None or controller.time < duration_s
    
    def _get_behavior(self, transition: Any) -> Optional[Any]:
        """Get behavior object for transition.

        Delegates to controller._get_behavior(transition) which keys the
        cache by id(transition) (Python object address), not transition.id
        (string '"T1"').  Using the string key was the original bug that
        caused all tau-leaping behavior lookups to return None.

        Args:
            transition: Transition object

        Returns:
            Behavior object or None
        """
        # Preferred: delegate to controller which manages the cache correctly.
        # Guard: only use the controller method when it is a real class-level
        # definition (not an auto-attribute generated by unittest.mock.Mock).
        ctrl = getattr(self, '_controller', None)
        if ctrl is not None and getattr(type(ctrl), '_get_behavior', None) is not None:
            return ctrl._get_behavior(transition)

        # Fallback: check if transition has behavior attribute (backward compatibility)
        if hasattr(transition, 'behavior'):
            return transition.behavior

    def get_statistics(self) -> Dict[str, Any]:
        """Get engine statistics.
        
        Returns:
            Dictionary with execution statistics
        """
        return {
            **self.stats,
            'epsilon': self.leap_selector.epsilon,
            'critical_threshold': self.leap_selector.critical_threshold
        }
    
    def reset_statistics(self) -> None:
        """Reset statistics counters."""
        self.stats = {
            'total_leaps': 0,
            'total_firings': 0,
            'mean_tau': 0.0,
            'exact_ssa_fallbacks': 0,
            'reversible_reactions': 0,
            'irreversible_reactions': 0
        }
    
    def _update_assignment_rules(self, controller: Any) -> None:
        """Update all assignment rule-defined species.
        
        Re-evaluates assignment rule formulas and updates place tokens.
        Called after each τ-leap to maintain algebraic constraints.
        
        Args:
            controller: Simulation controller with model and time
        """
        # Get any stochastic behavior (they all share the same assignment rules)
        stochastic_transitions = [
            t for t in controller.model.transitions
            if t.transition_type == 'stochastic'
        ]
        
        if not stochastic_transitions:
            return
        
        # Get behavior of first stochastic transition
        behavior = self._get_behavior(stochastic_transitions[0])
        if behavior is None or not hasattr(behavior, 'update_rule_defined_species'):
            return
        
        # Update all rule-defined species
        updated = behavior.update_rule_defined_species(controller.time)
        
        if updated > 0:
            self.logger.debug(
                f"Updated {updated} assignment rule-defined species at time {controller.time:.4f}"
            )
