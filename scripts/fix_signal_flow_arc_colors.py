#!/usr/bin/env python3
"""Fix SignalFlowArc colors in saved models.

This script loads all .shypn files in the workspace and fixes any SignalFlowArcs
that have incorrect black color (0.0, 0.0, 0.0) by resetting them to the correct
light gray color (0.7, 0.7, 0.7).

The issue occurred because:
1. SignalFlowArc instances were created with correct light gray color
2. When saved, they inherited the base Arc color (black) 
3. On reload, the saved black color overwrote the correct light gray

This has been fixed by adding SignalFlowArc.to_dict() which ensures the correct
color is always saved.

Usage:
    python fix_signal_flow_arc_colors.py [directory]
    
    If no directory is specified, scans workspace/ and test_output/
"""

import os
import sys
import json
from pathlib import Path


def fix_signal_flow_arc_colors(file_path: str, dry_run: bool = False) -> tuple[int, int]:
    """Fix SignalFlowArc colors in a single file.
    
    Args:
        file_path: Path to .shypn file
        dry_run: If True, only report changes without modifying file
        
    Returns:
        Tuple of (total_signal_flow_arcs, fixed_arcs)
    """
    try:
        with open(file_path, 'r') as f:
            data = json.load(f)
    except Exception as e:
        print(f"  [ERROR] Failed to load {file_path}: {e}")
        return 0, 0
    
    arcs = data.get('arcs', [])
    signal_flow_count = 0
    fixed_count = 0
    
    LIGHT_GRAY = [0.7, 0.7, 0.7]
    BLACK = [0.0, 0.0, 0.0]
    
    for arc in arcs:
        # Check if this is a signal_flow arc
        if arc.get('arc_type') == 'signal_flow':
            signal_flow_count += 1
            
            # Check if color is black (incorrect)
            color = arc.get('color', BLACK)
            if color == BLACK or tuple(color) == (0.0, 0.0, 0.0):
                fixed_count += 1
                arc['color'] = LIGHT_GRAY
                if not dry_run:
                    print(f"    Fixed arc {arc.get('id', '?')}: {arc.get('name', '?')}")
    
    # Save file if changes were made
    if fixed_count > 0 and not dry_run:
        try:
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"  [SAVED] {file_path}")
        except Exception as e:
            print(f"  [ERROR] Failed to save {file_path}: {e}")
    
    return signal_flow_count, fixed_count


def scan_directory(directory: str, dry_run: bool = False):
    """Scan directory for .shypn files and fix SignalFlowArc colors.
    
    Args:
        directory: Directory to scan recursively
        dry_run: If True, only report changes without modifying files
    """
    directory_path = Path(directory)
    if not directory_path.exists():
        print(f"[SKIP] Directory does not exist: {directory}")
        return
    
    print(f"\n{'='*70}")
    print(f"Scanning: {directory}")
    print(f"{'='*70}")
    
    shypn_files = list(directory_path.rglob('*.shypn'))
    
    if not shypn_files:
        print(f"No .shypn files found in {directory}")
        return
    
    total_files = len(shypn_files)
    total_signal_arcs = 0
    total_fixed = 0
    files_with_fixes = 0
    
    for file_path in shypn_files:
        signal_count, fixed_count = fix_signal_flow_arc_colors(str(file_path), dry_run=dry_run)
        
        if signal_count > 0:
            total_signal_arcs += signal_count
            
            if fixed_count > 0:
                files_with_fixes += 1
                total_fixed += fixed_count
                action = "[DRY-RUN]" if dry_run else "[FIXED]"
                print(f"{action} {file_path.name}: {fixed_count}/{signal_count} signal flow arcs")
    
    print(f"\n{'-'*70}")
    print(f"Summary for {directory}:")
    print(f"  Total files scanned: {total_files}")
    print(f"  Files with signal flow arcs: {files_with_fixes}")
    print(f"  Total signal flow arcs: {total_signal_arcs}")
    print(f"  Total arcs fixed: {total_fixed}")
    if dry_run:
        print(f"  (DRY RUN - no files modified)")
    print(f"{'-'*70}")


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Fix SignalFlowArc colors in saved models'
    )
    parser.add_argument(
        'directories',
        nargs='*',
        default=['workspace', 'test_output'],
        help='Directories to scan (default: workspace test_output)'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Report changes without modifying files'
    )
    
    args = parser.parse_args()
    
    print("\n" + "="*70)
    print("SignalFlowArc Color Fixer")
    print("="*70)
    print("\nThis script fixes SignalFlowArcs with incorrect black color.")
    print("Correct color: (0.7, 0.7, 0.7) - Light gray")
    print("Incorrect color: (0.0, 0.0, 0.0) - Black")
    
    if args.dry_run:
        print("\n[DRY RUN MODE] - No files will be modified")
    
    for directory in args.directories:
        scan_directory(directory, dry_run=args.dry_run)
    
    print("\n" + "="*70)
    print("Done!")
    print("="*70)


if __name__ == '__main__':
    main()
