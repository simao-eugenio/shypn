#!/usr/bin/env python3
"""
Debug P5 consumption issue - verify consumes_tokens() method fix.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from shypn.netobjs.inhibitor_arc import InhibitorArc
from shypn.netobjs.place import Place
from shypn.netobjs.transition import Transition

print('=== INHIBITOR ARC FIX VERIFICATION ===\n')

# Test that consumes_tokens() method exists
print('Testing InhibitorArc.consumes_tokens() method:')
print(f'  Method exists: {hasattr(InhibitorArc, "consumes_tokens")}')

# Create real Place and Transition objects
p = Place(x=0, y=0, id='P5', name='P5')
t = Transition(x=100, y=0, id='T9', name='T9')

# Create inhibitor arc
inh_arc = InhibitorArc(p, t, 1, 'I1', weight=5)

print(f'  consumes_tokens() returns: {inh_arc.consumes_tokens()}')
print(f'  Expected: False')
print()

if hasattr(inh_arc, 'consumes_tokens') and not inh_arc.consumes_tokens():
    print('✅ FIX VERIFIED: Inhibitor arcs will be SKIPPED during consumption phase')
    print('   The check "hasattr(arc, \'consumes_tokens\') and not arc.consumes_tokens()"')
    print('   will now correctly identify inhibitor arcs as read-only.')
else:
    print('❌ FIX FAILED: Something is wrong with the implementation')

print()
print('=== CONSUMPTION LOGIC ===')
print('Before fix:')
print('  - hasattr(inh_arc, "consumes_tokens") → False')
print('  - Arc treated as normal consuming arc → P5 consumed ❌')
print()
print('After fix:')
print('  - hasattr(inh_arc, "consumes_tokens") → True')
print('  - inh_arc.consumes_tokens() → False')
print('  - Arc skipped during consumption → P5 accumulates ✅')


