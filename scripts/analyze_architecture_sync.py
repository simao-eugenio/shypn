#!/usr/bin/env python3
"""
Architecture Synchronization Analysis

Analyzes the complete synchronization path:
Class Definition → Class Attributes → JSON (to_dict/from_dict) → Dialog Properties (UI)

Identifies mismatches and missing properties across all layers.
"""

import ast
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple

class ArchitectureSyncAnalyzer:
    """Analyzes architecture synchronization across OOP, JSON, and UI layers."""
    
    def __init__(self, src_dir: str = "src/shypn"):
        self.src_dir = Path(src_dir)
        self.results = {
            'Place': {},
            'Transition': {},
            'Arc': {}
        }
    
    def analyze_class_attributes(self, class_name: str) -> Set[str]:
        """Extract all attributes set in __init__ method."""
        if class_name == 'Place':
            file_path = self.src_dir / "netobjs" / "place.py"
        elif class_name == 'Transition':
            file_path = self.src_dir / "netobjs" / "transition.py"
        elif class_name == 'Arc':
            file_path = self.src_dir / "netobjs" / "arc.py"
        else:
            return set()
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Extract __init__ method
        init_match = re.search(r'def __init__\(.*?\n(.*?)(?=\n    def |\nclass |\Z)', content, re.DOTALL)
        if not init_match:
            return set()
        
        init_code = init_match.group(1)
        
        # Find all self.attribute assignments
        attributes = set()
        for match in re.finditer(r'self\.(\w+)\s*=', init_code):
            attr = match.group(1)
            if not attr.startswith('_'):  # Exclude private attributes
                attributes.add(attr)
        
        return attributes
    
    def analyze_to_dict(self, class_name: str) -> Set[str]:
        """Extract all properties saved in to_dict method."""
        if class_name == 'Place':
            file_path = self.src_dir / "netobjs" / "place.py"
        elif class_name == 'Transition':
            file_path = self.src_dir / "netobjs" / "transition.py"
        elif class_name == 'Arc':
            file_path = self.src_dir / "netobjs" / "arc.py"
        else:
            return set()
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Extract to_dict method
        to_dict_match = re.search(r'def to_dict\(self\).*?\n(.*?)(?=\n    def |\nclass |\Z)', content, re.DOTALL)
        if not to_dict_match:
            return set()
        
        to_dict_code = to_dict_match.group(1)
        
        # Find all keys added to dict
        properties = set()
        
        # Pattern 1: data["key"] = value or data.update({"key": value})
        for match in re.finditer(r'["\'](\w+)["\']\s*:', to_dict_code):
            properties.add(match.group(1))
        
        # Pattern 2: data["key"] = self.attr
        for match in re.finditer(r'data\[["\'](\w+)["\']\]', to_dict_code):
            properties.add(match.group(1))
        
        return properties
    
    def analyze_from_dict(self, class_name: str) -> Set[str]:
        """Extract all properties loaded in from_dict method."""
        if class_name == 'Place':
            file_path = self.src_dir / "netobjs" / "place.py"
        elif class_name == 'Transition':
            file_path = self.src_dir / "netobjs" / "transition.py"
        elif class_name == 'Arc':
            file_path = self.src_dir / "netobjs" / "arc.py"
        else:
            return set()
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Extract from_dict method
        from_dict_match = re.search(r'def from_dict\(.*?\n(.*?)(?=\n    def |\n    @|\nclass |\Z)', content, re.DOTALL)
        if not from_dict_match:
            return set()
        
        from_dict_code = from_dict_match.group(1)
        
        # Find all data.get("key") or data["key"] accesses
        properties = set()
        
        # Pattern: data.get("key") or data["key"]
        for match in re.finditer(r'data(?:\.get\(|\[)["\'](\w+)["\']', from_dict_code):
            properties.add(match.group(1))
        
        return properties
    
    def analyze_dialog_properties(self, class_name: str) -> Set[str]:
        """Extract all properties exposed in dialog UI."""
        if class_name == 'Place':
            file_path = self.src_dir.parent / "helpers" / "place_prop_dialog_loader.py"
        elif class_name == 'Transition':
            file_path = self.src_dir.parent / "helpers" / "transition_prop_dialog_loader.py"
        elif class_name == 'Arc':
            file_path = self.src_dir.parent / "helpers" / "arc_prop_dialog_loader.py"
        else:
            return set()
        
        if not file_path.exists():
            return set()
        
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Find all builder.get_object() calls (UI widgets)
        # and getattr/setattr/hasattr on object
        properties = set()
        
        # Pattern 1: self.place_obj.attribute or self.transition_obj.attribute
        obj_name = f"{class_name.lower()}_obj"
        for match in re.finditer(rf'self\.{obj_name}\.(\w+)', content):
            attr = match.group(1)
            if not attr.startswith('_'):
                properties.add(attr)
        
        # Pattern 2: hasattr(self.place_obj, 'attribute')
        for match in re.finditer(rf'hasattr\(self\.{obj_name},\s*["\'](\w+)["\']', content):
            properties.add(match.group(1))
        
        # Pattern 3: getattr(self.place_obj, 'attribute')
        for match in re.finditer(rf'getattr\(self\.{obj_name},\s*["\'](\w+)["\']', content):
            properties.add(match.group(1))
        
        return properties
    
    def compare_sets(self, set_a: Set[str], set_b: Set[str], name_a: str, name_b: str) -> Dict:
        """Compare two sets and return missing properties."""
        missing_in_b = set_a - set_b
        missing_in_a = set_b - set_a
        common = set_a & set_b
        
        return {
            f'in_{name_a}_not_{name_b}': sorted(missing_in_b),
            f'in_{name_b}_not_{name_a}': sorted(missing_in_a),
            'common': sorted(common)
        }
    
    def analyze_class(self, class_name: str):
        """Run complete analysis for a class."""
        print(f"\n{'='*80}")
        print(f"ANALYZING: {class_name}")
        print(f"{'='*80}\n")
        
        # Collect data from all layers
        class_attrs = self.analyze_class_attributes(class_name)
        to_dict_props = self.analyze_to_dict(class_name)
        from_dict_props = self.analyze_from_dict(class_name)
        dialog_props = self.analyze_dialog_properties(class_name)
        
        print(f"1. CLASS ATTRIBUTES (__init__): {len(class_attrs)} attributes")
        print(f"   {sorted(class_attrs)}\n")
        
        print(f"2. JSON SERIALIZATION (to_dict): {len(to_dict_props)} properties")
        print(f"   {sorted(to_dict_props)}\n")
        
        print(f"3. JSON DESERIALIZATION (from_dict): {len(from_dict_props)} properties")
        print(f"   {sorted(from_dict_props)}\n")
        
        print(f"4. DIALOG UI PROPERTIES: {len(dialog_props)} properties exposed")
        print(f"   {sorted(dialog_props)}\n")
        
        # Compare layers
        print(f"\n{'─'*80}")
        print("SYNCHRONIZATION ANALYSIS")
        print(f"{'─'*80}\n")
        
        # 1. Class → to_dict
        print("❶ CLASS ATTRIBUTES → to_dict (JSON serialization)")
        comp1 = self.compare_sets(class_attrs, to_dict_props, 'class', 'to_dict')
        if comp1['in_class_not_to_dict']:
            print(f"   ⚠️  NOT SAVED TO JSON: {comp1['in_class_not_to_dict']}")
        else:
            print(f"   ✅ All class attributes are saved to JSON")
        if comp1['in_to_dict_not_class']:
            print(f"   ℹ️  Extra in JSON (inherited/computed): {comp1['in_to_dict_not_class']}")
        print()
        
        # 2. to_dict → from_dict
        print("❷ to_dict → from_dict (JSON round-trip)")
        comp2 = self.compare_sets(to_dict_props, from_dict_props, 'to_dict', 'from_dict')
        if comp2['in_to_dict_not_from_dict']:
            print(f"   ⚠️  SAVED BUT NOT LOADED: {comp2['in_to_dict_not_from_dict']}")
        else:
            print(f"   ✅ All saved properties are loaded")
        if comp2['in_from_dict_not_to_dict']:
            print(f"   ℹ️  Loaded but not saved (legacy support): {comp2['in_from_dict_not_to_dict']}")
        print()
        
        # 3. Class → Dialog
        print("❸ CLASS ATTRIBUTES → DIALOG UI (user exposure)")
        comp3 = self.compare_sets(class_attrs, dialog_props, 'class', 'dialog')
        if comp3['in_class_not_dialog']:
            print(f"   ℹ️  Not exposed in UI (internal/computed): {comp3['in_class_not_dialog']}")
        if comp3['in_dialog_not_class']:
            print(f"   ⚠️  UI REFERENCES MISSING ATTRIBUTES: {comp3['in_dialog_not_class']}")
        else:
            print(f"   ✅ All dialog properties exist in class")
        
        # Calculate coverage
        coverage = len(comp3['common']) / len(class_attrs) * 100 if class_attrs else 0
        print(f"   📊 UI Coverage: {coverage:.1f}% of class attributes")
        print()
        
        # Store results
        self.results[class_name] = {
            'class_attrs': sorted(class_attrs),
            'to_dict_props': sorted(to_dict_props),
            'from_dict_props': sorted(from_dict_props),
            'dialog_props': sorted(dialog_props),
            'not_saved': comp1['in_class_not_to_dict'],
            'not_loaded': comp2['in_to_dict_not_from_dict'],
            'not_in_ui': comp3['in_class_not_dialog'],
            'ui_missing_attrs': comp3['in_dialog_not_class']
        }
    
    def generate_summary(self):
        """Generate summary report."""
        print(f"\n{'='*80}")
        print("ARCHITECTURE SYNCHRONIZATION SUMMARY")
        print(f"{'='*80}\n")
        
        for class_name in ['Place', 'Transition', 'Arc']:
            if class_name not in self.results:
                continue
            
            result = self.results[class_name]
            print(f"\n{class_name}:")
            print(f"  Class: {len(result['class_attrs'])} attrs | "
                  f"JSON: {len(result['to_dict_props'])} props | "
                  f"Dialog: {len(result['dialog_props'])} widgets")
            
            issues = []
            if result['not_saved']:
                issues.append(f"❌ {len(result['not_saved'])} not saved to JSON")
            if result['not_loaded']:
                issues.append(f"❌ {len(result['not_loaded'])} saved but not loaded")
            if result['ui_missing_attrs']:
                issues.append(f"❌ {len(result['ui_missing_attrs'])} UI refs missing attrs")
            
            if issues:
                for issue in issues:
                    print(f"    {issue}")
            else:
                print(f"    ✅ All layers synchronized")
        
        print(f"\n{'='*80}\n")

def main():
    analyzer = ArchitectureSyncAnalyzer()
    
    # Analyze each netobject class
    for class_name in ['Place', 'Transition', 'Arc']:
        analyzer.analyze_class(class_name)
    
    # Generate summary
    analyzer.generate_summary()
    
    print("Analysis complete. Check output above for synchronization issues.")

if __name__ == "__main__":
    main()
