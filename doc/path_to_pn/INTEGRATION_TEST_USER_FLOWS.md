# Integration Testing User Flows

**Date**: 2025-10-09  
**Purpose**: Document user flows for testing the pathway enhancement pipeline integration

---

## Overview

There are **three main approaches** to testing the pathway enhancement integration:

1. **Automated Integration Tests** (Already implemented ✅)
2. **Manual GUI Testing** (User-facing workflow)
3. **Programmatic API Testing** (Developer workflow)

---

## 1. Automated Integration Tests ✅

### Location
`tests/pathway/test_integration.py` (704 lines, 21 tests)

### How to Run

```bash
# Run all integration tests
cd /home/simao/projetos/shypn
PYTHONPATH=/home/simao/projetos/shypn/src:$PYTHONPATH \
  python3 -m pytest tests/pathway/test_integration.py -v

# Run specific test class
pytest tests/pathway/test_integration.py::TestIntegrationSmallPathways -v

# Run with performance output
pytest tests/pathway/test_integration.py::TestIntegrationPerformance::test_performance_scaling -v -s

# Run with coverage
pytest tests/pathway/test_integration.py --cov=shypn.pathway --cov-report=html
```

### Test Coverage

**8 Test Categories:**
1. **Small Pathways** (3 tests)
   - Empty documents
   - Minimal pathways (2-3 elements)
   - Overlapping elements

2. **Medium Pathways** (3 tests)
   - Linear chains (10+ elements)
   - Branching structures
   - Cyclic dependencies

3. **Large Pathways** (2 tests)
   - Grid layouts (100 elements)
   - Dense networks (50+ elements)

4. **Metadata Integration** (1 test)
   - KEGG compound/reaction data
   - Label enhancement
   - Color preservation

5. **Configuration Testing** (4 tests)
   - Layout only
   - Arcs only
   - All processors enabled
   - All processors disabled

6. **Performance Benchmarking** (2 tests)
   - Scaling tests (10→100 elements)
   - Memory efficiency

7. **Error Handling** (3 tests)
   - Invalid documents
   - Processor failures
   - Timeout scenarios

8. **Output Quality** (3 tests)
   - Arc connectivity
   - Position validity
   - Metadata preservation

### Expected Results

```
============================= test session starts ==============================
...
tests/pathway/test_integration.py::TestIntegrationSmallPathways::test_empty_document PASSED [  4%]
tests/pathway/test_integration.py::TestIntegrationSmallPathways::test_minimal_pathway PASSED [  9%]
tests/pathway/test_integration.py::TestIntegrationSmallPathways::test_small_pathway_with_overlaps PASSED [ 14%]
...
============================== 21 passed in 0.12s ==============================
```

---

## 2. Manual GUI Testing (End-User Workflow)

### Prerequisites
- Application running: `python3 src/shypn.py`
- Network connection (for KEGG API)

### User Flow: Import KEGG Pathway with Enhancements

#### Step 1: Open KEGG Import Panel

**Actions:**
1. Launch application: `python3 src/shypn.py`
2. Navigate to **Pathway** menu
3. Select **Import** → **KEGG Pathway**
4. Import panel appears on the right side

**Expected:**
- Import panel visible with pathway ID field
- Enhancement options visible (checkboxes)
- Fetch and Import buttons present

#### Step 2: Configure Enhancement Options

**Actions:**
1. Check/uncheck enhancement options:
   - ☑️ **Layout Optimization** - Resolve overlaps
   - ☑️ **Arc Routing** - Handle parallel arcs
   - ☑️ **Metadata Enhancement** - Enrich labels
2. Adjust parameters (optional):
   - Coordinate scale (default: 1.0)
   - Filter cofactors (optional)

**Expected:**
- Checkboxes toggle on/off
- Parameters adjustable via spinners
- Default values shown

#### Step 3: Fetch KEGG Pathway

**Test Pathways:**
- **Small**: `hsa04668` (TNF signaling, ~30 elements)
- **Medium**: `hsa00010` (Glycolysis, ~60 elements)
- **Large**: `hsa04010` (MAPK signaling, ~250+ elements)

**Actions:**
1. Enter pathway ID in text field (e.g., `hsa00010`)
2. Click **Fetch** button
3. Wait for download (1-5 seconds)

**Expected:**
- Status message: "Fetching pathway..."
- Preview appears with pathway info:
  ```
  Pathway: Glycolysis / Gluconeogenesis
  Organism: hsa
  Number: 00010
  
  Entries: 68
  Reactions: 42
  Relations: 15
  
    Compounds: 29
    Genes: 31
    Enzymes: 8
  ```
- Import button becomes enabled

#### Step 4: Import and Apply Enhancements

**Actions:**
1. Review preview information
2. Verify enhancement options are checked
3. Click **Import** button
4. Wait for processing (0.1-1 second)

**Expected:**
- Status message: "Converting pathway to Petri net..."
- New tab created with pathway name
- Canvas shows pathway with:
  - ✅ Places (circles) for compounds
  - ✅ Transitions (rectangles) for reactions
  - ✅ Arcs connecting elements
  - ✅ Labels with compound/reaction names
  - ✅ No overlapping elements (if layout optimization enabled)
  - ✅ Curved arcs for parallel connections (if arc routing enabled)
  - ✅ KEGG colors preserved (if metadata enhancement enabled)

#### Step 5: Verify Enhancements

**Layout Optimization Verification:**
1. **Visual Check**: No overlapping elements
2. **Zoom In**: Elements maintain spacing
3. **Select Element**: Can select individual elements clearly

**What to Look For:**
- Places and transitions have clear separation
- No overlapping bounding boxes
- Readable labels
- Consistent spacing

**Arc Routing Verification:**
1. **Find Parallel Arcs**: Look for multiple arcs between same nodes
2. **Check Curves**: Parallel arcs should be curved/spread out
3. **Zoom In**: Curves should be smooth Bézier curves

**What to Look For:**
- Parallel arcs don't overlap
- Curves are smooth and symmetric
- Arc directions clear (arrow heads visible)

**Metadata Enhancement Verification:**
1. **Check Labels**: Places show compound names (not generic "Place 1")
2. **Check Colors**: Elements retain KEGG color coding
3. **Hover/Select**: Tooltips or properties show KEGG IDs

**What to Look For:**
- Meaningful labels: "Glucose", "ATP", "Hexokinase"
- Color-coded elements (enzymes green, compounds blue, etc.)
- KEGG cross-references preserved

#### Step 6: Performance Testing

**Actions:**
1. Import small pathway (e.g., `hsa04668`)
   - Note import time
   - Should be < 0.5 seconds

2. Import medium pathway (e.g., `hsa00010`)
   - Note import time
   - Should be < 1 second

3. Import large pathway (e.g., `hsa04010`)
   - Note import time
   - Should be < 5 seconds
   - May take longer on first fetch (network download)

**Expected Performance:**
```
Pathway Size    Elements    Expected Time
-----------------------------------------
Small           20-50       < 0.5s
Medium          50-100      < 1.0s
Large           100-250     < 5.0s
Extra Large     250+        < 10.0s
```

#### Step 7: Test Configuration Combinations

**Test Cases:**

**A. Layout Only**
- ☑️ Layout Optimization
- ☐ Arc Routing
- ☐ Metadata Enhancement
- **Expect**: No overlaps, but generic labels and straight arcs

**B. Arcs Only**
- ☐ Layout Optimization
- ☑️ Arc Routing
- ☐ Metadata Enhancement
- **Expect**: Curved parallel arcs, but may have overlaps and generic labels

**C. Metadata Only**
- ☐ Layout Optimization
- ☐ Arc Routing
- ☑️ Metadata Enhancement
- **Expect**: Named labels and colors, but overlaps and straight arcs

**D. All Enabled** (Recommended)
- ☑️ Layout Optimization
- ☑️ Arc Routing
- ☑️ Metadata Enhancement
- **Expect**: Best quality - no overlaps, curved arcs, named labels

**E. All Disabled**
- ☐ Layout Optimization
- ☐ Arc Routing
- ☐ Metadata Enhancement
- **Expect**: Raw conversion - may have overlaps, straight arcs, generic labels

### Common Issues and Solutions

**Issue 1: Import button stays disabled**
- **Cause**: Pathway fetch failed
- **Solution**: Check network connection, verify pathway ID exists

**Issue 2: Elements overlap despite layout optimization**
- **Cause**: Pathway too complex or options too strict
- **Solution**: Increase layout iterations, adjust force strength in code

**Issue 3: Arcs don't curve**
- **Cause**: No parallel arcs detected
- **Solution**: Normal behavior if arcs aren't parallel

**Issue 4: Labels still generic (Place 1, Transition 1)**
- **Cause**: Metadata enhancement disabled or no KEGG metadata
- **Solution**: Enable metadata enhancement checkbox

**Issue 5: Import takes too long (>10 seconds)**
- **Cause**: Network download or very large pathway (>500 elements)
- **Solution**: Expected for first fetch; subsequent imports use cache

---

## 3. Programmatic API Testing (Developer Workflow)

### Use Case: Testing on Real KEGG Pathways

#### Test Script Template

```python
#!/usr/bin/env python3
"""Test pathway enhancement on real KEGG pathways."""

import sys
import time
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.importer.kegg import fetch_pathway, parse_kgml
from shypn.importer.kegg.pathway_converter import convert_pathway_enhanced
from shypn.pathway.options import get_standard_options, get_maximum_options

def test_pathway(pathway_id: str, description: str):
    """Test a single KEGG pathway."""
    print(f"\n{'='*60}")
    print(f"Testing: {pathway_id} - {description}")
    print(f"{'='*60}")
    
    # Fetch pathway
    print("1. Fetching pathway from KEGG...")
    start = time.time()
    kgml = fetch_pathway(pathway_id)
    fetch_time = time.time() - start
    print(f"   Fetched in {fetch_time:.2f}s")
    
    # Parse KGML
    print("2. Parsing KGML...")
    start = time.time()
    pathway = parse_kgml(kgml)
    parse_time = time.time() - start
    print(f"   Parsed in {parse_time:.3f}s")
    print(f"   Found: {len(pathway.entries)} entries, {len(pathway.reactions)} reactions")
    
    # Convert with enhancements
    print("3. Converting with enhancements...")
    options = get_standard_options()
    start = time.time()
    document = convert_pathway_enhanced(pathway, enhancement_options=options)
    convert_time = time.time() - start
    print(f"   Converted in {convert_time:.3f}s")
    print(f"   Result: {len(document.places)} places, "
          f"{len(document.transitions)} transitions, "
          f"{len(document.arcs)} arcs")
    
    # Calculate per-element time
    total_elements = len(document.places) + len(document.transitions)
    if total_elements > 0:
        per_element = (convert_time / total_elements) * 1000  # ms
        print(f"   Performance: {per_element:.2f}ms per element")
    
    # Verify quality
    print("4. Verifying output quality...")
    
    # Check no disconnected arcs
    disconnected = 0
    for arc in document.arcs:
        source_valid = (arc.source_id in [p.id for p in document.places] or
                       arc.source_id in [t.id for t in document.transitions])
        target_valid = (arc.target_id in [p.id for p in document.places] or
                       arc.target_id in [t.id for t in document.transitions])
        if not source_valid or not target_valid:
            disconnected += 1
    
    print(f"   Disconnected arcs: {disconnected}")
    
    # Check valid positions
    invalid_positions = 0
    for place in document.places:
        if not (0 <= place.x < 10000 and 0 <= place.y < 10000):
            invalid_positions += 1
    for transition in document.transitions:
        if not (0 <= transition.x < 10000 and 0 <= transition.y < 10000):
            invalid_positions += 1
    
    print(f"   Invalid positions: {invalid_positions}")
    
    # Overall result
    if disconnected == 0 and invalid_positions == 0:
        print("   ✅ PASSED - Output quality verified")
    else:
        print("   ❌ FAILED - Quality issues detected")
    
    return {
        'pathway_id': pathway_id,
        'description': description,
        'elements': total_elements,
        'fetch_time': fetch_time,
        'parse_time': parse_time,
        'convert_time': convert_time,
        'per_element_ms': per_element,
        'disconnected_arcs': disconnected,
        'invalid_positions': invalid_positions,
        'passed': disconnected == 0 and invalid_positions == 0
    }

# Test suite
if __name__ == '__main__':
    test_cases = [
        ('hsa04668', 'TNF signaling pathway (Small, ~30 elements)'),
        ('hsa00010', 'Glycolysis (Medium, ~60 elements)'),
        ('hsa04010', 'MAPK signaling pathway (Large, ~250 elements)'),
    ]
    
    results = []
    for pathway_id, description in test_cases:
        try:
            result = test_pathway(pathway_id, description)
            results.append(result)
        except Exception as e:
            print(f"   ❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    print(f"{'Pathway':<15} {'Elements':<10} {'Time(ms)':<12} {'ms/elem':<10} {'Result'}")
    print(f"{'-'*60}")
    
    for r in results:
        status = '✅ PASS' if r['passed'] else '❌ FAIL'
        print(f"{r['pathway_id']:<15} {r['elements']:<10} "
              f"{r['convert_time']*1000:<12.1f} {r['per_element_ms']:<10.2f} {status}")
    
    passed = sum(1 for r in results if r['passed'])
    print(f"\nPassed: {passed}/{len(results)}")
```

#### Running the Test Script

```bash
cd /home/simao/projetos/shypn
python3 test_real_kegg_pathways.py
```

#### Expected Output

```
============================================================
Testing: hsa04668 - TNF signaling pathway (Small, ~30 elements)
============================================================
1. Fetching pathway from KEGG...
   Fetched in 1.23s
2. Parsing KGML...
   Parsed in 0.012s
   Found: 32 entries, 18 reactions
3. Converting with enhancements...
   Converted in 0.034s
   Result: 28 places, 18 transitions, 52 arcs
   Performance: 0.74ms per element
4. Verifying output quality...
   Disconnected arcs: 0
   Invalid positions: 0
   ✅ PASSED - Output quality verified

============================================================
Testing: hsa00010 - Glycolysis (Medium, ~60 elements)
============================================================
1. Fetching pathway from KEGG...
   Fetched in 1.45s
2. Parsing KGML...
   Parsed in 0.018s
   Found: 68 entries, 42 reactions
3. Converting with enhancements...
   Converted in 0.089s
   Result: 54 places, 42 transitions, 128 arcs
   Performance: 0.93ms per element
4. Verifying output quality...
   Disconnected arcs: 0
   Invalid positions: 0
   ✅ PASSED - Output quality verified

============================================================
Testing: hsa04010 - MAPK signaling pathway (Large, ~250 elements)
============================================================
1. Fetching pathway from KEGG...
   Fetched in 2.34s
2. Parsing KGML...
   Parsed in 0.045s
   Found: 265 entries, 148 reactions
3. Converting with enhancements...
   Converted in 0.423s
   Result: 218 places, 148 transitions, 542 arcs
   Performance: 1.16ms per element
4. Verifying output quality...
   Disconnected arcs: 0
   Invalid positions: 0
   ✅ PASSED - Output quality verified

============================================================
SUMMARY
============================================================
Pathway         Elements   Time(ms)     ms/elem    Result
------------------------------------------------------------
hsa04668        46         34.0         0.74       ✅ PASS
hsa00010        96         89.0         0.93       ✅ PASS
hsa04010        366        423.0        1.16       ✅ PASS

Passed: 3/3
```

### Use Case: Testing Specific Enhancements

#### Test Individual Processors

```python
#!/usr/bin/env python3
"""Test individual enhancement processors."""

import sys
sys.path.insert(0, '/home/simao/projetos/shypn/src')

from shypn.pathway.options import EnhancementOptions
from shypn.pathway.pipeline import EnhancementPipeline
from shypn.pathway.layout_optimizer import LayoutOptimizer
from shypn.pathway.arc_router import ArcRouter
from shypn.pathway.metadata_enhancer import MetadataEnhancer
from shypn.data.canvas.document_model import DocumentModel
from shypn.importer.kegg import fetch_pathway, parse_kgml
from shypn.importer.kegg.pathway_converter import convert_pathway

def test_layout_only(pathway_id='hsa04668'):
    """Test layout optimization only."""
    print("Testing Layout Optimization Only")
    print("-" * 40)
    
    # Fetch and convert (no enhancements)
    kgml = fetch_pathway(pathway_id)
    pathway = parse_kgml(kgml)
    document = convert_pathway(pathway)
    
    print(f"Before: {len(document.places)} places, {len(document.transitions)} transitions")
    
    # Apply layout only
    options = EnhancementOptions(
        enable_layout_optimization=True,
        enable_arc_routing=False,
        enable_metadata_enhancement=False
    )
    
    pipeline = EnhancementPipeline(options)
    pipeline.add_processor(LayoutOptimizer(options))
    
    result = pipeline.process(document, pathway)
    
    # Check statistics
    report = pipeline.get_report()
    for entry in report['execution_log']:
        if entry['processor'] == 'Layout Optimizer':
            stats = entry['stats']
            print(f"Overlaps before: {stats['overlaps_before']}")
            print(f"Overlaps after: {stats['overlaps_after']}")
            print(f"Overlaps resolved: {stats['overlaps_resolved']}")
            print(f"Elements moved: {stats['elements_moved']}")
            print(f"Converged: {stats['converged']}")

def test_arcs_only(pathway_id='hsa04668'):
    """Test arc routing only."""
    print("\nTesting Arc Routing Only")
    print("-" * 40)
    
    # Fetch and convert
    kgml = fetch_pathway(pathway_id)
    pathway = parse_kgml(kgml)
    document = convert_pathway(pathway)
    
    print(f"Total arcs: {len(document.arcs)}")
    
    # Apply arc routing only
    options = EnhancementOptions(
        enable_layout_optimization=False,
        enable_arc_routing=True,
        enable_metadata_enhancement=False
    )
    
    pipeline = EnhancementPipeline(options)
    pipeline.add_processor(ArcRouter(options))
    
    result = pipeline.process(document, pathway)
    
    # Check statistics
    report = pipeline.get_report()
    for entry in report['execution_log']:
        if entry['processor'] == 'Arc Router':
            stats = entry['stats']
            print(f"Total arcs: {stats['total_arcs']}")
            print(f"Parallel groups: {stats['parallel_arc_groups']}")
            print(f"Arcs in groups: {stats['arcs_in_parallel_groups']}")
            print(f"Arcs with curves: {stats['arcs_with_curves']}")

def test_metadata_only(pathway_id='hsa04668'):
    """Test metadata enhancement only."""
    print("\nTesting Metadata Enhancement Only")
    print("-" * 40)
    
    # Fetch and convert
    kgml = fetch_pathway(pathway_id)
    pathway = parse_kgml(kgml)
    document = convert_pathway(pathway)
    
    print(f"Before: Places with labels: {sum(1 for p in document.places if p.label)}")
    
    # Apply metadata enhancement only
    options = EnhancementOptions(
        enable_layout_optimization=False,
        enable_arc_routing=False,
        enable_metadata_enhancement=True
    )
    
    pipeline = EnhancementPipeline(options)
    pipeline.add_processor(MetadataEnhancer(options))
    
    result = pipeline.process(document, pathway)
    
    # Check statistics
    report = pipeline.get_report()
    for entry in report['execution_log']:
        if entry['processor'] == 'Metadata Enhancer':
            stats = entry['stats']
            print(f"Places enhanced: {stats['places_enhanced']}")
            print(f"Transitions enhanced: {stats['transitions_enhanced']}")
            print(f"Compounds matched: {stats['compounds_matched']}")
            print(f"Reactions matched: {stats['reactions_matched']}")
    
    print(f"After: Places with labels: {sum(1 for p in result.places if p.label)}")
    print(f"Sample labels: {[p.label for p in result.places[:5]]}")

if __name__ == '__main__':
    test_layout_only()
    test_arcs_only()
    test_metadata_only()
```

---

## 4. Quick Validation Checklist

### After Any Change to Enhancement Code

**Run automated tests:**
```bash
pytest tests/pathway/test_integration.py -v
# Should see: 21 passed in ~0.2s
```

**Manual spot check in GUI:**
1. Launch app: `python3 src/shypn.py`
2. Import pathway: `hsa00010` (glycolysis)
3. Verify:
   - ✅ No overlapping elements
   - ✅ Parallel arcs are curved
   - ✅ Labels show compound names (Glucose, ATP, etc.)
   - ✅ Import completes in < 2 seconds

**Expected behavior:**
- All 21 automated tests pass
- GUI import works without errors
- Visual quality acceptable (no overlaps, curved arcs, named labels)

---

## 5. Performance Baselines

### Target Performance

| Pathway Size | Elements | Expected Time | Acceptable Range |
|--------------|----------|---------------|------------------|
| Empty        | 0        | <0.001s       | -                |
| Tiny         | 1-10     | <0.010s       | 0-0.050s         |
| Small        | 10-50    | <0.100s       | 0.050-0.200s     |
| Medium       | 50-100   | <0.500s       | 0.200-1.000s     |
| Large        | 100-250  | <2.000s       | 1.000-5.000s     |
| Extra Large  | 250+     | <10.000s      | 5.000-20.000s    |

### Regression Detection

**If performance degrades:**
- Run: `pytest tests/pathway/test_integration.py::TestIntegrationPerformance -v -s`
- Compare with baseline: ~0.04ms per element
- Investigate if >0.10ms per element (2.5x slower)

---

## Summary

### Three Testing Approaches

1. **Automated** (Fastest, for CI/CD)
   - Run: `pytest tests/pathway/test_integration.py`
   - Time: ~0.2 seconds
   - Coverage: 21 tests, all aspects

2. **Manual GUI** (User perspective)
   - Launch app, import KEGG pathway
   - Time: ~2-3 minutes per pathway
   - Coverage: Visual quality, user experience

3. **Programmatic** (Developer debugging)
   - Run custom test scripts
   - Time: ~1-2 minutes per pathway
   - Coverage: Specific processors, detailed stats

### Recommended Testing Workflow

**Before committing code:**
```bash
# 1. Run automated tests (fast)
pytest tests/pathway/test_integration.py -v

# 2. Manual spot check (medium)
python3 src/shypn.py
# Import hsa00010, verify visually

# 3. Optional: Run real pathway test (slow)
python3 test_real_kegg_pathways.py
```

**Expected time:**
- Automated: 0.2s
- Manual: 2 minutes
- Programmatic: 5 minutes
- **Total: < 10 minutes** for full validation

---

## Next Steps

Based on todo list, the remaining tasks are:

1. ✅ **Create integration test suite** - DONE
2. 🔄 **Test on diverse pathways** - Use programmatic test script above
3. 🔄 **Performance benchmarks** - Already documented, verify on real pathways
4. 🔄 **Create integration documentation** - This document!
5. ⏳ **Commit integration work** - Ready to commit

All flows documented and ready for execution! 🎉
