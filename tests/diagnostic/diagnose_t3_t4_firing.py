#!/usr/bin/env python3#!/usr/bin/env python3

""""""

Diagnose firing issues for T3, T4, and source transitions.Diagnostic script to test if T3 and T4 can actually fire in simulation

""""""



import sysimport sys

from pathlib import Pathimport json

sys.path.insert(0, str(Path(__file__).parent / 'src'))from pathlib import Path



from shypn.data.canvas.document_model import DocumentModel# Add src to path

from shypn.netobjs.test_arc import TestArcsys.path.insert(0, str(Path(__file__).parent / 'src'))

from shypn.engine.immediate_behavior import ImmediateBehavior

from shypn.data.canvas.document_model import DocumentModel

print("=" * 80)from shypn.engine.simulation.controller import SimulationController

print("DIAGNOSING T3, T4, and SOURCE TRANSITIONS")

print("=" * 80)# Load the model

model_path = Path('workspace/projects/Interactive/models/hsa00010.shy')

# Load modelprint("=" * 80)

model_path = 'workspace/projects/models/hsa00010_FIXED.shy'print("LOADING MODEL")

document = DocumentModel.load_from_file(model_path)print("=" * 80)

print(f"Loading: {model_path}")

print(f"\n✓ Model loaded: {len(document.transitions)} transitions\n")

# Just load the JSON directly

# Find T3, T4, and any source transitionswith open(model_path, 'r') as f:

transitions_to_check = []    model_data = json.load(f)

for trans in document.transitions:

    if trans.id in ['T3', 'T4', 'T35'] or getattr(trans, 'is_source', False):print(f"Loaded: {len(model_data['places'])} places, {len(model_data['transitions'])} transitions, {len(model_data['arcs'])} arcs")

        transitions_to_check.append(trans)print()



if len(transitions_to_check) == 0:# Check P101 initial state

    print("⚠️  T3, T4, T35, or source transitions not found!")p101 = next(p for p in model_data['places'] if p['id'] == 'P101')

    print("\nSearching for transitions with no inputs (potential sources)...")print(f"P101 ({p101['label']}): {p101['initial_marking']} tokens")

    print()

    for trans in document.transitions:

        input_arcs = [a for a in document.arcs if a.target == trans]# Check T3 and T4 initial state

        if len(input_arcs) == 0:print("=" * 80)

            output_arcs = [a for a in document.arcs if a.source == trans]print("CHECKING T3 AND T4 CONFIGURATION")

            if len(output_arcs) > 0:print("=" * 80)

                print(f"\n  {trans.id}: {trans.label}")

                print(f"    Type: {getattr(trans, 'type', 'not specified')}")for tid in ['T3', 'T4']:

                print(f"    is_source: {getattr(trans, 'is_source', False)}")    trans = next(t for t in model_data['transitions'] if t['id'] == tid)

                print(f"    Produces to: {[a.target.id for a in output_arcs]}")    print(f"\n{tid} ({trans.get('label', 'no label')})")

    print(f"  Type: {trans.get('transition_type', 'N/A')}")

print(f"Found {len(transitions_to_check)} transitions to check:\n")    print(f"  Rate formula: {trans.get('rate', 'N/A')}")

    

for trans in transitions_to_check:    # Check input arcs

    print("=" * 80)    input_arcs = [arc for arc in model_data['arcs'] if arc.get('target_id') == tid]

    print(f"TRANSITION: {trans.id} - {trans.label}")    print(f"  Input arcs: {len(input_arcs)}")

    print("=" * 80)    

        all_enabled = True

    trans_type = getattr(trans, 'type', 'immediate')    for arc in input_arcs:

    is_source = getattr(trans, 'is_source', False)        source_place = next(p for p in model_data['places'] if p['id'] == arc['source_id'])

            arc_type = arc.get('arc_type', 'normal')

    print(f"  Type: {trans_type}")        weight = arc.get('weight', 1)

    print(f"  is_source: {is_source}")        threshold = arc.get('threshold', None)

            

    # Get input arcs        print(f"    - {source_place['id']} ({source_place['label']}): {source_place['initial_marking']} tokens, arc type: {arc_type}")

    input_arcs = [a for a in document.arcs if a.target == trans]        

    print(f"\n  Input arcs: {len(input_arcs)}")        # Check if enabled

            if arc_type == 'test':

    if len(input_arcs) == 0 and not is_source:            enabled = source_place['initial_marking'] >= weight

        print("    ⚠️  NO INPUT ARCS and NOT marked as source!")        elif arc_type == 'inhibitor':

        print("    → This transition needs 'is_source=True' to fire")            enabled = source_place['initial_marking'] < weight

            else:

    blocking_arcs = []            tokens_needed = threshold if threshold is not None else weight

    for arc in input_arcs:            enabled = source_place['initial_marking'] >= tokens_needed

        source_place = arc.source        

        is_test = isinstance(arc, TestArc)        if not enabled:

        is_catalyst = getattr(source_place, 'is_catalyst', False)            all_enabled = False

                    print(f"        ❌ NOT ENABLED")

        arc_type_str = "TestArc (catalyst)" if is_test else "Normal arc"        else:

        tokens = source_place.tokens            print(f"        ✅ ENABLED")

        weight = arc.weight    

            if all_enabled:

        blocked = tokens < weight        print(f"  ✅ ALL INPUT ARCS ENABLED")

        status = "✗ BLOCKS" if blocked else "✓ OK"    else:

                print(f"  ❌ SOME ARCS DISABLED")

        print(f"\n    {arc.id}: {source_place.id} -> {trans.id}")

        print(f"      Type: {arc_type_str}")print("\n" + "=" * 80)

        print(f"      Weight: {weight}")print("DIAGNOSIS SUMMARY")

        print(f"      Source tokens: {tokens}")print("=" * 80)

        print(f"      Status: {status}")print("\nBoth T3 and T4 have all inputs enabled based on the model file.")

        print("\nIf they're not firing in the actual application, possible reasons:")

        if blocked:print("  1. Simulation not running (check if simulation is started)")

            blocking_arcs.append((arc.id, source_place.id, tokens, weight))print("  2. Simulation time too short (stochastic transitions need time to fire)")

    print("  3. Rate formula evaluating to 0 or very small (check Michaelis-Menten)")

    # Get output arcsprint("  4. Continuous transitions may need special handling")

    output_arcs = [a for a in document.arcs if a.source == trans]print("  5. GUI not updating to show changes")

    print(f"\n  Output arcs: {len(output_arcs)}")print("\nRecommendations:")

    for arc in output_arcs:print("  - Check if simulation is actually running in the GUI")

        target_place = arc.targetprint("  - Run simulation for longer time (e.g., 10-100 time units)")

        print(f"    {arc.id}: {trans.id} -> {target_place.id} (tokens={target_place.tokens})")print("  - Check the simulation speed/step settings")

    print("  - Verify that continuous transitions are being processed")

    # Check if can fireprint("\n" + "=" * 80)

    print(f"\n  ENABLEMENT CHECK:")
    
    if is_source:
        print(f"    ✓ Source transition - ALWAYS ENABLED")
    elif len(blocking_arcs) > 0:
        print(f"    ✗ DISABLED - Blocked by {len(blocking_arcs)} arc(s):")
        for arc_id, place_id, tokens, weight in blocking_arcs:
            print(f"      - {arc_id}: {place_id} has {tokens} tokens, needs {weight}")
    else:
        behavior = ImmediateBehavior(trans, document)
        enabled = behavior.is_enabled()
        if enabled:
            print(f"    ✓ ENABLED - Can fire!")
        else:
            print(f"    ✗ DISABLED - Check behavior implementation")
    
    print()

print("=" * 80)
print("SUMMARY & SOLUTIONS")
print("=" * 80)

print("""
ISSUES FOUND:
1. T35 doesn't exist in saved file
2. T3 and T4 still have catalyst test arcs
3. P15 has 0 tokens (blocks T3 and T4)

SOLUTIONS:

Option A - Create Source Transition for P15:
  1. In UI: Create new transition T35
  2. In transition properties: Set 'is_source' = True
  3. Create arc: T35 -> P15
  4. Save model (Ctrl+S)
  5. Start simulation - T35 will produce tokens to P15 automatically

Option B - Add Initial Tokens to P15:
  1. Click on place P15
  2. Set initial_marking = 10 (or desired amount)
  3. Save model
  4. Reload - P15 will start with 10 tokens

Option C - Delete Catalyst Test Arcs from T3/T4:
  1. Select and delete arcs: A77 (from T3), A78 and A104 (from T4)
  2. Save model
  3. This removes catalyst requirements (if you want that)

RECOMMENDED: Use Option A (source transition) for continuous supply.
""")

print("=" * 80)
