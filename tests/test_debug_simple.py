"""Minimal debug test to see where parallel hangs."""
import time
from tests.test_integration_parallel import BiochemicalModel
from src.shypn.topology.behavioral.reachability import ReachabilityAnalyzer

print("Creating model...")
model = BiochemicalModel()
print("Creating analyzer...")
analyzer = ReachabilityAnalyzer(model)

print("\n=== Testing Sequential ===")
start = time.time()
result = analyzer.analyze(max_states=5000, parallel=False)
elapsed = time.time() - start
print(f"Sequential: {result.get('total_states')} states in {elapsed:.3f}s")

print("\n=== Testing Parallel ===")
print("Starting parallel with 2 workers...")
start = time.time()
result = analyzer.analyze(max_states=5000, parallel=True, num_workers=2)
elapsed = time.time() - start
print(f"Parallel: {result.get('total_states')} states in {elapsed:.3f}s")
