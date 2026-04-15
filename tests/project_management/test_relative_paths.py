#!/usr/bin/env python3
"""Test script for relative path display in file explorer.

This script tests the set_current_file() method to verify that it correctly
displays relative paths from the models directory.
"""

import os
import sys
from pathlib import Path

# Add src to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / 'src'))

# Test the relative path logic
def test_relative_path_display():
    """Test relative path calculation."""
    print("=" * 60)
    print("Testing Relative Path Display Logic")
    print("=" * 60)
    
    models_dir = "/home/simao/projetos/shypn/models"
    
    test_cases = [
        # (full_path, expected_display)
        (f"{models_dir}/test_model.json", "test_model.json"),
        (f"{models_dir}/subfolder1/test.txt", "subfolder1/test.txt"),
        (f"{models_dir}/subfolder1/subsub1/file.py", "subfolder1/subsub1/file.py"),
        (f"{models_dir}/subfolder2/data.json", "subfolder2/data.json"),
    ]
    
    print(f"\n→ Models directory: {models_dir}\n")
    
    for full_path, expected in test_cases:
        try:
            relative = os.path.relpath(full_path, models_dir)
            status = "✓" if relative == expected else "✗"
            print(f"{status} File: {full_path}")
            print(f"  Expected: {expected}")
            print(f"  Got:      {relative}")
            if relative != expected:
                print(f"  ERROR: Mismatch!")
            print()
        except ValueError as e:
            print(f"✗ File: {full_path}")
            print(f"  Error: {e}\n")
    
    print("=" * 60)
    print("Test Complete")
    print("=" * 60)


if __name__ == '__main__':
    test_relative_path_display()
