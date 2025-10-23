#!/bin/bash
# Run shypn with detailed logging to diagnose button issues

cd /home/simao/projetos/shypn

echo "========================================================================"
echo "SHYPN - Master Palette Button Debug Session"
echo "========================================================================"
echo ""
echo "Instructions:"
echo "  1. Wait for the app to load"
echo "  2. Click 'Files' button"
echo "  3. Click 'Analyses' button"
echo "  4. Click 'Files' button again"
echo "  5. Close the app"
echo ""
echo "Watch the log output below for [MP] and [HANDLER] messages"
echo "========================================================================"
echo ""

/usr/bin/python3 src/shypn.py 2>&1 | grep -E "\[(MP|HANDLER|ERROR)\]" --line-buffered

echo ""
echo "========================================================================"
echo "Debug session complete"
echo "========================================================================"
