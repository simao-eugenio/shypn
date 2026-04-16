#!/usr/bin/env python3
"""Test event-driven cache invalidation in ModelRepository."""

import sys
from pathlib import Path
import json
import time

# Add shypn to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.repositories.model_repository import ModelRepository
from shypn.data.canvas.document_model import DocumentModel


def test_cache_invalidation():
    """Test that cache is invalidated when model file is saved."""
    
    workspace = Path("workspace/projects/gata/models")
    model_id = "phase3a_spatial_clean"
    model_path = workspace / f"{model_id}.shy"
    
    print("=" * 70)
    print("Testing Event-Driven Cache Invalidation")
    print("=" * 70)
    
    # Step 1: Create repository (this subscribes to 'file.saved' event)
    print("\n1️⃣  Creating ModelRepository...")
    repo = ModelRepository(str(workspace))
    print(f"   ✅ Repository created for workspace: {workspace}")
    
    # Step 2: Load model (this caches it)
    print(f"\n2️⃣  Loading model '{model_id}' (first time - should cache)...")
    model1 = repo.get_by_id(model_id)
    if model1:
        print(f"   ✅ Model loaded: {len(model1.places)} places, {len(model1.transitions)} transitions")
        print(f"   📊 Cache stats: {repo._cache_hits} hits, {repo._cache_misses} misses")
    else:
        print(f"   ❌ Model not found!")
        return False
    
    # Step 3: Load again (should hit cache)
    print(f"\n3️⃣  Loading model again (should hit cache)...")
    model2 = repo.get_by_id(model_id)
    print(f"   📊 Cache stats: {repo._cache_hits} hits, {repo._cache_misses} misses")
    print(f"   ✅ Same object in memory: {model1 is model2}")
    
    # Step 4: Modify and save via DocumentModel (emits event)
    print(f"\n4️⃣  Modifying and saving model (via DocumentModel.save_to_file)...")
    model1.metadata['test_timestamp'] = time.time()
    model1.save_to_file(str(model_path))
    print(f"   ✅ Model saved - 'file.saved' event emitted")
    
    # Step 5: Load again (cache should be invalidated)
    print(f"\n5️⃣  Loading model again (cache should be invalidated)...")
    model3 = repo.get_by_id(model_id)
    print(f"   📊 Cache stats: {repo._cache_hits} hits, {repo._cache_misses} misses")
    print(f"   ✅ Different object in memory (cache was invalidated): {model1 is not model3}")
    print(f"   ✅ Timestamp in new model: {model3.metadata.get('test_timestamp')}")
    
    # Step 6: Verify event-driven invalidation worked
    if model1 is not model3:
        print("\n" + "=" * 70)
        print("✅ SUCCESS: Event-driven cache invalidation works!")
        print("=" * 70)
        print("\nHow it works:")
        print("  1. ModelRepository.__init__() subscribes to 'file.saved' event")
        print("  2. DocumentModel.save_to_file() emits 'file.saved' event")
        print("  3. ModelRepository._on_file_saved() handles event and invalidates cache")
        print("  4. Next get_by_id() reloads from disk")
        return True
    else:
        print("\n" + "=" * 70)
        print("❌ FAILED: Cache was NOT invalidated (event not received?)")
        print("=" * 70)
        return False


if __name__ == '__main__':
    success = test_cache_invalidation()
    sys.exit(0 if success else 1)
