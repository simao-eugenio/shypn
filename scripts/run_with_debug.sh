#!/bin/bash
# Quick test script to run shypn and show right-click debug output

echo "========================================"
echo "Starting SHYpn with Right-Click Debug"
echo "========================================"
echo ""
echo "INSTRUCTIONS:"
echo "1. Wait for the app to load"
echo "2. Right-click ANYWHERE in the file browser"
echo "3. Watch this terminal for debug output"
echo ""
echo "Expected output:"
echo "  🖱️  Right-click detected at (x, y)"
echo "  ✓ Context menu exists"
echo "  → Showing context menu..."
echo ""
echo "If you see '✗ Context menu is None!' the menu wasn't created"
echo "If you see nothing, the gesture isn't being triggered"
echo ""
echo "========================================"
echo ""

cd /home/simao/projetos/shypn
/usr/bin/python3 src/shypn.py 2>&1 | grep -E "(✓|✗|🖱️|→|Context menu|right-click)" --line-buffered
