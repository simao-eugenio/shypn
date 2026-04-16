#!/usr/bin/env python3
"""
Test BatchProcessor

Validates batch processing with error isolation and result export.
"""
import sys
from pathlib import Path
import json
import csv
import tempfile

# Add src to path
sys.path.insert(0, str(Path(__file__).parents[3] / 'src'))

from shypn.data.batch import BatchProcessor


def test_batch_processor():
    """Test BatchProcessor functionality."""
    print("="*60)
    print("Testing BatchProcessor")
    print("="*60)
    
    # Create temporary test files
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Test 1: Create batch CSV
        print("\n1. Testing load_from_csv()...")
        batch_csv = tmpdir / 'batch.csv'
        with open(batch_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['model_id', 'model_path'])
            writer.writerow(['model_1', str(tmpdir / 'model1.txt')])
            writer.writerow(['model_2', str(tmpdir / 'model2.txt')])
            writer.writerow(['model_3', str(tmpdir / 'model3.txt')])
            writer.writerow(['model_4', str(tmpdir / 'model4.txt')])
            writer.writerow(['model_5', str(tmpdir / 'model5.txt')])
        
        # Create dummy model files
        for i in range(1, 6):
            model_file = tmpdir / f'model{i}.txt'
            model_file.write_text(f'Model {i} data\n')
        
        processor = BatchProcessor(verbose=True)
        models = processor.load_from_csv(batch_csv)
        
        assert len(models) == 5, f"Expected 5 models, got {len(models)}"
        assert models[0][0] == 'model_1'
        assert models[0][1].name == 'model1.txt'
        print(f"  ✓ Loaded {len(models)} models from CSV")
        
        # Test 2: Process batch (sequential)
        print("\n2. Testing process_batch() - sequential...")
        
        def mock_processor(model_id, model_path):
            """Mock processor that succeeds for even IDs, fails for odd."""
            # Read model file
            content = model_path.read_text()
            
            # Extract model number from ID
            num = int(model_id.split('_')[1])
            
            if num == 3:
                # Simulate failure for model 3
                raise ValueError(f"Simulated error for {model_id}")
            
            # Return some result
            return {
                'model_id': model_id,
                'model_file': model_path.name,
                'content_length': len(content),
                'processed': True
            }
        
        results = processor.process_batch(models, mock_processor, parallel=False)
        
        assert results['n_total'] == 5
        assert results['n_successful'] == 4, f"Expected 4 successful, got {results['n_successful']}"
        assert results['n_failed'] == 1, f"Expected 1 failed, got {results['n_failed']}"
        assert 'model_3' in results['failed']
        assert 'Simulated error' in results['failed']['model_3']
        print(f"  ✓ Sequential processing: {results['n_successful']}/{results['n_total']} successful")
        
        # Test 3: Export results
        print("\n3. Testing export_results()...")
        output_dir = tmpdir / 'results'
        processor.export_results(results, output_dir, include_details=True)
        
        # Verify files created
        assert (output_dir / 'batch_summary.json').exists()
        assert (output_dir / 'successful_models.csv').exists()
        assert (output_dir / 'failed_models.csv').exists()
        print("  ✓ Results exported")
        
        # Verify JSON content
        with open(output_dir / 'batch_summary.json', 'r') as f:
            summary = json.load(f)
            assert summary['n_total'] == 5
            assert summary['n_successful'] == 4
            assert summary['n_failed'] == 1
            assert summary['success_rate'] == 0.8
            assert 'results' in summary
            assert 'errors' in summary
            print(f"  ✓ Summary: {summary['n_successful']}/{summary['n_total']} "
                  f"({100*summary['success_rate']:.0f}% success rate)")
        
        # Verify successful CSV
        with open(output_dir / 'successful_models.csv', 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) == 5  # 1 header + 4 data rows
            assert rows[0] == ['model_id']
            print(f"  ✓ Successful models CSV: {len(rows)-1} models")
        
        # Verify failed CSV
        with open(output_dir / 'failed_models.csv', 'r') as f:
            reader = csv.reader(f)
            rows = list(reader)
            assert len(rows) == 2  # 1 header + 1 data row
            assert rows[0] == ['model_id', 'error']
            assert rows[1][0] == 'model_3'
            assert 'Simulated error' in rows[1][1]
            print(f"  ✓ Failed models CSV: {len(rows)-1} models")
        
        # Test 4: Error handling - missing CSV
        print("\n4. Testing error handling...")
        try:
            processor.load_from_csv('nonexistent.csv')
            assert False, "Should have raised FileNotFoundError"
        except FileNotFoundError:
            print("  ✓ FileNotFoundError raised for missing CSV")
        
        # Test 5: Error handling - invalid CSV format
        invalid_csv = tmpdir / 'invalid.csv'
        with open(invalid_csv, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['wrong_header', 'another_wrong'])
            writer.writerow(['data1', 'data2'])
        
        try:
            processor.load_from_csv(invalid_csv)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert 'model_id' in str(e)
            print("  ✓ ValueError raised for invalid CSV format")
        
        # Test 6: Process empty batch
        print("\n5. Testing empty batch...")
        empty_results = processor.process_batch([], mock_processor)
        assert empty_results['n_total'] == 0
        assert empty_results['n_successful'] == 0
        assert empty_results['n_failed'] == 0
        print("  ✓ Empty batch handled correctly")
        
        # Test 7: All models succeed
        print("\n6. Testing all-success batch...")
        def success_processor(model_id, model_path):
            return {'model_id': model_id, 'status': 'success'}
        
        success_results = processor.process_batch(
            [('m1', tmpdir / 'model1.txt'), ('m2', tmpdir / 'model2.txt')],
            success_processor
        )
        assert success_results['n_successful'] == 2
        assert success_results['n_failed'] == 0
        print("  ✓ All-success batch processed")
        
        # Test 8: All models fail
        print("\n7. Testing all-failure batch...")
        def fail_processor(model_id, model_path):
            raise RuntimeError("Always fails")
        
        fail_results = processor.process_batch(
            [('m1', tmpdir / 'model1.txt'), ('m2', tmpdir / 'model2.txt')],
            fail_processor
        )
        assert fail_results['n_successful'] == 0
        assert fail_results['n_failed'] == 2
        print("  ✓ All-failure batch handled")
        
        # Test 9: Export without details
        print("\n8. Testing export without details...")
        minimal_dir = tmpdir / 'minimal_results'
        processor.export_results(results, minimal_dir, include_details=False)
        
        with open(minimal_dir / 'batch_summary.json', 'r') as f:
            minimal_summary = json.load(f)
            assert 'n_total' in minimal_summary
            assert 'success_rate' in minimal_summary
            assert 'results' not in minimal_summary  # Details excluded
            assert 'errors' not in minimal_summary
            print("  ✓ Minimal export (without details)")
    
    print("\n" + "="*60)
    print("✅ ALL BATCHPROCESSOR TESTS PASSED!")
    print("="*60)
    print("\nBatchProcessor features validated:")
    print("  ✓ Load batch specification from CSV")
    print("  ✓ Process batch with error isolation")
    print("  ✓ Export results (JSON + CSV)")
    print("  ✓ Error handling (missing/invalid files)")
    print("  ✓ Edge cases (empty batch, all success, all failure)")


if __name__ == '__main__':
    test_batch_processor()
