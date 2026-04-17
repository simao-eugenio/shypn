"""CLI entry point for headless sweep execution.

Usage::

    python -m shypn.cli.sweep --model model.shy --sweep config.json --output results/
    python -m shypn.cli.sweep --model model.shy --sweep config.json --dry-run
    python -m shypn.cli.sweep --model model.shy --sweep config.json --workers 24

See ``python -m shypn.cli.sweep --help`` for the full option reference.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from shypn.cli.sweep_config import SweepConfig
from shypn.cli.sweep_runner import SweepRunner


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog='python -m shypn.cli.sweep',
        description='Run parametric sweeps on SHYpn models (headless).',
    )
    p.add_argument(
        '--project', '-p',
        type=Path,
        default=None,
        help='Project folder (all relative paths resolve from here).',
    )
    p.add_argument(
        '--model', '-m',
        type=Path,
        default=None,
        help='Path to .shy model file (overrides sweep config model_path).',
    )
    p.add_argument(
        '--sweep', '-s',
        required=True,
        type=Path,
        help='Path to sweep configuration JSON file.',
    )
    p.add_argument(
        '--output', '-o',
        type=Path,
        default=None,
        help='Output directory for results (default: <project>/experiments/results/).',
    )
    p.add_argument(
        '--workers', '-w',
        type=int,
        default=None,
        help='Number of parallel worker processes (default: auto).',
    )
    p.add_argument(
        '--dry-run',
        action='store_true',
        help='Print sweep plan without running simulations.',
    )
    p.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Print progress messages.',
    )
    return p


def _resolve_path(path: Path, project: Path | None) -> Path:
    """Resolve a path: if relative, anchor to project folder."""
    if path.is_absolute():
        return path
    if project is not None:
        return project / path
    return path


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    project: Path | None = args.project

    # Load sweep config (resolve relative to project if given)
    sweep_path = _resolve_path(args.sweep, project)
    if not sweep_path.exists():
        print(f"Error: sweep config not found: {sweep_path}", file=sys.stderr)
        return 1

    try:
        config = SweepConfig.load(sweep_path)
    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        print(f"Error: invalid sweep config: {exc}", file=sys.stderr)
        return 1

    # Model: CLI flag > sweep config "model_path" > error
    model_path: Path | None = args.model
    if model_path is None and hasattr(config, '_raw_model_path'):
        model_path = Path(config._raw_model_path)
    if model_path is None:
        print("Error: no model specified (use --model or include model_path in sweep config)", file=sys.stderr)
        return 1
    model_path = _resolve_path(model_path, project)
    if not model_path.exists():
        print(f"Error: model file not found: {model_path}", file=sys.stderr)
        return 1

    # Output: CLI flag > project/experiments/results > ./results
    output_dir = args.output
    if output_dir is None:
        if project is not None:
            output_dir = project / 'experiments' / 'results'
        else:
            output_dir = Path('results')
    else:
        output_dir = _resolve_path(output_dir, project)

    runner = SweepRunner(
        model_path=model_path,
        config=config,
        output_dir=output_dir,
        workers=args.workers,
        verbose=args.verbose or args.dry_run,
    )

    if args.dry_run:
        runner.dry_run()
        return 0

    try:
        run_dir = runner.run()
        print(f"Results: {run_dir}")
    except Exception as exc:
        import traceback; traceback.print_exc(file=sys.stderr)
        return 1

    return 0


if __name__ == '__main__':
    sys.exit(main())
