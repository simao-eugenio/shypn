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

import json
import logging
import os
import re
import shutil
import subprocess
import tempfile
import threading
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

logger = logging.getLogger(__name__)


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
        Only the **sweep config** (~1–5 KB JSON) is transferred over
        SCP.  Results are fetched back as a single compressed tar
        stream.  The user is responsible for keeping the model and
        engine code synced between client and server before dispatch.
    """

    def __init__(self, settings: RemoteSweepSettings):
        self.settings = settings
        self._cancel = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._ctl_path: Optional[str] = None  # SSH ControlMaster socket

    @property
    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def cancel(self):
        """Request cancellation of a running dispatch."""
        self._cancel.set()

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
        self._thread = threading.Thread(
            target=self._run_pipeline,
            args=(model_filepath, project_folder, experiment_manager,
                  sim_params, progress_cb, complete_cb, ssh_password),
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

            # ── 2. Export sweep config (local temp) ──────────────────
            self._emit(progress_cb, 'Exporting sweep config...')
            staging = Path(tempfile.mkdtemp(prefix='shypn_remote_'))
            config_path = staging / 'sweep_config.json'
            experiment_manager.export_sweep_config(
                filepath=str(config_path),
                model_path=model_rel_to_project,
                **sim_params,
            )

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

            if self._cancel.is_set():
                raise InterruptedError('Cancelled')

            # ── 3. SSH run CLI on remote ─────────────────────────────
            self._emit(progress_cb, 'Running sweep on remote server...')

            workers_flag = f"--workers {workers}" if workers > 0 else ""
            # Use 'exec' so Python replaces the bash process, becoming
            # sshd's direct child.  Combined with process_guard's
            # PR_SET_PDEATHSIG + watchdog, this ensures the process dies
            # cleanly when the SSH connection drops (no orphan zombies).
            remote_cmd = (
                f"cd {remote_repo} && "
                f"export PYTHONPATH=$PWD/src && "
                f"exec {remote_venv} -m shypn.cli.sweep "
                f"--project {project_rel} "
                f"--sweep sweep_config.json "
                f"{workers_flag} "
                f"--verbose"
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
            self._emit(progress_cb, 'Fetching results from remote...')

            run_name = Path(run_dir).name
            local_results_base = project_abs / 'experiments' / 'results'
            local_results_base.mkdir(parents=True, exist_ok=True)
            local_run_dir = local_results_base / run_name

            self._fetch_results_tar(host, run_dir, str(local_run_dir),
                                    password=ssh_password)

            # ── 5. Done ──────────────────────────────────────────────
            self._emit(progress_cb, f'Done — results at {local_run_dir.name}')

            if complete_cb:
                complete_cb(True, str(local_run_dir), f'Sweep complete: {run_name}')

        except InterruptedError:
            if complete_cb:
                complete_cb(False, '', 'Remote sweep cancelled.')
        except Exception as e:
            logger.exception("Remote sweep failed")
            if complete_cb:
                complete_cb(False, '', str(e))
        finally:
            self._close_control_master(host)
            if staging and staging.exists():
                shutil.rmtree(staging, ignore_errors=True)

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
            '-f',  # fork to background after auth
            '-N',  # no remote command
            host,
        ]
        if password:
            argv = ['sshpass', '-p', password] + argv
        result = subprocess.run(
            argv,
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            logger.warning("ControlMaster failed (%s), falling back to "
                           "per-command connections", result.stderr.strip())
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
            # Clean up the dead socket
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
        lines: list[str] = []
        try:
            for line in proc.stdout:              # type: ignore[union-attr]
                lines.append(line)
                stripped = line.strip()
                if stripped and progress_cb:
                    progress_cb(stripped)
                if cancel and cancel.is_set():
                    proc.terminate()
                    raise InterruptedError('Cancelled')
        finally:
            proc.stdout.close()                   # type: ignore[union-attr]
            proc.wait(timeout=30)

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
