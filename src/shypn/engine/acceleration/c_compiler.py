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

# Compiler flags:  -O3 for max speed, -ffast-math for Arrhenius exp() speed
_GCC_FLAGS = [
    "-O3",
    "-ffast-math",
    "-fPIC",
    "-shared",
    "-std=c99",
    "-lm",
]

_CACHE_BASE = Path.home() / ".cache" / "shypn" / "ode_accel"


def _source_hash(c_source: str) -> str:
    """Return a 16-char hex digest of the C source string."""
    return hashlib.sha256(c_source.encode()).hexdigest()[:16]


def _cache_dir(model_hash: str) -> Path:
    return _CACHE_BASE / model_hash


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
        logger.debug("ODE accel: using cached .so at %s", so)
        return so

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

    cmd = [gcc] + _GCC_FLAGS + ["-o", str(so), str(src)]
    logger.info("ODE accel: compiling %s …", src.name)
    logger.debug("ODE accel: cmd = %s", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        # Preserve source for debugging
        logger.error("ODE accel: compilation FAILED\n%s", result.stderr)
        raise RuntimeError(
            f"gcc compilation failed (exit {result.returncode}):\n"
            f"{result.stderr}\n"
            f"Source preserved at: {src}"
        )

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
        logger.debug("C accel: using cached .so at %s", so)
        return so

    cache.mkdir(parents=True, exist_ok=True)
    src.write_text(c_source)

    gcc = shutil.which("gcc")
    if gcc is None:
        raise RuntimeError(
            "gcc not found in PATH.  Install gcc to use acceleration "
            "(e.g. 'sudo apt install gcc' on Debian/Ubuntu)."
        )

    cmd = [gcc] + _GCC_FLAGS + ["-o", str(so), str(src)]
    logger.info("C accel: compiling %s …", src.name)
    logger.debug("C accel: cmd = %s", " ".join(cmd))

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        logger.error("C accel: compilation FAILED\n%s", result.stderr)
        raise RuntimeError(
            f"gcc compilation failed (exit {result.returncode}):\n"
            f"{result.stderr}\n"
            f"Source preserved at: {src}"
        )

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
