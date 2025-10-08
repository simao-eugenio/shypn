#!/bin/bash
# Quick verification of the entries iteration fix

cat << 'EOF'
╔════════════════════════════════════════════════════════════════╗
║           BUGFIX: Entries Iteration Error - FIXED              ║
╚════════════════════════════════════════════════════════════════╝

Issue:  'str' has no attribute 'type'
When:   Clicking "Fetch Pathway" button
Cause:  Iterating over dict keys instead of values

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Fix Applied:
  File: src/shypn/helpers/kegg_import_panel.py (lines 209-211)
  
  Before (WRONG):
    for e in pathway.entries if e.type == 'compound'
    # e is a string (dict key), not a KEGGEntry object
  
  After (CORRECT):
    for e in pathway.entries.values() if e.type == 'compound'
    # e is a KEGGEntry object with .type attribute

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Testing the fix...

EOF

cd /home/simao/projetos/shypn
python3 test_entries_iteration_fix.py

if [ $? -eq 0 ]; then
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                   FIX VERIFICATION: PASSED ✅                  ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    echo "The pathway fetch should now work correctly!"
    echo ""
    echo "Next steps:"
    echo "  1. python3 src/shypn.py"
    echo "  2. Click 'Pathways' button"
    echo "  3. Enter pathway ID: hsa00010"
    echo "  4. Click 'Fetch Pathway'"
    echo "  5. ✅ Should show preview with compound/gene counts"
    echo ""
else
    echo ""
    echo "❌ Fix verification failed"
    exit 1
fi
