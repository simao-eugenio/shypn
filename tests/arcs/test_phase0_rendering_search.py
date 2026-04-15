#!/usr/bin/env python3
"""
Phase 0: KEGG Parser Investigation - Test 2
Search for any Cairo drawing code outside Arc.render() that might create spurious lines.

This script searches for:
1. Cairo line drawing outside netobjs/
2. Direct cr.line_to() / cr.stroke() in helpers/
3. Any rendering of KEGG relations
4. Any rendering of KEGG graphics elements
"""

import os
import re

print("=" * 80)
print("PHASE 0 - TEST 2: Search for Spurious Line Rendering Code")
print("=" * 80)
print()

# Define search patterns
patterns = [
    (r'cr\.line_to', "Cairo line drawing"),
    (r'cr\.move_to.*cr\.line_to', "Cairo line sequence"),
    (r'pathway\.relations', "KEGG relations access"),
    (r'relation.*render|draw.*relation', "Relation rendering"),
    (r'graphics.*line|line.*graphics', "Graphics line elements"),
    (r'for.*relation.*in', "Iteration over relations"),
]

# Files to search (exclude netobjs/ since Arc.render() is supposed to draw lines)
search_paths = [
    "src/shypn/helpers/",
    "src/shypn/importer/kegg/",
    "src/shypn/canvas/",
    "src/shypn/data/",
]

print("Searching for suspicious rendering code...")
print()

findings = {}

for search_path in search_paths:
    if not os.path.exists(search_path):
        continue
    
    for root, dirs, files in os.walk(search_path):
        for file in files:
            if not file.endswith('.py'):
                continue
            
            filepath = os.path.join(root, file)
            
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                for pattern, description in patterns:
                    matches = re.finditer(pattern, content, re.IGNORECASE)
                    for match in matches:
                        # Find line number
                        line_num = content[:match.start()].count('\n') + 1
                        line_content = lines[line_num - 1].strip()
                        
                        # Skip comments
                        if line_content.startswith('#'):
                            continue
                        
                        key = (filepath, description)
                        if key not in findings:
                            findings[key] = []
                        findings[key].append((line_num, line_content))
            
            except Exception as e:
                print(f"  Error reading {filepath}: {e}")

# Report findings
if findings:
    print("FINDINGS:")
    print("=" * 80)
    print()
    
    for (filepath, description), matches in sorted(findings.items()):
        print(f"📄 {filepath}")
        print(f"   Type: {description}")
        print(f"   Occurrences: {len(matches)}")
        for line_num, line_content in matches[:3]:  # Show first 3
            print(f"     Line {line_num}: {line_content}")
        if len(matches) > 3:
            print(f"     ... and {len(matches) - 3} more")
        print()
else:
    print("✓ NO suspicious rendering code found outside netobjs/")
    print()

print("=" * 80)
print("ANALYSIS")
print("=" * 80)
print()

# Check specific files for KEGG relation handling
critical_files = [
    "src/shypn/helpers/model_canvas_loader.py",
    "src/shypn/importer/kegg/pathway_converter.py",
    "src/shypn/importer/kegg/kgml_parser.py",
]

print("Checking critical files for relation/graphics handling:")
print()

for filepath in critical_files:
    if not os.path.exists(filepath):
        print(f"  ⚠ File not found: {filepath}")
        continue
    
    print(f"  📄 {filepath}")
    
    with open(filepath, 'r') as f:
        content = f.read()
    
    # Check for relation processing
    has_relation_iter = bool(re.search(r'for.*relation.*in.*pathway\.relations', content))
    has_relation_render = bool(re.search(r'relation.*render|draw.*relation', content, re.IGNORECASE))
    has_graphics_render = bool(re.search(r'graphics.*render|draw.*graphics', content, re.IGNORECASE))
    
    if has_relation_iter:
        print(f"     ❌ ITERATES over pathway.relations")
    else:
        print(f"     ✓ Does NOT iterate over relations")
    
    if has_relation_render:
        print(f"     ❌ Contains relation rendering code")
    else:
        print(f"     ✓ No relation rendering")
    
    if has_graphics_render:
        print(f"     ❌ Contains graphics rendering code")
    else:
        print(f"     ✓ No graphics rendering")
    
    print()

print("=" * 80)
print("CONCLUSION")
print("=" * 80)
print()
print("Expected results:")
print("  - model_canvas_loader.py: Only draws objects from get_all_objects()")
print("  - pathway_converter.py: Does NOT process relations")
print("  - kgml_parser.py: Parses but does NOT render relations")
print()
print("If all checks pass:")
print("  → No spurious line rendering code found")
print("  → Spurious lines may be from incorrect Arc geometry")
print()
print("=" * 80)
