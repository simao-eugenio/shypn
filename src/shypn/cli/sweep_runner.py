"""Headless sweep orchestrator.

Coordinates model loading, snapshot generation, condition dispatch
(via :class:`ReplicateRunner`), and structured output writing.

This module contains **no** GTK imports and can run on a headless server.

Conditions are parallelised across worker processes when ``workers > 1``.
Each worker loads its own copy of the model (safe for fork/forkserver),
applies its snapshot overrides, and runs all replicates for that condition.
"""

from __future__ import annotations

import logging
import os
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
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

# Number of CPU threads to reserve for system/sshd (cores 0..N-1).
_RESERVED_CPUS = 4


def _apply_cpu_affinity() -> None:
    """Pin current process to CPUs beyond the reserved set.

    Reserves CPUs 0.._RESERVED_CPUS-1 for sshd and system tasks,
    preventing sweep workers from starving SSH and causing lockout.
    No-op on non-Linux or if os.sched_setaffinity is unavailable.
    """
    try:
        all_cpus = os.sched_getaffinity(0)
        allowed = {c for c in all_cpus if c >= _RESERVED_CPUS}
        if allowed:
            os.sched_setaffinity(0, allowed)
    except (AttributeError, OSError):
        # Not Linux or permission denied — silently skip
        pass


def _worker_init() -> None:
    """Initializer for ProcessPoolExecutor workers.

    Installs the process guard so worker processes also die cleanly
    when their parent is killed (e.g. SSH connection drop).
    Also marks the process so replicate_runner won't spawn a nested pool.
    Deprioritizes CPU scheduling so sshd/system stay responsive.
    Pins CPU affinity to avoid cores 0-3 (reserved for sshd/system).
    """
    os.environ['_SHYPN_IN_POOL_WORKER'] = '1'
    from shypn.engine.process_guard import install_process_guard
    install_process_guard()
    # Deprioritize worker so sshd (nice 0) stays responsive
    try:
        os.nice(19)
    except OSError:
        pass
    # Pin to cores 4+ so cores 0-3 remain free for sshd/system
    _apply_cpu_affinity()


class _GpuSampler:
    """Background ``nvidia-smi`` poller that records GPU utilisation.

    Spawns a single ``nvidia-smi --query-gpu=... -lms <period>`` process
    in the parent (one sampler shared across all workers, since they all
    share the same physical GPU).  When ``stop()`` is called, the
    subprocess is terminated, its stdout parsed, and aggregate stats
    (mean / peak SM utilisation, mean / peak VRAM in MiB, sample count)
    are returned as a dict.

    Returns ``{'available': False, ...}`` if ``nvidia-smi`` is missing
    or fails to start, so callers can always include the field
    unconditionally in their output.
    """

    @classmethod
    def start(cls, period_ms: int = 500) -> "_GpuSampler":
        self = cls()
        self.period_ms = period_ms
        self.proc = None
        self.t0 = time.monotonic()
        try:
            import subprocess
            # noheader,nounits => "<sm>, <mem_used>" per line
            self.proc = subprocess.Popen(
                [
                    "nvidia-smi",
                    "--query-gpu=utilization.gpu,memory.used",
                    "--format=csv,noheader,nounits",
                    f"-lms", str(period_ms),
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True,
                bufsize=1,
            )
        except (FileNotFoundError, OSError):
            self.proc = None
        return self

    def stop(self) -> dict:
        out = {
            "available": False,
            "period_ms": self.period_ms,
            "duration_seconds": round(time.monotonic() - self.t0, 2),
        }
        if self.proc is None:
            out["reason"] = "nvidia-smi unavailable"
            return out
        try:
            self.proc.terminate()
            stdout_text, _ = self.proc.communicate(timeout=2.0)
        except Exception:
            try:
                self.proc.kill()
                stdout_text, _ = self.proc.communicate(timeout=1.0)
            except Exception:
                stdout_text = ""
        sm_samples = []
        vram_samples = []
        for line in (stdout_text or "").splitlines():
            line = line.strip()
            if not line:
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 2:
                continue
            try:
                sm_samples.append(float(parts[0]))
                vram_samples.append(float(parts[1]))
            except ValueError:
                continue
        if not sm_samples:
            out["reason"] = "no samples collected"
            return out
        out.update(
            available=True,
            n_samples=len(sm_samples),
            avg_sm_pct=round(sum(sm_samples) / len(sm_samples), 1),
            max_sm_pct=round(max(sm_samples), 1),
            avg_vram_mib=round(sum(vram_samples) / len(vram_samples), 1),
            max_vram_mib=round(max(vram_samples), 1),
        )
        return out


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
        config_path: Optional[Path] = None,
    ) -> None:
        self.model_path = model_path
        self.config = config
        self.config_path = config_path
        self.output_dir = output_dir
        safe = self._compute_safe_workers()
        # User value acts as ceiling; never exceed memory-safe auto cap
        self.workers = min(workers, safe) if workers else safe
        self.verbose = verbose

    @staticmethod
    def _compute_safe_workers() -> int:
        """Compute max workers from CPU and memory constraints.

        Policy (recalibrated 2026-04-28 against measured RSS on remote-gpu
        — 16 workers running canabidiol-phase-1 averaged ~0.9 GB / 1.6 GB
        peak per worker, total 14 GB out of 49 GB available):
          - CPU: use *physical* cores minus a reserve of 4 threads for
            sshd / journald / system. Earlier 8-thread reserve was a
            workaround for SSH lockout that turned out to be a memory
            (swap-thrashing) problem, not a CPU-starvation problem.
          - Memory: estimate per-worker peak RSS at 1.5 GB (measured
            peak ~1.6 GB on the largest CBD-AD condition, with ~67%
            headroom). Cap to fit in available RAM minus a 12 GB
            system / page-cache / parent-process reserve.
            Swap is intentionally *not* counted — swap thrashing
            collapses throughput (~5× slowdown observed previously).
          - Final worker count = min(cpu_cap, mem_cap, hard_max=24)
        """
        # Detect physical cores (not logical threads)
        _logical = os.cpu_count() or 4
        try:
            with open('/proc/cpuinfo', 'r') as f:
                content = f.read()
            # "cpu cores" line gives physical cores per socket
            import re
            cores_per_socket = set(
                int(m.group(1))
                for m in re.finditer(r'^cpu cores\s*:\s*(\d+)', content, re.M)
            )
            sockets = len(set(
                m.group(1)
                for m in re.finditer(r'^physical id\s*:\s*(\d+)', content, re.M)
            )) or 1
            physical = max(cores_per_socket) * sockets if cores_per_socket else _logical
        except Exception:
            physical = _logical

        # Reserve 4 threads for sshd / system services. The earlier
        # 8-thread reserve was over-conservative — the real cause of
        # SSH lockout under load was memory-driven swap thrashing,
        # not CPU starvation.
        _reserved = 4
        cpu_cap = max(1, min(physical - _reserved, int(physical * 0.85)))

        # Memory-based cap
        try:
            # Use /proc/meminfo for available memory (more accurate than
            # psutil which may not be installed)
            mem_available_gb = None
            try:
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith('MemAvailable:'):
                            kb = int(line.split()[1])
                            mem_available_gb = kb / (1024 * 1024)
                            break
            except (OSError, ValueError):
                pass

            if mem_available_gb is None:
                # Fallback: total memory * 0.85 (assume 15% used by system)
                try:
                    with open('/proc/meminfo', 'r') as f:
                        for line in f:
                            if line.startswith('MemTotal:'):
                                kb = int(line.split()[1])
                                mem_available_gb = (kb / (1024 * 1024)) * 0.85
                                break
                except (OSError, ValueError):
                    pass

            if mem_available_gb is None:
                mem_available_gb = 16.0  # conservative default

            # Do NOT include swap in the worker cap calculation.
            # Swap should only be used as a safety buffer for transient
            # peaks, not as steady-state working memory.  Swap thrashing
            # kills throughput (observed: 9 GB/min swap growth with 16
            # workers on 62 GB RAM caused ~5× slowdown vs RAM-only).

            # Reserve 12 GB for OS, sshd, page cache, kernel buffers,
            # and the parent process (which holds model metadata + IPC).
            usable_gb = max(1.0, mem_available_gb - 12.0)
            # Per-worker peak RSS estimate, calibrated against measured
            # values on remote-gpu running canabidiol-phase-1 (32 cores,
            # 42 places, 45 transitions, 30 replicates × 4 h horizon):
            # observed peak 1.6 GB, mean 0.9 GB. 1.5 GB gives ~67%
            # headroom for Python heap fragmentation and larger models
            # while still allowing 24 workers on a 49 GB-available host.
            per_worker_gb = 1.5
            mem_cap = max(1, int(usable_gb / per_worker_gb))
        except Exception:
            mem_cap = cpu_cap  # If memory detection fails, trust CPU cap

        workers = min(cpu_cap, mem_cap, 24)
        return workers

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

        # 1. Load model (for metadata / dry-run info)
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
            print(f"Workers: {self.workers} (cpu_count={os.cpu_count()})")
            # Show memory info for diagnostics
            try:
                with open('/proc/meminfo', 'r') as f:
                    for line in f:
                        if line.startswith('MemAvailable:'):
                            avail_gb = int(line.split()[1]) / (1024 * 1024)
                            print(f"Memory available: {avail_gb:.1f} GB")
                            break
            except Exception:
                pass

        # 3. Prepare output
        output = SweepOutputManager(self.output_dir)
        output.save_config(self.config.to_dict(), str(self.model_path))

        # 3b. Snapshot the model + provenance into the run dir.
        # Hybrid sync (git + SCP): the canonical .shy may be edited or
        # overwritten between dispatches, so each run keeps its own
        # immutable copy. Combined with provenance.json (client/server
        # git SHAs + dirty flags + sha256), every run is independently
        # reconstructible.
        try:
            import shutil as _shutil
            model_src = Path(self.model_path)
            if model_src.is_file():
                _shutil.copy2(model_src,
                              output.run_dir / 'model_snapshot.shy')
                if self.verbose:
                    print(f"Snapshot: model_snapshot.shy "
                          f"({model_src.stat().st_size} bytes)")
        except OSError as _exc:
            print(f"WARNING: could not snapshot model: {_exc}")

        # Look for provenance.json next to the sweep config and copy
        # it into the run dir. Dispatcher writes it as a sibling of
        # sweep_config.json in the project folder.
        try:
            prov_candidates = []
            if self.config_path is not None:
                prov_candidates.append(Path(self.config_path).parent
                                       / 'provenance.json')
            for prov in prov_candidates:
                if prov.is_file():
                    import shutil as _shutil2
                    _shutil2.copy2(prov, output.run_dir / 'provenance.json')
                    if self.verbose:
                        print(f"Snapshot: provenance.json from {prov}")
                    break
        except OSError as _exc:
            print(f"WARNING: could not snapshot provenance: {_exc}")

        # 4. Dispatch conditions in bounded batches across worker processes.
        #    Each worker loads its own model copy — no shared mutable state.
        #    Workers write results directly to disk and return only a light
        #    summary payload, preventing IPC memory pressure from full
        #    trajectory data being pickled back to the parent.
        #
        #    Sliding-window dispatch: at most `n_workers` conditions are
        #    in-flight simultaneously.  As each finishes, the next is
        #    submitted immediately — no straggler idle time.  Workers
        #    flush results to disk before returning, so parent memory
        #    stays bounded.
        _apply_cpu_affinity()
        import gc
        from dataclasses import asdict
        sim_dict = asdict(sim)

        summary_rows: List[Optional[Dict[str, Any]]] = [None] * n_conditions
        n_workers = min(self.workers, n_conditions)

        # Adaptive replicate distribution: when there are fewer conditions
        # than total workers, spread the leftover budget across replicates
        # *within* each condition.  This eliminates the slow gating-run
        # case (1 condition × N replicates pinning only 1 outer worker).
        # Multi-condition sweeps where n_conditions >= self.workers keep
        # replicate_pool_size == 1 — unchanged behaviour.
        replicate_pool_size = max(1, self.workers // max(1, n_workers))
        if self.verbose and replicate_pool_size > 1:
            print(
                f"[adaptive] {n_conditions} condition(s) × {sim.replicates} reps → "
                f"{n_workers} cond-worker(s) × {replicate_pool_size} rep-worker(s) "
                f"per condition (total = {n_workers * replicate_pool_size}/{self.workers})"
            )

        # 4a. Optional GPU sampler (nvidia-smi). No-op if unavailable.
        gpu_sampler = _GpuSampler.start(period_ms=500)

        with ProcessPoolExecutor(
            max_workers=n_workers,
            initializer=_worker_init,
        ) as pool:
            # Sliding window: submit up to n_workers, then for each
            # completion, submit the next pending condition.
            futures_map: Dict[Any, int] = {}
            next_idx = 0  # index of the next condition to submit

            def _submit_one(idx: int) -> None:
                snapshot = snapshots[idx]
                if self.verbose:
                    print(
                        f"[{idx + 1}/{n_conditions}] {snapshot.name} "
                        f"({sim.replicates} replicates)...",
                        flush=True,
                    )
                fut = pool.submit(
                    _run_single_condition,
                    model_path=str(self.model_path),
                    baseline_dict=_snapshot_to_dict(baseline),
                    snapshot_dict=_snapshot_to_dict(snapshot),
                    sim_params=sim_dict,
                    condition_index=idx,
                    n_conditions=n_conditions,
                    output_dir=str(output.run_dir),
                    verbose=self.verbose,
                    events=list(getattr(self.config, 'events', []) or []),
                    output_options=self.config.output.to_dict(),
                    replicate_pool_size=replicate_pool_size,
                )
                futures_map[fut] = idx

            # Fill the initial window
            while next_idx < min(n_workers, n_conditions):
                _submit_one(next_idx)
                next_idx += 1

            # Process completions and refill the window
            while futures_map:
                # Wait for the next completion
                done_iter = as_completed(futures_map)
                fut = next(done_iter)
                idx = futures_map.pop(fut)
                label = snapshots[idx].name

                try:
                    result_payload = fut.result()
                    cond_elapsed = result_payload['wall_seconds']
                    n_ok = result_payload['replicates_ok']
                    n_err = result_payload['replicates_error']
                    cpu_s = result_payload.get('cpu_seconds', 0.0)
                    peak_mib = result_payload.get('peak_rss_mib', 0.0)

                    summary_rows[idx] = {
                        'condition': label,
                        'replicates_ok': n_ok,
                        'replicates_error': n_err,
                        'wall_seconds': round(cond_elapsed, 2),
                        'cpu_seconds': round(cpu_s, 2),
                        'peak_rss_mib': round(peak_mib, 1),
                    }

                    if self.verbose:
                        cpu_pct = (cpu_s / cond_elapsed * 100.0) if cond_elapsed > 0 else 0.0
                        print(
                            f"  done in {cond_elapsed:.1f}s "
                            f"({n_ok} ok, {n_err} errors) "
                            f"[cpu={cpu_s:.0f}s {cpu_pct:.0f}%, rss={peak_mib:.0f} MiB]",
                            flush=True,
                        )
                except Exception as exc:
                    logger.exception("Condition %d (%s) failed", idx, label)
                    summary_rows[idx] = {
                        'condition': label,
                        'replicates_ok': 0,
                        'replicates_error': sim.replicates,
                        'wall_seconds': 0.0,
                        'cpu_seconds': 0.0,
                        'peak_rss_mib': 0.0,
                    }
                    if self.verbose:
                        print(
                            f"  done in 0.0s (0 ok, {sim.replicates} errors) — {exc}",
                            flush=True,
                        )

                # Submit next condition if any remain
                if next_idx < n_conditions:
                    _submit_one(next_idx)
                    next_idx += 1

                # Incremental GC: reclaim IPC deserialization overhead
                gc.collect()

        # 5. Summary
        output.write_summary([r for r in summary_rows if r is not None])
        wall_total = time.monotonic() - wall_start

        # 5a. Stop GPU sampler and collect stats (None if unavailable)
        gpu_stats = gpu_sampler.stop()

        # 5b. Resource usage report (parent + per-condition aggregates)
        try:
            import json as _json
            import resource as _resource
            _ru_self = _resource.getrusage(_resource.RUSAGE_SELF)
            _ru_chld = _resource.getrusage(_resource.RUSAGE_CHILDREN)
            rows = [r for r in summary_rows if r is not None]
            total_cpu = sum(r.get('cpu_seconds', 0.0) for r in rows)
            peak_worker_rss = max(
                (r.get('peak_rss_mib', 0.0) for r in rows), default=0.0
            )
            cpu_efficiency = (
                (total_cpu / (wall_total * n_workers) * 100.0)
                if wall_total > 0 and n_workers > 0 else 0.0
            )
            usage = {
                'wall_seconds': round(wall_total, 2),
                'workers': n_workers,
                'n_conditions': n_conditions,
                'parent_peak_rss_mib': round(_ru_self.ru_maxrss / 1024.0, 1),
                'children_peak_rss_mib': round(_ru_chld.ru_maxrss / 1024.0, 1),
                'children_cpu_user_seconds': round(_ru_chld.ru_utime, 2),
                'children_cpu_sys_seconds': round(_ru_chld.ru_stime, 2),
                'sum_condition_cpu_seconds': round(total_cpu, 2),
                'max_condition_peak_rss_mib': round(peak_worker_rss, 1),
                'cpu_efficiency_percent': round(cpu_efficiency, 1),
                'gpu': gpu_stats,
                'per_condition': rows,
            }
            with open(output.run_dir / 'resource_usage.json', 'w') as f:
                _json.dump(usage, f, indent=2)
            if self.verbose:
                print(
                    f"Resource: cpu_eff={cpu_efficiency:.0f}% "
                    f"(sum_cpu={total_cpu:.0f}s / {wall_total:.0f}s × {n_workers} workers), "
                    f"max worker RSS={peak_worker_rss:.0f} MiB, "
                    f"parent RSS={_ru_self.ru_maxrss / 1024.0:.0f} MiB"
                )
                if gpu_stats and gpu_stats.get('available'):
                    print(
                        f"GPU: avg_sm={gpu_stats['avg_sm_pct']:.0f}% "
                        f"max_sm={gpu_stats['max_sm_pct']:.0f}% "
                        f"avg_vram={gpu_stats['avg_vram_mib']:.0f} MiB "
                        f"max_vram={gpu_stats['max_vram_mib']:.0f} MiB "
                        f"({gpu_stats['n_samples']} samples "
                        f"every {gpu_stats['period_ms']} ms)"
                    )
        except Exception as _exc:
            logger.warning("Failed to write resource_usage.json: %s", _exc)

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

        # Sync cached initial-state attributes so that _reset_model() and
        # SimulationController.reset() use the overridden values instead of
        # stale ones from a previous condition.
        for p in model.places:
            if hasattr(p, 'initial_tokens'):
                p.initial_tokens = p.tokens
            if hasattr(p, 'initial_marking'):
                p.initial_marking = p.tokens

    @staticmethod
    def _restore_baseline(model: Any, baseline: ExperimentSnapshot) -> None:
        """Reset model to baseline state."""
        for p in model.places:
            p.tokens = baseline.place_markings.get(p.id, p.tokens)
        for t in model.transitions:
            if t.id in baseline.transition_rates:
                t.rate = baseline.transition_rates[t.id]


# ═════════════════════════════════════════════════════════════════════
# Module-level helpers for parallel condition dispatch
# (must be picklable — cannot be methods or closures)
# ═════════════════════════════════════════════════════════════════════

def _snapshot_to_dict(snap: ExperimentSnapshot) -> dict:
    """Serialise an ExperimentSnapshot to a plain dict for pickling."""
    return {
        'name': snap.name,
        'place_markings': dict(snap.place_markings),
        'transition_rates': dict(snap.transition_rates),
        'arc_weights': dict(snap.arc_weights),
        'property_overrides': dict(getattr(snap, 'property_overrides', {})),
    }


def _dict_to_snapshot(d: dict) -> ExperimentSnapshot:
    """Reconstruct an ExperimentSnapshot from a plain dict."""
    snap = ExperimentSnapshot(d['name'])
    snap.place_markings = d['place_markings']
    snap.transition_rates = d['transition_rates']
    snap.arc_weights = d['arc_weights']
    snap.property_overrides = d.get('property_overrides', {})
    return snap


def _sanitise_condition_name(name: str) -> str:
    """Filesystem-safe condition name (mirrors sweep_output._sanitise)."""
    return (
        name.replace(' ', '_')
            .replace('/', '_')
            .replace('\\', '_')
            .replace(':', '_')
            .replace(',', '_')
            .replace(';', '_')
            .replace('=', '_eq_')
    )[:120]


def _strip_to_endpoint(stats: dict) -> dict:
    """Reduce per-step statistics to endpoint-only (G2 tier).

    Keeps only the last time-point of each trajectory array. Cuts
    statistics.json size by O(n_time_points) — typically ~1000×.
    """
    if not isinstance(stats, dict):
        return stats
    out: dict = {}
    for k, v in stats.items():
        if k == 'time_points' and isinstance(v, list) and v:
            out[k] = [v[-1]]
        elif k == 'species_statistics' and isinstance(v, dict):
            new_species = {}
            for sid, sdict in v.items():
                if not isinstance(sdict, dict):
                    new_species[sid] = sdict
                    continue
                slim = {}
                for field_name, arr in sdict.items():
                    if field_name == 'percentiles' and isinstance(arr, dict):
                        slim[field_name] = {
                            p: ([pa[-1]] if isinstance(pa, list) and pa else pa)
                            for p, pa in arr.items()
                        }
                    elif isinstance(arr, list) and arr:
                        slim[field_name] = [arr[-1]]
                    else:
                        slim[field_name] = arr
                new_species[sid] = slim
            out[k] = new_species
        else:
            out[k] = v
    return out


def _run_single_condition(
    *,
    model_path: str,
    baseline_dict: dict,
    snapshot_dict: dict,
    sim_params: dict,
    condition_index: int,
    n_conditions: int,
    output_dir: str,
    verbose: bool,
    events: list = None,
    output_options: dict = None,
    replicate_pool_size: int = 1,
) -> dict:
    """Execute one condition in a worker process.

    Loads its own model copy, applies overrides, runs all replicates,
    writes results directly to disk (avoiding IPC transfer of full
    trajectory data), and returns only a lightweight summary dict.

    Memory management: results are deleted and GC'd immediately after
    disk flush, so peak RSS = 1 condition's trajectory data only.
    """
    import gc
    import time as _time
    import resource as _resource
    cond_start = _time.monotonic()
    cpu_start = _time.process_time()

    # Suppress ODE acceleration noise in worker
    import logging as _logging
    _logging.basicConfig(level=_logging.WARNING)
    for _name in ('shypn.engine.simulation.controller',):
        _logging.getLogger(_name).setLevel(_logging.ERROR)

    # Load a fresh model in this process
    os.environ.setdefault('DISPLAY', '')
    from shypn.data.canvas.document_model import DocumentModel
    model = DocumentModel.load_from_file(model_path)

    baseline = _dict_to_snapshot(baseline_dict)
    snapshot = _dict_to_snapshot(snapshot_dict)

    # Apply overrides
    SweepRunner._apply_snapshot(model, snapshot, baseline)

    # Install environment events forwarded from the dispatching client.
    # These are defined on the GUI Environment Panel and travel inside
    # the sweep config JSON (top-level 'events' field).  The engine's
    # _evaluate_environment_events picks them up from model.events.
    if events:
        from shypn.data.pathway.pathway_data import Event as _Event
        import logging as _lg
        _log = _lg.getLogger(__name__)
        try:
            model.events = [_Event.from_dict(e) for e in events]
            if condition_index == 0:
                # Audit log only — NOT printed to stdout, otherwise this
                # would freeze the GUI status label on the SSH stream
                # for the duration of the worker's first simulation.
                _log.info(
                    "[EVENT_DISPATCH] worker installed %d event(s) on model: %s",
                    len(model.events),
                    [e.id + '@' + e.trigger for e in model.events],
                )
        except Exception as _exc:
            _log.warning(
                "Failed to install %d dispatched events: %s", len(events), _exc
            )

    # Run replicates
    # Override the pool-worker gate to grant this worker an explicit inner
    # replicate-pool budget. _worker_init() set this to '1' (sequential),
    # which is the right default; here we widen it only when the dispatcher
    # has computed leftover capacity (replicate_pool_size > 1).
    if replicate_pool_size and replicate_pool_size > 1:
        os.environ['_SHYPN_IN_POOL_WORKER'] = str(int(replicate_pool_size))
    from shypn.engine.simulation.replicate_runner import ReplicateRunner
    runner = ReplicateRunner(model)
    results = runner.run_replicates(
        n=sim_params['replicates'],
        use_parallel=True,
        use_tau_leaping=True,
        duration=sim_params['duration'],
        termination_condition=sim_params['termination'],
        epsilon=sim_params['tau_epsilon'],
        max_tau=sim_params['max_tau'],
        time_step=sim_params.get('time_step'),
        seed_base=sim_params['seed_base'],
        verbose=False,
    )

    stats = runner.compute_statistics(results)

    cond_elapsed = _time.monotonic() - cond_start
    n_ok = sum(1 for r in results if 'error' not in r)
    n_err = len(results) - n_ok

    # ── Worker-side disk flush ───────────────────────────────────────
    # Write results directly to disk in the worker process, then delete
    # the large trajectory data.  This prevents full result payloads
    # from being pickled back to the parent process via IPC, which was
    # the primary cause of memory exhaustion during large sweeps.
    from shypn.cli.sweep_output import SweepOutputManager
    from pathlib import Path

    run_dir = Path(output_dir)
    safe_name = _sanitise_condition_name(snapshot.name)
    cond_dir = run_dir / f"condition_{safe_name}"
    cond_dir.mkdir(parents=True, exist_ok=True)

    # Output-tier gate: see OutputOptions in sweep_config.py for tier→writes.
    from shypn.cli.sweep_config import OutputOptions as _OutputOptions
    _opts = _OutputOptions.from_dict(output_options)
    if _opts.write_replicates_csv:
        SweepOutputManager._write_replicates_csv(cond_dir, results, model)
    if _opts.write_statistics_json:
        if _opts.statistics_endpoint_only:
            stats_to_write = _strip_to_endpoint(stats)
        else:
            stats_to_write = stats
        SweepOutputManager._write_statistics_json(cond_dir, stats_to_write)

    # Free trajectory data immediately — this is the critical memory
    # reclamation point.  Without this, the worker holds ~0.5–1.5 GB
    # of trajectory arrays until the function returns.
    del results, stats, runner, model
    gc.collect()
    # ─────────────────────────────────────────────────────────────────

    # Resource usage — peak RSS in MiB, CPU seconds (user + sys for self
    # and any reaped child threads).  ru_maxrss is in KiB on Linux.
    _ru_self = _resource.getrusage(_resource.RUSAGE_SELF)
    cpu_elapsed = _time.process_time() - cpu_start
    peak_rss_mib = _ru_self.ru_maxrss / 1024.0  # KiB → MiB on Linux

    # Return only the lightweight summary — no trajectory data crosses IPC.
    return {
        'wall_seconds': cond_elapsed,
        'cpu_seconds': cpu_elapsed,
        'peak_rss_mib': peak_rss_mib,
        'replicates_ok': n_ok,
        'replicates_error': n_err,
    }
