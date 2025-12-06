# Week 1 Platform Development - Progress Log

## Overview
Building three facade classes that bridge CLI tools to core SHYpn platform:
1. **ReplicateRunner** - Run multiple simulation replicates with statistical analysis
2. **BatchProcessor** - Process multiple models with error isolation
3. **Export API** - Programmatic data export from DataCollector

## Timeline
- **Day 1-2**: ReplicateRunner ✅ **COMPLETED**
- **Day 3**: Export API ⏳ NEXT
- **Day 4-5**: BatchProcessor ⏳ TODO

---

## Day 1-2: ReplicateRunner ✅ COMPLETED

### Implementation Summary
Created `src/shypn/engine/simulation/replicate_runner.py` (456 lines)

**Core Class**: `ReplicateRunner`
- Takes `DocumentModel` in constructor
- Wraps existing `SimulationController` for each replicate
- Manages random seed assignment
- Collects trajectory data
- Computes statistics (NumPy)
- Exports to CSV and JSON

### Key Methods

#### 1. `run_replicates(n=1000, **kwargs)`
**Purpose**: Run n simulation replicates with different random seeds

**Parameters**:
- `n`: Number of replicates (default: 1000)
- `use_parallel`: Enable parallel execution (default: True)
- `use_tau_leaping`: Enable τ-leaping (default: True)
- `duration`: Simulation duration in time units
- `tau_epsilon`: τ-leaping accuracy (default: 0.03)
- `seed_base`: Base seed for reproducibility (default: 42)
- `verbose`: Progress messages (default: False)

**Returns**: `List[Dict[str, Any]]` - One dict per replicate containing:
```python
{
    'replicate_id': int,
    'seed': int,
    'time_points': List[float],
    'place_data': Dict[place_id, List[float]],  # Trajectory for each species
    'transition_data': Dict[transition_id, List[float]],  # Firing rates
    'final_marking': Dict[place_id, float],  # Final state
    'simulation_time': float  # Wall-clock time
}
```

**Error Handling**: Failed replicates stored with:
```python
{
    'replicate_id': int,
    'seed': int,
    'error': str  # Error message
}
```

**Example**:
```python
from shypn.engine.simulation.replicate_runner import ReplicateRunner

runner = ReplicateRunner(model)
results = runner.run_replicates(
    n=1000,
    use_parallel=True,
    use_tau_leaping=True,
    duration=100.0,
    verbose=True
)
```

#### 2. `compute_statistics(results, percentiles=[25,50,75])`
**Purpose**: Compute statistical measures across replicates

**Parameters**:
- `results`: List of replicate results from `run_replicates()`
- `percentiles`: List of percentiles to compute (default: 25, 50, 75)

**Returns**: `Dict[str, Any]` containing:
```python
{
    'n_replicates': int,
    'successful_replicates': int,
    'failed_replicates': int,
    'time_points': List[float],  # Common time grid (from first replicate)
    'species_statistics': {
        'place_id': {
            'mean': np.ndarray,      # Mean trajectory
            'std': np.ndarray,       # Standard deviation
            'min': np.ndarray,       # Minimum value at each timepoint
            'max': np.ndarray,       # Maximum value
            'cv': np.ndarray,        # Coefficient of variation (std/mean)
            'percentile_25': np.ndarray,  # 25th percentile
            'percentile_50': np.ndarray,  # Median
            'percentile_75': np.ndarray   # 75th percentile
        },
        ...  # One dict per species
    }
}
```

**Notes**:
- Uses NumPy for efficient computation
- CV (coefficient of variation) measures relative variability
- All arrays aligned with `time_points`
- Handles missing data gracefully (warns if trajectory lengths differ)

**Example**:
```python
stats = runner.compute_statistics(results, percentiles=[5, 25, 50, 75, 95])
species_mean = stats['species_statistics']['S1']['mean']
species_cv = stats['species_statistics']['S1']['cv']
```

#### 3. `export_trajectories_csv(results, filepath, format='wide')`
**Purpose**: Export trajectory data to CSV

**Parameters**:
- `results`: List of replicate results
- `filepath`: Output CSV file path
- `format`: 'wide' or 'long' (default: 'wide')

**CSV Formats**:

**Wide format** (matrix style):
```
replicate_id,time,S1,S2,S3,...
0,0.0,100,50,25,...
0,0.1,98,52,24,...
0,0.2,96,54,23,...
1,0.0,100,50,25,...
...
```
- One row per observation (replicate × timepoint)
- Species as columns
- Easy for Excel/spreadsheet analysis

**Long format** (tidy data):
```
replicate_id,time,species,value
0,0.0,S1,100
0,0.0,S2,50
0,0.0,S3,25
0,0.1,S1,98
0,0.1,S2,52
...
```
- One row per measurement
- Species stacked vertically
- Ideal for ggplot2, seaborn, Plotly
- Database-friendly structure

**Example**:
```python
# Wide format for Excel
runner.export_trajectories_csv(results, 'results_wide.csv', format='wide')

# Long format for ggplot2
runner.export_trajectories_csv(results, 'results_tidy.csv', format='long')
```

#### 4. `export_statistics_json(statistics, filepath)`
**Purpose**: Export statistics to JSON

**Parameters**:
- `statistics`: Dict from `compute_statistics()`
- `filepath`: Output JSON file path

**JSON Structure**:
```json
{
  "n_replicates": 1000,
  "successful_replicates": 998,
  "failed_replicates": 2,
  "time_points": [0.0, 0.1, 0.2, ...],
  "species_statistics": {
    "S1": {
      "mean": [100.0, 98.5, 97.2, ...],
      "std": [0.0, 2.3, 3.1, ...],
      "min": [100.0, 92.0, 88.0, ...],
      "max": [100.0, 105.0, 108.0, ...],
      "cv": [0.0, 0.023, 0.032, ...],
      "percentile_25": [100.0, 96.5, 94.8, ...],
      "percentile_50": [100.0, 98.0, 97.0, ...],
      "percentile_75": [100.0, 100.5, 99.5, ...]
    },
    ...
  }
}
```

**Example**:
```python
stats = runner.compute_statistics(results)
runner.export_statistics_json(stats, 'statistics.json')
```

### Internal Implementation Details

#### `_reset_model(model)`
**Purpose**: Reset all places to initial marking

```python
def _reset_model(self, model):
    """Reset model to initial state."""
    for place in model.places:
        place.tokens = place.initial_tokens
```

Called before each replicate to ensure consistent starting conditions.

#### `_export_wide(results, filepath)`
**Purpose**: Helper for wide-format CSV export

Creates matrix with:
- Rows: replicate × timepoint combinations
- Columns: replicate_id, time, species1, species2, ..., speciesN

#### `_export_long(results, filepath)`
**Purpose**: Helper for long-format (tidy) CSV export

Creates table with:
- Columns: replicate_id, time, species, value
- Rows: replicate × timepoint × species (stacked)

### Integration with Existing Platform

**Dependencies**:
```python
from shypn.engine.simulation.controller import SimulationController
from shypn.engine.simulation.data_collector import DataCollector
from shypn.engine.simulation.settings import SimulationSettings
```

**How ReplicateRunner uses SimulationController**:
1. Creates new controller for each replicate: `controller = SimulationController(model)`
2. Configures settings:
   ```python
   controller.settings.use_parallel_stochastic = use_parallel
   controller.settings.use_tau_leaping = use_tau_leaping
   controller.settings.tau_epsilon = tau_epsilon
   controller.settings.random_seed = seed_base + i
   ```
3. Starts data collection: `controller.data_collector.start_collection()`
4. Runs simulation: `controller.run(duration=duration)`
5. Extracts data:
   ```python
   time_points = controller.data_collector.time_points
   place_data = {place.id: controller.data_collector.place_data[place.id] 
                 for place in model.places}
   ```

### Testing

**Test File**: `tests/engine/simulation/test_replicate_runner.py` (gitignored)

**Test Strategy**: Mock model for basic initialization
```python
class MockModel:
    def __init__(self):
        self.places = [MockPlace(f'S{i}', tokens=100) for i in range(3)]
        self.transitions = [MockTransition(f'T{i}') for i in range(2)]

runner = ReplicateRunner(MockModel())
# ✅ Initialization test passed
```

**Future Integration Tests** (Week 2):
- Test with simple SBML model
- Verify statistical computations
- Validate CSV export formats
- Check error handling for failed replicates

### Commit Details
- **Commit**: 9352445
- **Message**: "feat: Add ReplicateRunner facade for experimental validation"
- **Files**: `src/shypn/engine/simulation/replicate_runner.py` (456 lines)
- **Timestamp**: 2024-01-XX (Day 1-2 of Week 1)

---

## Day 3: Export API ⏳ NEXT

### Objectives
Extend `DataCollector` with programmatic export methods.

### Tasks
1. Add `get_data()` method to DataCollector
2. Add `export_csv(filepath, format='wide')` method
3. Add `export_json(filepath)` method
4. Wire to existing exporters in `shypn.reporting.exporters`

### Implementation Plan

**File**: `src/shypn/engine/simulation/data_collector.py`

**New Methods**:
```python
def get_data(self) -> Dict[str, Any]:
    """Return data in format expected by exporters."""
    return {
        'time_points': self.time_points,
        'place_data': self.place_data,
        'transition_data': self.transition_data,
        'model': self.model  # Reference to model for metadata
    }

def export_csv(self, filepath: str, format: str = 'wide') -> None:
    """Export time-series to CSV.
    
    Args:
        filepath: Output file path
        format: 'wide' (matrix) or 'long' (tidy) format
    """
    from shypn.reporting.exporters import CSVSimulationExporter
    exporter = CSVSimulationExporter(self.get_data(), {})
    
    if format == 'wide':
        exporter.export_timeseries_wide(filepath)
    elif format == 'long':
        exporter.export_timeseries_long(filepath)
    else:
        raise ValueError(f"Unknown format: {format}")

def export_json(self, filepath: str) -> None:
    """Export data to JSON.
    
    Args:
        filepath: Output JSON file path
    """
    from shypn.reporting.exporters import JSONSimulationExporter
    exporter = JSONSimulationExporter(self.get_data(), {})
    exporter.export_full(filepath)
```

**Integration with ReplicateRunner**:
```python
# Current (manual):
time_points = controller.data_collector.time_points
place_data = {place.id: controller.data_collector.place_data[place.id] 
              for place in model.places}

# After Export API (cleaner):
data = controller.data_collector.get_data()
time_points = data['time_points']
place_data = data['place_data']
```

**Success Criteria**:
- ✅ `get_data()` returns dict with all trajectory data
- ✅ `export_csv()` creates valid wide-format CSV
- ✅ `export_csv(format='long')` creates valid tidy CSV
- ✅ `export_json()` creates valid JSON file
- ✅ Works with existing CSVSimulationExporter and JSONSimulationExporter
- ✅ No breaking changes to existing DataCollector API

---

## Day 4-5: BatchProcessor ⏳ TODO

### Objectives
Create facade for processing multiple models with error isolation.

### Implementation Plan

**File**: `src/shypn/data/batch/batch_processor.py` (NEW)

**Class**: `BatchProcessor`

**Methods**:
```python
class BatchProcessor:
    def __init__(self):
        """Initialize batch processor."""
        pass
    
    def load_from_csv(self, csv_path: str) -> List[Tuple[str, Path]]:
        """Load batch specification from CSV.
        
        CSV Format:
        model_id,model_path
        Model1,/path/to/model1.sbml
        Model2,/path/to/model2.xml
        ...
        
        Returns:
            List of (model_id, model_path) tuples
        """
        pass
    
    def process_batch(
        self, 
        models: List[Tuple[str, Path]], 
        processor_func: Callable,
        parallel: bool = False
    ) -> Dict[str, Any]:
        """Process batch of models.
        
        Args:
            models: List of (model_id, model_path) tuples
            processor_func: Function to apply to each model
                           Signature: func(model_id, model_path) -> result
            parallel: Use multiprocessing (default: False)
        
        Returns:
            Dict with:
            {
                'successful': {model_id: result, ...},
                'failed': {model_id: error_message, ...},
                'n_successful': int,
                'n_failed': int
            }
        """
        pass
    
    def export_results(
        self, 
        results: Dict[str, Any], 
        output_dir: Path
    ) -> None:
        """Export batch results.
        
        Creates:
        - batch_summary.json: Overall statistics
        - successful_models.csv: List of successful models
        - failed_models.csv: List with error messages
        """
        pass
```

**Error Isolation**:
```python
for model_id, model_path in models:
    try:
        result = processor_func(model_id, model_path)
        successful[model_id] = result
    except Exception as e:
        failed[model_id] = str(e)
        logging.error(f"Failed to process {model_id}: {e}")
```

**Integration with ReplicateRunner**:
```python
from shypn.data.batch.batch_processor import BatchProcessor
from shypn.engine.simulation.replicate_runner import ReplicateRunner

def process_model(model_id, model_path):
    """Process single model with replicates."""
    # Load model
    parser = SBMLParser()
    pathway = parser.parse_file(model_path)
    converter = PathwayConverter()
    model = converter.convert(pathway)
    
    # Run replicates
    runner = ReplicateRunner(model)
    results = runner.run_replicates(n=1000, duration=100.0)
    stats = runner.compute_statistics(results)
    
    return stats

# Process batch
processor = BatchProcessor()
models = processor.load_from_csv('biomodels_batch.csv')
results = processor.process_batch(models, process_model)
processor.export_results(results, Path('batch_results/'))
```

**Success Criteria**:
- ✅ `load_from_csv()` parses batch specification
- ✅ `process_batch()` handles errors without crashing
- ✅ Failed models logged but don't stop batch
- ✅ `export_results()` creates summary files
- ✅ Integration test with 10 SBML models

---

## Week 1 Summary

### Deliverables ✅
1. **ReplicateRunner** (456 lines) ✅ DONE
   - Run n replicates with different seeds
   - Compute statistics (mean, std, CV, percentiles)
   - Export to CSV (wide/long) and JSON
   
2. **Export API** ⏳ IN PROGRESS (Day 3)
   - `get_data()`, `export_csv()`, `export_json()` methods
   - Integration with existing exporters
   
3. **BatchProcessor** ⏳ TODO (Day 4-5)
   - Load batch from CSV
   - Process with error isolation
   - Export results

### Architecture Impact
Created **Facade Layer** between CLI and Core Platform:
```
CLI Tools (Week 2)
    ↓ uses
Facade Layer (Week 1) ← ReplicateRunner, BatchProcessor, Export API
    ↓ uses
Core Platform (existing) ← SimulationController, DataCollector, Settings
```

### Next Steps (Week 2)
After Week 1 platform development completes:
1. Implement 9 CLI tool stubs in `cli/experimental/`
2. Wire CLI tools to ReplicateRunner and BatchProcessor
3. Test full workflow: CLI → Facade → Platform
4. Begin experimental validation for Paper 2

---

## Files Created
- ✅ `src/shypn/engine/simulation/replicate_runner.py` (456 lines)
- ⏳ `src/shypn/engine/simulation/data_collector.py` (extend with 3 methods)
- ⏳ `src/shypn/data/batch/batch_processor.py` (NEW, ~200 lines)

## Commits
- ✅ 9352445: "feat: Add ReplicateRunner facade for experimental validation"
- ⏳ Next: "feat: Add Export API to DataCollector"
- ⏳ Next: "feat: Add BatchProcessor for model batch processing"
