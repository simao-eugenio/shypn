# Active TODO Items

**Date:** November 5, 2025  
**Status:** 4 active items requiring attention

## Overview

This document tracks active development items that need testing, verification, or completion. Items are prioritized by blocking status and user impact.

---

## 1. BRENDA API - Awaiting Response ⏳

**Status:** BLOCKED - Awaiting external response  
**Priority:** Medium  
**Blocker:** BRENDA support team response

### Current State
- ✅ BRENDA SOAP client implemented (`src/shypn/data/brenda_soap_client.py`)
- ✅ Authentication working (handshake successful)
- ❌ Free academic accounts return empty data from API
- ⏳ Awaiting response from BRENDA support (info@brenda-enzymes.org)

### Implementation Details
```python
# Location: src/shypn/data/brenda_soap_client.py
class BRENDAAPIClient:
    """Client for BRENDA SOAP API."""
    
    WSDL_URL = "https://www.brenda-enzymes.org/soap/brenda_server.php?wsdl"
    
    def authenticate(self):
        """Authenticate with BRENDA API and establish SOAP client session."""
        # Authentication works ✓
        # But data access returns empty for free accounts ✗
```

### Issue
Free academic accounts can authenticate but receive no data from SOAP API calls. This is a known limitation mentioned in BRENDA documentation.

### Next Steps
1. ⏳ **Wait for BRENDA support response** regarding:
   - Full API access for academic institutions
   - Alternative data access methods
   - Pricing/licensing for SOAP API access
   
2. 🔄 **Alternative approach** (if needed):
   - Parse BRENDA web interface (HTML scraping)
   - Use BRENDA download files (requires manual download)
   - Focus on SABIO-RK and other sources

### Related Files
- `src/shypn/data/brenda_soap_client.py` - SOAP client implementation
- `src/shypn/ui/panels/pathway_operations/brenda_category.py` - UI integration
- `tests/diagnostic/test_brenda_auth.py` - Authentication tests
- `tests/diagnostic/test_brenda_manual.py` - Manual testing script

### Testing
```bash
# Test authentication (works)
python tests/diagnostic/test_brenda_auth.py

# Test manual parameter format
python tests/diagnostic/test_brenda_parameter_format.py
```

---

## 2. SABIO-RK - Need Batch vs Single Fetch Tests ⚠️

**Status:** NEEDS TESTING  
**Priority:** High  
**Impact:** Performance and reliability

### Current State
- ✅ Single fetch implemented and working
- ✅ Batch fetch implemented (`apply_batch()`)
- ❌ No systematic tests comparing single vs batch
- ❌ No performance benchmarks
- ❌ Timeout behavior not validated

### Implementation Details
```python
# Location: src/shypn/helpers/sabio_rk_enrichment_controller.py

def apply_batch(self, transition_ids: List[str], batch_size: int = 10):
    """Apply SABIO-RK parameters to multiple transitions in batches."""
    # Batching implemented with 2-second delays
    # But not thoroughly tested ⚠️

# Location: src/shypn/data/sabio_rk_client.py

class SabioRKClient:
    def fetch_kinetics(self, ec_number: str, organism: str, timeout: int = 30):
        """Single fetch with timeout."""
        # Works but timeout behavior needs validation
```

### Issues to Test

#### 2.1 Single Fetch Behavior
- ✓ Basic fetch works
- ❓ Timeout handling (30s default)
- ❓ Rate limiting behavior
- ❓ Error recovery
- ❓ Empty result handling

#### 2.2 Batch Fetch Behavior
- ✓ Basic batching works (10 items per batch)
- ❓ Optimal batch size (currently 10)
- ❓ Delay between batches (currently 2s)
- ❓ Batch failure recovery
- ❓ Progress reporting accuracy
- ❓ Memory usage with large batches

#### 2.3 Performance Comparison
- ❓ Single vs batch speed
- ❓ API rate limit thresholds
- ❓ Network overhead
- ❓ Memory efficiency

### Required Tests

Create `tests/validation/sabio_rk/test_fetch_strategies.py`:

```python
class TestSabioRKFetchStrategies:
    """Test single vs batch fetching strategies."""
    
    def test_single_fetch_timeout(self):
        """Test single fetch timeout behavior."""
        # Test with short timeout
        # Verify exception handling
        # Check partial results
        
    def test_batch_fetch_completion(self):
        """Test batch fetch completes all items."""
        # Fetch 25 transitions (3 batches)
        # Verify all processed
        # Check delay between batches
        
    def test_batch_size_impact(self):
        """Test different batch sizes."""
        # Test batch_size = 5, 10, 20, 50
        # Measure completion time
        # Check for API rate limiting
        
    def test_error_recovery(self):
        """Test error handling in batch mode."""
        # Include invalid EC numbers
        # Verify batch continues
        # Check error reporting
        
    def test_memory_usage(self):
        """Test memory efficiency of batching."""
        # Process 100 transitions
        # Monitor memory usage
        # Verify cleanup
```

### Next Steps
1. 🔥 **Create comprehensive test suite** (high priority)
2. 📊 **Run performance benchmarks** on real KEGG models
3. 🔧 **Tune batch parameters** based on results
4. 📝 **Document best practices** for users

### Related Files
- `src/shypn/data/sabio_rk_client.py` - Client implementation
- `src/shypn/helpers/sabio_rk_enrichment_controller.py` - Batch controller
- `src/shypn/ui/panels/pathway_operations/sabio_rk_category.py` - UI
- `tests/diagnostic/check_sabio_count.py` - Count diagnostic

---

## 3. Heuristics - Best Inference for Limited Metadata Models 🎯

**Status:** NEEDS IMPROVEMENT  
**Priority:** High  
**Impact:** Quality of parameter inference

### Current State
- ✅ Heuristic engine implemented (`HeuristicInferenceEngine`)
- ✅ Multi-source inference (KEGG, SABIO-RK, structure)
- ✅ Confidence scoring system
- ❌ Limited metadata models get poor results
- ❌ Fallback strategies not comprehensive

### Implementation Details
```python
# Location: src/shypn/crossfetch/inference/heuristic_engine.py

class HeuristicInferenceEngine:
    """Intelligent parameter inference from multiple sources."""
    
    CONFIDENCE_THRESHOLDS = {
        'high': 0.9,      # Direct match from database
        'medium': 0.7,    # Partial match or structure inference
        'low': 0.5,       # Weak inference, needs validation
        'guess': 0.3      # Last resort fallback
    }
    
    def infer_km(self, transition, substrate_info):
        """Infer Km parameter."""
        # Priority 1: KEGG metadata ✓
        # Priority 2: SABIO-RK fetch ✓
        # Priority 3: Structure-based ⚠️ (needs improvement)
        # Priority 4: Fallback defaults ⚠️ (too generic)
```

### Problem Cases

#### 3.1 Minimal Metadata Models
**Example:** BioModels with only transition IDs and basic structure

Current behavior:
- Falls back to generic defaults (Km=1.0, Vmax=10.0)
- Confidence marked as "guess" (0.3)
- No use of structural patterns

Needed improvements:
- Analyze network topology (substrate/product patterns)
- Use statistical distributions from similar pathways
- Apply reaction type heuristics (e.g., phosphorylation vs hydrolysis)

#### 3.2 Cross-Species Inference
**Example:** KEGG pathway for organism without specific parameters

Current behavior:
- Uses default values if exact organism match not found
- No cross-species scaling

Needed improvements:
- Use closely related species data
- Apply phylogenetic scaling factors
- Mark confidence appropriately

#### 3.3 Uncommon Reaction Types
**Example:** Reactions not well-represented in SABIO-RK

Current behavior:
- Falls back to defaults immediately

Needed improvements:
- Analyze similar reaction mechanisms
- Use chemical similarity metrics
- Apply class-based defaults (e.g., kinase class averages)

### Enhancement Plan

#### Phase 1: Topology-Based Inference
```python
def infer_from_topology(self, transition, context):
    """Infer parameters from network topology."""
    
    # Analyze local structure
    - Count input/output arcs
    - Check for catalysts (test arcs)
    - Identify inhibitors
    
    # Pattern matching
    - Branch points → lower affinity
    - Linear chains → moderate affinity
    - Feedback loops → tight regulation
    
    # Apply heuristics
    return parameters, confidence
```

#### Phase 2: Statistical Distributions
```python
def infer_from_statistics(self, reaction_type, organism_group):
    """Use statistical distributions from databases."""
    
    # Query cached statistics
    - Median/mean Km for reaction class
    - Standard deviation
    - Organism-specific adjustments
    
    # Sample from distribution
    return parameters, confidence
```

#### Phase 3: Chemical Similarity
```python
def infer_from_similarity(self, substrate, product):
    """Use chemical similarity to known substrates."""
    
    # Compute similarity metrics
    - Molecular weight comparison
    - Functional group matching
    - Reaction mechanism similarity
    
    # Find similar reactions
    # Scale parameters based on similarity
    return parameters, confidence
```

### Required Tests

Create `tests/validation/heuristic/test_inference_quality.py`:

```python
class TestInferenceQuality:
    """Test quality of parameter inference with limited metadata."""
    
    def test_minimal_metadata_model(self):
        """Test inference on model with only IDs."""
        # Load stripped-down model
        # Run inference
        # Verify reasonable parameters (not all defaults)
        
    def test_topology_based_inference(self):
        """Test topology analysis improves inference."""
        # Create test topology patterns
        # Verify different patterns get different parameters
        
    def test_cross_species_inference(self):
        """Test inference across species."""
        # Use human pathway data
        # Infer for mouse model
        # Verify scaled parameters
        
    def test_confidence_scoring(self):
        """Test confidence scores match quality."""
        # High confidence → should match database
        # Low confidence → should flag for review
```

### Next Steps
1. 🔬 **Analyze failure cases** from real models
2. 🧠 **Implement topology-based inference**
3. 📊 **Build statistical parameter database**
4. 🧪 **Create comprehensive test suite**
5. 📈 **Benchmark improvements** on test models

### Related Files
- `src/shypn/crossfetch/inference/heuristic_engine.py` - Core inference
- `src/shypn/crossfetch/controllers/heuristic_parameters_controller.py` - Controller
- `src/shypn/ui/panels/pathway_operations/heuristic_parameters_category.py` - UI
- `doc/HEURISTIC_PARAMETERS_COMPLETE.md` - Documentation

---

## 4. Simulation Hangs After Applying Parameters ✅ FIXED

**Status:** ✅ FIXED - Attribute name mismatch prevented simulation reset  
**Priority:** 🔴 CRITICAL (was blocking immediate usability)  
**Impact:** Users can now run simulations after applying heuristic parameters

### Problem Description

After applying heuristic parameters to transitions, the simulation hung when user tried to step/run.
This completely blocked the heuristics workflow:
1. Load KEGG model ✅
2. Apply heuristic parameters ✅
3. Parameters appear in transitions ✅
4. Click "Run Simulation" ❌ **HUNG**
5. No error messages ❌
6. Reset button didn't help ❌

### Root Cause Identified

**Attribute Name Mismatch** in `heuristic_parameters_category.py`:
- Stored as: `self.model_canvas_loader` (line 44 in `__init__`)
- Used as: `self.canvas_loader` (lines 447, 451, 457, 458, 459, 462 in reset method)

Result: The `_reset_simulation_after_parameter_changes()` method **never executed** because
the attribute check `if not self.canvas_loader:` always evaluated to True (attribute doesn't exist).

Without reset:
- Simulation controller's behavior cache contained stale TransitionBehavior instances
- Old parameter values cached (Km, Vmax, rate functions)
- Transitions evaluated with incorrect rates
- Enablement checks used outdated state
- Simulation hung or behaved incorrectly

### Fix Implemented

**File:** `src/shypn/ui/panels/pathway_operations/heuristic_parameters_category.py`

Changed all occurrences in `_reset_simulation_after_parameter_changes()`:
```python
# BEFORE (broken):
if not self.canvas_loader:  # Always None - attribute doesn't exist
    return

drawing_area = self.canvas_loader.get_current_document()  # Never reached

# AFTER (fixed):
if not self.model_canvas_loader:  # Correct attribute name
    return

drawing_area = self.model_canvas_loader.get_current_document()  # Now works
```

Lines affected: 447, 451, 457, 458, 459, 462

Now the reset properly executes:
1. Gets current document via `model_canvas_loader.get_current_document()`
2. Finds simulation controller for that document
3. Gets canvas manager
4. Calls `controller.reset_for_new_model(canvas_manager)` (comprehensive reset)
5. Clears behavior cache, recreates model adapter, resets all state

### Test Created

**File:** `tests/test_simulation_reset_after_parameters.py`

5 unit tests validate:
1. ✅ Attribute name consistency (model_canvas_loader stored and used)
2. ✅ Reset called after parameter application
3. ✅ Fallback to basic reset if canvas_manager missing
4. ✅ Graceful handling when simulation controller missing
5. ✅ Graceful handling when model_canvas_loader is None

**Test Results:** All 5 tests pass ✅

### Historical Context

The reset code was correctly implemented with comprehensive documentation:
- Proper `reset_for_new_model()` call (not just basic `reset()`)
- Detailed comments explaining behavior cache issues
- References to past bugs (commit 864ae92, df037a6, be02ff5)
- Clear understanding of why reset is needed

But the code **never executed** due to simple typo in attribute name. This demonstrates
the importance of:
1. ✅ Integration tests (would have caught this)
2. ✅ Manual testing after implementation
3. ✅ Code review (easily spotted during review)

### Impact

This bug existed since heuristic parameters feature was added. Affected:
- All users applying heuristic parameters to KEGG models
- Any workflow using automated parameter inference
- Integration with SABIO-RK and other parameter sources

### Verification Recommended

While unit tests confirm the code path is fixed, manual verification with real models:
1. Load KEGG model (e.g., `eco00010.shy` or any KEGG model)
2. Open Heuristic Parameters panel
3. Click "Analyze & Infer Parameters"
4. Select transitions and apply parameters
5. Open Simulation panel
6. Initialize simulation and step multiple times
7. ✅ **Verify: Transitions fire correctly with new parameter values**
8. ✅ **Verify: No simulation hang or freeze**

### Related Files
- ✅ `src/shypn/ui/panels/pathway_operations/heuristic_parameters_category.py` - Fixed
- ✅ `tests/test_simulation_reset_after_parameters.py` - Test created
- 📝 `src/shypn/engine/simulation/controller.py` - Reset implementation (already correct)
- 📝 `src/shypn/crossfetch/controllers/heuristic_parameters_controller.py` - Apply logic (already correct)

---

## PREVIOUSLY INVESTIGATED (Bug was simpler than expected):

### Suspected Causes (NOT the issue)
        raise ValueError(f"Invalid Km: {parameters['km']}")
    
    # Validate Vmax > 0
    if parameters.get('vmax', 0) <= 0:
        raise ValueError(f"Invalid Vmax: {parameters['vmax']}")
    
    # Validate rate function syntax
    try:
        compile(rate_function, '<string>', 'eval')
    except SyntaxError as e:
        raise ValueError(f"Invalid rate function: {e}")
```

#### Step 3: Force Reset After Apply
```python
# Ensure simulation is reset after parameter changes

def apply_parameters(self, transition_id, parameters):
    """Apply parameters and reset simulation."""
    
    # Apply parameters
    self._apply_parameters_internal(transition_id, parameters)
    
    # FORCE RESET
    if self.simulation_controller:
        self.simulation_controller.reset()
        logger.info("[HEURISTIC] Simulation reset after parameter apply")
```

### Required Diagnostic Script

Create `scripts/diagnose_simulation_hang.py`:

```python
"""Diagnose simulation hang after parameter application."""

import logging
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.crossfetch.controllers import HeuristicParametersController
from shypn.engine.simulation.controller import SimulationController

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def diagnose_hang(model_path):
    """Diagnose simulation hang."""
    
    # Load model
    logger.info(f"Loading model: {model_path}")
    manager = ModelCanvasManager.load_from_file(model_path)
    
    # Apply heuristics
    logger.info("Applying heuristic parameters...")
    controller = HeuristicParametersController(manager)
    controller.infer_all_parameters()
    
    # Validate all transitions
    logger.info("Validating transitions...")
    for trans in manager.document_controller.transitions:
        logger.info(f"  {trans.id}:")
        logger.info(f"    Type: {trans.transition_type}")
        logger.info(f"    Rate: {trans.properties.get('rate_function')}")
        
        # Try to evaluate rate
        try:
            # Mock evaluation
            rate = trans.evaluate_rate({})
            logger.info(f"    Evaluation: OK (rate={rate})")
        except Exception as e:
            logger.error(f"    Evaluation: FAILED - {e}")
    
    # Try simulation
    logger.info("Starting simulation...")
    sim = SimulationController(manager)
    
    try:
        for i in range(10):
            logger.info(f"  Step {i+1}/10...")
            sim.step(time_step=0.1)
            logger.info(f"    Success! Time={sim.current_time}")
    except Exception as e:
        logger.error(f"  HANG at step {i+1}: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import sys
    diagnose_hang(sys.argv[1])
```

### Next Steps
1. 🔥 **URGENT: Create diagnostic script** (above)
2. 🔍 **Run on affected models** to identify exact hang point
3. 🐛 **Fix identified issues** (likely reset or validation)
4. ✅ **Add validation** to parameter application
5. 🧪 **Create regression tests** to prevent recurrence

### Related Files
- `src/shypn/engine/simulation/controller.py` - Simulation controller
- `src/shypn/crossfetch/controllers/heuristic_parameters_controller.py` - Parameter application
- `src/shypn/engine/transition_behavior.py` - Rate evaluation
- `doc/SIMULATION_RESET_IMPLEMENTATION.md` - Reset documentation

### Testing
```bash
# Run diagnostic on affected model
python scripts/diagnose_simulation_hang.py workspace/projects/models/hsa00010.shy

# Test with verbose logging
LOGLEVEL=DEBUG python src/shypn.py
# Load model → Apply parameters → Try simulate → Check logs
```

---

## Priority Order

1. **🔥 CRITICAL: Simulation Hang (#4)** - Blocks users immediately
2. **📊 HIGH: SABIO-RK Tests (#2)** - Needed for production reliability
3. **🎯 HIGH: Heuristics Improvement (#3)** - Affects quality of results
4. **⏳ MEDIUM: BRENDA Response (#1)** - Waiting on external dependency

## Related Documentation

- `doc/HEURISTIC_PARAMETERS_COMPLETE.md` - Heuristics system
- `doc/SIMULATION_RESET_IMPLEMENTATION.md` - Reset implementation
- `doc/SABIO_RK_ENHANCEMENTS.md` - SABIO-RK features
- `doc/validation/CONTINUOUS_CHAIN_EQUILIBRIUM_ANALYSIS.md` - Simulation validation

## Last Updated

**Date:** November 5, 2025  
**By:** Development team  
**Next Review:** After addressing simulation hang issue
