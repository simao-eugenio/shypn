#!/bin/bash
# Interactive test for Master Palette buttons

cd /home/simao/projetos/shypn

echo "========================================================================"
echo "Master Palette Button Interactive Test"
echo "========================================================================"
echo ""
echo "This will launch the app with debug logging."
echo "Please test the following sequence:"
echo ""
echo "  1. Click 'Files' button (folder icon)"
echo "  2. Click 'Analyses' button (monitor icon)"
echo "  3. Click 'Pathways' button (list icon)"  
echo "  4. Click 'Topology' button (network icon)"
echo "  5. Click 'Files' again"
echo "  6. Click 'Analyses' again"
echo ""
echo "Watch the terminal output for [HANDLER] messages."
echo "If you see handlers being called, the logic is working."
echo "If panels don't show, the issue is with panel visibility/attachment."
echo ""
echo "Press ENTER to start..."
read

echo "========================================================================"
echo "Starting application with debug logging..."
echo "========================================================================"
echo ""

/usr/bin/python3 src/shypn.py 2>&1 | grep -E "\[(MP|HANDLER)\]" --line-buffered | tee button_test.log

echo ""
echo "========================================================================"
echo "Test complete. Log saved to button_test.log"
echo "========================================================================"
