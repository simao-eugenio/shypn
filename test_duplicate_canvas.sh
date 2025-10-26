#!/bin/bash
# Test script to reproduce and diagnose duplicate canvas creation

echo "====== Testing SBML Import Duplicate Canvas Bug ======"
echo ""
echo "Instructions:"
echo "1. App will launch"
echo "2. Open the SBML project"
echo "3. Click the Pathway tab"
echo "4. Import BIOMD0000000001 (or any SBML model)"
echo "5. Watch the console output"
echo "6. Check how many tabs are created"
echo "7. Try opening properties on an object"
echo ""
echo "====== Starting app with detailed logging ======"
echo ""

cd /home/simao/projetos/shypn
python3 src/shypn.py 2>&1 | tee test_duplicate_canvas.log
