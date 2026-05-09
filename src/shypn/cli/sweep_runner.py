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
        use_gpu: str = 'auto',
    ) -> None:
        self.model_path = model_path
        self.config = config
        self.config_path = config_path
        self.output_dir = output_dir
        # Pass duration to the worker-cap heuristic so long horizons get
        # a more conservative per-worker memory budget.
        _duration_s = float(getattr(self.config.sim_params, 'duration', 0.0) or 0.0)
        safe = self._compute_safe_workers(duration_seconds=_duration_s)
        # User value acts as ceiling; never exceed memory-safe auto cap
        self.workers = min(workers, safe) if workers else safe
        self.verbose = verbose
        if use_gpu not in ('auto', 'force', 'off'):
            raise ValueError(f"use_gpu must be 'auto'|'force'|'off'; got {use_gpu!r}")
        self._gpu_mode = use_gpu

    @staticmethod
    def _compute_safe_workers(duration_seconds: float = 0.0) -> int:
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
          - Final worker count = min(cpu_cap, mem_cap, hard_max)

        Bug-fix 2026-05-05: ``duration_seconds`` is now consulted.  A
        7-day × 60-rep × 10-cond sweep (run_20260505_014609) silently
        OOM-thrashed on remote-gpu at the previous flat 1.5 GB / worker
        estimate (real per-worker peak ≈ 10 GB pre-decimation).  Even
        with the data-collector decimation now in place (replicate_runner
        ~5 000 records / replicate), long horizons still grow C-side
        propensity-accelerator state and intermediate Python objects,
        so we apply a duration-tier multiplier to ``per_worker_gb`` and
        a tighter ``hard_max``.
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
            # Duration-tier multiplier (2026-05-05): long horizons grow
            # propensity-accelerator C state and intermediate float
            # arrays even after data-collector decimation.
            #     ≤  4 h  → 1.0×  (calibration regime)
            #     ≤ 24 h  → 1.5×
            #     ≤ 72 h  → 2.0×
            #     >  72 h → 3.0×
            _h = (duration_seconds or 0.0) / 3600.0
            if _h > 72.0:
                per_worker_gb *= 3.0
            elif _h > 24.0:
                per_worker_gb *= 2.0
            elif _h > 4.0:
                per_worker_gb *= 1.5
            mem_cap = max(1, int(usable_gb / per_worker_gb))
        except Exception:
            mem_cap = cpu_cap  # If memory detection fails, trust CPU cap

        # Hard ceiling: 24 workers on short runs, 12 on long-horizon runs
        # (limit IPC pickling + GC contention from the parent process).
        _hard_max = 12 if (duration_seconds or 0.0) > 24 * 3600 else 24
        workers = min(cpu_cap, mem_cap, _hard_max)
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
            # GPU policy summary so operators see the effective decision
            # basis up-front (no need to grep for late warnings).
            # NOTE: the dispatcher will route via 'condition-batch' (one
            # work unit = R reps) when the condition-mode rule fires,
            # so reps are batched on the GPU rather than shredded across
            # CPU workers.
            _gpu_hint: str
            _will_batch = (
                self._gpu_mode == 'force'
                or (self._gpu_mode == 'auto'
                    and self.workers <= n_conditions)
            )
            if self._gpu_mode == 'off':
                _gpu_hint = "disabled (--use-gpu off) → flat-dispatch"
            elif self._gpu_mode == 'force':
                _gpu_hint = (
                    "forced (--use-gpu force) → condition-batch "
                    "(R reps per work unit)"
                )
            else:
                if _will_batch:
                    _gpu_hint = (
                        f"auto → condition-batch "
                        f"(workers={self.workers} ≤ conditions={n_conditions}; "
                        f"R={sim.replicates} reps batched on GPU)"
                    )
                else:
                    _gpu_hint = (
                        f"auto → flat-dispatch "
                        f"(workers={self.workers} > conditions={n_conditions}; "
                        f"CPU parallelism wins)"
                    )
            print(f"GPU policy: {_gpu_hint}")
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

        # 4. Flat replicate dispatch (Strategy A — May 2026).
        #
        #    A single ProcessPool of `self.workers` processes consumes a
        #    flat queue of (condition, replicate) work units. Each worker
        #    loads the baseline model exactly once via the pool
        #    initialiser; per-work-unit cost is from_dict(baseline) +
        #    apply_snapshot + run one replicate.
        #
        #    Why: under the legacy outer/inner two-tier design, an outer
        #    pool of `min(workers, n_conditions)` was the bottleneck
        #    when workers > n_conditions (e.g. 26 workers / 8 conditions
        #    pinned to 8 outer slots, each running 30 reps sequentially
        #    in a single subprocess). Flat dispatch saturates all cores
        #    for any C × R ≥ workers and removes the brittle nested-pool
        #    plumbing entirely.
        #
        #    Memory bound (main process buffer): up to C × R full
        #    per-replicate trajectory dicts during the worst case — but
        #    a condition is finalised the moment its R-th replicate
        #    arrives, so its buffer is freed promptly. Round-robin
        #    submission (r=0 across all C, then r=1, ...) keeps
        #    conditions advancing together so they finalise in clusters
        #    near the end of the sweep.
        _apply_cpu_affinity()
        import gc
        import time as _time_mod
        from collections import defaultdict
        from dataclasses import asdict
        sim_dict = asdict(sim)
        events_list = list(getattr(self.config, 'events', []) or [])
        # SimulationParams has no time_units field — sweeps assume seconds
        # (matches ReplicateRunner.run_replicates' default). The enum
        # value is a tuple ('seconds', 's', 1.0); pass it verbatim so the
        # worker can rehydrate via TimeUnits(value).
        from shypn.utils.time_utils import TimeUnits as _TU
        time_units_value = _TU.SECONDS.value

        summary_rows: List[Optional[Dict[str, Any]]] = [None] * n_conditions
        # Layer D: aggregate per-condition parameter_sources for provenance.
        sources_by_condition: Dict[str, Dict[str, Any]] = {}
        # TMD-1: aggregate per-condition timescale_audit profile for provenance
        # + summary.csv. Profile is identical across replicates of one
        # condition (deterministic on M₀); we capture the first non-empty.
        timescale_by_condition: Dict[str, Dict[str, Any]] = {}
        # Per-condition main-process buffer of replicate result dicts.
        results_by_cond: Dict[int, List[dict]] = defaultdict(list)
        # Per-condition wall-clock window (start = first rep submitted,
        # end = R-th rep arrived).
        cond_t0: Dict[int, float] = {}
        # Pre-serialise snapshots once.
        snapshot_dicts = [_snapshot_to_dict(s) for s in snapshots]
        # ── Dispatch-mode selection ──────────────────────────────────
        # 'flat'      → R reps shred into R work units; saturates many
        #               CPU cores; bypasses GPU.
        # 'condition' → all R reps batched per condition into one work
        #               unit; routes through ReplicateRunner.run_replicates
        #               which can dispatch the whole batch to GPU.
        #
        # Selection rule (2026-05-09):
        #   gpu_mode == 'off' or 'auto' with workers > n_conditions
        #     → flat (CPU parallelism dominates)
        #   gpu_mode == 'force' or 'auto' with workers ≤ n_conditions
        #     → condition (GPU batching pays off; no parallelism lost)
        if self._gpu_mode == 'off':
            _dispatch_mode = 'flat'
        elif self._gpu_mode == 'force':
            _dispatch_mode = 'condition'
        else:  # 'auto'
            _dispatch_mode = (
                'condition' if self.workers <= n_conditions else 'flat'
            )

        if _dispatch_mode == 'condition':
            n_workers = min(self.workers, n_conditions)
            n_units = n_conditions
            _unit_label = "condition-batch"
        else:
            n_workers = min(self.workers, n_conditions * sim.replicates)
            n_units = n_conditions * sim.replicates
            _unit_label = "flat-dispatch"
        if self.verbose:
            print(
                f"[{_unit_label}] {n_conditions} cond × {sim.replicates} reps "
                f"= {n_units} work units, pool={n_workers}"
            )

        # 4a. Optional GPU sampler (nvidia-smi). No-op if unavailable.
        gpu_sampler = _GpuSampler.start(period_ms=500)

        with ProcessPoolExecutor(
            max_workers=n_workers,
            initializer=_replicate_pool_init,
            initargs=(str(self.model_path), int(n_workers), self._gpu_mode),
        ) as pool:
            futures_map: Dict[Any, tuple] = {}

            if _dispatch_mode == 'condition':
                # One work unit per condition: all R reps batched.
                for c in range(n_conditions):
                    cond_t0[c] = _time_mod.monotonic()
                    if self.verbose:
                        print(
                            f"[{c + 1}/{n_conditions}] {snapshots[c].name} "
                            f"({sim.replicates} replicates, batched)...",
                            flush=True,
                        )
                    fut = pool.submit(
                        _run_one_condition_batch,
                        cond_idx=c,
                        cond_name=snapshots[c].name,
                        baseline_dict_inline=None,
                        snapshot_dict=snapshot_dicts[c],
                        sim_params=sim_dict,
                        events=events_list,
                        time_units_value=time_units_value,
                    )
                    futures_map[fut] = (c, -1)  # rep=-1 sentinel for batch
            else:
                # Submit all (cond, rep) work units in round-robin order so
                # every condition has reps in flight from t=0. Pool queues
                # the surplus internally; only n_workers run concurrently.
                for r in range(sim.replicates):
                    for c in range(n_conditions):
                        if r == 0:
                            cond_t0[c] = _time_mod.monotonic()
                            if self.verbose:
                                print(
                                    f"[{c + 1}/{n_conditions}] "
                                    f"{snapshots[c].name} "
                                    f"({sim.replicates} replicates)...",
                                    flush=True,
                                )
                        fut = pool.submit(
                            _run_one_replicate,
                            cond_idx=c,
                            rep_idx=r,
                            cond_name=snapshots[c].name,
                            baseline_dict_inline=None,
                            snapshot_dict=snapshot_dicts[c],
                            sim_params=sim_dict,
                            events=events_list,
                            time_units_value=time_units_value,
                        )
                        futures_map[fut] = (c, r)

            # Process replicate completions; finalise each condition
            # the moment its R-th replicate arrives.
            for fut in as_completed(futures_map):
                c, r = futures_map.pop(fut)
                label = snapshots[c].name
                try:
                    payload = fut.result()
                    if 'results' in payload:
                        # Condition-batch payload: R results in one shot.
                        for _res in payload['results']:
                            results_by_cond[c].append(_res)
                    else:
                        # Flat-dispatch payload: one result.
                        results_by_cond[c].append(payload['result'])
                    if 'param_sources' in payload:
                        sources_by_condition[label] = payload['param_sources']
                    # TMD-1: capture timescale_audit (first replicate carries it).
                    if label not in timescale_by_condition:
                        # Look in either shape (flat: 'result'; batch: 'results'[0]).
                        _probe = payload.get('result') or (
                            payload.get('results', [None])[0]
                        )
                        if _probe:
                            _tmd = (_probe.get('engine_stats', {})
                                    .get('timescale_audit'))
                            if _tmd:
                                timescale_by_condition[label] = _tmd
                except Exception as exc:
                    logger.exception(
                        "Condition %d (%s) replicate %d failed",
                        c, label, r,
                    )
                    # Inject synthetic error result(s) so the condition
                    # still finalises with the right replicate count.
                    # In condition-batch mode (r=-1) the entire batch
                    # failed → backfill all R reps as errors.
                    if r < 0:
                        for _r in range(sim.replicates):
                            results_by_cond[c].append({
                                'replicate_id': _r,
                                'seed': sim_dict['seed_base'] + _r,
                                'elapsed_time': 0.0,
                                'error': str(exc),
                            })
                    else:
                        results_by_cond[c].append({
                            'replicate_id': r,
                            'seed': sim_dict['seed_base'] + r,
                            'elapsed_time': 0.0,
                            'error': str(exc),
                        })

                # Has this condition completed?
                if len(results_by_cond[c]) < sim.replicates:
                    continue

                cond_results = results_by_cond.pop(c)
                n_ok = sum(1 for x in cond_results if 'error' not in x)
                n_err = len(cond_results) - n_ok
                cond_wall = _time_mod.monotonic() - cond_t0.get(c, _time_mod.monotonic())
                # Sum of per-replicate elapsed times approximates per-condition
                # CPU; not strictly process_time but a useful aggregate.
                cond_cpu = sum(float(x.get('elapsed_time', 0.0))
                               for x in cond_results)

                # Finalise: compute statistics + write per-condition outputs.
                # We need a model instance for compute_statistics + writers;
                # load lazily and reuse across remaining finalisations.
                if not hasattr(self, '_finalise_model'):
                    from shypn.data.canvas.document_model import DocumentModel
                    self._finalise_model = DocumentModel.load_from_file(
                        str(self.model_path))
                _finalize_condition(
                    model=self._finalise_model,
                    snapshot=snapshots[c],
                    cond_results=cond_results,
                    output_run_dir=output.run_dir,
                    output_options=self.config.output.to_dict(),
                )

                # Persist parameter_sources alongside statistics.
                try:
                    import json as _json_ps
                    safe_name = _sanitise_condition_name(label)
                    cond_dir = output.run_dir / f"condition_{safe_name}"
                    with open(cond_dir / 'parameter_sources.json', 'w') as _psf:
                        _json_ps.dump({
                            'condition': label,
                            'sources': sources_by_condition.get(label, {}),
                        }, _psf, indent=2, sort_keys=True)
                except OSError as _exc:
                    logger.warning(
                        "Failed to write parameter_sources.json for %s: %s",
                        label, _exc,
                    )

                summary_rows[c] = {
                    'condition': label,
                    'replicates_ok': n_ok,
                    'replicates_error': n_err,
                    'wall_seconds': round(cond_wall, 2),
                    'cpu_seconds': round(cond_cpu, 2),
                    # peak_rss is a per-process metric; the flat pool
                    # makes it ill-defined per-condition. Report 0.0 here
                    # and rely on resource_usage.json's children_peak_rss
                    # for the true aggregate.
                    'peak_rss_mib': 0.0,
                    # TMD-1 surface (always present; zero/empty when audit
                    # disabled or no continuous transitions).
                    'tmd_critical_count': len(
                        (timescale_by_condition.get(label) or {}).get(
                            'critical_transitions', []
                        )
                    ),
                    'tmd_stiffness_ratio': float(
                        (timescale_by_condition.get(label) or {}).get(
                            'stiffness_ratio', 0.0
                        ) or 0.0
                    ),
                    'tmd_recommended_dt': (
                        (timescale_by_condition.get(label) or {}).get(
                            'recommended_dt'
                        )
                    ),
                }

                if self.verbose:
                    cpu_pct = (cond_cpu / cond_wall * 100.0) if cond_wall > 0 else 0.0
                    print(
                        f"[done {c + 1}/{n_conditions}] {label} "
                        f"in {cond_wall:.1f}s "
                        f"({n_ok} ok, {n_err} errors) "
                        f"[cpu={cond_cpu:.0f}s {cpu_pct:.0f}%]",
                        flush=True,
                    )

                del cond_results
                gc.collect()

        # Drop the lazy finalisation model
        if hasattr(self, '_finalise_model'):
            del self._finalise_model
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

        # ── Layer D: parameter_sources audit ─────────────────────────
        # Persist per-condition source map so analysts (and the
        # 'reload-and-rerun' path) can confirm at a glance which knobs
        # actually moved away from the model defaults. Augments
        # provenance.json if it was uploaded; otherwise written
        # standalone next to it. Keys in the per-condition dict are
        # full property paths (e.g. "P38.initial_marking"); each value
        # is {source: 'sweep'|'fixed_override'|'event'|'snapshot',
        #     value: applied, prior: model-default}.
        try:
            import json as _json_ps2
            prov_file = output.run_dir / 'provenance.json'
            if prov_file.is_file():
                with open(prov_file, 'r') as _pf:
                    prov_doc = _json_ps2.load(_pf)
            else:
                prov_doc = {}
            prov_doc['parameter_sources'] = sources_by_condition
            # TMD-1: persist per-condition timescale audit profiles so the
            # 'reload-and-rerun' / analyst path can detect dt vs τ mismatches
            # without re-running anything. Empty dict means audit disabled
            # or no continuous transitions in the model.
            prov_doc['timescale_audit'] = timescale_by_condition
            with open(prov_file, 'w') as _pf:
                _json_ps2.dump(prov_doc, _pf, indent=2, sort_keys=True)
            if self.verbose:
                n_overrides = sum(len(v) for v in sources_by_condition.values())
                print(
                    f"Provenance: parameter_sources written "
                    f"({len(sources_by_condition)} conditions, "
                    f"{n_overrides} overrides total)"
                )
        except Exception as _exc:
            logger.warning("Failed to augment provenance.json: %s", _exc)

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
    ) -> Dict[str, Any]:
        """Apply a snapshot's overrides to the live model.

        Returns:
            ``parameter_sources``: dict mapping each property path that
            differs from the model default to the metadata needed for
            provenance — origin tag (``'sweep'`` / ``'fixed_override'`` /
            ``'snapshot'`` / ``'event'``), the applied value, and the
            prior model value.  Written into ``provenance.json`` alongside
            ``model_sha256`` so every run can be audited for which knobs
            actually moved.  See instructions §"Sweep \u2194 model
            superposition rule" (Layer D of the 2026-04-30 sweep-pipeline
            audit).
        """
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

        # ── Apply property_overrides (highest precedence) ─────────────
        # Tracks each applied override so the worker can write
        # parameter_sources into provenance.json.  An override is tagged
        # 'sweep' if its path matches snapshot.swept_parameter, otherwise
        # 'fixed_override' for sweep-wide constants or 'snapshot' for
        # bespoke per-condition values from mode:snapshots.
        param_sources: Dict[str, Any] = {}
        swept_path: Optional[str] = None
        swept_meta = getattr(snapshot, 'swept_parameter', None)
        if isinstance(swept_meta, dict):
            swept_id = swept_meta.get('id', '')
            # factorial uses '; '-joined ids; record each separately
            swept_path = swept_id

        for prop_path, value in getattr(snapshot, 'property_overrides', {}).items():
            origin = (
                'sweep'
                if swept_path and (
                    prop_path == swept_path
                    or (isinstance(swept_path, str) and prop_path in swept_path)
                )
                else 'fixed_override'
            )
            try:
                if _is_event_path(prop_path):
                    prior = _apply_event_override(model, prop_path, value)
                    origin = 'event'  # event-field sweeps are still 'event'-typed
                else:
                    obj_id, prop_name = parse_property_path(prop_path)
                    obj = resolve_object(model, obj_id)
                    if obj is None:
                        logger.warning(
                            "Override target %s not found in model", prop_path
                        )
                        continue
                    prior = _read_property(obj, prop_name)
                    apply_property_to_object(obj, prop_name, value)
                logger.info(
                    "[override] %s = %s (was %s, source=%s)",
                    prop_path, value, prior, origin,
                )
                param_sources[prop_path] = {
                    'source': origin,
                    'value': float(value)
                              if isinstance(value, (int, float)) else value,
                    'prior': prior,
                }
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

        return param_sources

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


# ── Event-field override helpers (Layer B+) ──────────────────────────
# A path is treated as an event-field override iff its first dotted
# component matches an event id present on the model.  Supported fields
# (the second component) are listed in _EVENT_SWEEPABLE_FIELDS.  All
# other event fields raise to keep the sweep error-loud.
#
# Canonical "sweep an event payload value" pattern: do **not** sweep an
# assignment expression directly — instead introduce a ▢ parameter place
# that the assignment RHS reads (Pattern A bridge per AGENT_RULES.md),
# and sweep that ▢ place's initial_marking.  This keeps event RHS
# deterministic and biologically-meaningful.
_EVENT_SWEEPABLE_FIELDS = frozenset({'delay', 'priority'})


def _is_event_path(prop_path: str) -> bool:
    """Heuristic: treat any path whose head starts with 'evt_' as an event override.

    The dispatcher / UI uses a stable ``evt_*`` prefix on every event id
    (see ui/panels/environment/events_category). Anything else falls
    through to the place/transition/arc resolver.
    """
    head = prop_path.split('.', 1)[0]
    return head.startswith('evt_')


def _apply_event_override(model: Any, prop_path: str, value: Any) -> Any:
    """Mutate one field on a ``model.events`` entry; return the prior value.

    Raises:
        ValueError: if the event id or field is unknown / unsupported.
    """
    parts = prop_path.split('.', 1)
    if len(parts) != 2:
        raise ValueError(
            f"event override path must be '<evt_id>.<field>', got {prop_path!r}"
        )
    evt_id, field = parts
    if field not in _EVENT_SWEEPABLE_FIELDS:
        raise ValueError(
            f"event field {field!r} is not sweepable; "
            f"supported fields: {sorted(_EVENT_SWEEPABLE_FIELDS)}. "
            f"For payload-value sweeps, sweep a ▢ parameter place that "
            f"the event RHS reads (Pattern A bridge)."
        )
    events = getattr(model, 'events', None) or []
    target = next((e for e in events if getattr(e, 'id', None) == evt_id), None)
    if target is None:
        raise ValueError(
            f"event {evt_id!r} not found on model "
            f"(known: {[getattr(e, 'id', '?') for e in events]})"
        )
    prior = getattr(target, field, None)
    setattr(target, field, float(value) if field == 'delay' else int(value))
    return prior


def _read_property(obj: Any, prop_name: str) -> Any:
    """Best-effort read of a property's prior value before override."""
    # Mirror the alias collapse done in apply_property_to_object
    if prop_name == 'initial_marking':
        return getattr(obj, 'tokens', getattr(obj, 'initial_marking', None))
    return getattr(obj, prop_name, None)


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


# ═════════════════════════════════════════════════════════════════════
# Flat replicate-level dispatch (Strategy A — May 2026)
# ═════════════════════════════════════════════════════════════════════
#
# Previous design: ProcessPoolExecutor of size N submits one
# `_run_single_condition` task per condition; that task internally
# spawns a nested ProcessPool to parallelise its replicates. With
# `workers >= n_conditions` (e.g. 26 workers / 8 conditions), the
# outer pool was the bottleneck — only `n_conditions` workers were
# ever active, each running its 30 reps sequentially. Measured wall
# on the canabidiol Q1 sweep: 78 min where the theoretical lower
# bound is ~25 min.
#
# Strategy A: a SINGLE flat ProcessPool of `workers` processes; the
# unit of work is one (condition, replicate) pair. Total in-flight
# = min(workers, C × R). For C=8, R=30, workers=26 → all 26 cores
# saturated for the whole sweep, modulo the tail.
#
# - Each worker loads the baseline model exactly once via the pool
#   initializer (`_replicate_pool_init`), caching the parsed dict in
#   a module global. Per-replicate cost: from_dict(baseline) +
#   apply_snapshot + run one replicate. Model-reload overhead is
#   amortised (~ms per work unit).
# - Worker returns the full per-replicate result dict via IPC. Main
#   process buffers per-condition; when all R replicates for some
#   condition arrive, it finalises (compute_statistics + write all
#   per-condition output files) and frees the buffer.
# - Memory bound (main process): C × R × ~trajectory_size. For
#   canabidiol Q1 (44 places × 4 800 timepoints × 8 bytes ≈ 1.7 MiB
#   per replicate), C=8, R=30 → ~400 MiB peak. Fine on the i9 server.
# - Submission order: round-robin by replicate index (r=0 across all
#   conditions, then r=1, ...). This keeps all conditions advancing
#   together and roughly synchronises completion times.
# - CLI emit format unchanged:
#       [c+1/C] cond_name (R replicates)...     <- when r=0 submitted
#       [done c+1/C] cond_name in Xs (n_ok ok, n_err errors) [...]
#                                               <- when R-th rep arrives
#   These pair correctly with the controller regex from
#   dispatch/remote.py (commit a1a2d57b).


# Module-global cache for the baseline model dict, populated by the
# pool initialiser exactly once per worker process.
_BASELINE_MODEL_DICT: Optional[dict] = None


def _replicate_pool_init(
    model_path: str,
    pool_worker_count: int = 1,
    gpu_mode: str = 'auto',
) -> None:
    """Initialiser for the flat replicate ProcessPool.

    Loads the baseline model from disk one time per worker, parses to
    a dict, and stashes the dict for reuse across the worker's many
    `_run_one_replicate` invocations. Also installs the standard
    process guard / nice / CPU affinity so the worker is well-behaved
    under SSH.

    Publishes pool size and GPU mode to env vars so the inner
    replicate_runner GPU 'auto' decision can distinguish a
    sole-worker pool (no GPU contention → use GPU) from a
    multi-worker pool (siblings contend for one GPU → skip).
    """
    global _BASELINE_MODEL_DICT
    os.environ['_SHYPN_IN_POOL_WORKER'] = '1'
    os.environ['_SHYPN_POOL_WORKER_COUNT'] = str(int(pool_worker_count))
    if gpu_mode in ('auto', 'force', 'off'):
        os.environ['_SHYPN_USE_GPU'] = gpu_mode
    os.environ.setdefault('DISPLAY', '')
    from shypn.engine.process_guard import install_process_guard
    install_process_guard()
    try:
        os.nice(19)
    except OSError:
        pass
    _apply_cpu_affinity()
    # Logging quiet
    import logging as _logging
    _logging.basicConfig(level=_logging.WARNING)
    for _name in ('shypn.engine.simulation.controller',
                  'shypn.engine.acceleration'):
        _logging.getLogger(_name).setLevel(_logging.ERROR)

    from shypn.data.canvas.document_model import DocumentModel
    model = DocumentModel.load_from_file(model_path)
    _BASELINE_MODEL_DICT = model.to_dict()


def _run_one_replicate(
    *,
    cond_idx: int,
    rep_idx: int,
    cond_name: str,
    baseline_dict_inline: Optional[dict],
    snapshot_dict: dict,
    sim_params: dict,
    events: list,
    time_units_value: str,
) -> dict:
    """Execute exactly one (condition, replicate) work unit.

    Args:
        cond_idx, rep_idx: addressing.
        cond_name: condition snapshot name (passed in to avoid an extra
            pickled object).
        baseline_dict_inline: optional inline baseline dict for callers
            that did not use the pool initialiser (e.g. tests). When
            ``None``, falls back to the worker's cached
            ``_BASELINE_MODEL_DICT``.
        snapshot_dict: serialised ExperimentSnapshot for this condition.
        sim_params: as ``self.config.sim_params`` (asdict).
        events: list of event dicts to install on the model.
        time_units_value: ``TimeUnits`` enum value string.

    Returns:
        ``{cond_idx, rep_idx, cond_name, result, param_sources?}``
        where ``result`` is the full per-replicate result dict from
        :func:`_run_replicate_chunk` (single element). ``param_sources``
        is included only on the first replicate (r=0) of each condition
        to avoid redundant IPC.
    """
    baseline_dict = baseline_dict_inline or _BASELINE_MODEL_DICT
    if baseline_dict is None:
        raise RuntimeError(
            "Replicate worker has no baseline model dict — "
            "_replicate_pool_init was not invoked"
        )

    from shypn.data.canvas.document_model import DocumentModel
    from shypn.engine.simulation.replicate_runner import _run_replicate_chunk

    # Reconstruct fresh model for this work unit (no shared state across
    # replicates within a worker — necessary for clean re-application of
    # the snapshot and event list, which mutate the model in place).
    model = DocumentModel.from_dict(baseline_dict)

    # Build a baseline snapshot from the in-worker model (used by
    # _apply_snapshot to reset per-id markings before applying overrides).
    baseline_snap = SweepRunner._capture_baseline(model)
    snapshot = _dict_to_snapshot(snapshot_dict)
    param_sources = SweepRunner._apply_snapshot(model, snapshot, baseline_snap)

    # Install events forwarded from the dispatcher, exactly as the
    # legacy per-condition path did.
    if events:
        from shypn.data.pathway.pathway_data import Event as _Event
        try:
            model.events = [_Event.from_dict(e) for e in events]
        except Exception as _exc:
            import logging as _lg
            _lg.getLogger(__name__).warning(
                "Failed to install %d events: %s", len(events), _exc
            )

    # Run exactly one replicate via the existing chunk runner.
    chunk = _run_replicate_chunk(
        model_dict=model.to_dict(),
        replicate_ids=[rep_idx],
        seed_base=sim_params['seed_base'],
        duration=sim_params['duration'],
        use_parallel=True,
        use_tau_leaping=True,
        termination_condition=sim_params['termination'],
        time_step=sim_params.get('time_step'),
        epsilon=sim_params['tau_epsilon'],
        max_tau=sim_params['max_tau'],
        time_units_value=time_units_value,
    )

    payload = {
        'cond_idx': cond_idx,
        'rep_idx': rep_idx,
        'cond_name': cond_name,
        'result': chunk[0],
    }
    # Carry parameter_sources only once per condition (with r=0) — saves
    # ~C × (R-1) redundant IPC sends.
    if rep_idx == 0:
        payload['param_sources'] = param_sources
    return payload


def _run_one_condition_batch(
    *,
    cond_idx: int,
    cond_name: str,
    baseline_dict_inline: Optional[dict],
    snapshot_dict: dict,
    sim_params: dict,
    events: list,
    time_units_value: str,
) -> dict:
    """Execute ALL R replicates of one condition in a single work unit.

    Used by the GPU-aware dispatch path: when ``gpu_mode in {'force'}``
    or ``gpu_mode == 'auto' and n_workers <= n_conditions``, we batch
    all replicates per condition into one work unit and route through
    :class:`ReplicateRunner.run_replicates`. That method houses the
    GPU-vs-CPU heuristic and, when GPU is selected, dispatches the
    full batch through the cupy hybrid engine (~100× per-replicate
    speedup verified on canabidiol Q1, 2026-05-09).

    Returns:
        ``{cond_idx, cond_name, results, param_sources}`` where
        ``results`` is the list of ALL R per-replicate result dicts.
    """
    baseline_dict = baseline_dict_inline or _BASELINE_MODEL_DICT
    if baseline_dict is None:
        raise RuntimeError(
            "Condition-batch worker has no baseline model dict — "
            "_replicate_pool_init was not invoked"
        )

    from shypn.data.canvas.document_model import DocumentModel
    from shypn.engine.simulation.replicate_runner import ReplicateRunner
    from shypn.engine.simulation.settings import SimulationSettings

    model = DocumentModel.from_dict(baseline_dict)

    baseline_snap = SweepRunner._capture_baseline(model)
    snapshot = _dict_to_snapshot(snapshot_dict)
    param_sources = SweepRunner._apply_snapshot(model, snapshot, baseline_snap)

    if events:
        from shypn.data.pathway.pathway_data import Event as _Event
        try:
            model.events = [_Event.from_dict(e) for e in events]
        except Exception as _exc:
            import logging as _lg
            _lg.getLogger(__name__).warning(
                "Failed to install %d events: %s", len(events), _exc
            )

    # Settings: pull GPU mode from env (set by _replicate_pool_init).
    _settings = SimulationSettings()
    _gpu_mode = os.environ.get('_SHYPN_USE_GPU', 'auto')
    if _gpu_mode in ('auto', 'force', 'off'):
        _settings.use_gpu = _gpu_mode  # type: ignore[assignment]

    runner = ReplicateRunner(model, settings=_settings)
    results = runner.run_replicates(
        n=int(sim_params['replicates']),
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

    return {
        'cond_idx': cond_idx,
        'cond_name': cond_name,
        'results': results,
        'param_sources': param_sources,
    }


def _finalize_condition(
    *,
    model: Any,
    snapshot: ExperimentSnapshot,
    cond_results: List[dict],
    output_run_dir: Path,
    output_options: dict,
) -> None:
    """Compute statistics and write per-condition outputs.

    Mirrors the disk-write half of the legacy `_run_single_condition`,
    but driven from the main process once all R replicates for a
    condition have arrived from the flat pool.
    """
    from shypn.engine.simulation.replicate_runner import ReplicateRunner
    from shypn.cli.sweep_output import SweepOutputManager
    from shypn.cli.sweep_config import OutputOptions as _OutputOptions

    runner = ReplicateRunner(model)
    stats = runner.compute_statistics(cond_results)

    safe_name = _sanitise_condition_name(snapshot.name)
    cond_dir = output_run_dir / f"condition_{safe_name}"
    cond_dir.mkdir(parents=True, exist_ok=True)

    _opts = _OutputOptions.from_dict(output_options)
    if _opts.write_replicates_csv:
        SweepOutputManager._write_replicates_csv(cond_dir, cond_results, model)
    if _opts.write_statistics_json:
        stats_to_write = (_strip_to_endpoint(stats)
                          if _opts.statistics_endpoint_only else stats)
        SweepOutputManager._write_statistics_json(cond_dir, stats_to_write)
    if _opts.write_per_replicate_trajectories:
        SweepOutputManager._write_per_replicate_trajectories(
            cond_dir, cond_results, model,
            trajectory_places=_opts.trajectory_places,
            trajectory_thin_seconds=_opts.trajectory_thin_seconds,
        )
    if _opts.write_covariance:
        SweepOutputManager._write_covariance(cond_dir, cond_results, model)


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

    # Apply overrides; capture per-path origin info for provenance (Layer D).
    param_sources = SweepRunner._apply_snapshot(model, snapshot, baseline)

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
    from shypn.engine.simulation.settings import SimulationSettings
    _settings = SimulationSettings()
    _gpu_mode = os.environ.get('_SHYPN_USE_GPU', 'auto')
    if _gpu_mode in ('auto', 'force', 'off'):
        _settings.use_gpu = _gpu_mode  # type: ignore[assignment]
    runner = ReplicateRunner(model, settings=_settings)
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
    if _opts.write_per_replicate_trajectories:
        SweepOutputManager._write_per_replicate_trajectories(
            cond_dir, results, model,
            trajectory_places=_opts.trajectory_places,
            trajectory_thin_seconds=_opts.trajectory_thin_seconds,
        )
    if _opts.write_covariance:
        SweepOutputManager._write_covariance(cond_dir, results, model)

    # Persist parameter_sources alongside statistics for provenance.
    # Empty dict still written so downstream tooling can rely on the
    # file's existence as evidence the new code path ran.
    try:
        import json as _json_ps
        with open(cond_dir / 'parameter_sources.json', 'w') as _psf:
            _json_ps.dump({
                'condition': snapshot.name,
                'sources': param_sources,
            }, _psf, indent=2, sort_keys=True)
    except OSError as _exc:
        import logging as _lg2
        _lg2.getLogger(__name__).warning(
            "Failed to write parameter_sources.json: %s", _exc
        )

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
        'parameter_sources': param_sources,
    }
