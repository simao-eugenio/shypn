"""SHYpn package entry point.

Supports two launch modes:

  python -m shypn            → launch the GUI (same as python src/shypn.py)
  python -m shypn --check    → headless install verification (no display needed)
  shypn                      → same as python -m shypn (after pip install)
  shypn --check              → same as python -m shypn --check
"""
import os
import sys


def _check() -> int:
    """Headless installation verification.  No GTK or display required."""
    import importlib
    import importlib.util

    GREEN  = '\033[0;32m'
    RED    = '\033[0;31m'
    YELLOW = '\033[1;33m'
    BOLD   = '\033[1m'
    RESET  = '\033[0m'

    ok   = lambda msg: print(f"  {GREEN}✓{RESET}  {msg}")
    fail = lambda msg: print(f"  {RED}✗{RESET}  {msg}")
    warn = lambda msg: print(f"  {YELLOW}⚠{RESET}  {msg}")

    errors = 0

    print(f"\n{BOLD}SHYpn — installation check{RESET}")
    print(f"  {'Python':<22} {sys.version.split()[0]}")

    # ── third-party scientific stack ──────────────────────────────────────────
    REQUIRED = {
        'numpy':       '1.24',
        'scipy':       '1.10',
        'matplotlib':  '3.6',
        'networkx':    '2.8',
        'openpyxl':    '3.1',
        'platformdirs':'4.0',
        'defusedxml':  '0.7',
    }
    print()
    for mod, min_ver in REQUIRED.items():
        try:
            m = importlib.import_module(mod)
            ver = getattr(m, '__version__', '?')
            ok(f"{mod:<22} {ver}")
        except ImportError as exc:
            fail(f"{mod:<22} NOT FOUND  ({exc})")
            errors += 1

    # ── GTK3 / GObject introspection ──────────────────────────────────────────
    print()
    try:
        import gi
        gi.require_version('Gtk', '3.0')
        gi.require_version('Gdk', '3.0')
        from gi.repository import Gtk  # noqa: F401 — import only to confirm
        gtk_ver = f"{Gtk.MAJOR_VERSION}.{Gtk.MINOR_VERSION}.{Gtk.MICRO_VERSION}"
        ok(f"{'gi (GTK3)':<22} {gtk_ver}")
    except Exception as exc:
        fail(f"{'gi (GTK3)':<22} NOT FOUND  ({exc})")
        errors += 1

    # ── SHYpn core modules ────────────────────────────────────────────────────
    print()
    SHYPN_MODULES = [
        'shypn.version',
        'shypn.engine.simulation.controller',
        'shypn.engine.simulation.tau_leaping.tau_leaping_engine',
        'shypn.netobjs.place',
        'shypn.netobjs.transition',
        'shypn.netobjs.arc',
        'shypn.data.canvas.document_model',
    ]
    for mod in SHYPN_MODULES:
        try:
            importlib.import_module(mod)
            ok(f"{mod}")
        except Exception as exc:
            fail(f"{mod}  ({exc})")
            errors += 1

    # ── optional accelerator ──────────────────────────────────────────────────
    print()
    try:
        import numba  # noqa: F401
        ok(f"{'numba (optional)':<22} {numba.__version__}")
    except ImportError:
        warn(f"{'numba (optional)':<22} not installed  (pip install shypn[acceleration])")

    try:
        import cupy  # noqa: F401
        ok(f"{'cupy (optional)':<22} {cupy.__version__}  (GPU path enabled)")
    except ImportError:
        warn(f"{'cupy (optional)':<22} not installed  (GPU path disabled)")

    # ── display environment ───────────────────────────────────────────────────
    print()
    display    = os.environ.get('DISPLAY', '')
    wayland    = os.environ.get('WAYLAND_DISPLAY', '')
    if display or wayland:
        display_str = display or f"wayland:{wayland}"
        ok(f"{'Display':<22} {display_str}  (GUI can start)")
    else:
        warn(f"{'Display':<22} not set  "
             "(headless session — GUI needs a desktop login or DISPLAY=:0)")

    # ── SHYpn version ─────────────────────────────────────────────────────────
    print()
    try:
        from shypn.version import __version__
        ok(f"SHYpn {__version__}")
    except Exception:
        pass

    print()
    if errors == 0:
        print(f"  {GREEN}{BOLD}All checks passed.{RESET}  "
              "Run 'shypn' (or 'python src/shypn.py') to launch.")
    else:
        print(f"  {RED}{BOLD}{errors} check(s) failed.{RESET}  "
              "See INSTALL.md → Troubleshooting.")
    print()
    return 0 if errors == 0 else 1


def _launch_gui(argv=None) -> int:
    """Launch the SHYpn GUI by running src/shypn.py.

    Strategy:
      - For an editable install (git clone + pip install -e .):
        src/shypn.py is at  <pkg_parent>/../shypn.py  relative to this file.
        We locate it via __file__ and execute it with runpy.
      - For a non-editable install (pip install from zip):
        src/shypn.py is not shipped; print a helpful error.
    """
    import runpy

    # this file → src/shypn/__main__.py
    # pkg dir   → src/shypn/
    # src dir   → src/
    # launcher  → src/shypn.py
    pkg_dir  = os.path.dirname(os.path.abspath(__file__))   # …/src/shypn
    src_dir  = os.path.dirname(pkg_dir)                     # …/src
    launcher = os.path.join(src_dir, 'shypn.py')

    if not os.path.isfile(launcher):
        print(
            "error: src/shypn.py not found at expected path:\n"
            f"  {launcher}\n\n"
            "If you installed from a zip archive (non-editable install),\n"
            "run the GUI directly from the extracted directory:\n"
            "  python src/shypn.py\n\n"
            "For the full experience, clone the repo and use an editable install:\n"
            "  git clone https://github.com/simao-eugenio/shypn.git\n"
            "  cd shypn && bash install_ubuntu.sh",
            file=sys.stderr,
        )
        return 2

    if argv is not None:
        sys.argv = argv
    runpy.run_path(launcher, run_name='__main__')
    return 0


def main(argv=None) -> int:
    if argv is None:
        argv = sys.argv[:]

    if '--check' in argv:
        return _check()
    return _launch_gui(argv)


if __name__ == '__main__':
    sys.exit(main())
