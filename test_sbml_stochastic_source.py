#!/usr/bin/env python3
"""
Test that stochastic source transitions work correctly in SBML models.

This test:
1. Loads an SBML model
2. Adds a stochastic source transition (T→P with is_source=True)
3. Runs simulation for N steps
4. Verifies tokens are being generated
"""
import sys
import json
sys.path.insert(0, 'src')

from shypn.data.canvas.document_model import DocumentModel
from shypn.data.model_canvas_manager import ModelCanvasManager
from shypn.engine.simulation.controller import SimulationController

print("=" * 80)
print("SBML STOCHASTIC SOURCE TEST")
print("=" * 80)

# Load SBML model
model_path = 'workspace/projects/SBML/models/BIOMD0000000001.shy'
print(f"\n1. Loading SBML model: {model_path}")

try:
    with open(model_path, 'r') as f:
        data = json.load(f)
    
    document = DocumentModel.from_dict(data)
    print(f"   ✓ Model loaded: {len(document.places)} places, {len(document.transitions)} transitions")
except Exception as e:
    print(f"   ❌ Failed to load model: {e}")
    sys.exit(1)

# Add a stochastic source transition
print(f"\n2. Adding stochastic source transition")
source_t = document.create_transition(x=500, y=300, label="TestSource")
source_t.transition_type = 'stochastic'
source_t.rate = 2.0  # Fire every ~0.5 seconds on average
source_t.is_source = True  # CRITICAL: Mark as source
print(f"   ✓ Created transition: {source_t.name}")
print(f"     - Type: {source_t.transition_type}")
print(f"     - Rate: {source_t.rate}")
print(f"     - is_source: {source_t.is_source}")

# Connect to first place as output
if document.places:
    target_place = document.places[0]
    arc = document.create_arc(source_t, target_place)
    arc.weight = 1
    print(f"   ✓ Connected: {source_t.name} → {target_place.name}")
    print(f"     - Target initial tokens: {target_place.tokens}")
else:
    print("   ❌ No places found in model!")
    sys.exit(1)

# Create canvas manager
print(f"\n3. Creating canvas manager")
manager = ModelCanvasManager()
manager.load_objects(
    places=document.places,
    transitions=document.transitions,
    arcs=document.arcs
)
print(f"   ✓ Manager created: {len(manager.places)} places, {len(manager.transitions)} transitions")

# Create simulation controller
print(f"\n4. Creating simulation controller")
controller = SimulationController(manager)
print(f"   ✓ Controller created")
print(f"     - Time: {controller.time}")

# Update enablement (this should schedule the source transition)
print(f"\n5. Updating transition enablement")
controller._update_enablement_states()

# Check the cached behavior in controller
cached_behavior = controller._get_behavior(source_t)
print(f"   ✓ Source behavior (from cache): {type(cached_behavior).__name__}")
print(f"     - Rate: {cached_behavior.rate}")
print(f"     - Scheduled fire time: {cached_behavior._scheduled_fire_time}")
print(f"     - Sampled burst: {cached_behavior._sampled_burst}")

# Check can_fire
can_fire, reason = cached_behavior.can_fire()
print(f"\n6. Checking can_fire()")
print(f"   - Result: {can_fire}")
print(f"   - Reason: {reason}")

# Run simulation
print(f"\n7. Running simulation (50 steps, 0.1s each)")
initial_tokens = target_place.tokens
print(f"   Initial tokens in {target_place.name}: {initial_tokens}")

steps_executed = 0
tokens_generated = 0

for i in range(50):
    # Step with 0.1 second increments
    result = controller.step(time_step=0.1)
    steps_executed += 1
    
    # Check token change
    current_tokens = target_place.tokens
    if current_tokens > initial_tokens:
        tokens_generated += (current_tokens - initial_tokens)
        print(f"   Step {i+1} (t={controller.time:.2f}s): Fired! Tokens: {initial_tokens} → {current_tokens} (+{current_tokens - initial_tokens})")
        initial_tokens = current_tokens
        # Continue to see if it fires multiple times
    
    # Stop after 10 steps if we got tokens
    if tokens_generated > 0 and i >= 10:
        break

print(f"\n" + "=" * 80)
print(f"TEST RESULTS")
print(f"=" * 80)
print(f"Steps executed: {steps_executed}")
print(f"Final tokens in {target_place.name}: {target_place.tokens}")
print(f"Tokens generated: {tokens_generated}")
print(f"Final time: {controller.time:.3f}")

if tokens_generated > 0:
    print(f"\n✅ SUCCESS! Stochastic source fired and generated {tokens_generated} tokens")
    print(f"   The behavior cache invalidation fix is working!")
    sys.exit(0)
else:
    # Get final cached behavior state
    final_behavior = controller._get_behavior(source_t)
    
    print(f"\n❌ FAILURE! Source did not generate any tokens")
    print(f"   Debugging info:")
    print(f"   - Source transition is_source: {source_t.is_source}")
    print(f"   - Source behavior scheduled: {final_behavior._scheduled_fire_time}")
    can_fire_final, reason_final = final_behavior.can_fire()
    print(f"   - Can fire: {can_fire_final}, reason: {reason_final}")
    sys.exit(1)
