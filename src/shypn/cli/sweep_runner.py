"""Headless sweep orchestrator.

Coordinates model loading, snapshot generation, condition dispatch
(via :class:`ReplicateRunner`), and structured output writing.

This module contains **no** GTK imports and can run on a headless server.
"""

from __future__ import annotations

import logging
import os
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

from shypn.cli.sweep_config import SweepConfig
from shypn.cli.sweep_output import SweepOutputManager
from shypn.ui.panels.viability.experiment_manager import ExperimentSnapshot
from shypn.ui.panels.viability.automation.property_path_parser import (
    apply_property_to_object,
    parse_property_path,
    resolve_object,
)

logger = logging.getLogger(__name__)


class SweepRunner:
    """Headless sweep orchestrator — no GUI dependencies.

    Usage::

        runner = SweepRunner(model_path, sweep_config, output_dir)
        runner.run()            # execute all conditions
        runner.dry_run()        # preview without executing
    """

    def __init__(
        self,
        model_path: Path,
        config: SweepConfig,
        output_dir: Path,
        workers: Optional[int] = None,
        verbose: bool = False,
    ) -> None:
        self.model_path = model_path
        self.config = config
        self.output_dir = output_dir
        self.workers = workers or max(1, (os.cpu_count() or 4) - 1)
        self.verbose = verbose

    # ── public API ───────────────────────────────────────────────────

    def dry_run(self) -> None:
        """Print what would be executed without running simulations."""
        model = self._load_model()
        baseline = self._capture_baseline(model)
        snapshots = self.config.generate_snapshots(baseline)
        sim = self.config.sim_params

        print(f"Model      : {self.model_path}")
        print(f"Places     : {len(model.places)}")
        print(f"Transitions: {len(model.transitions)}")
        print(f"Strategy   : {self.config.describe()}")
        print(f"Conditions : {len(snapshots)}")
        print(f"Replicates : {sim.replicates} per condition")
        print(f"Duration   : {sim.duration}s")
        print(f"Termination: {sim.termination}")
        print(f"Workers    : {self.workers}")
        total = len(snapshots) * sim.replicates
        print(f"Total sims : {total}")
        print()
        for i, snap in enumerate(snapshots):
            print(f"  [{i:3d}] {snap.name}")

    def run(self) -> Path:
        """Execute the full sweep and return the run directory path."""
        wall_start = time.monotonic()

        # 1. Load model
        model = self._load_model()
        if self.verbose:
            print(
                f"Model loaded: {len(model.places)} places, "
                f"{len(model.transitions)} transitions"
            )

        # 2. Generate conditions
        baseline = self._capture_baseline(model)
        snapshots = self.config.generate_snapshots(baseline)
        n_conditions = len(snapshots)
        sim = self.config.sim_params

        if self.verbose:
            print(f"Strategy: {self.config.describe()}")
            print(
                f"Running {n_conditions} conditions × "
                f"{sim.replicates} replicates = "
                f"{n_conditions * sim.replicates} total simulations"
            )

        # 3. Prepare output
        output = SweepOutputManager(self.output_dir)
        output.save_config(self.config.to_dict(), str(self.model_path))

        # 4. Import engine components (lazy — avoids importing at module level)
        from shypn.engine.simulation.replicate_runner import ReplicateRunner

        summary_rows: List[Dict[str, Any]] = []

        # 5. Iterate conditions
        for idx, snapshot in enumerate(snapshots):
            cond_start = time.monotonic()
            label = snapshot.name
            if self.verbose:
                print(
                    f"\n[{idx + 1}/{n_conditions}] {label} "
                    f"({sim.replicates} replicates)...",
                    flush=True,
                )

            # Apply snapshot overrides to model
            self._apply_snapshot(model, snapshot, baseline)

            # Run replicates
            runner = ReplicateRunner(model)
            results = runner.run_replicates(
                n=sim.replicates,
                use_parallel=True,
                use_tau_leaping=True,
                duration=sim.duration,
                termination_condition=sim.termination,
                epsilon=sim.tau_epsilon,
                max_tau=sim.max_tau,
                time_step=sim.time_step,
                seed_base=sim.seed_base,
                verbose=False,
            )

            # Compute statistics
            stats = runner.compute_statistics(results)

            # Persist
            output.save_condition(label, results, stats, model)

            cond_elapsed = time.monotonic() - cond_start
            n_ok = sum(1 for r in results if 'error' not in r)
            n_err = len(results) - n_ok

            summary_rows.append({
                'condition': label,
                'replicates_ok': n_ok,
                'replicates_error': n_err,
                'wall_seconds': round(cond_elapsed, 2),
            })

            if self.verbose:
                print(
                    f"  done in {cond_elapsed:.1f}s "
                    f"({n_ok} ok, {n_err} errors)"
                )

            # Restore baseline marking for next condition
            self._restore_baseline(model, baseline)

        # 6. Summary
        output.write_summary(summary_rows)
        wall_total = time.monotonic() - wall_start

        if self.verbose:
            print(f"\nSweep complete in {wall_total:.1f}s")
            print(f"Results: {output.run_dir}")

        return output.run_dir

    # ── private helpers ──────────────────────────────────────────────

    def _load_model(self) -> Any:
        """Load a .shy model file without any GTK dependency."""
        # Suppress GTK-related imports that DocumentModel might trigger
        os.environ.setdefault('DISPLAY', '')

        from shypn.data.canvas.document_model import DocumentModel

        return DocumentModel.load_from_file(str(self.model_path))

    @staticmethod
    def _capture_baseline(model: Any) -> ExperimentSnapshot:
        """Snapshot current model state as the baseline."""
        snap = ExperimentSnapshot('Baseline')
        snap.place_markings = {p.id: p.tokens for p in model.places}
        snap.transition_rates = {
            t.id: getattr(t, 'rate', 0.0) for t in model.transitions
        }
        snap.arc_weights = {
            a.id: getattr(a, 'weight', 1.0) for a in model.arcs
        }
        return snap

    @staticmethod
    def _apply_snapshot(
        model: Any,
        snapshot: ExperimentSnapshot,
        baseline: ExperimentSnapshot,
    ) -> None:
        """Apply a snapshot's overrides to the live model."""
        # First restore baseline so previous condition's overrides don't leak
        for p in model.places:
            p.tokens = baseline.place_markings.get(p.id, p.tokens)

        # Apply legacy dicts
        for p in model.places:
            if p.id in snapshot.place_markings:
                p.tokens = float(snapshot.place_markings[p.id])
        for t in model.transitions:
            if t.id in snapshot.transition_rates:
                rate = snapshot.transition_rates[t.id]
                if rate is None:
                    continue
                if isinstance(rate, str):
                    try:
                        t.rate = float(rate)
                    except ValueError:
                        t.rate = rate  # formula string
                else:
                    t.rate = float(rate)
        for a in model.arcs:
            if a.id in snapshot.arc_weights:
                a.weight = float(snapshot.arc_weights[a.id])

        # Apply property overrides (takes precedence)
        for prop_path, value in getattr(snapshot, 'property_overrides', {}).items():
            try:
                obj_id, prop_name = parse_property_path(prop_path)
                obj = resolve_object(model, obj_id)
                if obj is not None:
                    apply_property_to_object(obj, prop_name, value)
            except Exception as exc:
                logger.warning("Failed to apply %s=%s: %s", prop_path, value, exc)

    @staticmethod
    def _restore_baseline(model: Any, baseline: ExperimentSnapshot) -> None:
        """Reset model to baseline state."""
        for p in model.places:
            p.tokens = baseline.place_markings.get(p.id, p.tokens)
        for t in model.transitions:
            if t.id in baseline.transition_rates:
                t.rate = baseline.transition_rates[t.id]
