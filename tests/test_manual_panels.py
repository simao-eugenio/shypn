#!/usr/bin/env python3
"""
Simple test to check if panels are created when you click File -> New.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("\n" + "="*70)
print("Testing if panels are visible after File → New")
print("="*70 + "\n")

print("Instructions:")
print("1. Application will start")
print("2. Click File → New to create a model")
print("3. Click on Dynamic Analyses tab on the right")
print("4. Click on 'Transitions' sub-tab")
print("5. Check if you see:")
print("   - Selected list widget")
print("   - Clear Selection button")
print("   - Matplotlib canvas")
print("\nPress Ctrl+C in terminal when done testing.\n")

# Import and run the main app
from shypn import main

try:
    main()
except KeyboardInterrupt:
    print("\n\nTest interrupted by user.")
    sys.exit(0)
