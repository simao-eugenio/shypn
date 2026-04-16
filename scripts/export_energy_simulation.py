#!/usr/bin/env python3
"""
Export ATP, ADP, GTP, GDP simulation data to CSV
"""

import sys
import os
import csv

# Add shypn to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', 'src'))

from shypn.data.canvas.document_model import DocumentModel
from shypn.engine.simulation.controller import SimulationController

def export_energy_simulation():
    """Run Bacillus simulation and export energy data to CSV"""
    
    # Load model
    model_path = os.path.join(os.path.dirname(__file__), 'bacillus_sporulation_normal.shy')
    print(f"Loading model: {model_path}")
    
    doc_model = DocumentModel.load_from_file(model_path)
    
    # Restore tokens from JSON
    import json
    with open(model_path, 'r') as f:
        model_data = json.load(f)
    
    for place_data in model_data.get('places', []):
        place_id = place_data['id']
        for place in doc_model.places:
            if place.id == place_id:
                place.marking = place_data.get('marking', 0)
                break
    
    # Initialize simulation controller
    controller = SimulationController(doc_model)
    
    # Get energy places
    energy_places = {
        'ATP_pool': None,
        'ADP_pool': None,
        'GTP_pool': None,
        'GDP_pool': None
    }
    
    for place in doc_model.places:
        if place.id in energy_places:
            energy_places[place.id] = place
    
    print(f"\nInitial conditions:")
    for place_id, place in energy_places.items():
        if place:
            print(f"  {place_id}: {place.marking:.2f} mM")
    
    # Simulation parameters
    duration = 100.0  # seconds
    time_step = 0.1   # sample every 0.1 seconds
    
    # Data collection
    data_points = []
    sample_times = []
    
    print(f"\nRunning simulation for {duration} seconds...")
    
    # Initial data point
    data_points.append({
        'Time': 0.0,
        'ATP_pool': energy_places['ATP_pool'].marking if energy_places['ATP_pool'] else 0,
        'ADP_pool': energy_places['ADP_pool'].marking if energy_places['ADP_pool'] else 0,
        'GTP_pool': energy_places['GTP_pool'].marking if energy_places['GTP_pool'] else 0,
        'GDP_pool': energy_places['GDP_pool'].marking if energy_places['GDP_pool'] else 0
    })
    
    # Run simulation
    current_time = 0.0
    while current_time < duration:
        controller.step()
        current_time = controller.time
        
        # Sample at intervals
        if len(data_points) == 0 or current_time - data_points[-1]['Time'] >= time_step - 0.001:
            data_points.append({
                'Time': current_time,
                'ATP_pool': energy_places['ATP_pool'].marking if energy_places['ATP_pool'] else 0,
                'ADP_pool': energy_places['ADP_pool'].marking if energy_places['ADP_pool'] else 0,
                'GTP_pool': energy_places['GTP_pool'].marking if energy_places['GTP_pool'] else 0,
                'GDP_pool': energy_places['GDP_pool'].marking if energy_places['GDP_pool'] else 0
            })
    
    # Write to CSV
    csv_path = os.path.join(os.path.dirname(__file__), 'simulation_energy.csv')
    print(f"\nWriting data to: {csv_path}")
    
    with open(csv_path, 'w', newline='') as csvfile:
        fieldnames = ['Time', 'ATP_pool', 'ADP_pool', 'GTP_pool', 'GDP_pool']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for row in data_points:
            writer.writerow(row)
    
    print(f"✓ Exported {len(data_points)} data points")
    
    # Final conditions
    print(f"\nFinal conditions (t={current_time:.2f}s):")
    for place_id, place in energy_places.items():
        if place:
            print(f"  {place_id}: {place.marking:.2f} mM")
    
    # T20 firing rate
    for transition in doc_model.transitions:
        if transition.label == 'T20':
            firing_rate = transition.firing_count / current_time
            print(f"\nT20 (ATP regeneration):")
            print(f"  Total firings: {transition.firing_count:.2f}")
            print(f"  Firing rate: {firing_rate:.3f} firings/s")
            
            # Expected rate calculation
            nutrients = None
            for place in doc_model.places:
                if place.label == 'Nutrients':
                    nutrients = place.marking
                    break
            if nutrients is not None:
                expected_rate = 2.5 * nutrients / (10 + nutrients)
                print(f"  Expected rate: {expected_rate:.3f} firings/s")
                print(f"  Ratio: {firing_rate/expected_rate:.1%}")
    
    print(f"\n✓ Data saved to simulation_energy.csv")

if __name__ == '__main__':
    export_energy_simulation()
