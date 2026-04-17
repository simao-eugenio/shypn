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
        '--model', '-m',
        required=True,
        type=Path,
        help='Path to .shy model file.',
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
        default=Path('results'),
        help='Output directory for results (default: results/).',
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


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    # Validate inputs
    if not args.model.exists():
        print(f"Error: model file not found: {args.model}", file=sys.stderr)
        return 1
    if not args.sweep.exists():
        print(f"Error: sweep config not found: {args.sweep}", file=sys.stderr)
        return 1

    # Load sweep config
    try:
        config = SweepConfig.load(args.sweep)
    except (json.JSONDecodeError, ValueError, KeyError) as exc:
        print(f"Error: invalid sweep config: {exc}", file=sys.stderr)
        return 1

    runner = SweepRunner(
        model_path=args.model,
        config=config,
        output_dir=args.output,
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
