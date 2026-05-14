#!/usr/bin/env python3
"""Remote Sweep Dispatcher — run CLI sweeps on a remote server via SSH.

Architecture (minimal data transfer):
  1. **Export sweep config** to a local temp file (small JSON, ~1–5 KB)
  2. **SCP config only** to the remote project folder
  3. **SSH run** ``python -m shypn.cli.sweep`` on the remote
  4. **Fetch results** back via ``tar cz | tar xz`` over the
     multiplexed SSH tunnel

Only the experiment plan (sweep_config.json) crosses the network.
The user is responsible for keeping client and server code/model
in sync (e.g. via ``git push`` / ``git pull``) **before** dispatch.

Performance (WAN):
  - A persistent SSH ControlMaster socket is opened once per dispatch
    and reused for every subsequent SSH/SCP call.
  - All SSH traffic is compressed (``-C``).
  - Results are fetched as a single compressed tar stream (no per-file
    round-trips).

Requires:
  - SSH access to server (password or key)
  - Remote repo clone at a known path with ``.venv``
  - Client and server repos synced before dispatch

Author: Simão Eugénio
Date: April 2026
"""

import hashlib
import json
import logging
import os
import platform
import re
import shutil
import socket
import subprocess
import tempfile
import threading
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Callable, Optional

from .remote_results_proxy import RemoteResultsProxy
from .dispatch_registry import DispatchRegistry, PendingDispatch

logger = logging.getLogger(__name__)


class FetchMode(Enum):
    """Controls how much data is fetched after a sweep completes.

    FULL:
        Legacy behavior — fetch entire run directory via tar pipe.
        Suitable for local-network sweeps or small result sets.

    SUMMARY_ONLY:
        Fetch only summary.csv + config.json (~KB). Individual
        condition directories are fetched on-demand via the
        RemoteResultsProxy when the user requests plots/exports.
        Ideal for WAN connections with large result sets (GB+).
    """

    FULL = auto()
    SUMMARY_ONLY = auto()


class RemoteSweepSettings:
    """SSH/remote configuration for sweep dispatch.

    Persisted under ``~/.config/shypn/workspace.json`` →
    ``remote_sweep`` section.
    """

    DEFAULTS = {
        'ssh_host': 'remote-gpu',
        'remote_repo': '/home/simao/shypn',
        'remote_venv': '.venv/bin/python',
        'workers': 0,  # 0 = auto
        'fetch_mode': 'summary_only',  # 'full' or 'summary_only'
    }

    def __init__(self, workspace_settings=None):
        self._ws = workspace_settings
        self._section = dict(self.DEFAULTS)
        if self._ws:
            saved = self._ws.settings.get('remote_sweep', {})
            self._section.update(saved)

    # ── accessors ────────────────────────────────────────────────────
    @property
    def ssh_host(self) -> str:
        return self._section['ssh_host']

    @ssh_host.setter
    def ssh_host(self, v: str):
        self._section['ssh_host'] = v

    @property
    def remote_repo(self) -> str:
        return self._section['remote_repo']

    @remote_repo.setter
    def remote_repo(self, v: str):
        self._section['remote_repo'] = v

    @property
    def remote_venv(self) -> str:
        return self._section['remote_venv']

    @remote_venv.setter
    def remote_venv(self, v: str):
        self._section['remote_venv'] = v

    @property
    def workers(self) -> int:
        return self._section['workers']

    @workers.setter
    def workers(self, v: int):
        self._section['workers'] = max(0, int(v))

    @property
    def fetch_mode(self) -> FetchMode:
        raw = self._section.get('fetch_mode', 'summary_only')
        try:
            return FetchMode[raw.upper()]
        except KeyError:
            return FetchMode.SUMMARY_ONLY

    @fetch_mode.setter
    def fetch_mode(self, v: FetchMode) -> None:
        self._section['fetch_mode'] = v.name.lower()

    def save(self):
        """Persist to workspace.json."""
        if self._ws:
            self._ws.settings['remote_sweep'] = dict(self._section)
            self._ws.save()

    def to_dict(self) -> dict:
        return dict(self._section)


class RemoteSweepDispatcher:
    """Orchestrates a full remote sweep cycle (config → SSH → fetch).

    All heavy I/O runs on a background thread.  GTK callbacks are
    delivered via ``GLib.idle_add`` by the caller (automation category).

    Data-transfer policy:
        Controlled by ``FetchMode`` in settings:
        - **FULL**: Fetch entire run directory via compressed tar pipe.
        - **SUMMARY_ONLY** (default): Fetch only summary.csv + config.json.
          Individual conditions are fetched on-demand via ``RemoteResultsProxy``.
    """

    def __init__(self, settings: RemoteSweepSettings):
        self.settings = settings
        self._cancel = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._ctl_path: Optional[str] = None  # SSH ControlMaster socket
        self._ctl_proc: Optional[subprocess.Popen] = None  # Managed CM process
        self._stream_proc: Optional[subprocess.Popen] = None
        self._ssh_password: Optional[str] = None
        self.verbose_preflight = True
        self._last_proxy: Optional[RemoteResultsProxy] = None

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def results_proxy(self) -> Optional[RemoteResultsProxy]:
        """The proxy from the most recent successful SUMMARY_ONLY dispatch."""
        return self._last_proxy

    def cancel(self):
        """Request cancellation of a running dispatch.

        Sends a remote ``pkill`` to terminate the sweep process tree
        on the server, then terminates the local SSH stream process.
        Without the remote kill, the server-side sweep keeps running
        because ``-T`` (no PTY) prevents SIGHUP propagation.
        """
        self._cancel.set()
        self._kill_remote_sweep()

    # ── public entry point ───────────────────────────────────────────
    def dispatch(
        self,
        model_filepath: str,
        project_folder: str,
        experiment_manager,
        sim_params: dict,
        progress_cb: Optional[Callable[[str], None]] = None,
        complete_cb: Optional[Callable[[bool, str, str], None]] = None,
        ssh_password: Optional[str] = None,
        events: Optional[list] = None,
        fixed_overrides: Optional[dict] = None,
    ):
        """Launch the remote sweep pipeline on a background thread.

        Args:
            model_filepath: Absolute local path to the ``.shy`` model file.
                Used only to derive the repo-relative model path (the file
                itself is **not** transferred — it must already exist on
                the server).
            project_folder: Absolute local path to the project root
                (e.g. ``workspace/projects/canabidiol``).
            experiment_manager: ``ExperimentManager`` instance (has
                ``export_sweep_config``).
            sim_params: Dict with keys ``replicates``, ``duration``,
                ``termination``, ``seed_base``, ``tau_epsilon``, ``max_tau``.
            progress_cb: Called on the **background** thread with a status
                string for each pipeline phase.
            complete_cb: ``(success, local_results_dir, message)``
                — called when the pipeline finishes or fails.
            ssh_password: Optional SSH password (used via ``sshpass``).
        """
        if self.is_running:
            if complete_cb:
                complete_cb(False, '', 'A remote sweep is already running.')
            return

        self._cancel.clear()
        self._ssh_password = ssh_password
        self._thread = threading.Thread(
            target=self._run_pipeline,
            args=(model_filepath, project_folder, experiment_manager,
                  sim_params, progress_cb, complete_cb, ssh_password,
                  list(events) if events else [],
                  dict(fixed_overrides) if fixed_overrides else None),
            daemon=True,
        )
        self._thread.start()

    # ── pipeline ─────────────────────────────────────────────────────
    def _run_pipeline(
        self,
        model_filepath: str,
        project_folder: str,
        experiment_manager,
        sim_params: dict,
        progress_cb,
        complete_cb,
        ssh_password: Optional[str] = None,
        events: Optional[list] = None,
        fixed_overrides: Optional[dict] = None,
    ):
        staging = None
        host = self.settings.ssh_host
        try:
            remote_repo = self.settings.remote_repo
            remote_venv = self.settings.remote_venv
            workers = self.settings.workers

            # ── resolve paths ────────────────────────────────────────
            project_abs = Path(project_folder).resolve()
            repo_root = self._find_repo_root(project_abs)
            if repo_root is None:
                raise RuntimeError(
                    f"Cannot determine repo root from: {project_folder}")
            project_rel = str(project_abs.relative_to(repo_root))

            model_abs = Path(model_filepath).resolve()
            model_rel_to_project = str(model_abs.relative_to(project_abs))

            # ── 1. Open persistent SSH connection ────────────────────
            self._emit(progress_cb, 'Opening SSH connection...')
            self._open_control_master(host, password=ssh_password)

            # ── 1b. Pre-dispatch cleanup ─────────────────────────────
            # Clean stale state from previous failed/killed sweeps to
            # prevent swap pollution, orphan processes, and socket errors.
            self._emit(progress_cb, 'Cleaning up stale state...')
            cleanup_cmd = (
                # Kill orphaned sweep workers from prior runs
                "pkill -9 -f 'shypn[.]cli[.]sweep' 2>/dev/null; "
                # Give processes time to die
                "sleep 1; "
                # Report cleanup results
                "echo ORPHANS_KILLED=$?; "
                # Check swap usage — if high but RAM is free, advise
                "echo SWAP_USED_KB=$(awk '/SwapTotal/{t=$2} /SwapFree/{f=$2} END{print t-f}' /proc/meminfo); "
                "echo MEM_FREE_KB=$(awk '/MemAvailable/{print $2}' /proc/meminfo)"
            )
            try:
                cleanup_out = self._ssh(host, cleanup_cmd, password=ssh_password, timeout=15)
                cl = {}
                for line in cleanup_out.strip().splitlines():
                    if '=' in line:
                        k, v = line.split('=', 1)
                        cl[k.strip()] = v.strip()
                swap_gb = int(cl.get('SWAP_USED_KB', '0')) / (1024 * 1024)
                mem_free_gb = int(cl.get('MEM_FREE_KB', '0')) / (1024 * 1024)
                if swap_gb > 1.0 and mem_free_gb > 20.0:
                    logger.warning(
                        "Server has %.1f GB in swap with %.0f GB RAM free "
                        "(leftover from prior OOM). Performance may be "
                        "degraded until swap drains.", swap_gb, mem_free_gb)
                logger.info("Pre-dispatch cleanup done: swap=%.1f GB, "
                            "RAM free=%.0f GB", swap_gb, mem_free_gb)
            except Exception as e:
                logger.warning("Pre-dispatch cleanup failed (non-fatal): %s", e)

            # ── 2. Export sweep config (local temp) ──────────────────
            self._emit(progress_cb,
                       f'Exporting sweep config ({len(events or [])} event(s))...')
            staging = Path(tempfile.mkdtemp(prefix='shypn_remote_'))
            config_path = staging / 'sweep_config.json'
            experiment_manager.export_sweep_config(
                filepath=str(config_path),
                model_path=model_rel_to_project,
                events=events or None,
                fixed_overrides=fixed_overrides or None,
                **sim_params,
            )
            # Audit log: dump event count + ids straight from the file
            try:
                with open(config_path) as _f:
                    _exported = json.load(_f)
                _ev = _exported.get('events') or []
                logger.info(
                    "[EVENT_DISPATCH] sweep_config.json contains %d event(s): %s",
                    len(_ev),
                    [e.get('id') + '@' + e.get('trigger', '') for e in _ev],
                )
            except Exception:
                pass

            # Sanity check (parity with BatchExecutor): warn when an event
            # references a token (place id or name) not present in the
            # local model file. Catches typos like ``MANT_DOSE`` for
            # ``MAINT_DOSE`` that would otherwise silently no-op inside
            # remote workers (eval() failure is logged at debug level only).
            try:
                with open(model_filepath) as _mf:
                    _model_json = json.load(_mf)
                _model_place_ids = {p.get('id') for p in _model_json.get('places', [])
                                    if p.get('id')}
                _model_place_names = {p.get('name') for p in _model_json.get('places', [])
                                      if p.get('name')}
                import re as _re
                _token_re = _re.compile(r'\b([A-Za-z_][A-Za-z0-9_]*)\b')
                _BUILTINS = {'t', 'time', 'and', 'or', 'not', 'True', 'False',
                             'min', 'max', 'abs', 'log', 'exp', 'sqrt', 'if',
                             'else', 'None'}
                for _ev in _exported.get('events') or []:
                    _refs: set = set()
                    _refs.update(_token_re.findall(_ev.get('trigger', '') or ''))
                    for _k, _v in (_ev.get('assignments', {}) or {}).items():
                        _refs.add(_k)
                        _refs.update(_token_re.findall(str(_v)))
                    _missing = sorted(
                        t for t in _refs
                        if t not in _model_place_ids
                        and t not in _model_place_names
                        and not t.isdigit()
                        and t not in _BUILTINS
                    )
                    if _missing:
                        _msg = (
                            f"[EVENT_DISPATCH] event {_ev.get('id', '?')!r} "
                            f"references token(s) not present in model "
                            f"{Path(model_filepath).name!r}: {_missing}. "
                            f"These will silently no-op on workers (eval "
                            f"NameError logged at debug level only). "
                            f"Likely a typo in trigger/assignment expression "
                            f"or a missing parameter place."
                        )
                        logger.warning(_msg)
                        self._emit(progress_cb, _msg)
            except Exception as _exc:
                logger.warning(
                    "[EVENT_DISPATCH] event sanity check skipped (%s): %s",
                    type(_exc).__name__, _exc,
                )

            # ── 2b. Pre-flight validation ────────────────────────────
            # Detect duplicate snapshots (common when user clicks Generate
            # multiple times before the dedup fix).
            with open(config_path, 'r') as f:
                exported = json.load(f)
            if exported.get('mode') == 'snapshots':
                snap_names = [s.get('name', '') for s in exported.get('snapshots', [])]
                unique_names = set(snap_names)
                if len(snap_names) > len(unique_names):
                    dupes = len(snap_names) - len(unique_names)
                    raise RuntimeError(
                        f"Sweep config contains {dupes} duplicate snapshot(s) "
                        f"({len(snap_names)} total, {len(unique_names)} unique). "
                        f"Please clear and regenerate experiments.")

            # Allocation summary — emitted explicitly so the user sees
            # workers × conditions × replicates regardless of streaming
            # noise from the parent sweep CLI.
            try:
                _n_snap = len(exported.get('snapshots', [])) or 1
                _n_rep = int(exported.get('replicates', 1) or 1)
                _n_evt = len(exported.get('events', []) or [])
                _w = workers if workers > 0 else 'auto'
                self._emit(
                    progress_cb,
                    f"Allocated {_w} worker(s) for {_n_snap} condition(s) "
                    f"× {_n_rep} replicate(s) = {_n_snap * _n_rep} simulation(s) "
                    f"({_n_evt} event(s))",
                )
            except Exception:
                pass

            if self._cancel.is_set():
                raise InterruptedError('Cancelled')

            # ── 3. SCP config to remote ─────────────────────────────
            self._emit(progress_cb, 'Creating remote directory...')
            remote_project = f"{remote_repo}/{project_rel}"
            self._ssh(host, f"mkdir -p {remote_project}",
                      password=ssh_password)
            self._emit(progress_cb, 'Uploading sweep config...')
            self._scp_to(host, str(config_path),
                         f"{remote_project}/sweep_config.json",
                         password=ssh_password)

            # Upload the model file too. Without this, the remote uses
            # whatever stale revision is checked out in its working tree
            # (events, edits, parameter overrides applied locally would
            # silently no-op). Uploads to the relative path encoded in
            # the sweep config (model_rel_to_project) so the worker's
            # `model_path` resolves to the freshly uploaded file.
            remote_model_path = f"{remote_project}/{model_rel_to_project}"
            remote_model_dir = str(Path(remote_model_path).parent).replace('\\', '/')
            self._ssh(host, f"mkdir -p {remote_model_dir}",
                      password=ssh_password)
            self._emit(progress_cb,
                       f'Uploading model file ({Path(model_filepath).name})...')
            self._scp_to(host, str(model_abs), remote_model_path,
                         password=ssh_password)
            logger.info("[MODEL_DISPATCH] uploaded %s -> %s",
                        model_filepath, remote_model_path)

            # ── Provenance: git context (client + server) + digests ──
            # Hybrid sync model: SCP delivers the model, git remains the
            # canonical history. Provenance ties each run to a (client
            # SHA, server SHA, model sha256) triple so any run can be
            # reconstructed regardless of subsequent edits/commits.
            self._emit(progress_cb, 'Collecting provenance...')
            client_git = self._local_git_context(repo_root)
            server_git = self._remote_git_context(
                host, remote_repo, password=ssh_password)
            model_sha = self._sha256_file(model_abs)
            try:
                model_size = model_abs.stat().st_size
            except OSError:
                model_size = -1
            config_sha = self._sha256_file(config_path)
            provenance = self._build_provenance(
                client_git=client_git,
                server_git=server_git,
                model_filepath=str(model_abs),
                model_sha256=model_sha,
                model_size_bytes=model_size,
                remote_model_path=remote_model_path,
                sweep_config_sha256=config_sha,
                host=host,
            )

            # Dirty-tree warnings — non-blocking. Interactive science
            # often runs from a dirty tree; we only flag it loudly so
            # results stay traceable.
            if client_git.get('dirty'):
                msg = (f"Client repo {repo_root} has uncommitted changes "
                       f"({len(client_git.get('dirty_paths', []))} path(s)). "
                       f"Run will be marked dirty in provenance.json.")
                logger.warning("[PROVENANCE] %s", msg)
                self._emit(progress_cb, f"⚠ {msg}")
            if server_git.get('dirty'):
                msg = (f"Server repo {remote_repo} has uncommitted changes "
                       f"({len(server_git.get('dirty_paths', []))} path(s)). "
                       f"Engine code may differ from client.")
                logger.warning("[PROVENANCE] %s", msg)
                self._emit(progress_cb, f"⚠ {msg}")
            client_sha = client_git.get('head_sha')
            server_sha = server_git.get('head_sha')
            if client_sha and server_sha and client_sha != server_sha:
                msg = (f"Client/server git HEAD diverge "
                       f"({client_sha[:8]} vs {server_sha[:8]}). "
                       f"Engine semantics may differ from local expectations.")
                logger.warning("[PROVENANCE] %s", msg)
                self._emit(progress_cb, f"⚠ {msg}")

            # Stage + upload provenance.json next to sweep_config.json.
            # The CLI sweep_runner copies it into the run dir on startup.
            provenance_path = staging / 'provenance.json'
            try:
                with open(provenance_path, 'w') as _pf:
                    json.dump(provenance, _pf, indent=2, sort_keys=True)
                self._scp_to(host, str(provenance_path),
                             f"{remote_project}/provenance.json",
                             password=ssh_password)
                logger.info(
                    "[PROVENANCE] client=%s%s server=%s%s model_sha256=%s",
                    (client_sha or 'n/a')[:8],
                    '+dirty' if client_git.get('dirty') else '',
                    (server_sha or 'n/a')[:8],
                    '+dirty' if server_git.get('dirty') else '',
                    (model_sha or 'n/a')[:12],
                )
            except OSError as exc:
                logger.warning("Could not write/upload provenance.json: %s", exc)

            if self._cancel.is_set():
                raise InterruptedError('Cancelled')

            # ── 3b. Remote pre-flight: memory & sweep conflict check ─
            self._emit(progress_cb, 'Checking remote server resources...')
            preflight_cmd = (
                "echo MEM_AVAIL_KB=$(awk '/MemAvailable/{print $2}' /proc/meminfo) && "
                "echo SWEEP_PROCS=$(pgrep -fc 'shypn[.]cli[.]sweep' 2>/dev/null; true) && "
                "echo SWAP_USED_KB=$(awk '/SwapTotal/{t=$2} /SwapFree/{f=$2} END{print t-f}' /proc/meminfo)"
            )
            try:
                preflight_out = self._ssh(host, preflight_cmd, password=ssh_password, timeout=15)
                pf = {}
                for line in preflight_out.strip().splitlines():
                    if '=' in line:
                        k, v = line.split('=', 1)
                        pf[k.strip()] = v.strip()

                # Fail if another sweep is already running
                running = int(pf.get('SWEEP_PROCS', '0').split()[0])
                if running > 0:
                    raise RuntimeError(
                        f"Another sweep is already running on the server "
                        f"({running} processes). Wait for it to finish or "
                        f"kill it manually before dispatching a new one.")

                # Warn if available memory is low (< 8 GB)
                avail_kb = int(pf.get('MEM_AVAIL_KB', '0').split()[0])
                avail_gb = avail_kb / (1024 * 1024)
                swap_kb = int(pf.get('SWAP_USED_KB', '0').split()[0])
                swap_gb = swap_kb / (1024 * 1024)
                if avail_gb < 8.0:
                    raise RuntimeError(
                        f"Server has only {avail_gb:.1f} GB available RAM "
                        f"(swap used: {swap_gb:.1f} GB). "
                        f"Not enough for a sweep. Reboot or free memory first.")
                if self.verbose_preflight:
                    self._emit(progress_cb,
                               f"Remote: {avail_gb:.0f} GB RAM free, "
                               f"swap {swap_gb:.1f} GB used")
            except RuntimeError:
                raise
            except Exception as e:
                # Non-fatal: log and proceed (server might be non-Linux)
                logger.warning("Pre-flight check failed (non-fatal): %s", e)

            if self._cancel.is_set():
                raise InterruptedError('Cancelled')

            # ── 4. SSH run CLI on remote ─────────────────────────────
            self._emit(progress_cb, 'Running sweep on remote server...')

            # Pass user-specified workers as a ceiling hint; the server's
            # _compute_safe_workers() will cap it to a memory-safe value.
            workers_flag = f"--workers {workers}" if workers > 0 else ""
            # Design: the sweep runs in the background with stdout/stderr
            # redirected to a temp log file, completely decoupled from the
            # SSH channel.  `tail -f --pid=$SWEEP_PID` then streams the log
            # back to the client.
            #
            # This solves the SIGPIPE problem: previously the sweep wrote
            # directly to the SSH channel (stdout). When the client closed
            # the connection the SSH channel died and Python's next print()
            # call got BrokenPipeError → process exited after only 1 of 25
            # conditions (observed run_20260514_191917).
            #
            # With the log-file approach:
            #   • SSH closes → tail gets SIGPIPE → tail exits
            #   • sweep is still writing to the log file → keeps running
            #   • all 25 conditions complete and write results to disk
            #
            # setsid: detach from the SSH controlling tty so SIGHUP on
            # client disconnect does NOT propagate to the sweep process.
            #
            # nice -n 19 + ionice -c 3: lowest CPU/IO priority.
            # taskset -c 4-31: pin sweep to CPUs 4-31.
            remote_cmd = (
                f"cd {remote_repo} && "
                f"export PYTHONPATH=$PWD/src && "
                f"export PYTHONUNBUFFERED=1; "
                # NOTE: use ';' (not '&&') between the mktemp assignment,
                # the setsid background launch, and the echos.  In bash,
                # '&&' binds tighter than '&': 'A && B & C' is parsed as
                # '(A && B) & C', putting the assignment into a subshell so
                # $SWEEP_LOG is invisible to the parent. With ';' all
                # commands run sequentially in the same shell.
                f"SWEEP_LOG=$(mktemp /tmp/shypn_sweep_XXXXXX); "
                f"setsid nice -n 19 ionice -c 3 taskset -c 4-31 "
                f"{remote_venv} -u -m shypn.cli.sweep "
                f"--project {project_rel} "
                f"--sweep sweep_config.json "
                f"{workers_flag} "
                f"--verbose "
                f"> \"$SWEEP_LOG\" 2>&1 & "
                f"SWEEP_PID=$!; "
                f"echo \"[SWEEP_PID] $SWEEP_PID\"; "
                f"echo \"[SWEEP_LOG] $SWEEP_LOG\"; "
                f"tail -f --pid=$SWEEP_PID \"$SWEEP_LOG\" 2>/dev/null; "
                f"wait $SWEEP_PID 2>/dev/null; "
                f"EXIT=$?; "
                f"[ $EXIT -ne 0 ] && echo \"[SWEEP_EXIT] $EXIT\"; "
                f"rm -f \"$SWEEP_LOG\""
            )

            stdout = self._ssh_stream(
                host, remote_cmd,
                password=ssh_password,
                progress_cb=progress_cb,
                cancel=self._cancel,
            )

            # Parse "Results: <path>" from output
            run_dir = self._parse_results_dir(stdout)
            if not run_dir:
                raise RuntimeError(
                    f"Could not parse results directory from remote output:\n"
                    f"{stdout[-500:]}")

            if not run_dir.startswith('/'):
                run_dir = f"{remote_repo}/{run_dir}"

            if self._cancel.is_set():
                raise InterruptedError('Cancelled')

            # ── 4. Fetch results back ────────────────────────────────
            run_name = Path(run_dir).name
            local_results_base = project_abs / 'experiments' / 'results'
            local_results_base.mkdir(parents=True, exist_ok=True)
            local_run_dir = local_results_base / run_name

            fetch_mode = self.settings.fetch_mode

            # Persist a recovery record BEFORE the fetch begins.  If the
            # GUI is closed, restarted, or the connection drops between
            # this point and the successful complete_cb call below, the
            # next project-open will pick up this entry and retry the
            # summary fetch — recovering an otherwise-invisible run.
            registry = DispatchRegistry.for_project(project_abs)
            pending_entry = PendingDispatch(
                run_dir_remote=run_dir,
                run_dir_local=str(local_run_dir),
                ssh_host=host,
                fetch_mode=fetch_mode.name.lower(),
            )
            if registry is not None:
                registry.register(pending_entry)

            if fetch_mode == FetchMode.SUMMARY_ONLY:
                # Lightweight fetch: only summary.csv + config.json (~KB)
                self._emit(progress_cb,
                           'Fetching summary (lazy mode)...')
                proxy = RemoteResultsProxy(
                    remote_run_dir=run_dir,
                    local_run_dir=str(local_run_dir),
                    ssh_host=host,
                    ssh_password=ssh_password,
                    ctl_socket_args=self._ctl_socket_args(),
                )
                proxy.fetch_summary()
                self._last_proxy = proxy
                self._emit(progress_cb,
                           f'Done — summary at {local_run_dir.name} '
                           f'(conditions fetched on demand)')
            else:
                # Full fetch: entire run directory via tar pipe
                self._emit(progress_cb, 'Fetching results from remote...')
                self._fetch_results_tar(host, run_dir, str(local_run_dir),
                                        password=ssh_password)
                self._last_proxy = None
                self._emit(progress_cb,
                           f'Done — results at {local_run_dir.name}')

            # Fetch succeeded — drop the recovery record.
            if registry is not None:
                registry.unregister(str(local_run_dir))

            # ── 5. Done ──────────────────────────────────────────────
            if complete_cb:
                complete_cb(True, str(local_run_dir),
                            f'Sweep complete: {run_name}')

        except InterruptedError:
            if complete_cb:
                complete_cb(False, '', 'Remote sweep cancelled.')
        except Exception as e:
            logger.exception("Remote sweep failed")
            if complete_cb:
                complete_cb(False, '', str(e))
        finally:
            self._close_control_master(host)
            self._ssh_password = None
            if staging and staging.exists():
                shutil.rmtree(staging, ignore_errors=True)

    def _kill_remote_sweep(self):
        """Send a kill command to the remote server to stop the sweep."""
        host = self.settings.ssh_host
        try:
            # Use pgrep + kill instead of pkill to avoid killing our own
            # SSH session.  pkill -f "shypn.cli.sweep" matches the bash
            # shell running the pkill command (its cmdline contains the
            # pattern), causing exit 255.  pgrep excludes its own PID,
            # and [.] in the regex prevents matching the literal bracket
            # characters in the bash cmdline.
            kill_cmd = (
                "pids=$(pgrep -f 'shypn[.]cli[.]sweep'); "
                "[ -n \"$pids\" ] && kill -9 $pids; true"
            )
            # Use a completely independent SSH connection — bypass both
            # the app's ControlMaster socket and the user's ~/.ssh/config
            # ControlMaster, which may be stale or blocked by the
            # still-running stream connection.
            argv = [
                'ssh',
                '-o', 'ControlMaster=no',
                '-o', 'ControlPath=none',
                '-o', 'ConnectTimeout=10',
                '-C',
                host, kill_cmd,
            ]
            if self._ssh_password:
                argv = ['sshpass', '-p', self._ssh_password] + argv
            subprocess.run(argv, capture_output=True, timeout=15)
            logger.info("Sent remote kill for sweep processes on %s", host)
        except Exception as exc:
            logger.warning("Failed to kill remote sweep: %s", exc)

        # Also terminate the local SSH stream if still running
        proc = self._stream_proc
        if proc and proc.poll() is None:
            proc.terminate()

    # ── helpers ──────────────────────────────────────────────────────
    @staticmethod
    def _emit(cb, msg):
        if cb:
            cb(msg)

    @staticmethod
    def _find_repo_root(path: Path) -> Optional[Path]:
        """Walk up from *path* looking for a ``.git`` directory."""
        for parent in [path] + list(path.parents):
            if (parent / '.git').is_dir():
                return parent
        return None

    # ── provenance: git context + file digests ───────────────────────
    @staticmethod
    def _sha256_file(path: Path, *, chunk: int = 1 << 20) -> Optional[str]:
        """Return hex sha256 of *path* or ``None`` on read failure."""
        try:
            h = hashlib.sha256()
            with open(path, 'rb') as f:
                for buf in iter(lambda: f.read(chunk), b''):
                    h.update(buf)
            return h.hexdigest()
        except OSError as exc:
            logger.warning("Could not hash %s: %s", path, exc)
            return None

    @staticmethod
    def _local_git_context(repo_root: Path) -> dict:
        """Capture ``HEAD`` SHA, branch, dirty flag for *repo_root*.

        Never raises. Missing git / non-repo / disconnected state are
        all reported as ``None`` fields with a ``status`` annotation.
        """
        ctx: dict = {
            'repo_root': str(repo_root),
            'head_sha': None,
            'branch': None,
            'dirty': None,
            'dirty_paths': [],
            'status': 'ok',
        }
        try:
            head = subprocess.run(
                ['git', '-C', str(repo_root), 'rev-parse', 'HEAD'],
                capture_output=True, text=True, timeout=5)
            if head.returncode == 0:
                ctx['head_sha'] = head.stdout.strip()
            branch = subprocess.run(
                ['git', '-C', str(repo_root), 'rev-parse', '--abbrev-ref', 'HEAD'],
                capture_output=True, text=True, timeout=5)
            if branch.returncode == 0:
                ctx['branch'] = branch.stdout.strip()
            status = subprocess.run(
                ['git', '-C', str(repo_root), 'status', '--porcelain'],
                capture_output=True, text=True, timeout=5)
            if status.returncode == 0:
                lines = [ln for ln in status.stdout.splitlines() if ln.strip()]
                ctx['dirty'] = len(lines) > 0
                ctx['dirty_paths'] = lines[:50]  # cap
        except (subprocess.SubprocessError, FileNotFoundError, OSError) as exc:
            ctx['status'] = f'git probe failed: {exc}'
        return ctx

    def _remote_git_context(self, host: str, repo_root_remote: str,
                            *, password: Optional[str]) -> dict:
        """SSH-side equivalent of :meth:`_local_git_context`.

        One round-trip: combines ``rev-parse``, ``rev-parse --abbrev-ref``
        and ``status --porcelain`` into a single shell command.
        Returns same shape as the local context.
        """
        ctx: dict = {
            'repo_root': repo_root_remote,
            'head_sha': None,
            'branch': None,
            'dirty': None,
            'dirty_paths': [],
            'status': 'ok',
        }
        cmd = (
            f"cd {repo_root_remote} && "
            "echo HEAD=$(git rev-parse HEAD 2>/dev/null) && "
            "echo BRANCH=$(git rev-parse --abbrev-ref HEAD 2>/dev/null) && "
            "echo --STATUS-- && "
            "git status --porcelain 2>/dev/null | head -50"
        )
        try:
            out = self._ssh(host, cmd, password=password, timeout=15)
        except Exception as exc:
            ctx['status'] = f'remote git probe failed: {exc}'
            return ctx
        in_status = False
        dirty: list[str] = []
        for line in out.splitlines():
            if line.startswith('HEAD='):
                v = line.split('=', 1)[1].strip()
                ctx['head_sha'] = v or None
            elif line.startswith('BRANCH='):
                v = line.split('=', 1)[1].strip()
                ctx['branch'] = v or None
            elif line.strip() == '--STATUS--':
                in_status = True
            elif in_status and line.strip():
                dirty.append(line)
        ctx['dirty'] = bool(dirty) if ctx['head_sha'] else None
        ctx['dirty_paths'] = dirty
        return ctx

    @staticmethod
    def _build_provenance(
        *,
        client_git: dict,
        server_git: dict,
        model_filepath: str,
        model_sha256: Optional[str],
        model_size_bytes: int,
        remote_model_path: str,
        sweep_config_sha256: Optional[str],
        host: str,
    ) -> dict:
        """Assemble the provenance record for a single dispatch."""
        return {
            'schema_version': 1,
            'dispatched_at': datetime.now().isoformat(timespec='seconds'),
            'client': {
                'hostname': socket.gethostname(),
                'platform': platform.platform(),
                'python': platform.python_version(),
                'git': client_git,
            },
            'server': {
                'host': host,
                'git': server_git,
            },
            'model': {
                'source_path': str(model_filepath),
                'remote_path': remote_model_path,
                'sha256': model_sha256,
                'size_bytes': model_size_bytes,
            },
            'sweep_config_sha256': sweep_config_sha256,
        }

    # ── SSH ControlMaster multiplexing ───────────────────────────────
    def _ctl_socket_args(self) -> list[str]:
        """Return SSH args that attach to the persistent control socket."""
        if self._ctl_path:
            return ['-o', f'ControlPath={self._ctl_path}']
        return []

    def _open_control_master(self, host: str, *,
                             password: Optional[str] = None):
        """Open a persistent SSH connection (ControlMaster).

        Uses ``-f`` to fork into the background after authentication,
        so this call returns as soon as the connection is established
        (typically < 2 s) instead of blocking for the full timeout.

        All subsequent _ssh / _scp_to / _ssh_stream calls will
        multiplex over this single TCP connection, avoiding repeated
        handshakes (huge win on high-latency WAN links).
        """
        # Clean stale sockets from previous runs to prevent
        # "Connection refused" errors on reused socket paths.
        import glob
        for stale in glob.glob(os.path.join(tempfile.gettempdir(),
                                            'shypn_ssh_*.sock')):
            try:
                os.unlink(stale)
                logger.debug("Removed stale SSH socket: %s", stale)
            except OSError:
                pass

        ctl = tempfile.mktemp(prefix='shypn_ssh_', suffix='.sock',
                              dir=tempfile.gettempdir())
        argv = [
            'ssh', '-C',
            '-o', 'ControlMaster=yes',
            '-o', f'ControlPath={ctl}',
            '-o', 'ControlPersist=300',
            '-o', 'ServerAliveInterval=30',
            '-o', 'ServerAliveCountMax=3',
            '-o', 'ConnectTimeout=15',
            '-o', 'StrictHostKeyChecking=no',
            '-N',  # no remote command (stays in foreground)
            host,
        ]
        if password:
            # Force password auth to avoid wasting time on pubkey attempts
            # that will never succeed with sshpass.
            argv.insert(-1, '-o')
            argv.insert(-1, 'PreferredAuthentications=password')
            argv = ['sshpass', '-p', password] + argv

        # Launch as a managed background subprocess instead of ssh -f.
        # sshpass + ssh -f is unreliable: sshpass exits after auth but
        # the forked SSH process sometimes fails to bind the socket.
        # Running without -f keeps sshpass holding the pipe open.
        try:
            # Inherit the full environment so SSH_AUTH_SOCK (ssh-agent
            # socket) and SSH_AGENT_PID are visible to the subprocess.
            # Without this, the ControlMaster process cannot reach the
            # agent and pubkey auth fails with "Permission denied".
            self._ctl_proc = subprocess.Popen(
                argv,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                stdin=subprocess.DEVNULL,
                env=os.environ.copy(),
            )
        except Exception as e:
            logger.warning("ControlMaster launch failed (%s), falling back "
                           "to per-command connections", e)
            self._ctl_path = None
            return

        # Wait for socket to appear (up to 15 s)
        import time
        deadline = time.monotonic() + 15
        while time.monotonic() < deadline:
            if os.path.exists(ctl):
                break
            if self._ctl_proc.poll() is not None:
                # Process exited before creating socket
                stderr = self._ctl_proc.stderr.read().decode().strip() if self._ctl_proc.stderr else ''
                logger.warning("ControlMaster exited early (%s), falling back",
                               stderr)
                self._ctl_path = None
                return
            time.sleep(0.2)
        else:
            # Timeout — socket never appeared
            self._ctl_proc.terminate()
            logger.warning("ControlMaster socket never appeared, falling back")
            self._ctl_path = None
            return

        # Verify the socket is actually alive
        check = subprocess.run(
            ['ssh', '-O', 'check', '-o', f'ControlPath={ctl}', host],
            capture_output=True, text=True, timeout=10,
        )
        if check.returncode != 0:
            logger.warning("ControlMaster check failed (%s), falling back",
                           check.stderr.strip())
            self._ctl_proc.terminate()
            try:
                os.unlink(ctl)
            except OSError:
                pass
            self._ctl_path = None
            return

        self._ctl_path = ctl
        logger.info("SSH ControlMaster opened and verified: %s", ctl)

    def _close_control_master(self, host: str):
        """Tear down the persistent SSH connection."""
        if not self._ctl_path:
            return
        try:
            subprocess.run(
                ['ssh', '-O', 'exit',
                 '-o', f'ControlPath={self._ctl_path}', host],
                capture_output=True, text=True, timeout=10,
            )
        except Exception:
            pass
        # Terminate the managed ControlMaster process
        if self._ctl_proc and self._ctl_proc.poll() is None:
            self._ctl_proc.terminate()
            try:
                self._ctl_proc.wait(timeout=5)
            except Exception:
                self._ctl_proc.kill()
        self._ctl_proc = None
        # Remove stale socket file
        try:
            os.unlink(self._ctl_path)
        except OSError:
            pass
        logger.info("SSH ControlMaster closed: %s", self._ctl_path)
        self._ctl_path = None

    # ── SSH / SCP wrappers (with multiplexing + compression) ─────────
    def _ssh(self, host: str, cmd: str, *,
             password: Optional[str] = None,
             timeout: int = 60) -> str:
        """Run a command on the remote via SSH and return stdout (blocking).

        If a ControlMaster socket is active, tries that first.  On
        timeout, invalidates the dead socket and retries with a direct
        connection so the pipeline is not stuck forever.
        """
        argv = ['ssh', '-C'] + self._ctl_socket_args() + [host, cmd]
        if password and not self._ctl_path:
            argv = ['sshpass', '-p', password] + argv
        try:
            result = subprocess.run(
                argv,
                capture_output=True, text=True, timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            if self._ctl_path:
                logger.warning("SSH via ControlMaster timed out, "
                               "invalidating socket and retrying direct")
                self._invalidate_control_master(host)
                # Retry without the dead socket
                argv = ['ssh', '-C', host, cmd]
                if password:
                    argv = ['sshpass', '-p', password] + argv
                result = subprocess.run(
                    argv,
                    capture_output=True, text=True, timeout=timeout,
                )
            else:
                raise
        if result.returncode != 0:
            raise RuntimeError(
                f"SSH command failed (exit {result.returncode}):\n"
                f"  cmd: {cmd}\n"
                f"  stderr: {result.stderr.strip()}")
        return result.stdout

    def _invalidate_control_master(self, host: str):
        """Kill a dead/stuck ControlMaster and clear the socket path."""
        if not self._ctl_path:
            return
        try:
            subprocess.run(
                ['ssh', '-O', 'exit',
                 '-o', f'ControlPath={self._ctl_path}', host],
                capture_output=True, text=True, timeout=5,
            )
        except Exception:
            pass
        if self._ctl_proc and self._ctl_proc.poll() is None:
            self._ctl_proc.kill()
        self._ctl_proc = None
        try:
            os.unlink(self._ctl_path)
        except OSError:
            pass
        logger.info("Invalidated dead ControlMaster: %s", self._ctl_path)
        self._ctl_path = None

    def _ssh_stream(
        self,
        host: str,
        cmd: str,
        *,
        password: Optional[str] = None,
        progress_cb: Optional[Callable[[str], None]] = None,
        cancel: Optional[threading.Event] = None,
    ) -> str:
        """Run a command on the remote via SSH, streaming stdout lines.

        Each non-empty line from stdout is forwarded to *progress_cb*
        in real time.  Returns the full stdout when the process exits.

        Uses ``-T`` (no PTY) to avoid pseudo-terminal issues on long-
        running batch commands, and ``ServerAliveInterval`` to prevent
        NAT/firewall timeouts from killing the connection.

        On SSH-level failure (exit 255), invalidates the ControlMaster
        socket and retries with a direct connection.
        """
        result = self._ssh_stream_once(
            host, cmd,
            password=password,
            progress_cb=progress_cb,
            cancel=cancel,
            use_control=bool(self._ctl_path),
        )
        if result is not None:
            return result

        # SSH-level failure (exit 255) — invalidate dead socket, retry direct
        if cancel and cancel.is_set():
            raise InterruptedError('Cancelled')
        if self._ctl_path:
            logger.warning("SSH stream via ControlMaster failed (exit 255), "
                           "invalidating socket and retrying direct")
            self._invalidate_control_master(host)
            result = self._ssh_stream_once(
                host, cmd,
                password=password,
                progress_cb=progress_cb,
                cancel=cancel,
                use_control=False,
            )
            if result is not None:
                return result

        raise RuntimeError(
            f"SSH stream command failed after retry:\n"
            f"  cmd: {cmd}")

    def _ssh_stream_once(
        self,
        host: str,
        cmd: str,
        *,
        password: Optional[str] = None,
        progress_cb: Optional[Callable[[str], None]] = None,
        cancel: Optional[threading.Event] = None,
        use_control: bool = True,
    ) -> Optional[str]:
        """Single attempt to run a streaming SSH command.

        Returns the collected stdout on success, or ``None`` on SSH-level
        failure (exit 255) to signal the caller to retry.
        """
        ssh_opts = [
            '-T',  # no PTY — critical for long-running batch commands
            '-C',  # compression
            '-o', 'ServerAliveInterval=30',
            '-o', 'ServerAliveCountMax=3',
        ]
        ctl_args = self._ctl_socket_args() if use_control else []
        argv = ['ssh'] + ssh_opts + ctl_args + [host, cmd]
        if password and not (use_control and self._ctl_path):
            argv = ['sshpass', '-p', password] + argv
        proc = subprocess.Popen(
            argv,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,  # line-buffered
        )
        self._stream_proc = proc
        lines: list[str] = []
        try:
            for line in proc.stdout:              # type: ignore[union-attr]
                lines.append(line)
                stripped = line.strip()
                if stripped and progress_cb:
                    progress_cb(stripped)
                if cancel and cancel.is_set():
                    # Remote kill already sent by cancel(); just clean up local
                    proc.terminate()
                    raise InterruptedError('Cancelled')
        finally:
            self._stream_proc = None
            proc.stdout.close()                   # type: ignore[union-attr]
            proc.wait(timeout=30)

        # If cancelled, the remote kill caused exit 255 — don't retry
        if cancel and cancel.is_set():
            raise InterruptedError('Cancelled')

        if proc.returncode == 255:
            # SSH-level failure — signal retry
            stderr = proc.stderr.read() if proc.stderr else ''
            if proc.stderr:
                proc.stderr.close()
            logger.warning("SSH stream exit 255: %s", stderr.strip())
            return None

        if proc.returncode != 0:
            stderr = proc.stderr.read() if proc.stderr else ''
            if proc.stderr:
                proc.stderr.close()
            raise RuntimeError(
                f"SSH command failed (exit {proc.returncode}):\n"
                f"  cmd: {cmd}\n"
                f"  stderr: {stderr.strip()}")
        if proc.stderr:
            proc.stderr.close()
        return ''.join(lines)

    def _scp_to(self, host: str, local_path: str, remote_path: str,
                *, password: Optional[str] = None):
        """SCP a local file/dir to the remote."""
        argv = ['scp', '-C', '-r'] + self._ctl_socket_args() + \
               [local_path, f'{host}:{remote_path}']
        if password and not self._ctl_path:
            argv = ['sshpass', '-p', password] + argv
        try:
            result = subprocess.run(
                argv,
                capture_output=True, text=True, timeout=120,
            )
        except subprocess.TimeoutExpired:
            if self._ctl_path:
                logger.warning("SCP via ControlMaster timed out, retrying direct")
                self._invalidate_control_master(host)
                argv = ['scp', '-C', '-r', local_path, f'{host}:{remote_path}']
                if password:
                    argv = ['sshpass', '-p', password] + argv
                result = subprocess.run(
                    argv,
                    capture_output=True, text=True, timeout=120,
                )
            else:
                raise
        if result.returncode != 0:
            raise RuntimeError(f"SCP upload failed: {result.stderr.strip()}")

    def _scp_from(self, host: str, remote_path: str, local_path: str,
                  *, password: Optional[str] = None):
        """SCP a remote file/dir to local."""
        argv = ['scp', '-C', '-r'] + self._ctl_socket_args() + \
               [f'{host}:{remote_path}', local_path]
        if password and not self._ctl_path:
            argv = ['sshpass', '-p', password] + argv
        result = subprocess.run(
            argv,
            capture_output=True, text=True, timeout=600,
        )
        if result.returncode != 0:
            raise RuntimeError(f"SCP download failed: {result.stderr.strip()}")

    def _fetch_results_tar(self, host: str, remote_dir: str,
                           local_dir: str, *,
                           password: Optional[str] = None):
        """Fetch a remote directory via ``tar cz | tar xz`` over SSH.

        This is dramatically faster than ``scp -r`` over WAN because:
        - Single data stream (no per-file round-trips)
        - gzip compression on the wire
        - Reuses the ControlMaster connection
        Falls back to ``scp -r`` if tar piping fails.
        """
        os.makedirs(local_dir, exist_ok=True)
        parent = str(Path(remote_dir).parent)
        name = Path(remote_dir).name
        tar_cmd = f"tar czf - -C {parent} {name}"

        argv = ['ssh', '-C'] + self._ctl_socket_args() + [host, tar_cmd]
        if password and not self._ctl_path:
            argv = ['sshpass', '-p', password] + argv

        try:
            remote_proc = subprocess.Popen(
                argv,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            local_proc = subprocess.Popen(
                ['tar', 'xzf', '-', '-C', str(Path(local_dir).parent)],
                stdin=remote_proc.stdout,
                stderr=subprocess.PIPE,
            )
            remote_proc.stdout.close()  # type: ignore[union-attr]
            _, local_err = local_proc.communicate(timeout=600)
            remote_proc.wait(timeout=30)

            if remote_proc.returncode != 0 or local_proc.returncode != 0:
                remote_err = remote_proc.stderr.read() if remote_proc.stderr else b''
                remote_proc.stderr.close() if remote_proc.stderr else None
                raise RuntimeError(
                    f"tar fetch failed: remote={remote_err.decode().strip()}, "
                    f"local={local_err.decode().strip()}")
            if remote_proc.stderr:
                remote_proc.stderr.close()
            logger.info("Results fetched via tar pipe: %s", local_dir)
        except Exception as e:
            logger.warning("tar pipe failed (%s), falling back to scp -r", e)
            # Clean up partial extraction
            if os.path.isdir(local_dir):
                shutil.rmtree(local_dir, ignore_errors=True)
            self._scp_from(host, remote_dir, local_dir, password=password)

    @staticmethod
    def _parse_results_dir(output: str) -> Optional[str]:
        """Extract the run directory from CLI output like ``Results: /path/to/run_xxx``."""
        for line in reversed(output.splitlines()):
            m = re.match(r'^Results:\s+(.+)$', line.strip())
            if m:
                return m.group(1).strip()
        return None
