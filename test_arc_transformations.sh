#!/bin/bash
# Quick test script for arc transformations

echo "============================================"
echo "Arc Transformation Test"
echo "============================================"
echo ""
echo "1. Checking all required files exist..."
echo ""

files=(
    "src/shypn/netobjs/arc.py"
    "src/shypn/netobjs/curved_arc.py"
    "src/shypn/netobjs/inhibitor_arc.py"
    "src/shypn/netobjs/curved_inhibitor_arc.py"
    "src/shypn/utils/arc_transform.py"
    "src/shypn/helpers/model_canvas_loader.py"
    "src/shypn/data/model_canvas_manager.py"
)

all_exist=true
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "✓ $file"
    else
        echo "✗ $file (MISSING!)"
        all_exist=false
    fi
done

echo ""
if [ "$all_exist" = false ]; then
    echo "ERROR: Some files are missing!"
    exit 1
fi

echo "2. Checking syntax of all files..."
echo ""

python3 -m py_compile "${files[@]}" 2>&1
if [ $? -eq 0 ]; then
    echo "✓ All files have valid syntax"
else
    echo "✗ Syntax errors found!"
    exit 1
fi

echo ""
echo "3. Testing imports..."
echo ""

python3 -c "
import sys
sys.path.insert(0, 'src')
try:
    from shypn.netobjs import Arc, InhibitorArc, CurvedArc, CurvedInhibitorArc
    print('✓ Arc classes imported successfully')
except ImportError as e:
    print(f'✗ Failed to import arc classes: {e}')
    sys.exit(1)

try:
    from shypn.utils.arc_transform import (
        make_curved, make_straight,
        convert_to_inhibitor, convert_to_normal,
        is_straight, is_curved, is_inhibitor, is_normal
    )
    print('✓ Arc transformation utilities imported successfully')
except ImportError as e:
    print(f'✗ Failed to import arc_transform: {e}')
    sys.exit(1)

try:
    from shypn.data.model_canvas_manager import ModelCanvasManager
    print('✓ ModelCanvasManager imported successfully')
except ImportError as e:
    print(f'✗ Failed to import ModelCanvasManager: {e}')
    sys.exit(1)

print('')
print('4. Testing transformation logic...')
print('')

# Create test objects
from shypn.netobjs import Place, Transition

p1 = Place(100, 100, 1, 'P1')
t1 = Transition(200, 100, 1, 'T1')
arc = Arc(p1, t1, 1, 'A1', weight=2)

print(f'Created arc: {type(arc).__name__}')
print(f'  - is_straight: {is_straight(arc)}')
print(f'  - is_curved: {is_curved(arc)}')
print(f'  - is_normal: {is_normal(arc)}')
print(f'  - is_inhibitor: {is_inhibitor(arc)}')
print(f'  - weight: {arc.weight}')

# Test straight -> curved
print('')
print('Test 1: straight -> curved')
curved = make_curved(arc)
print(f'  Result: {type(curved).__name__}')
print(f'  - is_curved: {is_curved(curved)}')
print(f'  - weight preserved: {curved.weight == arc.weight}')
assert is_curved(curved), 'make_curved failed!'
assert curved.weight == arc.weight, 'Weight not preserved!'
print('  ✓ PASS')

# Test curved -> straight
print('')
print('Test 2: curved -> straight')
straight = make_straight(curved)
print(f'  Result: {type(straight).__name__}')
print(f'  - is_straight: {is_straight(straight)}')
print(f'  - weight preserved: {straight.weight == arc.weight}')
assert is_straight(straight), 'make_straight failed!'
assert straight.weight == arc.weight, 'Weight not preserved!'
print('  ✓ PASS')

# Test normal -> inhibitor
print('')
print('Test 3: normal -> inhibitor')
inhibitor = convert_to_inhibitor(arc)
print(f'  Result: {type(inhibitor).__name__}')
print(f'  - is_inhibitor: {is_inhibitor(inhibitor)}')
print(f'  - weight preserved: {inhibitor.weight == arc.weight}')
assert is_inhibitor(inhibitor), 'convert_to_inhibitor failed!'
assert inhibitor.weight == arc.weight, 'Weight not preserved!'
print('  ✓ PASS')

# Test inhibitor -> normal
print('')
print('Test 4: inhibitor -> normal')
normal = convert_to_normal(inhibitor)
print(f'  Result: {type(normal).__name__}')
print(f'  - is_normal: {is_normal(normal)}')
print(f'  - weight preserved: {normal.weight == arc.weight}')
assert is_normal(normal), 'convert_to_normal failed!'
assert normal.weight == arc.weight, 'Weight not preserved!'
print('  ✓ PASS')

# Test combined transformation
print('')
print('Test 5: straight normal -> curved inhibitor')
curved_inhibitor = make_curved(inhibitor)
print(f'  Result: {type(curved_inhibitor).__name__}')
print(f'  - is_curved: {is_curved(curved_inhibitor)}')
print(f'  - is_inhibitor: {is_inhibitor(curved_inhibitor)}')
assert is_curved(curved_inhibitor) and is_inhibitor(curved_inhibitor), 'Combined transformation failed!'
print('  ✓ PASS')

print('')
print('============================================')
print('All transformation tests PASSED! ✓')
print('============================================')
print('')
print('Next step: Launch the application and test transformations via UI')
echo 'Run: python3 src/shypn.py'
print('')
print('Then:')
print('  1. Create a Place and Transition')
print('  2. Draw an Arc between them')
print('  3. Right-click the arc')
print('  4. Select \"Transform Arc ►\"')
print('  5. Choose a transformation')
print('  6. Watch the console for debug output')
print('')
"

if [ $? -eq 0 ]; then
    echo ""
    echo "============================================"
    echo "✓ ALL TESTS PASSED!"
    echo "============================================"
    echo ""
    echo "The arc transformation code is working correctly."
    echo ""
    echo "To test in the UI, run:"
    echo "    python3 src/shypn.py"
    echo ""
    echo "Then follow the testing procedure in:"
    echo "    ARC_TRANSFORMATION_DEBUG_GUIDE.md"
    echo ""
else
    echo ""
    echo "============================================"
    echo "✗ TESTS FAILED"
    echo "============================================"
    echo ""
    echo "Check the error messages above."
    exit 1
fi
