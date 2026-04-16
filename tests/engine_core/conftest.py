"""pytest configuration for engine_core tests.

Ensures ``src/`` is on sys.path so tests can ``import shypn`` without
needing the package to be installed.
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'src')))
