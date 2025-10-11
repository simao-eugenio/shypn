#!/bin/bash
# Workspace Isolation Test Script
# Run this after starting the application to verify security

echo "================================================"
echo "Workspace Isolation Verification Tests"
echo "================================================"
echo ""

# Test 1: Check directory structure
echo "✓ Test 1: Verify workspace directory structure"
echo "  Expected: workspace/ with subdirectories examples/, projects/, cache/"
ls -la workspace/ 2>/dev/null || echo "  ❌ ERROR: workspace/ directory not found!"
echo ""

# Test 2: Check workspace contents
echo "✓ Test 2: Verify workspace subdirectories"
if [ -d "workspace/examples" ] && [ -d "workspace/projects" ] && [ -d "workspace/cache" ]; then
    echo "  ✅ All required subdirectories present"
else
    echo "  ❌ ERROR: Missing required subdirectories"
fi
echo ""

# Test 3: Check example files
echo "✓ Test 3: Verify example files present"
if [ -f "workspace/examples/simple.shy" ]; then
    echo "  ✅ workspace/examples/simple.shy exists"
else
    echo "  ❌ ERROR: simple.shy not found"
fi
echo ""

# Test 4: Verify application directories are protected
echo "✓ Test 4: Verify application directories exist (but shouldn't be visible in file explorer)"
for dir in "src" "tests" "ui" "data"; do
    if [ -d "$dir" ]; then
        echo "  ✅ $dir/ exists (protected)"
    else
        echo "  ⚠ WARNING: $dir/ not found"
    fi
done
echo ""

# Test 5: Check gitignore configuration
echo "✓ Test 5: Verify .gitignore properly configured"
if grep -q "workspace/projects/" .gitignore && grep -q "workspace/cache/" .gitignore; then
    echo "  ✅ .gitignore configured correctly"
else
    echo "  ❌ ERROR: .gitignore missing workspace entries"
fi
echo ""

# Test 6: Python syntax validation
echo "✓ Test 6: Python syntax validation"
python3 -m py_compile \
    src/shypn/helpers/left_panel_loader.py \
    src/shypn/data/project_models.py \
    src/shypn/helpers/file_explorer_panel.py 2>&1
if [ $? -eq 0 ]; then
    echo "  ✅ All Python files compile without errors"
else
    echo "  ❌ ERROR: Python syntax errors detected"
fi
echo ""

# Test 7: Check for modified files
echo "✓ Test 7: Git status check"
git status --short | head -20
echo ""

echo "================================================"
echo "Manual Testing Required:"
echo "================================================"
echo "1. Run application: python3 -m shypn"
echo "2. Verify file explorer starts in workspace/"
echo "3. Try to navigate above workspace/ (should be blocked)"
echo "4. Verify src/, tests/, ui/ are NOT visible"
echo "5. Open workspace/examples/simple.shy"
echo "6. Create a new project and verify it saves to workspace/projects/"
echo ""
echo "================================================"
echo "Security Validation:"
echo "================================================"
echo "In the running application:"
echo "- File explorer should ONLY show: examples/, projects/, cache/"
echo "- Up/parent navigation button should be disabled at workspace/"
echo "- No way to navigate to src/, tests/, ui/, data/, doc/"
echo ""
