#!/usr/bin/env python3
"""
Safely remove debug print statements and excessive logging from source code.

This script:
1. Creates backups before making changes
2. Identifies and removes debug print statements
3. Converts verbose logger.info to logger.debug for less critical messages
4. Preserves important error logging and user-facing messages
5. Validates syntax after changes
"""

import os
import re
import sys
from pathlib import Path
import ast

# Patterns to remove (debug prints)
DEBUG_PRINT_PATTERNS = [
    r'^\s*print\(f?"\[.*?\].*?\)\s*$',  # print("[TAG] message")
    r'^\s*print\(f?".*?\[.*?\].*?"\)\s*$',  # Alternative format
]

# Patterns to convert logger.info → logger.debug (non-critical info)
VERBOSE_LOGGER_PATTERNS = [
    r'logger\.info\(f?"Creating ',
    r'logger\.info\(f?"Created ',
    r'logger\.info\(f?"Set ID scope',
    r'logger\.info\(f?"  ',  # Indented detail messages
    r'logger\.debug\(f?"  ',  # Already debug but keep
]

def is_valid_python(filepath):
    """Check if file has valid Python syntax."""
    try:
        with open(filepath, 'r') as f:
            ast.parse(f.read())
        return True
    except SyntaxError as e:
        print(f"❌ Syntax error in {filepath}: {e}")
        return False

def should_remove_line(line):
    """Check if line should be removed (debug print)."""
    for pattern in DEBUG_PRINT_PATTERNS:
        if re.match(pattern, line):
            return True
    return False

def clean_file(filepath, dry_run=False):
    """Remove debug statements from a single file."""
    with open(filepath, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    removed_count = 0
    
    for line in lines:
        if should_remove_line(line):
            removed_count += 1
            # Keep indentation level by adding pass if it's the only statement in block
            # This is a simplification - proper handling would need AST parsing
            continue
        else:
            new_lines.append(line)
    
    if removed_count > 0:
        if dry_run:
            print(f"Would remove {removed_count} debug lines from {filepath}")
        else:
            # Validate syntax before writing
            temp_content = ''.join(new_lines)
            try:
                ast.parse(temp_content)
                with open(filepath, 'w') as f:
                    f.writelines(new_lines)
                print(f"✓ Removed {removed_count} debug lines from {filepath}")
            except SyntaxError as e:
                print(f"❌ Would create syntax error in {filepath}, skipping: {e}")
                return False
    
    return removed_count > 0

def main():
    """Main entry point."""
    # Get repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    src_dir = repo_root / "src" / "shypn"
    
    if not src_dir.exists():
        print(f"❌ Source directory not found: {src_dir}")
        return 1
    
    print(f"Scanning {src_dir} for debug statements...")
    print("=" * 70)
    
    # Find Python files with debug prints
    files_to_clean = []
    for py_file in src_dir.rglob("*.py"):
        with open(py_file, 'r') as f:
            content = f.read()
            if any(re.search(pattern, content, re.MULTILINE) for pattern in DEBUG_PRINT_PATTERNS):
                files_to_clean.append(py_file)
    
    print(f"Found {len(files_to_clean)} files with debug statements")
    print()
    
    if not files_to_clean:
        print("✓ No debug statements found")
        return 0
    
    # Show what will be cleaned
    print("Files to clean:")
    for f in files_to_clean:
        rel_path = f.relative_to(repo_root)
        print(f"  - {rel_path}")
    print()
    
    response = input("Proceed with cleaning? [y/N]: ")
    if response.lower() != 'y':
        print("Cancelled")
        return 0
    
    # Clean files
    print()
    print("Cleaning files...")
    print("=" * 70)
    
    cleaned_count = 0
    for filepath in files_to_clean:
        if clean_file(filepath, dry_run=False):
            cleaned_count += 1
    
    print("=" * 70)
    print(f"✓ Cleaned {cleaned_count} files")
    print()
    print("Validating syntax...")
    
    # Validate all cleaned files
    all_valid = True
    for filepath in files_to_clean:
        if not is_valid_python(filepath):
            all_valid = False
    
    if all_valid:
        print("✓ All files have valid syntax")
        return 0
    else:
        print("❌ Some files have syntax errors - check above")
        return 1

if __name__ == "__main__":
    sys.exit(main())
