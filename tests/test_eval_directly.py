#!/usr/bin/env python3
"""Direct test of rate function evaluation"""
import sys
import json
sys.path.insert(0, 'src')

from shypn.netobjs.transition import Transition
from shypn.netobjs.place import Place
from shypn.netobjs.arc import Arc
from shypn.data.canvas.petrinet import PetriNet
from shypn.engine.stochastic_behavior import StochasticBehavior
from shypn.engine.adaptive_hybrid_behavior import AdaptiveHybridBehavior

# Load model JSON  
model_path = "workspace/projects/My_Project/drug_discovery/models/manuscript/macrocycle_transport_normal_nme_0_enhanced.shy"
with open(model_path, 'r') as f:
    data = json.load(f)

# Create a petrinet
petrinet = PetriNet()

# Load places
places_dict = {}
for p_data in data['places']:
    place = Place.from_dict(p_data)
    places_dict[place.id] = place
    petrinet.add_place(place)

print(f"Loaded {len(places_dict)} places")

# Load transitions (focus on T10)
t10_data = None
for t_data in data['transitions']:
    if t_data['id'] == 'T10':
        t10_data = t_data
        break

t10 = Transition.from_dict(t10_data)
print(f"\nTransition T10 loaded:")
print(f"  Name: {t10.name}")
print(f"  Type: {t10.transition_type}")
print(f"  Properties: {t10.properties}")
print(f"  rate_function: {t10.rate_function}")

# Create a simple model adapter for behavior initialization
class SimpleModelAdapter:
    def __init__(self, places_dict):
        self.places_dict = places_dict
        self.places = places_dict  # Also as attribute
        
    def get_place_by_name(self, name):
        for p in self.places_dict.values():
            if p.name == name:
                return p
        return None

model = SimpleModelAdapter(places_dict)

# Create behavior
print(f"\nCreating AdaptiveHybridBehavior...")
try:
    behavior = AdaptiveHybridBehavior(t10, model)
    print(f"✅ Behavior created successfully")
    print(f"  has stochastic_behavior: {hasattr(behavior, 'stochastic_behavior')}")
    
    # Try to evaluate rate
    print(f"\nEvaluating rate at time 0.0...")
    rate = behavior._evaluate_rate_at_enablement(0.0)
    print(f"✅ Rate evaluated: {rate}")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
