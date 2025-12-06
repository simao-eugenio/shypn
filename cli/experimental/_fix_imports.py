#!/usr/bin/env python3
"""Fix imports by adding src to path - for all CLI tools"""
import sys
from pathlib import Path

# Add src directory to path
repo_root = Path(__file__).parent.parent.parent
src_path = repo_root / 'src'
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))
