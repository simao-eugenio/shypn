#!/bin/bash
# Manual GUI Testing Guide for KEGG Import
# Run this to launch the app with testing instructions

clear

cat << 'EOF'
╔════════════════════════════════════════════════════════════════╗
║          KEGG PATHWAY IMPORT - MANUAL TESTING GUIDE            ║
║                     October 7, 2025                            ║
╚════════════════════════════════════════════════════════════════╝

✅ AUTOMATED TESTS: PASSED

   Backend:  ✓ API client  ✓ Parser  ✓ Converter
   Frontend: ✓ Panel loader  ✓ Widgets  ✓ Close handler
   Pathways: ✓ hsa00010 (31P,34T,73A)  ✓ hsa00020  ✓ hsa00030

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 MANUAL TESTING CHECKLIST (20 tests)

Press Enter to launch the application, then follow these steps:

┌────────────────────────────────────────────────────────────────┐
│ BASIC PANEL OPERATIONS (Tests 1-3)                            │
└────────────────────────────────────────────────────────────────┘

  1. ✓ Check header bar has 3 buttons:
     → "File Ops" (left)
     → "Pathways" and "Analyses" (right, side by side)

  2. ✓ Click "Pathways" button
     → Panel docks on right side
     → Width ~320px
     → Shows 3 tabs: Import, Browse, History
     → Import tab active

  3. ✓ Verify Import tab widgets:
     → Pathway ID entry (empty)
     → Organism dropdown (default: Homo sapiens)
     → "Fetch Pathway" button (enabled)
     → "Import to Canvas" button (disabled)
     → Preview area (empty)

┌────────────────────────────────────────────────────────────────┐
│ FETCH PATHWAY (Tests 4-5)                                     │
└────────────────────────────────────────────────────────────────┘

  4. ✓ Enter "hsa00010" in Pathway ID field

  5. ✓ Click "Fetch Pathway"
     → Status shows: "Fetching pathway..."
     → After ~2-3 seconds: Success!
     → Preview shows:
        - Name: "Glycolysis / Gluconeogenesis"
        - ~31 places (compounds)
        - ~34 transitions (reactions)
        - ~73 arcs (connections)
     → "Import to Canvas" button now ENABLED

┌────────────────────────────────────────────────────────────────┐
│ IMPORT TO CANVAS (Tests 6-8)                                  │
└────────────────────────────────────────────────────────────────┘

  6. ✓ Click "Import to Canvas"
     → Status: "Importing pathway..."
     → After ~1-2 seconds: Success!
     → Canvas shows Petri net with:
        • Circles (places/compounds)
        • Rectangles (transitions/reactions)
        • Arrows (arcs/connections)

  7. ✓ Verify objects on canvas:
     → Places have labels (compound names)
     → Transitions have labels
     → Objects are connected
     → Layout roughly follows KEGG coordinates

  8. ✓ Test canvas interaction:
     → Click objects (should select)
     → Zoom in/out (Ctrl + scroll)
     → Pan canvas (drag)

┌────────────────────────────────────────────────────────────────┐
│ MUTUAL EXCLUSIVITY (Tests 9-10)                               │
└────────────────────────────────────────────────────────────────┘

  9. ✓ Click "Pathways" button again
     → Panel hides
     → Canvas expands to full width
     → Imported pathway remains visible

 10. ✓ Test panel switching:
     → Click "Analyses" → Analyses panel appears
     → Click "Pathways" → Pathways appears, Analyses hides
     → Click "Analyses" → Analyses appears, Pathways hides
     → Only ONE panel visible at a time ✓

┌────────────────────────────────────────────────────────────────┐
│ FLOAT/DOCK BEHAVIOR (Tests 11-13) - CRITICAL!                 │
└────────────────────────────────────────────────────────────────┘

 11. ✓ With Pathways panel visible:
     → Click float button (⇲) in panel header
     → Panel becomes floating window
     → Window title: "Pathway Operations"
     → Can move window independently

 12. ✓ **CRITICAL**: Click X button on floating window
     → Window closes smoothly
     → ✓ NO CRASH (no "Segmentation fault")
     → ✓ NO Exit Code 139
     → Panel hides
     → Float button inactive
     → Application still running

 13. ✓ Reopen panel after close:
     → Click "Pathways" button
     → Panel reappears docked
     → No errors

┌────────────────────────────────────────────────────────────────┐
│ MULTIPLE PATHWAYS (Test 14)                                   │
└────────────────────────────────────────────────────────────────┘

 14. ✓ Import second pathway:
     → Enter "hsa00020" (TCA Cycle)
     → Click "Fetch Pathway"
     → Click "Import to Canvas"
     → Both pathways now on canvas
     → No errors

┌────────────────────────────────────────────────────────────────┐
│ ERROR HANDLING (Tests 15-16)                                  │
└────────────────────────────────────────────────────────────────┘

 15. ✓ Test invalid pathway ID:
     → Enter "invalid123"
     → Click "Fetch Pathway"
     → Error message shown
     → Import button stays disabled
     → No crash

 16. ✓ Test empty field:
     → Clear pathway ID field
     → Try to fetch
     → Validation message OR button disabled
     → No crash

┌────────────────────────────────────────────────────────────────┐
│ FILE OPERATIONS (Tests 17-19)                                 │
└────────────────────────────────────────────────────────────────┘

 17. ✓ Save pathway:
     → File → Save As (or File Ops panel)
     → Save as "test_glycolysis.shy"
     → File saves successfully

 18. ✓ Clear and reload:
     → File → New (clear canvas)
     → File → Open "test_glycolysis.shy"
     → Pathway reloads correctly

 19. ✓ Exit application:
     → Close main window
     → ✓ NO crash
     → ✓ Clean exit
     → ✓ Exit code: 0

┌────────────────────────────────────────────────────────────────┐
│ STRESS TEST (Test 20 - Optional)                              │
└────────────────────────────────────────────────────────────────┘

 20. ✓ Repeat float/close cycle 5 times:
     → Click "Pathways"
     → Click float (⇲)
     → Click X
     → Repeat...
     → Should work smoothly every time
     → No memory leaks or slowdowns

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 EXPECTED RESULTS:

   ✅ All 20 tests pass
   ✅ No segmentation faults
   ✅ No crashes
   ✅ Smooth panel operations
   ✅ Pathway imports successfully
   ✅ Objects appear on canvas
   ✅ File operations work

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

🎯 CRITICAL SUCCESS CRITERIA:

   1. Pathway imports and appears on canvas
   2. X button closes cleanly (NO CRASH!)
   3. Panel mutual exclusivity works
   4. Float/dock cycle repeatable

Press Enter to launch application and start testing...
EOF

read -p ""

echo ""
echo "🚀 Launching shypn..."
echo ""

cd /home/simao/projetos/shypn
python3 src/shypn.py

EXIT_CODE=$?

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "Application exited with code: $EXIT_CODE"
echo ""

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Clean exit (code 0)"
elif [ $EXIT_CODE -eq 130 ]; then
    echo "⚠️  Interrupted by user (Ctrl+C)"
elif [ $EXIT_CODE -eq 139 ]; then
    echo "❌ SEGMENTATION FAULT (Exit Code 139)"
    echo "   This should NOT happen with the fix applied!"
else
    echo "⚠️  Exit code: $EXIT_CODE"
fi

echo ""
echo "After testing, update results in: test_kegg_end_to_end.md"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
