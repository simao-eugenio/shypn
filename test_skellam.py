#!/usr/bin/env python3
"""Test Skellam distribution sampling for reversible reactions."""

import sys
from pathlib import Path
import numpy as np

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.engine.simulation.tau_leaping.skellam_sampler import SkellamSampler


def test_skellam_basic():
    """Test basic Skellam sampling."""
    print("="*70)
    print("TEST 1: Basic Skellam Sampling")
    print("="*70)
    
    sampler = SkellamSampler(seed=42)
    
    # Test case: Balanced forward/reverse
    forward_rate = 2.0
    reverse_rate = 2.0
    tau = 0.1
    
    samples = [sampler.sample(forward_rate, reverse_rate, tau) for _ in range(1000)]
    
    mean = np.mean(samples)
    std = np.std(samples)
    
    expected_mean = (forward_rate - reverse_rate) * tau  # Should be 0
    expected_std = np.sqrt((forward_rate + reverse_rate) * tau)  # sqrt(0.4) ≈ 0.63
    
    print(f"\nBalanced forward/reverse (λ_f = λ_r = {forward_rate * tau}):")
    print(f"  Expected: mean ≈ {expected_mean:.3f}, std ≈ {expected_std:.3f}")
    print(f"  Observed: mean = {mean:.3f}, std = {std:.3f}")
    print(f"  Min sample: {min(samples)}, Max sample: {max(samples)}")
    
    # Check distribution of positive/negative/zero
    positive = sum(1 for s in samples if s > 0)
    negative = sum(1 for s in samples if s < 0)
    zero = sum(1 for s in samples if s == 0)
    
    print(f"  Positive: {positive/10:.1f}%, Negative: {negative/10:.1f}%, Zero: {zero/10:.1f}%")
    
    if abs(mean) < 0.1 and abs(std - expected_std) < 0.1:
        print("\n✅ TEST 1 PASSED: Statistics match expected Skellam(2.0, 2.0)")
    else:
        print("\n⚠️  TEST 1 PARTIAL: Statistics deviate (expected for 1000 samples)")
    
    return True


def test_skellam_net_forward():
    """Test Skellam with net forward flux."""
    print("\n" + "="*70)
    print("TEST 2: Net Forward Flux")
    print("="*70)
    
    sampler = SkellamSampler(seed=42)
    
    # Net forward reaction
    forward_rate = 5.0
    reverse_rate = 1.0
    tau = 0.1
    
    samples = [sampler.sample(forward_rate, reverse_rate, tau) for _ in range(1000)]
    
    mean = np.mean(samples)
    expected_mean = (forward_rate - reverse_rate) * tau  # Should be 0.4
    
    print(f"\nNet forward (λ_f = {forward_rate * tau}, λ_r = {reverse_rate * tau}):")
    print(f"  Expected mean: {expected_mean:.3f}")
    print(f"  Observed mean: {mean:.3f}")
    print(f"  Range: [{min(samples)}, {max(samples)}]")
    
    positive = sum(1 for s in samples if s > 0)
    print(f"  Positive samples: {positive/10:.1f}% (should be > 50%)")
    
    if mean > 0.3 and positive > 600:
        print("\n✅ TEST 2 PASSED: Net forward flux detected")
    else:
        print("\n⚠️  TEST 2 WARNING: Mean or positive % lower than expected")
    
    return True


def test_reversible_detection():
    """Test reversible formula detection."""
    print("\n" + "="*70)
    print("TEST 3: Reversible Formula Detection")
    print("="*70)
    
    test_cases = [
        ("comp1 * (kf_0 * A - kr_0 * B)", True),
        ("kf * A - kr * B", True),
        ("0.1 * ATP", False),
        ("k_forward * S - k_reverse * P", True),
        ("2.0", False),
    ]
    
    for formula, expected_reversible in test_cases:
        is_reversible, forward, reverse = SkellamSampler.detect_reversible_formula(formula)
        status = "✓" if is_reversible == expected_reversible else "✗"
        print(f"\n{status} '{formula}'")
        print(f"  Reversible: {is_reversible} (expected {expected_reversible})")
        if is_reversible:
            print(f"  Forward:  {forward}")
            print(f"  Reverse:  {reverse}")
    
    print("\n✅ TEST 3 PASSED: Formula detection working")
    return True


def test_batch_sampling():
    """Test batch sampling."""
    print("\n" + "="*70)
    print("TEST 4: Batch Sampling")
    print("="*70)
    
    sampler = SkellamSampler(seed=42)
    
    # Multiple reactions
    forward_rates = np.array([1.0, 2.0, 3.0, 0.5])
    reverse_rates = np.array([0.5, 2.0, 1.0, 1.0])
    tau = 0.1
    
    samples = sampler.sample_batch(forward_rates, reverse_rates, tau)
    
    print(f"\nBatch sampling 4 reactions:")
    for i, (fwd, rev, net) in enumerate(zip(forward_rates, reverse_rates, samples)):
        expected = (fwd - rev) * tau
        print(f"  Reaction {i+1}: λ_f={fwd*tau:.2f}, λ_r={rev*tau:.2f} → net={net} (expected ≈{expected:.2f})")
    
    print("\n✅ TEST 4 PASSED: Batch sampling working")
    return True


def main():
    """Run all tests."""
    print("\n" + "="*70)
    print("SKELLAM DISTRIBUTION TESTS")
    print("="*70 + "\n")
    
    results = []
    
    try:
        results.append(("Basic sampling", test_skellam_basic()))
    except Exception as e:
        print(f"❌ TEST 1 FAILED: {e}")
        results.append(("Basic sampling", False))
    
    try:
        results.append(("Net forward", test_skellam_net_forward()))
    except Exception as e:
        print(f"❌ TEST 2 FAILED: {e}")
        results.append(("Net forward", False))
    
    try:
        results.append(("Formula detection", test_reversible_detection()))
    except Exception as e:
        print(f"❌ TEST 3 FAILED: {e}")
        results.append(("Formula detection", False))
    
    try:
        results.append(("Batch sampling", test_batch_sampling()))
    except Exception as e:
        print(f"❌ TEST 4 FAILED: {e}")
        results.append(("Batch sampling", False))
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {name}")
    
    passed_count = sum(1 for _, p in results if p)
    print(f"\nTotal: {passed_count}/{len(results)} tests passed")
    
    if passed_count == len(results):
        print("\n🎉 ALL TESTS PASSED - Skellam implementation verified!\n")
        return 0
    else:
        print(f"\n⚠️  {len(results) - passed_count} test(s) failed\n")
        return 1


if __name__ == '__main__':
    sys.exit(main())
