#!/usr/bin/env python3
"""Test hasattr and getattr with property decorators."""

class TestClass:
    def __init__(self):
        self._properties = {'rate_function': 'test'}
    
    @property
    def properties(self):
        return self._properties

# Test
obj = TestClass()

print("1. hasattr(obj, 'properties'):", hasattr(obj, 'properties'))
print("2. getattr(obj, 'properties', {}):", getattr(obj, 'properties', {}))
print("3. 'rate_function' in obj.properties:", 'rate_function' in obj.properties)
print("4. Direct access obj.properties:", obj.properties)

# Test what stochastic_behavior.py does
props = getattr(obj, 'properties', {})
print("\n5. props = getattr(obj, 'properties', {}):", props)
print("6. 'rate_function' in props:", 'rate_function' in props)
