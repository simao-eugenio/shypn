#!/usr/bin/env python3
"""Verify that new analyzers are properly integrated in UI categories."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

def verify_graph_network_category():
    """Verify GraphNetworkCategory has all analyzers."""
    from shypn.ui.panels.topology.graph_network_category import GraphNetworkCategory
    
    # Create instance
    category = GraphNetworkCategory()
    
    # Get analyzers
    analyzers = category._get_analyzers()
    
    print("📊 Graph & Network Category Analyzers:")
    expected = ['cycles', 'paths', 'hubs', 'centrality', 'communities', 'clustering']
    for name in expected:
        status = "✅" if name in analyzers else "❌"
        print(f"  {status} {name}: {analyzers.get(name, 'MISSING')}")
    
    print(f"\n  Total: {len(analyzers)}/6 analyzers registered\n")
    return len(analyzers) == 6

def verify_behavioral_category():
    """Verify BehavioralCategory has all analyzers."""
    from shypn.ui.panels.topology.behavioral_category import BehavioralCategory
    
    # Create instance
    category = BehavioralCategory()
    
    # Get analyzers
    analyzers = category._get_analyzers()
    
    print("🎯 Behavioral Category Analyzers:")
    expected = [
        'boundedness', 'fairness', 'throughput', 'response_time',
        'coverability', 'deadlocks', 'liveness', 'reachability'
    ]
    for name in expected:
        status = "✅" if name in analyzers else "❌"
        print(f"  {status} {name}: {analyzers.get(name, 'MISSING')}")
    
    print(f"\n  Total: {len(analyzers)}/8 analyzers registered\n")
    return len(analyzers) == 8

def verify_metadata():
    """Verify ANALYZER_METADATA has entries for new analyzers."""
    from shypn.ui.panels.topology.base_topology_category import ANALYZER_METADATA
    
    print("⚙️  Analyzer Metadata:")
    new_analyzers = ['centrality', 'communities', 'clustering', 
                     'throughput', 'response_time', 'coverability']
    
    all_present = True
    for name in new_analyzers:
        if name in ANALYZER_METADATA:
            meta = ANALYZER_METADATA[name]
            priority = meta.get('priority', '?')
            complexity = meta.get('complexity', '?')
            timeout = meta.get('timeout_seconds', '?')
            print(f"  ✅ {name}: Priority {priority}, {complexity}, {timeout}s timeout")
        else:
            print(f"  ❌ {name}: MISSING")
            all_present = False
    
    print(f"\n  Total: {sum(1 for n in new_analyzers if n in ANALYZER_METADATA)}/6 metadata entries\n")
    return all_present

def main():
    """Run all verifications."""
    print("=" * 70)
    print("🔍 VERIFYING UI INTEGRATION FOR NEW ANALYZERS")
    print("=" * 70 + "\n")
    
    results = []
    
    try:
        results.append(("Graph & Network Category", verify_graph_network_category()))
    except Exception as e:
        print(f"❌ Graph & Network Category: ERROR - {e}\n")
        results.append(("Graph & Network Category", False))
    
    try:
        results.append(("Behavioral Category", verify_behavioral_category()))
    except Exception as e:
        print(f"❌ Behavioral Category: ERROR - {e}\n")
        results.append(("Behavioral Category", False))
    
    try:
        results.append(("Analyzer Metadata", verify_metadata()))
    except Exception as e:
        print(f"❌ Analyzer Metadata: ERROR - {e}\n")
        results.append(("Analyzer Metadata", False))
    
    # Summary
    print("=" * 70)
    print("📋 SUMMARY")
    print("=" * 70)
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for name, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {name}")
    
    print(f"\n🎯 Result: {passed}/{total} checks passed")
    
    if passed == total:
        print("\n🎉 SUCCESS! All new analyzers are properly integrated in the UI!")
        return 0
    else:
        print("\n⚠️  WARNING: Some integrations are incomplete.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
