#!/usr/bin/env python3
"""
Test DataCollector Export API

Validates new export methods: get_data(), export_csv(), export_json()
"""
import sys
from pathlib import Path
import json
import csv

# Add src to path
sys.path.insert(0, str(Path(__file__).parents[3] / 'src'))

from shypn.engine.simulation.data_collector import DataCollector


class MockPlace:
    """Mock place for testing."""
    def __init__(self, id, tokens=0):
        self.id = id
        self.name = id
        self.tokens = tokens
        self.initial_tokens = tokens
        

class MockTransition:
    """Mock transition for testing."""
    def __init__(self, id):
        self.id = id
        self.name = id
        self.firing_count = 0


class MockModel:
    """Mock model for testing."""
    def __init__(self):
        self.places = [
            MockPlace('S1', tokens=100),
            MockPlace('S2', tokens=50),
            MockPlace('S3', tokens=25)
        ]
        self.transitions = [
            MockTransition('T1'),
            MockTransition('T2')
        ]


def test_export_api():
    """Test DataCollector export methods."""
    print("Creating mock model and data collector...")
    model = MockModel()
    collector = DataCollector(model)
    
    # Simulate some data collection
    print("\nSimulating data collection...")
    collector.start_collection()
    
    # Record 5 time points with changing values
    for i in range(5):
        time = i * 0.5
        collector.record_state(time)
        
        # Modify tokens for next time point
        model.places[0].tokens -= 5  # S1 decreases
        model.places[1].tokens += 3  # S2 increases
        model.places[2].tokens += 2  # S3 increases
        model.transitions[0].firing_count += 2
        model.transitions[1].firing_count += 1
    
    collector.stop_collection()
    
    print(f"  ✓ Collected {len(collector.time_points)} time points")
    print(f"  ✓ Tracked {len(collector.place_data)} places")
    print(f"  ✓ Tracked {len(collector.transition_data)} transitions")
    
    # Test get_data()
    print("\nTesting get_data()...")
    data = collector.get_data()
    
    assert 'time_points' in data
    assert 'place_data' in data
    assert 'transition_data' in data
    assert 'model' in data
    assert len(data['time_points']) == 5
    assert len(data['place_data']) == 3
    assert len(data['transition_data']) == 2
    print("  ✓ get_data() returns correct structure")
    
    # Test export_csv() - wide format
    print("\nTesting export_csv(format='wide')...")
    output_dir = Path('/tmp/shypn_export_test')
    output_dir.mkdir(exist_ok=True)
    
    csv_wide = output_dir / 'test_wide.csv'
    success = collector.export_csv(str(csv_wide), format='wide')
    assert success, "CSV wide export failed"
    assert csv_wide.exists(), "CSV file not created"
    
    # Verify CSV content
    with open(csv_wide, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
        assert len(rows) == 6, f"Expected 6 rows (1 header + 5 data), got {len(rows)}"
        header = rows[0]
        assert 'Time (s)' in header[0], f"Missing time column in header: {header}"
        print(f"  ✓ Wide CSV created: {csv_wide}")
        print(f"    Header: {header[:4]}...")
        print(f"    Rows: {len(rows) - 1} data rows")
    
    # Test export_csv() - long format
    print("\nTesting export_csv(format='long')...")
    csv_long = output_dir / 'test_long.csv'
    success = collector.export_csv(str(csv_long), format='long')
    assert success, "CSV long export failed"
    assert csv_long.exists(), "CSV file not created"
    
    # Verify CSV content
    with open(csv_long, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
        # 5 time points × (3 places + 2 transitions) = 25 rows + 1 header
        assert len(rows) == 26, f"Expected 26 rows, got {len(rows)}"
        header = rows[0]
        assert header == ['Time', 'Entity', 'Type', 'Value', 'Unit']
        print(f"  ✓ Long CSV created: {csv_long}")
        print(f"    Header: {header}")
        print(f"    Rows: {len(rows) - 1} data rows")
    
    # Test export_json()
    print("\nTesting export_json()...")
    json_file = output_dir / 'test_data.json'
    success = collector.export_json(str(json_file))
    assert success, "JSON export failed"
    assert json_file.exists(), "JSON file not created"
    
    # Verify JSON content
    with open(json_file, 'r') as f:
        data = json.load(f)
        assert 'metadata' in data
        assert 'time_points' in data
        assert 'places' in data
        assert 'transitions' in data
        assert 'statistics' in data
        assert len(data['time_points']) == 5
        print(f"  ✓ JSON created: {json_file}")
        print(f"    Time points: {len(data['time_points'])}")
        print(f"    Places: {len(data['places'])}")
        print(f"    Transitions: {len(data['transitions'])}")
    
    # Test export_json() with custom options
    print("\nTesting export_json() with custom options...")
    json_minimal = output_dir / 'test_minimal.json'
    success = collector.export_json(
        str(json_minimal),
        include_metadata=False,
        include_statistics=False
    )
    assert success, "JSON minimal export failed"
    
    with open(json_minimal, 'r') as f:
        data = json.load(f)
        assert 'metadata' not in data
        assert 'statistics' not in data
        assert 'time_points' in data
        print(f"  ✓ Minimal JSON created: {json_minimal}")
    
    # Test invalid format error
    print("\nTesting error handling...")
    try:
        collector.export_csv('test.csv', format='invalid')
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert 'Invalid format' in str(e)
        print("  ✓ ValueError raised for invalid format")
    
    print("\n" + "="*60)
    print("✅ ALL EXPORT API TESTS PASSED!")
    print("="*60)
    print(f"\nTest files created in: {output_dir}")
    print(f"  - {csv_wide.name} (wide format)")
    print(f"  - {csv_long.name} (long format)")
    print(f"  - {json_file.name} (full data)")
    print(f"  - {json_minimal.name} (minimal)")


if __name__ == '__main__':
    test_export_api()
