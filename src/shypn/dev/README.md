# Development Tools and Experiments

This directory contains development utilities, experimental code, and prototyping tools used during development but not part of the core application.

## Purpose

The `dev/` directory serves as a sandbox for:
- **Prototyping**: Test new features before integration
- **Experiments**: Try alternative implementations
- **Debug Scripts**: One-off scripts for debugging
- **Test Generators**: Generate test data and models
- **Performance Tests**: Benchmark code performance
- **Development Utilities**: Tools to assist development

## Content Guidelines

### What Belongs Here
✅ Experimental features under development  
✅ Prototype implementations  
✅ Development scripts and utilities  
✅ Test data generators  
✅ Performance benchmarking scripts  
✅ API exploration code  
✅ Proof-of-concept implementations  

### What Doesn't Belong Here
❌ Production code (goes in appropriate module)  
❌ Unit tests (goes in `tests/`)  
❌ Documentation (goes in `doc/`)  
❌ User-facing features (goes in appropriate module)  
❌ Build scripts (goes in `scripts/`)  

## Typical Contents

### Prototype Scripts
```python
# dev/prototype_curved_arcs.py
# Experimental Bézier curve implementation
# Testing different control point algorithms

def test_bezier_algorithm_1():
    # Implementation A
    pass

def test_bezier_algorithm_2():
    # Implementation B
    pass

# Compare performance and visual quality
compare_algorithms()
```

### Test Data Generators
```python
# dev/generate_large_model.py
# Generate large Petri Net for performance testing

def generate_model(num_places, num_transitions):
    """Generate random Petri Net model"""
    model = DocumentModel()
    
    for i in range(num_places):
        place = Place(f"P{i}", x=random(), y=random())
        model.add_place(place)
    
    # ... generate transitions and arcs
    
    return model

if __name__ == '__main__':
    model = generate_model(1000, 800)
    model.save('test_large_model.shy')
```

### Performance Benchmarks
```python
# dev/benchmark_rendering.py
# Benchmark canvas rendering performance

import time
from shypn.data.canvas.document_model import DocumentModel

def benchmark_rendering():
    model = DocumentModel.load('test_model.shy')
    
    start = time.time()
    for _ in range(100):
        canvas.draw(model)
    end = time.time()
    
    avg_time = (end - start) / 100
    print(f"Average render time: {avg_time*1000:.2f}ms")

benchmark_rendering()
```

### API Exploration
```python
# dev/explore_gtk4_features.py
# Explore GTK4 API features

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk

def test_new_widget():
    """Test GTK4 widget capabilities"""
    window = Gtk.Window()
    # Experiment with new features
    pass
```

### Debug Utilities
```python
# dev/debug_arc_connections.py
# Debug arc connection issues

def visualize_connections(model):
    """Visualize all arc connections"""
    for arc in model.arcs:
        print(f"Arc: {arc.source.name} -> {arc.target.name}")
        print(f"  Source pos: {arc.source.position}")
        print(f"  Target pos: {arc.target.position}")
        print(f"  Weight: {arc.weight}")
```

## Workflow

### 1. Prototype New Feature
```bash
# Create prototype in dev/
$ touch dev/prototype_feature_name.py

# Implement and test
$ python dev/prototype_feature_name.py

# Iterate until satisfied
```

### 2. Integrate into Production
```bash
# When ready, move to appropriate module
$ git mv dev/prototype_feature_name.py src/shypn/module/

# Update imports and integrate
# Add proper error handling
# Add documentation
# Add unit tests in tests/
```

### 3. Clean Up
```bash
# Remove temporary files
$ rm dev/temp_*.py

# Archive successful prototypes
$ git mv dev/prototype_name.py archive/prototypes/
```

## Development Scripts

### Model Validators
```python
# dev/validate_model.py
# Validate Petri Net model structure

def validate_model(filepath):
    model = DocumentModel.load(filepath)
    
    # Check for disconnected objects
    disconnected = find_disconnected(model)
    if disconnected:
        print(f"Warning: {len(disconnected)} disconnected objects")
    
    # Check for invalid arcs
    invalid_arcs = find_invalid_arcs(model)
    if invalid_arcs:
        print(f"Error: {len(invalid_arcs)} invalid arcs")
    
    # Check for duplicate names
    duplicates = find_duplicate_names(model)
    if duplicates:
        print(f"Warning: Duplicate names: {duplicates}")
```

### Migration Tools
```python
# dev/migrate_old_format.py
# Migrate old file format to new format

def migrate_v1_to_v2(old_filepath, new_filepath):
    """Migrate version 1.0 to 2.0"""
    with open(old_filepath) as f:
        old_data = json.load(f)
    
    new_data = {
        'version': '2.0',
        'places': migrate_places(old_data['places']),
        'transitions': migrate_transitions(old_data['transitions']),
        'arcs': migrate_arcs(old_data['arcs'])
    }
    
    with open(new_filepath, 'w') as f:
        json.dump(new_data, f, indent=2)
```

### Performance Profilers
```python
# dev/profile_simulation.py
# Profile simulation performance

import cProfile
import pstats

def profile_simulation():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run simulation
    controller = SimulationController(model)
    for _ in range(1000):
        controller.step()
    
    profiler.disable()
    
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
```

## Testing and Validation

### Integration Tests
Prototype integration scenarios:
```python
# dev/test_integration_scenario.py

def test_workflow():
    """Test complete workflow"""
    # Create model
    model = create_test_model()
    
    # Add objects
    place = Place("P1", 100, 100)
    model.add_place(place)
    
    # Save
    model.save('test_workflow.shy')
    
    # Load
    loaded = DocumentModel.load('test_workflow.shy')
    
    # Verify
    assert len(loaded.places) == 1
    assert loaded.places[0].name == "P1"
```

### Visual Tests
Manual visual inspection:
```python
# dev/visual_test_arcs.py

def visual_test():
    """Display arcs for visual inspection"""
    window = Gtk.Window()
    canvas = Gtk.DrawingArea()
    
    def draw_callback(area, cr, width, height):
        # Draw test arcs with different styles
        draw_test_arcs(cr)
    
    canvas.set_draw_func(draw_callback)
    window.set_child(canvas)
    window.present()
```

## Best Practices

### Documentation
Add comments explaining:
- Purpose of the experiment
- Known issues or limitations
- References to related code
- TODO items before production

```python
# dev/experiment_name.py
"""
Experimental implementation of feature X.

Purpose:
  Testing alternative algorithm for Y to improve performance.

Status:
  Prototype - do not use in production

Issues:
  - Edge case A not handled
  - Performance regression for large inputs

References:
  - Related to src/shypn/module/file.py
  - See doc/FEATURE_X_DESIGN.md

TODO:
  - Handle edge cases
  - Add error handling
  - Optimize for large inputs
  - Add unit tests
"""
```

### Version Control
- Commit experimental code with `[dev]` prefix
- Use branches for larger experiments
- Clean up before merging to main

```bash
# Commit dev changes
$ git add dev/experiment_name.py
$ git commit -m "[dev] Experiment with feature X algorithm"

# Create branch for larger experiment
$ git checkout -b experiment/feature-y
$ git add dev/
$ git commit -m "[dev] Feature Y prototype"
```

### Dependencies
- Use only dependencies available in main project
- Document any experimental dependencies
- Don't add dev dependencies to production requirements

## Examples

### Example 1: Algorithm Comparison
```python
# dev/compare_layout_algorithms.py

import time
from shypn.data.canvas.document_model import DocumentModel

def algorithm_force_directed(model):
    """Force-directed layout algorithm"""
    pass

def algorithm_hierarchical(model):
    """Hierarchical layout algorithm"""
    pass

def compare_algorithms(model):
    """Compare layout algorithms"""
    algorithms = [
        ('Force-Directed', algorithm_force_directed),
        ('Hierarchical', algorithm_hierarchical)
    ]
    
    for name, algo in algorithms:
        start = time.time()
        result = algo(model)
        elapsed = time.time() - start
        
        print(f"{name}: {elapsed:.3f}s")
        visualize_result(result)
```

### Example 2: Data Migration
```python
# dev/migrate_old_models.py

import os
import glob

def migrate_directory(directory):
    """Migrate all .shy files in directory"""
    files = glob.glob(os.path.join(directory, '*.shy'))
    
    for filepath in files:
        print(f"Migrating {filepath}...")
        try:
            migrate_file(filepath)
            print("  ✓ Success")
        except Exception as e:
            print(f"  ✗ Error: {e}")
```

### Example 3: Performance Baseline
```python
# dev/performance_baseline.py

def establish_baseline():
    """Establish performance baseline"""
    tests = [
        ('Render 100 objects', test_render_100),
        ('Simulate 1000 steps', test_simulate_1000),
        ('Load large model', test_load_large),
        ('Save large model', test_save_large)
    ]
    
    results = {}
    for name, test_func in tests:
        time_ms = measure_time(test_func)
        results[name] = time_ms
        print(f"{name}: {time_ms:.2f}ms")
    
    # Save baseline for future comparison
    with open('baseline.json', 'w') as f:
        json.dump(results, f, indent=2)
```

## Cleanup Policy

### Regular Cleanup
- Review dev/ monthly
- Remove obsolete experiments
- Archive successful prototypes
- Update documentation

### Before Release
- Clean up all temporary files
- Archive or remove unfinished experiments
- Document remaining experiments
- Ensure no production code in dev/

## Import Patterns

Development code can import from production modules:
```python
# It's OK to import from production in dev/
from shypn.netobjs.place import Place
from shypn.data.canvas.document_model import DocumentModel

# But production should NEVER import from dev/
# ❌ WRONG: from shypn.dev.experiment import something
```

---

**Remember:** Code in `dev/` is for experimentation. When a feature is ready for production, move it to the appropriate module with proper error handling, documentation, and tests.
