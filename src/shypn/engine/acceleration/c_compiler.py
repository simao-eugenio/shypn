"""Compile generated C source to a shared library (.so) via gcc.

Compiled libraries are cached in ``~/.cache/shypn/ode_accel/`` indexed by
a SHA-256 hash of the source code.  Re-compilation only occurs when the
generated code changes (i.e., model structure or rate expressions changed).

Usage::

    from shypn.engine.acceleration.c_compiler import compile_ode_rhs

    so_path = compile_ode_rhs(c_source_code, model_hash)
    # → "/home/user/.cache/shypn/ode_accel/<hash>/ode_rhs.so"
"""

import hashlib
import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Compiler flags:
#   -O3             maximum optimisation
#   -march=native   enable AVX2/FMA auto-vectorisation on the build machine
#   -funroll-loops  unroll the fixed-size propensity / ODE loops
#   -ffast-math     allow reassociation / fast exp() — safe for rate expressions
_GCC_FLAGS = [
    "-O3",
    "-march=native",
    "-funroll-loops",
    "-ffast-math",
    "-fPIC",
    "-shared",
    "-std=c99",
    "-lm",
]

# Fallback flags used when -march=native is not supported by the host gcc
# (e.g. cross-compilation or very old gcc versions).
_GCC_FLAGS_SAFE = [
    "-O3",
    "-funroll-loops",
    "-ffast-math",
    "-fPIC",
    "-shared",
    "-std=c99",
    "-lm",
]

# A short tag derived from the active flags set.
# Embedding this in the cache directory name ensures that changing flags
# (e.g. adding -march=native) triggers automatic recompilation instead of
# silently reusing a stale .so built with different flags.
_FLAGS_HASH: str = hashlib.md5(" ".join(_GCC_FLAGS).encode()).hexdigest()[:6]

_CACHE_BASE = Path.home() / ".cache" / "shypn" / "ode_accel"


def _source_hash(c_source: str) -> str:
    """Return a 16-char hex digest of the C source string."""
    return hashlib.sha256(c_source.encode()).hexdigest()[:16]


_ELF_MAGIC = b"\x7fELF"


def _is_valid_elf(path: Path) -> bool:
    """Return True iff *path* looks like a valid ELF shared library.

    Checks:
    - File exists and is non-empty
    - Starts with the ELF magic bytes (\x7fELF)
    - At least one PT_LOAD segment is present (offset 0x18-0x1f in ELF header
      points to program-header table; we just confirm the file is large enough
      to plausibly contain one — 4 KB minimum for a real .so)

    The two failure modes seen in practice are:
    - ``file too short``                  → file exists but has 0–few bytes
    - ``object file has no loadable segments`` → partial ELF, no PT_LOAD

    Both are caught by the ELF-magic + size check below.
    """
    try:
        size = path.stat().st_size
        if size < 4096:
            return False
        with path.open("rb") as fh:
            magic = fh.read(4)
        return magic == _ELF_MAGIC
    except OSError:
        return False


def _cache_dir(model_hash: str) -> Path:
    # Include the flags tag so any change to _GCC_FLAGS causes a fresh directory
    # (and therefore a fresh compilation) without manual cache clearing.
    return _CACHE_BASE / f"{model_hash}_{_FLAGS_HASH}"


def _so_path(model_hash: str) -> Path:
    return _cache_dir(model_hash) / "ode_rhs.so"


def _src_path(model_hash: str) -> Path:
    return _cache_dir(model_hash) / "ode_rhs.c"


def is_cached(model_hash: str) -> bool:
    """True if a compiled .so already exists for *model_hash*."""
    return _so_path(model_hash).exists()


def compile_ode_rhs(
    c_source: str,
    *,
    model_hash: Optional[str] = None,
    force: bool = False,
) -> Path:
    """Compile *c_source* to a shared library and return its path.

    Parameters
    ----------
    c_source:
        Full C source code (must define ``void ode_rhs(…)``).
    model_hash:
        Identifier for cache lookup.  Defaults to SHA-256 of *c_source*.
    force:
        Recompile even if a cached .so exists.

    Returns
    -------
    Path
        Absolute path to the compiled ``.so``.

    Raises
    ------
    RuntimeError
        If gcc is not found or compilation fails.
    """
    if model_hash is None:
        model_hash = _source_hash(c_source)

    so = _so_path(model_hash)

    if so.exists() and not force:
        if _is_valid_elf(so):
            logger.debug("ODE accel: using cached .so at %s", so)
            return so
        logger.warning(
            "ODE accel: cached .so at %s appears corrupt (bad ELF / too small). "
            "Deleting and recompiling.",
            so,
        )
        so.unlink()

    # Create cache directory
    cache = _cache_dir(model_hash)
    cache.mkdir(parents=True, exist_ok=True)

    # Write C source
    src = _src_path(model_hash)
    src.write_text(c_source)

    # Locate gcc
    gcc = shutil.which("gcc")
    if gcc is None:
        raise RuntimeError(
            "gcc not found in PATH.  Install gcc to use ODE acceleration "
            "(e.g. 'sudo apt install gcc' on Debian/Ubuntu)."
        )

    def _try_compile(flags: list) -> subprocess.CompletedProcess:
        return subprocess.run(
            [gcc] + flags + ["-o", str(so_tmp), str(src)],
            capture_output=True, text=True,
        )

    # Compile to a temp file first so that concurrent workers never see a
    # partial ELF at the final path (ctypes.CDLL fails with "file too short"
    # when it tries to load a .so that gcc is still writing).
    so_tmp = so.with_suffix(".so.tmp")

    cmd_flags = _GCC_FLAGS
    logger.info("ODE accel: compiling %s (flags: %s) …", src.name, " ".join(cmd_flags))
    result = _try_compile(cmd_flags)

    # If -march=native caused a failure (rare: old gcc or cross-compile env),
    # retry with the safe fallback flags before giving up.
    if result.returncode != 0 and "-march=native" in cmd_flags:
        logger.warning(
            "ODE accel: compilation with -march=native failed; retrying with safe flags.\n%s",
            result.stderr,
        )
        cmd_flags = _GCC_FLAGS_SAFE
        result = _try_compile(cmd_flags)

    if result.returncode != 0:
        # Preserve source for debugging
        logger.error("ODE accel: compilation FAILED\n%s", result.stderr)
        so_tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"gcc compilation failed (exit {result.returncode}):\n"
            f"{result.stderr}\n"
            f"Source preserved at: {src}"
        )

    # Atomic rename: the final path is either absent or a complete .so.
    # os.replace is atomic on the same filesystem (POSIX rename semantics).
    so_tmp.replace(so)
    logger.info("ODE accel: compiled successfully → %s", so)
    return so


def compile_c_lib(
    c_source: str,
    lib_name: str = "lib",
    *,
    model_hash: Optional[str] = None,
    force: bool = False,
) -> Path:
    """Generic version of ``compile_ode_rhs`` for any C source / library name.

    Compiles *c_source* to ``~/.cache/shypn/ode_accel/<hash>/<lib_name>.so``
    and returns the path.  The cache is keyed by the SHA-256 of the source
    string, then the ``<lib_name>`` suffix distinguishes different functions
    that live under the same cache directory.

    Parameters
    ----------
    c_source:
        Full C source code.
    lib_name:
        Base name for the ``.so`` file (no extension, no path).
    model_hash:
        Optional explicit hash prefix.  Defaults to the SHA-256 of *c_source*.
    force:
        Recompile even if a cached ``.so`` already exists.
    """
    if model_hash is None:
        model_hash = _source_hash(c_source)

    # Unique subdirectory per hash; unique filenames per lib_name inside it
    cache = _cache_dir(model_hash)
    so  = cache / f"{lib_name}.so"
    src = cache / f"{lib_name}.c"

    if so.exists() and not force:
        if _is_valid_elf(so):
            logger.debug("C accel: using cached .so at %s", so)
            return so
        logger.warning(
            "C accel: cached .so at %s appears corrupt (bad ELF / too small). "
            "Deleting and recompiling.",
            so,
        )
        so.unlink()

    cache.mkdir(parents=True, exist_ok=True)
    src.write_text(c_source)

    gcc = shutil.which("gcc")
    if gcc is None:
        raise RuntimeError(
            "gcc not found in PATH.  Install gcc to use acceleration "
            "(e.g. 'sudo apt install gcc' on Debian/Ubuntu)."
        )

    def _try_compile(flags: list) -> subprocess.CompletedProcess:
        return subprocess.run(
            [gcc] + flags + ["-o", str(so_tmp), str(src)],
            capture_output=True, text=True,
        )

    # Compile to a temp file first (atomic rename — prevents "file too short").
    so_tmp = so.with_suffix(".so.tmp")

    cmd_flags = _GCC_FLAGS
    logger.info("C accel: compiling %s (flags: %s) …", src.name, " ".join(cmd_flags))
    result = _try_compile(cmd_flags)

    if result.returncode != 0 and "-march=native" in cmd_flags:
        logger.warning(
            "C accel: compilation with -march=native failed; retrying with safe flags.\n%s",
            result.stderr,
        )
        cmd_flags = _GCC_FLAGS_SAFE
        result = _try_compile(cmd_flags)

    if result.returncode != 0:
        logger.error("C accel: compilation FAILED\n%s", result.stderr)
        so_tmp.unlink(missing_ok=True)
        raise RuntimeError(
            f"gcc compilation failed (exit {result.returncode}):\n"
            f"{result.stderr}\n"
            f"Source preserved at: {src}"
        )

    so_tmp.replace(so)
    logger.info("C accel: compiled successfully → %s", so)
    return so


def clear_cache(model_hash: Optional[str] = None) -> None:
    """Remove cached .so files.

    If *model_hash* is given, removes only that entry; otherwise clears all.
    """
    if model_hash:
        d = _cache_dir(model_hash)
        if d.exists():
            shutil.rmtree(d)
    else:
        if _CACHE_BASE.exists():
            shutil.rmtree(_CACHE_BASE)
