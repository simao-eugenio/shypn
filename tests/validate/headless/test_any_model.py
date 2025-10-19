#!/usr/bin/env python3
"""
Universal Model Simulation Test

Tests any .shy model file for simulation correctness.
Can be used to validate imported models, verify simulation setup, or debug issues.

Usage:
    # Test a specific model
    python3 test_any_model.py --model path/to/model.shy
    
    # Test with custom step count
    python3 test_any_model.py --model path/to/model.shy --steps 50
    
    # Verbose output showing all steps
    python3 test_any_model.py --model path/to/model.shy --verbose
    
    # Show only summary
    python3 test_any_model.py --model path/to/model.shy --quiet
    
    # Test multiple models
    python3 test_any_model.py --model model1.shy model2.shy model3.shy

Examples:
    # Test Glycolysis
    python3 test_any_model.py --model workspace/projects/Flow_Test/models/Glycolysis_fresh_Gluconeogenesis.shy
    
    # Test with sources
    python3 test_any_model.py --model workspace/projects/Flow_Test/models/Glycolysis_fresh_WITH_SOURCES.shy --steps 100
"""

import sys
import os
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# Add src to path (go up 3 levels: headless -> validate -> tests -> project_root)
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root / 'src'))


class ModelTester:
    """Test runner for simulation models."""
    
    def __init__(self, model_path: str, steps: int = 20, verbose: bool = False, quiet: bool = False):
        self.model_path = Path(model_path)
        self.steps = steps
        self.verbose = verbose
        self.quiet = quiet
        self.results = {}
    
    def print_header(self, title: str, char: str = "="):
        """Print formatted header."""
        if not self.quiet:
            print()
            print(char * 80)
            print(title)
            print(char * 80)
            print()
    
    def print_info(self, message: str):
        """Print info message."""
        if not self.quiet:
            print(message)
    
    def print_detail(self, message: str):
        """Print detailed message (only in verbose mode)."""
        if self.verbose:
            print(message)
    
    def test_model(self) -> bool:
        """Run all tests on the model."""
        try:
            self.print_header(f"TESTING MODEL: {self.model_path.name}")
            
            if not self.model_path.exists():
                print(f"✗ Model file not found: {self.model_path}")
                return False
            
            self.print_info(f"Model path: {self.model_path}")
            print()
            
            # Test 1: Load model
            if not self._test_load_model():
                return False
            
            # Test 2: Check transition types
            if not self._test_transition_types():
                return False
            
            # Test 3: Create canvas manager
            if not self._test_canvas_manager():
                return False
            
            # Test 4: Create simulation controller
            if not self._test_simulation_controller():
                return False
            
            # Test 5: Check behaviors
            if not self._test_behaviors():
                return False
            
            # Test 6: Analyze model structure
            self._analyze_model()
            
            # Test 7: Run simulation
            if not self._test_simulation():
                return False
            
            # Summary
            self._print_summary()
            
            return True
            
        except Exception as e:
            print(f"✗ Unexpected error: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            return False
    
    def _test_load_model(self) -> bool:
        """Test 1: Load model from file."""
        self.print_info("=" * 80)
        self.print_info("TEST 1: Loading Model")
        self.print_info("=" * 80)
        
        try:
            from shypn.data.canvas.document_model import DocumentModel
            
            self.document = DocumentModel.load_from_file(str(self.model_path))
            
            self.print_info(f"✓ Model loaded successfully")
            self.print_info(f"  Places: {len(self.document.places)}")
            self.print_info(f"  Transitions: {len(self.document.transitions)}")
            self.print_info(f"  Arcs: {len(self.document.arcs)}")
            print()
            
            self.results['load'] = True
            return True
            
        except Exception as e:
            print(f"✗ Failed to load model: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            self.results['load'] = False
            return False
    
    def _test_transition_types(self) -> bool:
        """Test 2: Check all transitions have valid transition_type."""
        self.print_info("=" * 80)
        self.print_info("TEST 2: Checking Transition Types")
        self.print_info("=" * 80)
        
        transition_types = {}
        corrupted = []
        
        for t in self.document.transitions:
            ttype = getattr(t, 'transition_type', 'MISSING')
            if ttype == 'MISSING':
                corrupted.append(f"{t.name}: no transition_type attribute")
            elif ttype not in ['immediate', 'timed', 'stochastic', 'continuous']:
                corrupted.append(f"{t.name}: invalid type '{ttype}'")
            else:
                transition_types[ttype] = transition_types.get(ttype, 0) + 1
        
        if corrupted:
            print(f"✗ Found {len(corrupted)} transitions with invalid types:")
            for msg in corrupted[:10]:  # Show first 10
                print(f"    {msg}")
            if len(corrupted) > 10:
                print(f"    ... and {len(corrupted) - 10} more")
            print()
            self.results['transition_types'] = False
            return False
        else:
            self.print_info(f"✓ All transitions have valid transition_type!")
            for ttype, count in sorted(transition_types.items()):
                self.print_info(f"    {ttype}: {count}")
            print()
            self.results['transition_types'] = True
            self.transition_type_counts = transition_types
            return True
    
    def _test_canvas_manager(self) -> bool:
        """Test 3: Create canvas manager and load objects."""
        self.print_info("=" * 80)
        self.print_info("TEST 3: Creating Canvas Manager")
        self.print_info("=" * 80)
        
        try:
            from shypn.data.model_canvas_manager import ModelCanvasManager
            from shypn.core.controllers.document_controller import DocumentController
            
            doc_controller = DocumentController()
            self.canvas_manager = ModelCanvasManager(doc_controller)
            
            # Load objects (this registers observers)
            self.canvas_manager.load_objects(
                self.document.places,
                self.document.transitions,
                self.document.arcs
            )
            
            self.print_info(f"✓ Canvas manager created successfully")
            self.print_info(f"  Places loaded: {len(self.canvas_manager.places)}")
            self.print_info(f"  Transitions loaded: {len(self.canvas_manager.transitions)}")
            self.print_info(f"  Arcs loaded: {len(self.canvas_manager.arcs)}")
            print()
            
            self.results['canvas_manager'] = True
            return True
            
        except Exception as e:
            print(f"✗ Failed to create canvas manager: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            self.results['canvas_manager'] = False
            return False
    
    def _test_simulation_controller(self) -> bool:
        """Test 4: Create simulation controller."""
        self.print_info("=" * 80)
        self.print_info("TEST 4: Creating Simulation Controller")
        self.print_info("=" * 80)
        
        try:
            from shypn.engine.simulation.controller import SimulationController
            
            self.controller = SimulationController(self.canvas_manager)
            
            self.print_info(f"✓ Simulation controller created")
            self.print_info(f"  Initial time: {self.controller.time}")
            print()
            
            self.results['controller'] = True
            return True
            
        except Exception as e:
            print(f"✗ Failed to create simulation controller: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            self.results['controller'] = False
            return False
    
    def _test_behaviors(self) -> bool:
        """Test 5: Check that behaviors can be created for all transitions."""
        self.print_info("=" * 80)
        self.print_info("TEST 5: Checking Transition Behaviors")
        self.print_info("=" * 80)
        
        behavior_types = {}
        behavior_errors = []
        
        for t in self.canvas_manager.transitions:
            try:
                behavior = self.controller._get_behavior(t)
                btype = type(behavior).__name__
                behavior_types[btype] = behavior_types.get(btype, 0) + 1
            except Exception as e:
                behavior_errors.append(f"{t.name}: {e}")
        
        if behavior_errors:
            print(f"✗ Found {len(behavior_errors)} behavior errors:")
            for msg in behavior_errors[:10]:
                print(f"    {msg}")
            if len(behavior_errors) > 10:
                print(f"    ... and {len(behavior_errors) - 10} more")
            print()
            self.results['behaviors'] = False
            return False
        else:
            self.print_info(f"✓ All transitions have valid behaviors!")
            for btype, count in sorted(behavior_types.items()):
                self.print_info(f"    {btype}: {count}")
            print()
            self.results['behaviors'] = True
            self.behavior_type_counts = behavior_types
            return True
    
    def _analyze_model(self):
        """Test 6: Analyze model structure."""
        self.print_info("=" * 80)
        self.print_info("TEST 6: Model Structure Analysis")
        self.print_info("=" * 80)
        
        # Count tokens
        total_tokens = sum(p.tokens for p in self.canvas_manager.places)
        self.print_info(f"Total tokens: {total_tokens}")
        
        # Find source transitions
        sources = [t for t in self.canvas_manager.transitions 
                  if t.is_source or (hasattr(t, 'name') and 'SOURCE_' in str(t.name))]
        self.print_info(f"Source transitions: {len(sources)}")
        if sources and self.verbose:
            for src in sources[:10]:
                self.print_detail(f"  - {src.name} (rate: {src.rate})")
            if len(sources) > 10:
                self.print_detail(f"  ... and {len(sources) - 10} more")
        
        # Find sink transitions
        sinks = [t for t in self.canvas_manager.transitions if t.is_sink]
        self.print_info(f"Sink transitions: {len(sinks)}")
        if sinks and self.verbose:
            for sink in sinks[:10]:
                self.print_detail(f"  - {sink.name}")
            if len(sinks) > 10:
                self.print_detail(f"  ... and {len(sinks) - 10} more")
        
        # Count enabled transitions
        self.print_info(f"\nChecking structural enablement...")
        enabled_count = 0
        for trans in self.canvas_manager.transitions:
            try:
                behavior = self.controller._get_behavior(trans)
                can_fire, reason = behavior.can_fire()
                if can_fire:
                    enabled_count += 1
                    self.print_detail(f"  Enabled: {trans.name}")
            except:
                pass
        
        self.print_info(f"Structurally enabled: {enabled_count}/{len(self.canvas_manager.transitions)}")
        print()
        
        self.initial_tokens = total_tokens
        self.source_count = len(sources)
        self.sink_count = len(sinks)
        self.enabled_count = enabled_count
    
    def _test_simulation(self) -> bool:
        """Test 7: Run simulation steps."""
        self.print_info("=" * 80)
        self.print_info(f"TEST 7: Running Simulation ({self.steps} steps)")
        self.print_info("=" * 80)
        
        try:
            initial_tokens = sum(p.tokens for p in self.canvas_manager.places)
            self.print_info(f"Initial tokens: {initial_tokens:.2f}")
            self.print_info(f"Initial time: {self.controller.time:.3f}")
            print()
            
            if self.verbose:
                self.print_detail("Step-by-step execution:")
            
            steps_executed = 0
            for i in range(self.steps):
                result = self.controller.step()
                steps_executed += 1
                
                tokens_now = sum(p.tokens for p in self.canvas_manager.places)
                
                # Show steps based on verbosity
                if self.verbose:
                    # Show all steps
                    self.print_detail(f"  Step {i+1:3d}: tokens={tokens_now:8.2f}, time={self.controller.time:8.3f}, result={result}")
                elif not self.quiet:
                    # Show first 5 and last 5
                    if i < 5 or i >= self.steps - 5:
                        self.print_info(f"  Step {i+1:3d}: tokens={tokens_now:8.2f}, time={self.controller.time:8.3f}, result={result}")
                    elif i == 5:
                        self.print_info("  ...")
                
                if not result:
                    self.print_info(f"\n  Simulation stopped after {steps_executed} steps (no enabled transitions)")
                    break
            
            final_tokens = sum(p.tokens for p in self.canvas_manager.places)
            final_time = self.controller.time
            
            print()
            self.print_info(f"Simulation completed:")
            self.print_info(f"  Steps executed: {steps_executed}")
            self.print_info(f"  Final time: {final_time:.3f}")
            self.print_info(f"  Final tokens: {final_tokens:.2f}")
            
            token_change = final_tokens - initial_tokens
            self.print_info(f"  Token change: {token_change:+.2f}")
            
            # Interpretation
            print()
            if token_change > 0.01:
                self.print_info("✓ Tokens generated (sources working or token-producing transitions)")
            elif token_change < -0.01:
                self.print_info("✓ Tokens consumed (sinks working or token-consuming transitions)")
            elif abs(token_change) < 0.01:
                if self.source_count > 0 or self.sink_count > 0:
                    self.print_info("⚠ No token change (sources/sinks may not be firing)")
                else:
                    self.print_info("✓ Token conservation maintained (no sources/sinks)")
            
            print()
            
            self.results['simulation'] = True
            self.steps_executed = steps_executed
            self.final_tokens = final_tokens
            self.token_change = token_change
            return True
            
        except Exception as e:
            print(f"✗ Simulation failed: {e}")
            if self.verbose:
                import traceback
                traceback.print_exc()
            self.results['simulation'] = False
            return False
    
    def _print_summary(self):
        """Print test summary."""
        self.print_header("TEST SUMMARY", "=")
        
        all_passed = all(self.results.values())
        
        self.print_info("Test Results:")
        for test_name, passed in self.results.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            self.print_info(f"  {status}: {test_name}")
        
        print()
        self.print_info("Model Statistics:")
        self.print_info(f"  Places: {len(self.canvas_manager.places)}")
        self.print_info(f"  Transitions: {len(self.canvas_manager.transitions)}")
        self.print_info(f"  Arcs: {len(self.canvas_manager.arcs)}")
        
        if hasattr(self, 'transition_type_counts'):
            print()
            self.print_info("Transition Types:")
            for ttype, count in sorted(self.transition_type_counts.items()):
                self.print_info(f"  {ttype}: {count}")
        
        if hasattr(self, 'steps_executed'):
            print()
            self.print_info("Simulation Results:")
            self.print_info(f"  Steps executed: {self.steps_executed}")
            self.print_info(f"  Token change: {self.token_change:+.2f}")
            self.print_info(f"  Sources: {self.source_count}")
            self.print_info(f"  Sinks: {self.sink_count}")
        
        print()
        if all_passed:
            self.print_header("✓ ALL TESTS PASSED!", "=")
        else:
            self.print_header("✗ SOME TESTS FAILED", "=")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Test any .shy model file for simulation correctness',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Test a single model
  %(prog)s --model workspace/projects/Flow_Test/models/Glycolysis_fresh_Gluconeogenesis.shy
  
  # Test with more steps
  %(prog)s --model my_model.shy --steps 100
  
  # Verbose output
  %(prog)s --model my_model.shy --verbose
  
  # Test multiple models
  %(prog)s --model model1.shy model2.shy model3.shy
        """
    )
    
    parser.add_argument('--model', '-m', nargs='+', required=True,
                       help='Path(s) to .shy model file(s) to test')
    parser.add_argument('--steps', '-s', type=int, default=20,
                       help='Number of simulation steps to run (default: 20)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed output including all steps')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Show only summary (minimal output)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.verbose and args.quiet:
        print("Error: Cannot use --verbose and --quiet together")
        return 1
    
    models = args.model
    all_passed = True
    
    print("=" * 80)
    print("UNIVERSAL MODEL SIMULATION TEST")
    print("=" * 80)
    print(f"\nTesting {len(models)} model(s)")
    print(f"Steps per model: {args.steps}")
    print(f"Verbosity: {'verbose' if args.verbose else 'quiet' if args.quiet else 'normal'}")
    
    # Test each model
    for i, model_path in enumerate(models, 1):
        if len(models) > 1:
            print(f"\n{'=' * 80}")
            print(f"MODEL {i}/{len(models)}: {model_path}")
            print(f"{'=' * 80}")
        
        tester = ModelTester(
            model_path=model_path,
            steps=args.steps,
            verbose=args.verbose,
            quiet=args.quiet
        )
        
        passed = tester.test_model()
        if not passed:
            all_passed = False
    
    # Overall summary for multiple models
    if len(models) > 1:
        print("\n" + "=" * 80)
        print("OVERALL SUMMARY")
        print("=" * 80)
        print(f"Models tested: {len(models)}")
        if all_passed:
            print("✓ All models passed all tests!")
        else:
            print("✗ Some models failed tests")
        print()
    
    return 0 if all_passed else 1


if __name__ == '__main__':
    sys.exit(main())
