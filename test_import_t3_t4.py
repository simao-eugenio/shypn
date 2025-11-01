#!/usr/bin/env python3
"""Test T3 and T4 import and initial state."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.data.canvas.document_model import DocumentModel

# Load model
model_path = 'workspace/projects/Interactive/models/hsa00010.shy'
print("=" * 80)
print(f"LOADING MODEL: {model_path}")
print("=" * 80)

doc = DocumentModel.load_from_file(model_path)

print(f"\nLoaded: {len(doc.places)} places, {len(doc.transitions)} transitions, {len(doc.arcs)} arcs")

# Find T3 and T4
t3 = next((t for t in doc.transitions if t.id == 'T3'), None)
t4 = next((t for t in doc.transitions if t.id == 'T4'), None)

if not t3:
    print("\n❌ T3 not found in model!")
    sys.exit(1)
if not t4:
    print("\n❌ T4 not found in model!")
    sys.exit(1)

print("\n" + "=" * 80)
print("T3 IMPORTED STATE")
print("=" * 80)
print(f"ID: {t3.id}")
print(f"Name: {t3.name}")
print(f"Type: {t3.transition_type}")
print(f"Rate: {t3.rate}")
print(f"Guard: {t3.guard}")
print(f"Enabled: {t3.enabled}")
print(f"Is source: {t3.is_source}")
print(f"Priority: {t3.priority}")

print("\n" + "=" * 80)
print("T4 IMPORTED STATE")
print("=" * 80)
print(f"ID: {t4.id}")
print(f"Name: {t4.name}")
print(f"Type: {t4.transition_type}")
print(f"Rate: {t4.rate}")
print(f"Guard: {t4.guard}")
print(f"Enabled: {t4.enabled}")
print(f"Is source: {t4.is_source}")
print(f"Priority: {t4.priority}")

# Check input arcs
print("\n" + "=" * 80)
print("T3 INPUT ARCS")
print("=" * 80)

t3_inputs = [arc for arc in doc.arcs if arc.target == t3]
print(f"Found {len(t3_inputs)} input arcs:")

for arc in t3_inputs:
    source = arc.source
    print(f"\nArc {arc.id}:")
    print(f"  From: {source.id} ({source.label})")
    print(f"  Type: {arc.__class__.__name__}")
    print(f"  Weight: {arc.weight}")
    print(f"  Source tokens: {source.tokens}")
    print(f"  Source initial_marking: {source.initial_marking}")
    
    if hasattr(arc, 'consumes_tokens'):
        print(f"  Consumes tokens: {arc.consumes_tokens()}")

print("\n" + "=" * 80)
print("T4 INPUT ARCS")
print("=" * 80)

t4_inputs = [arc for arc in doc.arcs if arc.target == t4]
print(f"Found {len(t4_inputs)} input arcs:")

for arc in t4_inputs:
    source = arc.source
    print(f"\nArc {arc.id}:")
    print(f"  From: {source.id} ({source.label})")
    print(f"  Type: {arc.__class__.__name__}")
    print(f"  Weight: {arc.weight}")
    print(f"  Source tokens: {source.tokens}")
    print(f"  Source initial_marking: {source.initial_marking}")
    
    if hasattr(arc, 'consumes_tokens'):
        print(f"  Consumes tokens: {arc.consumes_tokens()}")

# Check P101
p101 = next((p for p in doc.places if p.id == 'P101'), None)
if p101:
    print("\n" + "=" * 80)
    print("P101 STATE")
    print("=" * 80)
    print(f"ID: {p101.id}")
    print(f"Label: {p101.label}")
    print(f"Tokens: {p101.tokens}")
    print(f"Initial marking: {p101.initial_marking}")
    
    # Check if P101 has any input transitions (sources)
    p101_inputs = [arc for arc in doc.arcs if arc.target == p101]
    print(f"\nP101 has {len(p101_inputs)} input arc(s):")
    for arc in p101_inputs:
        if hasattr(arc.source, 'transition_type'):
            print(f"  From transition {arc.source.id} (type: {arc.source.transition_type})")

print("\n" + "=" * 80)
print("DIAGNOSIS")
print("=" * 80)

if p101 and p101.tokens == 0:
    print("❌ PROBLEM: P101 has 0 tokens")
    print("   T3 and T4 cannot fire without substrate tokens")
    print("\nSOLUTION: Either:")
    print("  1. Set P101 initial_marking > 0 in the model file")
    print("  2. Add a source transition that produces tokens to P101")
else:
    print("✅ P101 has tokens")

print()
